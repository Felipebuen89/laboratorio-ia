# Auditoria Clipador IA — 10 podcasts de 2 horas (2026-11-01)

## Resultado

**10/10 testes aprovados** — execução https://github.com/Felipebuen89/laboratorio-ia/actions/runs/41261316627

- 10 arquivos MP4 de duração real 7.200 segundos (2h), com áudio AAC e imagens sintéticas distintas.
- 10 links de formato Dropbox **simulados por transporte HTTP controlado**; não foram 10 links reais externos.
- Transcrições **simuladas**, já que os vídeos possuem áudio sintético, não diálogo.
- Cada caso validou a importação de origem, duração, seek, MP4 vertical, SRT, ASS, JPEG, ZIP e SEO.
- Execução da bateria: 101,71 segundos em GitHub Actions com FFmpeg. Não é tempo de processamento real de um podcast falado.
- Não comprova processamento real de 2h no Render Free (512 MB) nem desbloqueio de links do YouTube.

## Dez casos validados

| Caso | Cor / tom | Estilo | Corte (s) | Link simulado | Resultado |
|---|---|---|---|---|---|
| 1 | Azul 220 Hz | Dinâmico | 19,6–40,2 | HTTP com Content-Length | PASS |
| 2 | Verde 250 Hz | Humor leve | 119,7–140,2 | Redirecionamento HTTPS | PASS |
| 3 | Vermelho 280 Hz | Sóbrio | 699,6–720,2 | Sem Content-Length | PASS |
| 4 | Amarelo 310 Hz | Dinâmico | 1319,7–1340,2 | Redirect e sem tamanho | PASS |
| 5 | Roxo 340 Hz | Humor leve | 2189,7–2210,2 | HTTP normal | PASS |
| 6 | Turquesa 370 Hz | Sóbrio | 3109,7–3130,2 | Redirect | PASS |
| 7 | Laranja 400 Hz | Dinâmico | 4079,7–4100,2 | Sem tamanho declarado | PASS |
| 8 | Cinza 430 Hz | Humor leve | 5009,6–5030,2 | Redirect e sem tamanho | PASS |
| 9 | Rosa 460 Hz | Sóbrio | 6119,6–6140,2 | HTTP normal | PASS |
| 10 | Branco 490 Hz | Dinâmico | 7134,6–7155,2 | Redirect HTTPS | PASS |

## O erro original do YouTube continua independente

O app recebeu a mensagem "Sign in to confirm you're not a bot" para o vídeo do usuário. Não existe um método garantido de baixar vídeo de qualquer URL do YouTube via serviço gratuito. A política da API restringe baixar/importar audiovisual sem autorização prévia. OpusClip também registra incidentes de importação YouTube e orienta usar arquivos locais e Drive.

## Concorrentes consultados

- OpusClip: https://opuspro.instatus.com/history/1
- Vizard: https://help.vizard.ai/en/articles/8965410-why-do-i-get-error-messages-when-i-try-to-upload-from-link
- AutoClip (americano), com etapas retomáveis: https://github.com/artbyjazi/autoclip
- Chopify, com fila e cache de etapas: https://github.com/mehbul/chopify
- HotClip (chinês), fila persistente e retomada: https://github.com/xixihhhh/hotclip
- AutoClip chinês desktop/CLI: https://github.com/zhouxiaoka/autoclip
- YouTube Developer Policies: https://developers.google.com/youtube/terms/developer-policies
- Render Free: https://render.com/docs/free

## Próxima validação necessária para produção

Dez URLs **reais** de arquivos originais com direito de edição e download permitido (por exemplo Dropbox) e execução com transcrição real no worker definitivo. O Render Free perde arquivos locais em reinício, portanto a arquitetura de produção precisa de armazenamento persistente, fila e checkpoints. Não confundir esta bateria sintética de 10 projetos com uma comprovação real de dez podcasts baixados pela internet.
