import bcrypt
from database import get_db_connection, init_database
import json

def test_database():
    """데이터베이스 테스트"""
    try:
        # 데이터베이스 초기화
        print("데이터베이스 초기화 중...")
        init_database()
        
        # 테스트 사용자 추가
        print("테스트 사용자 추가 중...")
        test_email = "test@example.com"
        test_password = "testpassword123"
        test_nickname = "테스트유저"
        
        # 비밀번호 해시화
        hashed_password = bcrypt.hashpw(test_password.encode('utf-8'), bcrypt.gensalt())
        
        with get_db_connection() as connection:
            cursor = connection.cursor()
            
            # 기존 테스트 사용자 삭제
            cursor.execute("DELETE FROM users WHERE email = %s", (test_email,))
            
            # 새 사용자 추가
            insert_user_query = """
            INSERT INTO users (email, password, nickname) 
            VALUES (%s, %s, %s)
            """
            cursor.execute(insert_user_query, (test_email, hashed_password.decode('utf-8'), test_nickname))
            
            # 사용자 조회
            cursor.execute("SELECT id, email, nickname, created_at FROM users WHERE email = %s", (test_email,))
            user = cursor.fetchone()
            
            if user:
                print(f"✅ 사용자 추가 성공:")
                print(f"   ID: {user[0]}")
                print(f"   Email: {user[1]}")
                print(f"   Nickname: {user[2]}")
                print(f"   Created: {user[3]}")
            
            # 테스트 곡 정보 추가
            print("\n테스트 곡 정보 추가 중...")
            test_song_data = {
                'video_id': 'dQw4w9WgXcQ',
                'title': 'Rick Astley - Never Gonna Give You Up',
                'channel_title': 'Rick Astley',
                'thumbnail_url': 'https://i.ytimg.com/vi/dQw4w9WgXcQ/hqdefault.jpg',
                'bpm': 113,
                'signature': '4/4',
                'song_key': 'F Major',
                'chords': [
                    {"chord": "F", "timestamp": 0.0, "duration": 2.0},
                    {"chord": "Am", "timestamp": 2.0, "duration": 2.0},
                    {"chord": "Bb", "timestamp": 4.0, "duration": 2.0},
                    {"chord": "F", "timestamp": 6.0, "duration": 2.0}
                ],
                'chord_charts': [
                    {"chord": "F", "frets": [1, 3, 3, 2, 1, 1], "fingers": [1, 3, 4, 2, 1, 1]},
                    {"chord": "Am", "frets": [0, 0, 2, 2, 1, 0], "fingers": [0, 0, 2, 3, 1, 0]},
                    {"chord": "Bb", "frets": [1, 1, 3, 3, 3, 1], "fingers": [1, 1, 2, 3, 4, 1]}
                ],
                'file_path': '/downloads/test_song.mp3'
            }
            
            # 기존 테스트 곡 삭제
            cursor.execute("DELETE FROM analyzed_songs WHERE video_id = %s", (test_song_data['video_id'],))
            
            # 새 곡 정보 추가
            insert_song_query = """
            INSERT INTO analyzed_songs 
            (video_id, title, channel_title, thumbnail_url, bpm, signature, song_key, chords, chord_charts, file_path) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(insert_song_query, (
                test_song_data['video_id'],
                test_song_data['title'],
                test_song_data['channel_title'],
                test_song_data['thumbnail_url'],
                test_song_data['bpm'],
                test_song_data['signature'],
                test_song_data['song_key'],
                json.dumps(test_song_data['chords']),
                json.dumps(test_song_data['chord_charts']),
                test_song_data['file_path']
            ))
            
            # 곡 정보 조회
            cursor.execute("SELECT id, video_id, title, bpm, song_key FROM analyzed_songs WHERE video_id = %s", (test_song_data['video_id'],))
            song = cursor.fetchone()
            
            if song:
                print(f"✅ 곡 정보 추가 성공:")
                print(f"   ID: {song[0]}")
                print(f"   Video ID: {song[1]}")
                print(f"   Title: {song[2]}")
                print(f"   BPM: {song[3]}")
                print(f"   Key: {song[4]}")
            
            connection.commit()
            print("\n✅ 데이터베이스 테스트 완료!")
            
    except Exception as e:
        print(f"❌ 데이터베이스 테스트 실패: {e}")
        raise

if __name__ == "__main__":
    test_database()