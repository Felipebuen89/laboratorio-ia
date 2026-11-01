"""Casos adversariais e fallback do clipador v2; nenhum download externo."""
from pathlib import Path
from types import SimpleNamespace

import pytest

from advanced import (CaptionWord, _safe_text, detect_scene_times, rerank_with_ollama,
                      select_visual_only, visual_bonus, words_for_clip, write_dynamic_ass)
from engine import Candidate, Segment, Word, validate_url, select_clips, package_metadata


@pytest.mark.parametrize("url", [
    "https://www.youtube.com/watch?v=ABCDEFG",
    "https://www.instagram.com/reel/ABC123/",
    "https://instagram.com/p/ABC123/",
    "https://www.facebook.com/watch/?v=123456",
    "https://fb.watch/ABC123/",
    "https://www.vimeo.com/1234567",
])
def test_supported_public_domains(url):
    assert validate_url(url) == url


@pytest.mark.parametrize("url", [
    "http://instagram.com/reel/x", "https://instagram.com.evil.test/reel/x",
    "https://facebook.com:8999/watch/?v=x", "https://facebook.com/",
    "https://evil.test/file", "https://www.facebook.com@localhost/reel/123",
    "file:///etc/passwd",
])
def test_deny_unapproved_links(url):
    with pytest.raises(ValueError):
        validate_url(url)


def test_precise_caption_timestamps_and_escaped_content(tmp_path: Path):
    seg = Segment(6, 9, "O segredo é {perigoso}!",
                  (Word(6, 6.4, "O"), Word(6.4, 7.0, "segredo"),
                   Word(7.0, 7.5, "é"), Word(7.5, 9, "{perigoso}!")))
    clip = Candidate(5.5, 9.5, seg.text, 82)
    words = words_for_clip([seg], clip)
    assert words[0].start == pytest.approx(0.5)
    assert words[-1].end == pytest.approx(3.5)
    out = tmp_path / "dynamic.ass"
    assert write_dynamic_ass([seg], clip, out) == 4
    txt = out.read_text(encoding="utf-8")
    assert "{perigoso}" not in txt
    assert "Dialogue: 0,0:00:00.50" in txt
    assert r"{\c" in txt
    assert _safe_text(r"{\r}") == "(r)"


def test_visual_fallback_and_bonus():
    assert visual_bonus(0, 50, [2, 8, 13, 22]) > visual_bonus(0, 50, [])
    clips = select_visual_only(150, [5, 33, 62, 95, 128], count=3)
    assert len(clips) >= 2
    assert all(0 <= c.start < c.end <= 150 for c in clips)
    assert select_visual_only(1, [], count=5) == []
    ranked = select_clips([Segment(i * 5, (i+1) * 5, "Uma história interessante termina aqui.")
                           for i in range(12)], count=2, scene_times=(15, 25, 35))
    assert ranked


def test_local_ai_offline_graceful():
    clips = [Candidate(0, 30, "Primeiro corte.", 40),
             Candidate(35, 65, "Segundo corte.", 38)]
    out, message = rerank_with_ollama(clips, enabled=False)
    assert out == clips and "heurística" in message.lower()
    out, message = rerank_with_ollama(clips, enabled=True, model="bad model/unsafe")
    assert out == clips and "inválido" in message


def test_scene_toggle_without_dependency(tmp_path):
    cuts, message = detect_scene_times(tmp_path / "missing.mp4", 60, enabled=False)
    assert cuts == []
    assert "desativada" in message


def test_no_invented_seo():
    m = package_metadata("", 2)
    assert m["titulo"] == "Corte 2"
    assert "não garantia" in m["aviso"]
