import os
import uuid
import shutil
import glob
import tempfile
import json

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
def download_audio_file(video_url: str, force_mp3: bool = True):
    """
    YouTube에서 오디오를 다운로드하고 MP3로 변환합니다.
    force_mp3가 True면 FFmpeg 없어도 librosa로 변환 시도
    """
    uid = str(uuid.uuid4())
    
    if force_mp3:
        # 강제로 MP3 변환
        temp_path = os.path.join(OUTPUT_DIR, f"{uid}_temp")
        final_path = os.path.join(OUTPUT_DIR, f"{uid}.mp3")
        
        # 1단계: 원본 다운로드
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': f"{temp_path}.%(ext)s",
            'quiet': True
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])
        
        # 다운로드된 파일 찾기
        temp_files = glob.glob(f"{temp_path}.*")
        if not temp_files:
            raise FileNotFoundError("다운로드 실패")
        
        downloaded_file = temp_files[0]
        
        # 2단계: librosa로 MP3 변환
        try:
            print(f"Converting {downloaded_file} to MP3...")
            y, sr = librosa.load(downloaded_file, sr=22050)
            
            # soundfile로 MP3 저장 (librosa 내부적으로 사용)
            import soundfile as sf
            sf.write(final_path, y, sr, format='mp3')
            
            # 임시 파일 삭제
            os.remove(downloaded_file)
            
            return final_path, f"{uid}.mp3"
            
        except Exception as e:
            print(f"MP3 변환 실패, 원본 파일 사용: {e}")
            # 변환 실패시 원본 파일 이름 변경
            new_name = f"{uid}.{downloaded_file.split('.')[-1]}"
            new_path = os.path.join(OUTPUT_DIR, new_name)
            shutil.move(downloaded_file, new_path)
            return new_path, new_name
    
    else:
        # 기존 방식
        if HAS_FFMPEG:
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
            outtmpl = os.path.join(OUTPUT_DIR, f"{uid}.%(ext)s")
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': outtmpl,
                'quiet': True
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.extract_info(video_url, download=True)

        pattern = os.path.join(OUTPUT_DIR, f"{uid}.*")
        matches = glob.glob(pattern)
        if not matches:
            raise FileNotFoundError(f"No file found matching pattern {pattern}")
        audio_path = matches[0]
        filename = os.path.basename(audio_path)
        return audio_path, filename


# ─── 코드 진행 & 차트 데이터 ────────────────────────────────────
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
    'Gm':   {'chord':'Gm',  'frets':[3,5,5,3,3,3], 'fingers':[1,3,4,1,1,1]},
    'Cm':   {'chord':'Cm',  'frets':[3,3,5,5,4,3], 'fingers':[1,1,3,4,2,1]},
    'Fm':   {'chord':'Fm',  'frets':[1,3,3,1,1,1], 'fingers':[1,3,4,1,1,1]},
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
    intervals = sorted(list(set([(p - root) % 12 for p in pitches])))
    
    print(f"Root: {root_name}, Intervals: {intervals}")
    
    # 기본적인 코드 패턴 매칭
    if len(intervals) >= 3:
        if 4 in intervals and 7 in intervals:  # Major triad
            return root_name
        elif 3 in intervals and 7 in intervals:  # Minor triad
            return root_name + 'm'
        elif 4 in intervals and 7 in intervals and 10 in intervals:  # Dominant 7th
            return root_name + '7'
        elif 3 in intervals and 7 in intervals and 10 in intervals:  # Minor 7th
            return root_name + 'm7'
        elif 4 in intervals and 7 in intervals and 11 in intervals:  # Major 7th
            return root_name + 'maj7'
    
    # 2음 조합
    if len(intervals) >= 2:
        if 4 in intervals:
            return root_name
        elif 3 in intervals:
            return root_name + 'm'
    
    # 기본적으로 근음 이름 반환
    return root_name


