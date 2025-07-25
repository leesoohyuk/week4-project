@@ .. @@
             # 분석된 곡 정보 테이블 생성
             create_songs_table = """
             CREATE TABLE IF NOT EXISTS analyzed_songs (
                 id INT AUTO_INCREMENT PRIMARY KEY,
                 video_id VARCHAR(20) NOT NULL,
+                user_id INT NOT NULL,
                 title VARCHAR(500) NOT NULL,
                 channel_title VARCHAR(255) NOT NULL,
                 thumbnail_url TEXT,
@@ .. @@
                 file_path VARCHAR(500),
                 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                 updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
+                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
+                UNIQUE KEY unique_user_video (user_id, video_id),
                 INDEX idx_video_id (video_id),
+                INDEX idx_user_id (user_id),
                 INDEX idx_title (title(100))
             ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
             """