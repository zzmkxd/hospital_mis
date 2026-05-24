# 医院管理信息系统 — 部署与运行指南

> 数据库系统原理与实践课程设计  
> FastAPI + MySQL + 原生 JS SPA

---

## 目录

1. [环境要求](#1-环境要求)
2. [快速启动（5 分钟）](#2-快速启动5-分钟)
3. [详细步骤](#3-详细步骤)
4. [测试账号](#4-测试账号)
5. [访问地址](#5-访问地址)
6. [业务流程验证](#6-业务流程验证)
7. [端到端自动验证](#7-端到端自动验证)
8. [常见问题](#8-常见问题)
9. [项目结构](#9-项目结构)

---

## 1. 环境要求

| 软件 | 最低版本 | 说明 |
|------|----------|------|
| Python | 3.10+ | 后端运行环境 |
| MySQL | 8.0+ | 数据库 |
| pip | 最新即可 | Python 包管理器 |

---

## 2. 快速启动（3 分钟）

**方式一：.env 文件（推荐，无需修改代码）**

```bash
# 第一步：创建 .env 文件，填入你的 MySQL 密码
echo DB_PASSWORD=你的密码 > .env

# 第二步：安装依赖
pip install -r requirements.txt

# 第三步：初始化数据库 + 导入测试数据
python init_db.py
python seed_data.py

# 第四步：启动
uvicorn main:app --host 127.0.0.1 --port 8000

# 第五步：浏览器打开
# http://127.0.0.1:8000/static/index.html
```

**方式二：设置环境变量**

```bash
# Windows (CMD):     set DB_PASSWORD=你的密码
# Windows (PowerShell): $env:DB_PASSWORD="你的密码"
# Linux/Mac:         export DB_PASSWORD=你的密码
```

然后同上从第二步开始执行。

**方式三：直接改 `config.py` 第 28 行**

```python
"password": "你的MySQL密码",
```

然后同上从第二步开始执行。

---

## 3. 详细步骤

### 3.1 确保 MySQL 已启动

Windows 下打开服务管理器确认 MySQL 服务正在运行。或执行：

```bash
mysql -u root -p -e "SELECT 1"
```

如果提示 `mysql: command not found`，请将 MySQL 的 `bin` 目录加入系统 PATH。

### 3.2 配置数据库密码

**只需改一处**。三种方式任选：

**方式一：创建 `.env` 文件（推荐，不修改代码）**

```bash
echo DB_PASSWORD=你的密码 > .env
```

`config.py` 会通过 `python-dotenv` 自动加载 `.env` 文件。参考 `.env.example` 模板。

**方式二：设置环境变量**

| 系统 | 命令 |
|------|------|
| Windows CMD | `set DB_PASSWORD=你的密码` |
| Windows PowerShell | `$env:DB_PASSWORD="你的密码"` |
| Linux / Mac | `export DB_PASSWORD=你的密码` |

**方式三：直接改 `config.py` 第 28 行**

```python
"password": "你的MySQL密码",
```

所有脚本（`init_db.py`、`seed_data.py`、后端路由）都统一从 `config.py` 读取密码。

### 3.3 安装依赖

```bash
pip install fastapi uvicorn pymysql pydantic
```

或者从 requirements.txt 安装：
```bash
pip install -r requirements.txt
```

### 3.4 初始化数据库

```bash
python init_db.py
```

这一步会：
1. 删除旧的 `hospital_mis` 数据库（如果存在）
2. 创建新的 `hospital_mis` 数据库
3. 执行 `hospital_ddl.sql`，建立全部 14 张表

成功输出：`14 tables created`

### 3.5 导入测试数据

```bash
python seed_data.py
```

这一步会插入覆盖全部 6 条业务流程的测试数据：
- 3 个科室、5 个医生、3 个病房、10 个床位
- 3 个病人、5 种药品、5 条排班
- 3 条挂号记录、1 张门诊处方 + 2 条明细
- 1 份住院档案 + 对应的账号记录

### 3.6 启动服务

```bash
uvicorn main:app --host 127.0.0.1 --port 8000
```

看到以下输出表示启动成功：
```
Uvicorn running on http://127.0.0.1:8000
```

> **注意**：`uvicorn` 必须从 `hospital_mis/` 目录下执行，否则找不到 `routers` 等模块。

### 3.7 打开前端

浏览器访问：
```
http://127.0.0.1:8000/static/index.html
```

登录即可使用。

---

## 4. 测试账号

| 角色 | 账号 (ref_id) | 密码 | 说明 |
|------|--------------|------|------|
| 管理员 | `999` | `admin123` | 维护基础数据、排班、入院出院、统计 |
| 医生 | `1`（或 2~5） | `123456` | 门诊接诊、开处方、每日查房 |
| 病人 | `1`（或 2~3） | `123456` | 挂号、缴费、查看历史 |

---

## 5. 访问地址

| 地址 | 说明 |
|------|------|
| `http://127.0.0.1:8000/` | 自动跳转到 Swagger API 文档 |
| `http://127.0.0.1:8000/docs` | Swagger UI — 交互式 API 测试面板 |
| `http://127.0.0.1:8000/redoc` | ReDoc — API 文档 |
| `http://127.0.0.1:8000/static/index.html` | **前端页面**（从这里开始使用系统） |

---

## 6. 业务流程验证

用种子数据可以完整跑通以下链路：

### 门诊链（病人挂号 → 医生接诊 → 病人缴费）

```
1. 登录病人 (1 / 123456)
   → 挂号 → 选科室 → 选医生 → 确认挂号
2. 登录医生 (1 / 123456)
   → 工作台 → 接诊 → 选病人 → 添加药品 → 提交处方
3. 登录病人
   → 缴费 & 历史 → 待支付 → 查看费用 → 确认支付
```

### 住院链（入院 → 查房 → 出院）

```
1. 登录管理员 (999 / admin123)
   → 入院登记 → 选科室 → 选病房/床位 → 填病案号 → 确认入院
2. 登录医生
   → 每日查房 → 选病人 → 填治疗方案 → 加药品 → 提交
3. 登录管理员
   → 出院结算 → 选病人 → 查看费用汇总 → 确认出院
```

### 管理维护

```
管理员登录 → 科室/医生/药品增删改查 → 排班管理 → 统计报表
```

---

## 7. 端到端自动验证

除了手动测试，还提供了自动化验证脚本，一次命令跑通全部 6 条业务流程：

```bash
# 确保服务已启动，然后：
python verify_e2e.py
```

脚本覆盖：
- **流程 1**：登录（管理员 / 医生 / 病人三种角色）
- **流程 2**：管理员基础数据维护（科室/医生/药品 CRUD）
- **流程 3**：排班管理（含冲突检测 409）
- **流程 4**：门诊链路（挂号 → 接诊 → 开处方 → 缴费）
- **流程 5**：住院链路（入院 → 查房 → R21 重复查房拒绝 → 出院）
- **流程 6**：统计查询（5 类报表）

成功输出：`48/48 passed — ALL PASSED. 6 business flows verified successfully.`

> 每次运行前建议重置数据：`python init_db.py && python seed_data.py`，防止上一次运行的残留数据干扰。

---

## 8. 常见问题

### Q1: `ModuleNotFoundError: No module named 'fastapi'`

```bash
pip install fastapi uvicorn pymysql pydantic
```

### Q2: `pymysql.err.OperationalError: Access denied`

MySQL 密码不正确。三种方式解决：
1. 创建 `.env` 文件填入正确密码（推荐）：`echo DB_PASSWORD=你的密码 > .env`
2. 设置环境变量 `DB_PASSWORD`
3. 直接修改 `config.py` 第 28 行的 password

### Q3: `pymysql.err.InternalError: Unknown database 'hospital_mis'`

数据库还没创建。先执行：
```bash
python init_db.py
```

### Q4: 前端表格数据为空 / 列显示空白

可能是后端服务未启动或端口被占用。确认 `uvicorn` 正在运行，并访问 `http://127.0.0.1:8000/docs` 验证 API 是否正常。

### Q5: 中文在浏览器中显示乱码

确认 `index.html` 的 `<meta charset="UTF-8">` 声明存在，且浏览器编码设置为 UTF-8。

### Q6: 数据库中文乱码

`init_db.py` 已设置 `utf8mb4` 编码。如果仍有问题，检查 MySQL 的 `my.ini` 配置：
```ini
[mysqld]
character-set-server=utf8mb4
collation-server=utf8mb4_unicode_ci
```

### Q7: 端口 8000 被占用

Windows：
```bash
netstat -ano | findstr :8000
taskkill //F //PID <PID号>
```

Linux/Mac：
```bash
lsof -i :8000
kill -9 <PID>
```

或者换个端口启动：
```bash
uvicorn main:app --host 127.0.0.1 --port 8080
```

### Q8: 想重置数据

```bash
python init_db.py     # 删除并重建 14 张表
python seed_data.py   # 重新导入测试数据
```

---

## 9. 项目结构

```
hospital_mis/
├── README.md                # 本文件
├── .env.example             # 环境变量模板
├── .gitignore               # Git 忽略规则
├── main.py                  # FastAPI 入口
├── config.py                # 数据库连接、服务端口（支持 .env）
├── db.py                    # 数据库工具（query / execute / transaction）
├── requirements.txt         # Python 依赖
├── init_db.py               # 一键建库（执行 hospital_ddl.sql）
├── seed_data.py             # 测试数据初始化
├── verify_e2e.py            # 端到端自动验证（6 条业务流程，48 步）
├── hospital_ddl.sql         # 14 张表 DDL（数据源）
│
├── routers/                 # API 路由（10 个模块）
│   ├── m1_login.py          # M1 登录认证
│   ├── m2_admin_maintenance.py  # M2 科室/医生/药品 CRUD
│   ├── m3_schedule.py       # M3 排班管理 + 冲突检测
│   ├── m4_registration.py   # M4 挂号 + 初复诊判定
│   ├── m5_outpatient.py     # M5 门诊接诊与处方
│   ├── m6_payment.py        # M6 缴费与历史
│   ├── m7_admission.py      # M7 住院登记（5 步事务）
│   ├── m8_daily_rounds.py   # M8 每日查房（8 步事务）
│   ├── m9_discharge.py      # M9 出院结算（7 步事务）
│   └── stats.py             # 统计查询（5 类）
│
├── schemas/                 # Pydantic 请求/响应模型
├── sql/                     # SQL 参考文件（与路由三向对齐）
├── docs/                    # 开发思路文档 + 开发日志
│
└── static/                  # 前端 SPA
    ├── index.html           # 入口 HTML
    ├── css/style.css        # 全局样式
    └── js/
        ├── api.js           # fetch 封装
        ├── auth.js          # 登录态管理
        ├── router.js        # Hash 路由器
        ├── render-utils.js  # DOM 工具
        ├── app.js           # 路由注册 + 登录页
        ├── admin.js         # 管理员 8 页面
        ├── doctor.js        # 医生 3 页面
        └── patient.js       # 病人 3 页面
```

---

**数据库课程设计 · 2026**
