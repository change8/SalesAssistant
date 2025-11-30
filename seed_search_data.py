"""Seed sample contracts and qualifications for testing."""
import sqlite3
from pathlib import Path
from datetime import date, datetime

DB_PATH = Path(__file__).parent / "sales_assistant.db"

def seed_contracts():
    """Add sample contract data."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    contracts = [
        ("智慧城市综合管理平台开发项目", "HT-2023-001", "某市政府", 8500000, "2023-03-15", "2023-04-01", "2024-03-31", "开发", "智慧城市管理系统，包含城市监控、应急调度、数据分析等模块", "completed"),
        ("银行核心系统运维服务", "HT-2023-012", "某商业银行", 3200000, "2023-06-20", "2023-07-01", "2024-06-30", "运维", "银行核心业务系统运维、技术支持及优化", "active"),
        ("电子政务系统集成项目", "HT-2024-003", "某省政务服务中心", 12000000, "2024-01-10", "2024-02-01", "2025-01-31", "开发", "省级政务服务平台建设，包含网上办事、数据共享等功能", "active"),
        ("医院信息化建设项目", "HT-2023-008", "某三甲医院", 4500000, "2023-08-15", "2023-09-01", "2024-08-31", "开发", "HIS系统、电子病历、远程医疗等信息化系统建设", "active"),
        ("企业ERP系统咨询服务", "HT-2024-005", "某大型制造企业", 1800000, "2024-03-01", "2024-03-15", "2024-12-31", "咨询", "ERP系统选型、实施规划及上线指导", "active"),
        ("教育云平台开发项目", "HT-2022-015", "某市教育局", 6800000, "2022-10-10", "2022-11-01", "2023-10-31", "开发", "区域教育资源共享平台、在线学习系统", "completed"),
        ("交通指挥中心系统升级", "HT-2023-020", "某市交通局", 5500000, "2023-11-05", "2023-12-01", "2024-11-30", "开发", "智能交通指挥系统升级改造，增加AI分析功能", "active"),
        ("政府大数据平台建设", "HT-2024-002", "某市大数据局", 15000000, "2024-01-20", "2024-02-15", "2025-02-14", "开发", "政府数据汇聚、治理、共享、开放平台建设", "active"),
    ]
    
    for contract in contracts:
        cursor.execute("""
            INSERT INTO contracts (
                project_name, contract_number, client_name, contract_amount,
                signing_date, start_date, end_date, contract_type,
                project_description, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, contract)
    
    conn.commit()
    print(f"✅ Inserted {len(contracts)} sample contracts")
    conn.close()


def seed_qualifications():
    """Add sample qualification data."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    qualifications = [
        ("信息系统集成及服务资质", "系统集成", "三级", "XXXXXX12345678", "中国电子信息行业联合会", "2022-06-01", "2026-06-01", "计算机信息系统集成", "valid"),
        ("软件企业认定证书", "软件开发", "无", "XXXXXX87654321", "工业和信息化部", "2023-01-15", "2027-01-15", "软件产品研发与销售", "valid"),
        ("信息安全服务资质", "安全服务", "二级", "XXXXXX11223344", "中国网络安全审查技术与认证中心", "2023-03-10", "2026-03-10", "风险评估、应急处理、安全集成", "valid"),
        ("CMMI5级认证", "软件成熟度", "Level 5", "XXXXXX99887766", "CMMI Institute", "2023-08-20", "2026-08-20", "软件开发过程管理", "valid"),
        ("ISO27001信息安全管理体系认证", "质量体系", "无", "XXXXXX55667788", "中国质量认证中心", "2022-11-01", "2025-11-01", "信息安全管理", "valid"),
        ("ISO9001质量管理体系认证", "质量体系", "无", "XXXXXX22334455", "中国质量认证中心", "2023-04-15", "2026-04-15", "软件开发与技术服务", "valid"),
        ("ITSS信息技术服务运行维护标准符合性证书", "运维服务", "三级", "XXXXXX44556677", "中国电子工业标准化技术协会", "2023-09-01", "2025-09-01", "信息系统运维服务", "valid"),
        ("涉密信息系统集成资质", "涉密集成", "乙级", "XXXXXX66778899", "国家保密局", "2022-12-10", "2025-12-10", "涉密信息系统集成", "valid"),
    ]
    
    for qual in qualifications:
        cursor.execute("""
            INSERT INTO qualifications (
                qualification_name, qualification_type, qualification_level,
                certificate_number, issue_organization, issue_date, expire_date,
                scope, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, qual)
    
    conn.commit()
    print(f"✅ Inserted {len(qualifications)} sample qualifications")
    conn.close()


if __name__ == "__main__":
    print("Seeding sample data...")
    seed_contracts()
    seed_qualifications()
    print("✅ All done!")
