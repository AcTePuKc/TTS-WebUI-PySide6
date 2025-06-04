from __future__ import annotations

from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from . import BACKENDS

app = FastAPI(title="Hybrid TTS API")


class SynthesisRequest(BaseModel):
    text: str
    backend: str = "pyttsx3"


@app.post("/synthesize")
def synthesize(req: SynthesisRequest):
    if req.backend not in BACKENDS:
        raise HTTPException(status_code=400, detail="Unknown backend")
    output = Path("output_api.wav")
    BACKENDS[req.backend](req.text, output)
    return {"output": str(output)}


def run_server(host: str = "0.0.0.0", port: int = 8000):
    import uvicorn

    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    run_server()
