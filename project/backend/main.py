import os
import uuid
import shutil
import glob

import numpy as np
import librosa
import yt_dlp

from flask import Flask, request, jsonify
from flask_cors import CORS

# ─── 설정 ─────────────────────────────────────────────────────
OUTPUT_DIR = "downloads"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# FFmpeg 설치 여부 체크
HAS_FFMPEG = bool(shutil.which("ffmpeg"))
if HAS_FFMPEG:
    print("✅ FFmpeg detected on PATH.")
else:
    print(
        "⚠️ WARNING: FFmpeg not found on PATH.\n"
        "  • MP3 변환(postprocessor)이 건너뛰어질 수 있습니다.\n"
        "  • 다운로드된 원본(ext)을 librosa로 바로 읽습니다."
    )

# Flask 앱 (downloads/ → /downloads URL 매핑)
app = Flask(
    __name__,
    static_folder=OUTPUT_DIR,
    static_url_path="/downloads"
)
CORS(app)


# ─── 유틸: YouTube URL → 로컬 오디오 파일 다운로드 ────────────────
def download_audio_file(video_url: str, to_mp3: bool = True):
    """
    • to_mp3 and HAS_FFMPEG → .mp3 로 변환
    • 그 외              → 원본(ext) 유지
    반환: (전체 파일 경로, 파일명)
    """
    uid = str(uuid.uuid4())

    if to_mp3 and HAS_FFMPEG:
        # 확장자 없이 uid만 템플릿으로 주면 yt_dlp가 후처리기로 .mp3를 붙입니다.
        outtmpl = os.path.join(OUTPUT_DIR, uid)
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': outtmpl,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'quiet': True
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])
    else:
        # 원본 확장자 유지
        outtmpl = os.path.join(OUTPUT_DIR, f"{uid}.%(ext)s")
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': outtmpl,
            'quiet': True
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.extract_info(video_url, download=True)

    # glob으로 실제 생성된 파일(uid.mp3 또는 uid.<ext>)을 찾아 반환
    pattern = os.path.join(OUTPUT_DIR, f"{uid}.*")
    matches = glob.glob(pattern)
    if not matches:
        raise FileNotFoundError(f"No file found matching pattern {pattern}")
    audio_path = matches[0]
    filename = os.path.basename(audio_path)
    return audio_path, filename


# ─── 코드 진행 & 차트 데이터 ────────────────────────────────────
COMMON_CHORD_PROGRESSIONS = {
    'C': ['C', 'Am', 'F', 'G'],
    'G': ['G', 'Em', 'C', 'D'],
    'D': ['D', 'Bm', 'G', 'A'],
    'A': ['A', 'F#m', 'D', 'E'],
    'E': ['E', 'C#m', 'A', 'B'],
    'F': ['F', 'Dm', 'Bb', 'C']
}

CHORD_CHARTS = {
    'C':    {'chord':'C',   'frets':[0,3,2,0,1,0], 'fingers':[0,3,2,0,1,0]},
    'Am':   {'chord':'Am',  'frets':[0,0,2,2,1,0], 'fingers':[0,0,2,3,1,0]},
    'F':    {'chord':'F',   'frets':[1,3,3,2,1,1], 'fingers':[1,3,4,2,1,1]},
    'G':    {'chord':'G',   'frets':[3,2,0,0,3,3], 'fingers':[3,1,0,0,4,4]},
    'Em':   {'chord':'Em',  'frets':[0,2,2,0,0,0], 'fingers':[0,1,2,0,0,0]},
    'D':    {'chord':'D',   'frets':[-1,0,0,2,3,2], 'fingers':[0,0,0,1,3,2]},
    'Bm':   {'chord':'Bm',  'frets':[2,2,4,4,3,2], 'fingers':[1,1,3,4,2,1]},
    'A':    {'chord':'A',   'frets':[0,0,2,2,2,0], 'fingers':[0,0,1,2,3,0]},
    'E':    {'chord':'E',   'frets':[0,2,2,1,0,0], 'fingers':[0,2,3,1,0,0]},
    'C#m':  {'chord':'C#m', 'frets':[4,4,6,6,5,4], 'fingers':[1,1,3,4,2,1]},
    'B':    {'chord':'B',   'frets':[2,2,4,4,4,2], 'fingers':[1,1,2,3,4,1]},
    'Dm':   {'chord':'Dm',  'frets':[-1,0,0,2,3,1], 'fingers':[0,0,0,2,3,1]},
    'Bb':   {'chord':'Bb',  'frets':[1,1,3,3,3,1], 'fingers':[1,1,2,3,4,1]},
    'F#m':  {'chord':'F#m', 'frets':[2,4,4,2,2,2], 'fingers':[1,3,4,1,1,1]},
}


# ─── 오디오 분석 ────────────────────────────────────────────────
def analyze_audio_for_chords(audio_path: str) -> dict:
    try:
        app.logger.info(f"Analyzing audio: {audio_path}")
        y, sr = librosa.load(audio_path, duration=60)
        tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
        tempo = float(tempo)  # numpy scalar → Python float

        chroma = librosa.feature.chroma_stft(y=y, sr=sr)
        key_profile = np.mean(chroma, axis=1)
        key_index = int(np.argmax(key_profile))
        keys = ['C','C#','D','D#','E','F','F#','G','G#','A','A#','B']
        est_key = keys[key_index]

        prog = COMMON_CHORD_PROGRESSIONS.get(est_key, COMMON_CHORD_PROGRESSIONS['C'])
        chord_duration = 4.0
        chords = [
            {'chord': c, 'timestamp': i*chord_duration, 'duration': chord_duration}
            for i, c in enumerate(prog * 4)
        ]

        unique = list(dict.fromkeys(prog))
        charts = [CHORD_CHARTS.get(c, CHORD_CHARTS['C']) for c in unique]

        return {
            'bpm': int(tempo),
            'signature': '4/4',
            'key': f'{est_key} Major',
            'chords': chords,
            'chordCharts': charts
        }
    except Exception as e:
        app.logger.error(f"Analysis error: {e}", exc_info=True)
        return {
            'bpm': 120,
            'signature': '4/4',
            'key': 'C Major',
            'chords': [
                {'chord':'C','timestamp':0,'duration':4},
                {'chord':'Am','timestamp':4,'duration':4},
                {'chord':'F','timestamp':8,'duration':4},
                {'chord':'G','timestamp':12,'duration':4},
            ],
            'chordCharts': [
                CHORD_CHARTS['C'],
                CHORD_CHARTS['Am'],
                CHORD_CHARTS['F'],
                CHORD_CHARTS['G']
            ]
        }


# ─── /download 엔드포인트 ────────────────────────────────────────
@app.route("/download", methods=["POST"])
def download_endpoint():
    data = request.get_json()
    url = data.get("url")
    if not url:
        return jsonify({"error": "URL is required"}), 400

    try:
        path, filename = download_audio_file(url, to_mp3=True)
        return jsonify({"file": f"downloads/{filename}"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ─── /analyze 엔드포인트 ────────────────────────────────────────
@app.route("/analyze", methods=["POST"])
def analyze_endpoint():
    data = request.get_json()
    vid = data.get("videoId")
    if not vid:
        return jsonify({"error": "videoId is required"}), 400

    video_url = f"https://www.youtube.com/watch?v={vid}"
    try:
        temp_path, _ = download_audio_file(video_url, to_mp3=True)
        result = analyze_audio_for_chords(temp_path)
        os.remove(temp_path)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ─── 앱 실행 ──────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(port=5001, debug=True)
