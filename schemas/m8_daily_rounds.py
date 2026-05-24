"""
M8 每日查房 — Pydantic Schema
"""

from pydantic import BaseModel, Field


class DailyRoundItem(BaseModel):
    """一张处方的用药明细项。"""
    medicine_id: int = Field(..., description="药品ID")
    qty: int = Field(..., gt=0, description="数量")
    usage_inst: str | None = Field(None, max_length=200, description="用法")


class DailyRoundCreate(BaseModel):
    """
    每日查房请求 — 触发 8 步事务。
    一天一条住院记录 + 一张住院处方 + 多条用药明细。
    """
    file_no: int = Field(..., description="住院档案号")
    doctor_id: int = Field(..., description="主治医生ID")
    treatment_desc: str | None = Field(None, description="当日治疗方案描述")
    details: list[DailyRoundItem] = Field(..., min_length=1, description="用药明细列表")
