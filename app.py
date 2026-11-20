import base64
from pathlib import Path
import streamlit as st
import streamlit.components.v1 as components
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
    caminhos = [
        Path("assets/yara_icone.png"),
        Path("src/assets/yara_icone.png"),
    ]
    for caminho in caminhos:
        if caminho.exists():
            return base64.b64encode(caminho.read_bytes()).decode("utf-8")
    return ""

LOGO_B64 = carregar_logo_base64()

# --- CSS PROFISSIONAL (ESTILO GEMINI / CLAUDE / CHATGPT) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    .stApp {
        background-color: #0B0F17;
        color: #E5E7EB;
    }
    html, body, p, h1, h2, h3, h4, label, input, textarea, button {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

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

    /* Botão Nova Conversa */
    div[data-testid="stSidebar"] div.stButton:first-of-type > button {
        background: linear-gradient(135deg, #10B981 0%, #059669 100%);
        color: #FFFFFF !important;
        font-weight: 600;
        border: none;
        box-shadow: 0 2px 10px rgba(16, 185, 129, 0.25);
        justify-content: center;
    }

    /* Coluna Central */
    .block-container {
        max-width: 820px !important;
        padding-top: 2rem !important;
        padding-bottom: 6.5rem !important;
        margin: 0 auto !important;
    }

    /* Hero / Tela Inicial */
    .yara-hero {
        text-align: center;
        padding: 2.5rem 1rem 1.5rem 1rem;
        animation: fadeIn 0.4s ease-out;
    }
    .yara-hero img {
        width: 82px;
        height: 82px;
        border-radius: 22px;
        margin-bottom: 1rem;
        box-shadow: 0 8px 28px rgba(16, 185, 129, 0.22);
    }
    .yara-hero h1 {
        font-size: 2.15rem;
        font-weight: 700;
        background: linear-gradient(90deg, #FFFFFF 0%, #6EE7B7 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.35rem;
    }
    .yara-hero p {
        color: #94A3B8;
        font-size: 1.02rem;
        max-width: 500px;
        margin: 0 auto;
    }

    /* Prompt Chips */
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
        padding: 0.65rem 0 !important;
        gap: 0.9rem;
    }
    div[data-testid="stChatMessage"]:has(div[data-testid="stChatMessageAvatarUser"]) {
        background-color: #162033 !important;
        border: 1px solid #24324D !important;
        border-radius: 18px !important;
        padding: 0.85rem 1.15rem !important;
        margin-left: 3.5rem;
    }

    /* Barra de Entrada Unificada (Estilo Gemini / ChatGPT) */
    div[data-testid="stChatInput"] {
        background-color: #131B2E !important;
        border: 1px solid #283754 !important;
        border-radius: 26px !important;
        padding: 4px 8px !important;
        box-shadow: 0 6px 24px rgba(0, 0, 0, 0.35) !important;
    }
    div[data-testid="stChatInput"]:focus-within {
        border-color: #10B981 !important;
        box-shadow: 0 0 0 2px rgba(16, 185, 129, 0.22) !important;
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

# --- COMPONENTE DE BARRA DE ÍCONES ABAIXO DA RESPOSTA (ESTILO GEMINI/CHATGPT) ---
def render_barra_acoes_resposta(texto: str, audio_b64: str | None, msg_id: int, auto_tocar: bool = False):
    """Renderiza ícones compactos (Ouvir, Copiar, Gostei, Não gostei) sem barra gigante."""
    texto_escapado = (
        texto.replace("\\", "\\\\")
        .replace("`", "\\`")
        .replace("$", "\\$")
        .replace("\n", "\\n")
    )
    audio_tag = (
        f'<audio id="aud_{msg_id}" src="data:audio/mp3;base64,{audio_b64}" {"autoplay" if auto_tocar else ""}></audio>'
        if audio_b64 else ""
    )
    btn_audio_html = (
        f"""
        <button class="act-btn" id="btn_play_{msg_id}" onclick="toggleAudio_{msg_id}()" title="Ouvir resposta">
            <svg id="ico_play_{msg_id}" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon>
                <path d="M15.54 8.46a5 5 0 0 1 0 7.07"></path>
                <path d="M19.07 4.93a10 10 0 0 1 0 14.14"></path>
            </svg>
            <span id="lbl_play_{msg_id}">Ouvir</span>
        </button>
        """
        if audio_b64 else ""
    )

    html_acoes = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <style>
        body {{
            margin: 0;
            padding: 2px 0;
            background: transparent;
            font-family: 'Inter', sans-serif;
        }}
        .actions-bar {{
            display: flex;
            align-items: center;
            gap: 6px;
        }}
        .act-btn {{
            display: inline-flex;
            align-items: center;
            gap: 5px;
            background: transparent;
            border: none;
            color: #94A3B8;
            padding: 5px 8px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 12.5px;
            transition: all 0.15s ease;
        }}
        .act-btn:hover {{
            background: #1E293B;
            color: #F8FAFC;
        }}
        .act-btn.active {{
            color: #10B981;
            background: rgba(16, 185, 129, 0.12);
        }}
    </style>
    </head>
    <body>
        {audio_tag}
        <div class="actions-bar">
            {btn_audio_html}
            <button class="act-btn" id="btn_copy_{msg_id}" onclick="copiarTexto_{msg_id}()" title="Copiar resposta">
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                    <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                </svg>
                <span id="lbl_copy_{msg_id}">Copiar</span>
            </button>
            <button class="act-btn" id="btn_like_{msg_id}" onclick="marcarFeedback_{msg_id}('like')" title="Boa resposta">
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3"></path>
                </svg>
            </button>
            <button class="act-btn" id="btn_dislike_{msg_id}" onclick="marcarFeedback_{msg_id}('dislike')" title="Pode melhorar">
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M10 15v4a3 3 0 0 0 3 3l4-9V2H5.72a2 2 0 0 0-2 1.7l-1.38 9a2 2 0 0 0 2 2.3zm7-13h2.67A2.31 2.31 0 0 1 22 4v7a2.31 2.31 0 0 1-2.33 2H17"></path>
                </svg>
            </button>
        </div>
        <script>
            const aud = document.getElementById('aud_{msg_id}');
            const btnPlay = document.getElementById('btn_play_{msg_id}');
            const lblPlay = document.getElementById('lbl_play_{msg_id}');

            if (aud) {{
                aud.onplay = () => {{
                    btnPlay.classList.add('active');
                    lblPlay.innerText = 'Pausar';
                }};
                aud.onpause = () => {{
                    btnPlay.classList.remove('active');
                    lblPlay.innerText = 'Ouvir';
                }};
                aud.onended = () => {{
                    btnPlay.classList.remove('active');
                    lblPlay.innerText = 'Ouvir';
                }};
            }}

            function toggleAudio_{msg_id}() {{
                if (!aud) return;
                if (aud.paused) {{
                    aud.play();
                }} else {{
                    aud.pause();
                }}
            }}

            function copiarTexto_{msg_id}() {{
                navigator.clipboard.writeText(`{texto_escapado}`);
                const lbl = document.getElementById('lbl_copy_{msg_id}');
                const btn = document.getElementById('btn_copy_{msg_id}');
                lbl.innerText = 'Copiado!';
                btn.classList.add('active');
                setTimeout(() => {{
                    lbl.innerText = 'Copiar';
                    btn.classList.remove('active');
                }}, 1800);
            }}

            function marcarFeedback_{msg_id}(tipo) {{
                document.getElementById('btn_like_{msg_id}').classList.remove('active');
                document.getElementById('btn_dislike_{msg_id}').classList.remove('active');
                document.getElementById('btn_' + tipo + '_{msg_id}').classList.add('active');
            }}
        </script>
    </body>
    </html>
    """
    components.html(html_acoes, height=36)

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
    tocar_automatico = st.toggle("🔊 Falar resposta automaticamente", value=False)

    st.markdown("<div style='height: 20px'></div>", unsafe_allow_html=True)
    st.caption(f"⚡ Modelo ativo: `{llm.modelo_ativo}`")

# --- PROCESSAMENTO DA PERGUNTA ---
def processar_pergunta_chat(pergunta: str):
    st.session_state.mensagens_geral.append({"role": "user", "content": pergunta})
    with st.spinner("Yara está pensando..."):
        resposta = llm.gerar_resposta(st.session_state.mensagens_geral, modo="geral")
        audio_bytes = sintetizar_voz(resposta)
        audio_b64 = base64.b64encode(audio_bytes).decode("utf-8") if audio_bytes else None

    st.session_state.mensagens_geral.append({
        "role": "assistant",
        "content": resposta,
        "audio_b64": audio_b64,
        "auto_tocar": tocar_automatico
    })
    st.rerun()

# --- ROTEAMENTO DAS TELAS ---
if st.session_state.pagina_atual == "chat":
    avatar_yara = "assets/yara_icone.png" if Path("assets/yara_icone.png").exists() else "🌿"

    # 1. TELA INICIAL (ESTILO GEMINI / CLAUDE)
    if not st.session_state.mensagens_geral:
        img_html = (
            f'<img src="data:image/png;base64,{LOGO_B64}" alt="Yara">'
            if LOGO_B64 else '<div style="font-size: 3.5rem;">🌿</div>'
        )
        st.markdown(f"""
        <div class="yara-hero">
            {img_html}
            <h1>Olá! Eu sou a Yara</h1>
            <p>Sua assistente virtual da Amazônia. Pergunte digitando ou toque no microfone na barra abaixo.</p>
        </div>
        """, unsafe_allow_html=True)

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

    # 2. CONVERSA ATIVA
    else:
        total_msgs = len(st.session_state.mensagens_geral)
        for idx, msg in enumerate(st.session_state.mensagens_geral):
            avatar = avatar_yara if msg["role"] == "assistant" else "🧑"
            with st.chat_message(msg["role"], avatar=avatar):
                st.markdown(msg["content"])
                if msg["role"] == "assistant":
                    # Só toca automaticamente se for a última mensagem recém-chegada
                    deve_tocar = msg.get("auto_tocar", False) and (idx == total_msgs - 1)
                    render_barra_acoes_resposta(
                        texto=msg["content"],
                        audio_b64=msg.get("audio_b64"),
                        msg_id=idx,
                        auto_tocar=deve_tocar
                    )

    # 3. BARRA DE ENTRADA UNIFICADA (TEXTO + MICROFONE NA MESMA BARRA)
    entrada = st.chat_input(
        "Peça à Yara...",
        accept_audio=True,
        audio_sample_rate=16000
    )

    if entrada:
        # Caso o usuário tenha gravado áudio pelo microfone da barra
        if getattr(entrada, "audio", None) is not None:
            audio_bytes = entrada.audio.getvalue()
            with st.spinner("Ouvindo sua pergunta..."):
                transcricao = stt.transcrever_audio(audio_bytes)
            if transcricao:
                processar_pergunta_chat(transcricao)
        # Caso o usuário tenha digitado texto
        elif getattr(entrada, "text", None):
            processar_pergunta_chat(entrada.text)

elif st.session_state.pagina_atual == "alfabetizacao":
    render_modulo_alfabetizacao(llm, stt)

elif st.session_state.pagina_atual == "saude":
    render_modulo_audiovisual(
        chave_modulo="saude",
        titulo_pagina="🩺 Saúde e Bem-Estar",
        subtitulo="Vídeos educativos sobre prevenção de doenças, higiene da água e saúde comunitária.",
        llm=llm,
        stt=stt
    )

elif st.session_state.pagina_atual == "ambiental":
    render_modulo_audiovisual(
        chave_modulo="ambiental",
        titulo_pagina="🌱 Educação Ambiental",
        subtitulo="Preservação da Amazônia, rios voadores e práticas sustentáveis na comunidade.",
        llm=llm,
        stt=stt
    )

elif st.session_state.pagina_atual == "cultura":
    render_modulo_audiovisual(
        chave_modulo="cultura",
        titulo_pagina="🛶 Cultura e História",
        subtitulo="Lendas amazônicas, folclore regional e memórias das comunidades ribeirinhas.",
        llm=llm,
        stt=stt
    )