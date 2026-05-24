"""
M6 病人缴费与查看 — Pydantic Schema
"""

from pydantic import BaseModel, Field


class PaymentRequest(BaseModel):
    """支付处方请求。"""
    presc_id: int = Field(..., description="处方ID")


class PatientHistoryQuery(BaseModel):
    """病人历史查询条件 — 目前以 case_no 为主，后续可扩展时间范围。"""
    case_no: int = Field(..., description="病案号")
