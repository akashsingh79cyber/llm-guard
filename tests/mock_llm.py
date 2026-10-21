import asyncio
import json
import time

from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse

app = FastAPI(title="Mock LLM")


@app.post("/v1/chat/completions")
async def chat(request: Request):
    body = await request.json()
    user_msg = body["messages"][-1]["content"]
    reply = f"Mock LLM reply: tumne bola '{user_msg}'"

    if body.get("stream"):
        async def generate():
            for word in reply.split():
                chunk = {
                    "id": "mock-1",
                    "object": "chat.completion.chunk",
                    "choices": [{"index": 0, "delta": {"content": word + " "}, "finish_reason": None}],
                }
                yield f"data: {json.dumps(chunk)}\n\n"
                await asyncio.sleep(0.2)
            yield "data: [DONE]\n\n"

        return StreamingResponse(generate(), media_type="text/event-stream")

    return {
        "id": "mock-1",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": body.get("model", "mock-model"),
        "choices": [
            {"index": 0, "message": {"role": "assistant", "content": reply}, "finish_reason": "stop"}
        ],
    }