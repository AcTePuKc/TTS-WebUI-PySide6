# AGENTS.md

## Project Agents / Roles

- Architect: Hybrid TTS App Architect (PySide6 GUI + optional FastAPI server)
- Coding Agent: Writes modular, future-proof Python code
- Packaging Agent: Maintains clean packaging (Briefcase + UV + Docker)
- UI Agent: Builds PySide6 native UI (no Gradio glue in core app)
- Installer Agent: Manages lazy install of optional TTS backends

## Architecture Notes

- Core dependencies go in requirements.uv.toml
- Optional TTS backends go in backend_requirements.json
- Extensions are installed lazily at runtime
- App is Hybrid: supports Local GUI and optional API Server
- Target packaging: Briefcase (.exe), Dockerfile.server (optional), no Conda
- Gradio WebUI is optional and separate — core app is not Gradio dependent

## Coding Style

- Modular
- Explicit imports
- No decorator soup
- Clear utils functions
- Minimal base install
- No unnecessary dependencies
- No Gradio in core app
- No Conda packaging
- No unnecessary complexity