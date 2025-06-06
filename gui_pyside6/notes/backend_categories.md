# Backend Categories

This note summarizes which features the optional backends provide. It is based on the investigation notes dated 2025‑06‑04.

## TTS engines
These backends synthesize speech from text and therefore show a text input field in the UI.

- **pyttsx3** – stable
- **gTTS** – stable
- **edge_tts** – stable
- **mms** – stable
- **kokoro** – stable
- **chatterbox** – stable
- **seamless_m4t** – experimental
- **bark** – experimental
- **tortoise** – experimental

## Audio tools
These backends operate on audio files instead of text. The UI displays a file picker when one of them is selected.

- **demucs** – splits audio into stems
- **vocos** – reconstructs audio using a neural codec
- **whisper** – transcribes speech to text

Backends marked as experimental either failed to install or had unresolved issues during testing.
