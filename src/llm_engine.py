from groq import Groq
from src.config import get_groq_api_key, LLM_MODEL, PROMPT_CHAT_GERAL, PROMPT_ALFABETIZACAO

class LLMEngine:
    def __init__(self):
        api_key = get_groq_api_key()
        self.client = Groq(api_key=api_key) if api_key else None

    def gerar_resposta(self, historico: list[dict], modo: str = "geral", contexto_extra: str = "") -> str:
        if not self.client:
            return "⚠️ Chave da API Groq não configurada. Adicione GROQ_API_KEY nas configurações."

        system_prompt = PROMPT_ALFABETIZACAO if modo == "alfabetizacao" else PROMPT_CHAT_GERAL
        if contexto_extra:
            system_prompt += f"\n\nContexto adicional do vídeo que o usuário está assistindo:\n{contexto_extra}"

        mensagens = [{"role": "system", "content": system_prompt}]
        # Mantém as últimas 10 mensagens para economizar tokens e manter velocidade
        for msg in historico[-10:]:
            mensagens.append({"role": msg["role"], "content": msg["content"]})

        try:
            resposta = self.client.chat.completions.create(
                model=LLM_MODEL,
                messages=mensagens,
                temperature=0.6 if modo == "geral" else 0.4,
                max_tokens=300 if modo == "alfabetizacao" else 600,
            )
            return resposta.choices[0].message.content.strip()
        except Exception as e:
            return f"Desculpe, tive um problema para responder agora: {str(e)}"