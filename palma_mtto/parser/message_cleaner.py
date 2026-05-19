NOISE_PATTERNS = [
    "end-to-end encrypted", "Messages and calls are", "created group", "added you", "added +"
]
import re

def is_noise(text: str) -> bool:
    txt = text.strip()
    if not txt:
        return True
    for pat in NOISE_PATTERNS:
        if pat in txt:
            return True
    # Solo menciones: ^(@[^\s]+[,. ]*)+$
    if re.match(r"^(@[^\s]+[,. ]*)+$", txt):
        return True
    return False
