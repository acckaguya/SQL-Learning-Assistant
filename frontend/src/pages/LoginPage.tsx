import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { 
  Box, 
  TextField, 
  Button, 
  Typography, 
  Tabs, 
  Tab, 
  Paper, 
  Alert,
  FormControl,
  InputLabel,
  MenuItem,
  Select,
  SelectChangeEvent
} from '@mui/material';
import { useNavigate } from 'react-router-dom';

const LoginPage = () => {
  const { login, register, loading } = useAuth();
  const navigate = useNavigate();
  

  const [activeTab, setActiveTab] = useState(0);
  const [error, setError] = useState<string | null>(null);
  
  // 登录表单状态
  const [loginData, setLoginData] = useState({
    username: '',
    password: ''
  });
  
  // 注册表单状态
  const [registerData, setRegisterData] = useState({ 
    username: '', 
    password: '', 
    confirmPassword: '',
    role: 'student'
  });

  const handleLogin = async () => {
    setError(null);
    try {
      await login(loginData.username, loginData.password);
      navigate('/');
    } catch (error: any) {
      setError(error.message || '登录失败');
    }
  };

  const handleRegister = async () => {
    setError(null);
    if (registerData.password !== registerData.confirmPassword) {
      setError('两次输入的密码不一致');
      return;
    }
    try {
      await register(registerData.username, registerData.password, registerData.role);
      navigate('/');
    } catch (error: any) {
      setError(error.message || '注册失败');
    }
  };

  // 处理登录表单变更
  const handleLoginChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setLoginData(prev => ({ ...prev, [name]: value }));
  };

  // 处理注册表单变更
  const handleRegisterChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setRegisterData(prev => ({ ...prev, [name]: value }));
  };

  // 处理角色选择变更
  const handleRoleChange = (e: SelectChangeEvent<string>) => {
    setRegisterData(prev => ({
      ...prev,
      role: e.target.value as 'student' | 'teacher'
    }));
  };

  return (
    <Box sx={{ maxWidth: 500, margin: 'auto', mt: 5 }}>
      <Paper elevation={3} sx={{ p: 3 }}>
        <Tabs value={activeTab} onChange={(_, newValue) => setActiveTab(newValue)}>
          <Tab label="登录" />
          <Tab label="注册" />
        </Tabs>
        
        {error && <Alert severity="error" sx={{ mt: 2 }}>{error}</Alert>}

        {/* 登录表单 */}
        {activeTab === 0 && (
          <Box sx={{ mt: 2 }}>
            <Typography variant="h5" gutterBottom>SQL学习平台</Typography>
            
            <TextField
              label="用户名"
              name="username"
              fullWidth
              margin="normal"
              value={loginData.username}
              onChange={handleLoginChange}
            />
            
            <TextField
              label="密码"
              name="password"
              type="password"
              fullWidth
              margin="normal"
              value={loginData.password}
              onChange={handleLoginChange}
            />
            
            <Button 
              variant="contained" 
              fullWidth 
              sx={{ mt: 2 }}
              onClick={handleLogin}
              disabled={loading}
            >
              {loading ? '登录中...' : '登录'}
            </Button>
          </Box>
        )}
        
        {/* 注册表单 */}
        {activeTab === 1 && (
          <Box sx={{ mt: 2 }}>
            <Typography variant="h5" gutterBottom>创建账户</Typography>
            
            {/* 用户名 */}
            <TextField
              label="用户名"
              name="username"
              fullWidth
              margin="normal"
              value={registerData.username}
              onChange={handleRegisterChange}
            />
            
            {/* 密码 */}
            <TextField
              label="密码"
              name="password"
              type="password"
              fullWidth
              margin="normal"
              value={registerData.password}
              onChange={handleRegisterChange}
            />
            
            {/* 确认密码 */}
            <TextField
              label="确认密码"
              name="confirmPassword"
              type="password"
              fullWidth
              margin="normal"
              value={registerData.confirmPassword}
              onChange={handleRegisterChange}
            />
            
            {/* 角色选择器 */}
            <FormControl fullWidth margin="normal">
              <InputLabel>账户类型</InputLabel>
              <Select
                value={registerData.role}
                label="账户类型"
                onChange={handleRoleChange}
              >
                <MenuItem value="student">学生账户</MenuItem>
                <MenuItem value="teacher">教师账户</MenuItem>
              </Select>
            </FormControl>

            {/* 注册按钮 */}
            <Button 
              variant="contained" 
              fullWidth 
              sx={{ mt: 2 }}
              onClick={handleRegister}
              disabled={loading}
            >
              {loading ? '注册中...' : '完成注册'}
            </Button>
          </Box>
        )}
      </Paper>
    </Box>
  );
};

export default LoginPage;