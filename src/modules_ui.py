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

def _extrair_palavra_e_fala(texto_bruto: str) -> tuple[str, str, str]:
    """Separa a linha estruturada (PALAVRA / SILABAS) do texto que será falado pela Yara."""
    linhas = [l.strip() for l in texto_bruto.strip().splitlines() if l.strip()]
    palavra = "RIO"
    silabas = "RI - O"
    fala = texto_bruto

    if linhas and linhas[0].upper().startswith("PALAVRA:"):
        cabecalho = linhas[0]
        fala = " ".join(linhas[1:]).strip()
        partes = cabecalho.split("|")
        for p in partes:
            p_limpa = p.strip()
            if p_limpa.upper().startswith("PALAVRA:"):
                palavra = p_limpa.split(":", 1)[1].strip()
            elif p_limpa.upper().startswith("SILABAS:") or p_limpa.upper().startswith("SÍLABAS:"):
                silabas = p_limpa.split(":", 1)[1].strip()

    return palavra, silabas, fala

def _render_orbe_siri_alexa(fala_yara: str, palavra: str, silabas: str, audio_b64: str | None, msg_idx: int):
    """Renderiza o visual pulsante estilo Siri/Alexa com cartão grande de leitura."""
    audio_html = (
        f'<audio id="yara_voice_{msg_idx}" src="data:audio/mp3;base64,{audio_b64}" autoplay></audio>'
        if audio_b64 else ""
    )

    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@500;600;700;800&display=swap');
        body {{
            margin: 0;
            padding: 0;
            background: transparent;
            font-family: 'Inter', sans-serif;
            color: #F8FAFC;
        }}
        .assistant-stage {{
            background: radial-gradient(circle at top, #132A24 0%, #0F1624 75%);
            border: 1px solid #1E3A34;
            border-radius: 24px;
            padding: 28px 24px;
            text-align: center;
            box-shadow: 0 12px 32px rgba(0, 0, 0, 0.35);
        }}
        /* Orbe animado estilo Siri/Alexa */
        .orb-wrapper {{
            display: flex;
            justify-content: center;
            align-items: center;
            margin-bottom: 16px;
        }}
        .yara-orb {{
            width: 78px;
            height: 78px;
            border-radius: 50%;
            background: radial-gradient(circle at 30% 30%, #6EE7B7, #10B981 55%, #047857 100%);
            box-shadow: 0 0 25px rgba(16, 185, 129, 0.55), inset 0 0 14px rgba(255, 255, 255, 0.45);
            animation: breathe 3s ease-in-out infinite;
            transition: all 0.3s ease;
        }}
        .yara-orb.speaking {{
            animation: speakPulse 0.85s ease-in-out infinite alternate;
            box-shadow: 0 0 42px rgba(52, 211, 153, 0.9), 0 0 70px rgba(16, 185, 129, 0.45);
        }}
        @keyframes breathe {{
            0%, 100% {{ transform: scale(0.96); opacity: 0.88; }}
            50% {{ transform: scale(1.04); opacity: 1; }}
        }}
        @keyframes speakPulse {{
            0% {{ transform: scale(0.95); }}
            100% {{ transform: scale(1.13); }}
        }}

        .status-pill {{
            display: inline-block;
            font-size: 12px;
            font-weight: 600;
            letter-spacing: 0.06em;
            text-transform: uppercase;
            color: #6EE7B7;
            background: rgba(16, 185, 129, 0.14);
            border: 1px solid rgba(16, 185, 129, 0.3);
            padding: 4px 12px;
            border-radius: 999px;
            margin-bottom: 18px;
        }}

        /* Cartão Gigante da Palavra e Sílabas */
        .word-board {{
            background: #0B101B;
            border: 1px solid #23334D;
            border-radius: 18px;
            padding: 18px 16px;
            margin: 0 auto 20px auto;
            max-width: 440px;
        }}
        .word-main {{
            font-size: 38px;
            font-weight: 800;
            letter-spacing: 0.12em;
            color: #FFFFFF;
            margin: 0;
        }}
        .word-syllables {{
            font-size: 20px;
            font-weight: 600;
            letter-spacing: 0.14em;
            color: #34D399;
            margin-top: 6px;
        }}

        /* Legenda da fala da Yara */
        .speech-text {{
            font-size: 19px;
            line-height: 1.55;
            color: #E2E8F0;
            max-width: 620px;
            margin: 0 auto 20px auto;
            font-weight: 500;
        }}

        /* Botão grande para repetir o áudio */
        .replay-btn {{
            display: inline-flex;
            align-items: center;
            gap: 8px;
            background: #182638;
            hover: #22354D;
            color: #F8FAFC;
            border: 1px solid #2E4463;
            padding: 10px 20px;
            border-radius: 999px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s ease;
        }}
        .replay-btn:hover {{
            background: #10B981;
            border-color: #10B981;
            color: #06241B;
        }}
    </style>
    </head>
    <body>
        {audio_html}
        <div class="assistant-stage">
            <div class="orb-wrapper">
                <div class="yara-orb" id="orb_{msg_idx}"></div>
            </div>
            <div class="status-pill" id="status_{msg_idx}">🌿 Yara • Professora de Voz</div>

            <div class="word-board">
                <div class="word-main">{palavra}</div>
                <div class="word-syllables">{silabas}</div>
            </div>

            <div class="speech-text">“{fala_yara}”</div>

            <button class="replay-btn" onclick="reproduzir_{msg_idx}()">
                🔊 Ouvir a Yara novamente
            </button>
        </div>

        <script>
            const audioEl = document.getElementById('yara_voice_{msg_idx}');
            const orbEl = document.getElementById('orb_{msg_idx}');
            const statusEl = document.getElementById('status_{msg_idx}');

            if (audioEl) {{
                audioEl.onplay = () => {{
                    orbEl.classList.add('speaking');
                    statusEl.innerText = '🔊 Yara está falando...';
                }};
                audioEl.onended = () => {{
                    orbEl.classList.remove('speaking');
                    statusEl.innerText = '🎙️ Sua vez de falar abaixo';
                }};
                audioEl.onpause = () => {{
                    orbEl.classList.remove('speaking');
                    statusEl.innerText = '🌿 Yara • Professora de Voz';
                }};
            }}

            function reproduzir_{msg_idx}() {{
                if (!audioEl) return;
                audioEl.currentTime = 0;
                audioEl.play();
            }}
        </script>
    </body>
    </html>
    """
    components.html(html_code, height=415)


def render_modulo_alfabetizacao(llm: LLMEngine, stt: SpeechEngine):
    st.markdown("### 🗣️ Alfabetização por Voz")
    st.caption("Converse com a Yara como em uma chamada. Ouça a lição e toque no microfone para responder.")

    # Barra superior com nível de aprendizado e botão de reiniciar
    col_niv, col_btn = st.columns([2.5, 1])
    with col_niv:
        nivel = st.selectbox(
            "Nível da aula:",
            [
                "Nível 1: Letras e Sons Iniciais",
                "Nível 2: Sílabas e Palavras do Dia a Dia",
                "Nível 3: Leitura de Frases Curtas"
            ],
            label_visibility="collapsed"
        )
    with col_btn:
        reiniciar = st.button("🔄 Nova Lição", use_container_width=True)

    # Reinicia lição se clicar no botão ou mudar de nível
    if (
        reiniciar
        or "hist_alfabetizacao" not in st.session_state
        or st.session_state.get("nivel_alfab_atual") != nivel
    ):
        st.session_state.nivel_alfab_atual = nivel
        if "Nível 1" in nivel:
            abertura_bruta = (
                "PALAVRA: LETRA A | SILABAS: A\n"
                "Olá! Vamos começar pelo som das letras. Esta na tela é a letra A, de Açaí e Água. "
                "Você consegue repetir o som da letra A e me dizer uma palavra que começa com ela?"
            )
        elif "Nível 2" in nivel:
            abertura_bruta = (
                "PALAVRA: RIO | SILABAS: RI - O\n"
                "Olá! Vamos juntar as letras para ler a palavra RIO. O R com o I faz RI, e depois vem o O. "
                "Repita comigo a palavra RIO, ou me diga outra palavra que você conhece!"
            )
        else:
            abertura_bruta = (
                "PALAVRA: O RIO É AZUL | SILABAS: O - RI - O - É - A - ZUL\n"
                "Que bom ter você aqui! Vamos ler juntos uma frase curta: O rio é azul. "
                "Tente ler essa frase em voz alta no microfone para eu ouvir!"
            )

        palavra, silabas, fala = _extrair_palavra_e_fala(abertura_bruta)
        audio_bytes = sintetizar_voz(fala)
        audio_b64 = base64.b64encode(audio_bytes).decode("utf-8") if audio_bytes else None

        st.session_state.hist_alfabetizacao = [{"role": "assistant", "content": abertura_bruta}]
        st.session_state.alfab_visual = {
            "palavra": palavra,
            "silabas": silabas,
            "fala": fala,
            "audio_b64": audio_b64,
            "turno": 1
        }
        if reiniciar:
            st.rerun()

    # Exibe o palco estilo Siri/Alexa com a palavra em destaque
    visual = st.session_state.alfab_visual
    _render_orbe_siri_alexa(
        fala_yara=visual["fala"],
        palavra=visual["palavra"],
        silabas=visual["silabas"],
        audio_b64=visual["audio_b64"],
        msg_idx=visual["turno"]
    )

    # Área grande e acessível para o aluno falar
    st.markdown("##### 🎙️ Toque no microfone abaixo para responder à Yara:")
    audio_aluno = st.audio_input("Gravar resposta falada", key="mic_alfabetizacao", label_visibility="collapsed")

    if audio_aluno is not None:
        audio_bytes = audio_aluno.getvalue()
        if st.session_state.get("ultimo_audio_alfab") != audio_bytes:
            st.session_state.ultimo_audio_alfab = audio_bytes
            with st.spinner("Yara está ouvindo você..."):
                texto_aluno = stt.transcrever_audio(audio_bytes)

            if texto_aluno:
                st.session_state.hist_alfabetizacao.append({"role": "user", "content": texto_aluno})
                with st.spinner("Preparando próxima lição..."):
                    resposta_bruta = llm.gerar_resposta(
                        st.session_state.hist_alfabetizacao,
                        modo="alfabetizacao",
                        contexto_extra=f"Nível atual selecionado pelo aluno: {nivel}"
                    )
                    palavra, silabas, fala = _extrair_palavra_e_fala(resposta_bruta)
                    audio_resp = sintetizar_voz(fala)
                    audio_b64 = base64.b64encode(audio_resp).decode("utf-8") if audio_resp else None

                st.session_state.hist_alfabetizacao.append({"role": "assistant", "content": resposta_bruta})
                st.session_state.alfab_visual = {
                    "palavra": palavra,
                    "silabas": silabas,
                    "fala": fala,
                    "audio_b64": audio_b64,
                    "turno": visual["turno"] + 1
                }
                st.rerun()

    # Histórico recolhível para acompanhamento do professor ou familiar
    with st.expander("📖 Ver o que já praticamos nesta aula"):
        for msg in st.session_state.hist_alfabetizacao:
            if msg["role"] == "assistant":
                _, _, fala_limpa = _extrair_palavra_e_fala(msg["content"])
                st.markdown(f"**🌿 Yara:** {fala_limpa}")
            else:
                st.markdown(f"**🧑 Aluno:** {msg['content']}")


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