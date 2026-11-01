# Clipador IA V3 — fila persistente com retomada (Codespaces)

## Entrega implementada

- Fila SQLite armazenada em `apps/clipador-ia/.runtime/v3/queue.sqlite3`, com estados, tentativas e progresso.
- O arquivo enviado é copiado para uma pasta por tarefa. Links autorizados são importados pelo worker, e o arquivo permanece na pasta do job para evitar baixá-lo novamente ao retomar.
- A transcrição é dividida em trechos de 300 s. Cada trecho concluído é salvo como `transcript_0000.json`, `transcript_0001.json` etc., com escrita atômica.
- As escolhas de cortes são preservadas em `candidates.json`.
- Cada MP4 é renderizado em arquivo temporário, validado por ffprobe e promovido por renomeação atômica. Capas e arquivos SEO também são preservados.
- ZIP só é criado quando os arquivos de saída estiverem disponíveis.
- Uma falha salva status e causa amigável; botão **Repetir tarefa com erro** aproveita os checkpoints.
- No Codespaces, `scripts/start.sh` inicia o worker automaticamente, com trava de processo (flock). Se reiniciar, recoloca tarefas que ficaram `running` na fila.
- No painel privado do Codespaces: botões para adicionar tarefa, consultar progresso, listar IDs salvos, repetir após falha e baixar ZIP quando concluído.

## Segregação e limites

**A nova fila NÃO está habilitada no Render Free.** O serviço web público permanece usando o processamento síncrono antigo, sem garantia de retomada. A V3 precisa do Codespaces com a configuração privada (sem cobrança extra garantida).

A fila guarda os dados dentro do **workspace do Codespaces**. Eles sobrevivem à reinicialização do processo, mas podem desaparecer se o Codespaces for excluído, reconstruído sem preservação de arquivos, se ficar sem espaço ou se houver limpeza. Não é ainda uma fila distribuída nem um armazenamento externo durável. O Codespaces pode ser suspenso por inatividade; trabalhos não continuam se a máquina estiver parada.

**Os dados de mídia e transcrição são privados**, não devem ir ao GitHub. Nunca torne pública a porta do Codespaces. Não inclua tokens de YouTube/Dropbox, credenciais ou arquivos sensíveis no repositório.

Nenhum banco Supabase existente de outros projetos foi alterado. Para operação contínua: criar projeto/banco próprio, storage persistente de arquivos e worker dedicado com quota, fila de recuperação e autenticação por usuário.

## Testes automatizados

`tests/test_jobs.py` cobre:

1. Fila criada e lida em conexões SQLite diferentes.
2. Entradas inválidas, ausência de direitos e links não aprovados.
3. Podcast sintético de duas horas em 24 segmentos de ASR simulada; travamento no segundo corte; nova tentativa sem retranscrever os 24 segmentos nem refazer o primeiro corte.
4. Recuperação de tarefa `running` após reiniciar worker.
5. Bloqueio de repetição de tarefas que não falharam.

Testes de lógica **não comprovam** um podcast falado real de duas horas, estabilidade de infraestrutura externa ou importação garantida de qualquer link do YouTube.

## Operação

```bash
cd apps/clipador-ia
source .venv/bin/activate
python worker.py --once   # para processar uma tarefa e sair
python worker.py          # para processar continuamente
```

No Codespaces configurado para Clipador IA, `start.sh` executa worker e interface automaticamente. A aplicação precisa rodar com `CLIPADOR_ENABLE_LOCAL_QUEUE=1`; o startup do Codespaces já define esta variável. Para usar a fila, marque a autorização e clique **Adicionar vídeo à fila**, depois **Atualizar progresso**. Para recuperar o identificador depois de fechar o navegador, clique **Listar tarefas**.

O processamento pesado continua dependente da CPU e da RAM do Codespaces e do direito de acesso à mídia. Shorts, legendar ou zoom não tornam conteúdos de terceiros automaticamente monetizáveis.
