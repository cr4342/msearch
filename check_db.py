#!/usr/bin/env python3
import lancedb

db = lancedb.connect('/data/project/msearch/data/database/lancedb')
table = db.open_table('unified_vectors')
print(f'总记录数: {table.count_rows()}')
df = table.to_pandas()
print(f'\n列名: {list(df.columns)}')
print(f'\n文件路径:')
for idx, row in df.iterrows():
    file_path = row.get('file_path', 'N/A')
    file_type = row.get('file_type', 'N/A')
    vector_id = row.get('id', 'N/A')
    print(f'  {idx+1}. {vector_id} - {file_path} ({file_type})')
    print(f"     所有列数据: {dict(row)}")