def extract_chords_from_midi(midi_path: str) -> dict:
    """
    MIDI 파일에서 코드 진행을 추출합니다.
    """
    try:
        print(f"MIDI 파일 분석 시작: {midi_path}")
        
        # MIDI 파일 로드
        midi_file = mido.MidiFile(midi_path)
        
        # MIDI에서 노트 정보 추출
        notes = []
        current_time = 0
        
        for track_idx, track in enumerate(midi_file.tracks):
            track_time = 0
            print(f"Track {track_idx}: {len(track)} messages")
            
            for msg in track:
                track_time += msg.time
                if msg.type == 'note_on' and msg.velocity > 0:
                    notes.append({
                        'pitch': msg.note,
                        'time': track_time / (midi_file.ticks_per_beat or 480),
                        'velocity': msg.velocity
                    })
        
        print(f"총 {len(notes)}개의 노트 추출됨")
        
        if not notes:
            print("노트가 없어서 기본값 반환")
            return get_default_analysis()
        
        # 시간대별로 노트 그룹화 (2초 단위)
        chord_duration = 2.0
        max_time = max(note['time'] for note in notes) if notes else 16.0
        print(f"최대 시간: {max_time}초")
        
        chords_data = []
        chord_charts_set = set()
        
        # 시간 구간별로 분석
        num_segments = max(8, int(max_time / chord_duration))
        
        for i in range(num_segments):
            start_time = i * chord_duration
            end_time = (i + 1) * chord_duration
            
            # 해당 시간대의 노트들 수집
            time_notes = [n for n in notes if start_time <= n['time'] < end_time]
            
            if time_notes:
                # 가장 많이 나타나는 음들을 기반으로 코드 추정
                pitches = [n['pitch'] % 12 for n in time_notes]
                pitch_counts = {}
                for p in pitches:
                    pitch_counts[p] = pitch_counts.get(p, 0) + 1
                
                # 상위 3-4개 음으로 코드 구성
                top_pitches = sorted(pitch_counts.items(), key=lambda x: x[1], reverse=True)[:4]
                chord_pitches = [p[0] for p in top_pitches if p[1] >= 2]  # 최소 2번 이상 나타난 음만
                
                if chord_pitches:
                    chord_name = estimate_chord_name(chord_pitches)
                else:
                    # 기본 진행에서 선택
                    default_progression = ['C', 'Am', 'F', 'G', 'Em', 'Dm']
                    chord_name = default_progression[i % len(default_progression)]
                
                print(f"시간 {start_time}-{end_time}: {chord_pitches} -> {chord_name}")
                
            else:
                # 기본 코드 진행 사용
                default_progression = ['C', 'Am', 'F', 'G', 'Em', 'Dm']
                chord_name = default_progression[i % len(default_progression)]
                print(f"시간 {start_time}-{end_time}: 노트 없음 -> {chord_name}")
            
            chords_data.append({
                'chord': chord_name,
                'timestamp': start_time,
                'duration': chord_duration
            })
            chord_charts_set.add(chord_name)
        
        # BPM 추정
        estimated_bpm = 120
        if len(notes) > 10:
            # 연속된 노트들 간의 시간 간격 분석
            time_diffs = []
            sorted_notes = sorted(notes, key=lambda x: x['time'])
            
            for i in range(1, min(len(sorted_notes), 50)):
                diff = sorted_notes[i]['time'] - sorted_notes[i-1]['time']
                if 0.1 < diff < 2.0:
                    time_diffs.append(diff)
            
            if time_diffs:
                # 가장 일반적인 시간 간격 찾기
                time_diffs.sort()
                median_diff = time_diffs[len(time_diffs)//2]
                estimated_bpm = int(60 / (median_diff * 2))  # 8분음표 기준
                estimated_bpm = max(60, min(200, estimated_bpm))
        
        print(f"추정 BPM: {estimated_bpm}")
        
        # 조성 추정
        if notes:
            pitch_profile = [0] * 12
            for note in notes:
                pitch_profile[note['pitch'] % 12] += note['velocity']
            
            # 가장 많이 나타나는 음을 근음으로 추정
            root_pitch = pitch_profile.index(max(pitch_profile))
            keys = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
            
            # Major/Minor 판별 (간단한 휴리스틱)
            major_third = (root_pitch + 4) % 12
            minor_third = (root_pitch + 3) % 12
            
            if pitch_profile[major_third] > pitch_profile[minor_third]:
                estimated_key = f"{keys[root_pitch]} Major"
            else:
                estimated_key = f"{keys[root_pitch]} Minor"
        else:
            estimated_key = "C Major"
        
        print(f"추정 조성: {estimated_key}")
        
        # 코드 차트 생성
        chord_charts = []
        for chord_name in sorted(chord_charts_set):
            if chord_name in CHORD_CHARTS:
                chord_charts.append(CHORD_CHARTS[chord_name])
            else:
                # 기본 C 코드로 대체
                chord_charts.append({
                    'chord': chord_name,
                    'frets': [0,3,2,0,1,0],
                    'fingers': [0,3,2,0,1,0]
                })
        
        result = {
            'bpm': estimated_bpm,
            'signature': '4/4',
            'key': estimated_key,
            'chords': chords_data,
            'chordCharts': chord_charts
        }
        
        print(f"분석 완료: {len(chords_data)}개 코드, {len(chord_charts)}개 차트")
        return result
        
    except Exception as e:
        print(f"MIDI 분석 오류: {e}")
        import traceback
        traceback.print_exc()
        return get_default_analysis()


def get_default_analysis():
    """기본 분석 결과 반환"""
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


def analyze_audio_for_chords_basic_pitch(audio_path: str) -> dict:
    """
    Basic Pitch를 사용하여 오디오에서 MIDI를 추출하고 코드를 분석합니다.
    """
    try:
        print(f"Basic Pitch로 오디오 분석 시작: {audio_path}")
        
        # 오디오 파일 존재 확인
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"오디오 파일을 찾을 수 없습니다: {audio_path}")
        
        # 파일 크기 확인
        file_size = os.path.getsize(audio_path)
        print(f"오디오 파일 크기: {file_size} bytes")
        
        if file_size == 0:
            raise ValueError("오디오 파일이 비어있습니다")
        
        # 임시 디렉토리 생성
        with tempfile.TemporaryDirectory() as temp_dir:
            print(f"임시 디렉토리: {temp_dir}")
            
            # Basic Pitch로 MIDI 파일 생성
            print("Basic Pitch로 MIDI 변환 중...")
            
            try:
                # Basic Pitch 실행
                predict_and_save(
                    [audio_path],
                    temp_dir,
                    save_midi=True,
                    sonify_midi=False,
                    save_model_outputs=False,
                    save_notes=False
                )
                
                print("Basic Pitch 변환 완료")
                
            except Exception as bp_error:
                print(f"Basic Pitch 오류: {bp_error}")
                # Basic Pitch 실패시 librosa로 대체 분석
                return analyze_with_librosa_fallback(audio_path)
            
            # 생성된 MIDI 파일 찾기
            midi_files = glob.glob(os.path.join(temp_dir, "*.mid"))
            if not midi_files:
                print("MIDI 파일이 생성되지 않았습니다. Librosa로 대체 분석")
                return analyze_with_librosa_fallback(audio_path)
            
            midi_path = midi_files[0]
            print(f"MIDI 파일 생성 완료: {midi_path}")
            
            # MIDI 파일 크기 확인
            midi_size = os.path.getsize(midi_path)
            print(f"MIDI 파일 크기: {midi_size} bytes")
            
            if midi_size == 0:
                print("MIDI 파일이 비어있습니다. Librosa로 대체 분석")
                return analyze_with_librosa_fallback(audio_path)
            
            # MIDI에서 코드 추출
            result = extract_chords_from_midi(midi_path)
            print("코드 분석 완료")
            
            return result
            
    except Exception as e:
        print(f"Basic Pitch 분석 오류: {e}")
        import traceback
        traceback.print_exc()
        # 오류 발생 시 librosa로 대체 분석
        return analyze_with_librosa_fallback(audio_path)


