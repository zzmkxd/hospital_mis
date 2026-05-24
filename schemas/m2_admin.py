"""
M2 管理员基础数据维护 — Pydantic Schema
"""

from pydantic import BaseModel, Field
from typing import Literal


# ---- 科室 ----

class DepartmentCreate(BaseModel):
    dept_name: str = Field(..., max_length=50, description="科室名称")
    dept_type: Literal["门诊", "住院", "两者兼有"] = Field(..., description="科室类型")
    phone: str | None = Field(None, max_length=20, description="联系电话")


class DepartmentUpdate(BaseModel):
    dept_name: str = Field(..., max_length=50)
    dept_type: Literal["门诊", "住院", "两者兼有"]
    phone: str | None = Field(None, max_length=20)


# ---- 医生 ----

class DoctorCreate(BaseModel):
    """新增医生 + 同时创建账号（事务）。"""
    name: str = Field(..., max_length=30, description="姓名")
    gender: Literal["男", "女"] | None = None
    title: str | None = Field(None, max_length=30, description="职称")
    consultation_fee: float = Field(..., gt=0, description="诊疗费")
    phone: str | None = Field(None, max_length=20)
    dept_id: int = Field(..., description="所属科室ID")
    password: str = Field(..., min_length=1, description="登录密码（明文，后端负责哈希）")


class DoctorUpdate(BaseModel):
    name: str = Field(..., max_length=30)
    gender: Literal["男", "女"] | None = None
    title: str | None = Field(None, max_length=30)
    consultation_fee: float = Field(..., gt=0)
    phone: str | None = Field(None, max_length=20)
    dept_id: int


# ---- 药品 ----

class MedicineCreate(BaseModel):
    med_name: str = Field(..., max_length=100, description="药品名称")
    specification: str | None = Field(None, max_length=50, description="规格")
    unit: str | None = Field(None, max_length=20, description="单位")
    unit_price: float = Field(..., gt=0, description="单价")
    stock_qty: int = Field(..., ge=0, description="库存数量")


class MedicineUpdate(BaseModel):
    med_name: str = Field(..., max_length=100)
    specification: str | None = Field(None, max_length=50)
    unit: str | None = Field(None, max_length=20)
    unit_price: float = Field(..., gt=0)
    stock_qty: int = Field(..., ge=0)
