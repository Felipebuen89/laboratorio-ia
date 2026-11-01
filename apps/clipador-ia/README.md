# Entrada de arquivo por link: alternativa estável ao YouTube

**Por que o link YouTube falha?** O servidor do Render recebe a mensagem
"Sign in to confirm you're not a bot", que é uma restrição do YouTube.
Não existe uma API oficial de download do MP4 de qualquer vídeo público.
O nosso aplicativo não usa cookies de usuário, proxies rotativos, captcha
ou métodos de contorno. Um URL público do YouTube **não equivale** a uma
URL de um arquivo MP4 autorizado para download.

## Para usar somente um link no Clipador IA

1. Utilize a mídia **original que você possui ou tem autorização de editar**.
   Se o vídeo for seu e você só tiver uma cópia no YouTube, o YouTube Studio
   oferece a função oficial de baixar vídeos que você publicou.
2. Guarde a mídia num serviço que permita baixar o arquivo, como Dropbox.
   Configure o compartilhamento para permitir download ao destinatário.
3. Copie o link compartilhado do **arquivo MP4**, no formato
   \`https://www.dropbox.com/scl/fi/.../podcast.mp4?rlkey=...&dl=0\`.
4. Cole o link no Clipador IA. O importador usa \`dl=1\`, preservando a chave
   \`rlkey\`, e recebe o arquivo por streaming com limites e checagem de domínio.
   Não é necessário reenviar o arquivo pelo formulário a cada vez.

Links protegidos por login, vídeos de outros autores sem autorização ou
arquivos cujo dono desativou o download não são importáveis por esse método.
Google Drive permanece como tentativa de importação sujeita a permissões e
restrições; esta versão dedica um importador robusto especificamente ao Dropbox.

**Atenção:** importação bem-sucedida não significa processamento gratuito
ilimitado. Render Free tem memória, CPU e armazenamento efêmero; podcasts
de 2h ainda podem exigir um worker maior ou Codespaces. Não declare o
serviço pronto para carga de produção antes de testes com vídeo real.

Referências oficiais:
- https://support.google.com/youtube/answer/56100
- https://developers.google.com/youtube/terms/developer-policies
- https://help.dropbox.com/share/force-download
- https://render.com/docs/free

---

## Atualização: podcasts longos e links de arquivos

- O bloqueio de **20 minutos foi removido**. No Render, `CLIPADOR_MAX_SECONDS=0`
  representa ausência de limite automático de duração; o upload continua limitado
  a 1 GB e o processamento gratuito pode falhar por CPU/memória/reinício.
- O áudio é transcrito em segmentos de 5 minutos, com progresso visível para
  podcasts de 2 horas ou mais, reduzindo a memória de transcrição.
- Além do YouTube/Instagram/Facebook/Vimeo, o app tenta ler **links públicos
  de arquivos do Google Drive ou Dropbox** autorizados, sem ignorar login/DRM.
- Não é possível garantir download de qualquer link do YouTube pelo Render.
  Quando bloqueado por verificação antibot, use o arquivo original autorizado.
- Testes automatizados simulam podcasts com mais de 2 horas. A execução real
  de 2h em Render Free **ainda não foi validada**.

---

# Publicação em um clique no Render (opcional)

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https%3A%2F%2Fgithub.com%2FFelipebuen89%2Flaboratorio-ia)

O botão utiliza o arquivo [render.yaml](https://github.com/Felipebuen89/laboratorio-ia/blob/main/render.yaml), configura um serviço Docker no plano **free** e gera uma senha privada dentro do Render. **Não é um link para o app já publicado**: o proprietário da conta precisa revisar e aprovar a criação no painel Render.

Login após publicar: usuário `felipe`. A senha é gerada pelo Render e pode ser consultada nas variáveis de ambiente do serviço no Dashboard. Não cole a senha no GitHub. A hospedagem gratuita tem limites e pode suspender serviços inativos; não é processamento ilimitado de podcasts.

---

# ✂️ Clipador IA v2 — Cortes inteligentes sem assinatura de API

Aplicativo de edição para podcasts, entrevistas e vídeos longos **próprios ou licenciados**, acessível pelo navegador quando o Codespaces privado está ativo.

## O que a v2 faz

- Recebe arquivo local MP4/MOV/MKV/WEBM ou link público HTTPS do YouTube, Instagram, Facebook ou Vimeo, conforme o extrator yt-dlp permitir. Não contorna bloqueios, DRM, login ou paywall.
- Transcreve falas em CPU com faster-whisper e timestamps por palavra.
- Propõe até 6 cortes com critérios heurísticos de ganchos, densidade da fala, fechamento de frase e mudanças visuais detectadas pelo PySceneDetect.
- Opcional: modelo gratuito rodando **localmente em Ollama** pode reordenar candidatos. Requer instalação separada, memória e espaço; não está conectado automaticamente.
- Em vídeos sem fala, oferece trechos visuais experimentais (não compreende a história só pela imagem).
- Edita em 9:16 com fundo desfocado, cor e fade; gera legendas embutidas com palavra destacada, SRT e ASS.
- Gera capas usando fotogramas, título e descrição fiéis à transcrição, hashtags e arquivo JSON de SEO.
- Mostra prévia do primeiro corte e exporta o pacote ZIP com vídeos e materiais.

## O que ainda NÃO faz

Não faz previsão real de viralização, interpretação semântica de cenas de humor, tracking facial, edição de memes/transições complexas, narração gerada, publicação automática ou certificação de originalidade/monetização. O estilo Humor leve só muda o visual. **Efeitos e legendas não tornam automaticamente um vídeo reutilizado monetizável.** Verifique autorização e acrescente contribuição criativa substancial.

## Abrir pelo iPhone/Android sem terminal manual

1. Entre em https://github.com/Felipebuen89/laboratorio-ia com a conta GitHub.
2. Abra **Code → Codespaces → New with options**, escolha branch main e o devcontainer **Clipador IA - Gradio (privado)**, em .devcontainer/clipador-ia/devcontainer.json.
3. A preparação automática instala Python, FFmpeg, fontes e bibliotecas; o app tenta iniciar pela porta 7860. Abra-a na aba **Ports**, visibilidade **Private**.
4. Marque a autorização de direitos, cole seu link ou envie vídeo próprio e selecione as opções.
5. Revise o resultado antes de publicar.

Esta abertura num Codespaces real **ainda não foi testada**. A configuração principal do Laboratório IA não foi alterada. GitHub Codespaces tem cotas gratuitas e pode gerar cobrança fora dos limites; não é hospedagem permanente.

## Testes e segurança

O GitHub Actions verifica sintaxe, interface e teste de vídeo sintético com MP4, SRT, ASS, capa e ZIP. Isso **não comprova** acesso a links reais, acerto editorial ou transcrição de podcast em produção. Sem vídeo de terceiros ou credenciais nos testes.

- Repositório público = somente código. Não commitar segredos, vídeos particulares nem cookies.
- Servidor só privado, acesso via Codespaces autenticado, sem compartilhamento público.
- Os processamentos devem ser apagados regularmente do armazenamento temporário. Para produção multiusuário, faltam autenticação, filas e limites robustos de recursos.

## Bibliotecas e pesquisa

- https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md
- https://github.com/SYSTRAN/faster-whisper
- https://github.com/Breakthrough/PySceneDetect
- https://github.com/artbyjazi/autoclip
- https://github.com/mehbul/chopify
- https://support.google.com/youtube/answer/1311392

Implementação própria, sem copiar código fechado de concorrentes.
