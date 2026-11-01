"""Clipador IA v2 — interface web para uso no celular e Codespaces privado."""
import os
from pathlib import Path
import gradio as gr
from engine import generate

PUBLIC_MODE = os.getenv("CLIPADOR_PUBLIC_MODE") == "1"
MAX_FILE_MB = int(os.getenv("CLIPADOR_MAX_BYTES", "1000000000")) // 1000000


def processar(link, arquivo, direitos, quantidade, estilo, qualidade, cenas, ia_local):
    try:
        archive, covers, rows, message = generate(
            link, arquivo, direitos, int(quantidade), estilo, int(qualidade),
            scene_analysis=bool(cenas), local_ai=bool(ia_local))
        first_video = Path(archive).parent / "resultados" / "corte_01.mp4"
        return archive, str(first_video) if first_video.exists() else None, covers, rows, message
    except Exception as exc:
        raise gr.Error(str(exc)) from exc


css = """
.gradio-container {max-width: 1120px !important; margin: auto !important;}
h1 {font-weight: 800 !important; letter-spacing: -0.04em;}
"""
with gr.Blocks(title="Clipador IA | Estúdio de Shorts", theme=gr.themes.Soft(), css=css) as demo:
    gr.Markdown(
        "# ✂️ Clipador IA — Estúdio de Shorts\n"
        "### Um vídeo longo → vários cortes verticais com legendas, capas e textos de publicação\n"
        "**Fontes:** link público do YouTube, Instagram, Facebook ou Vimeo (se acessível pelo extrator) "
        "e upload de arquivos próprios. **Sem assinatura de API ou marca d'água nossa.**"
    )
    if PUBLIC_MODE:
        gr.Markdown(
            "🧪 **Beta gratuito online**: envie arquivo até "
            + str(MAX_FILE_MB) + " MB ou vídeo de até 20 minutos. "
            "Para podcasts mais longos, a versão completa roda no Codespaces. "
            "Esta hospedagem tem recursos limitados e pode reiniciar automaticamente."
        )
    with gr.Row():
        with gr.Column():
            link = gr.Textbox(label="Link do vídeo", lines=1,
                              placeholder="https://www.youtube.com/watch?v=... ou link do Instagram/Facebook")
            arquivo = gr.File(label="Ou envie seu próprio vídeo",
                              file_types=[".mp4", ".mov", ".mkv", ".webm"], type="filepath")
            direitos = gr.Checkbox(
                label="Confirmo que possuo os direitos ou autorização para editar e publicar este vídeo")
        with gr.Column():
            quantidade = gr.Slider(label="Número de cortes", minimum=1, maximum=2 if PUBLIC_MODE else 6, value=2 if PUBLIC_MODE else 3, step=1)
            estilo = gr.Radio(["Dinâmico", "Humor leve", "Sóbrio"], value="Dinâmico",
                              label="Visual das legendas e cores",
                              info="Humor leve é um preset visual; não cria piadas artificiais.")
            qualidade = gr.Radio([720, 1080], value=720, label="Resolução",
                                 info="720p é mais leve em máquinas gratuitas.")
            cenas = gr.Checkbox(value=not PUBLIC_MODE, interactive=not PUBLIC_MODE, label="Analisar mudanças de cenas (mais lento)",
                                info="Melhora a priorização visual; não compreende sozinho o significado das imagens.")
            ia_local = gr.Checkbox(value=False, interactive=not PUBLIC_MODE, label="Reordenar trechos com IA local (Ollama)",
                                   info="Só funciona se o Ollama e um modelo local já estiverem instalados.")
    botao = gr.Button("✨ Produzir cortes", variant="primary")
    status = gr.Markdown()
    preview = gr.Video(label="Prévia do primeiro corte")
    tabela = gr.Dataframe(
        headers=["Corte", "Início (s)", "Fim (s)", "Prioridade heurística", "Título sugerido"],
        label="Trechos selecionados", interactive=False)
    galeria = gr.Gallery(label="Capas geradas a partir dos fotogramas", columns=3, height=280)
    download = gr.File(label="Baixar ZIP com MP4, SRT, ASS, capas e SEO")
    botao.click(processar,
                inputs=[link, arquivo, direitos, quantidade, estilo, qualidade, cenas, ia_local],
                outputs=[download, preview, galeria, tabela, status],
                show_progress="full")
    gr.Markdown(
        "⚠️ **Publicação e monetização:** a plataforma pode bloquear a obtenção de determinados links. "
        "O app não contorna DRM, login, paywall nem controles de acesso. "
        "Os cortes não garantem viralização, originalidade ou elegibilidade de monetização. "
        "Revise os vídeos, legendas, título, crédito e direitos autorais antes de publicar."
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
        max_file_size=f"{MAX_FILE_MB}mb")
