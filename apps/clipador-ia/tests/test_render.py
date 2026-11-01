"""Teste real de renderização com um vídeo sintético livre de direitos."""
import shutil
import subprocess
from pathlib import Path

import pytest

from engine import Candidate, Segment, make_cover, probe_duration, render_clip, write_captions


@pytest.mark.skipif(not shutil.which("ffmpeg") or not shutil.which("ffprobe"),
                    reason="FFmpeg não está disponível")
def test_render_mp4_capa_legenda(tmp_path: Path):
    pytest.importorskip("PIL")
    source = tmp_path / "sample.mp4"
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error",
         "-f", "lavfi", "-i", "color=c=blue:s=640x360:r=24:d=4",
         "-f", "lavfi", "-i", "sine=frequency=440:duration=4",
         "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac",
         "-shortest", str(source)],
        check=True, timeout=35)
    c = Candidate(0.0, 3.0, "Atenção, esta é uma legenda de teste!", 80.0)
    captions = tmp_path / "corte_01.srt"
    video = tmp_path / "corte_01.mp4"
    cover = tmp_path / "corte_01_capa.jpg"
    write_captions([Segment(0, 3, c.text)], c, captions)
    assert "-->" in captions.read_text(encoding="utf-8")
    render_clip(source, c, captions, video, "Dinâmico", 720)
    make_cover(source, c, "Como fazer um corte melhor", cover)
    assert video.stat().st_size > 10_000
    assert cover.stat().st_size > 5_000
    assert 2.5 <= probe_duration(video) <= 3.5
