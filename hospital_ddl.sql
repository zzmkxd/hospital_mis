-- ============================================================
-- 医院管理信息系统 DDL
-- 共 14 个实体（排除 诊室Clinic、职称费率表TitleFeeRate）
-- 数据库: MySQL 8.0+
-- ============================================================

CREATE DATABASE IF NOT EXISTS hospital_mis
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_unicode_ci;
USE hospital_mis;


-- ============================================================
-- 1. 基础管理（2个实体）
-- ============================================================

-- 1.1 科室表
CREATE TABLE department (
    dept_id      INT           NOT NULL AUTO_INCREMENT  COMMENT '科室ID',
    dept_name    VARCHAR(50)   NOT NULL                 COMMENT '科室名称，如「内科」「妇产科」',
    dept_type    ENUM('门诊','住院','两者兼有') NOT NULL  COMMENT '科室类型',
    phone        VARCHAR(20)   DEFAULT NULL             COMMENT '联系电话',
    PRIMARY KEY (dept_id)
) ENGINE=InnoDB COMMENT='科室';

-- 1.2 账号表
CREATE TABLE account (
    account_id   INT           NOT NULL AUTO_INCREMENT  COMMENT '账号ID',
    ref_id       INT           NOT NULL                 COMMENT '关联ID，指向医生ID或病案号',
    role         ENUM('医生','病人','管理员') NOT NULL  COMMENT '角色',
    password_hash VARCHAR(255) NOT NULL                 COMMENT '密码哈希',
    PRIMARY KEY (account_id)
) ENGINE=InnoDB COMMENT='账号';


-- ============================================================
-- 2. 门诊部（5个实体）
-- ============================================================

-- 2.1 医生表
CREATE TABLE doctor (
    doctor_id    INT           NOT NULL AUTO_INCREMENT  COMMENT '医生ID',
    name         VARCHAR(30)   NOT NULL                 COMMENT '姓名',
    gender       ENUM('男','女') DEFAULT NULL           COMMENT '性别',
    title        VARCHAR(30)   DEFAULT NULL             COMMENT '职称，如「主任医师」「主治医师」',
    consultation_fee DECIMAL(10,2) NOT NULL              COMMENT '诊疗费，按职称确定，同职称费用相同',
    phone        VARCHAR(20)   DEFAULT NULL             COMMENT '联系电话',
    dept_id      INT           NOT NULL                 COMMENT '所属科室ID',
    PRIMARY KEY (doctor_id),
    CONSTRAINT fk_doctor_dept FOREIGN KEY (dept_id) REFERENCES department(dept_id)
) ENGINE=InnoDB COMMENT='医生';

-- 2.2 排班表
CREATE TABLE schedule (
    schedule_id  INT           NOT NULL AUTO_INCREMENT  COMMENT '排班ID',
    doctor_id    INT           NOT NULL                 COMMENT '医生ID',
    sched_date   DATE          NOT NULL                 COMMENT '排班日期',
    start_time   TIME          NOT NULL                 COMMENT '开始时间',
    end_time     TIME          NOT NULL                 COMMENT '结束时间',
    sched_type   ENUM('门诊坐诊','住院巡诊') NOT NULL  COMMENT '排班类型',
    clinic        VARCHAR(20)  DEFAULT NULL             COMMENT '诊室，如「内科诊室01」（门诊坐诊时填写，住院巡诊时为NULL）',
    PRIMARY KEY (schedule_id),
    CONSTRAINT fk_schedule_doctor FOREIGN KEY (doctor_id) REFERENCES doctor(doctor_id)
) ENGINE=InnoDB COMMENT='排班';

-- 2.3 病人表
CREATE TABLE patient (
    case_no       INT           NOT NULL AUTO_INCREMENT  COMMENT '病案号',
    name          VARCHAR(30)   NOT NULL                 COMMENT '姓名',
    gender        ENUM('男','女') DEFAULT NULL           COMMENT '性别',
    age           TINYINT       DEFAULT NULL             COMMENT '年龄',
    address       VARCHAR(200)  DEFAULT NULL             COMMENT '地址',
    phone         VARCHAR(20)   DEFAULT NULL             COMMENT '电话',
    is_inpatient  ENUM('是','否') NOT NULL DEFAULT '否'  COMMENT '是否住院',
    ward_id       INT           DEFAULT NULL             COMMENT '当前入住病房ID',
    bed_id        INT           DEFAULT NULL             COMMENT '当前分配床位ID',
    PRIMARY KEY (case_no)
) ENGINE=InnoDB COMMENT='病人';

