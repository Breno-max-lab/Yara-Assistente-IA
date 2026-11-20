import base64
import json
from pathlib import Path
import streamlit as st
import streamlit.components.v1 as components
from src.llm_engine import LLMEngine
from src.speech_engine import SpeechEngine
from src.tts_engine import sintetizar_voz

DATA_PATH = Path(__file__).parent.parent / "data" / "conteudos_modulos.json"


def carregar_conteudos() -> dict:
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _extrair_foco_e_fala(texto_bruto: str) -> tuple[str, str]:
    """Extrai apenas a letra/sílaba gigante (FOCO:) e o texto curto que a Yara vai falar."""
    linhas = [l.strip() for l in texto_bruto.strip().splitlines() if l.strip()]
    foco = "A"
    fala = texto_bruto

    if linhas and linhas[0].upper().startswith("FOCO:"):
        foco = linhas[0].split(":", 1)[1].strip().upper()
        fala = " ".join(linhas[1:]).strip()

    return foco, fala


def _render_orbe_chatgpt_voice(fala_yara: str, foco_visual: str, audio_b64: str | None, msg_idx: int):
    """Renderiza a tela minimalista estilo ChatGPT Voice com orbe verde-esmeralda fluido."""
    audio_html = (
        f'<audio id="yara_voice_{msg_idx}" src="data:audio/mp3;base64,{audio_b64}" autoplay></audio>'
        if audio_b64 else ""
    )

    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@500;700;800&display=swap');
        body {{
            margin: 0;
            padding: 0;
            background: transparent;
            font-family: 'Inter', sans-serif;
            color: #F8FAFC;
            user-select: none;
        }}
        .voice-stage {{
            background: #05070B;
            border: 1px solid #141E2B;
            border-radius: 28px;
            padding: 36px 20px 28px 20px;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            text-align: center;
            min-height: 360px;
            box-shadow: 0 18px 45px rgba(0, 0, 0, 0.6);
        }}

        /* Círculo luminoso verde-esmeralda fluido (Estilo ChatGPT Voice) */
        .orb-container {{
            position: relative;
            width: 170px;
            height: 170px;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 24px;
        }}
        .emerald-orb {{
            width: 155px;
            height: 155px;
            border-radius: 50%;
            background:
                radial-gradient(circle at 32% 28%, rgba(236, 253, 245, 0.95) 0%, rgba(110, 231, 183, 0.85) 28%, rgba(16, 185, 129, 0.92) 60%, rgba(4, 120, 87, 1) 100%);
            box-shadow:
                0 0 38px rgba(16, 185, 129, 0.45),
                inset 0 -14px 26px rgba(6, 78, 59, 0.75);
            animation: idleFloat 3.6s ease-in-out infinite;
            transition: transform 0.25s ease, box-shadow 0.25s ease;
        }}
        .emerald-orb.speaking {{
            animation: voiceWave 0.75s ease-in-out infinite alternate;
            box-shadow:
                0 0 55px rgba(52, 211, 153, 0.85),
                0 0 95px rgba(16, 185, 129, 0.4),
                inset 0 -10px 20px rgba(6, 78, 59, 0.6);
        }}
        @keyframes idleFloat {{
            0%, 100% {{ transform: scale(0.97); }}
            50% {{ transform: scale(1.03); }}
        }}
        @keyframes voiceWave {{
            0% {{ transform: scale(0.95); border-radius: 50%; }}
            50% {{ transform: scale(1.08); border-radius: 48% 52% 50% 50%; }}
            100% {{ transform: scale(1.13); border-radius: 50%; }}
        }}

        /* Letra ou sílaba gigante única para associação visual sem textos longos */
        .giant-letter {{
            font-size: 64px;
            font-weight: 800;
            color: #FFFFFF;
            letter-spacing: 0.08em;
            line-height: 1;
            margin-bottom: 12px;
            text-shadow: 0 4px 20px rgba(16, 185, 129, 0.35);
        }}

        /* Indicador simples de estado */
        .voice-status {{
            font-size: 14px;
            font-weight: 500;
            color: #94A3B8;
            margin-bottom: 20px;
        }}
        .voice-status.active {{
            color: #6EE7B7;
        }}

        /* Botão discreto para repetir o áudio */
        .listen-again-btn {{
            background: #111827;
            color: #E2E8F0;
            border: 1px solid #1F2937;
            border-radius: 999px;
            padding: 10px 22px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            gap: 8px;
            transition: all 0.2s ease;
        }}
        .listen-again-btn:hover {{
            background: #10B981;
            color: #042F2E;
            border-color: #10B981;
        }}
    </style>
    </head>
    <body>
        {audio_html}
        <div class="voice-stage">
            <div class="orb-container">
                <div class="emerald-orb" id="orb_{msg_idx}"></div>
            </div>

            <div class="giant-letter">{foco_visual}</div>
            <div class="voice-status" id="status_{msg_idx}">Toque no microfone abaixo para falar</div>

            <button class="listen-again-btn" onclick="tocarNovamente_{msg_idx}()">
                🔊 Ouvir novamente
            </button>
        </div>

        <script>
            const aud = document.getElementById('yara_voice_{msg_idx}');
            const orb = document.getElementById('orb_{msg_idx}');
            const statusTxt = document.getElementById('status_{msg_idx}');

            if (aud) {{
                aud.onplay = () => {{
                    orb.classList.add('speaking');
                    statusTxt.classList.add('active');
                    statusTxt.innerText = 'Yara está falando...';
                }};
                aud.onended = () => {{
                    orb.classList.remove('speaking');
                    statusTxt.classList.remove('active');
                    statusTxt.innerText = 'Sua vez! Aperte o microfone para responder';
                }};
                aud.onpause = () => {{
                    orb.classList.remove('speaking');
                    statusTxt.classList.remove('active');
                    statusTxt.innerText = 'Aperte o microfone para falar';
                }};
            }}

            function tocarNovamente_{msg_idx}() {{
                if (!aud) return;
                aud.currentTime = 0;
                aud.play();
            }}
        </script>
    </body>
    </html>
    """
    components.html(html_code, height=430)


def render_modulo_alfabetizacao(llm: LLMEngine, stt: SpeechEngine):
    # Inicializa a aula do zero (foco 100% auditivo e visual simples)
    if "hist_alfabetizacao" not in st.session_state:
        abertura_bruta = (
            "FOCO: A\n"
            "Olá! Eu sou a Yara e vou te ensinar a ler bem devagar, sem pressa. "
            "Olha essa letra grandona na tela: é a letra A, de Água e Açaí. "
            "Aperta o botão do microfone aqui embaixo e repete comigo: A!"
        )
        foco, fala = _extrair_foco_e_fala(abertura_bruta)
        audio_bytes = sintetizar_voz(fala)
        audio_b64 = base64.b64encode(audio_bytes).decode("utf-8") if audio_bytes else None

        st.session_state.hist_alfabetizacao = [{"role": "assistant", "content": abertura_bruta}]
        st.session_state.alfab_visual = {
            "foco": foco,
            "fala": fala,
            "audio_b64": audio_b64,
            "turno": 1
        }

    visual = st.session_state.alfab_visual

    # Palco principal estilo ChatGPT Voice (sem textos longos na tela)
    _render_orbe_chatgpt_voice(
        fala_yara=visual["fala"],
        foco_visual=visual["foco"],
        audio_b64=visual["audio_b64"],
        msg_idx=visual["turno"]
    )

    # Barra inferior limpa: Microfone grande à esquerda + Reiniciar (✕) à direita
    col_mic, col_close = st.columns([4, 1])
    with col_mic:
        audio_aluno = st.audio_input(
            "🎙️ Falar com a Yara",
            key=f"mic_alfab_{visual['turno']}",
            label_visibility="collapsed"
        )
    with col_close:
        if st.button("✕", help="Recomeçar aula do início", use_container_width=True):
            for k in ["hist_alfabetizacao", "alfab_visual", "ultimo_audio_alfab"]:
                st.session_state.pop(k, None)
            st.rerun()

    # Processamento rápido do áudio do aluno
    if audio_aluno is not None:
        audio_bytes = audio_aluno.getvalue()
        if st.session_state.get("ultimo_audio_alfab") != audio_bytes:
            st.session_state.ultimo_audio_alfab = audio_bytes
            with st.spinner("Ouvindo..."):
                texto_aluno = stt.transcrever_audio(audio_bytes)

            if texto_aluno:
                st.session_state.hist_alfabetizacao.append({"role": "user", "content": texto_aluno})
                with st.spinner("..."):
                    resposta_bruta = llm.gerar_resposta(
                        st.session_state.hist_alfabetizacao,
                        modo="alfabetizacao"
                    )
                    foco, fala = _extrair_foco_e_fala(resposta_bruta)
                    audio_resp = sintetizar_voz(fala)
                    audio_b64 = base64.b64encode(audio_resp).decode("utf-8") if audio_resp else None

                st.session_state.hist_alfabetizacao.append({"role": "assistant", "content": resposta_bruta})
                st.session_state.alfab_visual = {
                    "foco": foco,
                    "fala": fala,
                    "audio_b64": audio_b64,
                    "turno": visual["turno"] + 1
                }
                st.rerun()


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