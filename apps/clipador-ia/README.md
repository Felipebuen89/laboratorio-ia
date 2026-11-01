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
