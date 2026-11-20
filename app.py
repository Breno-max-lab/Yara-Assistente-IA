import streamlit as st
from src.llm_engine import LLMEngine
from src.speech_engine import SpeechEngine
from src.tts_engine import sintetizar_voz
from src.modules_ui import render_modulo_alfabetizacao, render_modulo_audiovisual

st.set_page_config(
    page_title="Yara - Assistente Ribeirinha Online",
    page_icon="🌿",
    layout="wide"
)

@st.cache_resource
def inicializar_motores():
    return LLMEngine(), SpeechEngine()

llm, stt = inicializar_motores()

# --- BARRA LATERAL (NAVEGAÇÃO) ---
with st.sidebar:
    st.title("🌿 Projeto Yara")
    st.caption("Assistente Educacional e Comunitária — PET / UFOPA")
    st.divider()

    pagina = st.radio(
        "Escolha onde quer ir:",
        [
            "💬 Chat Geral com a Yara",
            "🗣️ 1. Alfabetização (Voz)",
            "🩺 2. Saúde e Bem-Estar",
            "🌳 3. Educação Ambiental",
            "🛶 4. Cultura e História"
        ]
    )

    st.divider()
    ativar_voz_chat = st.toggle("🔊 Yara responde com voz no Chat Geral", value=True)

# --- ROTEAMENTO DAS TELAS ---
if pagina == "💬 Chat Geral com a Yara":
    st.header("💬 Converse com a Yara")
    st.caption("Tire dúvidas do dia a dia escrevendo ou enviando uma mensagem de voz.")

    if "mensagens_geral" not in st.session_state:
        st.session_state.mensagens_geral = [
            {"role": "assistant", "content": "Olá! Eu sou a Yara. Como posso ajudar você hoje?"}
        ]

    for msg in st.session_state.mensagens_geral:
        with st.chat_message(msg["role"], avatar="🌿" if msg["role"] == "assistant" else "🧑"):
            st.markdown(msg["content"])
            if msg.get("audio"):
                st.audio(msg["audio"], format="audio/mp3")

    # Entrada por voz ou texto
    audio_chat = st.audio_input("🎙️ Falar com a Yara", key="mic_geral")
    texto_chat = st.chat_input("Ou digite sua mensagem aqui...")

    entrada_usuario = None
    if audio_chat is not None:
        audio_bytes = audio_chat.getvalue()
        if st.session_state.get("ultimo_audio_geral") != audio_bytes:
            st.session_state.ultimo_audio_geral = audio_bytes
            with st.spinner("Transcrevendo sua fala..."):
                entrada_usuario = stt.transcrever_audio(audio_bytes)
    elif texto_chat:
        entrada_usuario = texto_chat

    if entrada_usuario:
        st.session_state.mensagens_geral.append({"role": "user", "content": entrada_usuario})
        with st.chat_message("user", avatar="🧑"):
            st.markdown(entrada_usuario)

        with st.chat_message("assistant", avatar="🌿"):
            with st.spinner("Yara está escrevendo..."):
                resposta = llm.gerar_resposta(st.session_state.mensagens_geral, modo="geral")
                st.markdown(resposta)
                audio_bytes = sintetizar_voz(resposta) if ativar_voz_chat else None
                if audio_bytes:
                    st.audio(audio_bytes, format="audio/mp3", autoplay=True)

        st.session_state.mensagens_geral.append({
            "role": "assistant",
            "content": resposta,
            "audio": audio_bytes
        })

elif pagina == "🗣️ 1. Alfabetização (Voz)":
    render_modulo_alfabetizacao(llm, stt)

elif pagina == "🩺 2. Saúde e Bem-Estar":
    render_modulo_audiovisual(
        chave_modulo="saude",
        titulo_pagina="🩺 Saúde e Bem-Estar",
        subtitulo="Vídeos e animações sobre prevenção de doenças, cuidados com a água e saúde comunitária.",
        llm=llm
    )

elif pagina == "🌳 3. Educação Ambiental":
    render_modulo_audiovisual(
        chave_modulo="ambiental",
        titulo_pagina="🌳 Educação Ambiental na Amazônia",
        subtitulo="Entenda os desafios da floresta, dos rios e como proteger nosso território.",
        llm=llm
    )

elif pagina == "🛶 4. Cultura e História":
    render_modulo_audiovisual(
        chave_modulo="cultura",
        titulo_pagina="🛶 Cultura, Lendas e História",
        subtitulo="Animações e histórias do folclore amazônico e da memória das comunidades.",
        llm=llm
    )