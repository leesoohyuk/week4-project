# AutoChord 🎵

YouTube Data API v3와 React/Vite로 만든 코드·영상 검색 & 재생 웹앱입니다.

---

## 🚀 주요 기능

- 키워드 기반 YouTube 영상 검색  
- 검색 결과 페이징 & 무한 스크롤  
- IFrame 플레이어로 동영상 재생  
- 코드 차트(Chord Chart) 및 진행도 표시  

---

## 📋 사전 준비

1. Node.js (v16 이상 권장) & npm 설치  
2. YouTube Data API v3 사용 가능한 API 키 발급  
   - [Google Cloud Platform 콘솔](https://console.cloud.google.com/apis/library/youtube.googleapis.com)에서 “YouTube Data API v3” 활성화 후 API 키 생성  
3. Git 클라이언트  
4. ffmpeg 다운로드
   - 다운로드 | [ffmpeg builds](https://www.gyan.dev/ffmpeg/builds/) 
   - 압축 해제 | `C:\ffmpeg\ffmpeg\bin\ffmpeg.exe` 확인 
   - 환경변수 설정 | `C:\ffmpeg\ffmpeg\bin` 을 Path에 추가 
   - 확인 | `ffmpeg -version` 실행해 확인 

---

## 🔧 설치 및 실행

1. 레포지터리 클론  
   ```bash
   git clone https://github.com/your-username/your-repo.git
   cd your-repo

2. 환경 변수 예시 파일 복사
    ```bash
    cp .env.example .env.local

3. .env.local 파일 열어 API 키 입력
    VITE_YOUTUBE_API_KEY=YOUR_YOUTUBE_API_KEY_HERE
    YOUR_YOUTUBE_API_KEY_HERE -> API Key

4. 의존성 설치 & 개발 서버 실행
    ```bash
    npm install
    npm run dev

---

## 🔐 환경 변수

- .env.local 파일 커밋 금지
- 저장소에는 .env.example만 포함