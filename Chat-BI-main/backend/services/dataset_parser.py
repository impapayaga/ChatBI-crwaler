"""
数据集文件解析服务
支持CSV和Excel解析,转换为Parquet格式
"""
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from sqlalchemy import select
from models.sys_dataset import SysDataset, SysDatasetColumn
from db.session import async_session
from core.minio_client import minio_client
import io
import logging
from typing import List, Dict, Any
from datetime import datetime
import numpy as np

logger = logging.getLogger(__name__)


def detect_header_rows(
    file_data: bytes, 
    engine: str = 'openpyxl', 
    max_rows: int = 10,
    min_data_confidence: float = 0.7
) -> List[int]:
    """
    智能检测Excel表头行数（支持任意层级）
    
    策略：动态检测，直到遇到明显的数据行为止
    
    Args:
        file_data: Excel文件数据（bytes）
        engine: pandas读取引擎
        max_rows: 最大检测行数（防止无限循环，默认10行）
        min_data_confidence: 判断为数据行的最小置信度（0-1）
    
    Returns:
        表头行索引列表，例如 [0] 表示单行表头，[0, 1, 2] 表示三行表头
    """
    try:
        # 读取更多行用于检测（增加检测范围）
        preview_buffer = io.BytesIO(file_data)
        preview_df = pd.read_excel(
            preview_buffer,
            nrows=max_rows + 2,  # 多读几行，用于对比判断
            header=None,
            engine=engine
        )
        
        if len(preview_df) == 0:
            return [0]
        
        # 检查每行的特征，动态判断
        header_candidates = [0]  # 至少第一行是表头
        
        for i in range(1, min(max_rows, len(preview_df))):
            row = preview_df.iloc[i]
            
            if len(row) == 0:
                # 空行，跳过
                continue
            
            # 计算各种特征
            null_ratio = row.isna().sum() / len(row)
            unique_ratio = row.nunique() / len(row)
            
            # 检查数据类型：表头通常是字符串，数据行通常有数值
            string_count = sum(1 for val in row if pd.notna(val) and isinstance(val, str))
            numeric_count = sum(1 for val in row if pd.notna(val) and isinstance(val, (int, float)))
            string_ratio = string_count / len(row) if len(row) > 0 else 0
            numeric_ratio = numeric_count / len(row) if len(row) > 0 else 0
            
            # 判断是否为表头行的综合指标
            is_likely_header = False
            
            # 条件1：空值比例高（可能是合并单元格）
            if null_ratio > 0.3:
                is_likely_header = True
            
            # 条件2：唯一值比例低（可能是重复的表头结构）
            elif unique_ratio < 0.5:
                is_likely_header = True
            
            # 条件3：整行都是字符串（更可能是表头）
            elif string_ratio > 0.8 and numeric_ratio < 0.2:
                is_likely_header = True
            
            # 条件4：与上一行对比，如果结构相似（都有空值），可能是同一层级表头
            if i > 0:
                prev_row = preview_df.iloc[i-1]
                prev_null_ratio = prev_row.isna().sum() / len(prev_row) if len(prev_row) > 0 else 0
                # 如果两行都有较高的空值比例，可能是多层级表头
                if null_ratio > 0.2 and prev_null_ratio > 0.2:
                    is_likely_header = True
            
            if is_likely_header:
                header_candidates.append(i)
            else:
                # 这一行看起来像数据，停止检测
                # 但需要确认：如果数值比例很高，几乎肯定是数据行
                if numeric_ratio > min_data_confidence:
                    logger.info(f"在第 {i+1} 行检测到数据特征（数值比例: {numeric_ratio:.2f}），停止检测")
                    break
        
        # 如果检测到多行表头，返回所有候选行
        if len(header_candidates) > 1:
            logger.info(f"检测到 {len(header_candidates)} 行表头: {header_candidates}")
            return header_candidates
        
        # 默认单行表头
        return [0]
    except Exception as e:
        logger.warning(f"表头行数检测失败，使用单行表头: {e}")
        return [0]  # 失败时降级为单行表头


