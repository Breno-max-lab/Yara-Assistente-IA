import base64
from pathlib import Path
import streamlit as st
from src.llm_engine import LLMEngine
from src.speech_engine import SpeechEngine
from src.tts_engine import sintetizar_voz
from src.modules_ui import render_modulo_alfabetizacao, render_modulo_audiovisual

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Yara • Assistente IA",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded"
)

def carregar_logo_base64() -> str:
    """Carrega o ícone da Yara em base64 para embutir no HTML com nitidez."""
    caminhos = [
        Path("assets/yara_icone.png"),
        Path("src/assets/yara_icone.png"),
    ]
    for caminho in caminhos:
        if caminho.exists():
            return base64.b64encode(caminho.read_bytes()).decode("utf-8")
    return ""

LOGO_B64 = carregar_logo_base64()

# --- CSS PROFISSIONAL (ESTILO CLAUDE / GEMINI / CHATGPT) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    /* Fundo principal e tipografia (preservando ícones do Streamlit) */
    .stApp {
        background-color: #0B0F17;
        color: #E5E7EB;
    }
    html, body, p, h1, h2, h3, h4, label, input, textarea, button {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* Limpeza do topo padrão do Streamlit */
    header[data-testid="stHeader"] {
        background: transparent !important;
    }
    #MainMenu, footer {
        visibility: hidden;
    }

    /* Sidebar Minimalista */
    section[data-testid="stSidebar"] {
        background-color: #0F1522 !important;
        border-right: 1px solid #1E293B;
    }
    section[data-testid="stSidebar"] .stButton > button {
        background-color: transparent;
        color: #CBD5E1;
        border: 1px solid transparent;
        border-radius: 10px;
        text-align: left;
        justify-content: flex-start;
        padding: 0.6rem 0.9rem;
        font-weight: 500;
        transition: all 0.15s ease;
    }
    section[data-testid="stSidebar"] .stButton > button:hover {
        background-color: #1E293B;
        color: #FFFFFF;
        border-color: #334155;
    }

    /* Botão "Nova Conversa" no topo da Sidebar */
    div[data-testid="stSidebar"] div.stButton:first-of-type > button {
        background: linear-gradient(135deg, #10B981 0%, #059669 100%);
        color: #FFFFFF !important;
        font-weight: 600;
        border: none;
        box-shadow: 0 2px 10px rgba(16, 185, 129, 0.25);
        justify-content: center;
    }
    div[data-testid="stSidebar"] div.stButton:first-of-type > button:hover {
        filter: brightness(1.08);
        transform: translateY(-1px);
    }

    /* Coluna Central de Leitura (Estilo ChatGPT / Claude) */
    .block-container {
        max-width: 860px !important;
        padding-top: 2rem !important;
        padding-bottom: 6rem !important;
        margin: 0 auto !important;
    }

    /* Hero / Tela Inicial Centralizada */
    .yara-hero {
        text-align: center;
        padding: 2.5rem 1rem 1.5rem 1rem;
        animation: fadeIn 0.5s ease-out;
    }
    .yara-hero img {
        width: 84px;
        height: 84px;
        border-radius: 22px;
        margin-bottom: 1rem;
        box-shadow: 0 8px 28px rgba(16, 185, 129, 0.22);
    }
    .yara-hero h1 {
        font-size: 2.2rem;
        font-weight: 700;
        background: linear-gradient(90deg, #FFFFFF 0%, #6EE7B7 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.35rem;
    }
    .yara-hero p {
        color: #94A3B8;
        font-size: 1.05rem;
        max-width: 520px;
        margin: 0 auto;
    }

    /* Cards de Sugestão (Prompt Chips) */
    div.prompt-chip button {
        background-color: #131B2E !important;
        border: 1px solid #1E293B !important;
        border-radius: 14px !important;
        padding: 0.85rem 1rem !important;
        color: #E2E8F0 !important;
        font-size: 0.9rem !important;
        text-align: left !important;
        justify-content: flex-start !important;
        height: 100% !important;
        transition: all 0.2s ease !important;
    }
    div.prompt-chip button:hover {
        background-color: #1A253E !important;
        border-color: #10B981 !important;
        transform: translateY(-2px);
    }

    /* Mensagens do Chat */
    div[data-testid="stChatMessage"] {
        background-color: transparent !important;
        border: none !important;
        padding: 0.75rem 0 !important;
        gap: 1rem;
    }
    /* Balão sutil apenas para a mensagem do usuário */
    div[data-testid="stChatMessage"]:has(div[data-testid="stChatMessageAvatarUser"]) {
        background-color: #162033 !important;
        border: 1px solid #24324D !important;
        border-radius: 18px !important;
        padding: 0.9rem 1.2rem !important;
        margin-left: 3.5rem;
    }

    /* Input de Áudio Compacto e Integrado */
    div[data-testid="stAudioInput"] {
        background-color: #131B2E;
        border: 1px solid #24324D;
        border-radius: 16px;
        padding: 0.35rem 0.75rem;
    }
    div[data-testid="stAudioInput"] label {
        font-size: 0.82rem !important;
        color: #94A3B8 !important;
    }

    /* Caixa de Chat Inferior */
    div[data-testid="stChatInput"] {
        background-color: #131B2E !important;
        border: 1px solid #283754 !important;
        border-radius: 24px !important;
    }
    div[data-testid="stChatInput"]:focus-within {
        border-color: #10B981 !important;
        box-shadow: 0 0 0 2px rgba(16, 185, 129, 0.2) !important;
    }

    /* Player de Áudio Discreto */
    audio {
        height: 36px;
        border-radius: 10px;
        margin-top: 6px;
    }

    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(8px); }
        to { opacity: 1; transform: translateY(0); }
    }
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def inicializar_motores():
    return LLMEngine(), SpeechEngine()

