"""
M1 登录认证 — Pydantic Schema
"""

from pydantic import BaseModel, Field
from typing import Literal


class LoginRequest(BaseModel):
    """
    登录请求。
    ref_id 是医生ID或病案号；role 决定路由到哪个实体表。
    """
    ref_id: int = Field(..., description="医生ID或病案号")
    password: str = Field(..., min_length=1, description="明文密码，后端哈希比对")
    role: Literal["医生", "病人", "管理员"] = Field(..., description="登录角色")


class LoginResponse(BaseModel):
    """登录成功返回 session 信息。"""
    account_id: int
    ref_id: int
    role: str
    message: str = "登录成功"
