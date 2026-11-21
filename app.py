import base64
from pathlib import Path
from PIL import Image
import streamlit as st
import streamlit.components.v1 as components
from src.llm_engine import LLMEngine
from src.speech_engine import SpeechEngine
from src.tts_engine import sintetizar_voz
from src.rag_engine import buscar_contexto_documentos
from src.modules_ui import render_modulo_alfabetizacao, render_modulo_audiovisual
from src.professor_ui import render_painel_professor


def preparar_favicon():
    caminho = Path("assets/yara_icone.png")
    if not caminho.exists():
        return "🌿"
    try:
        img = Image.open(caminho).convert("RGBA")
        dados = img.getdata()
        nova_img = Image.new("RGBA", img.size)
        pixels = [
            (0, 0, 0, 0) if (r < 18 and g < 18 and b < 18) else (r, g, b, a)
            for r, g, b, a in dados
        ]
        nova_img.putdata(pixels)

        bbox = nova_img.getbbox()
        if bbox:
            simbolo = nova_img.crop(bbox)
            lado = max(simbolo.size)
            margem = int(lado * 0.06)
            tamanho_final = lado + margem * 2
            canvas = Image.new("RGBA", (tamanho_final, tamanho_final), (0, 0, 0, 0))
            pos_x = (tamanho_final - simbolo.width) // 2
            pos_y = (tamanho_final - simbolo.height) // 2
            canvas.paste(simbolo, (pos_x, pos_y), simbolo)
            return canvas.resize((256, 256), Image.Resampling.LANCZOS)
        return img
    except Exception:
        return str(caminho)


# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Yara • Assistente IA",
    page_icon=preparar_favicon(),
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


@st.cache_data(show_spinner=False)
def gerar_audio_apresentacao_b64() -> str:
    texto_apresentacao = (
        "Olá! Eu sou a Yara, sua assistente virtual da Amazônia. "
        "Aqui no menu ao lado você pode conversar comigo, treinar leitura na escolinha de voz, "
        "assistir vídeos sobre saúde, meio ambiente e cultura, ou escrever e falar sua dúvida na barra abaixo."
    )
    audio_bytes = sintetizar_voz(texto_apresentacao)
    return base64.b64encode(audio_bytes).decode("utf-8") if audio_bytes else ""


LOGO_B64 = carregar_logo_base64()

