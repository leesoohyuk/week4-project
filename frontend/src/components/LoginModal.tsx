@@ .. @@
 import React, { useState } from 'react';
 import { X } from 'lucide-react';
+import { useAuth } from '../contexts/AuthContext';

 interface LoginModalProps {
@@ .. @@
 }

 const LoginModal: React.FC<LoginModalProps> = ({ isOpen, onClose, onSwitchToSignup }) => {
+  const { login } = useAuth();
   const [formData, setFormData] = useState({
-    username: '',
+    email: '',
     password: ''
   });
@@ .. @@
     setLoading(true);
     
     try {
-      // TODO: 로그인 API 호출
-      console.log('로그인 시도:', formData);
-      // 임시로 성공 처리
-      alert('로그인 성공!');
-      onClose();
+      const success = await login(formData.email, formData.password);
+      if (success) {
+        onClose();
+      } else {
+        alert('로그인에 실패했습니다. 이메일과 비밀번호를 확인해주세요.');
+      }
     } catch (error) {
       console.error('로그인 실패:', error);
       alert('로그인에 실패했습니다.');
@@ .. @@
           <div>
             <div className="relative">
-              <span className="absolute left-3 top-3 text-gray-600 text-sm">👤</span>
+              <span className="absolute left-3 top-3 text-gray-600 text-sm">📧</span>
               <input
-                type="text"
-                name="username"
-                placeholder="Username"
-                value={formData.username}
+                type="email"
+                name="email"
+                placeholder="Email"
+                value={formData.email}
                 onChange={handleChange}
                 className="w-full pl-10 pr-4 py-3 bg-white border-0 rounded-md text-gray-800 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
                 required