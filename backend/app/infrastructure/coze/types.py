"""Coze API 类型定义"""
from dataclasses import dataclass, field
from typing import Optional, Any


class CozeOperation:
    """Coze 查询操作符"""
    EQUAL = "="
    NOT_EQUAL = "!="
    GREATER_THAN = ">"
    GREATER_THAN_OR_EQUAL = ">="
    LESS_THAN = "<"
    LESS_THAN_OR_EQUAL = "<="
    LIKE = "like"
    IS_NULL = "is_null"
    IS_NOT_NULL = "is_not_null"


class CozeLogic:
    """Coze 逻辑连接符"""
    AND = "and"
    OR = "or"


@dataclass
class CozeCondition:
    """单个查询条件"""
    left: str                          # 字段名
    operation: str                     # 操作符
    right: Optional[str] = None        # 比较值


@dataclass
class CozeFilter:
    """组合查询条件"""
    logic: str                                   # "and" / "or"
    conditions: list["CozeCondition | CozeFilter"] = field(default_factory=list)