# --- CSS ESTILO GEMINI ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    .stApp {
        background-color: #0D0F11;
        color: #E3E5E8;
    }
    html, body, p, h1, h2, h3, h4, label, input, textarea, button {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    header[data-testid="stHeader"] {
        background: transparent !important;
    }
    [data-testid="stToolbarActions"],
    [data-testid="stDecoration"],
    [data-testid="stStatusWidget"],
    .viewerBadge_container__1QSob,
    .viewerBadge_link__1S137,
    div[class*="viewerBadge"],
    #MainMenu,
    footer {
        display: none !important;
        visibility: hidden !important;
    }

    /* =========================================================================
       BARRA LATERAL ESTILO GEMINI
       ========================================================================= */
    section[data-testid="stSidebar"] {
        background-color: #131517 !important;
        border-right: 1px solid #1E2023;
        width: 275px !important;
    }
    section[data-testid="stSidebar"] > div:first-child {
        padding-top: 0.75rem !important;
    }
    div[data-testid="stSidebarHeader"] {
        height: 1.4rem !important;
        padding: 0 0.75rem !important;
        margin-bottom: 0.15rem !important;
    }

    .gemini-brand-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0.2rem 0.65rem 1rem 0.65rem;
    }
    .gemini-brand-left {
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .gemini-brand-left img {
        width: 24px;
        height: 24px;
        border-radius: 6px;
    }
    .gemini-brand-title {
        font-size: 1.18rem;
        font-weight: 600;
        color: #E3E5E8;
        letter-spacing: -0.01em;
    }
    .gemini-badge-pet {
        font-size: 0.7rem;
        color: #8E9297;
        background: #1C1F22;
        padding: 2px 7px;
        border-radius: 6px;
        font-weight: 500;
    }

    section[data-testid="stSidebar"] .stButton {
        margin-bottom: -0.65rem !important;
    }
    section[data-testid="stSidebar"] .stButton > button {
        background-color: transparent !important;
        color: #C4C7C5 !important;
        border: none !important;
        border-radius: 999px !important;
        text-align: left !important;
        justify-content: flex-start !important;
        padding: 0.5rem 0.9rem !important;
        font-size: 0.9rem !important;
        font-weight: 400 !important;
        box-shadow: none !important;
        transition: background-color 0.15s ease, color 0.15s ease !important;
    }
    section[data-testid="stSidebar"] .stButton > button > div {
        width: 100%;
        text-align: left !important;
        justify-content: flex-start !important;
    }
    section[data-testid="stSidebar"] .stButton > button:hover {
        background-color: #1E2023 !important;
        color: #FFFFFF !important;
    }
    section[data-testid="stSidebar"] div.nav-active .stButton > button {
        background-color: #25282C !important;
        color: #FFFFFF !important;
        font-weight: 500 !important;
    }

    .sidebar-section-label {
        font-size: 0.78rem;
        font-weight: 600;
        color: #8E9297;
        padding: 1.25rem 0.9rem 0.35rem 0.9rem;
    }

    .sidebar-profile-card {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 0.55rem 0.75rem;
        border-radius: 12px;
        background-color: #191B1E;
        margin-top: 0.45rem;
    }
    .profile-avatar {
        width: 30px;
        height: 30px;
        border-radius: 50%;
        background: linear-gradient(135deg, #10B981 0%, #047857 100%);
        color: #FFFFFF;
        font-weight: 700;
        font-size: 0.85rem;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .profile-info-name {
        font-size: 0.85rem;
        font-weight: 600;
        color: #E3E5E8;
        line-height: 1.2;
    }
    .profile-info-role {
        font-size: 0.72rem;
        color: #8E9297;
    }

    /* =========================================================================
       ÁREA PRINCIPAL E MENSAGENS (LARGURA UNIFICADA COM A BARRA DE PERGUNTA)
       ========================================================================= */
    .block-container {
        max-width: 760px !important;
        padding-top: 2.8rem !important;
        padding-bottom: 6.5rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
        margin: 0 auto !important;
    }

    .yara-hero {
        text-align: center;
        padding: 2.5rem 1rem 1.2rem 1rem;
        animation: fadeIn 0.4s ease-out;
    }
    .yara-hero img {
        width: 78px;
        height: 78px;
        border-radius: 22px;
        margin-bottom: 1rem;
        box-shadow: 0 8px 28px rgba(16, 185, 129, 0.22);
    }
    .yara-hero h1 {
        font-size: 2.2rem;
        font-weight: 600;
        background: linear-gradient(90deg, #FFFFFF 0%, #6EE7B7 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.4rem;
    }
    .yara-hero p {
        color: #8E9297;
        font-size: 1.02rem;
        max-width: 490px;
        margin: 0 auto;
    }

    /* Oculta ícones de avatar nas mensagens */
    div[data-testid="stChatMessageAvatarUser"],
    div[data-testid="stChatMessageAvatarAssistant"] {
        display: none !important;
    }

    div[data-testid="stChatMessage"] {
        background-color: transparent !important;
        border: none !important;
        padding: 0.45rem 0 !important;
        gap: 0 !important;
    }

    /* Pergunta do Usuário: balão à direita */
    div[data-testid="stChatMessage"]:has(div[data-testid="stChatMessageAvatarUser"]) {
        background-color: #1E2125 !important;
        border: 1px solid #2A2E33 !important;
        border-radius: 22px 22px 6px 22px !important;
        padding: 0.75rem 1.15rem !important;
        margin-left: auto !important;
        margin-right: 0 !important;
        width: fit-content !important;
        max-width: 78% !important;
    }
    div[data-testid="stChatMessage"]:has(div[data-testid="stChatMessageAvatarUser"]) p {
        margin-bottom: 0 !important;
        color: #F8FAFC !important;
    }

    /* Resposta da Yara: texto limpo à esquerda */
    div[data-testid="stChatMessage"]:has(div[data-testid="stChatMessageAvatarAssistant"]) {
        background-color: transparent !important;
        padding: 0.6rem 0.2rem !important;
        margin-right: auto !important;
        margin-left: 0 !important;
        width: 100% !important;
    }

    /* Container inferior alinhado na mesma largura exata (760px) da área de chat */
    div[data-testid="stBottom"] {
        background-color: #0D0F11 !important;
        padding-bottom: 1rem !important;
    }
    div[data-testid="stBottom"] > div {
        background-color: #0D0F11 !important;
        max-width: 760px !important;
        margin: 0 auto !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }

    /* Retângulo externo único da barra de chat */
    div[data-testid="stChatInput"] {
        width: 100% !important;
        background-color: #16181B !important;
        border: 1px solid #2A2E33 !important;
        border-radius: 26px !important;
        padding: 8px 14px !important;
        box-shadow: 0 6px 24px rgba(0, 0, 0, 0.35) !important;
    }
    div[data-testid="stChatInput"]:focus-within {
        border-color: #10B981 !important;
    }

    div[data-testid="stChatInput"] > div,
    div[data-testid="stChatInput"] div[data-baseweb="base-input"],
    div[data-testid="stChatInput"] div[data-baseweb="textarea"],
    div[data-testid="stChatInput"] textarea {
        background-color: transparent !important;
        border: none !important;
        box-shadow: none !important;
        outline: none !important;
    }

    @media (max-width: 768px) {
        .block-container {
            padding-top: 1.5rem !important;
            padding-left: 0.85rem !important;
            padding-right: 0.85rem !important;
        }
        div[data-testid="stBottom"] > div {
            padding-left: 0.85rem !important;
            padding-right: 0.85rem !important;
        }
        .yara-hero { padding-top: 1.5rem; }
        .yara-hero h1 { font-size: 1.7rem; }
        div[data-testid="stChatMessage"]:has(div[data-testid="stChatMessageAvatarUser"]) {
            max-width: 88% !important;
        }
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


# --- BOTÃO DE BOAS-VINDAS COM VOZ NEURAL NATURAL ---
def render_botao_boas_vindas_voz():
    audio_b64 = gerar_audio_apresentacao_b64()
    if not audio_b64:
        return

    html_voz = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <style>
        body {{
            margin: 0;
            padding: 0;
            background: transparent;
            display: flex;
            justify-content: center;
            font-family: 'Inter', sans-serif;
        }}
        .welcome-voice-btn {{
            background: #16181B;
            color: #6EE7B7;
            border: 1px solid #23262A;
            border-radius: 999px;
            padding: 8px 18px;
            font-size: 13.5px;
            font-weight: 500;
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            gap: 8px;
            transition: all 0.2s ease;
        }}
        .welcome-voice-btn:hover {{
            background: #1E2125;
            border-color: #10B981;
        }}
    </style>
    </head>
    <body>
        <audio id="aud_welcome" src="data:audio/mp3;base64,{audio_b64}" preload="auto"></audio>
        <button class="welcome-voice-btn" id="btn_welcome" onclick="toggleBoasVindas()">
            🔊 Ouvir apresentação da Yara
        </button>
        <script>
            const aud = document.getElementById('aud_welcome');
            const btn = document.getElementById('btn_welcome');

            aud.onplay = () => {{ btn.innerText = '⏸️ Pausar apresentação'; }};
            aud.onpause = () => {{ btn.innerText = '🔊 Ouvir apresentação da Yara'; }};
            aud.onended = () => {{ btn.innerText = '🔊 Ouvir apresentação da Yara'; }};

            function toggleBoasVindas() {{
                if (aud.paused) {{
                    aud.play();
                }} else {{
                    aud.pause();
                }}
            }}
        </script>
    </body>
    </html>
    """
    components.html(html_voz, height=44)


# --- BARRA DE ÍCONES COMPACTA ABAIXO DA RESPOSTA ---
def render_barra_acoes_resposta(texto: str, audio_b64: str | None, msg_id: int, auto_tocar: bool = False):
    texto_escapado = (
        texto.replace("\\", "\\\\")
        .replace("`", "\\`")
        .replace("$", "\\$")
        .replace("\n", "\\n")
    )
    audio_tag = (
        f'<audio id="aud_{msg_id}" src="data:audio/mp3;base64,{audio_b64}" preload="auto" {"autoplay" if auto_tocar else ""}></audio>'
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
            color: #8E9297;
            padding: 5px 8px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 12.5px;
            transition: all 0.15s ease;
        }}
        .act-btn:hover {{
            background: #1E2023;
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
            <button class="act-btn" id="btn_play_{msg_id}" onclick="toggleAudio_{msg_id}()" title="Ouvir resposta">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon>
                    <path d="M15.54 8.46a5 5 0 0 1 0 7.07"></path>
                    <path d="M19.07 4.93a10 10 0 0 1 0 14.14"></path>
                </svg>
                <span id="lbl_play_{msg_id}">Ouvir</span>
            </button>
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

# ==============================================================================
# BARRA LATERAL ESTILO GEMINI
# ==============================================================================
with st.sidebar:
    logo_topo = (
        f'<img src="data:image/png;base64,{LOGO_B64}" alt="Yara">'
        if LOGO_B64 else '<span style="font-size:1.3rem;">🌿</span>'
    )
    st.markdown(f"""
    <div class="gemini-brand-header">
        <div class="gemini-brand-left">
            {logo_topo}
            <span class="gemini-brand-title">Yara</span>
        </div>
        <span class="gemini-badge-pet">PET • UFOPA</span>
    </div>
    """, unsafe_allow_html=True)

    if st.button("📝   Nova conversa", key="btn_nova_conversa", use_container_width=True):
        st.session_state.mensagens_geral = []
        st.session_state.pagina_atual = "chat"
        st.rerun()

    if st.session_state.mensagens_geral and st.session_state.pagina_atual != "chat":
        if st.button("💬   Voltar ao Chat", key="nav_chat", use_container_width=True):
            st.session_state.pagina_atual = "chat"
            st.rerun()

    menu_itens = [
        ("🗣️", "Alfabetização por Voz", "alfabetizacao"),
        ("🩺", "Saúde e Bem-Estar", "saude"),
        ("🌱", "Educação Ambiental", "ambiental"),
        ("🛶", "Cultura e História", "cultura"),
    ]

    for icone, titulo, chave in menu_itens:
        ativo = st.session_state.pagina_atual == chave
        if ativo:
            st.markdown('<div class="nav-active">', unsafe_allow_html=True)
        if st.button(f"{icone}   {titulo}", key=f"nav_{chave}", use_container_width=True):
            st.session_state.pagina_atual = chave
            st.rerun()
        if ativo:
            st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="sidebar-section-label">Modo de Uso</div>', unsafe_allow_html=True)
    perfil = st.radio(
        "Perfil de uso:",
        ["Aluno / Comunidade", "Professor / Monitor"],
        label_visibility="collapsed"
    )

    if perfil == "Professor / Monitor":
        ativo_prof = st.session_state.pagina_atual == "professor"
        if ativo_prof:
            st.markdown('<div class="nav-active">', unsafe_allow_html=True)
        if st.button("＋   Estúdio do Professor", key="nav_professor", use_container_width=True):
            st.session_state.pagina_atual = "professor"
            st.rerun()
        if ativo_prof:
            st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<div style='height: 18px'></div>", unsafe_allow_html=True)
    tocar_automatico = st.toggle("🔊 Falar resposta automaticamente", value=False)

    nome_perfil = "Professor / Monitor" if perfil == "Professor / Monitor" else "Comunidade"
    badge_plano = "Estúdio Ativo" if perfil == "Professor / Monitor" else "Acesso Livre"
    inicial_avatar = "P" if perfil == "Professor / Monitor" else "Y"

    st.markdown(f"""
    <div class="sidebar-profile-card">
        <div class="profile-avatar">{inicial_avatar}</div>
        <div>
            <div class="profile-info-name">{nome_perfil}</div>
            <div class="profile-info-role">{badge_plano} • {llm.modelo_ativo.split('-')[0].upper()}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)


# --- PROCESSAMENTO DA PERGUNTA NO CHAT ---
def processar_pergunta_chat(pergunta: str):
    st.session_state.mensagens_geral.append({"role": "user", "content": pergunta})
    with st.spinner("Yara está pensando..."):
        contexto_rag = buscar_contexto_documentos(pergunta)
        resposta = llm.gerar_resposta(
            st.session_state.mensagens_geral,
            modo="geral",
            contexto_extra=contexto_rag,
        )
        audio_bytes = sintetizar_voz(resposta)
        audio_b64 = base64.b64encode(audio_bytes).decode("utf-8") if audio_bytes else None

    st.session_state.mensagens_geral.append({
        "role": "assistant",
        "content": resposta,
        "audio_b64": audio_b64,
        "auto_tocar": tocar_automatico,
        "usou_rag": bool(contexto_rag),
    })
    st.rerun()


# --- ROTEAMENTO DAS TELAS ---
if st.session_state.pagina_atual == "chat":
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

        render_botao_boas_vindas_voz()

    else:
        total_msgs = len(st.session_state.mensagens_geral)
        for idx, msg in enumerate(st.session_state.mensagens_geral):
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
                if msg["role"] == "assistant":
                    if msg.get("usou_rag"):
                        st.caption("📚 *Baseado nos documentos do projeto*")
                    deve_tocar = msg.get("auto_tocar", False) and (idx == total_msgs - 1)
                    render_barra_acoes_resposta(
                        texto=msg["content"],
                        audio_b64=msg.get("audio_b64"),
                        msg_id=idx,
                        auto_tocar=deve_tocar
                    )

    entrada = st.chat_input(
        "Peça à Yara...",
        accept_audio=True,
        audio_sample_rate=16000
    )

    if entrada:
        if getattr(entrada, "audio", None) is not None:
            audio_bytes = entrada.audio.getvalue()
            with st.spinner("Ouvindo sua pergunta..."):
                transcricao = stt.transcrever_audio(audio_bytes)
            if transcricao:
                processar_pergunta_chat(transcricao)
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

elif st.session_state.pagina_atual == "professor":
    render_painel_professor(llm)