"""
统计查询 — Pydantic Schema
"""

from pydantic import BaseModel, Field
from datetime import date


class DateRangeQuery(BaseModel):
    """时间段过滤参数。"""
    start_date: date = Field(..., description="起始日期")
    end_date: date = Field(..., description="截止日期")