-- 2.4 挂号表
CREATE TABLE registration (
    reg_id        INT           NOT NULL AUTO_INCREMENT  COMMENT '挂号ID',
    case_no       INT           NOT NULL                 COMMENT '病案号',
    doctor_id     INT           NOT NULL                 COMMENT '医生ID（冗余，方便直接查询）',
    schedule_id   INT           NOT NULL                 COMMENT '排班ID',
    reg_date      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '挂号日期',
    reg_type      ENUM('初诊','复诊') NOT NULL          COMMENT '挂号类型',
    reg_status    ENUM('待就诊','已就诊','已取消') NOT NULL DEFAULT '待就诊' COMMENT '挂号状态',
    PRIMARY KEY (reg_id),
    CONSTRAINT fk_reg_case      FOREIGN KEY (case_no)    REFERENCES patient(case_no),
    CONSTRAINT fk_reg_doctor    FOREIGN KEY (doctor_id)  REFERENCES doctor(doctor_id),
    CONSTRAINT fk_reg_schedule  FOREIGN KEY (schedule_id) REFERENCES schedule(schedule_id)
) ENGINE=InnoDB COMMENT='挂号';

-- 2.5 门诊处方表
CREATE TABLE outpatient_prescription (
    presc_id      INT           NOT NULL AUTO_INCREMENT  COMMENT '处方ID',
    reg_id        INT           NOT NULL                 COMMENT '挂号ID',
    doctor_id     INT           NOT NULL                 COMMENT '医生ID（处方签名人）',
    presc_time    DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '开方时间',
    symptom_desc  TEXT          DEFAULT NULL             COMMENT '症状描述',
    pay_status    ENUM('待支付','已支付') NOT NULL DEFAULT '待支付' COMMENT '支付状态',
    PRIMARY KEY (presc_id),
    CONSTRAINT fk_opresc_reg    FOREIGN KEY (reg_id)     REFERENCES registration(reg_id),
    CONSTRAINT fk_opresc_doctor FOREIGN KEY (doctor_id)  REFERENCES doctor(doctor_id)
) ENGINE=InnoDB COMMENT='门诊处方';


-- ============================================================
-- 3. 药品（2个实体）
-- ============================================================

-- 3.1 药品表
CREATE TABLE medicine (
    medicine_id   INT           NOT NULL AUTO_INCREMENT  COMMENT '药品ID',
    med_name      VARCHAR(100)  NOT NULL                 COMMENT '药品名称',
    specification VARCHAR(50)   DEFAULT NULL             COMMENT '规格，如「500mg/片」',
    unit          VARCHAR(20)   DEFAULT NULL             COMMENT '单位，如「片」「瓶」「支」',
    unit_price    DECIMAL(10,2) NOT NULL                 COMMENT '单价',
    stock_qty     INT           NOT NULL DEFAULT 0       COMMENT '库存数量',
    PRIMARY KEY (medicine_id)
) ENGINE=InnoDB COMMENT='药品';

-- 3.2 处方明细表
CREATE TABLE prescription_detail (
    detail_id     INT           NOT NULL AUTO_INCREMENT  COMMENT '明细ID',
    presc_id      INT           NOT NULL                 COMMENT '处方ID',
    presc_type    ENUM('门诊','住院') NOT NULL           COMMENT '处方类型',
    medicine_id   INT           NOT NULL                 COMMENT '药品ID',
    qty           INT           NOT NULL                 COMMENT '数量',
    usage_inst    VARCHAR(200)  DEFAULT NULL             COMMENT '用法，如「每日三次，每次一片」',
    PRIMARY KEY (detail_id),
    CONSTRAINT fk_detail_medicine FOREIGN KEY (medicine_id) REFERENCES medicine(medicine_id)
) ENGINE=InnoDB COMMENT='处方明细';


-- ============================================================
-- 4. 住院部（5个实体）
-- ============================================================