def analyze_with_librosa_fallback(audio_path: str) -> dict:
    """
    Basic Pitch 실패시 librosa를 사용한 대체 분석
    """
    try:
        print("Librosa로 대체 분석 시작")
        
        # 오디오 로드
        y, sr = librosa.load(audio_path, sr=22050, duration=60)  # 첫 60초만 분석
        
        # 크로마 특성 추출
        chroma = librosa.feature.chroma_stft(y=y, sr=sr, hop_length=512)
        
        # 템포 추정
        tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
        estimated_bpm = int(tempo)
        
        print(f"Librosa 추정 BPM: {estimated_bpm}")
        
        # 크로마 기반 코드 추정
        chord_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        
        # 시간 구간별 분석 (4초 단위)
        segment_duration = 4.0
        hop_length = 512
        frames_per_segment = int(segment_duration * sr / hop_length)
        
        chords_data = []
        chord_charts_set = set()
        
        for i in range(0, chroma.shape[1], frames_per_segment):
            segment_chroma = chroma[:, i:i+frames_per_segment]
            if segment_chroma.shape[1] == 0:
                continue
                
            # 평균 크로마 벡터
            avg_chroma = np.mean(segment_chroma, axis=1)
            
            # 가장 강한 음 찾기
            root_idx = np.argmax(avg_chroma)
            
            # Major/Minor 판별 (간단한 휴리스틱)
            major_third_idx = (root_idx + 4) % 12
            minor_third_idx = (root_idx + 3) % 12
            
            if avg_chroma[major_third_idx] > avg_chroma[minor_third_idx]:
                chord_name = chord_names[root_idx]
            else:
                chord_name = chord_names[root_idx] + 'm'
            
            timestamp = i * hop_length / sr
            
            chords_data.append({
                'chord': chord_name,
                'timestamp': timestamp,
                'duration': segment_duration
            })
            chord_charts_set.add(chord_name)
        
        # 조성 추정
        overall_chroma = np.mean(chroma, axis=1)
        key_idx = np.argmax(overall_chroma)
        estimated_key = f"{chord_names[key_idx]} Major"
        
        # 코드 차트 생성
        chord_charts = []
        for chord_name in sorted(chord_charts_set):
            if chord_name in CHORD_CHARTS:
                chord_charts.append(CHORD_CHARTS[chord_name])
            else:
                chord_charts.append({
                    'chord': chord_name,
                    'frets': [0,3,2,0,1,0],
                    'fingers': [0,3,2,0,1,0]
                })
        
        result = {
            'bpm': estimated_bpm,
            'signature': '4/4',
            'key': estimated_key,
            'chords': chords_data,
            'chordCharts': chord_charts
        }
        
        print(f"Librosa 분석 완료: {len(chords_data)}개 코드")
        return result
        
    except Exception as e:
        print(f"Librosa 분석도 실패: {e}")
        return get_default_analysis()


# ─── /download 엔드포인트 ────────────────────────────────────────
@app.route("/download", methods=["POST"])
def download_endpoint():
    data = request.get_json()
    url = data.get("url")
    if not url:
        return jsonify({"error": "URL is required"}), 400

    try:
        path, filename = download_audio_file(url, force_mp3=True)
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
    temp_path = None
    
    try:
        print(f"분석 시작: {video_url}")
        temp_path, _ = download_audio_file(video_url, force_mp3=True)
        print(f"다운로드 완료: {temp_path}")
        
        result = analyze_audio_for_chords_basic_pitch(temp_path)
        print("분석 완료")
        
        return jsonify(result)
        
    except Exception as e:
        print(f"분석 오류: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
        
    finally:
        # 임시 파일 정리
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
                print(f"임시 파일 삭제: {temp_path}")
            except:
                pass


# ─── 앱 실행 ──────────────────────────────────────────────────
if __name__ == "__main__":
    print("서버 시작...")
    app.run(port=5001, debug=True)