# 化工厂危险废物管理系统 - 系统文档

## 1. 系统概述

### 1.1 系统简介

本系统是一个**化工厂危险废物管理系统**（Chemical Plant Hazardous Waste Management System），旨在实现危险废物从产生到处置的全生命周期管理。系统采用**RBAC（基于角色的访问控制）**架构，配合**服务端强制状态机**确保废物处理流程的合规性，并提供**审计日志**、**规则告警**、**报表导出**等核心功能。

### 1.2 系统目标

| 目标 | 描述 |
|------|------|
| 合规管理 | 确保危险废物处理符合环保法规要求 |
| 流程控制 | 通过状态机强制规范废物批次的生命周期流转 |
| 安全审计 | 完整记录所有操作，支持追溯和合规审查 |
| 风险预警 | 基于规则的告警机制，及时发现潜在风险 |
| 数据集成 | 提供REST API支持与ERP/LIMS等外部系统对接 |

---

## 2. 系统架构

### 2.1 架构设计

```
┌─────────────────────────────────────────────────────────────────┐
│                        前端层 (Frontend)                        │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐  │
│  │  Admin  │ │   EHS   │ │Operator │ │Auditor  │ │  Public │  │
│  │ Console │ │ Dashboard│ │ Console │ │ Console │ │  Trace  │  │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘  │
└──────────────────┬──────────────────────────────────────────────┘
                   │ HTTP/HTTPS
                   ▼
┌─────────────────────────────────────────────────────────────────┐
│                        应用层 (Application)                      │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐│
│  │  Auth    │ │  Batch   │ │  Alert   │ │  Audit   │ │   API    ││
│  │  Module  │ │  Module  │ │  Module  │ │  Module  │ │  Module  ││
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘│
└──────────────────┬──────────────────────────────────────────────┘
                   │ SQLAlchemy ORM
                   ▼
┌─────────────────────────────────────────────────────────────────┐
│                      数据层 (Data Layer)                        │
│                    SQLite Database (hazard_waste.db)            │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 技术栈

| 层级 | 技术 | 版本 |
|------|------|------|
| 框架 | Flask | 2.x |
| ORM | SQLAlchemy | 2.x |
| 认证 | Flask-Login | 0.6.x |
| 密码 | Werkzeug Security | 2.x |
| 部署 | Docker / Docker Compose | 20.x |
| 测试 | pytest | 7.x |

---

## 3. 功能模块

### 3.1 模块概览

| 模块 | 功能描述 |
|------|----------|
| **认证模块** | 用户注册、登录、权限验证 |
| **批次管理** | 废物批次的创建、状态流转、查询 |
| **状态机** | 服务端强制的合法状态转换规则 |
| **告警引擎** | 基于规则的告警检测与通知 |
| **审计日志** | 完整记录所有操作行为 |
| **报表导出** | CSV/PDF格式的报表生成 |
| **QR溯源** | 公开可访问的废物批次追溯 |
| **REST API** | 外部系统集成接口 |

### 3.2 角色权限 (RBAC)

| 角色 | 用户名（预置） | 密码 | 权限描述 |
|------|---------------|------|----------|
| **Administrator** | `admin` | `Admin123!` | 用户管理、告警规则、全量数据访问、审计、导出 |
| **Environmental Safety Officer** | `es_officer` | `Eso123!` | 合规监督、告警处理、状态流转、导出、审计 |
| **Operator** | `operator1` | `Op123!` | 创建/编辑批次、状态流转、转移记录 |
| **Auditor** | `auditor1` | `Audit123!` | 只读访问、审计日志、报表导出 |

### 3.3 状态机流程

```
registered ──► stored ──► pending_transfer ──► in_transit 
     │                                        │
     │                                        ▼
     │                              received_by_disposal_vendor
     │                                        │
     │                                        ▼
     │                                    disposed ──► archived
     └─────────────────────────────────────────────────┘
```

**合法状态转换表**：

| 当前状态 | 允许转换到 |
|----------|-----------|
| `registered` | `stored` |
| `stored` | `pending_transfer` |
| `pending_transfer` | `in_transit` |
| `in_transit` | `received_by_disposal_vendor` |
| `received_by_disposal_vendor` | `disposed` |
| `disposed` | `archived` |
| `archived` | 无（终端状态） |

---

## 4. 数据模型

### 4.1 核心实体关系图 (ERD)

```
┌──────────┐      1:N      ┌──────────────┐      1:N      ┌──────────────────┐
│  User    │◄──────────────│ WasteBatch   │──────────────►│ WasteStatusHistory│
├──────────┤               ├──────────────┤               ├──────────────────┤
│ id       │               │ id           │               │ id               │
│ username │               │ batch_code   │               │ waste_batch_id   │
│ role     │               │ name         │               │ from_status      │
│ email    │               │ category     │               │ to_status        │
│ status   │               │ quantity     │               │ changed_by       │
└──────────┘               │ hazard_level │               └──────────────────┘
                           │ current_status│
                           │ created_by   │      1:N      ┌─────────────┐
                           └──────────────┘──────────────►│TransferRecord│
                                                          ├─────────────┤
                                                          │ id          │
                                                          │ vendor      │
                                                          │ destination │
                                                          └─────────────┘
                                      │
                                      │ 1:N
                                      ▼
                           ┌──────────────┐      1:N      ┌─────────────┐
                           │  AlertRule   │──────────────►│ AlertEvent  │
                           ├──────────────┤               ├─────────────┤
                           │ id           │               │ id          │
                           │ rule_name    │               │ rule_id     │
                           │ rule_type    │               │ severity    │
                           │ threshold    │               │ status      │
                           │ enabled      │               └─────────────┘
                           └──────────────┘
