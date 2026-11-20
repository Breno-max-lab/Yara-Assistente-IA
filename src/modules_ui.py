import json
from pathlib import Path
import streamlit as st
from src.llm_engine import LLMEngine
from src.speech_engine import SpeechEngine
from src.tts_engine import sintetizar_voz

DATA_PATH = Path(__file__).parent.parent / "data" / "conteudos_modulos.json"

def carregar_conteudos() -> dict:
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def render_modulo_alfabetizacao(llm: LLMEngine, stt: SpeechEngine):
    st.header("🗣️ Alfabetização por Voz com a Yara")
    st.caption("Converse com a Yara como se fosse uma chamada de voz. Aperte o microfone para falar!")

    if "hist_alfabetizacao" not in st.session_state:
        boas_vindas = (
            "Olá! Eu sou a Yara e vamos aprender a ler juntos. "
            "Vamos começar com a palavra RIO. Ela começa com a letra R. "
            "Você consegue repetir comigo a palavra RIO, ou me dizer outra palavra que começa com R?"
        )
        st.session_state.hist_alfabetizacao = [{"role": "assistant", "content": boas_vindas}]
        st.session_state.audio_alfab_atual = sintetizar_voz(boas_vindas)

    # Cartão visual estilo Assistente de Voz (Siri / Alexa)
    ultima_fala_yara = st.session_state.hist_alfabetizacao[-1]["content"]
    with st.container(border=True):
        st.markdown("### 🌿 Yara diz:")
        st.markdown(f"#### *\"{ultima_fala_yara}\"*")
        if st.session_state.get("audio_alfab_atual"):
            st.audio(st.session_state.audio_alfab_atual, format="audio/mp3", autoplay=True)

    st.divider()

    col1, col2 = st.columns([3, 1])
    with col1:
        audio_aluno = st.audio_input("🎙️ Aperte para falar com a Yara", key="mic_alfabetizacao")
    with col2:
        st.write("")
        st.write("")
        if st.button("🔄 Nova Lição", use_container_width=True):
            del st.session_state["hist_alfabetizacao"]
            st.rerun()

    # Evita reprocessar o mesmo áudio ao recarregar a página
    if audio_aluno is not None:
        audio_bytes = audio_aluno.getvalue()
        if st.session_state.get("ultimo_audio_alfab") != audio_bytes:
            st.session_state.ultimo_audio_alfab = audio_bytes
            with st.spinner("Ouvindo você..."):
                texto_aluno = stt.transcrever_audio(audio_bytes)

            if texto_aluno:
                st.session_state.hist_alfabetizacao.append({"role": "user", "content": texto_aluno})
                with st.spinner("Yara está pensando..."):
                    resposta = llm.gerar_resposta(st.session_state.hist_alfabetizacao, modo="alfabetizacao")
                    audio_resp = sintetizar_voz(resposta)

                st.session_state.hist_alfabetizacao.append({"role": "assistant", "content": resposta})
                st.session_state.audio_alfab_atual = audio_resp
                st.rerun()

    with st.expander("📜 Ver histórico da aula de hoje"):
        for msg in st.session_state.hist_alfabetizacao:
            quem = "🌿 Yara" if msg["role"] == "assistant" else "🧑 Você"
            st.markdown(f"**{quem}:** {msg['content']}")


def render_modulo_audiovisual(chave_modulo: str, titulo_pagina: str, subtitulo: str, llm: LLMEngine):
    st.header(titulo_pagina)
    st.caption(subtitulo)

    conteudos = carregar_conteudos().get(chave_modulo, [])
    if not conteudos:
        st.info("Nenhum vídeo cadastrado neste módulo ainda.")
        return

    for item in conteudos:
        with st.container(border=True):
            col_vid, col_info = st.columns([1.4, 1])
            with col_vid:
                st.video(item["video_url"])
            with col_info:
                st.subheader(item["titulo"])
                st.markdown(f"**Tema:** `{item['categoria']}` • ⏱️ `{item['duracao']}`")
                st.write(item["descricao"])
                st.markdown("**Pontos principais:** " + ", ".join(item["topicos_chave"]))

                # Mini-interação rápida com a Yara sobre o vídeo
                pergunta = st.text_input(
                    "Ficou com dúvida sobre este vídeo? Pergunte à Yara:",
                    key=f"input_{item['id']}",
                    placeholder="Ex: Como faço isso na prática?"
                )
                if st.button("Perguntar à Yara", key=f"btn_{item['id']}"):
                    if pergunta.strip():
                        with st.spinner("Yara está respondendo..."):
                            contexto = f"Vídeo: {item['titulo']}. Resumo: {item['descricao']}"
                            resp = llm.gerar_resposta(
                                [{"role": "user", "content": pergunta}],
                                modo="geral",
                                contexto_extra=contexto
                            )
                            st.success(resp)
                            audio_resp = sintetizar_voz(resp)
                            if audio_resp:
                                st.audio(audio_resp, format="audio/mp3")