llm, stt = inicializar_motores()

# --- CONTROLE DE ESTADO ---
if "pagina_atual" not in st.session_state:
    st.session_state.pagina_atual = "chat"
if "mensagens_geral" not in st.session_state:
    st.session_state.mensagens_geral = []

# --- BARRA LATERAL ---
with st.sidebar:
    st.markdown("### 🌿 Yara IA")
    st.caption("Assistente Educacional • PET UFOPA")

    if st.button("＋ Nova conversa", use_container_width=True):
        st.session_state.mensagens_geral = []
        st.session_state.pagina_atual = "chat"
        st.rerun()

    st.markdown("<div style='height: 12px'></div>", unsafe_allow_html=True)
    st.caption("MÓDULOS DE APRENDIZAGEM")

    menu_itens = [
        ("💬", "Conversa Geral", "chat"),
        ("🗣️", "Alfabetização por Voz", "alfabetizacao"),
        ("🩺", "Saúde e Bem-Estar", "saude"),
        ("🌱", "Educação Ambiental", "ambiental"),
        ("🛶", "Cultura e História", "cultura"),
    ]

    for icone, titulo, chave in menu_itens:
        ativo = st.session_state.pagina_atual == chave
        prefixo = "▸ " if ativo else ""
        if st.button(f"{prefixo}{icone}  {titulo}", key=f"nav_{chave}", use_container_width=True):
            st.session_state.pagina_atual = chave
            st.rerun()

    st.divider()
    st.caption("CONFIGURAÇÕES")
    perfil = st.radio(
        "Perfil de uso:",
        ["Aluno / Comunidade", "Professor / Monitor"],
        label_visibility="collapsed"
    )
    ativar_voz_chat = st.toggle("🔊 Ler respostas em voz alta", value=True)

    st.markdown("<div style='height: 20px'></div>", unsafe_allow_html=True)
    st.caption(f"⚡ Modelo ativo: `{llm.modelo_ativo}`")

# --- FUNÇÃO AUXILIAR PARA ENVIAR PERGUNTA NO CHAT ---
def processar_pergunta_chat(pergunta: str):
    st.session_state.mensagens_geral.append({"role": "user", "content": pergunta})
    with st.spinner("Yara está formulando a resposta..."):
        resposta = llm.gerar_resposta(st.session_state.mensagens_geral, modo="geral")
        audio_resp = sintetizar_voz(resposta) if ativar_voz_chat else None
    st.session_state.mensagens_geral.append({
        "role": "assistant",
        "content": resposta,
        "audio": audio_resp
    })
    st.rerun()

