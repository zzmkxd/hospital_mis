"""
FastAPI 应用入口
----------------
启动命令：
    uvicorn main:app --reload --host 127.0.0.1 --port 8000

启动后访问：
    http://127.0.0.1:8000/docs     ← Swagger UI（接口测试面板）
    http://127.0.0.1:8000/redoc    ← ReDoc 文档

项目结构：
    main.py            ← 本文件，注册路由
    config.py          ← 数据库连接、端口配置
    db.py              ← 数据库工具（连接池、事务封装）
    init_db.py         ← 一键建库脚本
    seed_data.py       ← 测试数据初始化
    routers/           ← 路由层，一个模块一个文件
    schemas/           ← Pydantic 请求/响应模型
    sql/               ← 所有 SQL 查询（开发文档引用的源文件）
    docs/              ← 开发文档
    static/            ← 前端静态文件（HTML/JS/CSS）
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# 导入所有路由模块
from routers import (
    m1_login,
    m2_admin_maintenance,
    m3_schedule,
    m4_registration,
    m5_outpatient,
    m6_payment,
    m7_admission,
    m8_daily_rounds,
    m9_discharge,
    stats,
)

app = FastAPI(
    title="医院管理信息系统 API",
    description="Hospital Management Information System — 数据库课程设计",
    version="1.0.0",
)

# CORS — 允许前端跨域访问（前后端分离开发时需要）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# 注册路由（每个模块对应一个 prefix）
# Swagger UI 中会按 tag 分组显示
# ============================================================

app.include_router(m1_login.router,          prefix="/api/auth",       tags=["M1 登录认证"])
app.include_router(m2_admin_maintenance.router, prefix="/api/admin",   tags=["M2 基础数据维护"])
app.include_router(m3_schedule.router,       prefix="/api/schedules",  tags=["M3 排班管理"])
app.include_router(m4_registration.router,   prefix="/api/registrations", tags=["M4 挂号"])
app.include_router(m5_outpatient.router,     prefix="/api/outpatient", tags=["M5 门诊接诊与处方"])
app.include_router(m6_payment.router,        prefix="/api/payment",    tags=["M6 缴费与查看"])
app.include_router(m7_admission.router,      prefix="/api/admission",  tags=["M7 住院登记"])
app.include_router(m8_daily_rounds.router,   prefix="/api/rounds",     tags=["M8 每日查房"])
app.include_router(m9_discharge.router,      prefix="/api/discharge",  tags=["M9 出院结算"])
app.include_router(stats.router,             prefix="/api/stats",      tags=["统计查询"])

# 前端静态文件（后续放置 HTML/JS/CSS）
# 访问方式：http://127.0.0.1:8000/static/index.html
app.mount("/static", StaticFiles(directory="static", html=True), name="static")


@app.get("/")
def root():
    """根路径重定向到 Swagger 文档。"""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/docs")
