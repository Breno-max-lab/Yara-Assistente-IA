import streamlit as st
from src.llm_engine import LLMEngine
from src.speech_engine import SpeechEngine
from src.tts_engine import sintetizar_voz
from src.modules_ui import render_modulo_alfabetizacao, render_modulo_audiovisual

# Configuração da Página
st.set_page_config(
    page_title="Yara - Assistente IA",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilização CSS Avançada (Design Escuro, Botões Personalizados e Margens)
st.markdown("""
    <style>
        /* Ajuste do Tema Geral Escuro Escuro */
        [data-testid="stSidebar"] {
            background-color: #0E131F !important;
            border-right: 1px solid #1D2A44;
            padding-top: 10px;
        }
        .main {
            background-color: #0A0D14 !important;
        }
        
        /* Fontes e Texto */
        h1, h2, h3, h4, p, span, label {
            font-family: 'Inter', sans-serif !important;
        }

        /* Menu de Navegação Personalizado na Esquerda */
        .sidebar-btn {
            display: flex;
            align-items: center;
            background-color: #172237;
            color: #E2E8F0 !important;
            padding: 12px 16px;
            border-radius: 8px;
            margin-bottom: 10px;
            border: 1px solid #233554;
            cursor: pointer;
            transition: all 0.2s ease-in-out;
            font-weight: 500;
            text-decoration: none !important;
        }
        .sidebar-btn:hover {
            background-color: #1E2D4A;
            border-color: #2E8B57;
            transform: translateY(-1px);
        }
        .sidebar-btn-active {
            background-color: #2E8B57 !important;
            border-color: #3CB371;
            font-weight: 600;
        }

        /* Centralizar o Layout da Logo e Pergunta Inicial */
        .central-container {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            text-align: center;
            padding-top: 6%;
            margin-bottom: 2rem;
        }
        
        /* Chat e Mensagens */
        .stChatMessage {
            background-color: #111827 !important;
            border: 1px solid #1F2937 !important;
            border-radius: 12px !important;
            padding: 15px !important;
            margin-bottom: 12px !important;
        }
        
        /* Ajustar Inputs de Entrada */
        div[data-baseweb="input"] {
            background-color: #131A26 !important;
            border-radius: 25px !important;
            border: 1px solid #233554 !important;
        }
    </style>
""", unsafe_allow_html=True)

@st.cache_resource
def inicializar_motores():
    return LLMEngine(), SpeechEngine()

llm, stt = inicializar_motores()

# --- ESTADO DO MENU (Sessão para controlar a navegação) ---
if "pagina_atual" not in st.session_state:
    st.session_state.pagina_atual = "💬 Chat Geral com a Yara"

# --- BARRA LATERAL (Navegação baseada na imagem) ---
with st.sidebar:
    st.markdown("<h2 style='color: #fff; font-size: 24px; margin-bottom: 5px;'>Yara</h2>", unsafe_allow_html=True)
    
    # Botão "Novo" (Reseta o Chat)
    if st.button("➕ Novo", use_container_width=True):
        st.session_state.mensagens_geral = [
            {"role": "assistant", "content": "Olá! Eu sou a Yara. Como posso ajudar você hoje?"}
        ]
        st.session_state.pagina_atual = "💬 Chat Geral com a Yara"
        st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # Botões de Navegação Customizados (Ativos e Inativos)
    paginas_opcoes = {
        "🗣️ Alfabetização": "🗣️ 1. Alfabetização (Voz)",
        "🌱 Educação Ambiental": "🌳 3. Educação Ambiental",
        "❤️ Saúde e Bem-estar": "🩺 2. Saúde e Bem-Estar",
        "🛶 Cultura e História": "🛶 4. Cultura e História"
    }

    for label, valor in paginas_opcoes.items():
        ativo = "sidebar-btn-active" if st.session_state.pagina_atual == valor else ""
        if st.button(label, key=f"btn_{label}", use_container_width=True, help=f"Ir para {label}"):
            st.session_state.pagina_atual = valor
            st.rerun()

    st.markdown("<hr style='border-color: #1D2A44;'>", unsafe_allow_html=True)

    # Filtros de Perfil do Usuário
    st.markdown("<p style='font-size: 14px; font-weight: 600; color: #94A3B8; margin-bottom: 5px;'>Selecione o Perfil do Usuário: ⚙️</p>", unsafe_allow_html=True)
    perfil = st.radio(
        "Perfil", ["Aluno", "Professor"], 
        label_visibility="collapsed", index=0
    )

    st.markdown("<br>", unsafe_allow_html=True)
    
    # Toggle de Áudio
    ativar_voz_chat = st.checkbox("🔊 Responder também em áudio", value=True)

# --- ROTEAMENTO E EXIBIÇÃO DE TELAS ---

if st.session_state.pagina_atual == "💬 Chat Geral com a Yara":
    # MODO INICIAL: Interface limpa e centralizada com a imagem de logo
    if "mensagens_geral" not in st.session_state or len(st.session_state.mensagens_geral) <= 1:
        st.session_state.mensagens_geral = [
            {"role": "assistant", "content": "Olá! Eu sou a Yara. Como posso ajudar você hoje?"}
        ]
        
        # Injeção da Yara centralizada
        st.markdown("<div class='central-container'>", unsafe_allow_html=True)
        # Busca a logo e adiciona no centro
        try:
            st.image("assets/yara_icone.png", width=140)
        except Exception:
            # Fallback caso não ache a imagem no local correto
            st.image("https://raw.githubusercontent.com/Breno-max-lab/Yara-Assistente-IA/main/src/assets/yara_icone.png", width=140)
            
        st.markdown("""
            <h1 style='color:#FFFFFF; font-size: 42px; font-weight: 700; margin-top:10px; margin-bottom:5px;'>Yara</h1>
            <p style='color:#94A3B8; font-size: 18px; margin-bottom: 25px;'>Como posso te ajudar hoje?</p>
        </div>
        """, unsafe_allow_html=True)
        
    else:
        # Modo Conversa Ativa: Exibe histórico
        st.markdown("<h2 style='color:#FFF; font-weight:700;'>💬 Conversar com a Yara</h2>", unsafe_allow_html=True)
        st.caption("Tire dúvidas do dia a dia escrevendo ou enviando uma mensagem de voz.")
        
        for msg in st.session_state.mensagens_geral:
            with st.chat_message(msg["role"], avatar="🌿" if msg["role"] == "assistant" else "🧑"):
                st.markdown(msg["content"])
                if msg.get("audio"):
                    st.audio(msg["audio"], format="audio/mp3")

    # Inputs de texto e voz integrados
    audio_chat = st.audio_input("🎙️ Falar com a Yara", key="mic_geral")
    texto_chat = st.chat_input("Escreva ou grave uma mensagem...")

    entrada_usuario = None
    if audio_chat is not None:
        audio_bytes = audio_chat.getvalue()
        if st.session_state.get("ultimo_audio_geral") != audio_bytes:
            st.session_state.ultimo_audio_geral = audio_bytes
            with st.spinner("Ouvindo..."):
                entrada_usuario = stt.transcrever_audio(audio_bytes)
    elif texto_chat:
        entrada_usuario = texto_chat

    if entrada_usuario:
        # Remove a saudação inicial vazia se for a primeira mensagem real
        if (
            len(st.session_state.mensagens_geral) == 1
            and st.session_state.mensagens_geral[0]["content"] == "Olá! Eu sou a Yara. Como posso ajudar você hoje?"
        ):
            st.session_state.mensagens_geral = []

        st.session_state.mensagens_geral.append({"role": "user", "content": entrada_usuario})

        with st.spinner("Yara está pensando..."):
            resposta = llm.gerar_resposta(st.session_state.mensagens_geral, modo="geral")
            audio_resp = sintetizar_voz(resposta) if ativar_voz_chat else None

        st.session_state.mensagens_geral.append({
            "role": "assistant",
            "content": resposta,
            "audio": audio_resp
        })
        st.rerun()

elif st.session_state.pagina_atual == "🗣️ 1. Alfabetização (Voz)":
    render_modulo_alfabetizacao(llm, stt)

elif st.session_state.pagina_atual == "🩺 2. Saúde e Bem-Estar":
    render_modulo_audiovisual(
        chave_modulo="saude",
        titulo_pagina="❤️ Saúde e Bem-estar",
        subtitulo="Animações e dicas sobre cuidados de saúde, higiene e prevenção de doenças.",
        llm=llm
    )

elif st.session_state.pagina_atual == "🌳 3. Educação Ambiental":
    render_modulo_audiovisual(
        chave_modulo="ambiental",
        titulo_pagina="🌱 Educação Ambiental",
        subtitulo="Vídeos, lendas e animações sobre a preservação e valorização da Amazônia.",
        llm=llm
    )

elif st.session_state.pagina_atual == "🛶 4. Cultura e História":
    render_modulo_audiovisual(
        chave_modulo="cultura",
        titulo_pagina="🛶 Cultura e História",
        subtitulo="Animações, mitos e contos folclóricos de nossa gente e região.",
        llm=llm
    )