"""Clipador IA: interface mobile-first, com limites honestos no modo gratuito."""
import os
from pathlib import Path

import gradio as gr

from engine import generate


PUBLIC_MODE = os.getenv("CLIPADOR_PUBLIC_MODE") == "1"
MAX_FILE_MB = int(os.getenv("CLIPADOR_MAX_BYTES", "1000000000")) // 1_000_000


def processar(link, arquivo, direitos, quantidade, estilo, qualidade, cenas, ia_local):
    """Exibe um único aviso claro no painel, sem quebrar cada saída do Gradio."""
    try:
        archive, covers, rows, message = generate(
            link, arquivo, direitos, int(quantidade), estilo, int(qualidade),
            scene_analysis=bool(cenas), local_ai=bool(ia_local))
        first_video = Path(archive).parent / "resultados" / "corte_01.mp4"
        return archive, str(first_video) if first_video.exists() else None, covers, rows, message
    except ValueError as exc:
        # Erros previstos: vídeo bloqueado pela plataforma, formato/tamanho ou licença.
        return None, None, [], [], f"⚠️ **Não foi possível gerar os cortes.**\n\n{str(exc)}"
    except Exception:
        # Não expõe stacktrace, nomes de arquivos privados ou dados do servidor na UI.
        return None, None, [], [], (
            "⚠️ **Falha ao processar este vídeo.** O app não conseguiu finalizar a edição. "
            "Tente um arquivo MP4 próprio e curto. Se persistir, precisamos consultar os logs."
        )


css = """
.gradio-container {
    max-width: 980px !important;
    margin: auto !important;
    padding: 16px 18px 32px !important;
    font-size: 16px !important;
}
.gradio-container .prose, .gradio-container label,
.gradio-container input, .gradio-container textarea {
    font-size: 15px !important;
    line-height: 1.45 !important;
}
.gradio-container h1 {
    font-size: clamp(29px, 5.5vw, 43px) !important;
    font-weight: 800 !important;
    line-height: 1.12 !important;
    letter-spacing: -0.035em !important;
}
.gradio-container h2 { font-size: clamp(19px, 4vw, 25px) !important; }
.gradio-container h3 { font-size: 18px !important; }
.gradio-container .primary-action button {
    min-height: 54px !important;
    font-size: 17px !important;
    font-weight: 750 !important;
}
.gradio-container .gradio-checkbox label {
    white-space: normal !important;
    line-height: 1.45 !important;
}
.gradio-container .gradio-button { min-height: 44px; }
@media (max-width: 640px) {
    .gradio-container { padding: 14px 12px 34px !important; }
    .gradio-container .gap { gap: 12px !important; }
    .gradio-container .prose { line-height: 1.55 !important; }
    .gradio-container input, .gradio-container textarea {
        font-size: 16px !important;
        min-height: 43px !important;
    }
}
"""
with gr.Blocks(title="Clipador IA | Estúdio de Cortes", theme=gr.themes.Soft(), css=css) as demo:
    gr.Markdown(
        "# ✂️ Clipador IA\n"
        "**Transforme vídeos longos em cortes para Shorts, Reels e TikTok.**\n\n"
        "A ferramenta seleciona trechos pela fala, cria legendas sincronizadas, "
        "gera capas e sugere títulos e descrições."
    )
    if PUBLIC_MODE:
        gr.Markdown(
            "🧪 **Beta gratuito:** até **20 minutos**, **"
            + str(MAX_FILE_MB)
            + " MB**, **2 cortes** e **720p** por processamento. "
            "Podcasts maiores podem ser processados na versão para Codespaces. "
            "O serviço pode demorar a acordar após ficar inativo."
        )

    gr.Markdown("## 1. Escolha o vídeo")
    link = gr.Textbox(
        label="Cole o link do vídeo",
        placeholder="Link público do YouTube, Instagram, Facebook ou Vimeo",
        lines=1,
        info="Links do YouTube podem ser bloqueados pela verificação antibot. Se acontecer, use o upload de um MP4 autorizado."
    )
    arquivo = gr.File(
        label="Ou envie o arquivo do vídeo",
        file_types=[".mp4", ".mov", ".mkv", ".webm"],
        type="filepath"
    )
    direitos = gr.Checkbox(
        label="Confirmo que tenho os direitos ou autorização para editar e publicar este conteúdo."
    )

    gr.Markdown("## 2. Personalize os cortes")
    with gr.Row():
        quantidade = gr.Slider(
            label="Quantidade de cortes", minimum=1, maximum=2 if PUBLIC_MODE else 6,
            value=2 if PUBLIC_MODE else 3, step=1
        )
        estilo = gr.Radio(
            ["Dinâmico", "Humor leve", "Sóbrio"], value="Dinâmico",
            label="Estilo visual das legendas"
        )
    if PUBLIC_MODE:
        qualidade = gr.Radio(
            [720], value=720, label="Qualidade: 720p no beta gratuito", interactive=False
        )
        # Controles não disponíveis no Render, mas mantidos para compatibilidade da função.
        cenas = gr.Checkbox(value=False, visible=False)
        ia_local = gr.Checkbox(value=False, visible=False)
    else:
        with gr.Row():
            qualidade = gr.Radio([720, 1080], value=720, label="Resolução do vídeo")
            cenas = gr.Checkbox(
                value=True, label="Priorizar trechos com mudanças de cena"
            )
            ia_local = gr.Checkbox(
                value=False, label="Usar Ollama local, se estiver instalado"
            )

    gr.Markdown("## 3. Gere e revise os resultados")
    botao = gr.Button("✨ Produzir meus cortes", variant="primary", elem_classes=["primary-action"])
    status = gr.Markdown("✅ Pronto para receber o vídeo. O resultado ou um aviso aparecerá aqui.")
    preview = gr.Video(label="Assista ao primeiro corte")
    download = gr.File(label="Baixar todos os cortes e capas (ZIP)")
    with gr.Accordion("Ver detalhes e sugestões de publicação", open=False):
        tabela = gr.Dataframe(
            headers=["Corte", "Início (s)", "Fim (s)", "Prioridade", "Título sugerido"],
            label="Trechos selecionados", interactive=False
        )
        galeria = gr.Gallery(label="Capas geradas", columns=2, height=300)

    botao.click(
        processar,
        inputs=[link, arquivo, direitos, quantidade, estilo, qualidade, cenas, ia_local],
        outputs=[download, preview, galeria, tabela, status],
        show_progress="full"
    )
    gr.Markdown(
        "ℹ️ **Antes de publicar:** confira as legendas, a edição e os direitos do material. "
        "Vídeos curtos e efeitos não garantem viralização, originalidade nem monetização. "
        "Não acessamos vídeos privados ou protegidos."
    )

if __name__ == "__main__":
    user = os.getenv("CLIPADOR_AUTH_USER")
    password = os.getenv("CLIPADOR_AUTH_PASSWORD")
    if PUBLIC_MODE and (not user or not password):
        raise RuntimeError("Proteção de acesso obrigatória para hospedagem pública.")
    auth = (user, password) if user and password else None
    demo.queue(default_concurrency_limit=1, max_size=2).launch(
        server_name=os.environ.get("CLIPADOR_HOST", "127.0.0.1"),
        server_port=int(os.getenv("PORT", "7860")),
        auth=auth,
        share=False,
        max_file_size=f"{MAX_FILE_MB}mb"
    )