def read_excel_with_multilevel_header(
    file_data: bytes, 
    engine: str = 'openpyxl',
    detect_headers: bool = True
) -> pd.DataFrame:
    """
    读取Excel，自动处理多行表头
    
    Args:
        file_data: Excel文件数据（bytes）
        engine: pandas读取引擎
        detect_headers: 是否自动检测表头行数
    
    Returns:
        处理后的DataFrame，多行表头已合并为单层列名
    """
    file_buffer = io.BytesIO(file_data)
    
    try:
        if detect_headers:
            # 尝试检测表头行数（支持任意层级）
            header_rows = detect_header_rows(file_data, engine, max_rows=10)
            file_buffer.seek(0)
        else:
            header_rows = [0]
        
        # 读取数据
        if len(header_rows) > 1:
            # 多行表头：使用MultiIndex
            logger.info(f"使用多行表头读取: header={header_rows}")
            df = pd.read_excel(
                file_buffer,
                header=header_rows,
                engine=engine
            )
            
            # 将MultiIndex转换为单层列名
            # 处理逻辑：合并非空值，用下划线连接
            def merge_column_names(col_tuple):
                """合并MultiIndex列名为单个字符串"""
                # 过滤掉空值、nan、空字符串
                parts = []
                for col in col_tuple:
                    col_str = str(col).strip()
                    if col_str and col_str.lower() not in ['nan', 'none', '']:
                        parts.append(col_str)
                
                # 用下划线连接
                merged = '_'.join(parts)
                
                # 如果合并后为空，使用默认列名
                return merged if merged else None
            
            # 转换列名
            new_columns = []
            for i, col_tuple in enumerate(df.columns.values):
                merged_name = merge_column_names(col_tuple)
                if merged_name:
                    new_columns.append(merged_name)
                else:
                    new_columns.append(f'Column_{i}')
            
            df.columns = new_columns
            
            logger.info(f"多表头合并完成，列名示例: {new_columns[:5]}")
            
        else:
            # 单行表头：正常读取
            df = pd.read_excel(
                file_buffer,
                header=0,
                engine=engine
            )
        
        return df
        
    except Exception as e:
        # 降级：尝试单行表头
        logger.warning(f"多表头读取失败，降级为单行表头: {e}")
        file_buffer.seek(0)
        try:
            return pd.read_excel(file_buffer, header=0, engine=engine)
        except Exception as e2:
            logger.error(f"单行表头读取也失败: {e2}")
            raise


