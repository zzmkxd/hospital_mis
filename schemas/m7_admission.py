"""
M7 住院登记 — Pydantic Schema
"""

from pydantic import BaseModel, Field


class AdmissionCreate(BaseModel):
    """
    入院登记请求 — 触发 6 表联动事务。
    """
    case_no: int = Field(..., description="病案号")
    doctor_id: int = Field(..., description="主治医生ID")
    ward_id: int = Field(..., description="病房ID")
    bed_id: int = Field(..., description="床位ID")
    deposit_balance: float = Field(..., ge=0, description="预交金金额")


class WardQuery(BaseModel):
    """查询可选病房的参数。"""
    dept_id: int = Field(..., description="住院科室ID")
