import base64
import json
import re
import unicodedata
from pathlib import Path
import streamlit as st
import streamlit.components.v1 as components
from src.llm_engine import LLMEngine
from src.speech_engine import SpeechEngine
from src.tts_engine import sintetizar_voz
from src.video_curadoria import (
    atualizar_catalogo_automatico,
    buscar_videos_youtube,
    gerar_ficha_pedagogica_ia,
)

DATA_PATH = Path(__file__).parent.parent / "data" / "conteudos_modulos.json"

# Trilha lúdica para não-leitores (Figura grande + Letra/Sílaba + Palavra-âncora para o Whisper)
TRILHA_ALFABETIZACAO = [
    {
        "emoji": "🦜",
        "foco": "A",
        "palavra_alvo": "ARARA",
        "aceitas": ["arara", "acai", "açaí", "agua", "água", "abelha", "amor", "avião", "aviao", "letra a"],
        "dica_whisper": "Arara, Açaí, Água, Abelha, Letra A.",
        "fala_inicial": (
            "Oi, que alegria ter você na minha escolinha! Eu sou a professora Yara. "
            "Olha o passarinho colorido e a letra A na tela: é o A de Arara! "
            "Aperta o microfone aqui embaixo e fala bem bonito: Arara!"
        ),
    },
    {
        "emoji": "⭐",
        "foco": "E",
        "palavra_alvo": "ESTRELA",
        "aceitas": ["estrela", "escola", "elefante", "escada", "espelho", "letra e"],
        "dica_whisper": "Estrela, Escola, Elefante, Escada, Letra E.",
        "fala_inicial": (
            "Agora olha essa figura brilhando junto com a letra E: é o E de Estrela! "
            "Aperta o microfone e fala comigo bem forte: Estrela!"
        ),
    },
    {
        "emoji": "🏝️",
        "foco": "I",
        "palavra_alvo": "ILHA",
        "aceitas": ["ilha", "igarape", "igarapé", "indio", "índio", "igreja", "letra i"],
        "dica_whisper": "Ilha, Igarapé, Índio, Igreja, Letra I.",
        "fala_inicial": (
            "Olha só a letra I fininha igual um lápis, junto com a Ilha no meio do rio! "
            "Fala no microfone comigo: Ilha!"
        ),
    },
    {
        "emoji": "🐆",
        "foco": "O",
        "palavra_alvo": "ONÇA",
        "aceitas": ["onca", "onça", "ovo", "onda", "olho", "orelha", "letra o"],
        "dica_whisper": "Onça, Ovo, Onda, Olho, Letra O.",
        "fala_inicial": (
            "Essa letra redondinha igual uma bola é a letra O, de Onça pintada! "
            "Aperta o microfone e fala comigo: Onça!"
        ),
    },
    {
        "emoji": "🍇",
        "foco": "U",
        "palavra_alvo": "UVA",
        "aceitas": ["uva", "urubu", "urso", "unha", "letra u"],
        "dica_whisper": "Uva, Urubu, Urso, Unha, Letra U.",
        "fala_inicial": (
            "Chegamos na última vogal, a letra U, de Uva e Urubu! "
            "Faz biquinho e fala no microfone: Uva!"
        ),
    },
    {
        "emoji": "🍌",
        "foco": "BA",
        "palavra_alvo": "BANANA",
        "aceitas": ["banana", "barco", "baleia", "batata", "bacia", "ba"],
        "dica_whisper": "Banana, Barco, Baleia, Batata, Ba.",
        "fala_inicial": (
            "Você já conhece todas as vogais! Agora quando o B dá a mão para o A, faz BA, de Banana! "
            "Aperta o microfone e fala comigo: Banana!"
        ),
    },
    {
        "emoji": "🐬",
        "foco": "BO",
        "palavra_alvo": "BOTO",
        "aceitas": ["boto", "bola", "bolo", "boca", "botina", "bo"],
        "dica_whisper": "Boto, Bola, Bolo, Boca, Bo.",
        "fala_inicial": (
            "E quando o B dá a mão para o O, faz BO, de Boto cor-de-rosa! "
            "Fala no microfone para a professora ouvir: Boto!"
        ),
    },
    {
        "emoji": "🛶",
        "foco": "CA",
        "palavra_alvo": "CANOA",
        "aceitas": ["canoa", "casa", "cachorro", "cavalo", "camisa", "ca"],
        "dica_whisper": "Canoa, Casa, Cachorro, Cavalo, Ca.",
        "fala_inicial": (
            "Para fechar com chave de ouro, o C com o A faz CA, de Canoa! "
            "Aperta o microfone e fala bem alegre: Canoa!"
        ),
    },
]


