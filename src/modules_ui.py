import json
import re
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

# Trilha lúdica para não-leitores (Figura grande + Letra/Sílaba + Palavra-âncora)
TRILHA_ALFABETIZACAO = [
    {
        "emoji": "🦜",
        "foco": "A",
        "palavra_alvo": "ARARA",
        "aceitas": ["arara", "acai", "açaí", "agua", "água", "abelha", "amor", "aviao", "avião", "ara"],
        "fala_inicial": "Oi, que alegria ter você na minha escolinha! Eu sou a professora Yara. Olha o passarinho colorido e a letra A na tela: é o A de Arara! Toca no botão verde do microfone e fala bem bonito: Arara!",
    },
    {
        "emoji": "⭐",
        "foco": "E",
        "palavra_alvo": "ESTRELA",
        "aceitas": ["estrela", "escola", "elefante", "escada", "espelho"],
        "fala_inicial": "Agora olha essa figura brilhando junto com a letra E: é o E de Estrela! Toca no microfone e fala comigo bem forte: Estrela!",
    },
    {
        "emoji": "🏝️",
        "foco": "I",
        "palavra_alvo": "ILHA",
        "aceitas": ["ilha", "igarape", "igarapé", "indio", "índio", "igreja"],
        "fala_inicial": "Olha só a letra I fininha igual um lápis, junto com a Ilha no meio do rio! Toca no microfone e fala comigo: Ilha!",
    },
    {
        "emoji": "🐆",
        "foco": "O",
        "palavra_alvo": "ONÇA",
        "aceitas": ["onca", "onça", "ovo", "onda", "olho", "orelha"],
        "fala_inicial": "Essa letra redondinha igual uma bola é a letra O, de Onça pintada! Toca no microfone e fala comigo: Onça!",
    },
    {
        "emoji": "🍇",
        "foco": "U",
        "palavra_alvo": "UVA",
        "aceitas": ["uva", "urubu", "urso", "unha"],
        "fala_inicial": "Chegamos na última vogal, a letra U, de Uva e Urubu! Faz biquinho e fala no microfone: Uva!",
    },
    {
        "emoji": "🍌",
        "foco": "BA",
        "palavra_alvo": "BANANA",
        "aceitas": ["banana", "barco", "baleia", "batata", "bacia"],
        "fala_inicial": "Você já conhece todas as vogais! Agora quando o B dá a mão para o A, faz BA, de Banana! Toca no microfone e fala comigo: Banana!",
    },
    {
        "emoji": "🐬",
        "foco": "BO",
        "palavra_alvo": "BOTO",
        "aceitas": ["boto", "bola", "bolo", "boca", "botina"],
        "fala_inicial": "E quando o B dá a mão para o O, faz BO, de Boto cor-de-rosa! Fala no microfone para a professora ouvir: Boto!",
    },
    {
        "emoji": "🛶",
        "foco": "CA",
        "palavra_alvo": "CANOA",
        "aceitas": ["canoa", "casa", "cachorro", "cavalo", "camisa"],
        "fala_inicial": "Para fechar com chave de ouro, o C com o A faz CA, de Canoa! Toca no microfone e fala bem alegre: Canoa!",
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
    """Extrai a imagem de capa (thumbnail) automática se o link for do YouTube."""
    padrao = r"(?:v=|\/)([0-9A-Za-z_-]{11}).*"
    match = re.search(padrao, url or "")
    if match:
        video_id = match.group(1)
        return f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"
    return "https://images.unsplash.com/photo-1518173946687-a4c8892bbd9f?auto=format&fit=crop&w=600&q=60"


# ==============================================================================
# MÓDULO 1: ALFABETIZAÇÃO POR VOZ (TEMPO REAL NO NAVEGADOR, ZERO TRAVAMENTO)
# ==============================================================================
def render_modulo_alfabetizacao(llm: LLMEngine, stt: SpeechEngine):
    """Escolinha de Voz em tempo real (zero travamento, 100% orientada por voz no navegador)."""
    trilha_json = json.dumps(TRILHA_ALFABETIZACAO, ensure_ascii=False)

    html_app = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <meta charset="utf-8">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@500;600;700;800&display=swap');
        * {{ box-sizing: border-box; }}
        body {{
            margin: 0;
            padding: 0;
            background: transparent;
            font-family: 'Inter', sans-serif;
            color: #F8FAFC;
            user-select: none;
        }}
        .stage {{
            background: #05070B;
            border: 1px solid #141E2B;
            border-radius: 28px;
            padding: 26px 20px 30px 20px;
            display: flex;
            flex-direction: column;
            align-items: center;
            text-align: center;
            box-shadow: 0 18px 45px rgba(0, 0, 0, 0.65);
        }}

        /* Estrelas */
        .stars-bar {{
            display: flex;
            gap: 8px;
            margin-bottom: 18px;
            background: #0D131F;
            padding: 6px 18px;
            border-radius: 999px;
            border: 1px solid #1E293B;
        }}
        .star {{
            font-size: 22px;
            color: #263244;
            transition: all 0.35s ease;
        }}
        .star.earned {{
            color: #FBBF24;
            text-shadow: 0 0 14px rgba(251, 191, 36, 0.85);
            transform: scale(1.18);
        }}

        /* Orbe Verde-Esmeralda */
        .orb-wrap {{
            width: 145px;
            height: 145px;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 18px;
            cursor: pointer;
        }}
        .orb {{
            width: 130px;
            height: 130px;
            border-radius: 50%;
            background: radial-gradient(circle at 32% 28%, #ECFDF5 0%, #6EE7B7 28%, #10B981 60%, #047857 100%);
            box-shadow: 0 0 34px rgba(16, 185, 129, 0.45), inset 0 -12px 22px rgba(6, 78, 59, 0.75);
            animation: floatOrb 3.5s ease-in-out infinite;
            transition: all 0.25s ease;
        }}
        .orb.speaking {{
            animation: speakOrb 0.6s ease-in-out infinite alternate;
            box-shadow: 0 0 55px rgba(52, 211, 153, 0.95), 0 0 95px rgba(16, 185, 129, 0.5);
        }}
        .orb.listening {{
            background: radial-gradient(circle at 32% 28%, #FEF3C7 0%, #FCD34D 30%, #F59E0B 65%, #B45309 100%);
            box-shadow: 0 0 50px rgba(245, 158, 11, 0.85);
            animation: speakOrb 0.7s ease-in-out infinite alternate;
        }}
        @keyframes floatOrb {{
            0%, 100% {{ transform: scale(0.97); }}
            50% {{ transform: scale(1.03); }}
        }}
        @keyframes speakOrb {{
            0% {{ transform: scale(0.94); border-radius: 50%; }}
            50% {{ transform: scale(1.09); border-radius: 47% 53% 50% 50%; }}
            100% {{ transform: scale(1.14); border-radius: 50%; }}
        }}

        /* Figura + Letra Gigante */
        .cue-box {{
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 24px;
            background: #0D131F;
            border: 1px solid #1E293B;
            border-radius: 22px;
            padding: 14px 32px;
            margin-bottom: 14px;
        }}
        .cue-emoji {{ font-size: 62px; line-height: 1; }}
        .cue-letter {{
            font-size: 72px;
            font-weight: 800;
            color: #FFFFFF;
            letter-spacing: 0.06em;
            line-height: 1;
            text-shadow: 0 4px 20px rgba(16, 185, 129, 0.4);
        }}

        .status-msg {{
            font-size: 15px;
            font-weight: 600;
            color: #94A3B8;
            min-height: 22px;
            margin-bottom: 6px;
        }}
        .status-msg.highlight {{ color: #6EE7B7; }}
        .status-msg.listen {{ color: #FCD34D; }}

        .heard-text {{
            font-size: 13.5px;
            color: #CBD5E1;
            min-height: 20px;
            margin-bottom: 18px;
            font-style: italic;
        }}

        /* Controles Inferiores Grandes e Acessíveis */
        .controls {{
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 14px;
            flex-wrap: wrap;
        }}
        .btn-mic {{
            background: linear-gradient(135deg, #10B981 0%, #059669 100%);
            color: #FFFFFF;
            border: none;
            border-radius: 999px;
            padding: 16px 32px;
            font-size: 17px;
            font-weight: 700;
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            gap: 10px;
            box-shadow: 0 6px 24px rgba(16, 185, 129, 0.35);
            transition: transform 0.15s ease, filter 0.15s ease;
        }}
        .btn-mic:hover {{ filter: brightness(1.08); transform: translateY(-1px); }}
        .btn-mic.recording {{
            background: linear-gradient(135deg, #F59E0B 0%, #D97706 100%);
            box-shadow: 0 6px 24px rgba(245, 158, 11, 0.45);
        }}

        .btn-sec {{
            background: #111827;
            color: #E2E8F0;
            border: 1px solid #1F2937;
            border-radius: 999px;
            padding: 14px 20px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.15s ease;
        }}
        .btn-sec:hover {{ background: #1E293B; border-color: #334155; }}

        /* Tela inicial de 1 clique para liberar áudio do navegador */
        .start-overlay {{
            padding: 36px 16px;
        }}
        .start-overlay h2 {{ margin: 12px 0 8px 0; font-size: 24px; }}
        .start-overlay p {{ color: #94A3B8; max-width: 420px; margin: 0 auto 24px auto; font-size: 15px; }}
    </style>
    </head>
    <body>
        <div class="stage">
            <!-- TELA DE ENTRADA (DESTRAVA VOZ DO NAVEGADOR) -->
            <div id="tela_inicio" class="start-overlay">
                <div style="font-size: 64px;">🌿🦜</div>
                <h2>Escolinha de Voz da Professora Yara</h2>
                <p>Aperte o botão verde abaixo para ouvir a professora e começar a brincar com os sons das letras!</p>
                <button class="btn-mic" onclick="iniciarEscolinha()">
                    ▶ Começar Aula Agora
                </button>
            </div>

            <!-- PALCO ATIVO DA AULA -->
            <div id="tela_aula" style="display:none; width:100%; flex-direction:column; align-items:center;">
                <div class="stars-bar" id="stars_bar"></div>

                <div class="orb-wrap" onclick="repetirFala()" title="Toque para ouvir de novo">
                    <div class="orb" id="orb"></div>
                </div>

                <div class="cue-box">
                    <span class="cue-emoji" id="cue_emoji">🦜</span>
                    <span class="cue-letter" id="cue_letter">A</span>
                </div>

                <div class="status-msg" id="status_msg">Preparando...</div>
                <div class="heard-text" id="heard_text"></div>

                <div class="controls">
                    <button class="btn-sec" onclick="repetirFala()" title="Ouvir novamente">
                        🔊 Ouvir de novo
                    </button>
                    <button class="btn-mic" id="btn_mic" onclick="alternarMicrofone()">
                        🎙️ Falar com a Yara
                    </button>
                    <button class="btn-sec" onclick="pularEtapa()" title="Próxima figura">
                        ⏭️
                    </button>
                    <button class="btn-sec" onclick="reiniciarAula()" title="Recomeçar">
                        ✕
                    </button>
                </div>
            </div>
        </div>

        <script>
            const trilha = {trilha_json};
            let etapaIdx = 0;
            let estrelas = 0;
            let falaAtual = "";
            let reconhecimento = null;
            let gravando = false;
            let vozEscolhida = null;

            function carregarVozes() {{
                if (!('speechSynthesis' in window)) return;
                const vozes = window.speechSynthesis.getVoices();
                vozEscolhida =
                    vozes.find(v => v.lang.includes('pt-BR') && (v.name.includes('Maria') || v.name.includes('Francisca') || v.name.includes('Thalita') || v.name.includes('Google'))) ||
                    vozes.find(v => v.lang.includes('pt'));
            }}
            if ('speechSynthesis' in window) {{
                carregarVozes();
                window.speechSynthesis.onvoiceschanged = carregarVozes;
            }}

            function normalizar(str) {{
                return str.toLowerCase().normalize("NFD").replace(/[\\u0300-\\u036f]/g, "").trim();
            }}

            function renderizarEstrelas() {{
                const bar = document.getElementById('stars_bar');
                bar.innerHTML = '';
                for (let i = 0; i < trilha.length; i++) {{
                    const s = document.createElement('span');
                    s.className = 'star' + (i < estrelas ? ' earned' : '');
                    s.innerText = '★';
                    bar.appendChild(s);
                }}
            }}

            function atualizarTelaEtapa() {{
                const item = trilha[etapaIdx];
                document.getElementById('cue_emoji').innerText = item.emoji;
                document.getElementById('cue_letter').innerText = item.foco;
                renderizarEstrelas();
            }}

            function falarYara(texto, callbackFim = null) {{
                falaAtual = texto;
                const orb = document.getElementById('orb');
                const status = document.getElementById('status_msg');

                if (!('speechSynthesis' in window)) {{
                    status.innerText = texto;
                    if (callbackFim) callbackFim();
                    return;
                }}

                window.speechSynthesis.cancel();
                const utter = new SpeechSynthesisUtterance(texto);
                utter.lang = 'pt-BR';
                if (vozEscolhida) utter.voice = vozEscolhida;
                utter.rate = 0.96;
                utter.pitch = 1.08;

                utter.onstart = () => {{
                    orb.classList.remove('listening');
                    orb.classList.add('speaking');
                    status.className = 'status-msg highlight';
                    status.innerText = 'Professora Yara está falando...';
                }};

                utter.onend = () => {{
                    orb.classList.remove('speaking');
                    status.className = 'status-msg';
                    status.innerText = 'Sua vez! Aperte o botão verde e fale';
                    if (callbackFim) callbackFim();
                }};

                utter.onerror = () => {{
                    orb.classList.remove('speaking');
                    status.className = 'status-msg';
                    status.innerText = 'Aperte o botão verde para falar';
                }};

                window.speechSynthesis.speak(utter);
            }}

            function iniciarEscolinha() {{
                document.getElementById('tela_inicio').style.display = 'none';
                document.getElementById('tela_aula').style.display = 'flex';
                etapaIdx = 0;
                estrelas = 0;
                atualizarTelaEtapa();
                falarYara(trilha[0].fala_inicial);
            }}

            function repetirFala() {{
                if (falaAtual) falarYara(falaAtual);
            }}

            function pularEtapa() {{
                etapaIdx = (etapaIdx + 1) % trilha.length;
                document.getElementById('heard_text').innerText = '';
                atualizarTelaEtapa();
                falarYara(trilha[etapaIdx].fala_inicial);
            }}

            function reiniciarAula() {{
                etapaIdx = 0;
                estrelas = 0;
                document.getElementById('heard_text').innerText = '';
                atualizarTelaEtapa();
                falarYara(trilha[0].fala_inicial);
            }}

            function avaliarFalaAluno(transcricao) {{
                const item = trilha[etapaIdx];
                const faladoNorm = normalizar(transcricao);
                document.getElementById('heard_text').innerText = `Você falou: "${{transcricao}}"`;

                const acertou = item.aceitas.some(palavra => faladoNorm.includes(normalizar(palavra)));

                if (acertou) {{
                    if (estrelas < trilha.length) estrelas++;
                    const elogios = [
                        `Ebaaa! Muito bem! Você falou ${{item.palavra_alvo}} direitinho e ganhou uma estrelinha!`,
                        `Isso mesmo! Parabéns, você brilhou falando ${{item.palavra_alvo}}!`,
                        `Que lindo! Palmas para você, acertou ${{item.palavra_alvo}} de primeira!`
                    ];
                    const elogio = elogios[etapaIdx % elogios.length];

                    if (etapaIdx + 1 < trilha.length) {{
                        etapaIdx++;
                        atualizarTelaEtapa();
                        const proximaFala = `${{elogio}} ${{trilha[etapaIdx].fala_inicial}}`;
                        falarYara(proximaFala);
                    }} else {{
                        atualizarTelaEtapa();
                        falarYara(`${{elogio}} Você completou todas as estrelinhas da escolinha hoje! Parabéns, campeão!`);
                    }}
                }} else {{
                    const dica = `Quase lá! Vamos tentar juntinhos? Olha a figura na tela e fala bem pertinho do microfone: ${{item.palavra_alvo}}!`;
                    falarYara(dica);
                }}
            }}

            function alternarMicrofone() {{
                const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
                const status = document.getElementById('status_msg');
                const orb = document.getElementById('orb');
                const btnMic = document.getElementById('btn_mic');

                if (!SpeechRec) {{
                    status.innerText = 'Seu navegador não suporta reconhecimento de voz direto. Use o Google Chrome ou Edge.';
                    return;
                }}

                if (gravando && reconhecimento) {{
                    reconhecimento.stop();
                    return;
                }}

                if ('speechSynthesis' in window) window.speechSynthesis.cancel();

                reconhecimento = new SpeechRec();
                reconhecimento.lang = 'pt-BR';
                reconhecimento.interimResults = true;
                reconhecimento.maxAlternatives = 3;

                reconhecimento.onstart = () => {{
                    gravando = true;
                    orb.classList.remove('speaking');
                    orb.classList.add('listening');
                    btnMic.classList.add('recording');
                    btnMic.innerHTML = '⏹️ Ouvindo... (Toque para enviar)';
                    status.className = 'status-msg listen';
                    status.innerText = 'Pode falar agora! Estou ouvindo...';
                }};

                let resultadoFinal = '';
                reconhecimento.onresult = (event) => {{
                    let parcial = '';
                    for (let i = event.resultIndex; i < event.results.length; i++) {{
                        const texto = event.results[i][0].transcript;
                        if (event.results[i].isFinal) {{
                            resultadoFinal += texto;
                        }} else {{
                            parcial += texto;
                        }}
                    }}
                    document.getElementById('heard_text').innerText = `Ouvindo: "${{resultadoFinal || parcial}}"`;
                }};

                reconhecimento.onerror = () => {{
                    gravando = false;
                    orb.classList.remove('listening');
                    btnMic.classList.remove('recording');
                    btnMic.innerHTML = '🎙️ Falar com a Yara';
                    status.className = 'status-msg';
                    status.innerText = 'Não ouvi bem. Aperte o botão verde e tente de novo!';
                }};

                reconhecimento.onend = () => {{
                    gravando = false;
                    orb.classList.remove('listening');
                    btnMic.classList.remove('recording');
                    btnMic.innerHTML = '🎙️ Falar com a Yara';

                    if (resultadoFinal.trim()) {{
                        avaliarFalaAluno(resultadoFinal.trim());
                    }} else {{
                        status.className = 'status-msg';
                        status.innerText = 'Não captei nenhuma palavra. Aperte o microfone e fale de novo!';
                    }}
                }};

                reconhecimento.start();
            }}
        </script>
    </body>
    </html>
    """
    components.html(html_app, height=520)


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