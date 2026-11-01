# Clipador IA v2 — evolução do MVP

Um vídeo ou podcast longo autorizado pode ser transformado em até seis cortes verticais, com legenda sincronizada por palavra, capa e pacote de publicação. O app roda em ambiente privado no GitHub Codespaces (quando iniciado) e não precisa de APIs comerciais.

## Recursos da v2

- Links HTTPS públicos de YouTube, Instagram, Facebook e Vimeo, sujeitos à disponibilidade dos extratores do yt-dlp. Não usa login, cookies, DRM ou técnicas de evasão; se a plataforma bloquear, envie um arquivo autorizado.
- Whisper base em CPU com timestamps por palavra, SRT e legenda dinâmica ASS com destaque da palavra ativa incorporada ao MP4.
- Pontuação heurística de gancho inicial, densidade, fechamento de frase e bônus para mudanças de cena do PySceneDetect.
- IA local (Ollama) opcional, desativada por padrão: ordena uma shortlist de cortes já selecionados sem inventar falas nem timestamps. Configure a variável CLIPADOR_OLLAMA_MODEL para um modelo local (exemplo qwen2.5:3b), que precisa ser instalado à parte com RAM suficiente. Se não houver IA, a seleção heurística continua.
- Se não houver fala, pode propor cortes visuais experimentais. Não reconhece humor, história ou emoção somente pelas imagens.
- Prévia do primeiro vídeo e download ZIP com MP4, SRT, ASS, capa e SEO JSON.
- Visual mobile-friendly, sem marca d'água própria.

## O que ainda falta

Sem análise semântica visual real, tracking de rosto, efeitos de meme, narração gerada, geração de piadas, publicação automática, previsão real de viralização, teste real com links Instagram/Facebook, nem confirmação de elegibilidade para monetização. O preset Humor leve só altera a estética.

**Monetização:** ter autorização de uso não garante aceitação pelas políticas de conteúdo reutilizado. É necessária contribuição original substancial e revisão humana.

## Abrir no celular

1. Abra https://github.com/Felipebuen89/laboratorio-ia, autenticado no GitHub.
2. Use Code → Codespaces → New with options, branch main e a configuração Clipador IA - Gradio (privado), no caminho .devcontainer/clipador-ia/devcontainer.json.
3. Um Codespaces novo instala as dependências e tenta iniciar o app. Abra a porta 7860 na aba Ports com visibilidade Private. **Ainda não foi validado num Codespaces real.**
4. Cole link ou envie vídeo autorizado; escolha cortes e estilo, clique Produzir cortes.
5. Revise cada MP4, legenda, capa e texto antes de publicar.

**Segurança:** o repositório é público. Nunca envie tokens, cookies, vídeos particulares ou senhas para o GitHub. O Codespaces consome cotas de CPU e armazenamento e não é hospedagem contínua grátis.

## Referências de engenharia

- https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md
- https://github.com/Breakthrough/PySceneDetect
- https://github.com/SYSTRAN/faster-whisper
- https://github.com/artbyjazi/autoclip
- https://support.google.com/youtube/answer/1311392

Não copiamos código de concorrentes proprietários.

---

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

O CI valida cinco testes (incluindo geração real de MP4 sintético com legendas e capa), instalação das dependências e importação da interface Gradio. Ainda **não** valida transcrição Whisper em vídeo falado, escolha editorial de melhores trechos nem acesso real ao Codespaces.

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
main, configuração **Clipador IA - Gradio (privado)**.
A configuração separada fica em .devcontainer/clipador-ia/devcontainer.json.
Acesse https://github.com/Felipebuen89/laboratorio-ia e abra **Code > Codespaces > New with options**.
Ela instala Python, FFmpeg, fontes e dependências ao criar o ambiente; o app inicia
automaticamente ao abrir o Codespaces. Na aba **Ports**, abra a porta privada 7860.
Não mude a visibilidade para Public. Não é hospedagem 24/7: o Codespaces dorme,
precisa ser reaberto e consome cota de CPU/armazenamento.

**Atenção:** a configuração padrão do laboratório segue sendo outra; o Codespaces antigo
não muda sozinho, e esta nova configuração ainda precisa ser testada no Codespaces real.