async def parse_dataset_task(dataset_id: str, file_path: str, filename: str):
    """
    后台任务: 解析上传的CSV/Excel文件

    Args:
        dataset_id: 数据集ID
        file_path: MinIO文件路径
        filename: 原始文件名

    流程:
        1. 从MinIO下载文件
        2. 根据格式解析(CSV/Excel)
        3. 推断Schema和统计信息
        4. 转换为Parquet并上传MinIO
        5. 保存列信息到数据库
        6. 更新数据集状态
    """
    async with async_session() as session:
        try:
            # 1. 更新状态为parsing
            result = await session.execute(
                select(SysDataset).where(SysDataset.id == dataset_id)
            )
            dataset = result.scalar_one()
            dataset.parse_status = 'parsing'
            dataset.parse_progress = 10
            await session.commit()

            logger.info(f"开始解析数据集: {dataset_id}")

            # 2. 从MinIO下载文件
            object_name = file_path.split('/')[-1]
            file_data = minio_client.download_file(f"uploads/{object_name}")
            logger.info(f"文件已下载: {len(file_data)} bytes")

            dataset.parse_progress = 20
            await session.commit()

            # 3. 根据格式解析文件
            try:
                if filename.endswith('.csv'):
                    df = pd.read_csv(
                        io.BytesIO(file_data),
                        encoding='utf-8',
                        low_memory=False
                    )
                elif filename.endswith(('.xlsx', '.xls', '.et')):
                    # Excel/WPS文件,尝试多种引擎
                    df = None
                    errors = []

                    # 尝试顺序: openpyxl -> xlrd (for .et files, try both)
                    engines_to_try = []
                    if filename.endswith('.xlsx'):
                        engines_to_try = ['openpyxl']
                    elif filename.endswith('.xls'):
                        engines_to_try = ['xlrd']
                    elif filename.endswith('.et'):
                        # .et文件尝试所有可用引擎
                        engines_to_try = ['openpyxl', 'xlrd']

                    for engine in engines_to_try:
                        try:
                            # 使用多表头支持函数读取
                            df = read_excel_with_multilevel_header(
                                file_data,
                                engine=engine,
                                detect_headers=True
                            )
                            logger.info(f"使用{engine}引擎解析成功（支持多表头）")
                            break
                        except Exception as e:
                            error_msg = str(e)
                            errors.append(f"{engine}: {error_msg}")
                            logger.warning(f"{engine}解析失败: {e}")

                            # 如果是 DataValidation 错误，尝试多种降级策略
                            if "DataValidation" in error_msg and engine == "openpyxl":
                                # 策略1: 使用 openpyxl 底层 API 跳过验证
                                try:
                                    import openpyxl
                                    from openpyxl.worksheet.datavalidation import DataValidation as DV

                                    # 临时禁用 DataValidation 的参数检查
                                    original_init = DV.__init__
                                    def patched_init(self, *args, **kwargs):
                                        # 移除不兼容的参数
                                        kwargs.pop('id', None)
                                        original_init(self, *args, **kwargs)

                                    DV.__init__ = patched_init

                                    try:
                                        # 降级策略：使用openpyxl手动读取
                                        # 注意：这个降级策略只支持单行表头，因为已经是降级路径了
                                        wb = openpyxl.load_workbook(io.BytesIO(file_data), data_only=True)
                                        ws = wb.active
                                        data = list(ws.values)

                                        if data and len(data) > 0:
                                            # 尝试检测多表头（简单版本）
                                            # 检查前两行，如果有大量空值，可能是多表头
                                            if len(data) >= 2:
                                                first_row = data[0]
                                                second_row = data[1]
                                                null_count = sum(1 for val in first_row if val is None or val == '')
                                                
                                                # 如果第一行空值多，尝试合并前两行
                                                if null_count > len(first_row) * 0.3:
                                                    # 合并表头：用第二行填充第一行的空值
                                                    merged_cols = []
                                                    for i, (first_val, second_val) in enumerate(zip(first_row, second_row)):
                                                        if first_val and str(first_val).strip():
                                                            if second_val and str(second_val).strip():
                                                                merged_cols.append(f"{first_val}_{second_val}")
                                                            else:
                                                                merged_cols.append(str(first_val))
                                                        elif second_val and str(second_val).strip():
                                                            merged_cols.append(str(second_val))
                                                        else:
                                                            merged_cols.append(f'Column_{i}')
                                                    cols = merged_cols
                                                    rows = data[2:]  # 从第三行开始
                                                    logger.info("检测到多表头，已合并（降级模式）")
                                                else:
                                                    # 单行表头
                                                    cols = data[0]
                                                    cols = [str(col) if col is not None else f'Column_{i}' for i, col in enumerate(cols)]
                                                    rows = data[1:]
                                            else:
                                                # 数据不足，使用单行表头
                                                cols = data[0]
                                                cols = [str(col) if col is not None else f'Column_{i}' for i, col in enumerate(cols)]
                                                rows = data[1:]

                                            # 确保每行数据长度与列数一致
                                            clean_rows = []
                                            for row in rows:
                                                # 转换为列表，确保长度与列数一致
                                                row_list = list(row) if row else []
                                                # 填充或截断到正确的列数
                                                if len(row_list) < len(cols):
                                                    row_list.extend([None] * (len(cols) - len(row_list)))
                                                elif len(row_list) > len(cols):
                                                    row_list = row_list[:len(cols)]
                                                clean_rows.append(row_list)

                                            # 创建 DataFrame
                                            df = pd.DataFrame(clean_rows, columns=cols)

                                        wb.close()
                                        logger.info(f"使用{engine}引擎(补丁模式)解析成功")
                                        break
                                    finally:
                                        # 恢复原始方法
                                        DV.__init__ = original_init

                                except Exception as e2:
                                    errors.append(f"{engine}(补丁模式): {str(e2)}")
                                    logger.warning(f"{engine}补丁模式失败: {e2}")

                                # 策略2: 尝试使用 pyxlsb (如果是 xlsb 格式)
                                try:
                                    import pyxlsb
                                    from pyxlsb import open_workbook
                                    with open_workbook(io.BytesIO(file_data)) as wb:
                                        with wb.get_sheet(1) as sheet:
                                            data = [[item.v if item else None for item in row] for row in sheet.rows()]
                                            if data:
                                                cols = data[0]
                                                df = pd.DataFrame(data[1:], columns=cols)
                                    logger.info(f"使用 pyxlsb 引擎解析成功")
                                    break
                                except (ImportError, Exception) as e3:
                                    errors.append(f"pyxlsb: {str(e3)}")
                                    logger.warning(f"pyxlsb 解析失败: {e3}")

                            continue

                    if df is None:
                        # 如果所有引擎都失败
                        if filename.endswith('.et'):
                            raise ValueError(
                                f".et文件解析失败。WPS .et格式与Excel不完全兼容，所有解析引擎均失败。"
                                f"请将文件另存为 .xlsx 或 .csv 格式后重新上传。"
                            )
                        else:
                            raise ValueError(f"Excel文件解析失败: {'; '.join(errors)}")
                else:
                    raise ValueError(f"不支持的文件格式: {filename}")

                logger.info(f"文件解析成功: {len(df)} 行, {len(df.columns)} 列")
            except Exception as e:
                raise ValueError(f"文件解析失败: {str(e)}")

            dataset.parse_progress = 40
            await session.commit()

            # 4. 清理列名(移除特殊字符)
            df.columns = [clean_column_name(col) for col in df.columns]

            # 5. 推断Schema并生成统计信息
            schema_info = infer_schema(df)
            logger.info(f"Schema推断完成: {len(schema_info)} 列")

            dataset.parse_progress = 60
            await session.commit()

            # 6. 清理数据类型,确保PyArrow能够正确转换
            df = clean_dataframe_for_parquet(df)
            logger.info("数据类型清理完成")

            # 7. 转换为Parquet并上传MinIO
            parquet_filename = f"{dataset_id}.parquet"
            parquet_buffer = io.BytesIO()

            # 使用pyarrow写入Parquet
            try:
                table = pa.Table.from_pandas(df)
                pq.write_table(
                    table,
                    parquet_buffer,
                    compression='snappy',
                    use_dictionary=True
                )
            except Exception as e:
                logger.error(f"PyArrow转换失败: {e}")
                raise ValueError(f"数据格式转换失败，请检查文件中是否有混合类型的列: {str(e)}")

            parquet_data = parquet_buffer.getvalue()
            parquet_path = minio_client.upload_file(
                parquet_data,
                f"parquet/{parquet_filename}",
                content_type="application/x-parquet"
            )
            logger.info(f"Parquet文件已上传: {parquet_path}")

            dataset.parse_progress = 80
            await session.commit()

            # 8. 保存列信息到数据库
            for idx, col_info in enumerate(schema_info):
                col = SysDatasetColumn(
                    dataset_id=dataset_id,
                    col_name=col_info['name'],
                    col_index=idx,
                    col_type=col_info['type'],
                    stats=col_info['stats'],
                    sample_values=col_info['samples']
                )
                session.add(col)

            # 9. 更新数据集状态
            dataset.parsed_path = parquet_path
            dataset.row_count = len(df)
            dataset.column_count = len(df.columns)
            dataset.parse_status = 'parsed'
            dataset.parse_progress = 100
            await session.commit()

            logger.info(f"数据集 {dataset_id} 解析成功")

            # 10. 数据分片准备(构造列描述)
            try:
                dataset.chunk_status = 'chunking'
                dataset.chunk_progress = 0
                await session.commit()

                # 分片逻辑：为每一列构造描述文本
                from services.embedding_service import build_column_description
                chunked_data = []
                for idx, col_info in enumerate(schema_info):
                    description = build_column_description(col_info)
                    chunked_data.append({
                        'index': idx,
                        'col_info': col_info,
                        'description': description
                    })
                    # 更新分片进度
                    progress = int((idx + 1) / len(schema_info) * 100)
                    dataset.chunk_progress = progress
                    await session.commit()

                dataset.chunk_status = 'completed'
                dataset.chunk_progress = 100
                await session.commit()
                logger.info(f"数据集 {dataset_id} 分片准备完成，共 {len(chunked_data)} 个列")

                # 11. 向量化生成
                dataset.vectorize_status = 'vectorizing'
                dataset.vectorize_progress = 0
                await session.commit()

                from services.embedding_service import vectorize_columns
                await vectorize_columns(str(dataset_id), chunked_data)

                dataset.vectorize_status = 'completed'
                dataset.vectorize_progress = 100
                await session.commit()
                logger.info(f"数据集 {dataset_id} 向量化完成")

            except Exception as e:
                error_msg = str(e)
                # 判断是哪个步骤失败
                if dataset.chunk_status != 'completed':
                    logger.error(f"数据分片失败: {e}")
                    dataset.chunk_status = 'failed'
                    dataset.chunk_error = error_msg
                else:
                    logger.error(f"向量化失败: {e}")
                    dataset.vectorize_status = 'failed'
                    dataset.vectorize_error = error_msg
                await session.commit()
                # 不影响主流程,文件仍然可用

        except Exception as e:
            logger.error(f"解析数据集失败: {e}", exc_info=True)
            # 更新为失败状态
            try:
                dataset.parse_status = 'failed'
                dataset.error_message = str(e)
                await session.commit()
            except:
                pass


