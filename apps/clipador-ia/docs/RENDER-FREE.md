# Beta online no Render (plano Free)

- Código de execução igual ao do Codespaces, com recursos limitados.
- Dockerfile em `apps/clipador-ia/Dockerfile.render`, Docker context na raiz do repositório.
- Execução pública protegida por login Gradio **definido exclusivamente nas variáveis de ambiente do Render**.
- Variáveis: CLIPADOR_PUBLIC_MODE=1, CLIPADOR_AUTH_USER, CLIPADOR_AUTH_PASSWORD, CLIPADOR_WHISPER_MODEL=tiny, CLIPADOR_MAX_SECONDS=0 (duração ilimitada no aplicativo), CLIPADOR_MAX_BYTES=1000000000 (1 GB), CLIPADOR_SOURCE_HEIGHT=480, CLIPADOR_AUDIO_CHUNK_SECONDS=300, PORT=10000.
- Beta online: sem limite de minutos no código / 1 GB de arquivo / dois cortes / 720p. Análise visual e Ollama desativados nesta hospedagem para economizar recursos. Para podcasts maiores use Codespaces.
- Render Free suspende por inatividade, armazenamento é efêmero, pode faltar memória para ASR, e a plataforma pode bloquear alguns links. Serviço não deve ser tratado como pronto até teste real e log de deploy.
- Uma conta com acesso ao repositório ainda pode ver o código. Nunca commitar senhas ou arquivos de vídeos.
- Usuário confirma licença/autorização do vídeo. Monetização depende de originalidade, contribuição criativa e políticas da plataforma.

## Podcasters e vídeos de duas horas (ou mais)

A limitação de 20 minutos foi removida. A transcrição usa blocos de 5 minutos,
que são apagados a cada passagem. Isso diminui a memória usada pela transcrição
em um podcast de 2+ horas. O servidor Render Free ainda tem **512 MB de RAM**,
CPU limitada, armazenamento efêmero e pode reiniciar, portanto processar duas
horas **não está garantido** nem foi validado em produção.

Para vídeos bloqueados pela verificação antibot do YouTube, não há um bypass
oficial ou confiável. Oferecemos upload de arquivo autorizado, links de arquivos
públicos do Google Drive/Dropbox (se o extrator conseguir ler), ou usar o arquivo
original obtido no YouTube Studio pelo titular. A extração por link continua
sujeita a limitações das plataformas.

Para vídeo grande: use um arquivo comprimido de até 1 GB e mantenha a janela
aberta acompanhando o indicador de progresso. Para trabalho real de 2h+
de forma confiável, use Codespaces ou um worker com armazenamento persistente
e fila de processamento.
