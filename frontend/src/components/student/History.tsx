import React, { useState } from 'react';
import { 
  Box, Typography, Card, CardContent, Collapse, 
  useTheme, IconButton, Alert
} from '@mui/material';
import { useApi } from '../../hooks/useApi';
import ErrorFormatter from '../shared/ErrorFormatter';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';

interface Attempt {
  attempt_id: string;
  question_id: string;
  student_sql: string;
  is_correct: boolean;
  error_type: string;
  detailed_errors: any[];
  submitted_at: string;
}


interface Question {
  question_id: string;
  question_title: string;
  description: string;
}

const History: React.FC = () => {
  const api = useApi();
  const theme = useTheme();
  const [attempts, setAttempts] = useState<Attempt[]>([]);
  const [questions, setQuestions] = useState<Record<string, Question>>({});
  const [expandedAttempt, setExpandedAttempt] = useState<string | null>(null);

  // 获取练习历史
  React.useEffect(() => {
    const fetchHistory = async () => {
      try {
        const data = await api.get('/attempts/history');
        if (data) {
          setAttempts(data);
          
          const questionIds = Array.from(
            new Set(data.map((a: any) => a.question_id))
          );
          
          if (questionIds.length > 0) {
            const qData = await api.post('/questions/get/batch', questionIds);
            
            const questionsMap = qData.reduce((acc: Record<string, Question>, q: Question) => {
              acc[q.question_id] = {
                question_id: q.question_id,
                question_title: q.question_title || `未命名题目#${q.question_id.slice(0, 4)}`,
                description: q.description
              };
              return acc;
            }, {});
            setQuestions(questionsMap);
          }
        }
      } catch (error) {
        console.error("获取练习历史失败:", error);
      }
    };
    
    fetchHistory();
  }, []);

  // 获取题目信息（带缓存）
  const getQuestionInfo = (questionId: string) => {
    return questions[questionId] || {
      question_id: questionId,
      question_title: `题目#${questionId.slice(0, 4)}`,
      description: '题目信息加载中...'
    };
  };

  return (
    <Box sx={{ p: 3, display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
      <Typography variant="h5" gutterBottom sx={{ mb: 3 }}>
        练习历史
      </Typography>
      
      <Box sx={{ width: '100%', maxWidth: 800, display: 'flex', flexDirection: 'column', gap: 2 }}>
        {attempts.length === 0 ? (
          <Alert severity="info" sx={{ mb: 2, width: '100%' }}>
            暂无练习记录
          </Alert>
        ) : (
          attempts.map(attempt => {
            const questionInfo = getQuestionInfo(attempt.question_id);
            
            return (
              <Card 
                key={attempt.attempt_id} 
                variant="outlined"
                sx={{ boxShadow: 1 }}
              >
                <CardContent>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Box sx={{ maxWidth: '70%' }}>
                      {/* 修复3：使用question_title字段 */}
                      <Typography variant="subtitle1" sx={{ fontWeight: 500 }}>
                        {questionInfo.question_id}: {questionInfo.question_title}
                      </Typography>
                      <Typography variant="body2" color="textSecondary">
                        {new Date(attempt.submitted_at).toLocaleString()}
                      </Typography>
                    </Box>
                    
                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                      <Alert 
                        severity={attempt.is_correct ? "success" : "error"}
                        sx={{ py: 0, px: 1.5 }}
                      >
                        {attempt.is_correct ? '✓ 正确' : '✗ 错误'}
                      </Alert>
                      <IconButton 
                        onClick={() => setExpandedAttempt(
                          expandedAttempt === attempt.attempt_id ? null : attempt.attempt_id
                        )}
                        size="small"
                      >
                        {expandedAttempt === attempt.attempt_id ? 
                          <ExpandLessIcon /> : <ExpandMoreIcon />}
                      </IconButton>
                    </Box>
                  </Box>
                  
                  <Collapse in={expandedAttempt === attempt.attempt_id}>
                    <Box sx={{ mt: 2 }}>
                      <Typography variant="subtitle2" gutterBottom>
                        题目描述:
                      </Typography>
                      <Typography variant="body2">
                        {questionInfo.description}
                      </Typography>
                      
                      <Typography variant="subtitle2" gutterBottom sx={{ mt: 2 }}>
                        你的SQL:
                      </Typography>
                      <Box 
                        component="pre" 
                        sx={{ 
                          backgroundColor: theme.palette.grey[100], 
                          p: 2, 
                          borderRadius: 1,
                          overflowX: 'auto',
                          fontFamily: 'monospace',
                          fontSize: '0.875rem'
                        }}
                      >
                        {attempt.student_sql}
                      </Box>
                      
                      {!attempt.is_correct && attempt.detailed_errors && (
                        <Box sx={{ mt: 2 }}>
                          <Typography variant="subtitle2" gutterBottom>
                            错误分析:
                          </Typography>
                          <ErrorFormatter error={attempt.detailed_errors[0]} />
                        </Box>
                      )}
                    </Box>
                  </Collapse>
                </CardContent>
              </Card>
            );
          })
        )}
      </Box>
    </Box>
  );
};

export default History;