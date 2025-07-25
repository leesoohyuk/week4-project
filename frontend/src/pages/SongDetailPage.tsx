@@ .. @@
 import React, { useState, useEffect } from 'react';
 import { useParams, useNavigate } from 'react-router-dom';
+import { useAuth } from '../contexts/AuthContext';
 import SearchBar from '../components/SearchBar';
 import YouTubePlayer from '../components/YouTubePlayer';
 import LoginButton from '../components/LoginButton';
@@ .. @@
 import { getSongDetail } from '../utils/api';
 import { requestDownload } from '../utils/api';
 import { SongDetail } from '../types/song';
-import { analyzeSong } from '../utils/api';
+import { analyzeSong, loadSavedAnalysis, checkSavedAnalysis } from '../utils/api';

 const SongDetailPage: React.FC = () => {
   const { videoId } = useParams<{ videoId: string }>();
   const navigate = useNavigate();
+  const { isAuthenticated } = useAuth();
   const [songDetail, setSongDetail] = useState<SongDetail | null>(null);
   const [loading, setLoading] = useState(true);
@@ .. @@
   const [audioUrl, setAudioUrl] = useState('');
   const [downloading, setDownloading] = useState(false);
   const [analyzing, setAnalyzing] = useState(false);
+  const [hasSavedAnalysis, setHasSavedAnalysis] = useState(false);
+  const [loadingSaved, setLoadingSaved] = useState(false);

@@ .. @@
     loadSongDetail(videoId);
+    
+    // 로그인된 사용자의 경우 저장된 분석 데이터 확인
+    if (isAuthenticated && videoId) {
+      checkSavedAnalysis(videoId).then(setHasSavedAnalysis);
+    }
   }, [videoId]);

+  // 로그인 상태 변경 시 저장된 분석 데이터 확인
+  useEffect(() => {
+    if (isAuthenticated && videoId) {
+      checkSavedAnalysis(videoId).then(setHasSavedAnalysis);
+    } else {
+      setHasSavedAnalysis(false);
+    }
+  }, [isAuthenticated, videoId]);
+
   const handleSearch = (query: string) => {
@@ .. @@
   const handleAnalyze = async () => {
   if (!videoId) return;
   try {
     setAnalyzing(true);
-    const result = await analyzeSong(videoId);
+    const result = await analyzeSong(videoId, isAuthenticated);
     setSongDetail(prev => prev ? { ...prev, ...result } : result);  // 덮어쓰기
+    
+    // 분석 완료 후 저장된 분석 데이터 확인
+    if (isAuthenticated) {
+      setHasSavedAnalysis(true);
+    }
   } catch (err) {
     alert('분석 중 오류가 발생했습니다.');
     console.error(err);
@@ .. @@
     }
   };

+  const handleLoadSaved = async () => {
+    if (!videoId) return;
+    try {
+      setLoadingSaved(true);
+      const result = await loadSavedAnalysis(videoId);
+      setSongDetail(prev => prev ? { ...prev, ...result } : result);
+    } catch (err) {
+      alert('저장된 분석 데이터를 불러오는 중 오류가 발생했습니다.');
+      console.error(err);
+    } finally {
+      setLoadingSaved(false);
+    }
+  };
+
   if (loading) {
@@ .. @@
                   </div>
-                  <div className="mt-4">
+                  <div className="mt-4 flex gap-2">
                     <button
                       className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
                       onClick={handleAnalyze}
                       disabled={analyzing}
                     >
                       {analyzing ? '분석 중...' : '코드 자동 분석'}
                     </button>
+                    {isAuthenticated && hasSavedAnalysis && (
+                      <button
+                        className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50"
+                        onClick={handleLoadSaved}
+                        disabled={loadingSaved}
+                      >
+                        {loadingSaved ? '불러오는 중...' : '불러오기'}
+                      </button>
+                    )}
                   </div>
               </div>
             </div>