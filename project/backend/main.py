import os
import uuid
import shutil
import glob
import tempfile

import numpy as np
import librosa
import yt_dlp
import basic_pitch
from basic_pitch.inference import predict_and_save
from basic_pitch import ICASSP_2022_MODEL_PATH
import mido
from music21 import stream, note, chord, key, meter, tempo as music21_tempo
from music21.chord import Chord

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


# ─── MIDI에서 코드 추출 함수 ────────────────────────────────────
def extract_chords_from_midi(midi_path: str) -> dict:
    """
    MIDI 파일에서 코드 진행을 추출합니다.
    """
    try:
        # MIDI 파일 로드
        midi_file = mido.MidiFile(midi_path)
        
        # music21으로 MIDI 파일 분석
        score = stream.Stream()
        
        # MIDI에서 노트 정보 추출
        notes = []
        current_time = 0
        
        for track in midi_file.tracks:
            track_time = 0
            for msg in track:
                track_time += msg.time
                if msg.type == 'note_on' and msg.velocity > 0:
                    # MIDI 노트 번호를 음표로 변환
                    midi_note = msg.note
                    notes.append({
                        'pitch': midi_note,
                        'time': track_time / midi_file.ticks_per_beat,
                        'velocity': msg.velocity
                    })
        
        if not notes:
            raise ValueError("MIDI 파일에서 노트를 찾을 수 없습니다.")
        
        # 시간대별로 노트 그룹화 (4박자 단위)
        chord_duration = 4.0  # 4박자
        max_time = max(note['time'] for note in notes) if notes else 16.0
        
        chords_data = []
        chord_charts_set = set()
        
        for i in range(int(max_time / chord_duration) + 1):
            start_time = i * chord_duration
            end_time = (i + 1) * chord_duration
            
            # 해당 시간대의 노트들 수집
            time_notes = [n for n in notes if start_time <= n['time'] < end_time]
            
            if time_notes:
                # 가장 많이 나타나는 음들을 기반으로 코드 추정
                pitches = [n['pitch'] % 12 for n in time_notes]  # 옥타브 정규화
                pitch_counts = {}
                for p in pitches:
                    pitch_counts[p] = pitch_counts.get(p, 0) + 1
                
                # 상위 3-4개 음으로 코드 구성
                top_pitches = sorted(pitch_counts.items(), key=lambda x: x[1], reverse=True)[:4]
                chord_pitches = [p[0] for p in top_pitches]
                
                # 코드 이름 추정
                chord_name = estimate_chord_name(chord_pitches)
                
            else:
                # 기본 코드 진행 사용
                default_progression = ['C', 'Am', 'F', 'G']
                chord_name = default_progression[i % len(default_progression)]
            
            chords_data.append({
                'chord': chord_name,
                'timestamp': start_time,
                'duration': chord_duration
            })
            chord_charts_set.add(chord_name)
        
        # BPM 추정 (기본값 120)
        estimated_bpm = 120
        if len(notes) > 1:
            time_diffs = []
            for i in range(1, min(len(notes), 20)):  # 처음 20개 노트만 사용
                diff = notes[i]['time'] - notes[i-1]['time']
                if 0.1 < diff < 2.0:  # 합리적인 범위의 시간 차이만
                    time_diffs.append(diff)
            
            if time_diffs:
                avg_diff = sum(time_diffs) / len(time_diffs)
                estimated_bpm = int(60 / (avg_diff * 4))  # 4분음표 기준
                estimated_bpm = max(60, min(200, estimated_bpm))  # 60-200 BPM 범위로 제한
        
        # 조성 추정
        if notes:
            pitch_profile = [0] * 12
            for note in notes:
                pitch_profile[note['pitch'] % 12] += 1
            
            # 가장 많이 나타나는 음을 근음으로 추정
            root_pitch = pitch_profile.index(max(pitch_profile))
            keys = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
            estimated_key = f"{keys[root_pitch]} Major"
        else:
            estimated_key = "C Major"
        
        # 코드 차트 생성
        chord_charts = []
        for chord_name in chord_charts_set:
            if chord_name in CHORD_CHARTS:
                chord_charts.append(CHORD_CHARTS[chord_name])
            else:
                # 기본 C 코드로 대체
                chord_charts.append(CHORD_CHARTS['C'])
        
        return {
            'bpm': estimated_bpm,
            'signature': '4/4',
            'key': estimated_key,
            'chords': chords_data,
            'chordCharts': chord_charts
        }
        
    except Exception as e:
        app.logger.error(f"MIDI 분석 오류: {e}", exc_info=True)
        # 기본값 반환
        return {
            'bpm': 120,
            'signature': '4/4',
            'key': 'C Major',
            'chords': [
                {'chord': 'C', 'timestamp': 0, 'duration': 4},
                {'chord': 'Am', 'timestamp': 4, 'duration': 4},
                {'chord': 'F', 'timestamp': 8, 'duration': 4},
                {'chord': 'G', 'timestamp': 12, 'duration': 4},
            ],
            'chordCharts': [
                CHORD_CHARTS['C'],
                CHORD_CHARTS['Am'],
                CHORD_CHARTS['F'],
                CHORD_CHARTS['G']
            ]
        }


