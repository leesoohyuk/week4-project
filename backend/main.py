@@ .. @@
 from flask import Flask, request, jsonify
 from flask_cors import CORS
+from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
+import bcrypt
 import yt_dlp
 import os
@@ .. @@
 import logging
 from pathlib import Path
 from scipy.ndimage import gaussian_filter1d
+import sys
+sys.path.append(os.path.join(os.path.dirname(__file__), 'db'))
+from database import get_db_connection

 logging.basicConfig(level=logging.INFO)

 app = Flask(__name__)
 CORS(app)
+app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET', 'your-secret-key-change-this')
+jwt = JWTManager(app)

 OUTPUT_DIR = "downloads"
@@ .. @@
         raise


+@app.route("/auth/signup", methods=["POST"])
+def signup():
+    data = request.get_json()
+    email = data.get("email")
+    password = data.get("password")
+    nickname = data.get("nickname")
+
+    if not all([email, password, nickname]):
+        return jsonify({"error": "모든 필드를 입력해주세요"}), 400

+    try:
+        with get_db_connection() as connection:
+            cursor = connection.cursor()
+            
+            # 이메일 중복 확인
+            cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
+            if cursor.fetchone():
+                return jsonify({"error": "이미 존재하는 이메일입니다"}), 400
+            
+            # 비밀번호 해시화
+            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
+            
+            # 사용자 생성
+            cursor.execute(
+                "INSERT INTO users (email, password, nickname) VALUES (%s, %s, %s)",
+                (email, hashed_password.decode('utf-8'), nickname)
+            )
+            connection.commit()
+            
+            return jsonify({"message": "회원가입이 완료되었습니다"}), 201
+            
+    except Exception as e:
+        app.logger.exception("Signup failed")
+        return jsonify({"error": "회원가입 중 오류가 발생했습니다"}), 500


+@app.route("/auth/login", methods=["POST"])
+def login():
+    data = request.get_json()
+    email = data.get("email")
+    password = data.get("password")

+    if not all([email, password]):
+        return jsonify({"error": "이메일과 비밀번호를 입력해주세요"}), 400

+    try:
+        with get_db_connection() as connection:
+            cursor = connection.cursor()
+            cursor.execute("SELECT id, email, password, nickname FROM users WHERE email = %s", (email,))
+            user = cursor.fetchone()
+            
+            if user and bcrypt.checkpw(password.encode('utf-8'), user[2].encode('utf-8')):
+                access_token = create_access_token(identity=user[0])
+                return jsonify({
+                    "token": access_token,
+                    "user": {
+                        "id": user[0],
+                        "email": user[1],
+                        "nickname": user[3]
+                    }
+                }), 200
+            else:
+                return jsonify({"error": "이메일 또는 비밀번호가 잘못되었습니다"}), 401
+                
+    except Exception as e:
+        app.logger.exception("Login failed")
+        return jsonify({"error": "로그인 중 오류가 발생했습니다"}), 500


 @app.route("/analyze", methods=["POST"])
 def analyze_song():
     data = request.get_json(silent=True) or {}
     video_id = data.get("videoId")
     video_url = data.get("url")
+    save_to_db = data.get("saveToDb", False)

     if not video_url and video_id:
@@ .. @@
     try:
         audio_path = download_audio_from_youtube(video_url, OUTPUT_DIR)
         result = analyze_audio_for_chords(audio_path)
+        
+        # 로그인된 사용자이고 저장 요청이 있는 경우 DB에 저장
+        if save_to_db:
+            try:
+                user_id = get_jwt_identity()
+                if user_id:
+                    save_analysis_to_db(video_id, result, audio_path, user_id)
+            except Exception as e:
+                app.logger.warning(f"Failed to save analysis to DB: {e}")
+        
         return jsonify(result)
     except Exception as e:
         app.logger.exception("Analyze failed")
         return jsonify({"error": str(e)}), 500


