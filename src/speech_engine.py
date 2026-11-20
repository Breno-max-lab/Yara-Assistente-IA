import io
from groq import Groq
from src.config import get_groq_api_key, STT_MODEL


class SpeechEngine:
    def __init__(self):
        api_key = get_groq_api_key()
        self.client = Groq(api_key=api_key) if api_key else None

    def transcrever_audio(
        self,
        audio_bytes: bytes,
        nome_arquivo: str = "audio.wav",
        dica_contexto: str = ""
    ) -> str:
        """Recebe os bytes do st.audio_input e retorna o texto transcrito via Whisper."""
        if not self.client:
            return ""

        try:
            arquivo_virtual = io.BytesIO(audio_bytes)
            arquivo_virtual.name = nome_arquivo

            kwargs = {
                "file": (nome_arquivo, arquivo_virtual.read()),
                "model": STT_MODEL,
                "language": "pt",
                "response_format": "text",
                "temperature": 0.0,
            }
            if dica_contexto:
                kwargs["prompt"] = dica_contexto

            transcricao = self.client.audio.transcriptions.create(**kwargs)
            return str(transcricao).strip()
        except Exception as e:
            return f"[Erro ao entender o áudio: {str(e)}]"