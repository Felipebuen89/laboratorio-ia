"""Worker Clipador IA V3: transcrição em blocos e checkpoints retomáveis.

Executar: python worker.py --once (uma tarefa) ou python worker.py (fila contínua).
O trabalho fica em .runtime/v3 dentro do Codespaces. Não funciona sozinho
na hospedagem Render Free e não salva arquivos fora do Codespaces.
"""
from __future__ import annotations

import argparse
import fcntl
import json
import math
import os
import shutil
import time
import zipfile
from dataclasses import asdict
from pathlib import Path

import jobs
import engine


def _segments_from_json(payload):
    return [engine.Segment(float(row["start"]), float(row["end"]),str(row["text"]),
            tuple(engine.Word(float(w["start"]),float(w["end"]),str(w["text"]))
                  for w in row.get("words",[]))) for row in payload]


def _load_source(dest: Path, spec: dict) -> Path:
    if spec.get("input_name"):
        source = dest / spec["input_name"]
        if not source.is_file():
            raise ValueError("Arquivo original não está disponível no armazenamento da tarefa.")
    else:
        candidates = [p for p in dest.glob("source.*")
                      if p.suffix.lower() in (".mp4",".mov",".webm",".mkv")]
        source = candidates[0] if candidates else engine.acquire_source(spec["url"],None,dest)
    try:
        engine.probe_duration(source)
        return source
    except Exception:
        if not spec.get("input_name"):
            source.unlink(missing_ok=True)
        raise


def _transcript(source: Path, duration: float, folder: Path, job_id: str, root: Path):
    # Checkpoint por segmento de 5min: reinício não repete blocos já confirmados.
    chunk_seconds = int(os.getenv("CLIPADOR_AUDIO_CHUNK_SECONDS","300"))
    chunk_seconds = max(60,min(600,chunk_seconds))
    nchunks = math.ceil(duration/chunk_seconds)
    segments = []
    for i in range(nchunks):
        checkpoint = folder / f"transcript_{i:04d}.json"
        cached = jobs.load_json(checkpoint)
        if cached is None:
            temporary = folder / f"segment_{i:04d}.flac"
            offset=i*chunk_seconds
            try:
                engine.safe_run(["ffmpeg","-nostdin","-y","-hide_banner","-loglevel","error",
                                 "-ss",str(offset),"-t",str(min(chunk_seconds,duration-offset)),
                                 "-i",str(source),"-vn","-ac","1","-ar","16000",
                                 "-c:a","flac",str(temporary)])
                parts = engine._asr_segments(temporary,shift=offset)
                cached = [asdict(s) for s in parts]
                jobs.atomic_json(checkpoint,cached)
            finally:
                temporary.unlink(missing_ok=True)
        segments.extend(_segments_from_json(cached))
        jobs.update(job_id,"transcribing",0.08+0.61*(i+1)/nchunks,root)
    return segments


