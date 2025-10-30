#!/usr/bin/env python3
"""
测试数据生成器
生成用于测试文件上传功能的 CSV 和 Excel 文件
"""

import pandas as pd
from datetime import datetime, timedelta
import random
import os

# 确保测试数据目录存在
TEST_DATA_DIR = "test_data"
os.makedirs(TEST_DATA_DIR, exist_ok=True)

print("=" * 50)
print("ChatBI 测试数据生成器")
print("=" * 50)
print()

# ========== 1. 销售数据 (CSV) ==========
print("生成测试数据 1/3: 销售数据 (CSV)...")

sales_data = {
    '日期': [
        '2024-01-01', '2024-01-02', '2024-01-03', '2024-01-04', '2024-01-05',
        '2024-01-06', '2024-01-07', '2024-01-08', '2024-01-09', '2024-01-10'
    ],
    '产品名称': [
        '产品A', '产品B', '产品A', '产品C', '产品B',
        '产品C', '产品A', '产品B', '产品C', '产品A'
    ],
    '销售额': [
        1250.5, 3400.2, 890.0, 2100.8, 4500.0,
        1780.3, 2250.0, 3890.5, 1560.2, 2980.0
    ],
    '销售数量': [
        50, 120, 35, 80, 150,
        65, 90, 130, 55, 110
    ]
}

df_sales = pd.DataFrame(sales_data)
csv_path = os.path.join(TEST_DATA_DIR, "test_sales.csv")
df_sales.to_csv(csv_path, index=False, encoding='utf-8-sig')
print(f"✅ 已生成: {csv_path}")
print(f"   数据规模: {len(df_sales)} 行 × {len(df_sales.columns)} 列")
print()

# ========== 2. 用户数据 (Excel) ==========
print("生成测试数据 2/3: 用户数据 (Excel)...")

user_data = {
    '用户ID': [1001, 1002, 1003, 1004, 1005, 1006, 1007, 1008],
    '姓名': ['张三', '李四', '王五', '赵六', '钱七', '孙八', '周九', '吴十'],
    '年龄': [28, 35, 42, 26, 31, 45, 29, 38],
    '城市': ['北京', '上海', '广州', '深圳', '杭州', '成都', '西安', '南京'],
    '注册日期': [
        '2023-01-15', '2023-02-20', '2023-03-10', '2023-04-05',
        '2023-05-12', '2023-06-18', '2023-07-22', '2023-08-30'
    ],
    '消费金额': [12500, 8900, 15600, 6700, 23400, 11200, 9800, 18900]
}

df_users = pd.DataFrame(user_data)

# 尝试生成 Excel，如果 openpyxl 不可用则生成 CSV
try:
    import openpyxl
    excel_path = os.path.join(TEST_DATA_DIR, "test_users.xlsx")
    df_users.to_excel(excel_path, index=False, engine='openpyxl')
    print(f"✅ 已生成: {excel_path}")
except ImportError:
    print("⚠️  openpyxl 未安装，生成 CSV 格式代替")
    excel_path = os.path.join(TEST_DATA_DIR, "test_users.csv")
    df_users.to_csv(excel_path, index=False, encoding='utf-8-sig')
    print(f"✅ 已生成: {excel_path}")

print(f"   数据规模: {len(df_users)} 行 × {len(df_users.columns)} 列")
print()

# ========== 3. 复杂数据集 (CSV - 更多列) ==========
print("生成测试数据 3/3: 电商订单数据 (CSV)...")

# 生成 50 行订单数据
num_orders = 50
start_date = datetime(2024, 1, 1)

orders_data = {
    '订单ID': [f'ORD{i:05d}' for i in range(1001, 1001 + num_orders)],
    '订单日期': [(start_date + timedelta(days=random.randint(0, 60))).strftime('%Y-%m-%d') for _ in range(num_orders)],
    '客户ID': [random.randint(1001, 1020) for _ in range(num_orders)],
    '产品类别': [random.choice(['电子产品', '服装', '食品', '家居', '图书']) for _ in range(num_orders)],
    '产品名称': [random.choice(['商品A', '商品B', '商品C', '商品D', '商品E', '商品F']) for _ in range(num_orders)],
    '单价': [round(random.uniform(50, 500), 2) for _ in range(num_orders)],
    '数量': [random.randint(1, 10) for _ in range(num_orders)],
    '折扣': [round(random.choice([0, 0.05, 0.1, 0.15, 0.2]), 2) for _ in range(num_orders)],
    '配送城市': [random.choice(['北京', '上海', '广州', '深圳', '杭州', '成都']) for _ in range(num_orders)],
    '支付方式': [random.choice(['微信', '支付宝', '信用卡', '现金']) for _ in range(num_orders)],
    '订单状态': [random.choice(['已完成', '配送中', '已取消', '待支付']) for _ in range(num_orders)]
}

# 计算订单金额
orders_data['订单金额'] = [
    round(orders_data['单价'][i] * orders_data['数量'][i] * (1 - orders_data['折扣'][i]), 2)
    for i in range(num_orders)
]

df_orders = pd.DataFrame(orders_data)
orders_csv_path = os.path.join(TEST_DATA_DIR, "test_orders.csv")
df_orders.to_csv(orders_csv_path, index=False, encoding='utf-8-sig')
print(f"✅ 已生成: {orders_csv_path}")
print(f"   数据规模: {len(df_orders)} 行 × {len(df_orders.columns)} 列")
print()

# ========== 数据预览 ==========
print("=" * 50)
print("数据预览")
print("=" * 50)
print()

print("📊 销售数据 (前5行):")
print(df_sales.head())
print()

print("👥 用户数据 (前5行):")
print(df_users.head())
print()

print("📦 订单数据 (前5行):")
print(df_orders.head())
print()

# ========== 测试建议 ==========
print("=" * 50)
print("测试建议")
print("=" * 50)
print()
print("1️⃣ 测试简单 CSV 上传:")
print(f"   上传文件: {csv_path}")
print("   测试查询: '哪个产品的销售额最高？'")
print()

print("2️⃣ 测试 Excel 上传:")
print(f"   上传文件: {excel_path}")
print("   测试查询: '显示各城市用户的平均消费金额'")
print()

print("3️⃣ 测试复杂数据集:")
print(f"   上传文件: {orders_csv_path}")
print("   测试查询:")
print("   - '各产品类别的总销售额是多少？'")
print("   - '哪个城市的订单最多？'")
print("   - '使用微信支付的订单平均金额'")
print()

print("=" * 50)
print("✅ 测试数据生成完成！")
print("=" * 50)
print()
print("📁 文件位置: ./test_data/")
print("📖 使用指南: 参考 TEST_INTEGRATION.md")
