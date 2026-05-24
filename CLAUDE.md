# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Hospital Management Information System (医院管理信息系统) — a university database systems course project. The goal is to design and implement a MySQL relational database for hospital operations, covering outpatient and inpatient workflows.

- **Course**: 数据库系统原理与实践 (Database Systems Principles and Practice)
- **Deadline**: 2026-06-14
- **Team size**: 2–4 people
- **Deliverables**: Lab report (60%), source code (30%), participation (10%)

## Key Documents

- `../sql/2026《数据库系统原理与实践》综合设计实验指导书.docx` — Official lab guide with requirements, grading criteria, and report format
- `../sql/hospital_project_background.html` — Project background, scope definition, and user roles (Ch1.1)
- `../sql/hospital_business_process_analysis.html` — 6 business process flows with step-by-step entity/attribute involvement (Ch1.2)
- `../sql/hospital_entity_summary_table.html` — Complete entity-attribute table: 14 entities with PK/FK/nullable/enum annotations (Ch1.4)
- `../sql/hospital_business_rules.html` — 31 business rules across 8 categories extracted from the business processes (Ch1.5)
- `../sql/hospital_entity_relationships.html` — 22 FK relationships with cardinality, FK field mapping, and special design notes (Ch2.2)
- `../sql/数据库大作业——关系型数据库实例《英雄联盟》.pdf` — Reference example of a completed database project (League of Legends theme)

## Domain Model: 14 Entities

**Foundation (2)**: Department (科室), Account (账号表)
**Outpatient (5)**: Doctor (医生), Schedule (排班), Patient (病人), Registration (挂号), OutpatientPrescription (门诊处方)
**Pharmacy (2)**: Medicine (药品), PrescriptionDetail (处方明细)
**Inpatient (5)**: Ward (病房), Bed (病床), AdmissionFile (住院档案), InpatientRecord (住院记录), InpatientPrescription (住院处方)

Simplifications from the original 16-entity design:
- **TitleFeeRate removed** — `诊疗费` is now a direct attribute of `Doctor`. The fee is determined by the doctor's title (职称); same title = same fee.
- **Clinic removed** — `诊室` is now a varchar field in `Schedule` (nullable, only used for outpatient shifts). Room conflict detection (same room + same time) is still enforced at the application level. The mapping of which rooms belong to which department is a static reference table, not a database entity.

Key design decision: `PrescriptionDetail` serves both outpatient and inpatient prescriptions via a `处方类型` (prescription type) enum field.

Critical distinction: **AdmissionFile** (住院档案) is created once per hospital stay. **InpatientRecord** (住院记录) is created daily during rounds — one AdmissionFile has many InpatientRecords.

## Core Business Processes

1. **Outpatient registration & consultation** — patient login → select department/doctor → register → wait → doctor consultation
2. **Prescription & payment** — doctor prescribes (filtering out-of-stock meds) → patient pays (consultation fee = doctor title rate, drug fee = Σ qty × unit price) → pharmacy dispenses
3. **Admission** — outpatient diagnosis recommends admission → assign ward/bed → pay deposit → create AdmissionFile → update patient/bed status
4. **Daily rounds** — doctor ward-round schedule (no time conflict with outpatient) → create daily InpatientRecord → prescribe inpatient meds → calculate daily cost (bed fee + drug fee) → deduct from deposit
5. **Discharge** — set discharge time → aggregate all daily costs → settle deposit balance → release bed → reset statuses
6. **Admin maintenance & statistics** — CRUD on departments/doctors/medicines, manage schedules with conflict detection, workload stats

## Three User Roles

- **Admin** — maintain base data (departments, doctors, medicines), manage schedules
- **Doctor** — view own schedule, consult patients, prescribe, conduct ward rounds
- **Patient** — register, view prescriptions, pay fees, view medical history and cost details

## Tech Stack

- **Database**: MySQL
- **Backend/frontend**: No constraints — choose based on team familiarity. UI has no specific requirements; functional correctness is primary.
- **Report**: Word or PDF format, following textbook Chapter 6 structure for database design documentation

## Project Structure

```
hospital_mis/
├── main.py              # FastAPI entry — imports all routers
├── config.py            # DB_CONFIG + server host/port
├── db.py                # query / query_one / execute / transaction
├── requirements.txt     # fastapi, uvicorn, pymysql, pydantic
├── init_db.py           # Drop & recreate all 14 tables from DDL
├── seed_data.py         # Insert test data covering all 6 business flows
├── hospital_ddl.sql     # Complete DDL (source of truth for schema)
├── routers/             # 10 route modules (M1–M9 + stats)
├── schemas/             # 12 Pydantic schema modules
├── sql/                 # 10 SQL reference files (referenced by docs)
├── docs/                # 开发思路文档.md + 开发日志.md
└── static/              # Frontend static files
```

Design documents (HTML, Word) are in `../sql/` — the original project design folder.
