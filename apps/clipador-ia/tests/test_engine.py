import pytest
from engine import Segment, package_metadata, score_text, select_clips, validate_url, _srt_timestamp


def test_safe_links():
    assert validate_url("https://youtu.be/abcdefgh") == "https://youtu.be/abcdefgh"
    with pytest.raises(ValueError):
        validate_url("http://localhost/admin")
    with pytest.raises(ValueError):
        validate_url("https://evil.test/download")
    with pytest.raises(ValueError):
        validate_url("https://youtube.com:8443/watch?v=x")


def test_rank_and_no_overlap():
    segments = [Segment(i * 5, (i + 1) * 5, ("Descobri um segredo incrível! " if i in (6, 7)
                 else "Conversando sobre o trabalho e as melhores dicas.")) for i in range(32)]
    clips = select_clips(segments, count=3)
    assert 1 <= len(clips) <= 3
    assert clips[0].score > 0
    for a in clips:
        for b in clips:
            if a is not b:
                overlap = max(0, min(a.end, b.end) - max(a.start, b.start))
                assert overlap <= 0.25 * min(a.end - a.start, b.end - b.start)


def test_seo_only_transcript():
    metadata = package_metadata("Como melhorar sua produtividade no trabalho? É uma dica prática e simples.", 1)
    assert "produtividade" in metadata["titulo"].lower()
    assert "#Shorts" in metadata["hashtags"]
    assert "viralização" not in metadata["titulo"].lower()


def test_empty_and_short():
    assert select_clips([]) == []
    clip = select_clips([Segment(0, 7, "Oi, tudo bem?")], 1)[0]
    assert clip.end >= 7
    assert score_text("Atenção! Um segredo importante.", 20) > 0
    assert _srt_timestamp(62.345) == "00:01:02,345"
