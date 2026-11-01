"""10 projetos sintéticos de >= 2h, importados por URL Dropbox SIMULADA.

Cada projeto gera um MP4 original com imagem e áudio de 2 horas (cores,
frequências e janelas diferentes), passa pelo downloader real com HTTP
mockado, gera MP4 9:16, SRT, ASS, capa e ZIP. Não é prova de YouTube real,
Dropbox real, qualidade da IA ou capacidade do Render Free em produção.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import zipfile
from pathlib import Path

import pytest

import cloud_sources
import engine
from engine import Segment, Word

CASES = [
    (1, "azul", "002C9B", 220, "Dinâmico", 20.0, False, False),
    (2, "verde", "07823D", 250, "Humor leve", 120.0, True, False),
    (3, "vermelho", "B01E2C", 280, "Sóbrio", 700.0, False, True),
    (4, "amarelo", "DCAF20", 310, "Dinâmico", 1320.0, True, True),
    (5, "roxo", "7043BF", 340, "Humor leve", 2190.0, False, False),
    (6, "turquesa", "169EA8", 370, "Sóbrio", 3110.0, True, False),
    (7, "laranja", "D56A13", 400, "Dinâmico", 4080.0, False, True),
    (8, "cinza", "687581", 430, "Humor leve", 5010.0, True, True),
    (9, "rosa", "BA528A", 460, "Sóbrio", 6120.0, False, False),
    (10, "branco", "BBC6D8", 490, "Dinâmico", 7135.0, True, True),
]


class Streamed:
    def __init__(self, payload: bytes, *, redirect: str | None,
                 content_length: bool, filename: str | None):
        self.payload = payload
        self.redirect = redirect
        self.content_length = content_length
        self.filename = filename
        self.calls = 0

    def get(self, url, *, stream, allow_redirects, timeout, headers):
        assert url.startswith("https://")
        assert stream and not allow_redirects
        self.calls += 1
        if self.redirect and self.calls == 1:
            return Reply(302, {"Location": self.redirect}, b"")
        h = {"Content-Type": "application/octet-stream"}
        if self.content_length:
            h["Content-Length"] = str(len(self.payload))
        if self.filename:
            h["Content-Disposition"] = f'attachment; filename="{self.filename}"'
        return Reply(200, h, self.payload)


class Reply:
    def __init__(self, status, headers, payload):
        self.status_code = status
        self.headers = headers
        self.payload = payload
    def __enter__(self): return self
    def __exit__(self, *args): return False
    def iter_content(self, chunk_size):
        for i in range(0, len(self.payload), chunk_size):
            yield self.payload[i:i + chunk_size]


def build_two_hour_source(output: Path, color: str, frequency: int):
    """1 frame/s + AAC. O contêiner realmente dura duas horas."""
    subprocess.run(
        ["ffmpeg", "-nostdin", "-y", "-hide_banner", "-loglevel", "error",
         "-f", "lavfi", "-i", f"color=c=0x{color}:s=160x90:r=1",
         "-f", "lavfi", "-i", f"sine=frequency={frequency}:sample_rate=8000",
         "-t", "7200", "-c:v", "libx264", "-preset", "ultrafast",
         "-crf", "43", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-b:a", "12k", "-ar", "8000",
         "-movflags", "+faststart", str(output)],
        timeout=180, check=True)


@pytest.mark.slow
@pytest.mark.parametrize("index,colorname,color,frequency,style,at,redirect,no_size", CASES)
def test_ten_two_hour_projects_from_links(
    index, colorname, color, frequency, style, at,
    redirect, no_size, tmp_path, monkeypatch
):
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        pytest.skip("FFmpeg necessário")
    source = tmp_path / f"podcast-{index:02}-{colorname}.mp4"
    build_two_hour_source(source, color, frequency)
    duration = engine.probe_duration(source)
    assert duration >= 7199.5, (index, duration)
    raw = source.read_bytes()
    assert raw.startswith(b"\x00") and b"ftyp" in raw[:20]

    shared = (f"https://www.dropbox.com/scl/fi/project{index:02}/"
              f"podcast{index:02}.mp4?rlkey=testing{index:02}&dl=0")
    cdn = f"https://dl.dropboxusercontent.com/s/project{index:02}/podcast{index:02}.mp4"
    session = Streamed(
        raw, redirect=cdn if redirect else None,
        content_length=not no_size, filename=f"podcast{index:02}.mp4",
    )
    monkeypatch.setattr(cloud_sources.requests, "Session", lambda: session)
    monkeypatch.setenv("CLIPADOR_MAX_SECONDS", "0")
    monkeypatch.setenv("CLIPADOR_MAX_BYTES", str(max(100000000, len(raw) + 1024)))
    monkeypatch.delenv("CLIPADOR_PUBLIC_MODE", raising=False)

    # ASR substituída porque cada fonte é sintética (sem diálogo).
    # Posição varia entre o início e o fim do vídeo de 2h.
    words = (
        Word(at, at + 2, "Descubra"), Word(at + 2, at + 4, "uma"),
        Word(at + 4, at + 6, "história"), Word(at + 6, at + 8, "incrível!"),
    )
    transcript = [Segment(
        at, at + 20,
        f"Descubra uma história incrível! Projeto {index}. "
        "Esta é uma fala fictícia para testar legendas e SEO.",
        words
    )]
    monkeypatch.setattr(engine, "transcribe", lambda _: transcript)
    archive, gallery, rows, status = engine.generate(
        shared, None, True, 1, style, 720,
        scene_analysis=False, local_ai=False
    )
    assert session.calls == (2 if redirect else 1)
    assert len(rows) == 1
    assert Path(gallery[0]).is_file()
    with zipfile.ZipFile(archive) as z:
        names = z.namelist()
        assert {"corte_01.mp4", "corte_01.srt", "corte_01.ass",
                "corte_01_capa.jpg", "corte_01_seo.json"} <= set(names)
        meta = json.loads(z.read("corte_01_seo.json"))
        assert meta["fonte"] == shared
        assert meta["inicio"] >= 0 and meta["fim"] <= 7200
        extract = tmp_path / f"rendered_{index}.mp4"
        extract.write_bytes(z.read("corte_01.mp4"))
        assert extract.stat().st_size > 1000
        assert engine.probe_duration(extract) > 5

    print(f"PASS projeto {index}/10 | origem={duration:.1f}s "
          f"| link=simulado | corte={rows[0][1]}-{rows[0][2]}s "
          f"| pacote={Path(archive).stat().st_size} bytes")