def carregar_conteudos() -> dict:
    if not DATA_PATH.exists():
        return {"saude": [], "ambiental": [], "cultura": []}
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def salvar_conteudos(dados: dict):
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)


def _extrair_thumbnail_youtube(url: str) -> str:
    padrao = r"(?:v=|\/)([0-9A-Za-z_-]{11}).*"
    match = re.search(padrao, url or "")
    if match:
        video_id = match.group(1)
        return f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"
    return "https://images.unsplash.com/photo-1518173946687-a4c8892bbd9f?auto=format&fit=crop&w=600&q=60"


# ==============================================================================
# MÓDULO 1: ALFABETIZAÇÃO POR VOZ (PROFESSORA INFANTIL + ORBE VERDE-ESMERALDA)
# ==============================================================================
def _normalizar_texto(txt: str) -> str:
    nfkd = unicodedata.normalize("NFKD", txt.lower())
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def _avaliar_resposta_professora(texto_bruto: str) -> tuple[bool, str]:
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
    emoji_visual: str,
    foco_visual: str,
    estrelas: int,
    total_etapas: int,
    audio_b64: str | None,
    render_id: int,
):
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
            padding: 22px 20px 24px 20px;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            text-align: center;
            box-shadow: 0 18px 45px rgba(0, 0, 0, 0.6);
        }}
        .stars-bar {{
            display: flex;
            gap: 8px;
            margin-bottom: 16px;
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
            transform: scale(1.12);
        }}
        .orb-container {{
            width: 130px;
            height: 130px;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 16px;
            cursor: pointer;
        }}
        .emerald-orb {{
            width: 118px;
            height: 118px;
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

        /* Associação Visual: Figura Grande + Letra Gigante */
        .visual-cue {{
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 22px;
            background: #0D131F;
            border: 1px solid #1E293B;
            border-radius: 22px;
            padding: 12px 28px;
            margin-bottom: 12px;
        }}
        .cue-emoji {{
            font-size: 58px;
            line-height: 1;
        }}
        .giant-letter {{
            font-size: 68px;
            font-weight: 800;
            color: #FFFFFF;
            letter-spacing: 0.06em;
            line-height: 1;
            text-shadow: 0 4px 20px rgba(16, 185, 129, 0.4);
        }}

        .voice-status {{
            font-size: 14px;
            font-weight: 500;
            color: #94A3B8;
            margin-bottom: 16px;
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
            <div class="stars-bar">{estrelas_html}</div>
            <div class="orb-container" onclick="tocarVoz_{render_id}()">
                <div class="emerald-orb" id="orb_{render_id}"></div>
            </div>
            <div class="visual-cue">
                <span class="cue-emoji">{emoji_visual}</span>
                <span class="giant-letter">{foco_visual}</span>
            </div>
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
            setTimeout(() => {{ tocarVoz_{render_id}(); }}, 100);
        </script>
    </body>
    </html>
    """
    components.html(html_code, height=445)


def _preparar_etapa(indice_etapa: int, fala_customizada: str | None = None):
    etapa = TRILHA_ALFABETIZACAO[indice_etapa]
    fala = fala_customizada if fala_customizada else etapa["fala_inicial"]
    audio_bytes = sintetizar_voz(fala)
    audio_b64 = base64.b64encode(audio_bytes).decode("utf-8") if audio_bytes else None

    st.session_state.alfab_estado = {
        "etapa_idx": indice_etapa,
        "emoji": etapa["emoji"],
        "foco": etapa["foco"],
        "fala": fala,
        "audio_b64": audio_b64,
        "render_id": st.session_state.get("alfab_render_seq", 0) + 1,
        "ultima_fala_aluno": "",
    }
    st.session_state.alfab_render_seq = st.session_state.alfab_estado["render_id"]


def render_modulo_alfabetizacao(llm: LLMEngine, stt: SpeechEngine):
    total_etapas = len(TRILHA_ALFABETIZACAO)

    # Tela inicial com gesto explícito para destravar o áudio no navegador
    if not st.session_state.get("alfab_iniciada", False):
        st.markdown("""
        <div style="background:#05070B; border:1px solid #141E2B; border-radius:28px; padding:48px 24px; text-align:center;">
            <div style="font-size:64px; margin-bottom:12px;">🌿🦜</div>
            <h2 style="color:#FFFFFF; margin-bottom:8px;">Escolinha de Voz da Professora Yara</h2>
            <p style="color:#94A3B8; max-width:440px; margin:0 auto 24px auto;">
                Vamos aprender os sons das letras e palavras brincando! Toque no botão abaixo para começar.
            </p>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
        if st.button("▶ Começar Aula com a Professora Yara", type="primary", use_container_width=True):
            st.session_state.alfab_iniciada = True
            st.session_state.alfab_estrelas = 0
            _preparar_etapa(0)
            st.rerun()
        return

    if "alfab_estado" not in st.session_state:
        st.session_state.alfab_estrelas = 0
        _preparar_etapa(0)

    estado = st.session_state.alfab_estado
    etapa_atual = TRILHA_ALFABETIZACAO[estado["etapa_idx"]]

    _render_palco_professora_yara(
        fala_yara=estado["fala"],
        emoji_visual=estado["emoji"],
        foco_visual=estado["foco"],
        estrelas=st.session_state.get("alfab_estrelas", 0),
        total_etapas=total_etapas,
        audio_b64=estado["audio_b64"],
        render_id=estado["render_id"],
    )

    col_mic, col_next, col_reset = st.columns([4, 1, 1])
    with col_mic:
        audio_aluno = st.audio_input(
            "🎙️ Falar com a Professora Yara",
            key=f"mic_alfab_{estado['render_id']}",
            label_visibility="collapsed",
        )
    with col_next:
        if st.button("⏭️", help="Ir para a próxima figura", use_container_width=True):
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
                texto_aluno = ""

            fala_norm = _normalizar_texto(texto_aluno)
            aceitas_norm = [_normalizar_texto(p) for p in etapa_atual["aceitas"]]
            acertou_direto = any(palavra in fala_norm for palavra in aceitas_norm if palavra)

            if acertou_direto:
                elogios = [
                    f"Ebaaa! Muito bem, você falou {etapa_atual['palavra_alvo']} direitinho e ganhou uma estrelinha!",
                    f"Isso mesmo! Parabéns, você brilhou falando {etapa_atual['palavra_alvo']}!",
                    f"Que lindo! Palmas para você, acertou {etapa_atual['palavra_alvo']} de primeira!",
                ]
                fala_professora = elogios[estado["etapa_idx"] % len(elogios)]
                acertou = True
            else:
                prompt_avaliacao = [
                    {
                        "role": "user",
                        "content": (
                            f"Lição atual: Letra/Sílaba '{etapa_atual['foco']}' (Palavra-alvo: '{etapa_atual['palavra_alvo']}'). "
                            f"O que o aluno falou no microfone: '{texto_aluno or 'silêncio'}'."
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

            st.session_state.alfab_estado["ultima_fala_aluno"] = texto_aluno or "(Áudio muito baixinho)"
            st.rerun()


# ==============================================================================
# MÓDULOS 2, 3 E 4: VITRINE AUDIOVISUAL ESTILO STREAMING + TUTOR IA POR VOZ/TEXTO
# ==============================================================================
def render_modulo_audiovisual(
    chave_modulo: str,
    titulo_pagina: str,
    subtitulo: str,
    llm: LLMEngine,
    stt: SpeechEngine | None = None,
):
    st.markdown("""
    <style>
        .hero-video-badge {
            display: inline-block;
            background: rgba(16, 185, 129, 0.16);
            color: #6EE7B7;
            border: 1px solid rgba(16, 185, 129, 0.35);
            padding: 3px 12px;
            border-radius: 999px;
            font-size: 12px;
            font-weight: 600;
            margin-bottom: 8px;
        }
        .topic-pill {
            display: inline-block;
            background: #1E293B;
            color: #CBD5E1;
            padding: 4px 10px;
            border-radius: 8px;
            font-size: 12px;
            margin-right: 6px;
            margin-bottom: 6px;
        }
        .episode-card {
            background: #111827;
            border: 1px solid #1F2937;
            border-radius: 14px;
            overflow: hidden;
            margin-bottom: 8px;
        }
        .episode-thumb {
            width: 100%;
            height: 135px;
            object-fit: cover;
            display: block;
        }
        .episode-body {
            padding: 12px;
        }
        .episode-meta {
            font-size: 11.5px;
            color: #34D399;
            font-weight: 600;
            margin-bottom: 4px;
        }
        .episode-title {
            font-size: 14.5px;
            font-weight: 700;
            color: #F8FAFC;
            line-height: 1.3;
            min-height: 38px;
        }
    </style>
    """, unsafe_allow_html=True)

    st.markdown(f"## {titulo_pagina}")
    st.caption(subtitulo)

    todos_dados = carregar_conteudos()
    conteudos = todos_dados.get(chave_modulo, [])

    with st.expander("✨ Buscar e atualizar animações automaticamente por tema"):
        col_auto1, col_auto2 = st.columns([2, 1])
        with col_auto1:
            tema_custom = st.text_input(
                "Buscar nova animação no YouTube por assunto:",
                key=f"busca_auto_{chave_modulo}",
                placeholder="Ex: animação lenda da mandioca, higiene das mãos, queimadas...",
                label_visibility="collapsed",
            )
        with col_auto2:
            if st.button("🔍 Buscar e Adicionar", key=f"btn_busca_{chave_modulo}", use_container_width=True):
                if tema_custom.strip():
                    with st.spinner("Buscando animação e criando ficha educativa com a Yara..."):
                        encontrados = buscar_videos_youtube(f"animação educativa {tema_custom}", limite=1)
                        if encontrados:
                            ficha = gerar_ficha_pedagogica_ia(llm, encontrados[0], "Busca Temática", chave_modulo)
                            todos_dados.setdefault(chave_modulo, []).insert(0, ficha)
                            salvar_conteudos(todos_dados)
                            st.session_state[f"video_ativo_{chave_modulo}"] = ficha["id"]
                            st.success(f"Vídeo '{ficha['titulo']}' adicionado!")
                            st.rerun()
                        else:
                            st.warning("Não encontrei vídeos para esse termo. Tente palavras mais simples.")

        if st.button(
            "🔄 Renovar catálogo completo deste módulo automaticamente",
            key=f"renovar_tudo_{chave_modulo}",
            use_container_width=True,
        ):
            with st.spinner("A Yara está selecionando novas animações para todas as categorias deste módulo..."):
                novos = atualizar_catalogo_automatico(llm, chave_modulo)
                if novos:
                    todos_dados[chave_modulo] = novos
                    salvar_conteudos(todos_dados)
                    st.session_state[f"video_ativo_{chave_modulo}"] = novos[0]["id"]
                    st.success("Catálogo atualizado com vídeos reais e fichas geradas pela IA!")
                    st.rerun()

    if not conteudos:
        st.info("Nenhum vídeo cadastrado neste módulo ainda. Use o botão acima para preencher automaticamente!")
        return

    categorias = ["Todos"] + sorted(list({item["categoria"] for item in conteudos}))
    col_filtro, col_info_qtd = st.columns([2, 3])
    with col_filtro:
        cat_escolhida = st.selectbox(
            "Filtrar por tema:",
            categorias,
            key=f"filtro_{chave_modulo}",
            label_visibility="collapsed",
        )
    with col_info_qtd:
        st.markdown(
            f"<p style='color:#94A3B8; font-size:13px; padding-top:8px;'>🎬 {len(conteudos)} animações e vídeos disponíveis</p>",
            unsafe_allow_html=True,
        )

    lista_filtrada = (
        conteudos if cat_escolhida == "Todos"
        else [c for c in conteudos if c["categoria"] == cat_escolhida]
    )

    chave_selecao = f"video_ativo_{chave_modulo}"
    ids_validos = [v["id"] for v in lista_filtrada]
    if chave_selecao not in st.session_state or st.session_state[chave_selecao] not in ids_validos:
        st.session_state[chave_selecao] = lista_filtrada[0]["id"]

    video_atual = next(v for v in lista_filtrada if v["id"] == st.session_state[chave_selecao])

    with st.container(border=True):
        col_player, col_detalhes = st.columns([1.45, 1])

        with col_player:
            st.video(video_atual["video_url"])

        with col_detalhes:
            st.markdown(
                f'<span class="hero-video-badge">▶ {video_atual["categoria"]} • ⏱️ {video_atual["duracao"]}</span>',
                unsafe_allow_html=True,
            )
            st.markdown(f"### {video_atual['titulo']}")
            st.write(video_atual["descricao"])

            tags_html = "".join(
                f'<span class="topic-pill">✓ {topico}</span>'
                for topico in video_atual.get("topicos_chave", [])
            )
            st.markdown(tags_html, unsafe_allow_html=True)

            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
            if st.button("🔊 Ouvir resumo explicado pela Yara", key=f"ler_resumo_{video_atual['id']}", use_container_width=True):
                with st.spinner("Preparando áudio..."):
                    texto_leitura = f"{video_atual['titulo']}. {video_atual['descricao']}"
                    aud_resumo = sintetizar_voz(texto_leitura)
                    if aud_resumo:
                        st.audio(aud_resumo, format="audio/mp3", autoplay=True)

        st.divider()

        st.markdown("#### 🌿 Converse com a Yara sobre este vídeo")

        chave_chat_vid = f"chat_vid_{video_atual['id']}"
        if chave_chat_vid not in st.session_state:
            st.session_state[chave_chat_vid] = None

        def responder_duvida_video(duvida_usuario: str):
            contexto_vid = (
                f"O usuário está assistindo ao vídeo educativo '{video_atual['titulo']}' "
                f"(Categoria: {video_atual['categoria']}). "
                f"Resumo do vídeo: {video_atual['descricao']}. "
                f"Pontos principais: {', '.join(video_atual.get('topicos_chave', []))}."
            )
            with st.spinner("Yara está respondendo..."):
                resp_txt = llm.gerar_resposta(
                    [{"role": "user", "content": duvida_usuario}],
                    modo="geral",
                    contexto_extra=contexto_vid,
                )
                aud_bytes = sintetizar_voz(resp_txt)
            st.session_state[chave_chat_vid] = {
                "pergunta": duvida_usuario,
                "resposta": resp_txt,
                "audio": aud_bytes,
            }

        perguntas_sugeridas = video_atual.get("perguntas_rapidas", [])
        if perguntas_sugeridas:
            cols_sug = st.columns(len(perguntas_sugeridas))
            for i, p_sug in enumerate(perguntas_sugeridas):
                with cols_sug[i]:
                    if st.button(f"💬 {p_sug}", key=f"sug_{video_atual['id']}_{i}", use_container_width=True):
                        responder_duvida_video(p_sug)

        col_txt, col_mic = st.columns([3.5, 1.5])
        with col_txt:
            pergunta_livre = st.text_input(
                "Escreva sua dúvida sobre o vídeo:",
                key=f"txt_duvida_{video_atual['id']}",
                placeholder="Digite uma dúvida sobre este assunto...",
                label_visibility="collapsed",
            )
        with col_mic:
            audio_duvida = (
                st.audio_input(
                    "🎙️ Perguntar por voz",
                    key=f"mic_duvida_{video_atual['id']}",
                    label_visibility="collapsed",
                )
                if stt else None
            )

        if st.button("Enviar pergunta à Yara", key=f"send_duvida_{video_atual['id']}"):
            if pergunta_livre.strip():
                responder_duvida_video(pergunta_livre.strip())

        if audio_duvida is not None and stt is not None:
            aud_val = audio_duvida.getvalue()
            if st.session_state.get(f"last_aud_{video_atual['id']}") != aud_val:
                st.session_state[f"last_aud_{video_atual['id']}"] = aud_val
                with st.spinner("Ouvindo sua pergunta..."):
                    transc = stt.transcrever_audio(aud_val)
                if transc and not transc.startswith("[Erro"):
                    responder_duvida_video(transc)

        if st.session_state[chave_chat_vid]:
            interacao = st.session_state[chave_chat_vid]
            st.info(f"**Sua pergunta:** {interacao['pergunta']}")
            st.success(f"**🌿 Yara:** {interacao['resposta']}")
            if interacao.get("audio"):
                st.audio(interacao["audio"], format="audio/mp3", autoplay=True)

    st.markdown("### 🎬 Mais vídeos e animações deste módulo")
    cols_grade = st.columns(3)
    for idx, item in enumerate(lista_filtrada):
        col = cols_grade[idx % 3]
        thumb = _extrair_thumbnail_youtube(item["video_url"])
        esta_tocando = item["id"] == video_atual["id"]

        with col:
            st.markdown(
                f"""
                <div class="episode-card" style="border-color: {'#10B981' if esta_tocando else '#1F2937'};">
                    <img src="{thumb}" class="episode-thumb" alt="{item['titulo']}">
                    <div class="episode-body">
                        <div class="episode-meta">{item['categoria']} • {item['duracao']}</div>
                        <div class="episode-title">{item['titulo']}</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            label_btn = "✅ Assistindo agora" if esta_tocando else "▶ Assistir vídeo"
            if st.button(label_btn, key=f"select_{item['id']}", use_container_width=True, disabled=esta_tocando):
                st.session_state[chave_selecao] = item["id"]
                st.rerun()

    with st.expander("➕ Adicionar link de vídeo manualmente (Professor / PET)"):
        with st.form(key=f"form_add_vid_{chave_modulo}", clear_on_submit=True):
            novo_titulo = st.text_input("Título do vídeo ou animação")
            col_c, col_d = st.columns(2)
            with col_c:
                nova_cat = st.text_input("Categoria (ex: Prevenção, Lendas, Floresta)")
            with col_d:
                nova_dur = st.text_input("Duração (ex: 4 min)", value="3 min")
            nova_url = st.text_input("Link do YouTube (ex: https://www.youtube.com/watch?v=...)")
            nova_desc = st.text_area("Resumo curto sobre o que o vídeo ensina")
            novos_topicos = st.text_input("Pontos-chave separados por vírgula (ex: Água limpa, Saúde, Prevenção)")

            if st.form_submit_button("Salvar vídeo no catálogo"):
                if novo_titulo.strip() and nova_url.strip():
                    novo_item = {
                        "id": f"{chave_modulo}_{len(conteudos) + 1}",
                        "titulo": novo_titulo.strip(),
                        "categoria": nova_cat.strip() or "Geral",
                        "duracao": nova_dur.strip() or "3 min",
                        "descricao": nova_desc.strip() or "Conteúdo educativo selecionado pelo PET.",
                        "video_url": nova_url.strip(),
                        "topicos_chave": [t.strip() for t in novos_topicos.split(",") if t.strip()] or ["Educação Comunitária"],
                        "perguntas_rapidas": [
                            "Qual a mensagem principal deste vídeo?",
                            "Como aplicar isso no nosso dia a dia?"
                        ],
                    }
                    todos_dados.setdefault(chave_modulo, []).append(novo_item)
                    salvar_conteudos(todos_dados)
                    st.success("Vídeo adicionado com sucesso!")
                    st.rerun()
                else:
                    st.warning("Preencha pelo menos o Título e o Link do YouTube.")