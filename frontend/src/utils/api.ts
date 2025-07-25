@@ .. @@
 /**
  * 서버에 분석 요청
  * @param videoId 유튜브 영상 ID
  * @returns 분석 결과
  */
-export const analyzeSong = async (videoId: string) => {
+export const analyzeSong = async (videoId: string, saveToDb: boolean = false) => {
+  const token = localStorage.getItem('authToken');
+  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
+  
+  if (token) {
+    headers['Authorization'] = `Bearer ${token}`;
+  }
+
   const res = await fetch(`${SERVER_URL}/analyze`, {
     method: 'POST',
-    headers: { 'Content-Type': 'application/json' },
-    body: JSON.stringify({ videoId }),
+    headers,
+    body: JSON.stringify({ videoId, saveToDb }),
   });

   if (!res.ok) throw new Error('분석 실패');
   return await res.json();
 };
+
+/**
+ * 저장된 분석 데이터 불러오기
+ * @param videoId 유튜브 영상 ID
+ * @returns 저장된 분석 결과
+ */
+export const loadSavedAnalysis = async (videoId: string) => {
+  const token = localStorage.getItem('authToken');
+  if (!token) throw new Error('로그인이 필요합니다');
+
+  const res = await fetch(`${SERVER_URL}/analysis/${videoId}`, {
+    method: 'GET',
+    headers: {
+      'Authorization': `Bearer ${token}`,
+    },
+  });

+  if (!res.ok) throw new Error('저장된 분석 데이터를 불러올 수 없습니다');
+  return await res.json();
+};
+
+/**
+ * 분석 데이터 존재 여부 확인
+ * @param videoId 유튜브 영상 ID
+ * @returns 분석 데이터 존재 여부
+ */
+export const checkSavedAnalysis = async (videoId: string): Promise<boolean> => {
+  const token = localStorage.getItem('authToken');
+  if (!token) return false;
+
+  try {
+    const res = await fetch(`${SERVER_URL}/analysis/${videoId}/exists`, {
+      method: 'GET',
+      headers: {
+        'Authorization': `Bearer ${token}`,
+      },
+    });
+    
+    if (res.ok) {
+      const data = await res.json();
+      return data.exists;
+    }
+    return false;
+  } catch (error) {
+    return false;
+  }
+};