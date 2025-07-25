@@ .. @@
 import React, { useState } from 'react';
+import { useAuth } from '../contexts/AuthContext';
 import LoginModal from './LoginModal';
 import SignupModal from './SignupModal';

 const LoginButton: React.FC = () => {
+  const { user, logout, isAuthenticated } = useAuth();
   const [showLoginModal, setShowLoginModal] = useState(false);
   const [showSignupModal, setShowSignupModal] = useState(false);

@@ .. @@
     setShowLoginModal(true);
   };

+  const handleLogout = () => {
+    logout();
+  };
+
   const handleCloseModals = () => {
@@ .. @@
     setShowSignupModal(true);
   };

@@ .. @@
     setShowLoginModal(true);
   };

+  if (isAuthenticated && user) {
+    return (
+      <div className="flex items-center gap-3">
+        <span className="text-black font-medium">{user.nickname}님</span>
+        <button
+          onClick={handleLogout}
+          className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 transition-colors duration-200 font-medium"
+        >
+          로그아웃
+        </button>
+      </div>
+    );
+  }
+
   return (
     <>
       <button