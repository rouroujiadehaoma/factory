# 化工厂危险废物管理系统 - 测试文档

## 1. 测试概述

### 1.1 测试目标

本文档定义了化工厂危险废物管理系统的测试策略、测试用例和测试流程，确保系统功能的正确性、安全性和可靠性。

### 1.2 测试范围

| 模块 | 测试内容 |
|------|----------|
| **认证模块** | 用户注册、登录、权限验证 |
| **批次管理** | 创建、编辑、查询废物批次 |
| **状态机** | 合法/非法状态转换验证 |
| **告警引擎** | 规则触发、告警生成、去重机制 |
| **审计日志** | 操作记录的完整性和准确性 |
| **API接口** | REST API功能和安全性 |
| **RBAC** | 角色权限隔离验证 |

### 1.3 测试环境

| 环境 | 配置 |
|------|------|
| 操作系统 | Linux / Windows / macOS |
| Python版本 | 3.8+ |
| 数据库 | SQLite (测试环境) |
| 测试框架 | pytest |

---

## 2. 测试策略

### 2.1 测试类型

| 测试类型 | 描述 | 覆盖范围 |
|----------|------|----------|
| **单元测试** | 测试单个函数/方法 | 状态机逻辑、告警规则、工具函数 |
| **集成测试** | 测试模块间协作 | 数据库操作、API接口 |
| **系统测试** | 端到端测试 | 完整业务流程 |
| **安全测试** | 权限验证 | RBAC、API认证 |

### 2.2 测试方法

- **黑盒测试**：验证功能是否符合需求规格
- **白盒测试**：验证内部逻辑正确性（状态机、告警引擎）
- **边界测试**：验证边界条件和异常情况

---

## 3. 测试用例

### 3.1 认证模块测试

#### 3.1.1 用户登录

| 用例ID | 测试场景 | 输入 | 预期结果 |
|--------|----------|------|----------|
| AUTH-001 | 有效凭证登录 | 用户名: admin, 密码: Admin123! | 登录成功，跳转仪表盘 |
| AUTH-002 | 无效密码登录 | 用户名: admin, 密码: WrongPass! | 登录失败，显示错误提示 |
| AUTH-003 | 不存在用户 | 用户名: nonexist, 密码: AnyPass! | 登录失败，显示错误提示 |
| AUTH-004 | 禁用用户登录 | 禁用用户凭证 | 登录失败，显示账户禁用提示 |
| AUTH-005 | 已登录用户访问登录页 | 已登录状态访问 /auth/login | 自动重定向到仪表盘 |

#### 3.1.2 用户注册

| 用例ID | 测试场景 | 输入 | 预期结果 |
|--------|----------|------|----------|
| AUTH-006 | Operator注册（无需邀请码） | 用户名、邮箱、密码、角色: operator | 注册成功 |
| AUTH-007 | ES Officer注册（正确邀请码） | 用户名、邮箱、密码、角色: es_officer、邀请码: UCD-ES-2026 | 注册成功 |
| AUTH-008 | ES Officer注册（错误邀请码） | 用户名、邮箱、密码、角色: es_officer、邀请码: WrongCode | 注册失败 |
| AUTH-009 | Auditor注册（正确邀请码） | 用户名、邮箱、密码、角色: auditor、邀请码: UCD-AUDIT-2026 | 注册成功 |
| AUTH-010 | 重复用户名注册 | 已存在的用户名 | 注册失败，显示用户名已存在 |
| AUTH-011 | 重复邮箱注册 | 已存在的邮箱 | 注册失败，显示邮箱已存在 |

---

### 3.2 批次管理测试

#### 3.2.1 批次创建

| 用例ID | 测试场景 | 输入 | 预期结果 |
|--------|----------|------|----------|
| BATCH-001 | 创建有效批次 | 完整必填字段 | 批次创建成功，状态为 registered |
| BATCH-002 | 缺少必填字段 | 缺少名称或类别 | 创建失败，显示验证错误 |
| BATCH-003 | 重复批次编码 | 已存在的 batch_code | 创建失败，显示编码重复 |
| BATCH-004 | 非法危险等级 | hazard_level: invalid | 创建失败，显示验证错误 |

