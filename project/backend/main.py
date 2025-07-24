# main.py ver.4
from flask import Flask, request, jsonify
from flask_cors import CORS
import yt_dlp
import os
import uuid
import librosa
import numpy as np
import math
import json
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
CORS(app)

OUTPUT_DIR = "downloads"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 기타 코드 차트 데이터
CHORD_CHARTS = {
    'A':   {'chord': 'A',   'frets': [0, 0, 2, 2, 2, 0], 'fingers': [0, 0, 1, 2, 3, 0]},
    'A#':  {'chord': 'A#',  'frets': [1, 1, 3, 3, 3, 1], 'fingers': [1, 1, 2, 3, 4, 1]},
    'A#m': {'chord': 'A#m', 'frets': [1, 1, 3, 3, 2, 1], 'fingers': [1, 1, 3, 4, 2, 1]},
    'Am':  {'chord': 'Am',  'frets': [0, 0, 2, 2, 1, 0], 'fingers': [0, 0, 2, 3, 1, 0]},
    'B':   {'chord': 'B',   'frets': [2, 2, 4, 4, 4, 2], 'fingers': [1, 1, 2, 3, 4, 1]},
    'Bb':  {'chord': 'Bb',  'frets': [1, 1, 3, 3, 3, 1], 'fingers': [1, 1, 2, 3, 4, 1]},
    'Bm':  {'chord': 'Bm',  'frets': [2, 2, 4, 4, 3, 2], 'fingers': [1, 1, 3, 4, 2, 1]},
    'C':   {'chord': 'C',   'frets': [0, 3, 2, 0, 1, 0], 'fingers': [0, 3, 2, 0, 1, 0]},
    'C#':  {'chord': 'C#',  'frets': [-1, 4, 6, 6, 6, 4], 'fingers': [0, 1, 3, 4, 2, 1]},
    'C#m': {'chord': 'C#m', 'frets': [4, 4, 6, 6, 5, 4], 'fingers': [1, 1, 3, 4, 2, 1]},
    'Cm':  {'chord': 'Cm',  'frets': [-1, 3, 5, 5, 4, 3], 'fingers': [0, 1, 3, 4, 2, 1]},
    'D':   {'chord': 'D',   'frets': [-1, 0, 0, 2, 3, 2], 'fingers': [0, 0, 0, 1, 3, 2]},
    'D#':  {'chord': 'D#',  'frets': [-1, 6, 8, 8, 8, 6], 'fingers': [0, 1, 3, 4, 2, 1]},
    'D#m': {'chord': 'D#m', 'frets': [-1, 6, 8, 8, 7, 6], 'fingers': [0, 1, 3, 4, 2, 1]},
    'Dm':  {'chord': 'Dm',  'frets': [-1, 0, 0, 2, 3, 1], 'fingers': [0, 0, 0, 2, 3, 1]},
    'E':   {'chord': 'E',   'frets': [0, 2, 2, 1, 0, 0], 'fingers': [0, 2, 3, 1, 0, 0]},
    'Em':  {'chord': 'Em',  'frets': [0, 2, 2, 0, 0, 0], 'fingers': [0, 1, 2, 0, 0, 0]},
    'F':   {'chord': 'F',   'frets': [1, 3, 3, 2, 1, 1], 'fingers': [1, 3, 4, 2, 1, 1]},
    'F#':  {'chord': 'F#',  'frets': [2, 4, 4, 3, 2, 2], 'fingers': [1, 3, 4, 2, 1, 1]},
    'Fm':  {'chord': 'Fm',  'frets': [1, 3, 3, 1, 1, 1], 'fingers': [1, 3, 4, 1, 1, 1]},
    'F#m': {'chord': 'F#m', 'frets': [2, 4, 4, 2, 2, 2], 'fingers': [1, 3, 4, 1, 1, 1]},
    'G':   {'chord': 'G',   'frets': [3, 2, 0, 0, 3, 3], 'fingers': [3, 1, 0, 0, 4, 4]},
    'G#':  {'chord': 'G#',  'frets': [4, 6, 6, 5, 4, 4], 'fingers': [1, 3, 4, 2, 1, 1]},
    'G#m': {'chord': 'G#m', 'frets': [4, 6, 6, 4, 4, 4], 'fingers': [1, 3, 4, 1, 1, 1]},
    'Gm':  {'chord': 'Gm',  'frets': [3, 3, 5, 5, 3, 3], 'fingers': [1, 1, 3, 4, 1, 1]},
}

