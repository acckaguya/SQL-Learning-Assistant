import React, { useState, useEffect, useCallback } from 'react';
import { 
  Container, 
  Typography, 
  TextField, 
  Button, 
  Card, 
  CardContent, 
  CardActions, 
  CardHeader,
  IconButton,
  CircularProgress,
  Alert,
  Collapse,
  Box,
  useTheme
} from '@mui/material';
import { useApi } from '../../hooks/useApi';
import SchemaViewer from '../shared/SchemaViewer';
import DeleteIcon from '@mui/icons-material/Delete';
import AddCircleOutlineIcon from '@mui/icons-material/AddCircleOutline';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';

const SchemaManagement: React.FC = () => {
  const api = useApi();
  const theme = useTheme();
  const [schemas, setSchemas] = useState<any[]>([]);
  const [newSchema, setNewSchema] = useState({
    schema_name: '',
    schema_definition: '',
    init_sql: ''
  });
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [isCreating, setIsCreating] = useState(false);
  const [expandedSchema, setExpandedSchema] = useState<boolean[]>([]);


  const fetchSchemas = useCallback(async () => {
    try {
      const data = await api.get('/sample-schemas/get/schemas');
      if (data) {
        setSchemas(data);
        setExpandedSchema(new Array(data.length).fill(false));
      }
    } catch (err) {
      console.error("获取模式失败:", err);
    }
  }, [api]);


  useEffect(() => {
    fetchSchemas();
  }, []);

  const handleCreateSchema = async () => {
    if (!newSchema.schema_name || !newSchema.schema_definition) {
      setError('模式名称和定义不能为空');
      return;
    }
    
    setIsCreating(true);
    setError('');
    setSuccess('');
    
    try {
      const schemaDef = JSON.parse(newSchema.schema_definition);
      
      const result = await api.post('/sample-schemas/create', {
        schema_name: newSchema.schema_name,
        schema_definition: schemaDef,
        init_sql: newSchema.init_sql
      });
      
      if (result) {
        setSchemas(prev => [result, ...prev]);
        setNewSchema({ schema_name: '', schema_definition: '', init_sql: '' });
        setSuccess('数据库模式创建成功！');
        setTimeout(() => setSuccess(''), 3000);
      }
    } catch (e: any) {
      let errorMessage = 'JSON格式错误';
      if (e instanceof SyntaxError) {
        errorMessage += ": 无效的JSON格式";
      } else if (e instanceof Error) {
        errorMessage += `: ${e.message}`;
      } else {
        errorMessage += ": 未知错误";
      }
      setError(errorMessage);
    } finally {
      setIsCreating(false);
    }
  };

  const handleDeleteSchema = async (schemaId: string) => {
    if (window.confirm('确定删除此数据库模式吗？此操作不可逆！')) {
      const result = await api.delete(`/sample-schemas/delete/${schemaId}`);
      if (result) {
        setSchemas(prev => prev.filter(s => s.schema_id !== schemaId));
        setSuccess('数据库模式删除成功！');
        setTimeout(() => setSuccess(''), 3000);
      }
    }
  };

  const toggleSchemaView = (index: number) => {
    setExpandedSchema(prev => {
      const newExpanded = [...prev];
      newExpanded[index] = !newExpanded[index];
      return newExpanded;
    });
  };

  return (
    <Container maxWidth="xl">
      <Typography variant="h5" gutterBottom sx={{ mb: 3 }}>
        样例数据库管理
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

      {/* 创建新数据库模式 */}
      <Card sx={{ mb: 4, borderRadius: 2, boxShadow: 3 }}>
        <CardHeader
          title={
            <Box display="flex" alignItems="center">
              <AddCircleOutlineIcon color="primary" sx={{ mr: 1 }} />
              <Typography variant="h6">创建新数据库模式</Typography>
            </Box>
          }
          sx={{ backgroundColor: theme.palette.primary.light, color: 'white' }}
        />
        <CardContent>
          <Box sx={{ width: '100%', mb: 2 }}>
            <TextField
              fullWidth
              label="模式名称"
              value={newSchema.schema_name}
              onChange={e => setNewSchema(prev => ({
                ...prev, 
                schema_name: e.target.value
              }))}
              variant="outlined"
              size="small"
            />
          </Box>

          <Box sx={{ 
            display: 'flex',
            flexDirection: 'column',
            gap: 2,
            mt: 1,
            width: '100%'
          }}>
            <Box sx={{ width: '100%' }}>
              <TextField
                fullWidth
                label="模式定义 (JSON格式)"
                value={newSchema.schema_definition}
                onChange={e => setNewSchema(prev => ({
                  ...prev, 
                  schema_definition: e.target.value
                }))}
                variant="outlined"
                multiline
                rows={8}
                placeholder={`示例格式: \n{\n  "tables": [\n    {\n      "name": "users",\n      "columns": [ ... ],\n      "sample_data": [ ... ]\n    }\n  ]\n}`}
                InputProps={{
                  style: { fontFamily: 'monospace' }
                }}
              />
            </Box>
            <Box sx={{ width: '100%' }}>
              <TextField
                fullWidth
                label="初始数据SQL"
                value={newSchema.init_sql}
                onChange={e => setNewSchema(prev => ({
                  ...prev, 
                  init_sql: e.target.value
                }))}
                variant="outlined"
                multiline
                rows={4}
                placeholder="示例: INSERT INTO users VALUES (1, 'Alice', 'alice@example.com');"
                InputProps={{
                  style: { fontFamily: 'monospace' }
                }}
              />
            </Box>
          </Box>
        </CardContent>
        <CardActions sx={{ justifyContent: 'flex-end', p: 2 }}>
          <Button
            variant="contained"
            color="primary"
            onClick={handleCreateSchema}
            disabled={isCreating}
            startIcon={isCreating ? <CircularProgress size={20} /> : undefined}
          >
            {isCreating ? '创建中...' : '创建模式'}
          </Button>
        </CardActions>
      </Card>
      
      {/* 数据库列表 */}
      <Typography variant="h6" gutterBottom sx={{ mb: 2 }}>
        数据库列表
      </Typography>
      
      {schemas.length === 0 ? (
        <Card sx={{ p: 4, textAlign: 'center' }}>
          <Typography variant="body1" color="textSecondary">
            暂无数据库模式
          </Typography>
        </Card>
      ) : (
        <Box sx={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))',
          gap: 3,
          width: '100%'
        }}>
          {schemas.map((schema, index) => (
            <Box key={schema.schema_id}>
              <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
                <CardHeader
                  title={schema.schema_name}
                  subheader={`创建时间: ${new Date(schema.created_at).toLocaleDateString()}`}
                  action={
                    <IconButton 
                      color="error" 
                      onClick={() => handleDeleteSchema(schema.schema_id)}
                      aria-label="删除模式"
                    >
                      <DeleteIcon />
                    </IconButton>
                  }
                />
                
                <CardContent sx={{ flexGrow: 1 }}>
                  <Box 
                    sx={{ 
                      maxHeight: expandedSchema[index] ? 'none' : 200,
                      overflow: 'hidden'
                    }}
                  >
                    <SchemaViewer schema={schema.schema_definition} />
                  </Box>
                  
                  {schema.init_sql && (
                    <Box sx={{ mt: 2, maxHeight: 150, overflow: 'auto' }}>
                      <Typography variant="subtitle2" gutterBottom>
                        初始数据SQL:
                      </Typography>
                      <Box 
                        component="pre" 
                        sx={{ 
                          backgroundColor: theme.palette.grey[100], 
                          p: 1, 
                          borderRadius: 1,
                          fontSize: '0.75rem',
                          whiteSpace: 'pre-wrap',
                          wordWrap: 'break-word'
                        }}
                      >
                        {schema.init_sql}
                      </Box>
                    </Box>
                  )}
                </CardContent>
                
                <CardActions disableSpacing>
                  <Button
                    startIcon={expandedSchema[index] ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                    onClick={() => toggleSchemaView(index)}
                    size="small"
                  >
                    {expandedSchema[index] ? '收起' : '展开'}
                  </Button>
                </CardActions>
              </Card>
            </Box>
          ))}
        </Box>
      )}
    </Container>
  );
};

export default SchemaManagement;