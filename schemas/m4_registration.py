"""
M4 病人挂号 — Pydantic Schema
"""

from pydantic import BaseModel, Field
from typing import Literal
from datetime import date


class RegistrationCreate(BaseModel):
    """
    创建挂号请求。
    reg_type 由后端根据历史就诊记录自动判定，前端可不传。
    """
    case_no: int = Field(..., description="病案号")
    doctor_id: int = Field(..., description="医生ID")
    schedule_id: int = Field(..., description="排班ID")
    reg_type: Literal["初诊", "复诊"] = Field(..., description="挂号类型")


class AvailableDoctorsQuery(BaseModel):
    """查询可选医生列表的参数。"""
    dept_id: int = Field(..., description="科室ID")
    target_date: date = Field(..., description="就诊日期")
