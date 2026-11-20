import asyncio
import edge_tts
from src.config import TTS_VOICE

async def _gerar_audio_async(texto: str, voz: str) -> bytes:
    # Remove caracteres de markdown que o sintetizador leria literalmente (ex: asteriscos)
    texto_limpo = texto.replace("*", "").replace("#", "").replace("_", "")
    comunicador = edge_tts.Communicate(texto_limpo, voz)
    audio_bytes = b""
    async for chunk in comunicador.stream():
        if chunk["type"] == "audio":
            audio_bytes += chunk["data"]
    return audio_bytes

def sintetizar_voz(texto: str, voz: str = TTS_VOICE) -> bytes | None:
    """Converte texto em áudio MP3 (bytes) para tocar direto no Streamlit."""
    if not texto or texto.startswith("⚠️"):
        return None
    try:
        return asyncio.run(_gerar_audio_async(texto, voz))
    except Exception:
        return None