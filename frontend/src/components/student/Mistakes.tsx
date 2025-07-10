import React, { useState } from 'react';
import { 
  Box, Typography, Card, CardContent, Collapse, 
  Dialog, DialogTitle, DialogContent, DialogActions,
  IconButton, useTheme, Alert,
  Button, CircularProgress // 添加CircularProgress组件
} from '@mui/material';
import { useApi } from '../../hooks/useApi';
import SchemaViewer from '../shared/SchemaViewer';
import ErrorFormatter from '../shared/ErrorFormatter';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';
import CloseIcon from '@mui/icons-material/Close';


interface Question {
  question_id: string;
  question_title: string;
  description: string;
  schema_id: string;
}

const Mistakes: React.FC = () => {
  const api = useApi();
  const theme = useTheme();
  const [questions, setQuestions] = useState<Question[]>([]);
  const [expandedQuestion, setExpandedQuestion] = useState<string | null>(null);
  const [schemas, setSchemas] = useState<Record<string, any>>({});
  const [attempts, setAttempts] = useState<Record<string, any[]>>({});
  const [openSchemaDialog, setOpenSchemaDialog] = useState(false);
  const [selectedSchema, setSelectedSchema] = useState<any>(null);
  const [loadingAttempts, setLoadingAttempts] = useState<Record<string, boolean>>({});

  // 获取错题本
  React.useEffect(() => {
    const fetchMistakes = async () => {
      try {
        const data = await api.get('/attempts/mistakes');
        if (data) {
          const normalizedQuestions = data.map((q: any) => ({
            question_id: q.question_id,
            question_title: q.question_title || `未命名题目#${q.question_id.slice(0, 4)}`,
            description: q.description,
            schema_id: q.schema_id
          }));
          setQuestions(normalizedQuestions);
          
          const schemaIds = Array.from(
            new Set(normalizedQuestions.map((q: any) => q.schema_id))
          );
          
          const schemaPromises = schemaIds.map(id => api.get(`/sample-schemas/get/${id}`));
          const schemaResults = await Promise.all(schemaPromises);
          
          setSchemas(schemaResults.reduce((acc, schema) => {
            if (schema) acc[schema.schema_id] = schema;
            return acc;
          }, {} as Record<string, any>));
        }
      } catch (error) {
        console.error("获取错题失败:", error);
      }
    };
    
    fetchMistakes();
  }, []);

  // 获取题目的尝试记录
  const fetchQuestionAttempts = async (questionId: string) => {
    setLoadingAttempts(prev => ({ ...prev, [questionId]: true })); // 开始加载
    
    try {
      const data = await api.get(`/attempts/by_question/${questionId}`);
      if (data) {
        setAttempts(prev => ({
          ...prev,
          [questionId]: data.filter((a: any) => !a.is_correct)
        }));
      }
    } catch (error) {
      console.error(`获取题目${questionId}的尝试记录失败:`, error);
    } finally {
      setLoadingAttempts(prev => ({ ...prev, [questionId]: false })); // 结束加载
    }
  };

  const handleViewSchema = (schema: any) => {
    setSelectedSchema(schema);
    setOpenSchemaDialog(true);
  };

  return (
    <Box sx={{ p: 3, display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
      <Typography variant="h5" gutterBottom sx={{ mb: 3 }}>
        错题本
      </Typography>
      
      <Box sx={{ width: '100%', maxWidth: 800, display: 'flex', flexDirection: 'column', gap: 2 }}>
        {questions.length === 0 ? (
          <Alert severity="info" sx={{ mb: 2, width: '100%' }}>
            暂无错题记录
          </Alert>
        ) : (
          questions.map(question => (
            <Card 
              key={question.question_id} 
              variant="outlined"
              sx={{ boxShadow: 1 }}
            >
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Typography 
                    variant="subtitle1" 
                    sx={{ fontWeight: 500, maxWidth: '70%' }}
                  >
                    {question.question_id}: {question.question_title} {/* 使用question_title */}
                  </Typography>
                  <IconButton 
                    onClick={() => {
                      if (expandedQuestion === question.question_id) {
                        setExpandedQuestion(null);
                      } else {
                        setExpandedQuestion(question.question_id);
                        if (!attempts[question.question_id]) {
                          fetchQuestionAttempts(question.question_id);
                        }
                      }
                    }}
                    size="small"
                  >
                    {expandedQuestion === question.question_id ? 
                      <ExpandLessIcon /> : <ExpandMoreIcon />}
                  </IconButton>
                </Box>
                
                <Collapse in={expandedQuestion === question.question_id}>
                  <Box sx={{ mt: 2 }}>
                    <Typography variant="subtitle2" gutterBottom>
                      题目描述:
                    </Typography>
                    <Typography variant="body2" sx={{ mb: 2 }}>
                      {question.description}
                    </Typography>
                    
                    <Button 
                      variant="outlined" 
                      size="small"
                      onClick={() => handleViewSchema(schemas[question.schema_id])}
                      sx={{ mb: 2 }}
                    >
                      查看数据库模式
                    </Button>
                    
                    <Typography variant="subtitle2" gutterBottom>
                      错误尝试记录:
                    </Typography>
                    
                    {loadingAttempts[question.question_id] ? (
                      <Box sx={{ display: 'flex', justifyContent: 'center', py: 2 }}>
                        <CircularProgress size={24} />
                      </Box>
                    ) : attempts[question.question_id]?.length > 0 ? (
                      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
                        {attempts[question.question_id].map(attempt => (
                          <Card 
                            key={attempt.attempt_id} 
                            variant="outlined"
                            sx={{ backgroundColor: theme.palette.error.light }}
                          >
                            <CardContent>
                              <Typography variant="caption" color="textSecondary">
                                {new Date(attempt.submitted_at).toLocaleString()}
                              </Typography>
                              <Box 
                                component="pre" 
                                sx={{ 
                                  backgroundColor: theme.palette.grey[100], 
                                  p: 1.5, 
                                  borderRadius: 1,
                                  overflowX: 'auto',
                                  fontFamily: 'monospace',
                                  fontSize: '0.875rem',
                                  mt: 1
                                }}
                              >
                                {attempt.student_sql}
                              </Box>
                              <Box sx={{ mt: 1.5 }}>
                                <Typography variant="subtitle2" gutterBottom>
                                  错误分析:
                                </Typography>
                                <ErrorFormatter error={attempt.detailed_errors?.[0]} />
                              </Box>
                            </CardContent>
                          </Card>
                        ))}
                      </Box>
                    ) : (
                      <Typography variant="body2" color="textSecondary">
                        该题目暂无错误尝试记录
                      </Typography>
                    )}
                  </Box>
                </Collapse>
              </CardContent>
            </Card>
          ))
        )}
      </Box>
      
      {/* 数据库模式对话框 */}
      <Dialog
        open={openSchemaDialog}
        onClose={() => setOpenSchemaDialog(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          数据库模式
          <IconButton
            aria-label="close"
            onClick={() => setOpenSchemaDialog(false)}
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
          {selectedSchema && <SchemaViewer schema={selectedSchema?.schema_definition} />}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenSchemaDialog(false)} variant="outlined">
            关闭
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default Mistakes;