#### 3.2.2 批次查询

| 用例ID | 测试场景 | 输入 | 预期结果 |
|--------|----------|------|----------|
| BATCH-005 | 查询所有批次 | 无参数 | 返回批次列表 |
| BATCH-006 | 按状态筛选 | status: stored | 返回所有 stored 状态批次 |
| BATCH-007 | 按危险等级筛选 | hazard_level: high | 返回高危险等级批次 |
| BATCH-008 | 查询不存在批次 | batch_code: NOTEXIST | 返回空结果或404 |

---

### 3.3 状态机测试

#### 3.3.1 合法状态转换

| 用例ID | 测试场景 | 当前状态 | 目标状态 | 预期结果 |
|--------|----------|----------|----------|----------|
| SM-001 | registered → stored | registered | stored | 转换成功 |
| SM-002 | stored → pending_transfer | stored | pending_transfer | 转换成功 |
| SM-003 | pending_transfer → in_transit | pending_transfer | in_transit | 转换成功 |
| SM-004 | in_transit → received_by_disposal_vendor | in_transit | received_by_disposal_vendor | 转换成功 |
| SM-005 | received_by_disposal_vendor → disposed | received_by_disposal_vendor | disposed | 转换成功 |
| SM-006 | disposed → archived | disposed | archived | 转换成功 |

#### 3.3.2 非法状态转换

| 用例ID | 测试场景 | 当前状态 | 目标状态 | 预期结果 |
|--------|----------|----------|----------|----------|
| SM-007 | 跳过中间状态 | registered | pending_transfer | 转换失败 |
| SM-008 | 反向转换 | stored | registered | 转换失败 |
| SM-009 | 终端状态转换 | archived | stored | 转换失败 |
| SM-010 | 无效目标状态 | stored | invalid_status | 转换失败 |

---

### 3.4 告警引擎测试

#### 3.4.1 告警规则触发

| 用例ID | 测试场景 | 规则类型 | 条件 | 预期结果 |
|--------|----------|----------|------|----------|
| ALERT-001 | 存储超期检测 | storage_exceeds_days | 批次存储超过阈值天数 | 生成告警事件 |
| ALERT-002 | 危险等级阈值 | hazard_minimum_level | 批次危险等级 >= 阈值 | 生成告警事件 |
| ALERT-003 | 备注关键词检测 | remark_keyword | 备注包含关键词 | 生成告警事件 |
| ALERT-004 | 存储容量超限 | location_capacity | 位置总容量超过阈值 | 生成告警事件 |
| ALERT-005 | 长期未操作检测 | inactive_batch_days | 批次超过阈值天数未更新 | 生成告警事件 |

#### 3.4.2 告警去重

| 用例ID | 测试场景 | 输入 | 预期结果 |
|--------|----------|------|----------|
| ALERT-006 | 相同告警重复触发 | 同一规则+批次+消息多次触发 | 只生成一个open状态告警 |
| ALERT-007 | 已关闭告警重新触发 | 相同告警在关闭后再次触发 | 生成新告警事件 |

---

### 3.5 RBAC权限测试

#### 3.5.1 角色权限验证

| 用例ID | 测试场景 | 用户角色 | 操作 | 预期结果 |
|--------|----------|----------|------|----------|
| RBAC-001 | Admin访问用户管理 | administrator | 访问 /admin/users | 访问成功 |
| RBAC-002 | Operator访问用户管理 | operator | 访问 /admin/users | 访问被拒绝 |
| RBAC-003 | Auditor创建批次 | auditor | 创建批次 | 操作被拒绝（只读） |
| RBAC-004 | ES Officer处理告警 | es_officer | 处理告警 | 操作成功 |
| RBAC-005 | Operator创建批次 | operator | 创建批次 | 操作成功 |
| RBAC-006 | Auditor查看审计日志 | auditor | 访问 /audit/logs | 访问成功 |

---

### 3.6 API接口测试

#### 3.6.1 API认证

