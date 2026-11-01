"""Clipador IA: pipeline local, sem APIs pagas ou bypass de conteúdo protegido."""
from __future__ import annotations

import json
import os
import math
import re
import shutil
import subprocess
import tempfile
import unicodedata
import zipfile
from collections import Counter
from dataclasses import asdict, dataclass
from functools import lru_cache
from pathlib import Path
from urllib.parse import urlsplit

ALLOWED_HOSTS = {"youtube.com", "www.youtube.com", "m.youtube.com", "youtu.be",
                 "vimeo.com", "www.vimeo.com", "instagram.com", "www.instagram.com",
                 "facebook.com", "www.facebook.com", "m.facebook.com",
                 "web.facebook.com", "fb.watch", "www.fb.watch"}
STOPWORDS = set("""a o as os um uma uns umas de do da dos das e em no na nos nas
para por com que se como mais menos onde quando porque qual quem foi ser ter
isso esse essa este esta já muito sobre então também eu você vocês ele ela
eles elas pelo pela tem não sim mas ao aos à às até só são seu sua seus suas
meu minha meus minhas pelo porque tudo todos todo toda tanto aqui ali lá
the and from that this with have your about into there what when where
which will would could should them they then just very really been were
are was for you but not""".split())
HOOKS = ("nunca", "segredo", "erro", "verdade", "incrível", "atenção",
         "ninguém", "descobri", "aprendi", "cuidado", "por isso", "surpresa",
         "importante", "como fazer", "por que", "imagine", "absurdo",
         "never", "secret", "mistake", "actually", "watch", "why", "how to",
         "unbelievable", "wait", "funny", "risada", "engraçado", "piada")


@dataclass(frozen=True)
class Word:
    start: float
    end: float
    text: str


@dataclass(frozen=True)
class Segment:
    start: float
    end: float
    text: str
    words: tuple[Word, ...] = ()


@dataclass(frozen=True)
class Candidate:
    start: float
    end: float
    text: str
    score: float


def validate_url(value: str) -> str:
    """Allow known public video hosts only: avoid arbitrary server-side URL fetching."""
    value = (value or "").strip()
    parsed = urlsplit(value)
    if parsed.scheme != "https" or not parsed.hostname or parsed.hostname.lower() not in ALLOWED_HOSTS:
        raise ValueError("Use um link HTTPS público do YouTube, Instagram, Facebook ou Vimeo; ou envie um vídeo próprio.")
    if parsed.username or parsed.password or parsed.port:
        raise ValueError("Link com credenciais ou porta personalizada não é permitido.")
    if not parsed.path or parsed.path == "/":
        raise ValueError("Informe o endereço de um vídeo específico, não a página inicial.")
    return value


def safe_run(args: list[str], *, cwd: Path | None = None) -> None:
    result = subprocess.run(args, cwd=str(cwd) if cwd else None,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            text=True, check=False)
    if result.returncode:
        raise RuntimeError("Erro ao processar vídeo: " + result.stderr[-1400:])


def probe_duration(path: Path) -> float:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        capture_output=True, text=True, check=True)
    duration = float(result.stdout.strip())
    if not math.isfinite(duration) or duration < 3 or duration > int(os.getenv('CLIPADOR_MAX_SECONDS', '7200')):
        raise ValueError('O vídeo excede o limite permitido neste ambiente. Para podcasts longos, use o Codespaces completo.')
    return duration


def explain_import_error(message: str) -> str:
    """Converte erros do extrator em instruções compreensíveis, sem expor IDs ou cookies."""
    normalized = (message or "").casefold()
    if any(token in normalized for token in
           ("not a bot", "confirm you're not", "sign in to confirm", "login required",
            "log in to", "cookies from browser", "cookies for authentication")):
        return ("A plataforma bloqueou o acesso automatizado a este vídeo. "
                "Não é possível contornar essa verificação pelo aplicativo. "
                "Envie um arquivo MP4/MOV próprio ou autorizado para continuar.")
    if any(token in normalized for token in
           ("private video", "private content", "members-only", "drm", "password protected")):
        return ("Este vídeo tem restrição de acesso. "
                "Envie um arquivo que você tem direito de editar e publicar.")
    if any(token in normalized for token in
           ("max-filesize", "maximum file size", "too large", "requested format is not available")):
        return ("Não consegui importar a versão desse vídeo dentro dos limites gratuitos. "
                "Tente enviar um arquivo MP4 menor.")
    return ("Não foi possível importar o link pela plataforma. "
            "Verifique se é público e, se tiver autorização, envie o arquivo do vídeo.")