KEYS = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

# ---- 추가: 코드 템플릿/디코딩 유틸 ----
MAJOR = np.array([0, 4, 7])
MINOR = np.array([0, 3, 7])


def build_chord_templates():
    """24개(12메이저+12마이너) 코드 템플릿 반환"""
    names = []
    mats = []
    for i, root in enumerate(KEYS):
        vecM = np.zeros(12)
        vecM[(i + MAJOR) % 12] = 1
        vecm = np.zeros(12)
        vecm[(i + MINOR) % 12] = 1
        mats.append(vecM / vecM.sum())
        names.append(root)
        mats.append(vecm / vecm.sum())
        names.append(root + "m")
    return names, np.array(mats, dtype=float)


def viterbi_decode(score_matrix, switch_penalty=0.2):
    """
    score_matrix: (T, N)  값이 클수록 그 코드일 확률이 높다고 봄
    switch_penalty: 코드가 바뀔 때 패널티
    """
    T, N = score_matrix.shape
    dp = np.zeros((T, N), dtype=float)
    back = np.zeros((T, N), dtype=int)

    dp[0] = score_matrix[0]
    for t in range(1, T):
        # 이전 상태 값에 패널티 적용
        trans = dp[t-1][:, None] - switch_penalty
        stay_or_switch = np.maximum(
            trans.max(axis=0), dp[t-1])  # stay vs switch
        best_prev = np.argmax(trans, axis=0)
        dp[t] = score_matrix[t] + stay_or_switch
        back[t] = np.where(dp[t-1] >= trans.max(axis=0),
                           np.arange(N), best_prev)

    path = np.zeros(T, dtype=int)
    path[-1] = np.argmax(dp[-1])
    for t in range(T-2, -1, -1):
        path[t] = back[t+1, path[t+1]]
    return path


def merge_segments(idx_path, chord_names, times, min_dur=0.5):
    """프레임별 인덱스를 타임라인으로 병합"""
    segs = []
    start = 0
    cur = idx_path[0]
    limit = min(len(idx_path), len(times))  # 인덱스 초과 방지

    for i in range(1, limit):
        if idx_path[i] != cur:
            if i >= len(times) or start >= len(times):
                continue  # 안전하게 스킵
            dur = float(times[i] - times[start])
            if dur >= min_dur:
                segs.append({
                    "chord": chord_names[cur],
                    "timestamp": float(times[start]),
                    "duration": dur
                })
            start = i
            cur = idx_path[i]

    # 마지막 세그먼트 처리
    if start < len(times) and (limit - 1) < len(times):
        dur = float(times[limit - 1] - times[start])
        if dur >= min_dur:
            segs.append({
                "chord": chord_names[cur],
                "timestamp": float(times[start]),
                "duration": dur
            })
    return segs


def estimate_key_from_chords(chords):
    """추출된 코드들의 루트 다수결로 키 추정(간단버전)"""
    roots = [c.replace("m", "") for c in chords]
    if not roots:
        return "C"
    return max(set(roots), key=roots.count)
# ---- /추가 ----


def download_audio_from_youtube(video_url: str, out_dir: str) -> str:
    tmp_id = uuid.uuid4().hex
    out_tmpl = os.path.join(out_dir, f"{tmp_id}.%(ext)s")

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": out_tmpl,
        "noplaylist": True,
        "quiet": True,
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
        "extractor_args": {"youtube": {"player_client": ["android"]}},
        "http_headers": {"User-Agent": "Mozilla/5.0"},
        # ↓ 디버깅용 옵션(필요시 켜기)
        # "verbose": True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(video_url, download=True)
        pre_path = ydl.prepare_filename(info)
        final_path = str(Path(pre_path).with_suffix(".mp3"))

    # 혹시 mp3가 다른 이름으로 생겼는지 확인
    if not os.path.exists(final_path):
        candidates = list(Path(out_dir).glob(f"{tmp_id}*.mp3"))
        if candidates:
            final_path = str(candidates[0])

    size = os.path.getsize(final_path) if os.path.exists(final_path) else 0
    logging.info(f"[yt-dlp] saved: {final_path} ({size/1024:.1f} KB)")

    if size < 50_000:  # 50KB 미만이면 실패로 판단
        raise ValueError("Downloaded audio seems invalid/too small.")

    return final_path


