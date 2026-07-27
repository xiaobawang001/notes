"""笔记 CRUD API 路由"""
from fastapi import APIRouter, Depends, HTTPException, Query

from app.schemas.common import StandardResponse
from app.schemas.note import NoteCreate, NoteUpdate, NoteListParams
from app.services.note_service import NoteService
from app.core.deps import require_current_user, get_current_user

router = APIRouter(prefix="/notes", tags=["笔记"])


@router.get("", response_model=StandardResponse)
async def list_notes(
    type_: str | None = Query(None, alias="type", pattern="^(folder|article)$"),
    status: str | None = Query(None, alias="status", pattern="^(draft|published)$"),
    parent_id: int | None = Query(None),
    search: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=500),
    user: dict | None = Depends(get_current_user),
):
    """笔记列表：如果已登录则只看自己的，否则只看公开的"""
    svc = NoteService()
    if user:
        items, total = await svc.list_notes(
            user_id=user["id"], type_=type_, status=status,
            parent_id=parent_id, keyword=search,
            page=page, page_size=page_size,
        )
    else:
        items, total = await svc.get_public_list(page=page, page_size=page_size)
    return StandardResponse(data={
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
    })


@router.get("/categories", response_model=StandardResponse)
async def get_categories(user: dict | None = Depends(get_current_user)):
    """目录树（公开或按用户过滤）"""
    from app.services.tree_service import TreeService
    svc = TreeService()
    user_id = user["id"] if user else None
    tree = await svc.build_tree(user_id)
    return StandardResponse(data=tree)


@router.get("/search", response_model=StandardResponse)
async def search_notes(
    q: str = Query(..., min_length=1, description="搜索关键词"),
    user: dict | None = Depends(get_current_user),
):
    """全文搜索已发布文章"""
    from app.services.search_service import SearchService
    svc = SearchService()
    user_id = user["id"] if user else None
    items = await svc.search(q, user_id)
    return StandardResponse(data={"items": items, "total": len(items)})


@router.get("/{note_id}", response_model=StandardResponse)
async def get_note(note_id: int):
    """文章详情（通过 ID）"""
    svc = NoteService()
    try:
        note = await svc.get_note(note_id)
        return StandardResponse(data=note)
    except ValueError as e:
        raise HTTPException(status_code=404, detail={"code": 404, "msg": str(e)})


@router.get("/slug/{slug}", response_model=StandardResponse)
async def get_note_by_slug(slug: str):
    """文章详情（通过 slug，公开）"""
    svc = NoteService()
    try:
        note = await svc.get_note_by_slug(slug)
        return StandardResponse(data=note)
    except ValueError as e:
        raise HTTPException(status_code=404, detail={"code": 404, "msg": str(e)})


@router.post("", response_model=StandardResponse, status_code=201)
async def create_note(req: NoteCreate, user: dict = Depends(require_current_user)):
    """创建笔记（需登录）"""
    svc = NoteService()
    try:
        note = await svc.create(user["id"], req)
        return StandardResponse(data=note, msg="创建成功")
    except ValueError as e:
        raise HTTPException(status_code=400, detail={"code": 400, "msg": str(e)})
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail={"code": 500, "msg": str(e)})


@router.put("/{note_id}", response_model=StandardResponse)
async def update_note(
    note_id: int, req: NoteUpdate, user: dict = Depends(require_current_user),
):
    """更新笔记（需登录，只能编辑自己的笔记）"""
    svc = NoteService()
    try:
        note = await svc.update(note_id, user["id"], req)
        return StandardResponse(data=note, msg="更新成功")
    except PermissionError as e:
        raise HTTPException(status_code=403, detail={"code": 403, "msg": str(e)})
    except ValueError as e:
        raise HTTPException(status_code=404, detail={"code": 404, "msg": str(e)})


@router.delete("/{note_id}", response_model=StandardResponse)
async def delete_note(note_id: int, user: dict = Depends(require_current_user)):
    """删除笔记（需登录，只能删除自己的笔记）"""
    svc = NoteService()
    try:
        await svc.delete(note_id, user["id"])
        return StandardResponse(msg="删除成功")
    except PermissionError as e:
        raise HTTPException(status_code=403, detail={"code": 403, "msg": str(e)})
    except ValueError as e:
        raise HTTPException(status_code=404, detail={"code": 404, "msg": str(e)})
