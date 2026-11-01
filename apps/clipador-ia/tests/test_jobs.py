"""Testes de fila e retomada V3, sem internet nem modelos pagos."""
import shutil
from pathlib import Path

import pytest

import engine
import jobs
import worker


def fake_source(tmp_path):
    source=tmp_path/"podcast_original.mp4"
    source.write_bytes(b"mp4 synthetic source" * 100)
    return source


def test_queue_persists_after_reopen(tmp_path):
    root=tmp_path/"storage"
    src=fake_source(tmp_path)
    task=jobs.submit("",str(src),True,2,"Dinâmico",720,root)
    assert jobs.get(task,root)["status"]=="queued"
    item=jobs.claim(root)
    assert item[0]==task
    assert item[1]["input_name"]=="input.mp4"
    assert jobs.claim(root) is None
    assert jobs.get(task,root)["attempts"]==1
    assert (jobs.folder(task,root)/"input.mp4").is_file()
    assert jobs.recover_running(root)==1
    assert jobs.claim(root)[0]==task
    assert jobs.get(task,root)["attempts"]==2


def test_rejects_invalid_or_unauthorized_inputs(tmp_path):
    root=tmp_path/"storage"
    src=fake_source(tmp_path)
    with pytest.raises(ValueError,match="autorização"):
        jobs.submit("",str(src),False,2,"Dinâmico",720,root)
    with pytest.raises(ValueError,match="Configuração"):
        jobs.submit("",str(src),True,2,"unknown",720,root)
    with pytest.raises(ValueError):
        jobs.submit("https://127.0.0.1/private",None,True,2,"Dinâmico",720,root)


def test_resume_after_crash_skips_transcribed_chunks_and_rendered_cuts(tmp_path,monkeypatch):
    root=tmp_path/"queue"
    src=fake_source(tmp_path)
    task=jobs.submit("",str(src),True,2,"Dinâmico",720,root)
    monkeypatch.setattr(engine,"probe_duration",lambda _:7200.0)
    calls={"asr":0,"render":0}
    def simulated_ffmpeg(args,**kwargs):
        Path(args[-1]).write_bytes(b"fake flac bytes")
    def simulated_asr(path,shift=0):
        calls["asr"]+=1
        return [engine.Segment(float(shift),float(shift+20),
                 f"Atenção! Uma história interessante para o bloco {shift}.")]
    def simulated_render(source,c,srt,dest,style,resolution):
        calls["render"]+=1
        if calls["render"]==2:
            raise RuntimeError("simulated worker death during second render")
        Path(dest).write_bytes(b"\x00\x00\x00\x18ftypisom"+b"x"*3000)
    def simulated_cover(source,c,title,dest):
        Path(dest).write_bytes(b"\xff\xd8"+b"x"*2000)

    monkeypatch.setattr(engine,"safe_run",simulated_ffmpeg)
    monkeypatch.setattr(engine,"_asr_segments",simulated_asr)
    monkeypatch.setattr(engine,"render_clip",simulated_render)
    monkeypatch.setattr(engine,"make_cover",simulated_cover)

    assert worker.worker_once(root)
    state=jobs.get(task,root)
    assert state["status"]=="failed"
    assert calls["asr"]==24
    assert calls["render"]==2
    assert len(list(jobs.folder(task,root).glob("transcript_*.json")))==24
    jobs.retry(task,root)
    assert worker.worker_once(root)
    state=jobs.get(task,root)
    assert state["status"]=="done"
    assert state["attempts"]==2
    assert calls["asr"]==24  # sem transcrever tudo de novo
    assert calls["render"]==3  # corte 1 também não renderizado novamente
    import zipfile
    archive=jobs.folder(task,root)/"cortes_prontos.zip"
    with zipfile.ZipFile(archive) as pack:
        assert "corte_01.mp4" in pack.namelist()
        assert "corte_02.mp4" in pack.namelist()


def test_running_job_recovered_by_fresh_worker(tmp_path,monkeypatch):
    root=tmp_path/"jobs"
    src=fake_source(tmp_path)
    job_id=jobs.submit("",str(src),True,1,"Sóbrio",720,root)
    jobs.claim(root)
    assert jobs.get(job_id,root)["status"]=="running"
    monkeypatch.setattr(worker,"worker_once",lambda root: False)
    worker.run(root=root,once=True)
    assert jobs.get(job_id,root)["status"]=="queued"


def test_retry_only_failed(tmp_path):
    root=tmp_path/"jobs"
    src=fake_source(tmp_path)
    job_id=jobs.submit("",str(src),True,1,"Sóbrio",720,root)
    with pytest.raises(ValueError):
        jobs.retry(job_id,root)
    jobs.claim(root)
    jobs.finish(job_id,"erro temporário",root)
    jobs.retry(job_id,root)
    assert jobs.get(job_id,root)["status"]=="queued"
