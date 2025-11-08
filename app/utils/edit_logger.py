"""編輯日誌記錄工具"""
from __future__ import annotations

from flask import request
from flask_login import current_user

from ..extensions import db
from ..models import EditLog, EditLogAction, EditLogTarget


def log_edit(
    action: EditLogAction,
    target_type: EditLogTarget,
    target_id: int | None = None,
    target_name: str | None = None,
    description: str | None = None,
) -> EditLog:
    """記錄編輯動作"""
    
    # 取得 IP 和 User Agent
    ip_address = request.remote_addr
    user_agent = request.headers.get('User-Agent', '')
    
    log_entry = EditLog(
        user_id=current_user.id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        target_name=target_name,
        description=description,
        ip_address=ip_address,
        user_agent=user_agent[:500] if user_agent else None  # 限制長度
    )
    
    db.session.add(log_entry)
    db.session.commit()
    
    return log_entry


def log_keyword_create(keyword_id: int, keyword_title: str) -> EditLog:
    """記錄建立關鍵字"""
    return log_edit(
        action=EditLogAction.CREATE,
        target_type=EditLogTarget.KEYWORD,
        target_id=keyword_id,
        target_name=keyword_title,
        description=f"建立關鍵字「{keyword_title}」"
    )


def log_keyword_update(keyword_id: int, keyword_title: str, changes: str | None = None) -> EditLog:
    """記錄更新關鍵字"""
    description = f"更新關鍵字「{keyword_title}」"
    if changes:
        description += f": {changes}"
    
    return log_edit(
        action=EditLogAction.UPDATE,
        target_type=EditLogTarget.KEYWORD,
        target_id=keyword_id,
        target_name=keyword_title,
        description=description
    )


def log_keyword_delete(keyword_id: int, keyword_title: str) -> EditLog:
    """記錄刪除關鍵字"""
    return log_edit(
        action=EditLogAction.DELETE,
        target_type=EditLogTarget.KEYWORD,
        target_id=keyword_id,
        target_name=keyword_title,
        description=f"刪除關鍵字「{keyword_title}」"
    )


def log_keyword_visibility(keyword_id: int, keyword_title: str, is_public: bool) -> EditLog:
    """記錄關鍵字可見性變更"""
    action = EditLogAction.PUBLISH if is_public else EditLogAction.UNPUBLISH
    status = "公開" if is_public else "隱藏"
    
    return log_edit(
        action=action,
        target_type=EditLogTarget.KEYWORD,
        target_id=keyword_id,
        target_name=keyword_title,
        description=f"將關鍵字「{keyword_title}」設為{status}"
    )


def log_keyword_move(keyword_id: int, keyword_title: str, from_category: str, to_category: str) -> EditLog:
    """記錄關鍵字移動"""
    return log_edit(
        action=EditLogAction.MOVE,
        target_type=EditLogTarget.KEYWORD,
        target_id=keyword_id,
        target_name=keyword_title,
        description=f"將關鍵字「{keyword_title}」從「{from_category}」移動到「{to_category}」"
    )


def log_category_create(category_id: int, category_name: str) -> EditLog:
    """記錄建立分類"""
    return log_edit(
        action=EditLogAction.CREATE,
        target_type=EditLogTarget.CATEGORY,
        target_id=category_id,
        target_name=category_name,
        description=f"建立分類「{category_name}」"
    )


def log_category_update(category_id: int, category_name: str) -> EditLog:
    """記錄更新分類"""
    return log_edit(
        action=EditLogAction.UPDATE,
        target_type=EditLogTarget.CATEGORY,
        target_id=category_id,
        target_name=category_name,
        description=f"更新分類「{category_name}」"
    )


def log_category_delete(category_id: int, category_name: str, keyword_count: int) -> EditLog:
    """記錄刪除分類"""
    description = f"刪除分類「{category_name}」"
    if keyword_count > 0:
        description += f" (包含 {keyword_count} 筆關鍵字)"
    
    return log_edit(
        action=EditLogAction.DELETE,
        target_type=EditLogTarget.CATEGORY,
        target_id=category_id,
        target_name=category_name,
        description=description
    )


def log_user_action(action: EditLogAction, user_id: int, username: str, description: str) -> EditLog:
    """記錄用戶相關動作"""
    return log_edit(
        action=action,
        target_type=EditLogTarget.USER,
        target_id=user_id,
        target_name=username,
        description=description
    )
