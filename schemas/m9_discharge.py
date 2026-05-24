"""
M9 出院结算 — Pydantic Schema
"""

from pydantic import BaseModel, Field


class DischargeRequest(BaseModel):
    """出院请求 — 触发 8 步事务。"""
    file_no: int = Field(..., description="住院档案号")
