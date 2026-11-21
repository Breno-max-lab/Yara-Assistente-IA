import asyncio
import edge_tts
from src.config import TTS_VOICE


async def _gerar_audio_async(texto: str, voz: str) -> bytes:
    texto_limpo = texto.replace("*", "").replace("#", "").replace("`", "").strip()
    if not texto_limpo:
        return b""
    comunicador = edge_tts.Communicate(texto_limpo, voz, rate="+2%")
    audio_bytes = b""
    async for chunk in comunicador.stream():
        if chunk["type"] == "audio":
            audio_bytes += chunk["data"]
    return audio_bytes


def sintetizar_voz(texto: str, voz: str = TTS_VOICE) -> bytes:
    """Converte texto em áudio MP3 natural usando Edge-TTS."""
    try:
        return asyncio.run(_gerar_audio_async(texto, voz))
    except RuntimeError:
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(_gerar_audio_async(texto, voz))
        finally:
            loop.close()
    except Exception:
        return b""