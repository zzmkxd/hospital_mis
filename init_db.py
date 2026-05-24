"""重置数据库 — 删除重建所有表，不含测试数据"""
import pymysql, re
from config import DB_CONFIG

conn = pymysql.connect(
    host=DB_CONFIG["host"],
    port=DB_CONFIG["port"],
    user=DB_CONFIG["user"],
    password=DB_CONFIG["password"],
    charset="utf8mb4",
    use_unicode=True,
)
c = conn.cursor()

c.execute('DROP DATABASE IF EXISTS hospital_mis')
c.execute('CREATE DATABASE hospital_mis DEFAULT CHARACTER SET utf8mb4 DEFAULT COLLATE utf8mb4_unicode_ci')
c.execute('USE hospital_mis')

with open('hospital_ddl.sql', encoding='utf-8') as f:
    ddl = f.read()

ddl_clean = re.sub(r'--.*$', '', ddl, flags=re.MULTILINE)
statements = [s.strip() for s in ddl_clean.split(';') if s.strip()]

for stmt in statements:
    if stmt.upper().startswith('USE ') or stmt.upper().startswith('CREATE DATABASE'):
        continue
    c.execute(stmt)

conn.commit()

c.execute('SHOW TABLES')
tables = [t[0] for t in c.fetchall()]
print(f'{len(tables)} tables created')
conn.close()