# --- ROTEAMENTO DAS TELAS ---
if st.session_state.pagina_atual == "chat":
    avatar_yara = "assets/yara_icone.png" if Path("assets/yara_icone.png").exists() else "🌿"

    # 1. TELA INICIAL (ESTILO GEMINI / CLAUDE) QUANDO NÃO HÁ MENSAGENS
    if not st.session_state.mensagens_geral:
        img_html = (
            f'<img src="data:image/png;base64,{LOGO_B64}" alt="Yara">'
            if LOGO_B64 else '<div style="font-size: 3.5rem;">🌿</div>'
        )
        st.markdown(f"""
        <div class="yara-hero">
            {img_html}
            <h1>Olá! Eu sou a Yara</h1>
            <p>Sua assistente virtual da Amazônia. Pergunte por texto ou use o microfone para conversar comigo.</p>
        </div>
        """, unsafe_allow_html=True)

        # Sugestões rápidas clicáveis (Prompt Chips)
        sugestoes = [
            ("💧", "Como tratar a água do rio para beber com segurança?"),
            ("📖", "Quero treinar leitura e aprender novas palavras"),
            ("🐍", "Me conte a lenda amazônica da Cobra Grande"),
            ("🌱", "Como evitar queimadas e proteger o solo da roça?"),
        ]
        col1, col2 = st.columns(2)
        for idx, (ico, texto_sug) in enumerate(sugestoes):
            coluna = col1 if idx % 2 == 0 else col2
            with coluna:
                st.markdown('<div class="prompt-chip">', unsafe_allow_html=True)
                if st.button(f"{ico}  {texto_sug}", key=f"chip_{idx}", use_container_width=True):
                    processar_pergunta_chat(texto_sug)
                st.markdown('</div>', unsafe_allow_html=True)

    # 2. HISTÓRICO DA CONVERSA ATIVA
    else:
        for msg in st.session_state.mensagens_geral:
            avatar = avatar_yara if msg["role"] == "assistant" else "🧑"
            with st.chat_message(msg["role"], avatar=avatar):
                st.markdown(msg["content"])
                if msg.get("audio"):
                    st.audio(msg["audio"], format="audio/mp3")

    # 3. BARRA DE ENTRADA UNIFICADA (ÁUDIO + TEXTO)
    st.markdown("<div style='height: 16px'></div>", unsafe_allow_html=True)
    audio_chat = st.audio_input("🎙️ Prefere falar? Grave sua pergunta:", key="mic_geral")
    texto_chat = st.chat_input("Envie uma mensagem para a Yara...")

    if audio_chat is not None:
        audio_bytes = audio_chat.getvalue()
        if st.session_state.get("ultimo_audio_geral") != audio_bytes:
            st.session_state.ultimo_audio_geral = audio_bytes
            with st.spinner("Ouvindo sua mensagem..."):
                transcricao = stt.transcrever_audio(audio_bytes)
            if transcricao:
                processar_pergunta_chat(transcricao)

    if texto_chat:
        processar_pergunta_chat(texto_chat)

elif st.session_state.pagina_atual == "alfabetizacao":
    render_modulo_alfabetizacao(llm, stt)

elif st.session_state.pagina_atual == "saude":
    render_modulo_audiovisual(
        chave_modulo="saude",
        titulo_pagina="🩺 Saúde e Bem-Estar",
        subtitulo="Vídeos educativos sobre prevenção de doenças, higiene da água e saúde comunitária.",
        llm=llm
    )

elif st.session_state.pagina_atual == "ambiental":
    render_modulo_audiovisual(
        chave_modulo="ambiental",
        titulo_pagina="🌱 Educação Ambiental",
        subtitulo="Preservação da Amazônia, rios voadores e práticas sustentáveis na comunidade.",
        llm=llm
    )

elif st.session_state.pagina_atual == "cultura":
    render_modulo_audiovisual(
        chave_modulo="cultura",
        titulo_pagina="🛶 Cultura e História",
        subtitulo="Lendas amazônicas, folclore regional e memórias das comunidades ribeirinhas.",
        llm=llm
    )