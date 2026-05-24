"""
M3 排班管理 — Pydantic Schema
"""

from pydantic import BaseModel, Field, model_validator
from typing import Literal
from datetime import date, time


class ScheduleCreate(BaseModel):
    """
    创建排班请求。
    校验规则（应用层）：
      - sched_type='门诊坐诊' → clinic 必填
      - sched_type='住院巡诊' → clinic 必须为 None
    """
    doctor_id: int = Field(..., description="医生ID")
    sched_date: date = Field(..., description="排班日期")
    start_time: time = Field(..., description="开始时间")
    end_time: time = Field(..., description="结束时间")
    sched_type: Literal["门诊坐诊", "住院巡诊"] = Field(..., description="排班类型")
    clinic: str | None = Field(None, max_length=20, description="诊室（仅门诊坐诊填写）")

    @model_validator(mode="after")
    def check_clinic_rule(self):
        """R05：门诊坐诊诊室必填，住院巡诊诊室必空。"""
        if self.sched_type == "门诊坐诊" and not self.clinic:
            raise ValueError("门诊坐诊排班必须指定诊室")
        if self.sched_type == "住院巡诊" and self.clinic is not None:
            raise ValueError("住院巡诊排班诊室应为空")
        return self


class ScheduleUpdate(ScheduleCreate):
    """编辑排班，字段与创建相同。"""
    pass