def acquire_source(url: str, upload: str | None, work: Path) -> Path:
    if upload:
        src = Path(upload)
        if not src.is_file() or src.suffix.lower() not in (".mp4", ".mov", ".mkv", ".webm"):
            raise ValueError("Envie MP4, MOV, MKV ou WEBM válido.")
        if src.stat().st_size > int(os.getenv('CLIPADOR_MAX_BYTES', '1000000000')):
            raise ValueError('Arquivo acima do limite permitido nesta hospedagem.')
        dest = work / ("source" + src.suffix.lower())
        shutil.copy2(src, dest)
        return dest
    url = validate_url(url)
    import yt_dlp  # import sob demanda
    opts = {
        "outtmpl": str(work / "source.%(ext)s"),
        "format": "bv*[height<=1080]+ba/b[height<=1080]/b",
        "merge_output_format": "mp4", "noplaylist": True,
        "quiet": True, "no_warnings": True,
        "socket_timeout": 20, "retries": 2,
        "max_filesize": int(os.getenv("CLIPADOR_MAX_BYTES", "1000000000")),
        "match_filter": yt_dlp.utils.match_filter_func(f"duration <= {int(os.getenv('CLIPADOR_MAX_SECONDS', '7200'))}"),
    }
    try:
        with yt_dlp.YoutubeDL(opts) as client:
            client.download([url])
    except yt_dlp.utils.DownloadError as exc:
        raise ValueError(explain_import_error(str(exc))) from None
    matches = [p for p in work.glob("source.*") if p.suffix.lower() in
               (".mp4", ".webm", ".mkv", ".mov")]
    if not matches:
        raise ValueError("Não consegui importar este link. Experimente enviar um arquivo autorizado.")
    if matches[0].stat().st_size > int(os.getenv("CLIPADOR_MAX_BYTES", "1000000000")):
        raise ValueError("Vídeo acima do limite de tamanho desta hospedagem.")
    return matches[0]


@lru_cache(maxsize=1)
def speech_model():
    from faster_whisper import WhisperModel
    return WhisperModel(os.getenv("CLIPADOR_WHISPER_MODEL", "base"), device="cpu", compute_type="int8")


def transcribe(path: Path) -> list[Segment]:
    # Vídeos sem faixa de áudio: não baixar modelo de ASR desnecessariamente.
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "a:0",
         "-show_entries", "stream=index", "-of", "csv=p=0", str(path)],
        text=True, capture_output=True, check=False)
    if probe.returncode == 0 and not probe.stdout.strip():
        return []
    raw, _info = speech_model().transcribe(
        str(path), beam_size=3, vad_filter=True, language=None,
        word_timestamps=True)
    results = []
    for seg in raw:
        if not seg.text.strip() or seg.end <= seg.start:
            continue
        words = tuple(
            Word(round(w.start, 3), round(w.end, 3), w.word.strip())
            for w in (seg.words or []) if w.start is not None
            and w.end is not None and w.end > w.start and w.word.strip()
        )
        results.append(Segment(round(seg.start, 3), round(seg.end, 3),
                               seg.text.strip(), words))
    return results


def _tokens(text: str) -> list[str]:
    normalized = unicodedata.normalize("NFKD", text.lower())
    normalized = "".join(c for c in normalized if not unicodedata.combining(c))
    return re.findall(r"[a-z0-9]+", normalized)


