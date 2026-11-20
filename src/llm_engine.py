from groq import Groq
from src.config import get_groq_api_key, LLM_MODEL, PROMPT_CHAT_GERAL, PROMPT_ALFABETIZACAO

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

            # Ordem de preferência entre modelos comuns da Groq
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

            # Caso a Groq tenha lançado nomes novos, pega qualquer modelo de texto ativo
            ignorados = ("whisper", "tts", "guard", "safeguard", "embed", "vision")
            for mid in ids_disponiveis:
                if not any(termo in mid.lower() for termo in ignorados):
                    return mid

        except Exception:
            pass
        return LLM_MODEL

    def gerar_resposta(self, historico: list[dict], modo: str = "geral", contexto_extra: str = "") -> str:
        if not self.client:
            return "⚠️ Chave da API Groq não configurada. Adicione GROQ_API_KEY nas configurações."

        system_prompt = PROMPT_ALFABETIZACAO if modo == "alfabetizacao" else PROMPT_CHAT_GERAL
        if contexto_extra:
            system_prompt += f"\n\nContexto adicional do vídeo que o usuário está assistindo:\n{contexto_extra}"

        mensagens = [{"role": "system", "content": system_prompt}]
        for msg in historico[-10:]:
            mensagens.append({"role": msg["role"], "content": msg["content"]})

        try:
            resposta = self.client.chat.completions.create(
                model=self.modelo_ativo,
                messages=mensagens,
                temperature=0.6 if modo == "geral" else 0.4,
                max_tokens=300 if modo == "alfabetizacao" else 600,
            )
            return resposta.choices[0].message.content.strip()
        except Exception as e:
            # Diagnóstico claro caso a conta não tenha nenhum modelo habilitado
            return f"Erro com o modelo '{self.modelo_ativo}': {str(e)}"