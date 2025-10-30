from pydantic import BaseModel
from typing import Optional, List

class UserInput(BaseModel):
    user_input: str
    user_id: int = 1  # 默认为1,临时使用固定用户ID
    dataset_ids: Optional[List[str]] = None  # 用户选中的数据集ID列表，支持多数据集查询

class FilePathInput(BaseModel):
    file_path: str