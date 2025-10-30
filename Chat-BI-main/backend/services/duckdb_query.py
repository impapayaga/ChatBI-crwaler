"""
DuckDB查询服务
用于查询用户上传的Parquet文件
"""
import duckdb
import pandas as pd
from typing import Optional, List, Dict, Any
import logging
import tempfile
import os
import re
from core.minio_client import minio_client
from sqlalchemy import select
from models.sys_dataset import SysDataset
from db.session import async_session

logger = logging.getLogger(__name__)


async def query_parquet_with_duckdb(
    dataset_id: str,
    sql_query: str,
    limit: Optional[int] = 1000
) -> Optional[pd.DataFrame]:
    """
    使用DuckDB查询Parquet文件

    Args:
        dataset_id: 数据集ID
        sql_query: SQL查询语句
        limit: 最大返回行数

    Returns:
        查询结果DataFrame,失败返回None
    """
    temp_file = None

    try:
        # 1. 从数据库获取数据集信息
        async with async_session() as session:
            result = await session.execute(
                select(SysDataset).where(SysDataset.id == dataset_id)
            )
            dataset_info = result.scalar_one_or_none()

            if not dataset_info:
                logger.error(f"数据集不存在: {dataset_id}")
                return None

            if dataset_info.parse_status != 'parsed':
                logger.error(f"数据集未解析完成: {dataset_info.parse_status}")
                return None

            if not dataset_info.parsed_path:
                logger.error(f"数据集Parquet路径为空")
                return None

        # 2. 从MinIO下载Parquet文件到临时文件
        parquet_filename = dataset_info.parsed_path.split('/')[-1]
        parquet_data = minio_client.download_file(f"parquet/{parquet_filename}")

        # 创建临时文件
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.parquet')
        temp_file.write(parquet_data)
        temp_file.close()

        logger.info(f"Parquet文件已下载到临时路径: {temp_file.name}")

        # 3. 使用DuckDB执行查询
        con = duckdb.connect()
        
        # 注册Parquet文件为表
        table_name = f"dataset_{dataset_id.replace('-', '_')}"
        con.execute(f"CREATE TABLE {table_name} AS SELECT * FROM read_parquet('{temp_file.name}')")
        
        # 执行查询
        # 注意: 这里需要替换SQL中的表名
        # 使用正则表达式替换，支持多行和空白字符
        # 匹配 "FROM dataset" 或 "FROM\n    dataset" 等各种情况
        modified_sql = re.sub(
            r'FROM\s+dataset\b',
            f'FROM {table_name}',
            sql_query,
            flags=re.IGNORECASE
        )
        
        # 添加LIMIT保护
        if limit and 'LIMIT' not in modified_sql.upper():
            modified_sql += f" LIMIT {limit}"
        
        logger.info(f"执行DuckDB查询: {modified_sql}")
        
        df = con.execute(modified_sql).df()
        con.close()

        logger.info(f"查询成功,返回 {len(df)} 行数据")
        return df

    except Exception as e:
        logger.error(f"DuckDB查询失败: {e}", exc_info=True)
        return None

    finally:
        # 清理临时文件
        if temp_file and os.path.exists(temp_file.name):
            try:
                os.unlink(temp_file.name)
                logger.debug(f"临时文件已删除: {temp_file.name}")
            except:
                pass


async def get_dataset_sample(dataset_id: str, limit: int = 10) -> Optional[pd.DataFrame]:
    """
    获取数据集的示例数据

    Args:
        dataset_id: 数据集ID
        limit: 返回行数

    Returns:
        示例数据DataFrame
    """
    sql = f"SELECT * LIMIT {limit}"
    return await query_parquet_with_duckdb(dataset_id, sql)


async def execute_dataset_query(
    dataset_id: str,
    columns: Optional[List[str]] = None,
    filters: Optional[Dict[str, Any]] = None,
    group_by: Optional[List[str]] = None,
    order_by: Optional[List[str]] = None,
    limit: int = 1000
) -> Optional[pd.DataFrame]:
    """
    构建并执行数据集查询

    Args:
        dataset_id: 数据集ID
        columns: 查询的列名列表,None表示所有列
        filters: 过滤条件字典 {col_name: value}
        group_by: 分组列
        order_by: 排序列
        limit: 最大返回行数

    Returns:
        查询结果DataFrame
    """
    # 构建SQL
    if columns:
        cols_str = ', '.join([f'"{col}"' for col in columns])
    else:
        cols_str = '*'

    sql_parts = [f"SELECT {cols_str} FROM dataset"]

    # WHERE条件
    if filters:
        where_clauses = []
        for col, value in filters.items():
            if isinstance(value, str):
                where_clauses.append(f'"{col}" = \'{value}\'')
            else:
                where_clauses.append(f'"{col}" = {value}')
        if where_clauses:
            sql_parts.append("WHERE " + " AND ".join(where_clauses))

    # GROUP BY
    if group_by:
        group_cols = ', '.join([f'"{col}"' for col in group_by])
        sql_parts.append(f"GROUP BY {group_cols}")

    # ORDER BY
    if order_by:
        order_cols = ', '.join([f'"{col}"' for col in order_by])
        sql_parts.append(f"ORDER BY {order_cols}")

    # LIMIT
    sql_parts.append(f"LIMIT {limit}")

    sql = ' '.join(sql_parts)

    return await query_parquet_with_duckdb(dataset_id, sql, limit=None)