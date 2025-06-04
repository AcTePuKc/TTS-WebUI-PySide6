from .pyttsx_backend import synthesize_to_file

BACKENDS = {
    "pyttsx3": synthesize_to_file,
}


def available_backends():
    return list(BACKENDS.keys())
