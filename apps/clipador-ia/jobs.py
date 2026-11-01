"""Fila V3 persistente para um worker local do Codespaces.

SQLite + artefatos em .runtime/v3 (pasta do workspace).
O Render Free não executa este worker: a fila local só é ativada por variável
de ambiente. Não é uma fila distribuída ou armazenamento fora do Codespaces.
"""
from __future__ import annotations

import json
import os
import shutil
import sqlite3
import time
import uuid
from pathlib import Path

from engine import validate_url

ROOT = Path(os.getenv("CLIPADOR_JOB_ROOT", str(Path(__file__).resolve().parent / ".runtime" / "v3")))
STAGES = ("queued", "importing", "transcribing", "selecting", "rendering", "packaging", "done")


def _connect(root: Path):
    root.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(root / "queue.sqlite3", timeout=30)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("PRAGMA busy_timeout=30000")
    db.execute("""CREATE TABLE IF NOT EXISTS jobs (
        id TEXT PRIMARY KEY, spec TEXT NOT NULL, status TEXT NOT NULL,
        stage TEXT NOT NULL, progress REAL NOT NULL DEFAULT 0,
        attempts INTEGER NOT NULL DEFAULT 0, error TEXT NOT NULL DEFAULT '',
        created_at REAL NOT NULL, updated_at REAL NOT NULL
    )""")
    db.commit()
    return db


def folder(job_id: str, root: Path = ROOT) -> Path:
    if not isinstance(job_id, str) or len(job_id) != 32 or any(c not in "0123456789abcdef" for c in job_id):
        raise ValueError("Identificador de tarefa inválido.")
    return root / "jobs" / job_id


def submit(url: str, upload: str | None, rights: bool, count: int,
           style: str, resolution: int, root: Path = ROOT) -> str:
    if not rights:
        raise ValueError("Confirme autorização de uso da mídia.")
    if style not in ("Dinâmico", "Humor leve", "Sóbrio") or resolution not in (720, 1080):
        raise ValueError("Configuração inválida.")
    if not 1 <= int(count) <= 6:
        raise ValueError("Selecione entre 1 e 6 cortes.")
    if not upload and not url:
        raise ValueError("Informe um link ou arquivo.")
    if url and not upload:
        url = validate_url(url)
    job_id = uuid.uuid4().hex
    dest = folder(job_id, root)
    dest.mkdir(parents=True)
    input_name = None
    try:
        if upload:
            src = Path(upload).resolve()
            if not src.is_file() or src.suffix.lower() not in (".mp4", ".mov", ".mkv", ".webm"):
                raise ValueError("Envie MP4/MOV/MKV/WEBM válido.")
            if src.stat().st_size > int(os.getenv("CLIPADOR_MAX_BYTES", "1000000000")):
                raise ValueError("Arquivo acima do limite permitido.")
            input_name = "input" + src.suffix.lower()
            shutil.copyfile(src, dest / input_name)
        spec = {"url":url if not upload else "", "input_name":input_name,
                "rights":True, "count":int(count), "style":style,
                "resolution":int(resolution)}
        with _connect(root) as db:
            now = time.time()
            db.execute("INSERT INTO jobs(id,spec,status,stage,created_at,updated_at) VALUES(?,?,?,?,?,?)",
                       (job_id,json.dumps(spec,ensure_ascii=False),"queued","queued",now,now))
        return job_id
    except Exception:
        shutil.rmtree(dest, ignore_errors=True)
        raise


def get(job_id: str, root: Path = ROOT) -> dict:
    folder(job_id,root)
    with _connect(root) as db:
        row = db.execute("SELECT id, status, stage, progress, attempts, error, created_at, updated_at FROM jobs WHERE id=?",
                         (job_id,)).fetchone()
        if row is None:
            raise ValueError("Tarefa não encontrada.")
        return dict(row)


def claim(root: Path = ROOT) -> tuple[str,dict] | None:
    """Apenas um worker deve chamar claim: o lock do worker garante exclusividade."""
    with _connect(root) as db:
        db.execute("BEGIN IMMEDIATE")
        row = db.execute("SELECT id, spec FROM jobs WHERE status='queued' ORDER BY created_at LIMIT 1").fetchone()
        if not row:
            return None
        db.execute("UPDATE jobs SET status='running', attempts=attempts+1, updated_at=? WHERE id=?",
                   (time.time(),row["id"]))
        return row["id"],json.loads(row["spec"])


def update(job_id: str, stage: str, fraction: float, root: Path = ROOT):
    if stage not in STAGES:
        raise ValueError("Etapa inválida.")
    with _connect(root) as db:
        db.execute("UPDATE jobs SET stage=?, progress=?, updated_at=? WHERE id=? AND status='running'",
                   (stage,max(0,min(float(fraction),1)),time.time(),job_id))


def finish(job_id: str, error: str = "", root: Path = ROOT):
    error = error[:250]
    with _connect(root) as db:
        db.execute("UPDATE jobs SET status=?, stage=?, progress=?, error=?, updated_at=? WHERE id=?",
                   ("failed" if error else "done", "failed" if error else "done",
                    0 if error else 1, error,time.time(),job_id))


def retry(job_id: str, root: Path = ROOT):
    folder(job_id,root)
    with _connect(root) as db:
        result = db.execute(
            "UPDATE jobs SET status='queued', error='', updated_at=? WHERE id=? AND status='failed'",
            (time.time(),job_id))
        if result.rowcount != 1:
            raise ValueError("A tarefa não está em estado de erro.")


def recover_running(root: Path = ROOT) -> int:
    """Chamar exclusivamente sob flock, quando nenhum outro worker está ativo."""
    with _connect(root) as db:
        r = db.execute("UPDATE jobs SET status='queued', updated_at=? WHERE status='running'",(time.time(),))
        return r.rowcount


def atomic_json(path: Path, payload):
    tmp = path.with_suffix(path.suffix + ".partial")
    with tmp.open("w", encoding="utf-8") as out:
        json.dump(payload,out,ensure_ascii=False)
        out.flush()
        os.fsync(out.fileno())
    os.replace(tmp,path)


def load_json(path: Path):
    if path.exists():
        with path.open(encoding="utf-8") as stream:
            return json.load(stream)
    return None
