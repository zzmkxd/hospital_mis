"""
M1 登录认证路由
--------------
对应 SQL 文件：sql/m1_login.sql
"""
from fastapi import APIRouter, HTTPException
from db import query_one
from schemas.m1_login import LoginRequest
from schemas.common import ErrorResponse

router = APIRouter()


@router.post("/login",
             responses={401: {"model": ErrorResponse}})
def login(req: LoginRequest):
    """
    用户登录。

    流程：
      1. 根据 ref_id + role 查询 account 表
      2. 应用层比对密码哈希（TODO: 当前明文比对，后续应接入 bcrypt）
      3. 查对应实体表获取姓名
      4. 成功返回 session 信息

    对应 SQL：sql/m1_login.sql 第 1 条
    """
    row = query_one(
        "SELECT account_id, ref_id, role, password_hash "
        "FROM account WHERE ref_id = %s AND role = %s",
        (req.ref_id, req.role)
    )

    if not row:
        raise HTTPException(status_code=401, detail="账号不存在或角色不匹配")

    if row["password_hash"] != req.password:
        raise HTTPException(status_code=401, detail="密码错误")

    # 根据角色查姓名
    name = req.role  # fallback
    if req.role == "医生":
        doc = query_one("SELECT name FROM doctor WHERE doctor_id = %s", (req.ref_id,))
        if doc: name = doc["name"]
    elif req.role == "病人":
        pat = query_one("SELECT name FROM patient WHERE case_no = %s", (req.ref_id,))
        if pat: name = pat["name"]

    return {
        "account_id": row["account_id"],
        "ref_id": row["ref_id"],
        "role": row["role"],
        "name": name,
        "message": "登录成功",
    }
