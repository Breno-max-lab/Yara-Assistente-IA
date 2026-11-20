import io
import re
from pathlib import Path
from pypdf import PdfReader

DOCS_DIR = Path(__file__).parent.parent / "data" / "documentos_pet"


def garantir_pasta_docs():
    DOCS_DIR.mkdir(parents=True, exist_ok=True)


def extrair_texto_pdf(arquivo_bytes: bytes) -> str:
    try:
        leitor = PdfReader(io.BytesIO(arquivo_bytes))
        paginas = [p.extract_text() or "" for p in leitor.pages]
        return "\n".join(paginas)
    except Exception:
        return ""


def salvar_documento_pet(nome_arquivo: str, arquivo_bytes: bytes) -> bool:
    garantir_pasta_docs()
    destino = DOCS_DIR / nome_arquivo
    try:
        destino.write_bytes(arquivo_bytes)
        return True
    except Exception:
        return False


def listar_documentos_pet() -> list[str]:
    garantir_pasta_docs()
    arquivos = []
    for ext in ("*.pdf", "*.txt", "*.md"):
        arquivos.extend([f.name for f in DOCS_DIR.glob(ext)])
    return sorted(arquivos)


def _dividir_em_trechos(texto: str, tamanho_bloco: int = 700, sobreposicao: int = 120) -> list[str]:
    texto_limpo = re.sub(r"\s+", " ", texto).strip()
    if not texto_limpo:
        return []
    trechos = []
    inicio = 0
    while inicio < len(texto_limpo):
        fim = inicio + tamanho_bloco
        trechos.append(texto_limpo[inicio:fim])
        inicio += tamanho_bloco - sobreposicao
    return trechos


def buscar_contexto_documentos(pergunta: str, top_k: int = 3) -> str:
    """Busca os trechos mais relevantes nos PDFs/TXTs do PET para enriquecer a resposta."""
    garantir_pasta_docs()
    palavras_chave = {
        p.lower()
        for p in re.findall(r"\b\w{4,}\b", pergunta)
        if p.lower() not in {"como", "para", "qual", "quais", "sobre", "yara", "isso", "essa", "esse", "uma", "uns"}
    }
    if not palavras_chave:
        return ""

    candidatos = []
    for arquivo in DOCS_DIR.iterdir():
        if not arquivo.is_file():
            continue
        conteudo = ""
        if arquivo.suffix.lower() == ".pdf":
            conteudo = extrair_texto_pdf(arquivo.read_bytes())
        elif arquivo.suffix.lower() in (".txt", ".md"):
            conteudo = arquivo.read_text(encoding="utf-8", errors="ignore")

        for trecho in _dividir_em_trechos(conteudo):
            trecho_lower = trecho.lower()
            pontuacao = sum(trecho_lower.count(palavra) for palavra in palavras_chave)
            if pontuacao > 0:
                candidatos.append((pontuacao, arquivo.name, trecho))

    if not candidatos:
        return ""

    candidatos.sort(key=lambda x: x[0], reverse=True)
    melhores = candidatos[:top_k]

    blocos_formatados = [
        f"[Fonte: {nome_arq}] {texto_trecho}"
        for _, nome_arq, texto_trecho in melhores
    ]
    return (
        "Use as informações abaixo extraídas das cartilhas e documentos oficiais do projeto "
        "como base prioritária para responder com precisão:\n"
        + "\n---\n".join(blocos_formatados)
    )