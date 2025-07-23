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

def analyze_audio_for_chords(audio_path):
    """오디오 파일을 분석해서 코드 진행을 추출하는 함수"""
    try:
        # 오디오 로드
        y, sr = librosa.load(audio_path, duration=60)  # 첫 60초만 분석
        
        # 템포 분석
        tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
        
        # 키 추정 (간단한 방법)
        chroma = librosa.feature.chroma_stft(y=y, sr=sr)
        key_profile = np.mean(chroma, axis=1)
        key_index = np.argmax(key_profile)
        keys = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        estimated_key = keys[key_index]
        
        # 기본 코드 진행 생성 (실제로는 더 복잡한 분석이 필요)
        if estimated_key in COMMON_CHORD_PROGRESSIONS:
            chord_progression = COMMON_CHORD_PROGRESSIONS[estimated_key]
        else:
            chord_progression = COMMON_CHORD_PROGRESSIONS['C']  # 기본값
        
        # 시간별 코드 데이터 생성
        chord_duration = 4.0  # 각 코드당 4초
        chords = []
        for i, chord in enumerate(chord_progression * 4):  # 4번 반복
            chords.append({
                'chord': chord,
                'timestamp': i * chord_duration,
                'duration': chord_duration
            })
        
        # 코드 차트 데이터 생성
        unique_chords = list(set(chord_progression))
        chord_charts = [CHORD_CHARTS.get(chord, CHORD_CHARTS['C']) for chord in unique_chords]
        
        return {
            'bpm': int(tempo),
            'signature': '4/4',
            'key': f'{estimated_key} Major',
            'chords': chords,
            'chordCharts': chord_charts
        }
    except Exception as e:
        print(f"Audio analysis error: {e}")
        # 기본값 반환
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
    """유튜브 비디오 ID를 받아서 코드 분석 결과를 반환"""
    data = request.get_json()
    video_id = data.get("videoId")
    
    if not video_id:
        return jsonify({"error": "videoId is required"}), 400
    
    try:
        # 유튜브 URL 구성
        video_url = f"https://www.youtube.com/watch?v={video_id}"
        
        # 임시 파일 경로
        unique_id = str(uuid.uuid4())
        temp_audio_path = os.path.join(OUTPUT_DIR, f"temp_{unique_id}.mp3")
        
        # 오디오 다운로드
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': temp_audio_path,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'quiet': True
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])
        
        # 오디오 분석
        analysis_result = analyze_audio_for_chords(temp_audio_path)
        
        # 임시 파일 삭제
        try:
            os.remove(temp_audio_path)
        except:
            pass
        
        return jsonify(analysis_result)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(port=5001, debug=True)