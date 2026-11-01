# Clipador IA — MVP gratuito

Aplicativo web mobile-first com processamento local de vídeos autorizados. O laboratório original permanece intacto: este código reside somente em apps/clipador-ia.

## O que funciona no MVP

1. Colar URL HTTPS pública de YouTube/Vimeo (quando a plataforma autorizar o acesso) ou enviar MP4/MOV/MKV/WEBM.
2. Transcrever fala com faster-whisper base em CPU, sem API ou assinatura.
3. Agrupar frases em cortes de aproximadamente 20–55 segundos; pontuar *heuristicamente* ganchos, densidade e clareza de fala; selecionar clipes com sobreposição limitada.
4. Renderizar vídeo vertical 9:16 com fundo desfocado e imagem preservada (sem crop de rostos), cor por estilo e fade inicial.
5. Inserir legendas curtas no vídeo e exportar .srt para correções.
6. Gerar capas verticais a partir de fotograma real, título, descrição, hashtags e palavras-chave fiéis ao trecho.
7. Baixar ZIP com MP4, SRT, capa e SEO em JSON. Sem marca d'água própria.

**Limites honestos**: Não existe predição confiável de viralização; o escore só ordena candidatos. Nesta versão não há rastreamento facial, edição fina de timeline, reconhecimento de melhores momentos sem fala, transições avançadas, publicação automática, sotaque/dublagem, trilha sonora nem humor escrito por LLM. "Humor leve" ajusta o visual; não inventa piadas nem altera as falas.

## Executar (Linux / Codespaces)

Requer Python 3.11+, FFmpeg com libass, ffprobe e fontes DejaVu. É um app separado; não modifica o devcontainer do Free Claude Code.

~~~bash
cd apps/clipador-ia
sudo apt-get update && sudo apt-get install -y ffmpeg fonts-dejavu-core
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python ui.py
~~~

Abrir porta privada 7860 no Codespaces. O app inicia apenas em 127.0.0.1; para acesso remoto via port forwarding privado, ajustar manualmente a ligação de rede do serviço e manter autenticação do Codespaces. **Nunca expor servidor público de processamento de links.** A primeira transcrição baixa pesos do modelo Whisper.

## Testes rápidos

~~~bash
cd apps/clipador-ia
python -m pip install pytest
pytest -q tests
~~~

O CI roda apenas testes de lógica (sem grandes downloads de modelos ou processamento de vídeos). O teste de ponta a ponta exige um vídeo autorizado e ambiente com FFmpeg. Não indicar como validado até obter um MP4 real.

## Segurança, direitos e custos

- Processar só vídeos próprios ou com permissão de reutilização. Não contorna DRM, paywall, cookies ou limitações de acesso.
- A licença dos modelos e da mídia deve ser verificada individualmente. O app **não** torna o conteúdo original automaticamente.
- Regras de monetização do YouTube exigem contribuição criativa substancial; legenda, cortes e efeitos mínimos podem continuar sendo *reused content*.
- Codespaces tem cotas gratuitas, mas consome CPU e armazenamento. 1080p na CPU pode ser lento. Não prometer execução contínua grátis.
- O repositório está público. Nunca commitar vídeos particulares, tokens, cookies ou arquivos gerados; use os diretórios temporários fora do Git.
- Para produção: autenticação, fila, isolamento dos workers, cotas por usuário, varredura de arquivo, limitação de download e expiração do armazenamento são obrigatórios.

## Pesquisa e referências técnicas

- [AutoClip de artbyjazi — MIT](https://github.com/artbyjazi/autoclip): pipeline local, Whisper, Ollama, legenda e reenquadramento.
- [AutoClip chinês de zhouxiaoka — MIT](https://github.com/zhouxiaoka/autoclip): vídeo, capa e publicação de um único link.
- [FunClip / ModelScope — MIT](https://github.com/modelscope/FunClip): clipping guiado por transcrição e falante.
- [Chopify — MIT](https://github.com/mehbul/chopify): edição de legenda, retomada de jobs e interface local.
- [Políticas de monetização do YouTube](https://support.google.com/youtube/answer/1311392)
- [Capas do Shorts no YouTube Studio](https://support.google.com/youtube/answer/72431)

Implementação própria inspirada em arquiteturas publicadas, sem copiar arquivos de concorrentes proprietários.


## Abrir pelo celular sem digitar comandos (Codespaces novo)

Use o GitHub autenticado e escolha **New codespace with options** no repositório, branch
feature/clipador-ia-mvp, configuração **Clipador IA - Gradio**.
A configuração separada fica em .devcontainer/clipador-ia/devcontainer.json.
Ela instala Python, FFmpeg, fontes e dependências ao criar o ambiente; o app inicia
automaticamente ao abrir o Codespaces. Na aba **Ports**, abra a porta privada 7860.
Não mude a visibilidade para Public. Não é hospedagem 24/7: o Codespaces dorme,
precisa ser reaberto e consome cota de CPU/armazenamento.

**Atenção:** a configuração padrão do laboratório segue sendo outra; o Codespaces antigo
não muda sozinho, e esta nova configuração ainda precisa ser testada no Codespaces real.
