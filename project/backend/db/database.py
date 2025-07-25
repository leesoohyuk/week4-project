import mysql.connector
from mysql.connector import Error
import os
from contextlib import contextmanager

# 데이터베이스 설정
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'database': os.getenv('DB_NAME', 'autochord'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),
    'port': int(os.getenv('DB_PORT', 3306)),
    'charset': 'utf8mb4',
    'collation': 'utf8mb4_unicode_ci'
}

@contextmanager
def get_db_connection():
    """데이터베이스 연결 컨텍스트 매니저"""
    connection = None
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        yield connection
    except Error as e:
        print(f"데이터베이스 연결 오류: {e}")
        if connection:
            connection.rollback()
        raise
    finally:
        if connection and connection.is_connected():
            connection.close()

def create_database():
    """데이터베이스 생성"""
    try:
        # 데이터베이스 없이 연결
        temp_config = DB_CONFIG.copy()
        temp_config.pop('database')
        
        connection = mysql.connector.connect(**temp_config)
        cursor = connection.cursor()
        
        # 데이터베이스 생성
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_CONFIG['database']} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        print(f"데이터베이스 '{DB_CONFIG['database']}' 생성 완료")
        
        cursor.close()
        connection.close()
        
    except Error as e:
        print(f"데이터베이스 생성 오류: {e}")
        raise

def create_tables():
    """테이블 생성"""
    try:
        with get_db_connection() as connection:
            cursor = connection.cursor()
            
            # 사용자 테이블 생성
            create_users_table = """
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                email VARCHAR(255) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                nickname VARCHAR(100) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_email (email),
                INDEX idx_nickname (nickname)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """
            
            # 분석된 곡 정보 테이블 생성
            create_songs_table = """
            CREATE TABLE IF NOT EXISTS analyzed_songs (
                id INT AUTO_INCREMENT PRIMARY KEY,
                video_id VARCHAR(20) UNIQUE NOT NULL,
                title VARCHAR(500) NOT NULL,
                channel_title VARCHAR(255) NOT NULL,
                thumbnail_url TEXT,
                bpm INT,
                signature VARCHAR(10),
                song_key VARCHAR(20),
                chords JSON,
                chord_charts JSON,
                file_path VARCHAR(500),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_video_id (video_id),
                INDEX idx_title (title(100))
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """
            
            cursor.execute(create_users_table)
            cursor.execute(create_songs_table)
            
            connection.commit()
            print("테이블 생성 완료")
            
    except Error as e:
        print(f"테이블 생성 오류: {e}")
        raise

def init_database():
    """데이터베이스 초기화"""
    create_database()
    create_tables()

if __name__ == "__main__":
    init_database()