+def save_analysis_to_db(video_id, analysis_result, audio_path, user_id):
+    """분석 결과를 데이터베이스에 저장"""
+    try:
+        # YouTube API로 비디오 정보 가져오기 (간단히 구현)
+        title = f"Video {video_id}"
+        channel_title = "Unknown"
+        thumbnail_url = f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"
+        
+        with get_db_connection() as connection:
+            cursor = connection.cursor()
+            
+            # 기존 분석 데이터가 있는지 확인
+            cursor.execute("SELECT id FROM analyzed_songs WHERE video_id = %s AND user_id = %s", (video_id, user_id))
+            existing = cursor.fetchone()
+            
+            if existing:
+                # 업데이트
+                cursor.execute("""
+                    UPDATE analyzed_songs 
+                    SET bpm = %s, signature = %s, song_key = %s, chords = %s, chord_charts = %s, 
+                        file_path = %s, updated_at = CURRENT_TIMESTAMP
+                    WHERE video_id = %s AND user_id = %s
+                """, (
+                    analysis_result.get('bpm'),
+                    analysis_result.get('signature'),
+                    analysis_result.get('key'),
+                    json.dumps(analysis_result.get('chords', [])),
+                    json.dumps(analysis_result.get('chordCharts', [])),
+                    audio_path,
+                    video_id,
+                    user_id
+                ))
+            else:
+                # 새로 삽입
+                cursor.execute("""
+                    INSERT INTO analyzed_songs 
+                    (video_id, title, channel_title, thumbnail_url, bpm, signature, song_key, 
+                     chords, chord_charts, file_path, user_id) 
+                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
+                """, (
+                    video_id, title, channel_title, thumbnail_url,
+                    analysis_result.get('bpm'),
+                    analysis_result.get('signature'),
+                    analysis_result.get('key'),
+                    json.dumps(analysis_result.get('chords', [])),
+                    json.dumps(analysis_result.get('chordCharts', [])),
+                    audio_path,
+                    user_id
+                ))
+            
+            connection.commit()
+            
+    except Exception as e:
+        app.logger.exception(f"Failed to save analysis to DB: {e}")


+@app.route("/analysis/<video_id>", methods=["GET"])
+@jwt_required()
+def get_saved_analysis(video_id):
+    """저장된 분석 데이터 불러오기"""
+    try:
+        user_id = get_jwt_identity()
+        
+        with get_db_connection() as connection:
+            cursor = connection.cursor()
+            cursor.execute("""
+                SELECT bpm, signature, song_key, chords, chord_charts 
+                FROM analyzed_songs 
+                WHERE video_id = %s AND user_id = %s
+            """, (video_id, user_id))
+            
+            result = cursor.fetchone()
+            if result:
+                return jsonify({
+                    "bpm": result[0],
+                    "signature": result[1],
+                    "key": result[2],
+                    "chords": json.loads(result[3]) if result[3] else [],
+                    "chordCharts": json.loads(result[4]) if result[4] else []
+                })
+            else:
+                return jsonify({"error": "저장된 분석 데이터가 없습니다"}), 404
+                
+    except Exception as e:
+        app.logger.exception("Failed to load saved analysis")
+        return jsonify({"error": "분석 데이터를 불러오는 중 오류가 발생했습니다"}), 500


+@app.route("/analysis/<video_id>/exists", methods=["GET"])
+@jwt_required()
+def check_analysis_exists(video_id):
+    """분석 데이터 존재 여부 확인"""
+    try:
+        user_id = get_jwt_identity()
+        
+        with get_db_connection() as connection:
+            cursor = connection.cursor()
+            cursor.execute("""
+                SELECT COUNT(*) FROM analyzed_songs 
+                WHERE video_id = %s AND user_id = %s
+            """, (video_id, user_id))
+            
+            count = cursor.fetchone()[0]
+            return jsonify({"exists": count > 0})
+            
+    except Exception as e:
+        app.logger.exception("Failed to check analysis existence")
+        return jsonify({"exists": False})


 if __name__ == "__main__":