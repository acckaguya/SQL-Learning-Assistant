import React, { useState } from 'react';
import { 
  AppBar, 
  Toolbar, 
  Typography, 
  Button, 
  Container, 
  Tabs, 
  Tab, 
  Box, 
  Paper,
  IconButton
} from '@mui/material';
import { useAuth } from '../contexts/AuthContext';
import QuestionManagement from '../components/teacher/QuestionManagement';
import SchemaManagement from '../components/teacher/SchemaManagement';
import Stats from '../components/teacher/Stats';
import AccountCircleIcon from '@mui/icons-material/AccountCircle';
import ExitToAppIcon from '@mui/icons-material/ExitToApp';
import MenuIcon from '@mui/icons-material/Menu';
import { useTheme, useMediaQuery } from '@mui/material';

const TeacherDashboard: React.FC = () => {
  const { user, logout } = useAuth();
  const [activeTab, setActiveTab] = useState('questions');
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  if (!user) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="100vh">
        <Typography variant="h5" color="error">
          请先登录
        </Typography>
      </Box>
    );
  }

  const handleTabChange = (event: React.SyntheticEvent, newValue: string) => {
    setActiveTab(newValue);
    if (isMobile) {
      setMobileMenuOpen(false);
    }
  };

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      {/* 顶部应用栏 */}
      <AppBar position="static" color="primary" elevation={1}>
        <Toolbar>
          {isMobile && (
            <IconButton
              size="large"
              edge="start"
              color="inherit"
              aria-label="menu"
              sx={{ mr: 2 }}
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            >
              <MenuIcon />
            </IconButton>
          )}
          
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            SQL智能练习平台 - 教师端
          </Typography>
          
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <AccountCircleIcon sx={{ mr: 1 }} />
            <Typography variant="subtitle1" sx={{ mr: 2 }}>
              欢迎, {user.username}
            </Typography>
            <Button 
              variant="outlined" 
              color="inherit"
              startIcon={<ExitToAppIcon />}
              onClick={logout}
              sx={{ 
                borderColor: 'rgba(255, 255, 255, 0.5)',
                '&:hover': {
                  backgroundColor: 'rgba(255, 255, 255, 0.1)'
                }
              }}
            >
              退出
            </Button>
          </Box>
        </Toolbar>
      </AppBar>

      {/* 主内容区域 */}
      <Container maxWidth="xl" sx={{ py: 4, flexGrow: 1 }}>
        <Box sx={{ display: 'flex', flexDirection: { xs: 'column', sm: 'row' }, gap: 3 }}>
          {/* 导航标签 - 桌面视图 */}
          {!isMobile && (
            <Paper sx={{ width: 220, height: 'fit-content', borderRadius: 2 }}>
              <Tabs
                orientation="vertical"
                variant="scrollable"
                value={activeTab}
                onChange={handleTabChange}
                aria-label="教师仪表盘导航"
                sx={{ borderRight: 1, borderColor: 'divider' }}
              >
                <Tab 
                  label="题库管理" 
                  value="questions" 
                  sx={{ 
                    alignItems: 'flex-start',
                    justifyContent: 'flex-start',
                    textTransform: 'none',
                    fontSize: '1rem',
                    '&.Mui-selected': {
                      backgroundColor: theme.palette.action.selected,
                    }
                  }}
                />
                <Tab 
                  label="样例数据库" 
                  value="schemas" 
                  sx={{ 
                    alignItems: 'flex-start',
                    justifyContent: 'flex-start',
                    textTransform: 'none',
                    fontSize: '1rem',
                    '&.Mui-selected': {
                      backgroundColor: theme.palette.action.selected,
                    }
                  }}
                />
                <Tab 
                  label="学生练习情况" 
                  value="stats" 
                  sx={{ 
                    alignItems: 'flex-start',
                    justifyContent: 'flex-start',
                    textTransform: 'none',
                    fontSize: '1rem',
                    '&.Mui-selected': {
                      backgroundColor: theme.palette.action.selected,
                    }
                  }}
                />
              </Tabs>
            </Paper>
          )}

          {/* 移动端导航菜单 */}
          {isMobile && mobileMenuOpen && (
            <Paper sx={{ mb: 2, borderRadius: 2 }}>
              <Tabs
                orientation="vertical"
                variant="fullWidth"
                value={activeTab}
                onChange={handleTabChange}
                aria-label="教师仪表盘导航"
              >
                <Tab 
                  label="题库管理" 
                  value="questions" 
                  sx={{ 
                    textTransform: 'none',
                    fontSize: '1rem',
                    '&.Mui-selected': {
                      backgroundColor: theme.palette.action.selected,
                    }
                  }}
                />
                <Tab 
                  label="样例数据库" 
                  value="schemas" 
                  sx={{ 
                    textTransform: 'none',
                    fontSize: '1rem',
                    '&.Mui-selected': {
                      backgroundColor: theme.palette.action.selected,
                    }
                  }}
                />
                <Tab 
                  label="学生练习情况" 
                  value="stats" 
                  sx={{ 
                    textTransform: 'none',
                    fontSize: '1rem',
                    '&.Mui-selected': {
                      backgroundColor: theme.palette.action.selected,
                    }
                  }}
                />
              </Tabs>
            </Paper>
          )}

          {/* 内容区域 */}
          <Box sx={{ flexGrow: 1 }}>
            {/* 移动端标签栏 */}
            {isMobile && (
              <Paper sx={{ mb: 3, borderRadius: 2 }}>
                <Tabs
                  value={activeTab}
                  onChange={handleTabChange}
                  variant="fullWidth"
                  aria-label="教师仪表盘导航"
                >
                  <Tab 
                    label="题库" 
                    value="questions" 
                    sx={{ textTransform: 'none', fontSize: '0.875rem' }} 
                  />
                  <Tab 
                    label="数据库" 
                    value="schemas" 
                    sx={{ textTransform: 'none', fontSize: '0.875rem' }} 
                  />
                  <Tab 
                    label="练习情况" 
                    value="stats" 
                    sx={{ textTransform: 'none', fontSize: '0.875rem' }} 
                  />
                </Tabs>
              </Paper>
            )}

            <Paper 
              elevation={3} 
              sx={{ 
                borderRadius: 2, 
                overflow: 'hidden',
                minHeight: 500,
                p: { xs: 2, md: 3 }
              }}
            >
              {activeTab === 'questions' && <QuestionManagement />}
              {activeTab === 'schemas' && <SchemaManagement />}
              {activeTab === 'stats' && <Stats />}
            </Paper>
          </Box>
        </Box>
      </Container>

      {/* 页脚 */}
      <Box component="footer" sx={{ py: 3, backgroundColor: theme.palette.grey[100] }}>
        <Container maxWidth="lg">
          <Typography variant="body2" color="text.secondary" align="center">
            © {new Date().getFullYear()} SQL智能练习平台 - 教师端
          </Typography>
        </Container>
      </Box>
    </Box>
  );
};

export default TeacherDashboard;