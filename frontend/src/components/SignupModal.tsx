@@ .. @@
 import React, { useState } from 'react';
 import { X } from 'lucide-react';
+import { useAuth } from '../contexts/AuthContext';

 interface SignupModalProps {
@@ .. @@
 }

 const SignupModal: React.FC<SignupModalProps> = ({ isOpen, onClose, onSwitchToLogin }) => {
+  const { signup } = useAuth();
   const [formData, setFormData] = useState({
     email: '',
     password: '',
@@ .. @@
     setLoading(true);
     
     try {
-      // TODO: 회원가입 API 호출
-      console.log('회원가입 시도:', formData);
-      // 임시로 성공 처리
-      alert('회원가입 성공!');
-      onClose();
+      const success = await signup(formData.email, formData.password, formData.nickname);
+      if (success) {
+        alert('회원가입이 완료되었습니다. 로그인해주세요.');
+        onSwitchToLogin();
+      } else {
+        alert('회원가입에 실패했습니다. 다시 시도해주세요.');
+      }
     } catch (error) {
       console.error('회원가입 실패:', error);
       alert('회원가입에 실패했습니다.');