"""
测试SQL表名替换正则表达式
"""
import re

# 测试用例
test_cases = [
    # 单行SQL
    "SELECT * FROM dataset WHERE id = 1",

    # 多行SQL（换行符）
    """SELECT
    EXTRACT(YEAR FROM "发布时间") AS "年份",
    COUNT(*) AS "政策数量"
FROM
    dataset
WHERE
    "发布时间" BETWEEN '2020-01-01' AND '2024-12-31'""",

    # 多个空格
    "SELECT * FROM     dataset WHERE id = 1",

    # Tab字符
    "SELECT * FROM\tdataset WHERE id = 1",

    # 混合空白字符
    "SELECT * FROM \n\t  dataset WHERE id = 1",
]

table_name = "dataset_c657f527_574d_4e44_8ae8_29eba01f93b5"

print("=" * 80)
print("SQL表名替换测试")
print("=" * 80)

for i, sql in enumerate(test_cases, 1):
    print(f"\n测试用例 {i}:")
    print(f"原始SQL:\n{sql}")
    print(f"\n替换后:")

    modified_sql = re.sub(
        r'FROM\s+dataset\b',
        f'FROM {table_name}',
        sql,
        flags=re.IGNORECASE
    )

    print(modified_sql)

    # 验证替换是否成功（使用单词边界检查）
    if table_name in modified_sql and not re.search(r'FROM\s+dataset\b(?!_)', modified_sql, re.IGNORECASE):
        print("✅ 替换成功")
    else:
        print("❌ 替换失败")
    print("-" * 80)
