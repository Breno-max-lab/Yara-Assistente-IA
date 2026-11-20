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
    """Renderiza a tela minimalista estilo ChatGPT Voice com orbe verde-esmeralda pulsante."""
    fala_js = json.dumps(fala_yara)
    audio_html = (
        f'<audio id="yara_voice_{msg_idx}" src="data:audio/mp3;base64,{audio_b64}" preload="auto"></audio>'
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

        .orb-container {{
            position: relative;
            width: 170px;
            height: 170px;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 24px;
            cursor: pointer;
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
            animation: voiceWave 0.7s ease-in-out infinite alternate;
            box-shadow:
                0 0 55px rgba(52, 211, 153, 0.9),
                0 0 95px rgba(16, 185, 129, 0.45),
                inset 0 -10px 20px rgba(6, 78, 59, 0.6);
        }}
        @keyframes idleFloat {{
            0%, 100% {{ transform: scale(0.97); }}
            50% {{ transform: scale(1.03); }}
        }}
        @keyframes voiceWave {{
            0% {{ transform: scale(0.95); border-radius: 50%; }}
            50% {{ transform: scale(1.09); border-radius: 48% 52% 50% 50%; }}
            100% {{ transform: scale(1.14); border-radius: 50%; }}
        }}

        .giant-letter {{
            font-size: 68px;
            font-weight: 800;
            color: #FFFFFF;
            letter-spacing: 0.08em;
            line-height: 1;
            margin-bottom: 12px;
            text-shadow: 0 4px 20px rgba(16, 185, 129, 0.4);
        }}

        .voice-status {{
            font-size: 14px;
            font-weight: 500;
            color: #94A3B8;
            margin-bottom: 20px;
        }}
        .voice-status.active {{
            color: #6EE7B7;
        }}

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
            <div class="orb-container" onclick="tocarNovamente_{msg_idx}()" title="Toque para ouvir">
                <div class="emerald-orb" id="orb_{msg_idx}"></div>
            </div>

            <div class="giant-letter">{foco_visual}</div>
            <div class="voice-status" id="status_{msg_idx}">Toque no microfone abaixo para responder</div>

            <button class="listen-again-btn" onclick="tocarNovamente_{msg_idx}()">
                🔊 Ouvir a Professora Yara
            </button>
        </div>

        <script>
            const textoFala = {fala_js};
            const aud = document.getElementById('yara_voice_{msg_idx}');
            const orb = document.getElementById('orb_{msg_idx}');
            const statusTxt = document.getElementById('status_{msg_idx}');

            function iniciarAnimacaoFala() {{
                orb.classList.add('speaking');
                statusTxt.classList.add('active');
                statusTxt.innerText = 'Professora Yara está falando...';
            }}

            function pararAnimacaoFala() {{
                orb.classList.remove('speaking');
                statusTxt.classList.remove('active');
                statusTxt.innerText = 'Sua vez! Aperte o microfone para falar';
            }}

            function falarViaNavegador() {{
                if (!('speechSynthesis' in window)) return;
                window.speechSynthesis.cancel();
                const utter = new SpeechSynthesisUtterance(textoFala);
                utter.lang = 'pt-BR';
                utter.rate = 0.96;
                utter.pitch = 1.08;
                utter.onstart = iniciarAnimacaoFala;
                utter.onend = pararAnimacaoFala;
                utter.onerror = pararAnimacaoFala;
                window.speechSynthesis.speak(utter);
            }}

            function tocarNovamente_{msg_idx}() {{
                if (aud) {{
                    aud.currentTime = 0;
                    const promessa = aud.play();
                    if (promessa !== undefined) {{
                        promessa.catch(() => {{
                            falarViaNavegador();
                        }});
                    }}
                }} else {{
                    falarViaNavegador();
                }}
            }}

            if (aud) {{
                aud.onplay = iniciarAnimacaoFala;
                aud.onended = pararAnimacaoFala;
                aud.onpause = pararAnimacaoFala;
            }}

            window.addEventListener('load', () => {{
                setTimeout(() => {{
                    tocarNovamente_{msg_idx}();
                }}, 100);
            }});
        </script>
    </body>
    </html>
    """
    components.html(html_code, height=430)


def render_modulo_alfabetizacao(llm: LLMEngine, stt: SpeechEngine):
    if "hist_alfabetizacao" not in st.session_state:
        abertura_bruta = (
            "FOCO: A\n"
            "Oi, que alegria ter você na minha escolinha! Eu sou a professora Yara e vamos brincar de descobrir as letras. "
            "Olha essa letra grandona brilhando na tela: é a letra A, de Arara e Açaí! "
            "Aperta o microfone aqui embaixo e abre bem a boca para falar comigo: Aaaa!"
        )
        foco, fala = _extrair_foco_e_fala(abertura_bruta)
        audio_bytes = sintetizar_voz(fala)
        audio_b64 = base64.b64encode(audio_bytes).decode("utf-8") if audio_bytes else None

        st.session_state.hist_alfabetizacao = [{"role": "assistant", "content": abertura_bruta}]
        st.session_state.alfab_visual = {
            "foco": foco,
            "fala": fala,
            "audio_b64": audio_b64,
            "turno": 1,
            "ultima_fala_aluno": ""
        }

    visual = st.session_state.alfab_visual

    _render_orbe_chatgpt_voice(
        fala_yara=visual["fala"],
        foco_visual=visual["foco"],
        audio_b64=visual["audio_b64"],
        msg_idx=visual["turno"]
    )

    col_mic, col_close = st.columns([4, 1])
    with col_mic:
        audio_aluno = st.audio_input(
            "🎙️ Falar com a Professora Yara",
            key=f"mic_alfab_{visual['turno']}",
            label_visibility="collapsed"
        )
    with col_close:
        if st.button("✕", help="Recomeçar brincadeira do início", use_container_width=True):
            for k in ["hist_alfabetizacao", "alfab_visual", "ultimo_audio_alfab"]:
                st.session_state.pop(k, None)
            st.rerun()

    if visual.get("ultima_fala_aluno"):
        st.caption(f"🎙️ Você falou: *\"{visual['ultima_fala_aluno']}\"*")

    if audio_aluno is not None:
        audio_bytes = audio_aluno.getvalue()
        if st.session_state.get("ultimo_audio_alfab") != audio_bytes:
            st.session_state.ultimo_audio_alfab = audio_bytes
            with st.spinner("A professora Yara está ouvindo..."):
                texto_aluno = stt.transcrever_audio(audio_bytes)

            if not texto_aluno or texto_aluno.startswith("[Erro"):
                texto_aluno = "(Não ouvi direitinho, fala mais pertinho para a professora ouvir!)"

            # Mantém o histórico enxuto (últimas 6 mensagens) para resposta instantânea
            st.session_state.hist_alfabetizacao.append({"role": "user", "content": texto_aluno})
            historico_curto = st.session_state.hist_alfabetizacao[-6:]

            with st.spinner("..."):
                resposta_bruta = llm.gerar_resposta(
                    historico_curto,
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
                "turno": visual["turno"] + 1,
                "ultima_fala_aluno": texto_aluno
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