import React, { useState, useEffect } from 'react';
import { 
  Container, 
  Typography, 
  Card, 
  CardContent, 
  Box, 
  Chip, 
  Table, 
  TableBody, 
  TableCell, 
  TableContainer, 
  TableHead, 
  TableRow, 
  Paper, 
  CircularProgress,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  useTheme,
  Tooltip,
  IconButton
} from '@mui/material';
import { useApi } from '../../hooks/useApi';
import ErrorFormatter from '../shared/ErrorFormatter';
import BarChartIcon from '@mui/icons-material/BarChart';
import VisibilityIcon from '@mui/icons-material/Visibility';
import CloseIcon from '@mui/icons-material/Close';

const Stats: React.FC = () => {
  const api = useApi();
  const theme = useTheme();
  const [attempts, setAttempts] = useState<any[]>([]);
  const [questions, setQuestions] = useState<Record<string, any>>({});
  const [selectedAttempt, setSelectedAttempt] = useState<any>(null);
  const [errorStats, setErrorStats] = useState<Record<string, number>>({});
  const [loading, setLoading] = useState(true);
  const [openDetails, setOpenDetails] = useState(false);
  
  // 获取所有练习记录
  useEffect(() => {
    const fetchData = async () => {
      try {
        const [attemptsData, questionsData] = await Promise.all([
          api.get('/attempts/all_history'),
          api.get('/questions/get')
        ]);
        
        if (attemptsData) {
          setAttempts(attemptsData);
          
          // 计算错误类型统计
          const errors: Record<string, number> = {};
          attemptsData.forEach((a: any) => {
            if (!a.is_correct && a.error_type) {
              errors[a.error_type] = (errors[a.error_type] || 0) + 1;
            }
          });
          setErrorStats(errors);
        }
        
        if (questionsData) {
          const questionsMap = questionsData.reduce((acc: Record<string, any>, q: any) => {
            acc[q.question_id] = q;
            return acc;
          }, {});
          setQuestions(questionsMap);
        }
        
      } catch (err) {
        console.error("获取数据失败:", err);
      } finally {
        setLoading(false);
      }
    };
    
    fetchData();
  }, []);
  
  // 计算统计信息
  const totalAttempts = attempts.length;
  const correctCount = attempts.filter(a => a.is_correct).length;
  const accuracy = totalAttempts > 0 
    ? Math.round((correctCount / totalAttempts) * 100) 
    : 0;
  
  const viewAttemptDetails = (attempt: any) => {
    setSelectedAttempt(attempt);
    setOpenDetails(true);
  };
  
  const handleCloseDetails = () => {
    setOpenDetails(false);
  };
  
  if (loading) {
    return (
      <Container maxWidth="xl" sx={{ display: 'flex', justifyContent: 'center', py: 10 }}>
        <CircularProgress />
      </Container>
    );
  }
  
  return (
    <Container maxWidth="xl">
      <Box display="flex" alignItems="center" mb={3}>
        <BarChartIcon fontSize="large" color="primary" sx={{ mr: 1 }} />
        <Typography variant="h5">学生练习情况分析</Typography>
      </Box>
      
      {/* 统计卡片 */}
      <Box sx={{ 
        display: 'flex', 
        flexWrap: 'wrap', 
        gap: 3, 
        mb: 4,
        '& > *': {
          flex: '1 1 300px'
        }
      }}>
        <Card elevation={3}>
          <CardContent>
            <Typography variant="body2" color="textSecondary" gutterBottom>
              总练习次数
            </Typography>
            <Typography variant="h4" fontWeight="bold">
              {totalAttempts}
            </Typography>
          </CardContent>
        </Card>
        
        <Card elevation={3}>
          <CardContent>
            <Typography variant="body2" color="textSecondary" gutterBottom>
              正确率
            </Typography>
            <Typography variant="h4" fontWeight="bold">
              {accuracy}%
            </Typography>
          </CardContent>
        </Card>
        
        <Card elevation={3}>
          <CardContent>
            <Typography variant="body2" color="textSecondary" gutterBottom>
              错误类型数
            </Typography>
            <Typography variant="h4" fontWeight="bold">
              {Object.keys(errorStats).length}
            </Typography>
          </CardContent>
        </Card>
      </Box>
      
      {/* 错误类型分布 */}
      {Object.keys(errorStats).length > 0 && (
        <Card sx={{ mb: 4 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              错误类型分布
            </Typography>
            <Box sx={{ 
              display: 'flex', 
              flexWrap: 'wrap', 
              gap: 2 
            }}>
              {Object.entries(errorStats).map(([type, count]) => (
                <Card variant="outlined" key={type} sx={{ flex: '1 1 200px' }}>
                  <CardContent>
                    <Typography variant="body1">{type}</Typography>
                    <Typography variant="h5" color="error">
                      {count}
                      <Typography variant="body2" component="span" color="textSecondary">
                        次错误
                      </Typography>
                    </Typography>
                  </CardContent>
                </Card>
              ))}
            </Box>
          </CardContent>
        </Card>
      )}
      
      {/* 详细记录 */}
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            练习记录详情
          </Typography>
          
          {attempts.length > 0 ? (
            <TableContainer component={Paper} sx={{ maxHeight: 600 }}>
              <Table stickyHeader>
                <TableHead>
                  <TableRow>
                    <TableCell>学生</TableCell>
                    <TableCell>题目</TableCell>
                    <TableCell>提交SQL</TableCell>
                    <TableCell>结果</TableCell>
                    <TableCell>提交时间</TableCell>
                    <TableCell>操作</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {attempts.map(attempt => (
                    <TableRow key={attempt.attempt_id} hover>
                      <TableCell>{attempt.username}</TableCell>
                      <TableCell>
                        {questions[attempt.question_id]?.question_title || '未知题目'}
                      </TableCell>
                      <TableCell sx={{ maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis' }}>
                        <Tooltip title={attempt.student_sql} placement="top">
                          <Box component="span" sx={{ fontFamily: 'monospace' }}>
                            {attempt.student_sql}
                          </Box>
                        </Tooltip>
                      </TableCell>
                      <TableCell>
                        <Chip 
                          label={attempt.is_correct ? '✓ 正确' : '✗ 错误'}
                          color={attempt.is_correct ? 'success' : 'error'}
                        />
                      </TableCell>
                      <TableCell>
                        {new Date(attempt.submitted_at).toLocaleDateString()}
                      </TableCell>
                      <TableCell>
                        <Button
                          variant="outlined"
                          startIcon={<VisibilityIcon />}
                          size="small"
                          onClick={() => viewAttemptDetails(attempt)}
                        >
                          详情
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          ) : (
            <Box textAlign="center" py={4}>
              <Typography variant="body1" color="textSecondary">
                暂无练习记录
              </Typography>
            </Box>
          )}
        </CardContent>
      </Card>
      
      {/* 详情对话框 */}
      <Dialog
        open={openDetails}
        onClose={handleCloseDetails}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          练习详情
          <IconButton
            aria-label="close"
            onClick={handleCloseDetails}
            sx={{
              position: 'absolute',
              right: 8,
              top: 8,
              color: theme.palette.grey[500],
            }}
          >
            <CloseIcon />
          </IconButton>
        </DialogTitle>
        <DialogContent dividers>
          {selectedAttempt && (
            <>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2, mb: 2 }}>
                <Box sx={{ flex: '1 1 300px' }}>
                  <Typography variant="subtitle1">
                    <strong>学生:</strong> {selectedAttempt.username}
                  </Typography>
                </Box>
                <Box sx={{ flex: '1 1 300px' }}>
                  <Typography variant="subtitle1">
                    <strong>提交时间:</strong> {new Date(selectedAttempt.submitted_at).toLocaleString()}
                  </Typography>
                </Box>
              </Box>
              
              <Box sx={{ mb: 2 }}>
                <Typography variant="subtitle1" gutterBottom>
                  <strong>题目:</strong> {questions[selectedAttempt.question_id]?.question_title || '未知题目'}
                </Typography>
              </Box>
              
              <Box sx={{ mb: 2 }}>
                <Typography variant="h6" gutterBottom>
                  提交的SQL
                </Typography>
                <Box
                  component="pre"
                  sx={{
                    backgroundColor: theme.palette.grey[100],
                    p: 2,
                    borderRadius: 1,
                    overflowX: 'auto',
                    fontFamily: 'monospace'
                  }}
                >
                  {selectedAttempt.student_sql}
                </Box>
              </Box>
              
              {!selectedAttempt.is_correct && selectedAttempt.detailed_errors?.[0] && (
                <Box sx={{ mb: 2 }}>
                  <Typography variant="h6" gutterBottom>
                    错误分析
                  </Typography>
                  <ErrorFormatter error={selectedAttempt.detailed_errors[0]} />
                </Box>
              )}
              
              <Box>
                <Typography variant="h6" gutterBottom>
                  题目详情
                </Typography>
                <Typography variant="body1" gutterBottom>
                  {questions[selectedAttempt.question_id]?.description || '无描述'}
                </Typography>
                
                <Typography variant="subtitle1" mt={2}>
                  参考答案:
                </Typography>
                <Box
                  component="pre"
                  sx={{
                    backgroundColor: theme.palette.success.light,
                    p: 2,
                    borderRadius: 1,
                    overflowX: 'auto',
                    fontFamily: 'monospace',
                    color: 'white'
                  }}
                >
                  {questions[selectedAttempt.question_id]?.answer_sql || '无参考答案'}
                </Box>
              </Box>
            </>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDetails} variant="outlined">
            关闭
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default Stats;