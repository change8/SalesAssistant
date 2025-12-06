# 数据字典 (`data/contracts.db`)

## 1. contracts — 合同主表
| 字段 | 类型 | 说明 | 约束 |
| --- | --- | --- | --- |
| id | INTEGER | 主键，自增 | PK |
| record_uid | TEXT | 系统生成的唯一记录号（如 `CON-00000001`） | 唯一、索引 |
| contract_number | TEXT | 合同编号 | 索引，必填 |
| title | TEXT | 合同标题 | 必填 |
| contract_amount | TEXT | 金额原文 | 可空 |
| currency | TEXT | 币种 | 可空 |
| customer_name | TEXT | 客户名称 | 可空 |
| project_code | TEXT | 项目编号 | 可空 |
| signed_at | TEXT | 签订日期（YYYY-MM-DD） | 可空 |
| description | TEXT | 合同描述 | 可空 |
| status | TEXT | 合同状态 | 可空 |
| tags | TEXT | 标签（`,` 分隔） | 可空 |
| industry | TEXT | 业绩案例板块标题（如“业绩案例”） | 可空 |
| raw_payload | JSON/TEXT | 抓取原始内容 | 可空 |
| harvest_context | TEXT | 入库上下文（合同类型、日期范围、页码） | 可空 |
| borrow_materials | TEXT | 借用材料，格式如 `合同｜发票｜结算单` | 可空 |
| collected_at | DATETIME | 抓取时间 | 默认当前北京时间 |
| created_at | DATETIME | 创建时间戳 | 默认当前北京时间 |
| updated_at | DATETIME | 更新时间戳 | 默认当前北京时间，更新时刷新 |
| data_status | TEXT | 数据状态（默认 `normal`） | 可用于软删除 |

## 2. harvest_logs — 采集任务日志
| 字段 | 类型 | 说明 | 约束 |
| --- | --- | --- | --- |
| id | INTEGER | 主键 | PK |
| category | TEXT | `contract` / `qualification` / `intellectual_property` | 默认 `contract` |
| company_name | TEXT | 资质/知产任务对应的公司名 | 可空 |
| contract_type | TEXT | 合同类型或任务标签 | 必填 |
| year | INTEGER | 任务年份 | 必填 |
| start_date / end_date | TEXT | 任务时间范围 | 用于唯一索引 |
| pages_scraped | INTEGER | 尝试采集的页数（解析后进入 upsert 的页） | 默认 0 |
| records_scraped | INTEGER | 解析后交给 upsert 的条数 | 默认 0 |
| pages_committed | INTEGER | 实际新增数据的页数（页内至少新增 1 条算 1） | 默认 0 |
| records_committed | INTEGER | 实际新增成功的记录条数 | 默认 0 |
| expected_pages | INTEGER | 翻页器显示的总页数 | 可空 |
| expected_records | INTEGER | 翻页器显示的总条数 | 可空 |
| status | TEXT | `success`/`failure` | 默认 `running` |
| message | TEXT | 备注或异常信息 | 可空 |
| started_at / completed_at | DATETIME | 任务起止时间 | 自动记录 |
| created_at | DATETIME | 记录生成时间 | 默认 `CURRENT_TIMESTAMP` |
| 约束 |  | 唯一键 (`category`,`contract_type`,`company_name`,`start_date`,`end_date`) |

## 3. harvest_tasks — 任务表（重跑/拆分用）
| 字段 | 类型 | 说明 | 约束 |
| --- | --- | --- | --- |
| id | INTEGER | 主键 | PK |
| category | TEXT | `contract` / `qualification` / `intellectual_property` | 默认 `contract` |
| contract_type | TEXT | 合同类型或任务标签 | 可空 |
| start_date / end_date | TEXT | 时间范围 | 可空 |
| company_name | TEXT | 资质/知产任务的公司名 | 可空 |
| status | TEXT | `未开始`/`进行中`/`已拆分`/`已结束`/`任务中断` | 默认 `未开始` |
| remark | TEXT | 备注 | 可空 |
| current_page | INTEGER | 已抓取到的页码（续跑用） | 默认 0 |
| target_pages | TEXT | 指定补采的页码列表（字符串/JSON） | 可空 |
| created_at / updated_at | DATETIME | 创建/更新时间戳 | 默认 `CURRENT_TIMESTAMP` |
| 约束 |  | 唯一键 (`category`,`contract_type`,`company_name`,`start_date`,`end_date`) |

