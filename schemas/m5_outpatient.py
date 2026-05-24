"""
M5 门诊接诊与处方 — Pydantic Schema
"""

from pydantic import BaseModel, Field
from typing import Literal


class PrescriptionDetailItem(BaseModel):
    """处方明细中的一条药品记录。"""
    medicine_id: int = Field(..., description="药品ID")
    qty: int = Field(..., gt=0, description="数量")
    usage_inst: str | None = Field(None, max_length=200, description="用法说明（如'每日三次，每次一片'）")


class OutpatientPrescriptionCreate(BaseModel):
    """
    开具门诊处方请求。
    details 可包含多条药品明细。
    """
    reg_id: int = Field(..., description="挂号ID")
    doctor_id: int = Field(..., description="医生ID（开方人）")
    symptom_desc: str | None = Field(None, description="症状描述")
    details: list[PrescriptionDetailItem] = Field(..., min_length=1, description="用药明细列表")
    deduct_stock: bool = Field(False, description="是否同时扣减库存")
