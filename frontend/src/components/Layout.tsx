import React from 'react';
import { useAuth } from '../contexts/AuthContext';
import { Navigate } from 'react-router-dom';

const Layout = () => {
  const { user } = useAuth();

  if (!user) {
    return <Navigate to="/login" />;
  }

  // 根据用户角色重定向
  return (
    <Navigate to={user.role === 'teacher' ? '/teacher' : '/student'} />
  );
};

export default Layout;