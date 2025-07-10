import React, { useState, useEffect, useMemo } from 'react';
import { 
  Box, Typography, Card, CardContent, Button, TextField, 
  Select, MenuItem, Dialog, DialogTitle, DialogContent,
  DialogActions, CircularProgress, Alert, useTheme, IconButton,
  List, ListItem, ListItemText, Divider,
  ListItemButton, Chip, FormControlLabel, Checkbox
} from '@mui/material';
import { useApi } from '../../hooks/useApi';
import SchemaViewer from '../shared/SchemaViewer';
import ErrorFormatter from '../shared/ErrorFormatter';
import CloseIcon from '@mui/icons-material/Close';

// 知识点常量定义
const KNOWLEDGE_POINTS = [
  { id: 'basic_query', label: '基础查询' },
  { id: 'where_clause', label: '条件查询' },
  { id: 'aggregation', label: '聚合函数' },
  { id: 'group_by', label: '分组查询' },
  { id: 'order_by', label: '排序查询' },
  { id: 'limit_clause', label: '分页查询' },
  { id: 'joins', label: '多表连接' },
  { id: 'subqueries', label: '子查询' },
  { id: 'null_handling', label: 'NULL处理' },
  { id: 'execution_order', label: '执行顺序' },
];


interface Question {
  question_id: string;
  question_title: string;
  description: string;
  schema_id: string;
  order_sensitive: boolean;
  // 知识点字段
  basic_query: boolean;
  where_clause: boolean;
  aggregation: boolean;
  group_by: boolean;
  order_by: boolean;
  limit_clause: boolean;
  joins: boolean;
  subqueries: boolean;
  null_handling: boolean;
  execution_order: boolean;
}

