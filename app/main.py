import json
import time
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, StreamingResponse

from app import config
from app.modules import auth, dlp, output_validator, rules, scanner
from app.modules.logger import log_event


@asynccontextmanager
async def lifespan(app):
    scanner.load_model()
    print(f"[SCANNER] Model loaded, threshold = {scanner.load_threshold()}")
    yield


app = FastAPI(title="LLM-Guard", version="0.7", lifespan=lifespan)


def upstream_headers():
    headers = {"Content-Type": "application/json"}
    if config.LLM_API_KEY:
        headers["Authorization"] = f"Bearer {config.LLM_API_KEY}"
    return headers


@app.get("/health")
async def health():
    return {"status": "ok", "service": "LLM-Guard"}


@app.post("/auth/login")
async def auth_login(request: Request):
    try:
        body = await request.json()
    except Exception:
        return JSONResponse(status_code=400, content={"error": "JSON body required"})
    username = body.get("username", "")
    token = auth.login(username, body.get("password", ""))
    if not token:
        log_event("LOGIN_FAILED", username or "?", "AUTH", "Invalid credentials")
        return JSONResponse(status_code=401, content={"error": "Invalid credentials"})
    log_event("LOGIN_OK", username, "AUTH", "Login success")
    return {"access_token": token, "token_type": "bearer"}


@app.post("/dlp/test")
async def dlp_test(request: Request):
    body = await request.json()
    mapping = {}
    masked = dlp.mask_text(body.get("text", ""), mapping)
    return {"masked": masked, "found": list(mapping.keys())}


@app.post("/rules/preview")
async def rules_preview(request: Request):
    body = await request.json()
    msgs = rules.enforce_system_prompt(body.get("messages", []))
    return {"messages_sent_to_llm": msgs}


@app.post("/scan/test")
async def scan_test(request: Request):
    body = await request.json()
    is_attack, prob = scanner.scan(body.get("text", ""))
    return {
        "is_attack": is_attack,
        "score": round(prob, 3),
        "threshold": scanner.load_threshold(),
    }


def blocked(rule, reason, user_id, prompt, score=None):
    print(f"[BLOCKED] {rule}: {reason}")
    log_event("BLOCKED", user_id, rule, reason, score, prompt)
    content = {"error": "Blocked by LLM-Guard", "rule": rule, "reason": reason}
    if score is not None:
        content["score"] = round(score, 3)
    return JSONResponse(
        status_code=403, content=content, headers={"X-LLM-Guard-Blocked": rule}
    )


@app.post("/v1/chat/completions")
async def chat(request: Request):
    auth_header = request.headers.get("Authorization", "")
    identity = None
    if auth_header.startswith("Bearer "):
        identity = auth.verify(auth_header[7:])
    if identity is None:
        log_event("AUTH_FAILED", "unknown", "AUTH", "Missing or invalid token")
        return JSONResponse(
            status_code=401,
            content={"error": "Login required. Get a token from /auth/login"},
        )
    user_id = identity["user"]
    role = identity["role"]

    try:
        body = await request.json()
    except Exception:
        return JSONResponse(status_code=400, content={"error": "Invalid JSON body"})

    if "messages" not in body:
        return JSONResponse(status_code=400, content={"error": "'messages' field required"})

    prompt = rules.user_text(body["messages"])

    violation = rules.check_prompt(body["messages"])
    if violation:
        return blocked(violation["rule"], violation["reason"], user_id, prompt)

    t0 = time.perf_counter()
    is_attack, score = scanner.scan(prompt)
    scan_ms = (time.perf_counter() - t0) * 1000
    print(f"[SCANNER] user={user_id} role={role} score={score:.2f} attack={is_attack} time={scan_ms:.1f}ms")
    if is_attack:
        return blocked(
            "ML_CLASSIFIER",
            f"Prompt injection / jailbreak detected (score {score:.2f})",
            user_id,
            prompt,
            score,
        )

    body["messages"] = rules.enforce_system_prompt(body["messages"])

    body["messages"], mapping = dlp.mask_messages(body["messages"])
    if mapping:
        print(f"[DLP] Masked {len(mapping)} item(s): {list(mapping.keys())}")
        print(f"[DLP] Prompt sent to LLM: {body['messages'][-1]['content']}")
        log_event("DLP_MASKED", user_id, "DLP", f"Masked {list(mapping.keys())}", None, prompt)

    if body.get("stream"):
        log_event("ALLOWED", user_id, None, "stream", score, prompt)
        return stream_response(body)

    try:
        async with httpx.AsyncClient(timeout=config.REQUEST_TIMEOUT) as client:
            r = await client.post(config.LLM_API_URL, json=body, headers=upstream_headers())
        data = r.json()

        if r.status_code == 200:
            sys_inst = rules.load_rules()["system_instruction"]
            data, findings = output_validator.validate_response(data, sys_inst)
            if findings:
                print(f"[OUTPUT] Redacted/blocked in response: {findings}")
                log_event("OUTPUT_REDACTED", user_id, "OUTPUT_VALIDATOR", str(findings), None, prompt)

        if mapping:
            data = json.loads(dlp.unmask_text(json.dumps(data), mapping))

        log_event("ALLOWED", user_id, None, None, score, prompt)
        return JSONResponse(
            status_code=r.status_code,
            content=data,
            headers={"X-LLM-Guard-Masked": str(len(mapping))},
        )
    except httpx.TimeoutException:
        return JSONResponse(status_code=504, content={"error": "LLM timeout"})
    except httpx.RequestError:
        return JSONResponse(status_code=502, content={"error": "LLM unreachable"})
    except ValueError:
        return JSONResponse(status_code=502, content={"error": "LLM returned invalid response"})


def stream_response(body):
    async def event_generator():
        try:
            async with httpx.AsyncClient(timeout=None) as client:
                async with client.stream(
                    "POST", config.LLM_API_URL, json=body, headers=upstream_headers()
                ) as r:
                    async for chunk in r.aiter_raw():
                        yield chunk
        except httpx.RequestError:
            yield b'data: {"error": "LLM unreachable"}\n\n'

    return StreamingResponse(event_generator(), media_type="text/event-stream")