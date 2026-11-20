import asyncio
import concurrent.futures
import edge_tts
from src.config import TTS_VOICE


async def _gerar_audio_async(texto: str, voz: str, rate: str) -> bytes:
    texto_limpo = (
        texto.replace("*", "")
        .replace("#", "")
        .replace("_", "")
        .replace('"', "")
    )
    comunicador = edge_tts.Communicate(texto_limpo, voz, rate=rate)
    audio_bytes = b""
    async for chunk in comunicador.stream():
        if chunk["type"] == "audio":
            audio_bytes += chunk["data"]
    return audio_bytes


def sintetizar_voz(texto: str, voz: str = TTS_VOICE, rate: str = "+4%") -> bytes | None:
    """Converte texto em áudio MP3 de forma rápida e sem travar o loop do servidor."""
    if not texto or texto.startswith("⚠️"):
        return None
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            futuro = executor.submit(asyncio.run, _gerar_audio_async(texto, voz, rate))
            return futuro.result(timeout=10)
    except Exception:
        return None