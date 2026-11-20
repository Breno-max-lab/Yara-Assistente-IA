import io
from datetime import datetime
from pathlib import Path
import streamlit as st
from docx import Document
from src.llm_engine import LLMEngine
from src.rag_engine import (
    DOCS_DIR,
    listar_documentos_pet,
    salvar_documento_pet,
)

CATALOGO_PATH = Path(__file__).parent.parent / "data" / "conteudos_modulos.json"


def _gerar_arquivo_docx(titulo: str, conteudo_markdown: str) -> bytes:
    """Converte o material gerado pela IA em um documento Word (.docx) formatado para impressão."""
    doc = Document()
    doc.add_heading(titulo, level=1)
    doc.add_paragraph("Material gerado com apoio da Yara • Assistente Educacional (PET / UFOPA)")
    doc.add_paragraph("")

    for linha in conteudo_markdown.splitlines():
        linha_limpa = linha.strip()
        if not linha_limpa:
            continue
        if linha_limpa.startswith("### "):
            doc.add_heading(linha_limpa.replace("### ", ""), level=3)
        elif linha_limpa.startswith("## "):
            doc.add_heading(linha_limpa.replace("## ", ""), level=2)
        elif linha_limpa.startswith("# "):
            doc.add_heading(linha_limpa.replace("# ", ""), level=1)
        elif linha_limpa.startswith(("- ", "* ")):
            texto_item = linha_limpa[2:].replace("**", "")
            doc.add_paragraph(texto_item, style="List Bullet")
        else:
            doc.add_paragraph(linha_limpa.replace("**", ""))

    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer.getvalue()


def _registrar_no_historico_professor(titulo: str, categoria: str, conteudo: str):
    if "prof_historico" not in st.session_state:
        st.session_state.prof_historico = []

    item = {
        "id": len(st.session_state.prof_historico) + 1,
        "hora": datetime.now().strftime("%H:%M"),
        "titulo": titulo,
        "categoria": categoria,
        "conteudo": conteudo,
    }
    st.session_state.prof_historico.insert(0, item)
    st.session_state.prof_resultado = item