def safe_load_audio(path, duration=60):
    if not os.path.exists(path) or os.path.getsize(path) < 2048:
        raise ValueError("Audio file missing or too small.")
    y, sr = librosa.load(path, mono=True, duration=duration)
    if y.size == 0:
        raise ValueError("Empty audio array.")
    return y, sr


def safe_tempo(y, sr):
    try:
        tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
        return 120 if (tempo is None or np.isnan(tempo) or tempo == 0) else float(tempo)
    except Exception:
        return 120


def safe_key(y, sr):
    try:
        chroma = librosa.feature.chroma_stft(y=y, sr=sr)
        prof = np.mean(chroma, axis=1)
        idx = int(np.argmax(prof))
        return KEYS[idx]
    except Exception:
        return 'C'


def analyze_audio_for_chords(audio_path):
    """오디오에서 코드/타임라인 추출 (librosa만 사용)"""
    try:
        y, sr = safe_load_audio(audio_path, duration=60)

        # 1) 하모닉/퍼커시브 분리 → 하모닉만 사용
        y_h, _ = librosa.effects.hpss(y)

        # 2) 비트 트래킹
        tempo_raw, beat_frames = librosa.beat.beat_track(y=y_h, sr=sr)

        # tempo를 확실히 float로 변환
        tempo_val = float(np.asarray(tempo_raw).reshape(-1)[0])
        if math.isnan(tempo_val) or tempo_val <= 0:
            tempo_val = 120

        # ★추가★ 비트 프레임 -> 시간(초)
        beat_times = librosa.frames_to_time(beat_frames, sr=sr)

        # 3) 크로마 (CQT 추천) + 비트 싱크
        chroma = librosa.feature.chroma_cqt(y=y_h, sr=sr, bins_per_octave=36)
        chroma_sync = librosa.util.sync(
            chroma, beat_frames, aggregate=np.median).T  # (T, 12)

        # 4) 템플릿 매칭
        chord_names, templates = build_chord_templates()
        # cosine 유사도
        norm_chroma = chroma_sync / \
            (np.linalg.norm(chroma_sync, axis=1, keepdims=True) + 1e-9)
        norm_temp = templates / \
            (np.linalg.norm(templates, axis=1, keepdims=True) + 1e-9)
        sims = norm_chroma @ norm_temp.T  # (T, 24)

        # 5) Viterbi로 연속성 보정
        path = viterbi_decode(sims, switch_penalty=0.15)

        # 6) 타임라인 병합
        chord_segments = merge_segments(
            path, chord_names, beat_times, min_dur=0.5)

        # 7) 키 추정
        est_key = estimate_key_from_chords(
            [seg["chord"] for seg in chord_segments])

        # 8) 코드 다이어그램
        unique = list(dict.fromkeys([seg["chord"] for seg in chord_segments]))
        chord_charts = [CHORD_CHARTS.get(
            c, CHORD_CHARTS["C"]) for c in unique if c in CHORD_CHARTS]

        return {
            "bpm": int(round(tempo_val)),
            "signature": "4/4",
            "key": f"{est_key} Major",
            "chords": chord_segments,
            "chordCharts": chord_charts
        }
    except Exception as e:
        logging.exception(f"Audio analysis failed: {e}")
        raise


@app.route("/download", methods=["POST"])
def download_audio():
    data = request.get_json()
    video_url = data.get("url")

    if not video_url:
        return jsonify({"error": "URL is required"}), 400

    unique_id = str(uuid.uuid4())
    output_path = os.path.join(OUTPUT_DIR, f"{unique_id}.mp3")

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': output_path,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': True
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])
        return jsonify({"file": output_path})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/analyze", methods=["POST"])
def analyze_song():
    data = request.get_json(silent=True) or {}
    video_id = data.get("videoId")
    video_url = data.get("url")

    if not video_url and video_id:
        video_url = f"https://www.youtube.com/watch?v={video_id}"
    if not video_url:
        return jsonify({"error": "videoId or url is required"}), 400

    try:
        audio_path = download_audio_from_youtube(video_url, OUTPUT_DIR)
        result = analyze_audio_for_chords(audio_path)
        return jsonify(result)
    except Exception as e:
        app.logger.exception("Analyze failed")
        return jsonify({"error": str(e)}), 500
    finally:
        # 정리
        try:
            if 'audio_path' in locals() and os.path.exists(audio_path):
                os.remove(audio_path)
        except:
            pass


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