| 用例ID | 测试场景 | 认证方式 | 预期结果 |
|--------|----------|----------|----------|
| API-001 | 有效API Key | X-API-Key: demo-hazwaste-api-key | 请求成功 |
| API-002 | 无效API Key | X-API-Key: invalid-key | 返回401错误 |
| API-003 | 缺失API Key | 无X-API-Key头 | 返回401错误 |

#### 3.6.2 API功能

| 用例ID | 测试场景 | 端点 | 预期结果 |
|--------|----------|------|----------|
| API-004 | 健康检查 | GET /api/v1/health | 返回 {"status": "ok", "api": "v1"} |
| API-005 | 获取批次列表 | GET /api/v1/batches | 返回批次列表JSON |
| API-006 | 获取批次详情 | GET /api/v1/batches/<code> | 返回指定批次详情 |
| API-007 | 获取不存在批次 | GET /api/v1/batches/NOTEXIST | 返回404错误 |
| API-008 | ERP人员查询 | POST /api/v1/integration/erp/person | 返回mock人员信息 |
| API-009 | LIMS结果回调 | POST /api/v1/integration/lims/result | 返回mock检测结果 |
| API-010 | 当前用户信息（已登录） | GET /api/v1/me | 返回用户信息JSON |
| API-011 | 当前用户信息（未登录） | GET /api/v1/me | 返回401错误 |

---

## 4. 测试执行

### 4.1 测试命令

```bash
# 运行所有测试
pytest tests/ -v

# 运行指定模块测试
pytest tests/test_state_machine.py -v

# 生成测试报告
pytest tests/ --tb=short -q
```

### 4.2 测试结果判定

| 结果 | 判定条件 |
|------|----------|
| **通过** | 所有测试用例执行成功，无失败 |
| **部分通过** | 部分测试用例失败，需分析原因 |
| **失败** | 关键功能测试失败，系统不可用 |

---

## 5. 测试数据

### 5.1 预置测试用户

| 角色 | 用户名 | 密码 | 用途 |
|------|--------|------|------|
| Administrator | admin | Admin123! | 管理员权限测试 |
| Environmental Safety Officer | es_officer | Eso123! | EHS权限测试 |
| Operator | operator1 | Op123! | 操作员权限测试 |
| Operator | operator2 | Op123! | 多用户审计测试 |
| Auditor | auditor1 | Audit123! | 审计员权限测试 |

### 5.2 测试批次数据

| 字段 | 值 |
|------|------|
| batch_code | TEST-BATCH-001 |
| name | 废酸溶液 |
| category | 酸性废物 |
| source_unit | 生产车间A |
| quantity | 50.0 |
| unit | kg |
| storage_location | 仓库B区 |
| hazard_level | high |
| responsible_person | Zhang San |

---

## 6. 测试检查清单

### 6.1 功能测试清单

- [ ] 用户认证功能正常
- [ ] 批次创建/编辑/查询功能正常
- [ ] 状态机转换符合规则
- [ ] 告警规则正确触发
- [ ] 审计日志完整记录
- [ ] RBAC权限控制有效
- [ ] API接口功能正常

### 6.2 安全性测试清单

- [ ] 密码使用哈希存储
- [ ] 无SQL注入漏洞
- [ ] API认证有效
- [ ] 敏感数据不泄露
- [ ] 会话管理安全

### 6.3 性能测试清单

- [ ] 页面响应时间 < 2秒
- [ ] 批量数据处理正常
- [ ] 并发访问稳定

---

## 附录：测试用户脚本（供评分者使用）

1. **登录 operator1** → **Batches** → 创建批次 → 确认状态为 `registered`
2. 沿状态链推进直到 `stored` / `pending_transfer`（非法跳转被阻止）
3. 打开批次详情的 **QR** → 扫描或打开公共 **trace** URL
4. **登录 es_officer** → **Dashboard** → **Run alert rules** → **Alerts**
5. **登录 auditor1** → **Audit log** → **Reports** → 下载 CSV/PDF
6. **登录 admin** → **Users** / **Alert rules**