def process(job_id: str, spec: dict, root: Path=jobs.ROOT) -> Path:
    if not spec.get("rights"):
        raise ValueError("Sem confirmação de autorização de uso.")
    folder=jobs.folder(job_id,root)
    folder.mkdir(parents=True,exist_ok=True)
    jobs.update(job_id,"importing",0.01,root)
    source=_load_source(folder,spec)
    duration=engine.probe_duration(source)
    jobs.update(job_id,"transcribing",0.08,root)
    segments=_transcript(source,duration,folder,job_id,root)
    if not segments:
        raise ValueError("Não identifiquei fala. A fila V3 é destinada a podcasts falados.")

    picked_json=folder/"candidates.json"
    picked=jobs.load_json(picked_json)
    jobs.update(job_id,"selecting",0.70,root)
    if picked is None:
        chosen=engine.select_clips(segments,count=int(spec["count"]),
                min_seconds=min(20,max(3,duration/3)),max_seconds=min(55,duration))
        if not chosen:
            raise ValueError("Nenhum trecho apropriado foi encontrado.")
        picked=[asdict(c) for c in chosen]
        jobs.atomic_json(picked_json,picked)
    candidates=[engine.Candidate(**c) for c in picked]
    from advanced import write_dynamic_ass

    results=folder/"resultados"
    results.mkdir(exist_ok=True)
    total=len(candidates)
    for n, candidate in enumerate(candidates,1):
        jobs.update(job_id,"rendering",0.71+0.24*(n-1)/total,root)
        prefix=f"corte_{n:02d}"
        srt=results/f"{prefix}.srt"
        ass=results/f"{prefix}.ass"
        movie=results/f"{prefix}.mp4"
        cover=results/f"{prefix}_capa.jpg"
        metadata=results/f"{prefix}_seo.json"
        if not srt.is_file():
            engine.write_captions(segments,candidate,srt)
        if not ass.is_file():
            write_dynamic_ass(segments,candidate,ass,spec["style"])
        if not movie.is_file() or movie.stat().st_size<1500:
            movie_tmp=results/f"{prefix}.partial.mp4"
            engine.render_clip(source,candidate,srt,movie_tmp,spec["style"],int(spec["resolution"]))
            # Só considera concluído depois de validação do MP4 e rename atômico.
            engine.probe_duration(movie_tmp)
            os.replace(movie_tmp,movie)
        if not cover.is_file() or cover.stat().st_size<1000:
            cover_tmp=results/f"{prefix}_capa.partial.jpg"
            engine.make_cover(source,candidate,engine.package_metadata(candidate.text,n)["titulo"],cover_tmp)
            os.replace(cover_tmp,cover)
        if not metadata.is_file():
            data=engine.package_metadata(candidate.text,n)
            jobs.atomic_json(metadata,{**data,"inicio":candidate.start,"fim":candidate.end,
                 "prioridade_heuristica":candidate.score,
                 "revisao_humana_necessaria":True})
    jobs.update(job_id,"packaging",0.97,root)
    archive=folder/"cortes_prontos.zip"
    if not archive.exists() or archive.stat().st_size<1000:
        temporary=folder/"cortes_prontos.zip.partial"
        with zipfile.ZipFile(temporary,"w",compression=zipfile.ZIP_DEFLATED) as output:
            for item in sorted(results.iterdir()):
                if item.is_file() and ".partial." not in item.name:
                    output.write(item,arcname=item.name)
        os.replace(temporary,archive)
    return archive


def worker_once(root: Path=jobs.ROOT) -> bool:
    item=jobs.claim(root)
    if item is None:
        return False
    job_id,spec=item
    try:
        result=process(job_id,spec,root)
        if not result.exists():
            raise RuntimeError("Pacote ZIP não foi gerado.")
        jobs.finish(job_id,root=root)
    except Exception as exc:
        # Não imprimir URLs/cookies de terceiros no log ou interface.
        message = str(exc)
        safe_message = (message if isinstance(exc,ValueError) and len(message)<200
                        else "Falha na tarefa. Verifique os logs do worker; os checkpoints foram preservados.")
        jobs.finish(job_id,error=safe_message,root=root)
        print(f"Erro ao processar tarefa {job_id}: {type(exc).__name__}",flush=True)
    return True


def run(root: Path=jobs.ROOT, once: bool=False):
    root.mkdir(parents=True,exist_ok=True)
    lock=root/"worker.lock"
    with lock.open("w") as handle:
        try:
            fcntl.flock(handle.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:
            raise RuntimeError("Um worker já está processando a fila.")
        recovered=jobs.recover_running(root)
        if recovered:
            print(f"Retomando {recovered} tarefa(s) interrompida(s).",flush=True)
        while True:
            active=worker_once(root)
            if once:
                return
            if not active:
                time.sleep(3)


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--once",action="store_true")
    args=parser.parse_args()
    run(once=args.once)
