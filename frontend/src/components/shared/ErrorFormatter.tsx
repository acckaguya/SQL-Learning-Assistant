import React from 'react';

interface ErrorDetail {
  error_type: string;
  message?: string;
  invalid_tables?: Array<{ table: string; reason: string }>;
  invalid_columns?: Array<{ column: string; reason: string }>;
  student_columns?: string[];
  answer_columns?: string[];
  student_rows?: number;
  answer_rows?: number;
  comparison_details?: Array<{
    row: number;
    differences: Array<{
      column: string;
      student_value: any;
      answer_value: any;
    }>;
  }>;
}

const ErrorFormatter: React.FC<{ error: ErrorDetail }> = ({ error }) => {
  if (!error) return null;

  const renderSemanticError = () => (
    <div>
      <h3 className="text-red-600 font-bold">语义错误</h3>
      {error.invalid_tables && (
        <div className="mt-2">
          <h4 className="font-medium">表引用错误:</h4>
          <ul className="list-disc pl-5">
            {error.invalid_tables.map((t, i) => (
              <li key={i}>
                {t.table}: {t.reason}
              </li>
            ))}
          </ul>
        </div>
      )}
      {error.invalid_columns && (
        <div className="mt-2">
          <h4 className="font-medium">列引用错误:</h4>
          <ul className="list-disc pl-5">
            {error.invalid_columns.map((c, i) => (
              <li key={i}>
                {c.column}: {c.reason}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );

  const renderResultMismatch = () => (
    <div>
      <h3 className="text-red-600 font-bold">结果不匹配</h3>
      {error.student_columns && error.answer_columns && (
        <div className="mt-2">
          <p>你的查询返回列: {error.student_columns.join(', ')}</p>
          <p>参考答案返回列: {error.answer_columns.join(', ')}</p>
        </div>
      )}
      {error.student_rows !== undefined && error.answer_rows !== undefined && (
        <div className="mt-2">
          <p>你的查询返回 {error.student_rows} 行</p>
          <p>参考答案返回 {error.answer_rows} 行</p>
        </div>
      )}
      {error.comparison_details && (
        <div className="mt-2">
          <h4 className="font-medium">行数据不匹配:</h4>
          {error.comparison_details.map((d, i) => (
            <div key={i} className="mt-1">
              <p>第 {d.row} 行:</p>
              <ul className="list-disc pl-5">
                {d.differences.map((diff, j) => (
                  <li key={j}>
                    {diff.column}: 你的值 "{diff.student_value}", 
                    参考答案值 "{diff.answer_value}"
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      )}
    </div>
  );

  return (
    <div className="error-details p-3 border rounded bg-red-50">
      {error.error_type === 'semantic_error' && renderSemanticError()}
      {error.error_type === 'result_mismatch' && renderResultMismatch()}
      {error.message && <p>{error.message}</p>}
    </div>
  );
};

export default ErrorFormatter;