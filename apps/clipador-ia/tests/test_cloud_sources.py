"""Testes offline do importador de arquivos autorizados do Dropbox."""
from pathlib import Path
from types import SimpleNamespace

import pytest

from cloud_sources import download_dropbox, is_dropbox_link, normalize_dropbox_url
from engine import acquire_source, validate_url


class FakeReply:
    def __init__(self, status=200, headers=None, content=None):
        self.status_code = status
        self.headers = headers or {}
        self.content = content or []
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return False
    def iter_content(self, chunk_size=262144):
        yield from self.content


class FakeSession:
    def __init__(self, replies):
        self.replies = list(replies)
        self.visited = []
    def get(self, url, **kwargs):
        self.visited.append(url)
        assert kwargs.get("allow_redirects") is False
        return self.replies.pop(0)


SOURCE = "https://www.dropbox.com/scl/fi/ab2345/podcast.mp4?rlkey=key123&dl=0"
VIDEO_BYTES = b"\x00\x00\x00\x18ftypisom" + b"\x00" * 2000


def test_shared_link_forced_download_preserves_rlkey():
    url = normalize_dropbox_url(SOURCE)
    assert "rlkey=key123" in url
    assert "dl=1" in url and "dl=0" not in url
    assert is_dropbox_link(SOURCE)


@pytest.mark.parametrize("url", [
    "http://www.dropbox.com/scl/fi/abc/video.mp4",
    "https://www.dropbox.com.evil.invalid/scl/fi/abc/video.mp4",
    "https://www.dropbox.com:8443/scl/fi/abc/video.mp4",
    "https://www.dropbox.com@127.0.0.1/private",
    "https://www.dropbox.com/home",
    "https://www.dropbox.com/",
    "http://127.0.0.1:8080/private",
])
def test_dropbox_rejects_non_file_and_unsafe_links(url):
    with pytest.raises(ValueError):
        normalize_dropbox_url(url)


def test_dropbox_streams_public_video_with_redirect(tmp_path):
    session = FakeSession([
        FakeReply(302, {"Location": "https://dl.dropboxusercontent.com/s/ab2345/podcast.mp4"}),
        FakeReply(200, {"Content-Length": str(len(VIDEO_BYTES)), "Content-Type": "video/mp4"},
                  [VIDEO_BYTES[:600], VIDEO_BYTES[600:]]),
    ])
    target = download_dropbox(SOURCE, tmp_path, 100_000, session=session)
    assert target.name == "source.mp4"
    assert target.read_bytes() == VIDEO_BYTES
    assert len(session.visited) == 2
    assert "dl=1" in session.visited[0]


def test_dropbox_refuses_external_redirect(tmp_path):
    session = FakeSession([FakeReply(302, {"Location": "http://127.0.0.1:8080/secrets"})])
    with pytest.raises(ValueError, match="Redirecionamento"):
        download_dropbox(SOURCE, tmp_path, 100_000, session=session)
    assert len(session.visited) == 1


def test_dropbox_refuses_html_and_large_file(tmp_path):
    for reply in (
        FakeReply(200, {"Content-Type": "text/html"}, [b"<html>" * 400]),
        FakeReply(200, {"Content-Type": "application/octet-stream"}, [b"<html>" * 400]),
        FakeReply(200, {"Content-Type": "application/octet-stream"}, [VIDEO_BYTES]),
    ):
        session = FakeSession([reply])
        with pytest.raises(ValueError):
            download_dropbox(SOURCE, tmp_path, 1900, session=session)
        assert not (tmp_path / "source.mp4").exists()


def test_dropbox_backend_uses_dedicated_importer(tmp_path, monkeypatch):
    import cloud_sources
    called = []
    def fake_download(url, dest, max_bytes):
        called.append((url, max_bytes))
        path = dest / "source.mp4"
        path.write_bytes(VIDEO_BYTES)
        return path
    monkeypatch.setattr(cloud_sources, "download_dropbox", fake_download)
    monkeypatch.setenv("CLIPADOR_MAX_BYTES", "40000")
    path = acquire_source(SOURCE, None, tmp_path)
    assert path.exists()
    assert called == [(SOURCE, 40000)]
    assert validate_url(SOURCE) == SOURCE
