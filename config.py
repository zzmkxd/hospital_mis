"""
应用配置
--------
所有可调参数集中在这里。

通过环境变量覆盖默认值：
  方式1（推荐）：复制 .env.example 为 .env，安装 python-dotenv，自动加载
  方式2：直接设置系统环境变量
  方式3：修改下方 DB_CONFIG 默认值中的 password
"""
from os import environ, path

# 尝试加载 .env 文件（需要 pip install python-dotenv）
try:
    from dotenv import load_dotenv
    _env_file = path.join(path.dirname(__file__), ".env")
    if path.exists(_env_file):
        load_dotenv(_env_file)
except ImportError:
    pass

# MySQL 连接配置
# 优先级：环境变量 > 下方默认值
DB_CONFIG = {
    "host": environ.get("DB_HOST", "localhost"),
    "port": int(environ.get("DB_PORT", 3306)),
    "user": environ.get("DB_USER", "root"),
    "password": environ.get("DB_PASSWORD", ""),
    "database": environ.get("DB_NAME", "hospital_mis"),
    "charset": "utf8mb4",
}

# 服务端口
SERVER_HOST = environ.get("SERVER_HOST", "127.0.0.1")
SERVER_PORT = int(environ.get("SERVER_PORT", 8000))
