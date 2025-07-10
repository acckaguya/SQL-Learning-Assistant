import React, { useState, useEffect, useCallback } from 'react';
import { 
  Container, 
  Typography, 
  Card, 
  CardContent, 
  CardHeader, 
  Grid, 
  Button, 
  IconButton, 
  TextField,
  Checkbox,
  FormControlLabel,
  TableContainer,
  Table,
  TableHead,
  TableBody,
  TableRow,
  TableCell,
  TablePagination,
  Paper,
  CircularProgress,
  Alert,
  Collapse,
  Box,
  Chip,
  Tooltip,
  useTheme,
  CardActions, 
  DialogTitle,
  Dialog,
  DialogContent,
  DialogActions
} from '@mui/material';
import { useApi } from '../../hooks/useApi';
import AddIcon from '@mui/icons-material/Add';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import CloseIcon from '@mui/icons-material/Close';
import SearchIcon from '@mui/icons-material/Search';

interface KnowledgePoint {
  id: string;
  label: string;
}

const KNOWLEDGE_POINTS: KnowledgePoint[] = [
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

const QuestionManagement: React.FC = () => {
  const api = useApi();
  const theme = useTheme();
  const [questions, setQuestions] = useState<any[]>([]);
  const [schemas, setSchemas] = useState<any[]>([]);
  const [newQuestion, setNewQuestion] = useState({
    question_id: '',
    question_title: '',
    description: '',
    schema_id: '',
    answer_sql: '',
    order_sensitive: false,
  });
  
  const [knowledgePointsState, setKnowledgePointsState] = useState<Record<string, boolean>>(() => {
    const initialState: Record<string, boolean> = {};
    KNOWLEDGE_POINTS.forEach(point => {
      initialState[point.id] = false;
    });
    return initialState;
  });
  
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [loading, setLoading] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [selectedQuestion, setSelectedQuestion] = useState<any>(null);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [searchTerm, setSearchTerm] = useState('');
  
  // 获取所有题目
  const fetchQuestions = useCallback(async () => {
    setLoading(true);
    try {
      const data = await api.get('/questions/get');
      if (data) setQuestions(data);
    } catch (err) {
      console.error("获取题目失败:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  // 获取所有模式
  const fetchSchemas = useCallback(async () => {
    try {
      const data = await api.get('/sample-schemas/get/schemas');
      if (data) setSchemas(data);
    } catch (err) {
      console.error("获取模式失败:", err);
    }
  }, []);

  useEffect(() => {
    fetchQuestions();
    fetchSchemas();
  }, [fetchQuestions, fetchSchemas]);

  const handleGenerateQuestion = useCallback(async () => {
    if (!newQuestion.schema_id) {
      setError('请选择数据库模式');
      return;
    }
    
    const selectedPoints = Object.keys(knowledgePointsState)
      .filter(k => knowledgePointsState[k]);
    
    if (selectedPoints.length === 0) {
      setError('请至少选择一个知识点');
      return;
    }
    
    try {
      const result = await api.post('/questions/generate', {
        schema_id: newQuestion.schema_id,
        knowledge_points: selectedPoints
      });
      
      if (result) {
        setQuestions(prevQuestions => [result, ...prevQuestions]);
        setSuccess('题目生成成功！');
        setTimeout(() => setSuccess(''), 3000);
      }
    } catch (err: any) {
      setError(`生成题目失败: ${err.message || '未知错误'}`);
    } finally {
      setLoading(false);
    }
  }, [newQuestion.schema_id, knowledgePointsState, api]);

  const handleEditQuestion = useCallback((question: any) => {
    setSelectedQuestion(question);
    setNewQuestion({
      question_id: question.question_id,
      question_title: question.question_title,
      description: question.description,
      schema_id: question.schema_id,
      answer_sql: question.answer_sql,
      order_sensitive: question.order_sensitive || false,
    });
    
    setKnowledgePointsState(prev => {
      const newState = { ...prev };
      KNOWLEDGE_POINTS.forEach(kp => {
        newState[kp.id] = !!question[kp.id];
      });
      return newState;
    });
    
    setIsEditing(true);
  }, []);

  const handleKnowledgePointChange = useCallback((id: string) => (e: React.ChangeEvent<HTMLInputElement>) => {
    setKnowledgePointsState(prev => ({
      ...prev,
      [id]: e.target.checked
    }));
  }, []);

  const handleSaveQuestion = useCallback(async () => {
    try {
      const updated = await api.put(`/questions/update/${newQuestion.question_id}`, {
        ...newQuestion,
        ...knowledgePointsState
      });
      
      if (updated) {
        setQuestions(questions.map(q => 
          q.question_id === newQuestion.question_id ? updated : q
        ));
        setSuccess('题目更新成功！');
        setTimeout(() => setSuccess(''), 3000);
        setIsEditing(false);
      }
    } catch (err: any) {
      setError(`更新题目失败: ${err.message || '未知错误'}`);
    }
  }, [newQuestion, knowledgePointsState, questions, api]);

  const handleDeleteQuestion = useCallback(async (id: string) => {
    if (window.confirm('确定删除该题目吗？')) {
      try {
        await api.delete(`/questions/${id}`);
        setQuestions(questions.filter(q => q.question_id !== id));
        setSuccess('题目删除成功！');
        setTimeout(() => setSuccess(''), 3000);
        if (isEditing && selectedQuestion?.question_id === id) {
          setIsEditing(false);
        }
      } catch (err: any) {
        setError(`删除题目失败: ${err.message || '未知错误'}`);
      }
    }
  }, [api, questions, isEditing, selectedQuestion]);

  const filteredQuestions = questions.filter(question => 
    question.question_title.toLowerCase().includes(searchTerm.toLowerCase()) ||
    question.description.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <Container maxWidth="xl">
      <Typography variant="h5" gutterBottom sx={{ mb: 3 }}>
        题库管理
      </Typography>

      {/* 消息通知 */}
      <Collapse in={!!error || !!success}>
        {error && (
          <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>
            {error}
          </Alert>
        )}
        {success && (
          <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccess('')}>
            {success}
          </Alert>
        )}
      </Collapse>

      {/* 生成题目区域 */}
      <Card sx={{ mb: 4, boxShadow: 3 }}>
        <CardHeader
          title={
            <Box display="flex" alignItems="center">
              <AddIcon color="primary" sx={{ mr: 1 }} />
              <Typography variant="h6">生成新题目</Typography>
            </Box>
          }
          sx={{ backgroundColor: theme.palette.primary.light, color: 'white' }}
        />
        <CardContent>
          <Box>
            <TextField
              select
              fullWidth
              label="选择数据库模式"
              value={newQuestion.schema_id}
              onChange={e => setNewQuestion({...newQuestion, schema_id: e.target.value})}
              variant="outlined"
              SelectProps={{
                native: true,
              }}
            >
              <option value="">选择数据库模式</option>
              {schemas.map(schema => (
                <option key={schema.schema_id} value={schema.schema_id}>
                  {schema.schema_name}
                </option>
              ))}
            </TextField>
          </Box>
          
          <Typography variant="subtitle1" sx={{ mt: 3, mb: 2 }}>知识点选择</Typography>
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2 }}>
            {KNOWLEDGE_POINTS.map(point => (
              <Box key={point.id}>
                <FormControlLabel
                  control={
                    <Checkbox
                      checked={knowledgePointsState[point.id] || false}
                      onChange={handleKnowledgePointChange(point.id)}
                      color="primary"
                    />
                  }
                  label={point.label}
                />
              </Box>
            ))}
          </Box>
        </CardContent>
        <CardActions sx={{ justifyContent: 'flex-end', p: 2 }}>
          <Button
            variant="contained"
            color="primary"
            onClick={handleGenerateQuestion}
            disabled={loading}
            sx={{
              position: 'relative'
            }}
          >
            生成题目
          </Button>
        </CardActions>
      </Card>

      {/* 题目搜索 */}
      <TextField
        fullWidth
        label="搜索题目..."
        variant="outlined"
        value={searchTerm}
        onChange={e => setSearchTerm(e.target.value)}
        sx={{ mb: 3 }}
        InputProps={{
          endAdornment: <SearchIcon />
        }}
      />
      
      {/* 题目列表 */}
      <Card>
        <CardContent>
          <TableContainer component={Paper} sx={{ maxHeight: 600 }}>
            <Table stickyHeader>
              <TableHead>
                <TableRow>
                  <TableCell>标题</TableCell>
                  <TableCell>描述</TableCell>
                  <TableCell>知识点</TableCell>
                  <TableCell>操作</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {filteredQuestions.length > 0 ? (
                  <>
                    {filteredQuestions
                      .slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)
                      .map(question => (
                        <TableRow key={question.question_id} hover>
                          <TableCell>{question.question_title}</TableCell>
                          <TableCell>
                            <Tooltip title={question.description} placement="top">
                              <Typography 
                                variant="body2" 
                                noWrap 
                                sx={{ maxWidth: 200 }}
                              >
                                {question.description}
                              </Typography>
                            </Tooltip>
                          </TableCell>
                          <TableCell>
                            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                              {KNOWLEDGE_POINTS
                                .filter(kp => question[kp.id])
                                .map(kp => (
                                  <Chip
                                    key={kp.id}
                                    label={kp.label}
                                    size="small"
                                  />
                                ))}
                            </Box>
                          </TableCell>
                          <TableCell>
                            <IconButton onClick={() => handleEditQuestion(question)}>
                              <EditIcon color="primary" />
                            </IconButton>
                            <IconButton onClick={() => handleDeleteQuestion(question.question_id)}>
                              <DeleteIcon color="error" />
                            </IconButton>
                          </TableCell>
                        </TableRow>
                      ))}
                  </>
                ) : (
                  <TableRow>
                    <TableCell colSpan={4} align="center">
                      没有题目
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </TableContainer>
          <TablePagination
            rowsPerPageOptions={[5, 10, 25]}
            component="div"
            count={filteredQuestions.length}
            rowsPerPage={rowsPerPage}
            page={page}
            onPageChange={(event, newPage) => setPage(newPage)}
            onRowsPerPageChange={event => {
              setRowsPerPage(parseInt(event.target.value, 10));
              setPage(0);
            }}
          />
        </CardContent>
      </Card>
      
      {/* 编辑对话框 */}
      {isEditing && (
        <Dialog open={isEditing} onClose={() => setIsEditing(false)} maxWidth="md" fullWidth>
          <DialogTitle>
            编辑题目
            <IconButton
              onClick={() => setIsEditing(false)}
              sx={{
                position: 'absolute',
                right: 8,
                top: 8,
              }}
            >
              <CloseIcon />
            </IconButton>
          </DialogTitle>
          <DialogContent>
            <Box mt={2}>
              <TextField
                fullWidth
                label="题目标题"
                value={newQuestion.question_title}
                onChange={e => setNewQuestion({...newQuestion, question_title: e.target.value})}
                margin="normal"
              />
              
              <TextField
                fullWidth
                label="题目描述"
                value={newQuestion.description}
                onChange={e => setNewQuestion({...newQuestion, description: e.target.value})}
                margin="normal"
                multiline
                rows={4}
              />
              
              <TextField
                fullWidth
                label="参考答案SQL"
                value={newQuestion.answer_sql}
                onChange={e => setNewQuestion({...newQuestion, answer_sql: e.target.value})}
                margin="normal"
                multiline
                rows={3}
                InputProps={{
                  style: { fontFamily: 'monospace' }
                }}
              />
              
              <FormControlLabel
                control={
                  <Checkbox
                    checked={newQuestion.order_sensitive}
                    onChange={e => setNewQuestion({...newQuestion, order_sensitive: e.target.checked})}
                    color="primary"
                  />
                }
                label="是否对结果顺序敏感"
                sx={{ mt: 2 }}
              />
              
              <Typography variant="subtitle1" sx={{ mt: 3 }}>
                知识点设置
              </Typography>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2, mt: 1 }}>
                {KNOWLEDGE_POINTS.map(point => (
                  <Box key={point.id}>
                    <FormControlLabel
                      control={
                        <Checkbox
                          checked={knowledgePointsState[point.id] || false}
                          onChange={handleKnowledgePointChange(point.id)}
                          color="primary"
                        />
                      }
                      label={point.label}
                    />
                  </Box>
                ))}
              </Box>
            </Box>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setIsEditing(false)}>取消</Button>
            <Button 
              variant="contained" 
              color="primary" 
              onClick={handleSaveQuestion}
            >
              保存
            </Button>
          </DialogActions>
        </Dialog>
      )}
    </Container>
  );
};

export default QuestionManagement;