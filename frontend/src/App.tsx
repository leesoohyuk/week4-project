@@ .. @@
 import React from 'react';
 import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
+import { AuthProvider } from './contexts/AuthContext';
 import HomePage from './pages/HomePage';
 import SearchPage from './pages/SearchPage';
 import SongDetailPage from './pages/SongDetailPage';

 function App() {
   return (
-    <Router>
-      <div className="App">
-        <Routes>
-          <Route path="/" element={<HomePage />} />
-          <Route path="/search" element={<SearchPage />} />
-          <Route path="/song/:videoId" element={<SongDetailPage />} />
-          <Route path="*" element={<Navigate to="/" replace />} />
-        </Routes>
-      </div>
-    </Router>
+    <AuthProvider>
+      <Router>
+        <div className="App">
+          <Routes>
+            <Route path="/" element={<HomePage />} />
+            <Route path="/search" element={<SearchPage />} />
+            <Route path="/song/:videoId" element={<SongDetailPage />} />
+            <Route path="*" element={<Navigate to="/" replace />} />
+          </Routes>
+        </div>
+      </Router>
+    </AuthProvider>
   );
 }