const Practice: React.FC = () => {
  const api = useApi();
  const theme = useTheme();
  const [questions, setQuestions] = useState<Question[]>([]);
  const [selectedQuestion, setSelectedQuestion] = useState<Question | null>(null);
  const [schema, setSchema] = useState<any>(null);
  const [sql, setSql] = useState('');
  const [result, setResult] = useState<any>(null);
  const [analysis, setAnalysis] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [openSchemaDialog, setOpenSchemaDialog] = useState(false);
  const [isLoadingQuestions, setIsLoadingQuestions] = useState(true);
  
  // 知识点选择状态
  const [knowledgePointsState, setKnowledgePointsState] = useState<Record<string, boolean>>(() => {
    const initialState: Record<string, boolean> = {};
    KNOWLEDGE_POINTS.forEach(point => {
      initialState[point.id] = false;
    });
    return initialState;
  });

  // 获取题目列表 - 添加正确的类型处理
  useEffect(() => {
    const fetchQuestions = async () => {
      setIsLoadingQuestions(true);
      try {
        const data: Question[] = await api.get('/questions/get');
        if (data) {
          setQuestions(data);
        }
      } catch (error) {
        console.error("题目加载失败:", error);
      } finally {
        setIsLoadingQuestions(false);
      }
    };
    fetchQuestions();
  }, []);

  // 根据知识点状态过滤题目
  const filteredQuestions = useMemo(() => {
    const selectedPoints = Object.keys(knowledgePointsState)
      .filter(k => knowledgePointsState[k]);
    
    if (selectedPoints.length === 0) return questions;
    
    return questions.filter(q => {
      // 检查题目是否包含任何选中的知识点
      return selectedPoints.some(point => q[point as keyof Question] === true);
    });
  }, [questions, knowledgePointsState]);

  // 获取选中的题目详情
  useEffect(() => {
    if (!selectedQuestion) return;
    const fetchSchema = async () => {
      const data = await api.get(`/sample-schemas/get/${selectedQuestion.schema_id}`);
      setSchema(data);
    };
    fetchSchema();
  }, [selectedQuestion]);

  // 将题目知识点转换为标签数组
  const getKnowledgePointsForQuestion = (q: Question): string[] => {
    return KNOWLEDGE_POINTS
      .filter(point => q[point.id as keyof Question] === true)
      .map(point => point.label);
  };

  const handleSubmit = async () => {
    if (!selectedQuestion || !sql.trim()) return;
    
    setLoading(true);
    try {
      const attempt = await api.post('/attempts/submit', {
        student_sql: sql,
        question_id: selectedQuestion.question_id
      });
      
      setResult(attempt);
      const analysisData = await api.post('/analyze/sql', attempt);
      setAnalysis(analysisData);
    } catch (error) {
      console.error('提交失败', error);
    } finally {
      setLoading(false);
    }
  };

  // 知识点选择处理
  const handleKnowledgePointChange = (id: string) => (e: React.ChangeEvent<HTMLInputElement>) => {
    setKnowledgePointsState(prev => ({
      ...prev,
      [id]: e.target.checked
    }));
  };

  return (
    <Box sx={{ p: 3, display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
      <Typography variant="h5" gutterBottom sx={{ mb: 3 }}>
        SQL练习
      </Typography>
      
      <Box sx={{ width: '100%', maxWidth: 800, display: 'flex', flexDirection: 'column', gap: 2 }}>
        {/* 知识点选择 */}
        <Card variant="outlined" sx={{ boxShadow: 1 }}>
          <CardContent>
            <Typography variant="subtitle1" gutterBottom>
              选择知识点
            </Typography>
            
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1.5 }}>
              {KNOWLEDGE_POINTS.map(point => (
                <FormControlLabel
                  key={point.id}
                  control={
                    <Checkbox
                      size="small"
                      checked={knowledgePointsState[point.id] || false}
                      onChange={handleKnowledgePointChange(point.id)}
                      color="primary"
                    />
                  }
                  label={point.label}
                />
              ))}
            </Box>
          </CardContent>
        </Card>

        {/* 题目选择 */}
        <Card variant="outlined" sx={{ boxShadow: 1 }}>
          <CardContent>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Typography variant="subtitle1" gutterBottom>
                选择题目
              </Typography>
              
              {/* 显示当前选中的知识点 */}
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                {Object.keys(knowledgePointsState)
                  .filter(k => knowledgePointsState[k])
                  .map(k => {
                    const point = KNOWLEDGE_POINTS.find(p => p.id === k);
                    return point ? (
                      <Chip 
                        key={k}
                        label={point.label}
                        size="small"
                        color="primary"
                        onDelete={() => handleKnowledgePointChange(k)({ target: { checked: false } } as any)}
                      />
                    ) : null;
                  })}
              </Box>
            </Box>
            
            {/* 加载状态显示 */}
            {isLoadingQuestions && (
              <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
                <CircularProgress size={24} />
                <Typography variant="body2" sx={{ ml: 2 }}>题目加载中...</Typography>
              </Box>
            )}
            
            {/* 题目列表 */}
            {!isLoadingQuestions && (
              <>
                <Typography variant="subtitle2" sx={{ mb: 1, color: 'text.secondary' }}>
                  {Object.keys(knowledgePointsState).some(k => knowledgePointsState[k])
                    ? `筛选后题目 (${filteredQuestions.length})`
                    : `全部题目 (${questions.length})`
                  }
                </Typography>
                
                {filteredQuestions.length > 0 ? (
                  <List sx={{ maxHeight: 300, overflow: 'auto' }}>
                    {filteredQuestions.map(q => (
                      <React.Fragment key={q.question_id}>
                        <ListItemButton 
                          selected={selectedQuestion?.question_id === q.question_id}
                          onClick={() => setSelectedQuestion(q)}
                        >
                          <ListItemText 
                            primary={`${q.question_id}: ${q.question_title}`} 
                            secondary={
                              <>
                                {q.description.substring(0, 50) + '...'}
                                <Box component="span" sx={{ ml: 1, color: 'primary.main' }}>
                                  ({getKnowledgePointsForQuestion(q).join(', ') || '未分类'})
                                </Box>
                              </>
                            } 
                          />
                        </ListItemButton>
                        <Divider />
                      </React.Fragment>
                    ))}
                  </List>
                ) : (
                  <Alert severity="info">
                    {Object.keys(knowledgePointsState).some(k => knowledgePointsState[k])
                      ? "没有找到符合筛选条件的题目"
                      : "暂无题目"
                    }
                  </Alert>
                )}
              </>
            )}
          </CardContent>
        </Card>
        
        {/* 题目详情和答题区域 */}
        {selectedQuestion && (
          <>
            <Card variant="outlined" sx={{ boxShadow: 1 }}>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  题目详情
                </Typography>
                <Typography variant="body1">
                  {selectedQuestion.description}
                </Typography>
                <Box sx={{ mt: 1, display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                  <Typography variant="body2" color="text.secondary">
                    知识点:
                  </Typography>
                  {getKnowledgePointsForQuestion(selectedQuestion).map(point => (
                    <Chip key={point} label={point} size="small" />
                  ))}
                </Box>
              </CardContent>
            </Card>
            
            <Button 
              variant="outlined" 
              onClick={() => setOpenSchemaDialog(true)}
              sx={{ mb: 3 }}
            >
              查看数据库模式
            </Button>
            
            <Card variant="outlined" sx={{ boxShadow: 1 }}>
              <CardContent>
                <Typography variant="subtitle1" gutterBottom>
                  你的SQL答案
                </Typography>
                <TextField
                  fullWidth
                  multiline
                  minRows={4}
                  maxRows={8}
                  value={sql}
                  onChange={e => setSql(e.target.value)}
                  placeholder="在此输入SQL语句..."
                  variant="outlined"
                  InputProps={{
                    style: { 
                      fontFamily: 'monospace',
                      overflowX: 'auto'
                    }
                  }}
                />
              </CardContent>
            </Card>
            
            <Button 
              variant="contained" 
              onClick={handleSubmit}
              disabled={loading || !sql.trim()}
              sx={{ width: '100%' }}
            >
              {loading ? <CircularProgress size={24} /> : '提交答案'}
            </Button>
          </>
        )}
        
        {/* 结果展示 */}
        {result && (
          <Card variant="outlined" sx={{ boxShadow: 1 }}>
            <CardContent>
              {result.is_correct ? (
                <Alert severity="success" sx={{ mb: 2 }}>
                  ✅ 答案正确！
                </Alert>
              ) : (
                <Alert severity="error" sx={{ mb: 2 }}>
                  ❌ 答案错误: {result.error_type}
                  <Box sx={{ mt: 1 }}>
                    <Typography variant="subtitle2" gutterBottom>
                      详细错误:
                    </Typography>
                    <ErrorFormatter error={result.detailed_errors?.[0]} />
                  </Box>
                </Alert>
              )}
            </CardContent>
          </Card>
        )}
        
        {/* 分析结果 */}
        {analysis && (
          <Card variant="outlined" sx={{ boxShadow: 1 }}>
            <CardContent>
              <Typography variant="subtitle1" gutterBottom>
                AI分析报告
              </Typography>
              
              <Box sx={{ mb: 2 }}>
                <Typography variant="subtitle2" gutterBottom>
                  1. 正确性分析
                </Typography>
                <Typography variant="body1">
                  {analysis.correctness_analysis || '无'}
                </Typography>
              </Box>
              
              <Box sx={{ mb: 2 }}>
                <Typography variant="subtitle2" gutterBottom>
                  2. 优化建议
                </Typography>
                <Typography variant="body1">
                  {analysis.optimization_suggestions || '无'}
                </Typography>
              </Box>
              
              <Box>
                <Typography variant="subtitle2" gutterBottom>
                  3. 思路异同
                </Typography>
                <Typography variant="body1">
                  {analysis.thinking_difference || '无'}
                </Typography>
              </Box>
            </CardContent>
          </Card>
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
          {schema && <SchemaViewer schema={schema?.schema_definition} />}
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

export default Practice;