def render_painel_professor(llm: LLMEngine):
    st.markdown("""
    <style>
        .prof-banner {
            background: linear-gradient(135deg, #0F2922 0%, #111827 100%);
            border: 1px solid #1E3A34;
            border-radius: 18px;
            padding: 20px 24px;
            margin-bottom: 20px;
        }
        .prof-banner h2 {
            margin: 0 0 6px 0;
            color: #FFFFFF;
            font-size: 24px;
        }
        .prof-banner p {
            margin: 0;
            color: #94A3B8;
            font-size: 14.5px;
        }
    </style>
    <div class="prof-banner">
        <h2>🎓 Estúdio Pedagógico do Professor</h2>
        <p>Crie planos de aula alinhados à BNCC, provas com gabarito, apostilas e gerencie a base de conhecimento da Yara.</p>
    </div>
    """, unsafe_allow_html=True)

    # --- CONFIGURAÇÕES GERAIS DA TURMA / DISCIPLINA ---
    with st.container(border=True):
        st.markdown("#### 1. Dados da Aula ou Avaliação")
        col1, col2, col3 = st.columns(3)
        with col1:
            disciplina = st.selectbox(
                "Disciplina / Área:",
                [
                    "Língua Portuguesa",
                    "Matemática",
                    "Ciências / Biologia",
                    "Geografia",
                    "História",
                    "Educação Ambiental",
                    "Artes e Cultura Regional",
                    "Alfabetização / EJA",
                    "Outra (especificar no tema)",
                ],
            )
        with col2:
            etapa_ensino = st.selectbox(
                "Etapa / Nível da Turma:",
                [
                    "Educação Infantil",
                    "Ensino Fundamental I (1º ao 5º ano)",
                    "Ensino Fundamental II (6º ao 9º ano)",
                    "Ensino Médio",
                    "EJA (Educação de Jovens e Adultos)",
                    "Turma Multisseriada (Comunitária)",
                ],
            )
        with col3:
            contextualizar_amazonia = st.toggle(
                "🌿 Contextualizar com a realidade amazônica",
                value=True,
                help="Inclui exemplos ligados aos rios, floresta, fauna e cotidiano ribeirinho.",
            )

        tema_aula = st.text_input(
            "Tema ou Conteúdo Específico:",
            placeholder="Ex: Frações e medidas; Ciclo da água e rios voadores; Interpretação de lendas amazônicas...",
        )

    # --- ABAS DE FERRAMENTAS DO PROFESSOR ---
    aba_plano, aba_prova, aba_apostila, aba_dinamica, aba_base = st.tabs([
        "📋 Plano de Aula",
        "📝 Provas",
        "📖 Apostila",
        "🎲 Dinâmicas",
        "📚 Base & Backup",
    ])

    # ==========================================================================
    # ABA 1: PLANO DE AULA
    # ==========================================================================
    with aba_plano:
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            duracao_aula = st.selectbox("Duração prevista:", ["1 aula (50 min)", "2 aulas (1h40)", "Sequência didática (1 semana)"])
        with col_p2:
            recursos_disponiveis = st.selectbox(
                "Recursos da escola:",
                ["Quadro, giz/pincel e caderno (sem internet)", "Material impresso e cartolina", "Projetor / TV / Celular"],
            )

        obs_plano = st.text_input(
            "Observações adicionais (opcional):",
            key="obs_plano",
            placeholder="Ex: Turma com alunos em diferentes níveis de leitura...",
        )

        if st.button("✨ Gerar Plano de Aula Completo", key="btn_gerar_plano", type="primary", use_container_width=True):
            if not tema_aula.strip():
                st.warning("Digite o tema ou conteúdo específico no campo acima antes de gerar.")
            else:
                ctx_reg = "Sim, traga exemplos da realidade ribeirinha e amazônica." if contextualizar_amazonia else "Abordagem geral."
                prompt = (
                    f"Elabore um PLANO DE AULA completo e estruturado:\n"
                    f"- Disciplina: {disciplina}\n"
                    f"- Etapa/Turma: {etapa_ensino}\n"
                    f"- Tema: {tema_aula}\n"
                    f"- Duração: {duracao_aula}\n"
                    f"- Recursos disponíveis: {recursos_disponiveis}\n"
                    f"- Contextualização regional: {ctx_reg}\n"
                    f"- Observações: {obs_plano or 'Nenhuma'}\n\n"
                    "Estruture obrigatoriamente com:\n"
                    "1. Identificação e Objetivos de Aprendizagem\n"
                    "2. Habilidades da BNCC relacionadas (códigos e descrições aproximadas)\n"
                    "3. Desenvolvimento Metodológico (Passo a passo: Acolhimento, Explicação e Prática)\n"
                    "4. Recursos Didáticos Necessários\n"
                    "5. Avaliação da Aprendizagem"
                )
                with st.spinner("Yara está estruturando o plano de aula..."):
                    res = llm.gerar_resposta([{"role": "user", "content": prompt}], modo="professor")
                _registrar_no_historico_professor(f"Plano de Aula - {disciplina} ({tema_aula})", "Plano de Aula", res)

    # ==========================================================================
    # ABA 2: PROVAS E LISTAS DE EXERCÍCIOS
    # ==========================================================================
    with aba_prova:
        col_q1, col_q2, col_q3 = st.columns(3)
        with col_q1:
            qtd_questoes = st.slider("Número de questões:", min_value=3, max_value=15, value=5)
        with col_q2:
            tipo_questoes = st.selectbox(
                "Formato das questões:",
                [
                    "Mista (Múltipla escolha + Discursivas)",
                    "Apenas Múltipla Escolha (A, B, C, D)",
                    "Apenas Discursivas / Abertas",
                    "Verdadeiro ou Falso + Associação",
                ],
            )
        with col_q3:
            nivel_dificuldade = st.selectbox("Nível de dificuldade:", ["Básico / Introdutório", "Intermediário", "Desafiador"])

        if st.button("📝 Gerar Avaliação + Gabarito", key="btn_gerar_prova", type="primary", use_container_width=True):
            if not tema_aula.strip():
                st.warning("Digite o tema da avaliação no campo acima antes de gerar.")
            else:
                ctx_reg = "Use situações-problema e textos contextualizados na Amazônia." if contextualizar_amazonia else ""
                prompt = (
                    f"Crie uma AVALIAÇÃO / LISTA DE EXERCÍCIOS pronta para imprimir:\n"
                    f"- Disciplina: {disciplina} | Turma: {etapa_ensino}\n"
                    f"- Conteúdo: {tema_aula}\n"
                    f"- Quantidade: {qtd_questoes} questões | Formato: {tipo_questoes}\n"
                    f"- Nível: {nivel_dificuldade}\n"
                    f"- {ctx_reg}\n\n"
                    "Inclua um cabeçalho simples (Escola, Nome do Aluno, Data), as questões numeradas com clareza e, "
                    "ao final (após uma linha divisória), o GABARITO COMENTADO para o professor."
                )
                with st.spinner("Yara está elaborando as questões e o gabarito..."):
                    res = llm.gerar_resposta([{"role": "user", "content": prompt}], modo="professor")
                _registrar_no_historico_professor(f"Avaliação - {disciplina} ({tema_aula})", "Prova", res)

    # ==========================================================================
    # ABA 3: TEXTO DE APOIO / APOSTILA
    # ==========================================================================
    with aba_apostila:
        foco_texto = st.selectbox(
            "Estilo do material de leitura:",
            [
                "Resumo Didático para o Caderno / Apostila",
                "História / Crônica Educativa para Leitura em Sala",
                "Guia Visual com Glossário de Palavras-Chave",
            ],
        )

        if st.button("📖 Gerar Material de Apoio", key="btn_gerar_apostila", type="primary", use_container_width=True):
            if not tema_aula.strip():
                st.warning("Digite o tema do material no campo acima antes de gerar.")
            else:
                ctx_reg = "Conecte a explicação com exemplos da vida nos rios, floresta e comunidades amazônicas." if contextualizar_amazonia else ""
                prompt = (
                    f"Escreva um MATERIAL DIDÁTICO DE APOIO ({foco_texto}):\n"
                    f"- Disciplina: {disciplina} | Turma: {etapa_ensino}\n"
                    f"- Tema: {tema_aula}\n"
                    f"- {ctx_reg}\n\n"
                    "Use linguagem clara, envolvente e adequada à faixa etária. Inclua ao final um pequeno glossário "
                    "com 4 a 5 termos importantes explicados de forma simples e 3 perguntas de compreensão."
                )
                with st.spinner("Yara está escrevendo o material de apoio..."):
                    res = llm.gerar_resposta([{"role": "user", "content": prompt}], modo="professor")
                _registrar_no_historico_professor(f"Material de Apoio - {disciplina} ({tema_aula})", "Apostila", res)

    # ==========================================================================
    # ABA 4: DINÂMICAS E ATIVIDADES LÚDICAS
    # ==========================================================================
    with aba_dinamica:
        local_atividade = st.selectbox(
            "Onde será realizada:",
            ["Dentro da sala de aula", "No pátio / ao ar livre na comunidade", "Em roda de conversa"],
        )

        if st.button("🎲 Sugerir Dinâmicas e Jogos", key="btn_gerar_dinamica", type="primary", use_container_width=True):
            if not tema_aula.strip():
                st.warning("Digite o tema da aula no campo acima antes de gerar.")
            else:
                prompt = (
                    f"Sugira 3 DINÂMICAS PRÁTICAS OU JOGOS EDUCATIVOS para ensinar '{tema_aula}' "
                    f"na disciplina de {disciplina} para {etapa_ensino} (Local: {local_atividade}).\n"
                    "Priorize materiais recicláveis, elementos da natureza ou apenas papel e voz. "
                    "Para cada dinâmica, explique: Objetivo, Materiais e Passo a passo de como aplicar."
                )
                with st.spinner("Yara está criando ideias de atividades práticas..."):
                    res = llm.gerar_resposta([{"role": "user", "content": prompt}], modo="professor")
                _registrar_no_historico_professor(f"Dinâmicas - {disciplina} ({tema_aula})", "Dinâmica", res)

    # ==========================================================================
    # ABA 5: BASE DE CONHECIMENTO (PDFs DO PET) & BACKUP DO CATÁLOGO
    # ==========================================================================
    with aba_base:
        st.markdown("#### 📚 Documentos e Cartilhas da Yara (RAG)")
        st.caption("Envie cartilhas em PDF ou TXT (ex: manuais de saúde, apostilas do PET) para que a Yara use essas fontes nas respostas.")

        arquivo_up = st.file_uploader(
            "Enviar novo documento (.pdf ou .txt):",
            type=["pdf", "txt", "md"],
            key="upload_doc_pet",
        )
        if arquivo_up is not None:
            if salvar_documento_pet(arquivo_up.name, arquivo_up.getvalue()):
                st.success(f"Documento '{arquivo_up.name}' adicionado à memória da Yara!")

        docs_ativos = listar_documentos_pet()
        if docs_ativos:
            st.markdown("**Documentos ativos na base:**")
            for doc_nome in docs_ativos:
                col_d1, col_d2 = st.columns([4, 1])
                with col_d1:
                    st.markdown(f"📄 `{doc_nome}`")
                with col_d2:
                    if st.button("🗑️", key=f"del_doc_{doc_nome}", help="Remover documento"):
                        (DOCS_DIR / doc_nome).unlink(missing_ok=True)
                        st.rerun()
        else:
            st.info("Nenhum documento cadastrado ainda. Você também pode colocar arquivos PDF diretamente na pasta `data/documentos_pet/` do repositório.")

        st.divider()
        st.markdown("#### 💾 Backup do Catálogo de Vídeos (Persistência)")
        st.caption("Após renovar os vídeos automaticamente nos módulos, baixe o arquivo JSON atualizado para salvar definitivamente no seu GitHub.")
        if CATALOGO_PATH.exists():
            st.download_button(
                label="⬇️ Baixar conteudos_modulos.json atualizado",
                data=CATALOGO_PATH.read_bytes(),
                file_name="conteudos_modulos.json",
                mime="application/json",
                use_container_width=True,
            )

    # ==========================================================================
    # HISTÓRICO DA SESSÃO + EXIBIÇÃO DO MATERIAL GERADO
    # ==========================================================================
    historico_prof = st.session_state.get("prof_historico", [])
    if len(historico_prof) > 1:
        st.markdown("#### 🗂️ Materiais gerados nesta sessão")
        opcoes_hist = [f"[{h['hora']}] {h['titulo']}" for h in historico_prof]
        escolha_hist = st.selectbox(
            "Alternar entre materiais já gerados:",
            range(len(opcoes_hist)),
            format_func=lambda idx: opcoes_hist[idx],
            label_visibility="collapsed",
        )
        st.session_state.prof_resultado = historico_prof[escolha_hist]

    if "prof_resultado" in st.session_state and st.session_state.prof_resultado:
        resultado = st.session_state.prof_resultado
        st.markdown("---")
        with st.container(border=True):
            col_tit, col_dl1, col_dl2 = st.columns([2.5, 1, 1])
            with col_tit:
                st.markdown(f"### 📄 {resultado['titulo']}")
            with col_dl1:
                docx_bytes = _gerar_arquivo_docx(resultado["titulo"], resultado["conteudo"])
                st.download_button(
                    label="⬇️ Word (.docx)",
                    data=docx_bytes,
                    file_name=f"{resultado['titulo'].lower().replace(' ', '_')[:40]}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    use_container_width=True,
                )
            with col_dl2:
                st.download_button(
                    label="⬇️ Texto (.txt)",
                    data=resultado["conteudo"].encode("utf-8"),
                    file_name=f"{resultado['titulo'].lower().replace(' ', '_')[:40]}.txt",
                    mime="text/plain",
                    use_container_width=True,
                )

            st.markdown(resultado["conteudo"])