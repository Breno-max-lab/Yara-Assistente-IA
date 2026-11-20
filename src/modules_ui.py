import base64
import json
from pathlib import Path
import streamlit as st
import streamlit.components.v1 as components
from src.llm_engine import LLMEngine
from src.speech_engine import SpeechEngine
from src.tts_engine import sintetizar_voz

DATA_PATH = Path(__file__).parent.parent / "data" / "conteudos_modulos.json"

# Trilha pedagógica progressiva (do zero absoluto até as primeiras sílabas)
TRILHA_ALFABETIZACAO = [
    {
        "foco": "A",
        "dica_whisper": "Letra A, Ah, Arara, Açaí, Água, Abelha, Amor.",
        "fala_inicial": (
            "Oi, que alegria ter você na minha escolinha! Eu sou a professora Yara. "
            "Olha essa letra grandona brilhando na tela: é a letra A, de Arara e Açaí! "
            "Aperta o microfone aqui embaixo e fala bem bonito: Arara!"
        ),
    },
    {
        "foco": "E",
        "dica_whisper": "Letra E, É, Ê, Escola, Elefante, Estrela, Escada.",
        "fala_inicial": (
            "Agora chegamos na letra E, de Estrela e Escola! "
            "Aperta o microfone e fala comigo bem forte: Estrela!"
        ),
    },
    {
        "foco": "I",
        "dica_whisper": "Letra I, Ih, Índio, Igarapé, Ilha, Igreja.",
        "fala_inicial": (
            "Olha só a letra I! Ela é fininha igual um lápis, e é a letra de Ilha e Igarapé! "
            "Fala no microfone comigo: Ilha!"
        ),
    },
    {
        "foco": "O",
        "dica_whisper": "Letra O, Ó, Ô, Onça, Ovo, Onda, Olho.",
        "fala_inicial": (
            "Essa letra redondinha igual uma bola é a letra O, de Onça e Onda do rio! "
            "Aperta o microfone e fala comigo: Onça!"
        ),
    },
    {
        "foco": "U",
        "dica_whisper": "Letra U, Uh, Urubu, Uva, Urso, Unha.",
        "fala_inicial": (
            "Chegamos na última vogal, a letra U, de Uva e Urubu! "
            "Faz biquinho e fala no microfone: Uva!"
        ),
    },
    {
        "foco": "AI",
        "dica_whisper": "Ai, Aí, juntar letras, vogais.",
        "fala_inicial": (
            "Você já conhece todas as vogais! Agora vamos juntar duas letrinhas: o A com o I faz AI! "
            "Igual quando a gente dá uma topadinha no pé e fala: Ai! Tenta falar no microfone: Ai!"
        ),
    },
    {
        "foco": "BA",
        "dica_whisper": "Ba, Bá, Banana, Barco, Baleia, Batata.",
        "fala_inicial": (
            "Agora vamos conhecer a família da letra B! Quando o B dá a mão para o A, faz BA, de Banana e Barco! "
            "Aperta o microfone e fala comigo: Banana!"
        ),
    },
    {
        "foco": "BO",
        "dica_whisper": "Bo, Bó, Bô, Boto, Bola, Bolo, Boca.",
        "fala_inicial": (
            "E quando o B dá a mão para o O, faz BO, de Boto cor-de-rosa e Bola! "
            "Fala no microfone para a professora ouvir: Boto!"
        ),
    },
]


def carregar_conteudos() -> dict:
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _avaliar_resposta_professora(texto_bruto: str) -> tuple[bool, str]:
    """Extrai o status (ACERTOU / TENTAR_DE_NOVO) e a fala limpa da Professora Yara."""
    linhas = [l.strip() for l in texto_bruto.strip().splitlines() if l.strip()]
    acertou = False
    fala = texto_bruto

    if linhas and linhas[0].upper().startswith("STATUS:"):
        status_str = linhas[0].split(":", 1)[1].strip().upper()
        acertou = "ACERTOU" in status_str
        fala = " ".join(linhas[1:]).strip()

    return acertou, fala