## 3. harvest_warnings — 采集异常告警
| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | INTEGER | 主键 |
| category | TEXT | `contract`/`qualification`/`intellectual_property` |
| contract_type | TEXT | 合同/资质/IP 类型 |
| year | INTEGER | 年度 |
| start_date / end_date | TEXT | 关联的时间区间 |
| company_name | TEXT | 资质/知产权的公司名称，合同场景可空 |
| page_number | INTEGER | 出问题的页码（从 1 开始） |
| warning_type | TEXT | `split_limit`, `parse_mismatch`, `insert_mismatch` 等 |
| details | TEXT | 详细说明 |
| field_name | TEXT | 对应出问题的字段（如 `records_committed`) |
| file_name | TEXT | 相关文件名称（资质/知产的条目名等） |
| retry_count | INTEGER | 该 warning 已补跑的次数 | 默认 0 |
| created_at | DATETIME | 生成时间（默认 `CURRENT_TIMESTAMP`） |

## 4. qualification_assets — 资质表
| 字段 | 类型 | 说明 | 约束 |
| --- | --- | --- | --- |
| id | INTEGER | 主键 | PK |
| record_uid | TEXT | 系统生成的唯一记录号 | 唯一、索引 |
| company_name | TEXT | 公司名称 | 必填 |
| company_code | TEXT | 公司编号 | 可空 |
| business_type | TEXT | 公司业务类型（一级页） | 可空 |
| qualification_name | TEXT | 资质名称 | 必填 |
| qualification_level | TEXT | 资质等级 | 可空 |
| expire_date | TEXT | 到期日期 | 可空 |
| next_review_date | TEXT | 下次年审日期 | 可空 |
| internal_id | TEXT | 详情页内部编号 | 可空 |
| patent_category | TEXT | 额外类别（保留字段） | 可空 |
| registration_no | TEXT | 注册号 | 可空 |
| certificate_number | TEXT | 证书编号 | 可空 |
| issuer | TEXT | 颁证机构 | 可空 |
| issue_date | TEXT | 颁证日期 | 可空 |
| status | TEXT | 资质状态 | 可空 |
| keeper | TEXT | 证书原件保管人 | 可空 |
| remark | TEXT | 备注 | 可空 |
| download_url | TEXT | 详情页 URL | 可空 |
| raw_payload | JSON/TEXT | 详情 JSON 备份 | 可空 |
| created_at / updated_at | DATETIME | 创建/更新时间戳 | 默认 `CURRENT_TIMESTAMP` |
| data_status | TEXT | 数据状态（默认 `normal`） | 支持软删除 |
| 约束 |  | 唯一键 (`company_name`,`qualification_name`,`certificate_number`) |

## 5. intellectual_property_assets — 知识产权表
| 字段 | 类型 | 说明 | 约束 |
| --- | --- | --- | --- |
| id | INTEGER | 主键 | PK |
| record_uid | TEXT | 系统生成的唯一记录号 | 唯一、索引 |
| company_name | TEXT | 公司名称 | 必填 |
| company_code | TEXT | 公司编号 | 可空 |
| business_type | TEXT | 公司业务类型 | 可空 |
| knowledge_category | TEXT | 知识产权类别（如软件著作权） | 可空 |
| patent_category | TEXT | 专利类别（如申请/授权类别） | 可空 |
| knowledge_name | TEXT | 产权名称 | 必填 |
| certificate_number | TEXT | 证书号 | 可空 |
| inventor | TEXT | 专利人 | 可空 |
| issue_date | TEXT | 颁证日期 | 可空 |
| application_date | TEXT | 申请日期 | 可空 |
| internal_id | TEXT | 内部编号 | 可空 |
| property_summary | TEXT | 知识产权简介 | 可空 |
| application_status | TEXT | 申请状态（已颁证等） | 可空 |
| issuer | TEXT | 颁证机构 | 可空 |
| version | TEXT | 版本号 | 可空 |
| registration_no | TEXT | 登记号 | 可空 |
| download_url | TEXT | 详情页 URL | 可空 |
| raw_payload | JSON/TEXT | 详情 JSON 备份 | 可空 |
| created_at / updated_at | DATETIME | 创建/更新时间戳 | 默认 `CURRENT_TIMESTAMP` |
| data_status | TEXT | 数据状态（默认 `normal`） | 支持软删除 |
| 约束 |  | 唯一键 (`company_name`,`knowledge_name`,`certificate_number`) |