def score_text(text: str, duration: float) -> float:
    """Heurística transparente de priorização; não é previsão real de viralização."""
    if duration <= 0:
        return 0.0
    tokens = _tokens(text)
    count = len(tokens)
    keywords = sum(1 for token in tokens if token not in STOPWORDS and len(token) > 4)
    normalized = " ".join(tokens)
    hook_count = sum(1 for hook in HOOKS if " ".join(_tokens(hook)) in normalized)
    cadence = min(count / max(duration, 1), 3.4) / 3.4
    start_text = " ".join(tokens[:22])
    start_hook = sum(1 for hook in HOOKS if " ".join(_tokens(hook)) in start_text)
    ends_clean = bool(re.search(r"[.!…]\s*$", text))
    trailing = tokens[-1] if tokens else ""
    unfinished = trailing in {"porque", "entao", "mas", "and", "because", "but"}
    return round(30 * cadence + 20 * min(hook_count, 2) / 2
                 + 20 * min(keywords / 20, 1)
                 + 12 * min(duration / 35, 1)
                 + 13 * min(start_hook, 1)
                 + (5 if ends_clean else 0)
                 - (10 if unfinished else 0), 2)


def select_clips(segments: list[Segment], count: int = 3,
                 min_seconds: float = 20, max_seconds: float = 55,
                 scene_times: tuple[float, ...] = ()) -> list[Candidate]:
    if not segments:
        return []
    count = max(1, min(int(count), 6))
    candidates: list[Candidate] = []
    for i, first in enumerate(segments):
        start = max(0.0, first.start - 0.35)
        pieces: list[str] = []
        for s in segments[i:]:
            if s.start - start > max_seconds:
                break
            if s.end - start > max_seconds + 1:
                break
            pieces.append(s.text)
            length = s.end - start
            if length >= min_seconds:
                text = " ".join(pieces).strip()
                from advanced import visual_bonus
                val = score_text(text, length) + visual_bonus(start, s.end, scene_times)
                if length > 50:
                    val -= 3
                candidates.append(Candidate(start, round(s.end + 0.2, 2), text, val))
                if length >= 38:
                    break
    if not candidates:
        text = " ".join(s.text for s in segments)
        candidates = [Candidate(max(0, segments[0].start),
                                segments[-1].end, text,
                                score_text(text, segments[-1].end - segments[0].start))]
    chosen = []
    for c in sorted(candidates, key=lambda x: (-x.score, x.start)):
        overlap = any(max(0, min(c.end, o.end) - max(c.start, o.start)) >
                      0.25 * min(c.end - c.start, o.end - o.start) for o in chosen)
        if not overlap:
            chosen.append(c)
        if len(chosen) == count:
            break
    return chosen


def package_metadata(text: str, ordinal: int) -> dict:
    """Tags e título fiéis ao conteúdo; não inventa fatos nem promete alcance."""
    cleaned = re.sub(r"\s+", " ", text).strip()
    first_sentence = re.split(r"(?<=[.!?])\s+", cleaned)[0]
    title = " ".join(first_sentence.split()[:11]).strip(" ,.;:")
    if len(title) < 16:
        title = " ".join(cleaned.split()[:13]).strip(" ,.;:")
    title = title[:86].rstrip(" ,.;:")
    common = Counter(w for w in _tokens(cleaned)
                     if w not in STOPWORDS and len(w) > 4)
    tags = []
    for word, _ in common.most_common(5):
        if word not in tags:
            tags.append(word)
    hashtags = ["#Shorts", "#Cortes"] + ["#" + t.capitalize() for t in tags[:3]]
    return {
        "titulo": title or f"Corte {ordinal}",
        "descricao": (cleaned[:320].rstrip() + ("\n\n" if cleaned else "") +
                      "Trecho editado do vídeo original. " + " ".join(hashtags)),
        "hashtags": hashtags,
        "palavras_chave": tags,
        "aviso": "Sugestões de SEO, não garantia de alcance ou monetização.",
    }


def _srt_timestamp(t: float) -> str:
    ms = max(0, round(t * 1000))
    h, remainder = divmod(ms, 3600000)
    m, remainder = divmod(remainder, 60000)
    s, milli = divmod(remainder, 1000)
    return f"{h:02}:{m:02}:{s:02},{milli:03}"


