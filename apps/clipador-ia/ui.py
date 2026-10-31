"""Interface web responsiva do Clipador IA."""
import gradio as gr
from engine import generate


def processar(link, arquivo, direitos, quantidade, estilo, qualidade):
    try:
        return generate(link, arquivo, direitos, int(quantidade), estilo, int(qualidade))
    except Exception as exc:
        raise gr.Error(str(exc)) from exc


css = """
.gradio-container {max-width: 1120px !important; margin: auto !important;}
h1 {font-weight: 800 !important; letter-spacing: -0.04em;}
"""
with gr.Blocks(title="Clipador IA | Estúdio de Shorts", theme=gr.themes.Soft(), css=css) as demo:
    gr.Markdown(
        "# ✂️ Clipador IA\n"
        "### Transforme vídeos longos em Shorts, Reels e TikToks\n"
        "Cortes priorizados por fala, legendas incorporadas, edição vertical, capa e pacote de SEO. "
        "**100% local, sem chave de API ou marca d'água.**"
    )
    with gr.Row():
        with gr.Column():
            link = gr.Textbox(label="Link HTTPS do YouTube/Vimeo", placeholder="https://www.youtube.com/watch?v=...")
            arquivo = gr.File(label="Ou envie seu vídeo", file_types=[".mp4", ".mov", ".mkv", ".webm"], type="filepath")
            direitos = gr.Checkbox(label="Declaro que sou dono do conteúdo ou tenho autorização para editá-lo")
        with gr.Column():
            quantidade = gr.Slider(label="Quantidade de cortes", minimum=1, maximum=6, value=3, step=1)
            estilo = gr.Radio(["Dinâmico", "Humor leve", "Sóbrio"], value="Dinâmico", label="Tom da edição")
            qualidade = gr.Radio([720, 1080], value=720, label="Resolução vertical",
                                 info="720p é mais leve em máquinas gratuitas.")
            botao = gr.Button("✨ Gerar melhores cortes", variant="primary")
    status = gr.Markdown()
    tabela = gr.Dataframe(headers=["Corte", "Início (s)", "Fim (s)", "Prioridade", "Título sugerido"],
                          label="Cortes selecionados", interactive=False)
    galeria = gr.Gallery(label="Capas automáticas", columns=3, height=280)
    download = gr.File(label="Baixar pacote: MP4 + SRT + capas + SEO")
    botao.click(processar, inputs=[link, arquivo, direitos, quantidade, estilo, qualidade],
                outputs=[download, galeria, tabela, status], show_progress="full")
    gr.Markdown(
        "ℹ️ **Importante:** melhor trecho não significa viralização garantida. "
        "O app não ignora DRM nem restrições de plataformas. "
        "No modo gratuito em CPU, vídeos longos podem exigir bastante tempo de processamento."
    )

if __name__ == "__main__":
    demo.queue(default_concurrency_limit=1).launch(
        server_name="127.0.0.1", server_port=7860, share=False)
