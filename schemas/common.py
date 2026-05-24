"""
公共类型 — 各模块共用的枚举和响应模型。
"""

from pydantic import BaseModel, Field


# ============================================================
# 通用响应
# ============================================================

class MessageResponse(BaseModel):
    """简单操作结果，含受影响行数（UPDATE/DELETE 场景）。"""
    message: str
    affected_rows: int


class ErrorResponse(BaseModel):
    """统一错误返回格式。"""
    detail: str
    error_code: str | None = None