-- 4.1 病房表
CREATE TABLE ward (
    ward_id       INT           NOT NULL AUTO_INCREMENT  COMMENT '病房ID',
    ward_no       VARCHAR(20)   NOT NULL                 COMMENT '病房编号，如「外科301」',
    dept_id       INT           NOT NULL                 COMMENT '所属科室ID',
    location      VARCHAR(100)  DEFAULT NULL             COMMENT '地点描述',
    charge_rate   DECIMAL(10,2) NOT NULL                 COMMENT '收费标准（每日床位费）',
    total_beds    INT           NOT NULL                 COMMENT '总床位数',
    occupied_cnt  INT           NOT NULL DEFAULT 0       COMMENT '当前入住人数',
    PRIMARY KEY (ward_id),
    CONSTRAINT fk_ward_dept FOREIGN KEY (dept_id) REFERENCES department(dept_id)
) ENGINE=InnoDB COMMENT='病房';

-- 4.2 病床表
CREATE TABLE bed (
    bed_id        INT           NOT NULL AUTO_INCREMENT  COMMENT '病床ID',
    ward_id       INT           NOT NULL                 COMMENT '所属病房ID',
    bed_no        VARCHAR(10)   NOT NULL                 COMMENT '床位号，如「01」「02」',
    bed_status    ENUM('空闲','占用') NOT NULL DEFAULT '空闲' COMMENT '床位状态',
    PRIMARY KEY (bed_id),
    CONSTRAINT fk_bed_ward FOREIGN KEY (ward_id) REFERENCES ward(ward_id)
) ENGINE=InnoDB COMMENT='病床';

-- 病人表对病房/床位的FK（延迟添加，避免循环依赖）
ALTER TABLE patient
  ADD CONSTRAINT fk_patient_ward FOREIGN KEY (ward_id) REFERENCES ward(ward_id),
  ADD CONSTRAINT fk_patient_bed  FOREIGN KEY (bed_id)  REFERENCES bed(bed_id);

-- 4.3 住院档案表
CREATE TABLE admission_file (
    file_no       INT           NOT NULL AUTO_INCREMENT  COMMENT '档案号',
    case_no       INT           NOT NULL                 COMMENT '病案号',
    doctor_id     INT           NOT NULL                 COMMENT '主治医生ID',
    ward_id       INT           NOT NULL                 COMMENT '病房ID',
    bed_id        INT           NOT NULL                 COMMENT '床位ID',
    admit_time    DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '入院时间',
    discharge_time DATETIME    DEFAULT NULL             COMMENT '出院时间（NULL表示仍在院）',
    deposit_balance DECIMAL(12,2) NOT NULL DEFAULT 0    COMMENT '预交金余额',
    PRIMARY KEY (file_no),
    CONSTRAINT fk_af_case   FOREIGN KEY (case_no)   REFERENCES patient(case_no),
    CONSTRAINT fk_af_doctor FOREIGN KEY (doctor_id) REFERENCES doctor(doctor_id),
    CONSTRAINT fk_af_ward   FOREIGN KEY (ward_id)   REFERENCES ward(ward_id),
    CONSTRAINT fk_af_bed    FOREIGN KEY (bed_id)    REFERENCES bed(bed_id)
) ENGINE=InnoDB COMMENT='住院档案';

-- 4.4 住院记录表
CREATE TABLE inpatient_record (
    record_id     INT           NOT NULL AUTO_INCREMENT  COMMENT '记录ID',
    file_no       INT           NOT NULL                 COMMENT '档案号',
    record_date   DATE          NOT NULL                 COMMENT '记录日期',
    treatment_desc TEXT         DEFAULT NULL             COMMENT '治疗方案描述',
    daily_fee     DECIMAL(12,2) NOT NULL DEFAULT 0       COMMENT '当日费用（床位费+药费）',
    PRIMARY KEY (record_id),
    CONSTRAINT fk_ir_file FOREIGN KEY (file_no) REFERENCES admission_file(file_no)
) ENGINE=InnoDB COMMENT='住院记录';

-- 4.5 住院处方表
CREATE TABLE inpatient_prescription (
    presc_id      INT           NOT NULL AUTO_INCREMENT  COMMENT '处方ID',
    record_id     INT           NOT NULL                 COMMENT '住院记录ID',
    doctor_id     INT           NOT NULL                 COMMENT '主治医生ID',
    presc_time    DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '开方时间',
    PRIMARY KEY (presc_id),
    CONSTRAINT fk_ipresc_record FOREIGN KEY (record_id) REFERENCES inpatient_record(record_id),
    CONSTRAINT fk_ipresc_doctor FOREIGN KEY (doctor_id) REFERENCES doctor(doctor_id)
) ENGINE=InnoDB COMMENT='住院处方';
