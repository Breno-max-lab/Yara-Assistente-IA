from groq import Groq
from src.config import (
    get_groq_api_key,
    LLM_MODEL,
    PROMPT_CHAT_GERAL,
    PROMPT_ALFABETIZACAO,
    PROMPT_PROFESSOR,
)


class LLMEngine:
    def __init__(self):
        api_key = get_groq_api_key()
        self.client = Groq(api_key=api_key) if api_key else None
        self.modelo_ativo = self._descobrir_modelo_disponivel()

    def _descobrir_modelo_disponivel(self) -> str:
        """Consulta a API da Groq para pegar um modelo de texto realmente ativo na conta."""
        if not self.client:
            return LLM_MODEL
        try:
            modelos = self.client.models.list().data
            ids_disponiveis = [m.id for m in modelos]

            preferidos = [
                "llama-3.3-70b-versatile",
                "llama-3.1-8b-instant",
                "openai/gpt-oss-120b",
                "openai/gpt-oss-20b",
                "qwen/qwen3-32b",
                "gemma2-9b-it",
                "llama3-70b-8192",
                "llama3-8b-8192",
            ]
            for pref in preferidos:
                if pref in ids_disponiveis:
                    return pref

            ignorados = ("whisper", "tts", "guard", "safeguard", "embed", "vision")
            for mid in ids_disponiveis:
                if not any(termo in mid.lower() for termo in ignorados):
                    return mid

        except Exception:
            pass
        return LLM_MODEL

    def gerar_resposta(
        self,
        historico: list[dict],
        modo: str = "geral",
        contexto_extra: str = "",
    ) -> str:
        if not self.client:
            return "⚠️ Chave da API Groq não configurada. Adicione GROQ_API_KEY nas configurações."

        if modo == "alfabetizacao":
            system_prompt = PROMPT_ALFABETIZACAO
            tokens_limite = 140
            temperatura = 0.35
        elif modo == "professor":
            system_prompt = PROMPT_PROFESSOR
            tokens_limite = 2048
            temperatura = 0.6
        else:
            system_prompt = PROMPT_CHAT_GERAL
            tokens_limite = 600
            temperatura = 0.6

        if contexto_extra:
            system_prompt += f"\n\nContexto adicional:\n{contexto_extra}"

        mensagens = [{"role": "system", "content": system_prompt}]
        for msg in historico[-10:]:
            mensagens.append({"role": msg["role"], "content": msg["content"]})

        try:
            resposta = self.client.chat.completions.create(
                model=self.modelo_ativo,
                messages=mensagens,
                temperature=temperatura,
                max_tokens=tokens_limite,
            )
            return resposta.choices[0].message.content.strip()
        except Exception as e:
            return f"Erro com o modelo '{self.modelo_ativo}': {str(e)}"