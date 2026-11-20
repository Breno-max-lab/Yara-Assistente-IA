import json
import yt_dlp
from src.llm_engine import LLMEngine

# Consultas educativas padrão para cada módulo caso queira preencher automaticamente
QUERIES_PADRAO_MODULOS = {
    "saude": [
        ("Água e Higiene", "animação educativa tratamento da água hipoclorito saúde"),
        ("Prevenção de Doenças", "animação educativa prevenção dengue malária ministério da saúde"),
        ("Primeiros Socorros", "animação educativa primeiros socorros picada de cobra animais peçonhentos"),
    ],
    "ambiental": [
        ("Clima e Floresta", "animação educativa rios voadores amazônia preservação"),
        ("Prevenção de Queimadas", "animação educativa prevenção queimadas meio ambiente amazônia"),
        ("Saneamento e Rios", "animação educativa lixo nos rios poluição água preservação"),
    ],
    "cultura": [
        ("Lendas Amazônicas", "animação lenda da cobra grande boiúna folclore"),
        ("Folclore Regional", "animação lenda do boto cor de rosa folclore brasileiro"),
        ("Folclore e Natureza", "animação lenda do curupira protetor da floresta"),
    ],
}


def buscar_videos_youtube(termo_busca: str, limite: int = 3) -> list[dict]:
    """Busca vídeos reais no YouTube sem precisar de chave de API usando yt-dlp."""
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": True,
        "skip_download": True,
    }
    resultados = []
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch{limite}:{termo_busca}", download=False)
            for entry in info.get("entries", []):
                if not entry or not entry.get("id"):
                    continue
                duracao_seg = entry.get("duration") or 180
                minutos = max(1, round(int(duracao_seg) / 60))
                resultados.append({
                    "video_id": entry["id"],
                    "titulo_original": entry.get("title", "Vídeo Educativo"),
                    "url": f"https://www.youtube.com/watch?v={entry['id']}",
                    "duracao": f"{minutos} min",
                    "canal": entry.get("uploader", ""),
                })
    except Exception:
        pass
    return resultados


def gerar_ficha_pedagogica_ia(llm: LLMEngine, video_info: dict, categoria: str, modulo: str) -> dict:
    """Usa a IA da Yara para criar descrição acessível, tópicos e perguntas rápidas sobre o vídeo."""
    prompt = [
        {
            "role": "user",
            "content": (
                f"Crie uma ficha educativa curta em JSON para um vídeo do módulo '{modulo}' (categoria: '{categoria}').\n"
                f"Título do vídeo: {video_info['titulo_original']}\n"
                f"Canal: {video_info['canal']}\n\n"
                "Responda APENAS com um JSON válido neste formato exato:\n"
                "{\n"
                '  "titulo": "Título limpo e educativo em português",\n'
                '  "descricao": "Resumo acolhedor de 2 frases simples explicando o que o vídeo ensina.",\n'
                '  "topicos_chave": ["Ponto 1", "Ponto 2", "Ponto 3"],\n'
                '  "perguntas_rapidas": ["Pergunta prática 1?", "Pergunta prática 2?", "Pergunta prática 3?"]\n'
                "}"
            ),
        }
    ]
    resposta_bruta = llm.gerar_resposta(prompt, modo="geral")
    try:
        inicio = resposta_bruta.find("{")
        fim = resposta_bruta.rfind("}") + 1
        dados_ia = json.loads(resposta_bruta[inicio:fim])
    except Exception:
        dados_ia = {
            "titulo": video_info["titulo_original"],
            "descricao": f"Conteúdo educativo sobre {categoria} selecionado automaticamente para a comunidade.",
            "topicos_chave": [categoria, "Educação Comunitária", "Amazônia"],
            "perguntas_rapidas": [
                "Qual a principal lição deste vídeo?",
                "Como posso aplicar isso no dia a dia?",
                "Por que esse tema é importante para nossa comunidade?",
            ],
        }

    return {
        "id": f"{modulo}_{video_info['video_id']}",
        "titulo": dados_ia.get("titulo", video_info["titulo_original"]),
        "categoria": categoria,
        "duracao": video_info["duracao"],
        "descricao": dados_ia.get("descricao", ""),
        "video_url": video_info["url"],
        "topicos_chave": dados_ia.get("topicos_chave", [])[:3],
        "perguntas_rapidas": dados_ia.get("perguntas_rapidas", [])[:3],
    }


def atualizar_catalogo_automatico(llm: LLMEngine, chave_modulo: str) -> list[dict]:
    """Busca 1 animação/vídeo real para cada categoria padrão do módulo e monta a ficha completa."""
    consultas = QUERIES_PADRAO_MODULOS.get(chave_modulo, [])
    novos_itens = []
    ids_vistos = set()

    for categoria, query in consultas:
        encontrados = buscar_videos_youtube(query, limite=2)
        for vid in encontrados:
            if vid["video_id"] not in ids_vistos:
                ids_vistos.add(vid["video_id"])
                ficha = gerar_ficha_pedagogica_ia(llm, vid, categoria, chave_modulo)
                novos_itens.append(ficha)
                break

    return novos_itens