def _render_palco_professora_yara(
    fala_yara: str,
    foco_visual: str,
    estrelas: int,
    total_etapas: int,
    audio_b64: str | None,
    render_id: int,
):
    """Renderiza o orbe verde-esmeralda pulsante, estrelas de progresso e letra gigante."""
    fala_js = json.dumps(fala_yara)
    estrelas_html = "".join(
        f'<span class="star {"earned" if i < estrelas else ""}">★</span>'
        for i in range(total_etapas)
    )
    audio_tag = (
        f'<audio id="yara_aud_{render_id}" src="data:audio/mp3;base64,{audio_b64}" preload="auto"></audio>'
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
            padding: 24px 20px 26px 20px;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            text-align: center;
            box-shadow: 0 18px 45px rgba(0, 0, 0, 0.6);
        }}

        /* Barra de Estrelas estilo Google Read Along */
        .stars-bar {{
            display: flex;
            gap: 8px;
            margin-bottom: 18px;
            background: #0D131F;
            padding: 6px 16px;
            border-radius: 999px;
            border: 1px solid #1E293B;
        }}
        .star {{
            font-size: 20px;
            color: #263244;
            transition: all 0.3s ease;
        }}
        .star.earned {{
            color: #FBBF24;
            text-shadow: 0 0 12px rgba(251, 191, 36, 0.75);
            transform: scale(1.1);
        }}

        /* Orbe Verde-Esmeralda Pulsante */
        .orb-container {{
            width: 145px;
            height: 145px;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 18px;
            cursor: pointer;
        }}
        .emerald-orb {{
            width: 132px;
            height: 132px;
            border-radius: 50%;
            background:
                radial-gradient(circle at 32% 28%, rgba(236, 253, 245, 0.95) 0%, rgba(110, 231, 183, 0.85) 28%, rgba(16, 185, 129, 0.92) 60%, rgba(4, 120, 87, 1) 100%);
            box-shadow:
                0 0 34px rgba(16, 185, 129, 0.45),
                inset 0 -12px 22px rgba(6, 78, 59, 0.75);
            animation: idleFloat 3.6s ease-in-out infinite;
        }}
        .emerald-orb.speaking {{
            animation: voiceWave 0.65s ease-in-out infinite alternate;
            box-shadow:
                0 0 52px rgba(52, 211, 153, 0.9),
                0 0 90px rgba(16, 185, 129, 0.45);
        }}
        @keyframes idleFloat {{
            0%, 100% {{ transform: scale(0.97); }}
            50% {{ transform: scale(1.03); }}
        }}
        @keyframes voiceWave {{
            0% {{ transform: scale(0.94); border-radius: 50%; }}
            50% {{ transform: scale(1.09); border-radius: 47% 53% 50% 50%; }}
            100% {{ transform: scale(1.14); border-radius: 50%; }}
        }}

        /* Letra ou sílaba gigante */
        .giant-letter {{
            font-size: 72px;
            font-weight: 800;
            color: #FFFFFF;
            letter-spacing: 0.08em;
            line-height: 1;
            margin-bottom: 10px;
            text-shadow: 0 4px 20px rgba(16, 185, 129, 0.4);
        }}

        .voice-status {{
            font-size: 14px;
            font-weight: 500;
            color: #94A3B8;
            margin-bottom: 18px;
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
        {audio_tag}
        <div class="voice-stage">
            <div class="stars-bar" title="Estrelas conquistadas">{estrelas_html}</div>

            <div class="orb-container" onclick="tocarVoz_{render_id}()" title="Toque para ouvir">
                <div class="emerald-orb" id="orb_{render_id}"></div>
            </div>

            <div class="giant-letter">{foco_visual}</div>
            <div class="voice-status" id="status_{render_id}">Aperte o microfone abaixo para falar</div>

            <button class="listen-again-btn" onclick="tocarVoz_{render_id}()">
                🔊 Ouvir a Professora Yara
            </button>
        </div>

        <script>
            const falaTexto = {fala_js};
            const aud = document.getElementById('yara_aud_{render_id}');
            const orb = document.getElementById('orb_{render_id}');
            const statusTxt = document.getElementById('status_{render_id}');

            function animarInicio() {{
                orb.classList.add('speaking');
                statusTxt.classList.add('active');
                statusTxt.innerText = 'Professora Yara está falando...';
            }}

            function animarFim() {{
                orb.classList.remove('speaking');
                statusTxt.classList.remove('active');
                statusTxt.innerText = 'Sua vez! Aperte o microfone abaixo e fale';
            }}

            function fallbackVozNavegador() {{
                if (!('speechSynthesis' in window)) return;
                window.speechSynthesis.cancel();
                const u = new SpeechSynthesisUtterance(falaTexto);
                u.lang = 'pt-BR';
                u.rate = 0.96;
                u.pitch = 1.08;
                u.onstart = animarInicio;
                u.onend = animarFim;
                u.onerror = animarFim;
                window.speechSynthesis.speak(u);
            }}

            function tocarVoz_{render_id}() {{
                if (aud) {{
                    aud.currentTime = 0;
                    const p = aud.play();
                    if (p !== undefined) {{
                        p.catch(() => fallbackVozNavegador());
                    }}
                }} else {{
                    fallbackVozNavegador();
                }}
            }}

            if (aud) {{
                aud.onplay = animarInicio;
                aud.onended = animarFim;
                aud.onpause = animarFim;
            }}

            setTimeout(() => {{
                tocarVoz_{render_id}();
            }}, 120);
        </script>
    </body>
    </html>
    """
    components.html(html_code, height=430)


def _preparar_etapa(indice_etapa: int, fala_customizada: str | None = None):
    """Prepara os dados visuais e o áudio de uma etapa da trilha."""
    etapa = TRILHA_ALFABETIZACAO[indice_etapa]
    fala = fala_customizada if fala_customizada else etapa["fala_inicial"]
    audio_bytes = sintetizar_voz(fala)
    audio_b64 = base64.b64encode(audio_bytes).decode("utf-8") if audio_bytes else None

    st.session_state.alfab_estado = {
        "etapa_idx": indice_etapa,
        "foco": etapa["foco"],
        "fala": fala,
        "audio_b64": audio_b64,
        "render_id": st.session_state.get("alfab_render_seq", 0) + 1,
        "ultima_fala_aluno": "",
    }
    st.session_state.alfab_render_seq = st.session_state.alfab_estado["render_id"]


def render_modulo_alfabetizacao(llm: LLMEngine, stt: SpeechEngine):
    total_etapas = len(TRILHA_ALFABETIZACAO)

    if "alfab_estado" not in st.session_state:
        st.session_state.alfab_estrelas = 0
        _preparar_etapa(0)

    estado = st.session_state.alfab_estado
    etapa_atual = TRILHA_ALFABETIZACAO[estado["etapa_idx"]]

    # Palco principal estilo ChatGPT Voice + Estrelas Google Read Along
    _render_palco_professora_yara(
        fala_yara=estado["fala"],
        foco_visual=estado["foco"],
        estrelas=st.session_state.get("alfab_estrelas", 0),
        total_etapas=total_etapas,
        audio_b64=estado["audio_b64"],
        render_id=estado["render_id"],
    )

    # Barra de controles: Microfone grande | Pular etapa (⏭️) | Reiniciar (✕)
    col_mic, col_next, col_reset = st.columns([4, 1, 1])
    with col_mic:
        audio_aluno = st.audio_input(
            "🎙️ Falar com a Professora Yara",
            key=f"mic_alfab_{estado['render_id']}",
            label_visibility="collapsed",
        )
    with col_next:
        if st.button("⏭️", help="Ir para a próxima letra", use_container_width=True):
            proxima = (estado["etapa_idx"] + 1) % total_etapas
            _preparar_etapa(proxima)
            st.rerun()
    with col_reset:
        if st.button("✕", help="Recomeçar escolinha do início", use_container_width=True):
            st.session_state.alfab_estrelas = 0
            st.session_state.pop("ultimo_audio_alfab", None)
            _preparar_etapa(0)
            st.rerun()

    if estado.get("ultima_fala_aluno"):
        st.caption(f"🎙️ Você falou: *\"{estado['ultima_fala_aluno']}\"*")

    # Processamento da fala do aluno com guia fonético no Whisper
    if audio_aluno is not None:
        audio_bytes = audio_aluno.getvalue()
        if st.session_state.get("ultimo_audio_alfab") != audio_bytes:
            st.session_state.ultimo_audio_alfab = audio_bytes
            with st.spinner("A professora Yara está ouvindo você..."):
                texto_aluno = stt.transcrever_audio(
                    audio_bytes,
                    dica_contexto=etapa_atual["dica_whisper"],
                )

            if not texto_aluno or texto_aluno.startswith("[Erro"):
                texto_aluno = "(Não consegui ouvir bem, fale mais pertinho do microfone)"

            # Avalia se o aluno acertou a lição atual
            prompt_avaliacao = [
                {
                    "role": "user",
                    "content": (
                        f"Lição atual: Letra/Sílaba '{etapa_atual['foco']}'. "
                        f"O que a professora pediu: '{estado['fala']}'. "
                        f"O que o aluno falou no microfone: '{texto_aluno}'."
                    ),
                }
            ]
            with st.spinner("..."):
                resposta_bruta = llm.gerar_resposta(prompt_avaliacao, modo="alfabetizacao")
                acertou, fala_professora = _avaliar_resposta_professora(resposta_bruta)

            if acertou:
                st.session_state.alfab_estrelas = min(
                    total_etapas, st.session_state.get("alfab_estrelas", 0) + 1
                )
                proxima_idx = (estado["etapa_idx"] + 1) % total_etapas
                proxima_etapa = TRILHA_ALFABETIZACAO[proxima_idx]
                fala_completa = f"{fala_professora} {proxima_etapa['fala_inicial']}"
                _preparar_etapa(proxima_idx, fala_customizada=fala_completa)
            else:
                _preparar_etapa(estado["etapa_idx"], fala_customizada=fala_professora)

            st.session_state.alfab_estado["ultima_fala_aluno"] = texto_aluno
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
                    placeholder="Ex: Como faço isso na prática?",
                )
                if st.button("Perguntar à Yara", key=f"btn_{item['id']}"):
                    if pergunta.strip():
                        with st.spinner("Yara está respondendo..."):
                            contexto = f"Vídeo: {item['titulo']}. Resumo: {item['descricao']}"
                            resp = llm.gerar_resposta(
                                [{"role": "user", "content": pergunta}],
                                modo="geral",
                                contexto_extra=contexto,
                            )
                            st.success(resp)
                            audio_resp = sintetizar_voz(resp)
                            if audio_resp:
                                st.audio(audio_resp, format="audio/mp3")