"""Importador de links compartilhados do Dropbox para vídeos autorizados.

Não contorna YouTube, DRM nem autenticação. Usa lista de destinos HTTPS permitidos,
limite de bytes em streaming e valida o tipo de mídia após transferir.
"""
from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit, urljoin

import requests

MAX_REDIRECTS = 6
ALLOWED_SUFFIXES = ("dropbox.com", "dropboxusercontent.com")
EXTENSIONS = {".mp4", ".mov", ".mkv", ".webm"}


def is_dropbox_link(link: str) -> bool:
    try:
        host = (urlsplit(link).hostname or "").lower()
        return host in ("dropbox.com", "www.dropbox.com")
    except ValueError:
        return False


def _check_url(url: str) -> None:
    parts = urlsplit(url)
    host = (parts.hostname or "").lower()
    accepted = any(host == suffix or host.endswith("." + suffix)
                   for suffix in ALLOWED_SUFFIXES)
    if (parts.scheme != "https" or not accepted
            or parts.username or parts.password or parts.port is not None):
        raise ValueError("Redirecionamento não permitido para este domínio.")
    if not parts.path.startswith(("/s/", "/scl/fi/", "/s/dl/", "/s/raw/")):
        # Retornos no CDN Dropbox também podem usar caminhos /ap/... .
        if not host.endswith(".dropboxusercontent.com") and host != "dropboxusercontent.com":
            raise ValueError("Cole o link de compartilhamento de um arquivo do Dropbox.")


def normalize_dropbox_url(link: str) -> str:
    _check_url(link)
    parsed = urlsplit(link)
    if (parsed.hostname or "").lower() not in ("www.dropbox.com", "dropbox.com"):
        raise ValueError("Use o link compartilhado original do Dropbox.")
    params = dict(parse_qsl(parsed.query, keep_blank_values=True))
    params.pop("raw", None)
    params["dl"] = "1"
    return urlunsplit((parsed.scheme, parsed.netloc, parsed.path,
                       urlencode(params), ""))


def download_dropbox(url: str, work: Path, max_bytes: int,
                     *, session=None) -> Path:
    """Baixa um arquivo público via HTTPS e segue apenas redirecionamentos Dropbox.

    Não busca URLs arbitrárias (SSRF), não usa cookies/credenciais e não deixa
    mensagens de rede privadas ou conteúdo HTML entrar no motor de vídeo.
    """
    if max_bytes <= 0:
        raise ValueError("Limite de tamanho inválido.")
    current = normalize_dropbox_url(url)
    client = session or requests.Session()
    dest = work / "source.mp4"
    try:
        for _ in range(MAX_REDIRECTS + 1):
            _check_url(current)
            with client.get(current, stream=True, allow_redirects=False,
                            timeout=(8, 45), headers={"Accept": "application/octet-stream"}) as response:
                if response.status_code in (301, 302, 303, 307, 308):
                    location = response.headers.get("Location")
                    if not location:
                        raise ValueError("O Dropbox não retornou o endereço do arquivo.")
                    current = urljoin(current, location)
                    continue
                if response.status_code != 200:
                    raise ValueError("O Dropbox não liberou o arquivo. Confira se o compartilhamento permite downloads.")
                declared = response.headers.get("Content-Length", "").strip()
                if declared.isdecimal() and int(declared) > max_bytes:
                    raise ValueError("Arquivo maior do que o limite desta hospedagem.")
                kind = response.headers.get("Content-Type", "").lower()
                if "text/html" in kind or "application/json" in kind:
                    raise ValueError("O link abriu uma página, não um arquivo de vídeo.")
                file_name = response.headers.get("Content-Disposition", "")
                name_match = re.search(r'filename\*?=(?:UTF-8\'\')?["\']?([^"\'\r\n;]+)', file_name, flags=re.I)
                if name_match:
                    ext = Path(name_match.group(1)).suffix.lower()
                    if ext in EXTENSIONS:
                        dest = work / ("source" + ext)
                transferred = 0
                with dest.open("wb") as target:
                    for chunk in response.iter_content(chunk_size=256 * 1024):
                        if not chunk:
                            continue
                        transferred += len(chunk)
                        if transferred > max_bytes:
                            raise ValueError("Arquivo excede o limite permitido pelo aplicativo.")
                        target.write(chunk)
                if transferred < 1024:
                    raise ValueError("O arquivo recebido é vazio ou inválido.")
                # Rejeitar páginas HTML mascaradas como binário.
                with dest.open("rb") as inp:
                    header = inp.read(300).lstrip().lower()
                if header.startswith((b"<!doctype html", b"<html", b"<?xml")):
                    raise ValueError("O Dropbox retornou uma página, não um vídeo.")
                return dest
        raise ValueError("O Dropbox retornou redirecionamentos demais.")
    except (requests.RequestException, OSError) as exc:
        raise ValueError("Falha de rede durante a importação do Dropbox. Verifique o link público.") from None
    finally:
        if not dest.is_file() or dest.stat().st_size < 1024:
            dest.unlink(missing_ok=True)
