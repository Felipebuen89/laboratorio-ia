"""Teste real de renderização com um vídeo sintético livre de direitos."""
import shutil
import subprocess
from pathlib import Path

import pytest

from engine import Candidate, Segment, Word, make_cover, probe_duration, render_clip, write_captions, transcribe
from advanced import write_dynamic_ass


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
    pieces = (
        Word(0.0, 0.6, "Atenção,"), Word(0.6, 1.0, "esta"),
        Word(1.0, 1.5, "é"), Word(1.5, 2.0, "uma"),
        Word(2.0, 2.5, "legenda"), Word(2.5, 3.0, "de teste!"),
    )
    segments = [Segment(0, 3, c.text, pieces)]
    write_captions(segments, c, captions)
    ass = captions.with_suffix(".ass")
    assert write_dynamic_ass(segments, c, ass, "Dinâmico") == 6
    assert "Dialogue: 0" in ass.read_text(encoding="utf-8")
    assert "-->" in captions.read_text(encoding="utf-8")
    render_clip(source, c, captions, video, "Dinâmico", 720)
    make_cover(source, c, "Como fazer um corte melhor", cover)
    assert video.stat().st_size > 10_000
    assert cover.stat().st_size > 5_000
    assert 2.5 <= probe_duration(video) <= 3.5



@pytest.mark.skipif(not shutil.which("ffmpeg") or not shutil.which("ffprobe"),
                    reason="FFmpeg não disponível")
def test_video_without_audio_uses_visual_mode(tmp_path: Path, monkeypatch):
    import engine
    source = tmp_path / "silent.mp4"
    subprocess.run(["ffmpeg", "-y", "-v", "error",
                    "-f", "lavfi", "-i", "color=c=red:s=640x360:r=24:d=3",
                    "-an", "-c:v", "libx264", str(source)],
                   check=True, timeout=35)
    monkeypatch.setattr(engine, "speech_model",
                        lambda: (_ for _ in ()).throw(AssertionError("Whisper não deve abrir")))
    assert transcribe(source) == []
    empty_srt = tmp_path / "sem_audio.srt"
    write_captions([], Candidate(0, 2.8, "", 1), empty_srt)
    output = tmp_path / "sem_audio.mp4"
    render_clip(source, Candidate(0, 2.8, "", 1), empty_srt, output)
    assert output.stat().st_size > 1000