## 6. companies — 公司表
| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | INTEGER | 主键 |
| name | TEXT | 公司名称（可附带编号） |
| business_type | TEXT | 公司业务类型（列表页） |
| total_count | INTEGER | 一级页总资质数量 | 可空 |
| code | TEXT | 公司编号 | 可空 |
| qualification_count | INTEGER | 已抓取资质数量 | 默认 0 |
| ip_count | INTEGER | 已抓取知识产权数量 | 默认 0 |
| legal_person | TEXT | 法定代表人 | 可空 |
| setup_date | TEXT | 成立时间 | 可空 |
| registered_capital | TEXT | 注册资本 | 可空 |
| currency | TEXT | 注册资本币种 | 可空 |
| head_office | TEXT | 所属总公司 | 可空 |
| nuccn | TEXT | 统一社会信用代码 | 可空 |
| registered_address | TEXT | 注册地址 | 可空 |
| operating_period | TEXT | 经营期限 | 可空 |
| headcount | TEXT | 人员数量 | 可空 |
| registered_city | TEXT | 所属地区 | 可空 |
| operating_state | TEXT | 经营状态 | 可空 |
| unregister_date | TEXT | 注销/退出时间 | 可空 |
| company_type | TEXT | 公司类型 | 可空 |
| company_category | TEXT | 公司大类 | 可空 |
| english_name | TEXT | 英文名称 | 可空 |
| shorthand | TEXT | 公司简称 | 可空 |
| prev_name | TEXT | 曾用名 | 可空 |
| business_scope | TEXT | 经营范围 | 可空 |
| created_at / updated_at | DATETIME | 时间戳（默认 `CURRENT_TIMESTAMP`） |
| data_status | TEXT | 数据状态（默认 `normal`） |

## 7. employees — 员工主表
| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | INTEGER | 主键 |
| employee_no | TEXT | 工号，唯一 |
| name | TEXT | 姓名 |
| gender | TEXT | 性别 |
| status | TEXT | 员工状态（在职/离职） |
| joined_at | TEXT | 参加工作时间（可空） |
| age | REAL | 年龄 |
| seniority_years | REAL | 司龄 |
| working_years | REAL | 工龄 |
| company | TEXT | 人事范围/社保公司 |
| created_at / updated_at | DATETIME | 时间戳 | 默认 `CURRENT_TIMESTAMP` |
| data_status | TEXT | 数据状态（默认 `normal`） |

## 8. employee_educations — 员工学历
| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | INTEGER | 主键 |
| employee_id | INTEGER | 外键 -> employees.id |
| school | TEXT | 毕业院校 |
| major | TEXT | 专业 |
| degree | TEXT | 学历（本科/硕士等） |
| diploma | TEXT | 学位 | 
| created_at / updated_at | DATETIME | 时间戳 | 默认 `CURRENT_TIMESTAMP` |
| data_status | TEXT | 数据状态（默认 `normal`） |
| 约束 |  | UNIQUE(`employee_id`,`school`,`major`,`degree`) |

## 9. employee_certificates — 员工证书
| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | INTEGER | 主键 |
| employee_id | INTEGER | 外键 -> employees.id |
| certificate_name | TEXT | 证书名称 |
| level | TEXT | 等级/说明 |
| authority | TEXT | 认证机构 |
| effective_date / expire_date | TEXT | 生效 / 到期时间 |
| certificate_type | TEXT | 证书类型 |
| certificate_no | TEXT | 证书编号 |
| created_at / updated_at | DATETIME | 时间戳 | 默认 `CURRENT_TIMESTAMP` |
| data_status | TEXT | 数据状态（默认 `normal`） |
| 约束 |  | UNIQUE(`employee_id`,`certificate_name`,`certificate_type`,`certificate_no`) |

---
### 关系/说明
- `harvest_logs` / `harvest_warnings` 以 `category + contract_type + start_date/end_date` 标识一次采集任务，可用于对比系统总量 (`expected_*`) 和实际抓取 (`pages_scraped/records_scraped`)。
- `qualification_assets` / `intellectual_property_assets` 分别记录资质和知识产权详情，均可以 `company_name`/`company_code` 与 `companies` 逻辑关联。
- `employees` 与 `employee_educations`、`employee_certificates` 通过 `employee_id` 建立 1:N 关系。
- `contracts` 当前与其他表独立，仅用于合同入库；若需客户/项目维表可再扩展。
