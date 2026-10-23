import json

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, StreamingResponse

from app import config
from app.modules import dlp

app = FastAPI(title="LLM-Guard", version="0.3")


def upstream_headers():
    headers = {"Content-Type": "application/json"}
    if config.LLM_API_KEY:
        headers["Authorization"] = f"Bearer {config.LLM_API_KEY}"
    return headers


@app.get("/health")
def health():
    return {"status": "ok", "service": "LLM-Guard"}


@app.post("/dlp/test")
async def dlp_test(request: Request):
    """Demo ke liye: text bhejo, masked version dekho."""
    body = await request.json()
    mapping = {}
    masked = dlp.mask_text(body.get("text", ""), mapping)
    return {"masked": masked, "found": list(mapping.keys())}


@app.post("/v1/chat/completions")
async def chat(request: Request):
    try:
        body = await request.json()
    except Exception:
        return JSONResponse(status_code=400, content={"error": "Invalid JSON body"})

    if "messages" not in body:
        return JSONResponse(status_code=400, content={"error": "'messages' field required"})

    # DLP: LLM tak jaane se pehle sensitive data mask karo
    body["messages"], mapping = dlp.mask_messages(body["messages"])
    if mapping:
        print(f"[DLP] Masked {len(mapping)} item(s): {list(mapping.keys())}")
        print(f"[DLP] Prompt sent to LLM: {body['messages'][-1]['content']}")

    if body.get("stream"):
        return stream_response(body)

    try:
        async with httpx.AsyncClient(timeout=config.REQUEST_TIMEOUT) as client:
            r = await client.post(config.LLM_API_URL, json=body, headers=upstream_headers())
        data = r.json()
        # Return trip: placeholder ko wapas asli value banao
        if mapping:
            data = json.loads(dlp.unmask_text(json.dumps(data), mapping))
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