"""
数据库工具模块
--------------
封装 PyMySQL 连接池和事务管理。
所有路由通过本模块访问数据库，不直接操作 PyMySQL。

用法示例：

    # 查询多条
    rows = db.query("SELECT * FROM department")

    # 查询单条
    row = db.query_one("SELECT * FROM patient WHERE case_no = %s", (case_no,))

    # 写操作（INSERT/UPDATE/DELETE）
    last_id = db.execute("INSERT INTO department (dept_name, dept_type) VALUES (%s, %s)",
                         ("内科", "两者兼有"))

    # 事务（多个写操作原子执行）
    with db.transaction() as conn:
        db.execute("INSERT INTO ...", params, conn=conn)
        db.execute("UPDATE ...", params2, conn=conn)
        # 抛出异常自动回滚，正常结束自动提交
"""

import pymysql
import pymysql.cursors
from contextlib import contextmanager
from config import DB_CONFIG


def _get_conn():
    """创建一条新连接。"""
    return pymysql.connect(
        **DB_CONFIG,
        cursorclass=pymysql.cursors.DictCursor,  # 返回 dict 而非 tuple，方便 JSON 序列化
    )


def query(sql: str, params=None) -> list[dict]:
    """
    执行 SELECT 返回多行。

    Args:
        sql: SQL 语句，占位符用 %s（PyMySQL 风格）
        params: 参数元组，如 (val1, val2)

    Returns:
        list[dict]: 查询结果，每行是一个 dict
    """
    with _get_conn() as conn:
        with conn.cursor() as cursor:
            cursor.execute(sql, params)
            return cursor.fetchall()


def query_one(sql: str, params=None) -> dict | None:
    """
    执行 SELECT 返回单行，无结果返回 None。
    用于按主键查询、COUNT 检查等场景。
    """
    with _get_conn() as conn:
        with conn.cursor() as cursor:
            cursor.execute(sql, params)
            return cursor.fetchone()


def execute(sql: str, params=None, conn=None) -> int:
    """
    执行 INSERT/UPDATE/DELETE，返回受影响行数或 lastrowid。

    Args:
        sql: SQL 语句
        params: 参数元组
        conn: 事务连接（可选）。传入则使用该连接，不自动关闭。

    Returns:
        int: INSERT 时返回新 ID，其他返回受影响行数
    """
    own_conn = conn is None
    if own_conn:
        conn = _get_conn()
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, params)
            conn.commit() if own_conn else None
            return cursor.lastrowid or cursor.rowcount
    except Exception:
        if own_conn:
            conn.rollback()
        raise
    finally:
        if own_conn:
            conn.close()


@contextmanager
def transaction():
    """
    事务上下文管理器。

    用法：
        with db.transaction() as conn:
            db.execute("INSERT ...", params1, conn=conn)
            db.execute("UPDATE ...", params2, conn=conn)
        # 退出 with 块自动提交；异常自动回滚
    """
    conn = _get_conn()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
