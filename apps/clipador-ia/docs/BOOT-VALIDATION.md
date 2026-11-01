# Boot validation: Clipador IA

A GitHub Actions workflow runs the **same** two commands declared by the Clipador devcontainer:
`bash apps/clipador-ia/scripts/setup.sh` and
`bash apps/clipador-ia/scripts/start.sh`.

The startup script checks that the local Gradio server responds with HTTP 200 on 127.0.0.1:7860 and saves diagnostics in `.runtime/server.log`.

**What this validates:** a clean Ubuntu GitHub Actions runner can install and start the app.

**What it does not validate:** the user-created Codespaces instance actually launched, remote port forwarding/authentication, ability to download a real YouTube/Instagram/Facebook video, or video virality.

Never change a Codespaces port to public merely to simplify testing.
