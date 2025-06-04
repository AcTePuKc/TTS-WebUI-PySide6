from __future__ import annotations

from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from . import BACKENDS, TRANSCRIBERS

app = FastAPI(title="Hybrid TTS API")


class SynthesisRequest(BaseModel):
    text: str
    backend: str = "pyttsx3"
    rate: Optional[int] = None
    voice: Optional[str] = None
    lang: Optional[str] = None


class SeparationRequest(BaseModel):
    audio: str
    backend: str = "demucs"
    model: Optional[str] = None


class TranscriptionRequest(BaseModel):
    audio: str
    backend: str = "whisper"
    model: Optional[str] = None


@app.post("/synthesize")
def synthesize(req: SynthesisRequest):
    if req.backend not in BACKENDS:
        raise HTTPException(status_code=400, detail="Unknown backend")
    output = Path("output_api.wav")
    BACKENDS[req.backend](
        req.text, output, rate=req.rate, voice=req.voice, lang=req.lang
    )
    return {"output": str(output)}


@app.post("/separate")
def separate(req: SeparationRequest):
    if req.backend != "demucs":
        raise HTTPException(status_code=400, detail="Unsupported backend")
    output_dir = Path("demucs_output")
    stems = BACKENDS["demucs"](Path(req.audio), output_dir, model_name=req.model or "htdemucs")
    return {"stems": [str(p) for p in stems]}


@app.post("/transcribe")
def transcribe(req: TranscriptionRequest):
    if req.backend not in TRANSCRIBERS:
        raise HTTPException(status_code=400, detail="Unsupported backend")
    text = TRANSCRIBERS[req.backend](Path(req.audio), model_name=req.model or "openai/whisper-large-v3")
    return {"text": text}


def run_server(host: str = "0.0.0.0", port: int = 8000):
    import uvicorn

    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    run_server()
