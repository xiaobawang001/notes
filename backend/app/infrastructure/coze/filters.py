"""Coze 查询条件构建器"""
from app.infrastructure.coze.types import (
    CozeCondition,
    CozeFilter,
    CozeOperation,
    CozeLogic,
)


def _to_dict(cond: "CozeCondition | CozeFilter") -> dict:
    """将 Condition 或 Filter 序列化为 dict（递归）"""
    if isinstance(cond, CozeCondition):
        d: dict = {"left": cond.left, "operation": cond.operation}
        if cond.right is not None:
            d["right"] = cond.right
        return d
    if isinstance(cond, CozeFilter):
        return {
            "logic": cond.logic,
            "conditions": [_to_dict(c) for c in cond.conditions],
        }
    raise TypeError(f"Unknown condition type: {type(cond)}")


def to_filter_dict(filter_obj: CozeFilter) -> dict:
    """将 CozeFilter 序列化为 Coze API 使用的 filter JSON"""
    return _to_dict(filter_obj)


def condition(
    left: str,
    operation: str,
    right: str | int | bool | None = None,
) -> CozeCondition:
    """构建单个查询条件，right 自动转为字符串"""
    return CozeCondition(
        left=left,
        operation=operation,
        right=str(right) if right is not None else None,
    )


def and_(*conds: "CozeCondition | CozeFilter") -> CozeFilter:
    """AND 组合多个条件"""
    return CozeFilter(logic=CozeLogic.AND, conditions=list(conds))


def or_(*conds: "CozeCondition | CozeFilter") -> CozeFilter:
    """OR 组合多个条件"""
    return CozeFilter(logic=CozeLogic.OR, conditions=list(conds))


def empty_or_null(field: str) -> CozeFilter:
    """构建"为空或 NULL"的 OR 条件"""
    return or_(
        condition(field, CozeOperation.EQUAL, ""),
        condition(field, CozeOperation.IS_NULL),
    )


def not_deleted_filter() -> CozeCondition:
    """软删除过滤：is_deleted = 0"""
    return condition("is_deleted", CozeOperation.EQUAL, "0")