def write_captions(segments: list[Segment], clip: Candidate, output: Path) -> None:
    """SRT de 4 palavras, com tempos reais quando o Whisper fornece timestamps."""
    from advanced import words_for_clip
    words = words_for_clip(segments, clip)
    lines = []
    for idx in range(0, len(words), 4):
        group = words[idx: idx + 4]
        if not group:
            continue
        start = group[0].start
        end = max(group[-1].end, start + 0.02)
        line = " ".join(w.text for w in group).replace("<", "").replace(">", "")
        lines.append(f"{idx // 4 + 1}\n{_srt_timestamp(start)} --> {_srt_timestamp(end)}\n{line}\n")
    output.write_text("\n".join(lines), encoding="utf-8")


def render_clip(source: Path, c: Candidate, srt: Path, dest: Path,
                style: str = "Dinâmico", resolution: int = 720) -> None:
    if resolution not in (720, 1080):
        raise ValueError("Resolução inválida.")
    w, h = resolution, round(resolution * 16 / 9)
    saturation = "1.16" if style == "Humor leve" else ("1.10" if style == "Dinâmico" else "1.02")
    # Fundo desfocado + imagem integral: evita cortar rostos e gameplay sem rastreador.
    ass_path = srt.with_suffix(".ass")
    if ass_path.exists() and ass_path.stat().st_size:
        subtitle_filter = f"ass={ass_path.name},"
    elif srt.exists() and srt.stat().st_size:
        subtitle_filter = (
            f"subtitles={srt.name}:force_style='Fontname=DejaVu Sans,"
            f"Fontsize={24 if resolution == 720 else 32},Bold=1,"
            f"PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,"
            f"Outline=3,Shadow=1,Alignment=2,MarginV={115 if resolution == 720 else 172}',"
        )
    else:
        subtitle_filter = ""
    vf = (
        f"[0:v]scale={w}:{h}:force_original_aspect_ratio=increase,"
        f"crop={w}:{h},boxblur=20:6[bg];"
        f"[0:v]scale={w}:{h}:force_original_aspect_ratio=decrease,"
        f"eq=contrast=1.04:saturation={saturation}[fg];"
        f"[bg][fg]overlay=(W-w)/2:(H-h)/2:shortest=1,"
        + subtitle_filter + "fade=t=in:st=0:d=0.15[v]"
    )
    safe_run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
              "-ss", str(c.start), "-t", str(round(c.end - c.start, 2)),
              "-i", str(source), "-filter_complex", vf, "-map", "[v]",
              "-map", "0:a?", "-c:v", "libx264", "-preset", "veryfast",
              "-crf", "23", "-pix_fmt", "yuv420p",
              "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart",
              "-shortest", str(dest)], cwd=srt.parent)


def make_cover(source: Path, c: Candidate, title: str, dest: Path) -> None:
    from PIL import Image, ImageDraw, ImageFont
    still = dest.with_suffix(".frame.jpg")
    safe_run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
              "-ss", str(round((c.start + c.end) / 2, 2)), "-i", str(source),
              "-frames:v", "1", "-vf",
              "scale=720:1280:force_original_aspect_ratio=decrease,"
              "pad=720:1280:(ow-iw)/2:(oh-ih)/2:black",
              str(still)])
    canvas = Image.open(still).convert("RGBA")
    overlay = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    paint = ImageDraw.Draw(overlay)
    paint.rectangle((0, 870, 720, 1280), fill=(0, 0, 0, 205))
    paint.rounded_rectangle((35, 875, 208, 922), radius=15, fill=(235, 48, 77, 255))
    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    font = ImageFont.truetype(font_path, 37) if Path(font_path).exists() else ImageFont.load_default()
    small = ImageFont.truetype(font_path, 19) if Path(font_path).exists() else ImageFont.load_default()
    paint.text((55, 885), "CORTE IA", font=small, fill="white")
    words = title.split()
    rows, line = [], ""
    for word in words:
        test = (line + " " + word).strip()
        if paint.textbbox((0, 0), test, font=font)[2] > 645 and line:
            rows.append(line)
            line = word
        else:
            line = test
    rows.append(line)
    for i, row in enumerate(rows[:5]):
        paint.text((36, 945 + 55 * i), row, font=font, fill="white",
                   stroke_width=1, stroke_fill="black")
    Image.alpha_composite(canvas, overlay).convert("RGB").save(dest, "JPEG", quality=90)
    still.unlink(missing_ok=True)


