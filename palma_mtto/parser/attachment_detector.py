import re

def detect_attachments(text: str):
    FILE_ATTACHED = r'([\w\-]+\.(?:jpg|jpeg|png|mp4|pdf|doc|xlsx))\s*\\(file attached\\)'
    MEDIA_OMITTED = r'\\(media omitted\\)'
    archivos = re.findall(FILE_ATTACHED, text, re.IGNORECASE)
    media_omitida = bool(re.search(MEDIA_OMITTED, text, re.IGNORECASE))
    # Limpieza de texto: quita los fragmentos
    txt_clean = re.sub(FILE_ATTACHED, '', text, flags=re.IGNORECASE)
    txt_clean = re.sub(MEDIA_OMITTED, '', txt_clean, flags=re.IGNORECASE)
    return archivos, media_omitida, txt_clean.strip()
