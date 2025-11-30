# 数据字典 (`data/contracts.db`)

## contracts —— 合同主表
| 字段 | 类型 | 说明 | 约束 |
| --- | --- | --- | --- |
| id | INTEGER | 主键 | PK，自增 |
| contract_number | TEXT | 合同编号 | 唯一索引，爬虫去重依据 |
| title | TEXT | 合同标题 |  |
| contract_amount | TEXT | 金额原文 |  |
| currency | TEXT | 币种 |  |
| customer_name | TEXT | 客户名称 |  |
| project_code | TEXT | 项目编号 |  |
| signed_at | TEXT | 签订日期（YYYY-MM-DD） |  |
| description | TEXT | 合同描述 |  |
| status | TEXT | 合同状态 |  |
| tags | TEXT | 标签（逗号分隔） |  |
| raw_payload | JSON/TEXT | 抓取原始内容 |  |
| collected_at | DATETIME | 抓取时间 | 默认 `datetime('now')` |
| created_at / updated_at | DATETIME | 数据库时间戳 | server default |

## harvest_logs —— 采集任务日志
| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | INTEGER | 主键，自增 |
| contract_type | TEXT | 合同类型（固定金额、时间资源等） |
| year | INTEGER | 任务年份 |
| pages_scraped | INTEGER | 抓取页数 |
| records_scraped | INTEGER | 入库条数 |
| status | TEXT | `success`/`failure` |
| message | TEXT | 成功：`类型 起始~结束`；失败：异常信息 |
| category | TEXT | `contract`/`qualification`/`intellectual_property` |
| started_at / completed_at | DATETIME | 起止时间 |

## harvest_warnings —— 采集异常
| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | INTEGER | 主键 |
| category | TEXT | 所属类别 |
| contract_type | TEXT | 合同类型 |
| year | INTEGER | 年份 |
| start_date / end_date | TEXT | 区间 |
| warning_type | TEXT | `split_limit`, `partial_page` 等 |
| details | TEXT | 详细说明 |
| created_at | DATETIME | 创建时间 |

## assets —— 资质 / 知识产权表
| 字段 | 类型 | 说明 | 约束 |
| --- | --- | --- | --- |
| id | INTEGER | 主键 |
| category | TEXT | `qualification` / `intellectual_property` |
| company_name | TEXT | 公司名 |
| business_type | TEXT | 业务类型 |
| qualification_name | TEXT | 资质/知识产权名称 |
| qualification_level | TEXT | 等级 |
| expire_date | TEXT | 到期日期 |
| next_review_date | TEXT | 下次年审日期 |
| download_url | TEXT | 附件下载链接 |
| raw_payload | JSON/TEXT | 原始内容 |
| collected_at / created_at / updated_at | DATETIME | 时间戳 |
| 约束 |  | 唯一键 (`category`,`company_name`,`qualification_name`,`download_url`) |

## companies —— 公司表（资质/IP）
| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | INTEGER | 主键 |
| name | TEXT | 公司名称，唯一 (`uq_companies_name`) |
| business_type | TEXT | 业务类型 |
| total_count | INTEGER | 一级页总资质数 |
| code | TEXT | 公司编号（详情页） |
| collected_at / created_at / updated_at | DATETIME | 时间戳 |

## employees —— 员工主表
| 字段 | 类型 | 说明 | 约束 |
| --- | --- | --- | --- |
| id | INTEGER | 主键 |
| employee_no | TEXT | 工号 | 唯一 |
| name | TEXT | 姓名 |  |
| gender | TEXT | 性别 |  |
| status | TEXT | 在职/离职等 |  |
| joined_at | TEXT | 参加工作时间 |  |
| age | REAL | 年龄 |  |
| seniority_years | REAL | 司龄 |  |
| working_years | REAL | 工龄 |  |
| school | TEXT | 学校（若主表提供） |  |
| major | TEXT | 主专业 |  |
| degree | TEXT | 最高学历 |  |
| diploma | TEXT | 最高学位 |  |
| company | TEXT | 人事范围/社保公司 |  |
| industry_experience | TEXT | 行业经验描述 |  |
| created_at / updated_at | DATETIME | 时间戳 | 默认 `datetime('now')` |

## employee_educations —— 员工学历
| 字段 | 类型 | 说明 | 约束 |
| --- | --- | --- | --- |
| id | INTEGER | 主键 |
| employee_id | INTEGER | 外键 -> employees.id |
| degree | TEXT | 学历（本科/硕士等） |
| major | TEXT | 专业 |
| school | TEXT | 毕业院校 |
| diploma | TEXT | 学位 |
| is_highest | INTEGER | 默认 1 |
| 约束 |  | UNIQUE(`employee_id`,`degree`,`major`,`school`) |

## employee_certificates —— 员工证书
| 字段 | 类型 | 说明 | 约束 |
| --- | --- | --- | --- |
| id | INTEGER | 主键 |
| employee_id | INTEGER | 外键 -> employees.id |
| category | TEXT | 从 Excel “资质类型”映射 |
| certificate_type | TEXT | 证书类型（如项目管理类） |
| certificate_name | TEXT | 证书名称（PMP 等） |
| qualification_level | TEXT | 等级/说明 |
| authority | TEXT | 认证机构 |
| effective_date / expire_date | TEXT | 生效 / 到期日期 |
| certificate_no | TEXT | 证书编号 | 可空 |
| remarks | TEXT | 备注 | 可空 |
| 约束 |  | UNIQUE(`employee_id`,`certificate_name`,`certificate_type`,`qualification_level`,`authority`,`certificate_no`) |

---
**关系图谱**
- `harvest_logs` / `harvest_warnings` 通过 `category` 和 `contract_type` 对应合同或资质/IP 任务。
- `assets` 与 `companies` 以 `company_name` / `code` 逻辑关联（无外键）。
- `employees` 与 `employee_educations`、`employee_certificates` 为 1:N（外键 `employee_id`）。
- `contracts` 当前独立，可按需扩展客户表。