def generate(url: str, upload: str | None, rights: bool, count: int,
             style: str, resolution: int, scene_analysis: bool = True,
             local_ai: bool = False) -> tuple[str, list[str], list[list], str]:
    """Executa pipeline v2; fallback visual só indica trechos para revisão humana."""
    from advanced import (detect_scene_times, rerank_with_ollama,
                          select_visual_only, write_dynamic_ass)
    if not rights:
        raise ValueError("Confirme que possui direitos ou autorização para usar este vídeo.")
    if not (url or upload):
        raise ValueError("Cole um link ou envie um vídeo.")
    if style not in ("Dinâmico", "Humor leve", "Sóbrio"):
        raise ValueError("Estilo inválido.")
    if os.getenv("CLIPADOR_PUBLIC_MODE") == "1":
        count = min(int(count), 2)
        scene_analysis = False
        local_ai = False
        resolution = 720
    work = Path(tempfile.mkdtemp(prefix="clipador_"))
    output = work / "resultados"
    output.mkdir()
    source = acquire_source(url, upload, work)
    duration = probe_duration(source)
    scene_times, scene_status = detect_scene_times(source, duration, scene_analysis)
    segments = transcribe(source)
    if segments:
        # Com modelo local disponível, oferecemos até 6 candidatos para comparação.
        pool_size = 6 if local_ai else int(count)
        picked = select_clips(
            segments, count=pool_size, scene_times=tuple(scene_times),
            min_seconds=min(20, max(3, duration / 3)), max_seconds=min(55, duration))
        picked, selection_status = rerank_with_ollama(picked, enabled=local_ai)
        picked = picked[:max(1, min(6, int(count)))]
    else:
        if not scene_analysis:
            raise ValueError("Não identifiquei fala. Ative a análise visual para receber cortes experimentais.")
        picked = select_visual_only(duration, scene_times, count=int(count))
        selection_status = ("Sem fala reconhecida: cortes visuais experimentais. "
                            "Não foi possível avaliar a história, humor nem SEO automaticamente.")
    if not picked:
        raise ValueError("Não foi possível encontrar trechos adequados neste vídeo.")
    covers, rows = [], []
    for n, candidate in enumerate(picked, 1):
        stem = f"corte_{n:02d}"
        srt = output / (stem + ".srt")
        ass = output / (stem + ".ass")
        video = output / (stem + ".mp4")
        cover = output / (stem + "_capa.jpg")
        meta = package_metadata(candidate.text if segments else "", n)
        write_captions(segments, candidate, srt)
        if segments:
            write_dynamic_ass(segments, candidate, ass, style)
        render_clip(source, candidate, srt, video, style, int(resolution))
        make_cover(source, candidate, meta["titulo"], cover)
        (output / (stem + "_seo.json")).write_text(
            json.dumps({**meta, "inicio": candidate.start,
                        "fim": candidate.end, "prioridade_heuristica": candidate.score,
                        "fonte": url or "Arquivo enviado pelo usuário",
                        "revisao_humana_necessaria": True},
                       ensure_ascii=False, indent=2), encoding="utf-8")
        rows.append([n, round(candidate.start, 1), round(candidate.end, 1),
                     candidate.score, meta["titulo"]])
        covers.append(str(cover))
    archive = work / "cortes_prontos.zip"
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for file in output.iterdir():
            z.write(file, arcname=file.name)
    message = (f"✅ {len(picked)} corte(s) criados a partir de {duration:.0f} segundos. "
               f"{scene_status}. {selection_status}. "
               "Os scores são sinais heurísticos, não previsões de viralização; "
               "revise narrativa, licenças e originalidade antes de publicar.")
    return str(archive), covers, rows, message
