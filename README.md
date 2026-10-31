# Laboratório IA — Free Claude Code

Ambiente de desenvolvimento preparado para GitHub Codespaces, sem Replit.

## O que já foi configurado

- `.devcontainer/devcontainer.json` instala automaticamente as ferramentas em **novos Codespaces** ou quando houver **reconstrução do contêiner**.
- `scripts/bootstrap-codespaces.sh` instala Free Claude Code **6.18.5** e o cliente oficial Claude Code **2.1.308**, sem pedir para copiar comandos.
- A execução de instalação foi **testada com sucesso** em um ambiente isolado do GitHub Actions:
  https://github.com/Felipebuen89/laboratorio-ia/actions/runs/41213834073

## Limitações importantes

- O Codespaces chamado **unearthly cemetery** foi criado *antes* desta configuração. Ele **não recebe automaticamente** os programas só porque o repositório recebeu novos commits.
- A atualização desse Codespaces exige sincronizar o repositório e reconstruir o contêiner; alternativamente, criar um novo Codespaces já com esta configuração.
- O teste no GitHub Actions **não prova** que os programas estejam instalados no Codespaces existente.
- **Nenhuma chave de IA foi adicionada**. É necessário escolher e autenticar um provedor (por exemplo NVIDIA NIM ou OpenRouter) para executar solicitações de programação.
- O projeto Free Claude Code não oferece acesso ilimitado e gratuito aos modelos Anthropic; provedores gratuitos têm cotas e limites.
- `fcc-server` **não inicia automaticamente**, para evitar expor o painel sem autenticação.
- Este repositório é **público**: não adicione senhas, tokens, dados de clientes ou informações confidenciais.

## Referências

- [Free Claude Code](https://github.com/Alishahryar1/free-claude-code)
- [NVIDIA NIM](https://build.nvidia.com/settings/api-keys)
- [OpenRouter](https://openrouter.ai/keys)