```

### 4.2 实体详细说明

#### 4.2.1 User（用户）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | Integer | PK | 用户唯一标识 |
| `username` | String(80) | Unique, Not Null | 用户名 |
| `password_hash` | String(255) | Not Null | 密码哈希 |
| `role` | String(32) | Not Null | 角色：administrator/es_officer/operator/auditor |
| `email` | String(120) | Unique, Not Null | 邮箱 |
| `status` | String(20) | Default: active | 状态：active/disabled |
| `created_at` | DateTime | Default: now | 创建时间 |

#### 4.2.2 WasteBatch（废物批次）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | Integer | PK | 批次唯一标识 |
| `batch_code` | String(64) | Unique, Not Null | 批次编码 |
| `name` | String(200) | Not Null | 废物名称 |
| `category` | String(100) | Not Null | 废物类别 |
| `source_unit` | String(120) | Not Null | 产生部门 |
| `quantity` | Float | Not Null | 数量 |
| `unit` | String(32) | Default: kg | 单位 |
| `storage_location` | String(120) | Not Null | 存储位置 |
| `hazard_level` | String(32) | Default: low | 危险等级：low/medium/high/critical |
| `responsible_person` | String(120) | Not Null | 责任人 |
| `current_status` | String(64) | Default: registered | 当前状态 |
| `trace_code` | String(64) | Unique, Not Null | 溯源码 |
| `created_by` | Integer | FK → User | 创建者 |
| `created_at` | DateTime | Default: now | 创建时间 |
| `updated_at` | DateTime | Auto-update | 更新时间 |

#### 4.2.3 AlertRule（告警规则）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | Integer | PK | 规则唯一标识 |
| `rule_name` | String(120) | Not Null | 规则名称 |
| `rule_type` | String(64) | Not Null | 规则类型 |
| `threshold` | String(255) | - | 阈值配置 |
| `severity` | String(32) | Default: warning | 严重程度 |
| `enabled` | Integer | Default: 1 | 是否启用 |

**支持的规则类型**：

| 规则类型 | 说明 | 阈值示例 |
|----------|------|----------|
| `storage_exceeds_days` | 存储超期检测 | 30（天数） |
| `hazard_minimum_level` | 危险等级阈值 | high |
| `remark_keyword` | 备注关键词检测 | dangerous,critical |
| `location_capacity` | 存储位置容量 | 1000（kg） |
| `inactive_batch_days` | 批次长期未操作 | 14（天数） |

---

## 5. API 接口

### 5.1 认证要求

| 接口类型 | 认证方式 |
|----------|----------|
| 外部API | `X-API-Key` 请求头 |
| 会话API | Cookie Session |

### 5.2 接口列表

| 端点 | 方法 | 认证 | 描述 |
|------|------|------|------|
| `/api/v1/health` | GET | 无 | 健康检查 |
| `/api/v1/batches` | GET | API Key | 获取批次列表 |
| `/api/v1/batches/<code>` | GET | API Key | 获取批次详情 |
| `/api/v1/integration/erp/person` | POST | API Key | Mock ERP人员查询 |
| `/api/v1/integration/lims/result` | POST | API Key | Mock LIMS结果回调 |
| `/api/v1/me` | GET | Session | 当前用户信息 |

### 5.3 响应格式

**成功响应**：
```json
{
  "status": "ok",
  "data": { ... }
}
```

**错误响应**：
```json
{
  "error": "描述信息"
}
```

---

## 6. 部署与配置

### 6.1 环境变量

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `SECRET_KEY` | dev-change-me-hazwaste-2026 | 会话密钥 |
| `DATABASE_URL` | sqlite:///hazard_waste.db | 数据库连接 |
| `EXTERNAL_API_KEY` | demo-hazwaste-api-key | API密钥 |
| `REGISTRATION_INVITE_ES` | UCD-ES-2026 | ES角色邀请码 |
| `REGISTRATION_INVITE_AUDITOR` | UCD-AUDIT-2026 | 审计员邀请码 |

### 6.2 本地运行

```bash
cd webproject0
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python run.py
```

访问：http://127.0.0.1:5001

### 6.3 Docker 部署

```bash
docker compose up --build
```

---

## 7. 目录结构

```
webproject0/
├── app/                          # 应用核心代码
│   ├── routes/                   # 路由定义
│   │   ├── auth.py               # 认证路由
│   │   ├── batches.py            # 批次管理路由
│   │   ├── admin.py              # 管理员路由
│   │   ├── alerts.py             # 告警路由
│   │   ├── api_v1.py             # REST API
│   │   └── ...                   # 其他路由
│   ├── utils/                    # 工具函数
│   │   ├── state_machine.py      # 状态机逻辑
│   │   ├── alert_engine.py       # 告警引擎
│   │   ├── rbac.py               # 权限控制
│   │   └── ...                   # 其他工具
│   ├── models.py                 # 数据模型
│   ├── forms.py                  # 表单定义
│   └── __init__.py               # 应用工厂
├── templates/                    # 前端模板
├── static/                       # 静态资源
├── tests/                        # 测试代码
├── config.py                     # 配置文件
├── run.py                        # 启动脚本
├── docker-compose.yml            # Docker配置
└── requirements.txt              # 依赖列表
```

---

## 附录：预置用户

| 角色 | 用户名 | 密码 |
|------|--------|------|
| Administrator | admin | Admin123! |
| Environmental Safety Officer | es_officer | Eso123! |
| Operator | operator1 | Op123! |
| Operator | operator2 | Op123! |
| Auditor | auditor1 | Audit123! |
