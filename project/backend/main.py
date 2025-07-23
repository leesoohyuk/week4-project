# main.py ver.2
from flask import Flask, request, jsonify
from flask_cors import CORS
import yt_dlp
import os
import uuid
import librosa
import numpy as np
from scipy.signal import find_peaks
import json
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
CORS(app)

OUTPUT_DIR = "downloads"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 기본 코드 진행 패턴 (예시)
COMMON_CHORD_PROGRESSIONS = {
    'C': ['C', 'Am', 'F', 'G'],
    'G': ['G', 'Em', 'C', 'D'],
    'D': ['D', 'Bm', 'G', 'A'],
    'A': ['A', 'F#m', 'D', 'E'],
    'E': ['E', 'C#m', 'A', 'B'],
    'F': ['F', 'Dm', 'Bb', 'C']
}

# 기타 코드 차트 데이터
CHORD_CHARTS = {
    'C': {'chord': 'C', 'frets': [0, 3, 2, 0, 1, 0], 'fingers': [0, 3, 2, 0, 1, 0]},
    'Am': {'chord': 'Am', 'frets': [0, 0, 2, 2, 1, 0], 'fingers': [0, 0, 2, 3, 1, 0]},
    'F': {'chord': 'F', 'frets': [1, 3, 3, 2, 1, 1], 'fingers': [1, 3, 4, 2, 1, 1]},
    'G': {'chord': 'G', 'frets': [3, 2, 0, 0, 3, 3], 'fingers': [3, 1, 0, 0, 4, 4]},
    'Em': {'chord': 'Em', 'frets': [0, 2, 2, 0, 0, 0], 'fingers': [0, 1, 2, 0, 0, 0]},
    'D': {'chord': 'D', 'frets': [-1, 0, 0, 2, 3, 2], 'fingers': [0, 0, 0, 1, 3, 2]},
    'Bm': {'chord': 'Bm', 'frets': [2, 2, 4, 4, 3, 2], 'fingers': [1, 1, 3, 4, 2, 1]},
    'A': {'chord': 'A', 'frets': [0, 0, 2, 2, 2, 0], 'fingers': [0, 0, 1, 2, 3, 0]},
    'E': {'chord': 'E', 'frets': [0, 2, 2, 1, 0, 0], 'fingers': [0, 2, 3, 1, 0, 0]},
    'C#m': {'chord': 'C#m', 'frets': [4, 4, 6, 6, 5, 4], 'fingers': [1, 1, 3, 4, 2, 1]},
    'B': {'chord': 'B', 'frets': [2, 2, 4, 4, 4, 2], 'fingers': [1, 1, 2, 3, 4, 1]},
    'Dm': {'chord': 'Dm', 'frets': [-1, 0, 0, 2, 3, 1], 'fingers': [0, 0, 0, 2, 3, 1]},
    'Bb': {'chord': 'Bb', 'frets': [1, 1, 3, 3, 3, 1], 'fingers': [1, 1, 2, 3, 4, 1]},
    'F#m': {'chord': 'F#m', 'frets': [2, 4, 4, 2, 2, 2], 'fingers': [1, 3, 4, 1, 1, 1]}
}

KEYS = ['C','C#','D','D#','E','F','F#','G','G#','A','A#','B']

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

def build_chord_timeline(chords, duration_per=4.0, repeats=4):
    timeline = []
    t = 0.0
    for _ in range(repeats):
        for ch in chords:
            timeline.append({
                "chord": ch,
                "timestamp": t,
                "duration": duration_per
            })
            t += duration_per
    return timeline

def analyze_audio_for_chords(audio_path):
    """오디오 파일을 분석해서 코드 진행을 추출"""
    # 실패 시 기본값 리턴 대신 예외를 던지고, 라우터에서 잡아도 됨.
    # 여기서는 그대로 리턴하되 원인 로그는 확실히 남김.
    try:
        y, sr = safe_load_audio(audio_path, duration=60)
        tempo = safe_tempo(y, sr)
        est_key = safe_key(y, sr)

        # 진행 패턴 얻기
        prog = COMMON_CHORD_PROGRESSIONS.get(est_key, COMMON_CHORD_PROGRESSIONS['C'])

        chords = build_chord_timeline(prog, duration_per=4.0, repeats=4)

        # 코드 다이어그램
        unique = list(dict.fromkeys(prog))  # 순서유지 중복제거
        chord_charts = [CHORD_CHARTS.get(c, CHORD_CHARTS['C']) for c in unique]

        return {
            "bpm": int(round(tempo)),
            "signature": "4/4",
            "key": f"{est_key} Major",
            "chords": chords,
            "chordCharts": chord_charts
        }
    except Exception as e:
        logging.exception(f"Audio analysis failed: {e}")
        raise
        # 최소한의 기본값 (원하면 raise 해서 500 반환)
        return {
            'bpm': 120,
            'signature': '4/4',
            'key': 'C Major',
            'chords': [
                {'chord': 'C', 'timestamp': 0, 'duration': 4},
                {'chord': 'Am', 'timestamp': 4, 'duration': 4},
                {'chord': 'F', 'timestamp': 8, 'duration': 4},
                {'chord': 'G', 'timestamp': 12, 'duration': 4}
            ],
            'chordCharts': [CHORD_CHARTS['C'], CHORD_CHARTS['Am'], CHORD_CHARTS['F'], CHORD_CHARTS['G']]
        }


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
    app.run(port=5001, debug=True)