def clean_column_name(col_name: str) -> str:
    """
    清理列名,移除特殊字符和不可见字符

    Args:
        col_name: 原始列名

    Returns:
        清理后的列名
    """
    import unicodedata
    import re
    
    # 移除前后空格
    col_name = str(col_name).strip()
    
    # 移除不可见字符和控制字符
    # 包括零宽字符、制表符、换行符等
    col_name = ''.join(char for char in col_name 
                      if unicodedata.category(char) not in ('Cc', 'Cf', 'Cs', 'Co', 'Cn'))
    
    # 移除额外的空白字符（包括各种Unicode空白字符）
    col_name = re.sub(r'\s+', ' ', col_name).strip()

    # 替换特殊字符为下划线
    special_chars = [' ', '-', '.', '/', '\\', '(', ')', '[', ']', '{', '}']
    for char in special_chars:
        col_name = col_name.replace(char, '_')

    # 确保不以数字开头
    if col_name and col_name[0].isdigit():
        col_name = 'col_' + col_name

    return col_name or 'unnamed_column'


def clean_dataframe_for_parquet(df: pd.DataFrame) -> pd.DataFrame:
    """
    清理DataFrame以确保可以转换为Parquet格式

    Args:
        df: pandas DataFrame

    Returns:
        清理后的DataFrame
    """
    df_clean = df.copy()

    for col in df_clean.columns:
        col_data = df_clean[col]

        # 检查是否有混合类型
        if col_data.dtype == 'object':
            # 尝试推断为数值类型
            try:
                # 先尝试转换为数值
                numeric_col = pd.to_numeric(col_data, errors='coerce')
                # 如果超过50%的值可以转换为数值,则使用数值类型
                if numeric_col.notna().sum() > len(col_data) * 0.5:
                    df_clean[col] = numeric_col
                else:
                    # 否则全部转换为字符串
                    df_clean[col] = col_data.astype(str).replace('nan', None)
            except Exception as e:
                logger.warning(f"列 {col} 类型转换失败: {e}, 转换为字符串")
                df_clean[col] = col_data.astype(str).replace('nan', None)

        # 处理datetime类型
        elif pd.api.types.is_datetime64_any_dtype(col_data):
            # 确保日期类型是PyArrow支持的格式
            try:
                df_clean[col] = pd.to_datetime(col_data, errors='coerce')
            except Exception as e:
                logger.warning(f"列 {col} 日期转换失败: {e}, 转换为字符串")
                df_clean[col] = col_data.astype(str)

        # 处理NaN和Inf
        if pd.api.types.is_numeric_dtype(df_clean[col]):
            # 替换Inf为NaN
            df_clean[col] = df_clean[col].replace([np.inf, -np.inf], np.nan)

    return df_clean