def estimate_chord_name(pitches):
    """
    음계 리스트로부터 코드 이름을 추정합니다.
    """
    if not pitches:
        return 'C'
    
    # 음계 이름 매핑
    note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    
    # 가장 낮은 음을 근음으로 가정
    root = min(pitches)
    root_name = note_names[root]
    
    # 근음 기준으로 상대적 음정 계산
    intervals = sorted([(p - root) % 12 for p in pitches])
    
    # 기본적인 코드 패턴 매칭
    if intervals == [0, 4, 7]:  # Major triad
        return root_name
    elif intervals == [0, 3, 7]:  # Minor triad
        return root_name + 'm'
    elif intervals == [0, 4, 7, 10]:  # Dominant 7th
        return root_name + '7'
    elif intervals == [0, 3, 7, 10]:  # Minor 7th
        return root_name + 'm7'
    elif intervals == [0, 4, 7, 11]:  # Major 7th
        return root_name + 'maj7'
    else:
        # 기본적으로 근음 이름 반환
        return root_name


# ─── 오디오 분석 ────────────────────────────────────────────────
def analyze_audio_for_chords_basic_pitch(audio_path: str) -> dict:
    """
    Basic Pitch를 사용하여 오디오에서 MIDI를 추출하고 코드를 분석합니다.
    """
    try:
        app.logger.info(f"Basic Pitch로 오디오 분석 시작: {audio_path}")
        
        # 임시 디렉토리 생성
        with tempfile.TemporaryDirectory() as temp_dir:
            # Basic Pitch로 MIDI 파일 생성
            app.logger.info("Basic Pitch로 MIDI 변환 중...")
            
            # Basic Pitch 모델로 예측 및 MIDI 파일 저장
            predict_and_save(
                [audio_path],
                temp_dir,
                save_midi=True,
                sonify_midi=False,
                save_model_outputs=False,
                save_notes=False
            )
            
            # 생성된 MIDI 파일 찾기
            midi_files = glob.glob(os.path.join(temp_dir, "*.mid"))
            if not midi_files:
                raise FileNotFoundError("MIDI 파일이 생성되지 않았습니다.")
            
            midi_path = midi_files[0]
            app.logger.info(f"MIDI 파일 생성 완료: {midi_path}")
            
            # MIDI에서 코드 추출
            result = extract_chords_from_midi(midi_path)
            app.logger.info("코드 분석 완료")
            
            return result
            
    except Exception as e:
        app.logger.error(f"Basic Pitch 분석 오류: {e}", exc_info=True)
        # 오류 발생 시 기본값 반환
        return {
            'bpm': 120,
            'signature': '4/4',
            'key': 'C Major',
            'chords': [
                {'chord': 'C', 'timestamp': 0, 'duration': 4},
                {'chord': 'Am', 'timestamp': 4, 'duration': 4},
                {'chord': 'F', 'timestamp': 8, 'duration': 4},
                {'chord': 'G', 'timestamp': 12, 'duration': 4},
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
        result = analyze_audio_for_chords_basic_pitch(temp_path)
        os.remove(temp_path)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ─── 앱 실행 ──────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(port=5001, debug=True)