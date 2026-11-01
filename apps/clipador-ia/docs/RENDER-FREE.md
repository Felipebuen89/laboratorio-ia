# Beta online no Render (plano Free)

- Código de execução igual ao do Codespaces, com recursos limitados.
- Dockerfile em `apps/clipador-ia/Dockerfile.render`, Docker context na raiz do repositório.
- Execução pública protegida por login Gradio **definido exclusivamente nas variáveis de ambiente do Render**.
- Variáveis: CLIPADOR_PUBLIC_MODE=1, CLIPADOR_AUTH_USER, CLIPADOR_AUTH_PASSWORD, CLIPADOR_WHISPER_MODEL=tiny, CLIPADOR_MAX_SECONDS=1200, CLIPADOR_MAX_BYTES=100000000, PORT=10000.
- Limites online: 20 minutos / 100 MB / dois cortes / 720p. Análise visual e Ollama desativados nesta hospedagem para economizar recursos. Para podcasts maiores use Codespaces.
- Render Free suspende por inatividade, armazenamento é efêmero, pode faltar memória para ASR, e a plataforma pode bloquear alguns links. Serviço não deve ser tratado como pronto até teste real e log de deploy.
- Uma conta com acesso ao repositório ainda pode ver o código. Nunca commitar senhas ou arquivos de vídeos.
- Usuário confirma licença/autorização do vídeo. Monetização depende de originalidade, contribuição criativa e políticas da plataforma.