def infer_schema(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    推断DataFrame的Schema并生成统计信息

    Args:
        df: pandas DataFrame

    Returns:
        列信息列表,每列包含: name, type, stats, samples
    """
    schema_info = []

    for col in df.columns:
        col_data = df[col]

        # 推断类型
        dtype = infer_column_type(col_data)

        # 生成统计信息
        stats = generate_column_stats(col_data, dtype)

        # 获取示例值
        samples = get_sample_values(col_data, num_samples=5)

        schema_info.append({
            'name': col,
            'type': dtype,
            'stats': stats,
            'samples': samples
        })

    return schema_info


def infer_column_type(col_data: pd.Series) -> str:
    """
    推断列的数据类型

    Args:
        col_data: pandas Series

    Returns:
        类型字符串: int/float/date/bool/string
    """
    # 确保 col_data 是一个标准的 pandas Series
    if not isinstance(col_data, pd.Series):
        return 'string'

    # 先检查是否全为空
    try:
        if col_data.isna().all():
            return 'string'
    except (ValueError, TypeError, AttributeError):
        # 如果检查失败，继续后续判断
        pass

    # 检查布尔类型
    try:
        if pd.api.types.is_bool_dtype(col_data):
            return 'bool'
    except:
        pass

    # 检查日期类型
    try:
        if pd.api.types.is_datetime64_any_dtype(col_data):
            return 'date'
    except:
        pass

    # 检查数值类型
    try:
        if pd.api.types.is_integer_dtype(col_data):
            return 'int'
    except:
        pass

    try:
        if pd.api.types.is_float_dtype(col_data):
            return 'float'
    except:
        pass

    # 尝试转换为数值
    try:
        non_null = col_data.dropna()
        if len(non_null) == 0:
            return 'string'

        # 尝试转换为数值
        numeric_data = pd.to_numeric(non_null, errors='raise')

        # 检查是否为整数
        try:
            # 检查所有值是否等于其整数版本
            if all(val == int(val) for val in numeric_data if not pd.isna(val)):
                return 'int'
        except (ValueError, TypeError, OverflowError):
            pass
        return 'float'
    except:
        pass

    # 尝试转换为日期
    try:
        non_null = col_data.dropna()
        if len(non_null) > 0:
            # 抑制警告
            import warnings
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                pd.to_datetime(non_null, errors='raise')
            return 'date'
    except:
        pass

    # 默认为字符串
    return 'string'


def generate_column_stats(col_data: pd.Series, dtype: str) -> Dict[str, Any]:
    """
    生成列的统计信息

    Args:
        col_data: pandas Series
        dtype: 列类型

    Returns:
        统计信息字典
    """
    stats = {
        'null_count': int(col_data.isna().sum()),
        'unique_count': int(col_data.nunique()),
        'total_count': len(col_data)
    }

    # 数值类型统计
    if dtype in ['int', 'float']:
        try:
            stats['min'] = float(col_data.min()) if not pd.isna(col_data.min()) else None
            stats['max'] = float(col_data.max()) if not pd.isna(col_data.max()) else None
            stats['mean'] = float(col_data.mean()) if not pd.isna(col_data.mean()) else None
            stats['std'] = float(col_data.std()) if not pd.isna(col_data.std()) else None
            stats['median'] = float(col_data.median()) if not pd.isna(col_data.median()) else None
        except:
            pass

    # 字符串类型统计
    elif dtype == 'string':
        try:
            stats['max_length'] = int(col_data.astype(str).str.len().max())
            stats['min_length'] = int(col_data.astype(str).str.len().min())
            stats['avg_length'] = float(col_data.astype(str).str.len().mean())
        except:
            pass

    # 日期类型统计
    elif dtype == 'date':
        try:
            stats['min_date'] = str(col_data.min()) if not pd.isna(col_data.min()) else None
            stats['max_date'] = str(col_data.max()) if not pd.isna(col_data.max()) else None
        except:
            pass

    return stats


def get_sample_values(col_data: pd.Series, num_samples: int = 5) -> List[Any]:
    """
    获取列的示例值

    Args:
        col_data: pandas Series
        num_samples: 示例数量

    Returns:
        示例值列表
    """
    # 移除空值
    non_null_data = col_data.dropna()

    if len(non_null_data) == 0:
        return []

    # 获取前N个唯一值
    samples = non_null_data.drop_duplicates().head(num_samples).tolist()

    # 转换为可序列化的格式
    serializable_samples = []
    for sample in samples:
        if isinstance(sample, (np.integer, np.floating)):
            serializable_samples.append(float(sample))
        elif isinstance(sample, (datetime, pd.Timestamp)):
            serializable_samples.append(str(sample))
        elif pd.isna(sample):
            continue
        else:
            serializable_samples.append(str(sample))

    return serializable_samples
