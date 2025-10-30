"""
通用文档预览API端点
支持PDF、Excel、CSV、WPS、PPT、Word等多种办公文档格式的预览
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import Response, JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, Dict, Any
import logging
import io
import os
import tempfile
import base64
from pathlib import Path

from models.sys_dataset import SysDataset
from core.minio_client import minio_client
from api.dependencies.dependencies import get_async_session

router = APIRouter()
logger = logging.getLogger(__name__)

# 支持的文档格式配置
SUPPORTED_FORMATS = {
    # 表格文档
    'spreadsheet': {
        'extensions': ['.xlsx', '.xls', '.csv', '.et', '.ods'],
        'mime_types': [
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'application/vnd.ms-excel',
            'text/csv',
            'application/vnd.ms-excel'
        ]
    },
    # PDF文档
    'pdf': {
        'extensions': ['.pdf'],
        'mime_types': ['application/pdf']
    },
    # Word文档
    'document': {
        'extensions': ['.docx', '.doc', '.wps'],
        'mime_types': [
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/msword'
        ]
    },
    # PowerPoint文档
    'presentation': {
        'extensions': ['.pptx', '.ppt', '.dps'],
        'mime_types': [
            'application/vnd.openxmlformats-officedocument.presentationml.presentation',
            'application/vnd.ms-powerpoint'
        ]
    },
    # 文本文档
    'text': {
        'extensions': ['.txt', '.md', '.json', '.xml', '.log'],
        'mime_types': ['text/plain', 'text/markdown', 'application/json', 'text/xml']
    },
    # 图片文档
    'image': {
        'extensions': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg'],
        'mime_types': ['image/jpeg', 'image/png', 'image/gif', 'image/bmp', 'image/webp', 'image/svg+xml']
    }
}


def get_document_type(filename: str) -> str:
    """根据文件名判断文档类型"""
    ext = Path(filename).suffix.lower()
    
    for doc_type, config in SUPPORTED_FORMATS.items():
        if ext in config['extensions']:
            return doc_type
    
    return 'unknown'


def get_file_info(filename: str, file_size: int) -> Dict[str, Any]:
    """获取文件基本信息"""
    ext = Path(filename).suffix.lower()
    doc_type = get_document_type(filename)
    
    return {
        'filename': filename,
        'extension': ext,
        'document_type': doc_type,
        'file_size': file_size,
        'is_supported': doc_type != 'unknown',
        'preview_methods': get_available_preview_methods(doc_type)
    }


def get_available_preview_methods(doc_type: str) -> list:
    """获取可用的预览方法"""
    methods = ['download']  # 所有文件都支持下载
    
    if doc_type == 'spreadsheet':
        methods.extend(['table_view', 'html_preview'])
    elif doc_type == 'pdf':
        methods.extend(['pdf_viewer', 'image_preview'])
    elif doc_type == 'document':
        methods.extend(['html_preview', 'text_extract'])
    elif doc_type == 'presentation':
        methods.extend(['slide_preview', 'image_preview'])
    elif doc_type == 'text':
        methods.extend(['text_view', 'syntax_highlight'])
    elif doc_type == 'image':
        methods.extend(['image_view', 'thumbnail'])
    
    return methods


@router.get("/datasets/{dataset_id}/document-info")
async def get_document_info(
    dataset_id: str,
    session: AsyncSession = Depends(get_async_session)
):
    """
    获取文档基本信息和支持的预览方法
    """
    try:
        # 查询数据集信息
        result = await session.execute(
            select(SysDataset).where(SysDataset.id == dataset_id)
        )
        dataset = result.scalar_one_or_none()
        
        if not dataset:
            raise HTTPException(status_code=404, detail="数据集不存在")
            
        if not dataset.original_file_path:
            raise HTTPException(status_code=404, detail="原文件路径不存在")
        
        # 获取文件信息
        object_name = dataset.original_file_path
        if '/' in object_name and object_name.count('/') > 1:
            parts = object_name.split('/', 1)
            if len(parts) > 1:
                object_name = parts[1]
        
        # 检查文件是否存在并获取大小
        if not minio_client.file_exists(object_name):
            raise HTTPException(status_code=404, detail="原文件不存在")
        
        # 获取文件大小（这里需要MinIO客户端支持）
        file_size = 0  # 暂时设为0，后续可以通过MinIO API获取
        
        # 生成文件信息
        file_info = get_file_info(dataset.name, file_size)
        
        return {
            "success": True,
            "dataset_id": dataset_id,
            "dataset_name": dataset.name,
            "file_info": file_info,
            "message": f"文档类型: {file_info['document_type']}, 支持 {len(file_info['preview_methods'])} 种预览方式"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取文档信息失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取文档信息失败: {str(e)}")


@router.get("/datasets/{dataset_id}/document-preview")
async def get_document_preview(
    dataset_id: str,
    method: str = Query("auto", description="预览方法: auto, table_view, html_preview, pdf_viewer, text_view, image_view等"),
    page: int = Query(1, description="页码（适用于PDF等多页文档）"),
    lines: int = Query(100, description="预览行数（适用于表格和文本）"),
    session: AsyncSession = Depends(get_async_session)
):
    """
    通用文档预览接口
    根据文档类型和指定方法返回预览内容
    """
    try:
        # 查询数据集信息
        result = await session.execute(
            select(SysDataset).where(SysDataset.id == dataset_id)
        )
        dataset = result.scalar_one_or_none()
        
        if not dataset:
            raise HTTPException(status_code=404, detail="数据集不存在")
            
        if not dataset.original_file_path:
            raise HTTPException(status_code=404, detail="原文件路径不存在")
        
        # 获取文件
        object_name = dataset.original_file_path
        if '/' in object_name and object_name.count('/') > 1:
            parts = object_name.split('/', 1)
            if len(parts) > 1:
                object_name = parts[1]
        
        if not minio_client.file_exists(object_name):
            raise HTTPException(status_code=404, detail="原文件不存在")
        
        file_data = minio_client.download_file(object_name)
        doc_type = get_document_type(dataset.name)
        
        # 根据文档类型和方法选择预览策略
        if method == "auto":
            method = get_default_preview_method(doc_type)
        
        # 调用相应的预览处理器
        preview_result = await process_document_preview(
            file_data=file_data,
            filename=dataset.name,
            doc_type=doc_type,
            method=method,
            page=page,
            lines=lines
        )
        
        return {
            "success": True,
            "dataset_id": dataset_id,
            "document_type": doc_type,
            "preview_method": method,
            "page": page,
            **preview_result
        }
        
    except HTTPException:
        raise HTTPException(status_code=500, detail=f"文档预览失败: {str(e)}")
    except Exception as e:
        logger.error(f"文档预览失败: {e}")
        raise HTTPException(status_code=500, detail=f"文档预览失败: {str(e)}")


def get_default_preview_method(doc_type: str) -> str:
    """获取文档类型的默认预览方法"""
    defaults = {
        'spreadsheet': 'table_view',
        'pdf': 'pdf_viewer',
        'document': 'html_preview',
        'presentation': 'slide_preview',
        'text': 'text_view',
        'image': 'image_view'
    }
    return defaults.get(doc_type, 'download')


async def process_document_preview(
    file_data: bytes,
    filename: str,
    doc_type: str,
    method: str,
    page: int = 1,
    lines: int = 100
) -> Dict[str, Any]:
    """
    处理文档预览
    这是一个分发器，根据文档类型和方法调用具体的处理函数
    """
    
    if doc_type == 'spreadsheet':
        return await process_spreadsheet_preview(file_data, filename, method, lines)
    elif doc_type == 'pdf':
        return await process_pdf_preview(file_data, filename, method, page)
    elif doc_type == 'document':
        return await process_document_preview_handler(file_data, filename, method)
    elif doc_type == 'presentation':
        return await process_presentation_preview(file_data, filename, method, page)
    elif doc_type == 'text':
        return await process_text_preview(file_data, filename, method, lines)
    elif doc_type == 'image':
        return await process_image_preview(file_data, filename, method)
    else:
        raise HTTPException(status_code=400, detail=f"不支持的文档类型: {doc_type}")


async def process_spreadsheet_preview(file_data: bytes, filename: str, method: str, lines: int) -> Dict[str, Any]:
    """处理表格文档预览"""
    import pandas as pd
    
    try:
        df = None
        errors = []
        
        # 使用之前优化的Excel解析逻辑
        if filename.lower().endswith(('.xlsx', '.xls', '.et')):
            # 策略1: 标准pandas读取
            try:
                if filename.lower().endswith('.xlsx'):
                    df = pd.read_excel(io.BytesIO(file_data), engine='openpyxl', nrows=lines)
                elif filename.lower().endswith('.xls'):
                    df = pd.read_excel(io.BytesIO(file_data), engine='xlrd', nrows=lines)
                else:  # .et文件
                    df = pd.read_excel(io.BytesIO(file_data), engine='openpyxl', nrows=lines)
            except Exception as e:
                errors.append(f"标准读取失败: {str(e)}")
                
                # 策略2: openpyxl直接读取
                try:
                    import openpyxl
                    wb = openpyxl.load_workbook(io.BytesIO(file_data), read_only=True, data_only=True)
                    ws = wb.active
                    
                    data = []
                    for i, row in enumerate(ws.iter_rows(values_only=True)):
                        if i >= lines + 1:
                            break
                        data.append(row)
                    
                    wb.close()
                    
                    if data:
                        cols = data[0] if data[0] else []
                        cols = [str(col) if col is not None else f'Column_{i}' for i, col in enumerate(cols)]
                        rows = data[1:] if len(data) > 1 else []
                        clean_rows = []
                        
                        for row in rows:
                            row_list = list(row) if row else []
                            if len(row_list) < len(cols):
                                row_list.extend([None] * (len(cols) - len(row_list)))
                            elif len(row_list) > len(cols):
                                row_list = row_list[:len(cols)]
                            clean_rows.append(row_list)
                        
                        df = pd.DataFrame(clean_rows, columns=cols)
                        
                except Exception as e2:
                    errors.append(f"openpyxl读取失败: {str(e2)}")
        
        elif filename.lower().endswith('.csv'):
            # CSV文件处理
            encodings = ['utf-8', 'gbk', 'gb2312', 'utf-8-sig', 'latin1']
            for encoding in encodings:
                try:
                    df = pd.read_csv(io.BytesIO(file_data), encoding=encoding, nrows=lines)
                    break
                except UnicodeDecodeError:
                    continue
                except Exception as e:
                    errors.append(f"CSV读取失败({encoding}): {str(e)}")
        
        if df is None:
            raise ValueError(f"表格解析失败: {'; '.join(errors)}")
        
        # 数据清理和JSON序列化兼容性处理
        df = df.dropna(how='all')
        if len(df) > lines:
            df = df.head(lines)
        
        # 处理NaN、inf等不兼容JSON的值
        import numpy as np
        
        # 将所有数值列中的无穷大和NaN值替换为None
        for col in df.columns:
            if df[col].dtype in ['float64', 'float32', 'int64', 'int32']:
                df[col] = df[col].replace([np.inf, -np.inf, np.nan], None)
        
        # 确保所有NaN值都被替换为None
        df = df.where(pd.notnull(df), None)
        
        # 根据预览方法返回不同格式
        if method == 'table_view':
            return {
                'content_type': 'table',
                'columns': list(df.columns),
                'data': df.to_dict('records'),
                'total_rows': len(df),
                'total_columns': len(df.columns),
                'message': f'显示前 {len(df)} 行数据'
            }
        elif method == 'html_preview':
            html_content = df.to_html(classes='table table-striped', table_id='preview-table')
            return {
                'content_type': 'html',
                'html_content': html_content,
                'message': f'HTML表格预览 ({len(df)} 行)'
            }
        else:
            raise HTTPException(status_code=400, detail=f"表格文档不支持预览方法: {method}")
            
    except Exception as e:
        logger.error(f"表格预览处理失败: {e}")
        raise HTTPException(status_code=500, detail=f"表格预览失败: {str(e)}")


async def process_pdf_preview(file_data: bytes, filename: str, method: str, page: int) -> Dict[str, Any]:
    """处理PDF文档预览"""
    try:
        if method == 'pdf_viewer':
            # 返回PDF的base64编码，供前端PDF查看器使用
            pdf_base64 = base64.b64encode(file_data).decode('utf-8')
            return {
                'content_type': 'pdf',
                'pdf_data': pdf_base64,
                'current_page': page,
                'message': 'PDF文档预览'
            }
        elif method == 'image_preview':
            # 这里需要安装pdf2image库来将PDF转换为图片
            # 暂时返回提示信息
            return {
                'content_type': 'message',
                'message': 'PDF图片预览功能需要安装pdf2image库',
                'suggestion': '请使用PDF查看器预览'
            }
        else:
            raise HTTPException(status_code=400, detail=f"PDF文档不支持预览方法: {method}")
            
    except Exception as e:
        logger.error(f"PDF预览处理失败: {e}")
        raise HTTPException(status_code=500, detail=f"PDF预览失败: {str(e)}")


async def process_document_preview_handler(file_data: bytes, filename: str, method: str) -> Dict[str, Any]:
    """处理Word文档预览"""
    try:
        if method == 'html_preview':
            # 这里需要使用python-docx或mammoth库来转换Word文档
            # 暂时返回提示信息
            return {
                'content_type': 'message',
                'message': 'Word文档HTML预览功能开发中',
                'suggestion': '请下载文件使用Office软件查看'
            }
        elif method == 'text_extract':
            # 提取纯文本内容
            return {
                'content_type': 'message',
                'message': 'Word文档文本提取功能开发中',
                'suggestion': '请下载文件使用Office软件查看'
            }
        else:
            raise HTTPException(status_code=400, detail=f"Word文档不支持预览方法: {method}")
            
    except Exception as e:
        logger.error(f"Word文档预览处理失败: {e}")
        raise HTTPException(status_code=500, detail=f"Word文档预览失败: {str(e)}")


async def process_presentation_preview(file_data: bytes, filename: str, method: str, page: int) -> Dict[str, Any]:
    """处理PowerPoint文档预览"""
    try:
        if method == 'slide_preview':
            return {
                'content_type': 'message',
                'message': 'PowerPoint幻灯片预览功能开发中',
                'suggestion': '请下载文件使用Office软件查看'
            }
        else:
            raise HTTPException(status_code=400, detail=f"PowerPoint文档不支持预览方法: {method}")
            
    except Exception as e:
        logger.error(f"PowerPoint预览处理失败: {e}")
        raise HTTPException(status_code=500, detail=f"PowerPoint预览失败: {str(e)}")


async def process_text_preview(file_data: bytes, filename: str, method: str, lines: int) -> Dict[str, Any]:
    """处理文本文档预览"""
    try:
        # 尝试不同编码解码文本
        encodings = ['utf-8', 'gbk', 'gb2312', 'utf-8-sig', 'latin1']
        text_content = None
        used_encoding = None
        
        for encoding in encodings:
            try:
                text_content = file_data.decode(encoding)
                used_encoding = encoding
                break
            except UnicodeDecodeError:
                continue
        
        if text_content is None:
            raise ValueError("无法解码文本文件，可能是二进制文件")
        
        # 限制行数
        text_lines = text_content.split('\n')
        if len(text_lines) > lines:
            text_lines = text_lines[:lines]
            text_content = '\n'.join(text_lines)
            truncated = True
        else:
            truncated = False
        
        if method == 'text_view':
            return {
                'content_type': 'text',
                'text_content': text_content,
                'encoding': used_encoding,
                'total_lines': len(text_lines),
                'truncated': truncated,
                'message': f'文本预览 ({len(text_lines)} 行, {used_encoding} 编码)'
            }
        elif method == 'syntax_highlight':
            # 根据文件扩展名确定语法高亮类型
            ext = Path(filename).suffix.lower()
            language_map = {
                '.py': 'python',
                '.js': 'javascript',
                '.json': 'json',
                '.xml': 'xml',
                '.html': 'html',
                '.css': 'css',
                '.sql': 'sql',
                '.md': 'markdown'
            }
            language = language_map.get(ext, 'text')
            
            return {
                'content_type': 'code',
                'text_content': text_content,
                'language': language,
                'encoding': used_encoding,
                'total_lines': len(text_lines),
                'truncated': truncated,
                'message': f'代码预览 ({language}, {len(text_lines)} 行)'
            }
        else:
            raise HTTPException(status_code=400, detail=f"文本文档不支持预览方法: {method}")
            
    except Exception as e:
        logger.error(f"文本预览处理失败: {e}")
        raise HTTPException(status_code=500, detail=f"文本预览失败: {str(e)}")


async def process_image_preview(file_data: bytes, filename: str, method: str) -> Dict[str, Any]:
    """处理图片文档预览"""
    try:
        if method == 'image_view':
            # 返回图片的base64编码
            ext = Path(filename).suffix.lower()
            mime_type_map = {
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.png': 'image/png',
                '.gif': 'image/gif',
                '.bmp': 'image/bmp',
                '.webp': 'image/webp',
                '.svg': 'image/svg+xml'
            }
            mime_type = mime_type_map.get(ext, 'image/jpeg')
            
            image_base64 = base64.b64encode(file_data).decode('utf-8')
            return {
                'content_type': 'image',
                'image_data': image_base64,
                'mime_type': mime_type,
                'file_size': len(file_data),
                'message': f'图片预览 ({ext.upper()}, {len(file_data)} 字节)'
            }
        else:
            raise HTTPException(status_code=400, detail=f"图片文档不支持预览方法: {method}")
            
    except Exception as e:
        logger.error(f"图片预览处理失败: {e}")
        raise HTTPException(status_code=500, detail=f"图片预览失败: {str(e)}")