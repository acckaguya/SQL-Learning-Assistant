import React from 'react';

interface SchemaTable {
  name: string;
  columns: {
    name: string;
    type: string;
    primary?: boolean;
  }[];
  sample_data?: Record<string, any>[];
}

interface SchemaDefinition {
  tables: SchemaTable[];
}

const SchemaViewer: React.FC<{ schema?: SchemaDefinition }> = ({ schema }) => {
  if (!schema || !schema.tables) return <div>无模式定义</div>;

  return (
    <div className="schema-viewer">
      {schema.tables.map(table => (
        <div key={table.name} className="mb-6">
          <h3 className="text-lg font-bold mb-2">表: {table.name}</h3>
          <table className="w-full mb-4">
            <thead>
              <tr>
                <th className="border px-4 py-2">列名</th>
                <th className="border px-4 py-2">类型</th>
                <th className="border px-4 py-2">主键</th>
              </tr>
            </thead>
            <tbody>
              {table.columns.map(col => (
                <tr key={col.name}>
                  <td className="border px-4 py-2">{col.name}</td>
                  <td className="border px-4 py-2">{col.type}</td>
                  <td className="border px-4 py-2 text-center">
                    {col.primary ? "是" : "否"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          
          {table.sample_data && (
            <div>
              <h4 className="font-medium mb-2">示例数据:</h4>
              <table className="w-full">
                <thead>
                  <tr>
                    {table.columns.map(col => (
                      <th key={col.name} className="border px-4 py-2">
                        {col.name}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {table.sample_data.map((row, idx) => (
                    <tr key={idx}>
                      {table.columns.map(col => (
                        <td key={col.name} className="border px-4 py-2">
                          {row[col.name]?.toString()}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      ))}
    </div>
  );
};

export default SchemaViewer;