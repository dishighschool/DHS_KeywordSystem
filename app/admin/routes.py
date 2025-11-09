"""Admin and contributor dashboard routes."""
from __future__ import annotations

import os
from functools import wraps
from pathlib import Path
from typing import Any, Callable
from werkzeug.utils import secure_filename

from flask import Blueprint, abort, current_app, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from ..extensions import db
from ..sitemap import sitemap_manager
from ..forms import (
    AnnouncementBannerForm,
    CategoryForm,
    FooterLinkForm,
    KeywordForm,
    NavigationLinkForm,
    RegistrationKeyManagerForm,
    SiteBrandingForm,
)
from ..models import (
    AnnouncementBanner,
    FooterSocialLink,
    KeywordAlias,
    KeywordCategory,
    KeywordGoalItem,
    KeywordGoalList,
    LearningKeyword,
    NavigationLink,
    Role,
    SiteSetting,
    SiteSettingKey,
    User,
    YouTubeVideo,
    slugify,
)


def admin_required(func: Callable[..., Any]) -> Callable[..., Any]:
    """Ensure the current user is an administrator before executing a view."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            content_type = request.headers.get("Content-Type", "")
            accepts = request.accept_mimetypes.best
            expects_json = (
                request.is_json
                or content_type.startswith("application/json")
                or accepts == "application/json"
            )
            if expects_json:
                return jsonify({"success": False, "message": "需要管理員權限"}), 403
            abort(403)
        return func(*args, **kwargs)

    return wrapper


admin_bp = Blueprint("admin", __name__, template_folder="../templates/admin")


def allowed_file(filename: str) -> bool:
    """Check if a file extension is allowed for upload."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in current_app.config.get("ALLOWED_EXTENSIONS", set())


def save_uploaded_file(file, prefix: str = "logo") -> str | None:
    """Save an uploaded file and return the relative URL path."""
    if not file or file.filename == "":
        return None
    
    if not allowed_file(file.filename):
        return None
    
    filename = secure_filename(file.filename)
    # Add timestamp to prevent overwriting
    import time
    name, ext = os.path.splitext(filename)
    unique_filename = f"{prefix}_{int(time.time())}_{name}{ext}"
    
    upload_folder = Path(current_app.config["UPLOAD_FOLDER"])
    upload_folder.mkdir(parents=True, exist_ok=True)
    
    filepath = upload_folder / unique_filename
    file.save(filepath)
    
    # Return URL path relative to static folder
    return f"/static/uploads/{unique_filename}"


def delete_uploaded_file(file_path: str) -> bool:
    """Delete an uploaded file if it exists."""
    if not file_path or not file_path.startswith("/static/uploads/"):
        return False
    
    try:
        # Convert URL path to filesystem path
        filename = file_path.replace("/static/uploads/", "")
        upload_folder = Path(current_app.config["UPLOAD_FOLDER"])
        filepath = upload_folder / filename
        
        if filepath.exists() and filepath.is_file():
            filepath.unlink()
            return True
    except Exception as e:
        current_app.logger.error(f"Failed to delete file {file_path}: {e}")
    
    return False


@admin_bp.before_request
@login_required
def ensure_authenticated():  # pragma: no cover - integration guard
    """Require authentication for all dashboard routes."""
    return None


@admin_bp.post("/api/markdown-preview")
@login_required
def markdown_preview():
    """API endpoint to render markdown preview with same processing as frontend."""
    from html import unescape
    from markdown2 import markdown
    
    # 取得 JSON 或 form data
    if request.is_json:
        data = request.get_json()
    else:
        data = request.form.to_dict()
    
    if not data or 'markdown' not in data:
        return jsonify({'error': 'No markdown content provided', 'success': False}), 400
    
    markdown_text = data.get('markdown', '')
    
    try:
        # Apply same processing as frontend: unescape then convert to HTML
        html = markdown(
            unescape(markdown_text),
            extras=["fenced-code-blocks", "tables", "strikethrough", "task_lists"],
            safe_mode="escape"
        )
        return jsonify({'html': html, 'success': True})
    except Exception as e:
        current_app.logger.error(f"Markdown preview error: {e}")
        return jsonify({'error': str(e), 'success': False}), 500


@admin_bp.get("/")
def dashboard():
    """Render a role-aware dashboard overview."""
    my_keywords = (
        LearningKeyword.query.filter_by(author_id=current_user.id)
        .order_by(LearningKeyword.created_at.desc())
        .all()
    )

    stats = None
    if current_user.is_admin():
        stats = {
            "keywords": LearningKeyword.query.count(),
            "categories": KeywordCategory.query.count(),
            "nav_links": NavigationLink.query.count(),
            "total_users": User.query.count(),
            "admin_users": User.query.filter_by(role=Role.ADMIN).count(),
            "active_users": User.query.filter(User.active.is_(True)).count(),
        }

    return render_template("admin/dashboard.html", my_keywords=my_keywords, stats=stats)


@admin_bp.route("/profile", methods=["GET", "POST"])
def edit_profile():
    """用戶編輯個人資料"""
    from ..forms import UserProfileForm
    
    form = UserProfileForm(obj=current_user)
    
    if form.validate_on_submit():
        # 更新成員名稱
        current_user.username = form.username.data
        db.session.commit()
        
        flash("個人資料已更新。", "success")
        return redirect(url_for("admin.edit_profile"))
    
    return render_template("admin/profile.html", form=form)


@admin_bp.get("/sortable-demo")
@admin_required
def sortable_demo():
    """Demo page showing drag-and-drop sorting features."""
    return render_template("admin/sortable_demo.html")


@admin_bp.route("/keywords", methods=["GET", "POST"])
def manage_keywords():
    """舊的關鍵字管理頁面 - 重定向到新的內容管理中心"""
    return redirect(url_for("admin.content_manager"))


@admin_bp.route("/content-manager", methods=["GET"])
def content_manager():
    """新的內容管理中心 - YouTube Studio 風格"""
    # 取得所有分類及其關鍵字
    categories = KeywordCategory.query.order_by(KeywordCategory.position.asc()).all()
    
    # 所有成員都可以看到所有關鍵字
    for category in categories:
        category.keywords = LearningKeyword.query.filter_by(
            category_id=category.id
        ).order_by(LearningKeyword.position.asc()).all()
    
    # 計算統計資訊
    total_keywords = sum(len(cat.keywords) for cat in categories)
    public_keywords = sum(1 for cat in categories for kw in cat.keywords if kw.is_public)
    
    return render_template(
        "admin/content_manager.html",
        categories=categories,
        total_keywords=total_keywords,
        public_keywords=public_keywords
    )


@admin_bp.route("/keywords/new", methods=["GET", "POST"])
def create_keyword():
    """Create a new learning keyword entry - redirects to studio editor."""
    return redirect(url_for("admin.create_keyword_studio"))


@admin_bp.route("/keywords/create", methods=["GET"])
def create_keyword_studio():
    """YouTube Studio-style keyword creator."""
    form = KeywordForm()
    _assign_category_choices(form)

    if not form.category_id.choices:
        flash("請先建立分類才能新增關鍵字。", "warning")
        return redirect(url_for("admin.manage_categories"))

    # 設定預設值
    form.is_public.data = True
    form.seo_auto_generate.data = True
    
    # 檢查是否從目標清單項目來的
    from_goal_item = request.args.get('from_goal_item', type=int)
    goal_item = None
    
    if from_goal_item:
        goal_item = KeywordGoalItem.query.get(from_goal_item)
        if goal_item:
            # 預填標題
            form.title.data = request.args.get('title', goal_item.title)
            
            # 預填分類 (如果存在)
            category_name = request.args.get('category', goal_item.goal_list.category_name)
            category = KeywordCategory.query.filter_by(name=category_name).first()
            
            if not category:
                # 自動創建分類
                category = KeywordCategory(
                    name=category_name,
                    slug=slugify(category_name),
                    icon="bi-folder"
                )
                db.session.add(category)
                db.session.commit()
                flash(f"已自動創建分類「{category_name}」", "info")
                # 重新加載分類選項
                _assign_category_choices(form)
            
            if category:
                form.category_id.data = category.id

    return render_template("admin/keyword_editor.html", form=form, keyword=None, is_creating=True, goal_item=goal_item)


@admin_bp.route("/keywords/store", methods=["POST"])
def store_keyword():
    """Store new keyword from editor."""
    form = KeywordForm()
    _assign_category_choices(form)

    if form.validate_on_submit():
        from app.utils.seo import generate_seo_html
        from app.utils.edit_logger import log_keyword_create
        
        keyword = LearningKeyword(
            title=form.title.data,
            slug=slugify(form.title.data or ""),  # 自動根據標題生成 slug
            description_markdown=form.description_markdown.data,
            category_id=form.category_id.data,
            author_id=current_user.id,
            is_public=form.is_public.data,
            seo_auto_generate=form.seo_auto_generate.data,
            seo_content=form.seo_content.data if not form.seo_auto_generate.data else None,
        )
        
        _apply_video_updates(keyword, form)
        _apply_alias_updates(keyword, form)
        db.session.add(keyword)
        db.session.flush()  # 取得 keyword.id
        
        # 如果啟用自動生成,生成初始 SEO 內容
        if keyword.seo_auto_generate:
            all_aliases = [a.title for a in keyword.aliases]
            keyword.seo_content = generate_seo_html(keyword.title, aliases=all_aliases)
        
        # 檢查是否從目標清單項目來的,如果是則標記為完成
        from_goal_item = request.form.get('from_goal_item', type=int)
        goal_item_for_redirect = None
        if from_goal_item:
            goal_item_for_redirect = KeywordGoalItem.query.get(from_goal_item)
            if goal_item_for_redirect and not goal_item_for_redirect.is_completed:
                from datetime import datetime
                goal_item_for_redirect.is_completed = True
                goal_item_for_redirect.keyword_id = keyword.id
                goal_item_for_redirect.completed_by = current_user.id
                goal_item_for_redirect.completed_at = datetime.utcnow()
                flash(f"已完成目標項目「{goal_item_for_redirect.title}」", "success")
        
        db.session.commit()
        
        # 記錄編輯日誌
        log_keyword_create(keyword.id, keyword.title or "")
        
        flash("已新增學習關鍵字。", "success")
        
        # 如果是從目標清單來的,返回目標清單頁面
        if goal_item_for_redirect:
            return redirect(url_for("admin.view_goal_list", list_id=goal_item_for_redirect.goal_list_id))
        
        return redirect(url_for("admin.content_manager"))

    # If validation fails, return to creator with errors
    # 設定預設值
    form.is_public.data = True
    form.seo_auto_generate.data = True
    
    # 檢查是否從目標清單項目來的
    from_goal_item = request.form.get('from_goal_item', type=int)
    goal_item = None
    
    if from_goal_item:
        goal_item = KeywordGoalItem.query.get(from_goal_item)
    
    return render_template("admin/keyword_editor.html", form=form, keyword=None, is_creating=True, goal_item=goal_item)


@admin_bp.post("/keywords/quick-create")
def quick_create_keyword():
    """快速建立關鍵字 (從 Modal)"""
    title = request.form.get('title', '').strip()
    category_id = request.form.get('category_id')
    description_markdown = request.form.get('description_markdown', '').strip()
    is_public = request.form.get('is_public') == 'on'
    continue_edit = request.form.get('continue_edit') == '1'
    
    if not title:
        flash("關鍵字標題不能為空。", "danger")
        return redirect(url_for("admin.content_manager"))
    
    if not category_id:
        flash("請選擇所屬分類。", "danger")
        return redirect(url_for("admin.content_manager"))
    
    try:
        category_id = int(category_id)
        category = KeywordCategory.query.get(category_id)
        if not category:
            flash("所選分類不存在。", "danger")
            return redirect(url_for("admin.content_manager"))
    except (ValueError, TypeError):
        flash("無效的分類。", "danger")
        return redirect(url_for("admin.content_manager"))
    
    # 建立關鍵字
    keyword = LearningKeyword(
        title=title,
        description_markdown=description_markdown if description_markdown else None,
        category_id=category_id,
        author_id=current_user.id,
        is_public=is_public,
        seo_auto_generate=True
    )
    
    db.session.add(keyword)
    db.session.flush()
    
    # 自動生成 SEO 內容
    from app.utils.seo import generate_seo_html
    keyword.seo_content = generate_seo_html(keyword.title)
    
    db.session.commit()
    
    flash(f"已建立關鍵字「{title}」。", "success")
    
    # 如果選擇繼續編輯,跳轉到編輯頁面
    if continue_edit:
        return redirect(url_for("admin.edit_keyword", keyword_id=keyword.id))
    
    return redirect(url_for("admin.content_manager"))


@admin_bp.route("/keywords/<int:keyword_id>/edit", methods=["GET", "POST"])
def edit_keyword(keyword_id: int):
    """Edit an existing keyword entry - redirects to new editor."""
    keyword = LearningKeyword.query.get_or_404(keyword_id)
    # 團隊成員可以編輯所有關鍵字，管理員也可以編輯所有關鍵字
    return redirect(url_for("admin.edit_keyword_studio", keyword_id=keyword_id))


@admin_bp.route("/keywords/<int:keyword_id>/editor", methods=["GET"])
def edit_keyword_studio(keyword_id: int):
    """YouTube Studio-style keyword editor."""
    keyword = LearningKeyword.query.get_or_404(keyword_id)
    # 所有成員都可以編輯所有關鍵字

    form = KeywordForm(obj=keyword)
    _assign_category_choices(form)
    _populate_video_entries(form, keyword)
    _populate_alias_entries(form, keyword)

    return render_template("admin/keyword_editor.html", form=form, keyword=keyword)


@admin_bp.route("/keywords/<int:keyword_id>/save", methods=["POST"])
def save_keyword_editor(keyword_id: int):
    """Save keyword from editor."""
    from app.utils.edit_logger import log_keyword_update
    
    keyword = LearningKeyword.query.get_or_404(keyword_id)
    # 所有成員都可以編輯所有關鍵字

    form = KeywordForm(obj=keyword)
    _assign_category_choices(form)

    if form.validate_on_submit():
        keyword.title = (form.title.data or "").strip()
        keyword.slug = slugify(keyword.title)
        keyword.description_markdown = form.description_markdown.data
        keyword.category_id = form.category_id.data
        keyword.is_public = form.is_public.data
        keyword.seo_auto_generate = form.seo_auto_generate.data
        keyword.seo_content = form.seo_content.data if form.seo_content.data else None

        _apply_video_updates(keyword, form)
        _apply_alias_updates(keyword, form)
        db.session.commit()
        
        # 記錄編輯日誌
        log_keyword_update(keyword.id, keyword.title)

        flash("已更新學習關鍵字。", "success")
        return redirect(url_for("admin.content_manager"))

    # If validation fails, return to editor with errors
    _populate_video_entries(form, keyword)
    _populate_alias_entries(form, keyword)
    return render_template("admin/keyword_editor.html", form=form, keyword=keyword, is_creating=False)


@admin_bp.route("/keywords/<int:keyword_id>/regenerate-seo", methods=["POST"])
def regenerate_keyword_seo(keyword_id: int):
    """Regenerate SEO content for keyword."""
    keyword = LearningKeyword.query.get_or_404(keyword_id)
    # 所有成員都可以操作所有關鍵字

    try:
        from ..utils.seo import generate_seo_html
        all_aliases = [a.title for a in keyword.aliases]
        keyword.seo_content = generate_seo_html(keyword.title, aliases=all_aliases)
        keyword.seo_auto_generate = True
        db.session.commit()
        
        return jsonify({
            "success": True,
            "seo_content": keyword.seo_content,
            "message": "SEO 內容已重新生成"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"生成失敗: {str(e)}"
        }), 500


@admin_bp.route("/keywords/<int:keyword_id>/save-draft", methods=["POST"])
def save_keyword_draft(keyword_id: int):
    """Auto-save draft for keyword."""
    keyword = LearningKeyword.query.get_or_404(keyword_id)
    # 所有成員都可以操作所有關鍵字

    try:
        # Save basic fields only for draft
        if request.form.get('title'):
            keyword.title = request.form.get('title')
        if request.form.get('description_markdown'):
            keyword.description_markdown = request.form.get('description_markdown')
        
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "草稿已儲存"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"儲存失敗: {str(e)}"
        }), 500


@admin_bp.post("/keywords/<int:keyword_id>/delete")
@admin_required
def delete_keyword(keyword_id: int):
    """Delete a keyword entry (admin only)."""
    from app.utils.edit_logger import log_keyword_delete
    
    keyword = LearningKeyword.query.get_or_404(keyword_id)
    keyword_title = keyword.title
    
    db.session.delete(keyword)
    db.session.commit()
    
    # 記錄編輯日誌
    log_keyword_delete(keyword_id, keyword_title)
    
    flash("已刪除學習關鍵字。", "info")
    return redirect(url_for("admin.content_manager"))


@admin_bp.route("/categories", methods=["GET", "POST"])
@admin_required
def manage_categories():
    """Create and list keyword categories (admin only)."""
    form = CategoryForm()

    if form.validate_on_submit():
        from ..models import slugify
        
        # Generate slug if not provided
        slug = form.slug.data.strip() if form.slug.data else slugify(form.name.data or "")
        
        category = KeywordCategory(
            name=form.name.data,
            slug=slug,
            description=form.description.data,
            icon=form.icon.data or "bi-folder",
            is_public=form.is_public.data,
        )
        db.session.add(category)
        db.session.commit()
        flash("已建立分類。", "success")
        return redirect(url_for("admin.manage_keywords"))

    categories = KeywordCategory.query.order_by(KeywordCategory.position.asc()).all()
    return render_template("admin/categories.html", form=form, categories=categories)


@admin_bp.route("/categories/<int:category_id>/edit", methods=["GET", "POST"])
@admin_required
def edit_category(category_id: int):
    """Edit an existing category (admin only)."""
    category = KeywordCategory.query.get_or_404(category_id)
    form = CategoryForm(obj=category)

    if form.validate_on_submit():
        from ..models import slugify
        
        category.name = form.name.data
        # Update slug if provided, otherwise regenerate from name
        category.slug = form.slug.data.strip() if form.slug.data else slugify(form.name.data or "")
        category.description = form.description.data
        category.icon = form.icon.data or "bi-folder"
        category.is_public = form.is_public.data
        db.session.commit()
        flash("已更新分類。", "success")
        return redirect(url_for("admin.content_manager"))

    return render_template("admin/category_form.html", form=form, category=category)


@admin_bp.post("/categories/quick-create")
@admin_required
def quick_create_category():
    """快速建立分類 (從 Modal)"""
    name = request.form.get('name', '').strip()
    description = request.form.get('description', '').strip()
    icon = request.form.get('icon', 'bi-folder').strip()
    is_public = request.form.get('is_public') == 'on'
    
    if not name:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'message': '分類名稱不能為空'}), 400
        flash("分類名稱不能為空。", "danger")
        return redirect(url_for("admin.content_manager"))
    
    from ..models import slugify
    
    category = KeywordCategory(
        name=name,
        slug=slugify(name),  # 自動生成 slug
        description=description if description else None,
        icon=icon if icon else 'bi-folder',
        is_public=is_public
    )
    
    db.session.add(category)
    db.session.commit()
    
    # AJAX 請求回傳 JSON
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'success': True,
            'message': f'已建立分類「{name}」',
            'category': {
                'id': category.id,
                'name': category.name,
                'slug': category.slug,
                'icon': category.icon
            }
        })
    
    flash(f"已建立分類「{name}」。", "success")
    return redirect(url_for("admin.content_manager"))


@admin_bp.get("/categories/<int:category_id>/data")
@admin_required
def get_category_data(category_id: int):
    """取得分類資料 (用於編輯模態框)"""
    category = KeywordCategory.query.get_or_404(category_id)
    return jsonify({
        'id': category.id,
        'name': category.name,
        'slug': category.slug,
        'description': category.description,
        'icon': category.icon,
        'is_public': category.is_public
    })


@admin_bp.post("/categories/<int:category_id>/update")
@admin_required
def update_category(category_id: int):
    """更新分類 (從 Modal)"""
    category = KeywordCategory.query.get_or_404(category_id)
    
    name = request.form.get('name', '').strip()
    description = request.form.get('description', '').strip()
    icon = request.form.get('icon', '').strip()
    is_public = request.form.get('is_public') == 'on'
    
    if not name:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'message': '分類名稱不能為空'}), 400
        flash("分類名稱不能為空。", "danger")
        return redirect(url_for("admin.content_manager"))
    
    from ..models import slugify
    
    # 更新欄位
    category.name = name
    category.slug = slugify(name)  # 根據新名稱重新生成 slug
    category.description = description if description else None
    category.icon = icon if icon else 'bi-folder'
    category.is_public = is_public
    
    db.session.commit()
    
    # AJAX 請求回傳 JSON
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'success': True,
            'message': f'已更新分類「{name}」',
            'category': {
                'id': category.id,
                'name': category.name,
                'slug': category.slug,
                'icon': category.icon
            }
        })
    
    flash(f"已更新分類「{name}」。", "success")
    return redirect(url_for("admin.content_manager"))


@admin_bp.post("/categories/<int:category_id>/delete")
@admin_required
def delete_category(category_id: int):
    """Delete a category and all its keywords (admin only)."""
    category = KeywordCategory.query.get_or_404(category_id)
    
    # 刪除此分類下的所有關鍵字
    keyword_count = len(category.keywords)
    db.session.delete(category)
    db.session.commit()
    
    flash(f"已刪除分類「{category.name}」及其下 {keyword_count} 筆關鍵字。", "info")
    return redirect(url_for("admin.content_manager"))


@admin_bp.route("/navigation", methods=["GET", "POST"])
@admin_required
def manage_navigation():
    """舊的導航管理頁面 - 重定向到整合頁面"""
    return redirect(url_for("admin.site_settings"))


@admin_bp.post("/navigation/add")
@admin_required
def add_navigation_link():
    """快速新增導航連結"""
    form = NavigationLinkForm()
    
    if form.validate_on_submit():
        nav_link = NavigationLink(
            label=form.label.data,
            url=form.url.data,
            icon=form.icon.data,
            position=form.position.data or 0,
        )
        db.session.add(nav_link)
        db.session.commit()
        flash("已新增導航連結。", "success")
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{field}: {error}", "danger")
    
    return redirect(url_for("admin.site_settings"))


@admin_bp.route("/navigation/<int:link_id>/edit", methods=["POST"])
@admin_required
def edit_navigation(link_id: int):
    """Edit navigation link via AJAX."""
    nav_link = NavigationLink.query.get_or_404(link_id)
    
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "message": "無效的資料"}), 400
    
    try:
        if 'label' in data:
            nav_link.label = data['label'].strip()
        if 'url' in data:
            nav_link.url = data['url'].strip()
        if 'icon' in data:
            nav_link.icon = data['icon'].strip() if data['icon'] else None
        if 'position' in data:
            nav_link.position = int(data['position'])
        
        db.session.commit()
        return jsonify({
            "success": True,
            "message": "已更新導航連結",
            "link": {
                "id": nav_link.id,
                "label": nav_link.label,
                "url": nav_link.url,
                "icon": nav_link.icon,
                "position": nav_link.position
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": f"更新失敗: {str(e)}"}), 500


@admin_bp.post("/navigation/<int:link_id>/delete")
@admin_required
def delete_navigation(link_id: int):
    nav_link = NavigationLink.query.get_or_404(link_id)
    db.session.delete(nav_link)
    db.session.commit()
    flash("已刪除導航連結。", "info")
    return redirect(url_for("admin.manage_navigation"))


@admin_bp.route("/footer", methods=["GET", "POST"])
@admin_required
def manage_footer():
    """舊的底部連結頁面 - 重定向到整合頁面"""
    return redirect(url_for("admin.site_settings"))


@admin_bp.post("/footer/add")
@admin_required
def add_footer_link():
    """快速新增底部連結"""
    form = FooterLinkForm()

    if form.validate_on_submit():
        link = FooterSocialLink(
            label=form.label.data,
            url=form.url.data,
            icon=form.icon.data,
            position=form.position.data or 0,
        )
        db.session.add(link)
        db.session.commit()
        flash("已新增底部連結。", "success")
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{field}: {error}", "danger")
    
    return redirect(url_for("admin.site_settings"))


@admin_bp.route("/footer/<int:link_id>/edit", methods=["POST"])
@admin_required
def edit_footer(link_id: int):
    """Edit footer link via AJAX."""
    link = FooterSocialLink.query.get_or_404(link_id)
    
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "message": "無效的資料"}), 400
    
    try:
        if 'label' in data:
            link.label = data['label'].strip()
        if 'url' in data:
            link.url = data['url'].strip()
        if 'icon' in data:
            link.icon = data['icon'].strip() if data['icon'] else None
        if 'position' in data:
            link.position = int(data['position'])
        
        db.session.commit()
        return jsonify({
            "success": True,
            "message": "已更新底部連結",
            "link": {
                "id": link.id,
                "label": link.label,
                "url": link.url,
                "icon": link.icon,
                "position": link.position
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": f"更新失敗: {str(e)}"}), 500


@admin_bp.post("/footer/<int:link_id>/delete")
@admin_required
def delete_footer(link_id: int):
    link = FooterSocialLink.query.get_or_404(link_id)
    db.session.delete(link)
    db.session.commit()
    flash("已刪除底部連結。", "info")
    return redirect(url_for("admin.manage_footer"))


@admin_bp.route("/branding", methods=["GET", "POST"])
@admin_required
def manage_branding():
    """舊的品牌設定頁面 - 重定向到整合頁面"""
    return redirect(url_for("admin.site_settings"))


@admin_bp.route("/site-settings", methods=["GET", "POST"])
@admin_required
def site_settings():
    """整合的網站設定頁面"""
    branding_form = SiteBrandingForm(
        site_title=SiteSetting.get(SiteSettingKey.SITE_TITLE, ""),
        site_subtitle=SiteSetting.get(SiteSettingKey.SITE_SUBTITLE, ""),
        site_title_suffix=SiteSetting.get(SiteSettingKey.SITE_TITLE_SUFFIX, ""),
        footer_title=SiteSetting.get(SiteSettingKey.FOOTER_TITLE, ""),
        footer_description=SiteSetting.get(SiteSettingKey.FOOTER_DESCRIPTION, ""),
        header_logo_url=SiteSetting.get(SiteSettingKey.HEADER_LOGO_URL, ""),
        footer_logo_url=SiteSetting.get(SiteSettingKey.FOOTER_LOGO_URL, ""),
        footer_copy=SiteSetting.get(SiteSettingKey.FOOTER_COPY, ""),
    )
    
    nav_form = NavigationLinkForm()
    footer_form = FooterLinkForm()
    
    # 獲取所有連結
    nav_links = NavigationLink.query.order_by(NavigationLink.position.asc()).all()
    footer_links = FooterSocialLink.query.order_by(FooterSocialLink.position.asc()).all()
    
    # 獲取當前的 logo
    header_logo = SiteSetting.get(SiteSettingKey.HEADER_LOGO_FILE) or SiteSetting.get(SiteSettingKey.HEADER_LOGO_URL, "")
    footer_logo = SiteSetting.get(SiteSettingKey.FOOTER_LOGO_FILE) or SiteSetting.get(SiteSettingKey.FOOTER_LOGO_URL, "")
    
    return render_template(
        "admin/site_settings.html",
        branding_form=branding_form,
        nav_form=nav_form,
        footer_form=footer_form,
        nav_links=nav_links,
        footer_links=footer_links,
        current_header_logo=header_logo,
        current_footer_logo=footer_logo
    )


@admin_bp.route("/announcements")
@admin_required
def manage_announcements():
    """公告橫幅管理頁面"""
    form = AnnouncementBannerForm()
    announcements = AnnouncementBanner.query.order_by(AnnouncementBanner.position.asc()).all()
    
    return render_template(
        "admin/announcements.html",
        form=form,
        announcements=announcements
    )


@admin_bp.post("/site-settings/update")
@admin_required
def update_site_settings():
    """更新品牌設定"""
    form = SiteBrandingForm()
    
    if form.validate_on_submit():
        # 更新網站標題
        SiteSetting.set(SiteSettingKey.SITE_TITLE, form.site_title.data or "")
        SiteSetting.set(SiteSettingKey.SITE_SUBTITLE, form.site_subtitle.data or "")
        SiteSetting.set(SiteSettingKey.SITE_TITLE_SUFFIX, form.site_title_suffix.data or "")
        SiteSetting.set(SiteSettingKey.FOOTER_TITLE, form.footer_title.data or "")
        SiteSetting.set(SiteSettingKey.FOOTER_DESCRIPTION, form.footer_description.data or "")
        
        # 處理頁首 Logo
        header_logo_file = request.files.get('header_logo_file')
        if header_logo_file and header_logo_file.filename:
            old_header_file = SiteSetting.get(SiteSettingKey.HEADER_LOGO_FILE)
            if old_header_file:
                delete_uploaded_file(old_header_file)
            
            uploaded_path = save_uploaded_file(header_logo_file, "header_logo")
            if uploaded_path:
                SiteSetting.set(SiteSettingKey.HEADER_LOGO_FILE, uploaded_path)
                SiteSetting.set(SiteSettingKey.HEADER_LOGO_URL, "")
                flash("頁首 Logo 圖片已上傳。", "success")
            else:
                flash("頁首 Logo 上傳失敗，請檢查檔案格式。", "danger")
        elif form.header_logo_url.data:
            old_header_file = SiteSetting.get(SiteSettingKey.HEADER_LOGO_FILE)
            if old_header_file:
                delete_uploaded_file(old_header_file)
            
            SiteSetting.set(SiteSettingKey.HEADER_LOGO_URL, form.header_logo_url.data)
            SiteSetting.set(SiteSettingKey.HEADER_LOGO_FILE, "")
        
        # 處理頁尾 Logo
        footer_logo_file = request.files.get('footer_logo_file')
        if footer_logo_file and footer_logo_file.filename:
            old_footer_file = SiteSetting.get(SiteSettingKey.FOOTER_LOGO_FILE)
            if old_footer_file:
                delete_uploaded_file(old_footer_file)
            
            uploaded_path = save_uploaded_file(footer_logo_file, "footer_logo")
            if uploaded_path:
                SiteSetting.set(SiteSettingKey.FOOTER_LOGO_FILE, uploaded_path)
                SiteSetting.set(SiteSettingKey.FOOTER_LOGO_URL, "")
                flash("頁尾 Logo 圖片已上傳。", "success")
            else:
                flash("頁尾 Logo 上傳失敗，請檢查檔案格式。", "danger")
        elif form.footer_logo_url.data:
            old_footer_file = SiteSetting.get(SiteSettingKey.FOOTER_LOGO_FILE)
            if old_footer_file:
                delete_uploaded_file(old_footer_file)
            
            SiteSetting.set(SiteSettingKey.FOOTER_LOGO_URL, form.footer_logo_url.data)
            SiteSetting.set(SiteSettingKey.FOOTER_LOGO_FILE, "")
        
        # 更新版權文字
        SiteSetting.set(SiteSettingKey.FOOTER_COPY, form.footer_copy.data or "")
        
        flash("已更新網站品牌設定。", "success")
    
    return redirect(url_for("admin.site_settings"))


@admin_bp.post("/branding/delete-logo")
@admin_required
def delete_logo():
    """Delete an uploaded logo file."""
    data = request.get_json()
    logo_type = data.get("type")  # "header" or "footer"
    
    if logo_type not in ["header", "footer"]:
        return jsonify({"success": False, "message": "無效的 logo 類型"}), 400
    
    try:
        if logo_type == "header":
            old_file = SiteSetting.get(SiteSettingKey.HEADER_LOGO_FILE)
            if old_file:
                delete_uploaded_file(old_file)
                SiteSetting.set(SiteSettingKey.HEADER_LOGO_FILE, "")
        else:
            old_file = SiteSetting.get(SiteSettingKey.FOOTER_LOGO_FILE)
            if old_file:
                delete_uploaded_file(old_file)
                SiteSetting.set(SiteSettingKey.FOOTER_LOGO_FILE, "")
        
        return jsonify({"success": True, "message": "Logo 已刪除"})
    except Exception as e:
        return jsonify({"success": False, "message": f"刪除失敗: {str(e)}"}), 500


@admin_bp.route("/keys", methods=["GET", "POST"])
@admin_required
def manage_keys():
    form = RegistrationKeyManagerForm()

    if request.method == "GET":
        form.user_key.data = SiteSetting.get(SiteSettingKey.REGISTRATION_USER_KEY, "")
        form.admin_key.data = SiteSetting.get(SiteSettingKey.REGISTRATION_ADMIN_KEY, "")

    if form.validate_on_submit():
        SiteSetting.set(SiteSettingKey.REGISTRATION_USER_KEY, form.user_key.data or "")
        SiteSetting.set(SiteSettingKey.REGISTRATION_ADMIN_KEY, form.admin_key.data or "")
        flash("已更新註冊金鑰。", "success")
        return redirect(url_for("admin.manage_keys"))

    return render_template("admin/keys.html", form=form)


@admin_bp.post("/api/reorder-navigation")
@admin_required
def reorder_navigation():
    """API endpoint to reorder navigation links via drag and drop."""
    try:
        payload = request.get_json(silent=True) or {}
        order = payload.get("order", [])
        for index, link_id in enumerate(order):
            link = NavigationLink.query.get(link_id)
            if link:
                link.position = index
        db.session.commit()
        return jsonify({"success": True, "message": "順序已更新"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 400


@admin_bp.post("/api/reorder-footer")
@admin_required
def reorder_footer():
    """API endpoint to reorder footer links via drag and drop."""
    try:
        payload = request.get_json(silent=True) or {}
        order = payload.get("order", [])
        for index, link_id in enumerate(order):
            link = FooterSocialLink.query.get(link_id)
            if link:
                link.position = index
        db.session.commit()
        return jsonify({"success": True, "message": "順序已更新"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 400


@admin_bp.post("/api/reorder-categories")
@admin_required
def reorder_categories():
    """API endpoint to reorder keyword categories via drag and drop."""
    try:
        payload = request.get_json(silent=True) or {}
        order = payload.get("order", [])
        for index, category_id in enumerate(order):
            category = KeywordCategory.query.get(category_id)
            if category:
                category.position = index
        db.session.commit()
        return jsonify({"success": True, "message": "順序已更新"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 400


@admin_bp.post("/api/reorder-keywords")
def reorder_keywords():
    """API endpoint to reorder keywords via drag and drop."""
    try:
        payload = request.get_json(silent=True) or {}
        order = payload.get("order", [])
        for index, keyword_id in enumerate(order):
            keyword = LearningKeyword.query.get(keyword_id)
            if keyword:
                # 所有成員都可以調整所有關鍵字順序
                keyword.position = index
        db.session.commit()
        return jsonify({"success": True, "message": "順序已更新"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 400


@admin_bp.post("/api/move-keyword/<int:keyword_id>")
def move_keyword(keyword_id: int):
    """API endpoint to move a keyword to a different category."""
    try:
        keyword = LearningKeyword.query.get_or_404(keyword_id)
        
        # 所有成員都可以移動所有關鍵字
        
        payload = request.get_json(silent=True) or {}
        new_category_id = payload.get("category_id")
        if not new_category_id:
            return jsonify({"success": False, "message": "缺少目標分類"}), 400
        
        # 檢查目標分類是否存在
        category = KeywordCategory.query.get(new_category_id)
        if not category:
            return jsonify({"success": False, "message": "目標分類不存在"}), 404
        
        # 更新分類
        keyword.category_id = new_category_id
        db.session.commit()
        
        return jsonify({
            "success": True, 
            "message": "關鍵字已移動",
            "category_name": category.name
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 400


def _assign_category_choices(form: KeywordForm) -> None:
    categories = KeywordCategory.query.order_by(KeywordCategory.name.asc()).all()
    form.category_id.choices = [(category.id, category.name) for category in categories]


def _populate_video_entries(form: KeywordForm, keyword: LearningKeyword) -> None:
    while form.videos.entries:
        form.videos.pop_entry()
    for video in keyword.videos:
        entry = form.videos.append_entry({"title": video.title, "url": video.url})
        entry.form.title.data = video.title
        entry.form.url.data = video.url
    if not keyword.videos:
        form.videos.append_entry()


def _apply_video_updates(keyword: LearningKeyword, form: KeywordForm) -> None:
    from ..utils.youtube import extract_youtube_video_id
    
    keyword.videos.clear()
    for entry in form.videos.entries:
        data = entry.data
        url = (data or {}).get("url")
        if not url:
            continue
        
        # 雙重驗證：確保 URL 是有效的 YouTube 影片連結
        if not extract_youtube_video_id(url):
            continue  # 跳過無效的 YouTube URL
        
        video = YouTubeVideo(
            title=(data or {}).get("title"),
            url=url,
        )
        keyword.videos.append(video)


def _populate_alias_entries(form: KeywordForm, keyword: LearningKeyword) -> None:
    while form.aliases.entries:
        form.aliases.pop_entry()
    for alias in keyword.aliases:
        entry = form.aliases.append_entry({"alias_id": alias.id, "title": alias.title})
        entry.form.alias_id.data = str(alias.id)
        entry.form.title.data = alias.title


def _apply_alias_updates(keyword: LearningKeyword, form: KeywordForm) -> None:
    existing_aliases = {alias.id: alias for alias in keyword.aliases}
    updated_aliases: list[KeywordAlias] = []
    used_slugs: set[str] = {keyword.slug}

    for entry in form.aliases.entries:
        data = entry.data or {}
        title = (data.get("title") or "").strip()
        if not title:
            continue

        alias_id_raw = data.get("alias_id")
        alias_id = None
        if alias_id_raw:
            try:
                alias_id = int(alias_id_raw)
            except (TypeError, ValueError):
                alias_id = None

        alias_obj = existing_aliases.pop(alias_id, None) if alias_id else None
        if alias_obj is None:
            alias_obj = KeywordAlias()

        alias_obj.title = title
        alias_obj.slug = _generate_unique_alias_slug(title, alias_obj.id, used_slugs)
        used_slugs.add(alias_obj.slug)
        updated_aliases.append(alias_obj)

    keyword.aliases.clear()
    for alias in updated_aliases:
        keyword.aliases.append(alias)

    for stale_alias in existing_aliases.values():
        db.session.delete(stale_alias)


def _generate_unique_alias_slug(title: str, alias_id: int | None, used_slugs: set[str]) -> str:
    base_slug = slugify(title) or "alias"
    candidate = base_slug
    counter = 2

    while True:
        if candidate not in used_slugs:
            alias_conflict_query = KeywordAlias.query.filter(KeywordAlias.slug == candidate)
            if alias_id:
                alias_conflict_query = alias_conflict_query.filter(KeywordAlias.id != alias_id)
            alias_conflict = alias_conflict_query.first()
            keyword_conflict = LearningKeyword.query.filter_by(slug=candidate).first()
            if not alias_conflict and not keyword_conflict:
                return candidate
        candidate = f"{base_slug}-{counter}"
        counter += 1


@admin_bp.get("/edit-logs")
@admin_required
def view_edit_logs():
    """查看編輯日誌 (管理員專用)"""
    from ..models import EditLog
    from datetime import datetime
    from sqlalchemy import or_
    
    # 獲取篩選參數
    page = request.args.get('page', 1, type=int)
    per_page = 50
    action_filter = request.args.get('action', '')
    target_filter = request.args.get('target', '')
    user_filter = request.args.get('user', '', type=int)
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    search_query = request.args.get('search', '').strip()
    
    # 建立查詢
    query = EditLog.query
    
    if action_filter:
        query = query.filter_by(action=action_filter)
    if target_filter:
        query = query.filter_by(target_type=target_filter)
    if user_filter:
        query = query.filter_by(user_id=user_filter)
    
    # 日期範圍篩選
    if start_date:
        try:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            query = query.filter(EditLog.created_at >= start_dt)
        except ValueError:
            pass
    
    if end_date:
        try:
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
            # 包含結束日期的整天
            from datetime import timedelta
            end_dt = end_dt + timedelta(days=1)
            query = query.filter(EditLog.created_at < end_dt)
        except ValueError:
            pass
    
    # 搜索功能 (搜索描述和目標名稱)
    if search_query:
        search_pattern = f'%{search_query}%'
        query = query.filter(
            or_(
                EditLog.description.ilike(search_pattern),
                EditLog.target_name.ilike(search_pattern)
            )
        )
    
    # 按時間倒序排列
    logs = query.order_by(EditLog.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # 獲取所有成員列表用於篩選
    users = User.query.order_by(User.username.asc()).all()
    
    # 計算統計數據 (基於當前篩選)
    total_query = EditLog.query
    if action_filter:
        total_query = total_query.filter_by(action=action_filter)
    if target_filter:
        total_query = total_query.filter_by(target_type=target_filter)
    if user_filter:
        total_query = total_query.filter_by(user_id=user_filter)
    if start_date:
        try:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            total_query = total_query.filter(EditLog.created_at >= start_dt)
        except ValueError:
            pass
    if end_date:
        try:
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
            from datetime import timedelta
            end_dt = end_dt + timedelta(days=1)
            total_query = total_query.filter(EditLog.created_at < end_dt)
        except ValueError:
            pass
    if search_query:
        search_pattern = f'%{search_query}%'
        total_query = total_query.filter(
            or_(
                EditLog.description.ilike(search_pattern),
                EditLog.target_name.ilike(search_pattern)
            )
        )
    
    stats = {
        'keyword_count': total_query.filter_by(target_type='keyword').count(),
        'category_count': total_query.filter_by(target_type='category').count(),
        'user_count': total_query.filter_by(target_type='user').count(),
    }
    
    return render_template(
        'admin/edit_logs.html',
        logs=logs,
        users=users,
        action_filter=action_filter,
        target_filter=target_filter,
        user_filter=user_filter,
        start_date=start_date,
        end_date=end_date,
        search_query=search_query,
        stats=stats
    )


@admin_bp.get("/sitemap")
@admin_required
def manage_sitemap():
    """Display sitemap management and generation interface."""

    # Get sitemap statistics from manager
    stats = sitemap_manager.get_stats()
    sitemap_url = url_for('main.sitemap', _external=True)
    
    return render_template(
        'admin/sitemap.html',
        keywords_count=stats['keywords_count'],
        aliases_count=stats['aliases_count'],
        categories_count=stats['categories_count'],
        last_modified=stats.get('last_modified'),
        last_generated=stats.get('last_generated'),
        cache_exists=stats['cache_exists'],
        cache_age=stats.get('cache_age'),
        total_urls=stats['total_urls'],
        sitemap_url=sitemap_url,
    )


@admin_bp.post("/sitemap/generate")
@admin_required
def generate_sitemap():
    """Trigger sitemap regeneration."""

    # Force regenerate sitemap
    sitemap_manager.generate_sitemap(force=True)
    
    flash('Sitemap 已成功重新生成!', 'success')
    return redirect(url_for('admin.manage_sitemap'))


@admin_bp.post("/sitemap/clear-cache")
@admin_required
def clear_sitemap_cache():
    """Clear sitemap cache."""

    sitemap_manager.invalidate_cache()
    
    flash('Sitemap 緩存已清除!', 'info')
    return redirect(url_for('admin.manage_sitemap'))


@admin_bp.get("/keyword-linking")
@admin_required
def manage_keyword_linking():
    """Display keyword auto-linking feature information."""

    total_keywords = LearningKeyword.query.count()
    
    return render_template(
        'admin/keyword_linking.html',
        total_keywords=total_keywords,
    )


# ============================================================================
# Batch Operations API
# ============================================================================

@admin_bp.post("/api/toggle-keyword-visibility")
def toggle_keyword_visibility():
    """Toggle visibility of a single keyword."""
    from app.utils.edit_logger import log_keyword_visibility
    
    data = request.get_json()
    keyword_id = data.get('keyword_id')
    is_public = data.get('is_public', True)
    
    if not keyword_id:
        return jsonify({'success': False, 'message': '未指定關鍵字'}), 400
    
    try:
        keyword = LearningKeyword.query.get(keyword_id)
        if not keyword:
            return jsonify({'success': False, 'message': '關鍵字不存在'}), 404
        
        # 所有成員都可以修改關鍵字的可見性
        keyword.is_public = is_public
        db.session.commit()
        
        # 記錄編輯日誌
        log_keyword_visibility(keyword.id, keyword.title, is_public)
        
        status_text = '公開' if is_public else '隱藏'
        return jsonify({
            'success': True, 
            'message': f'已設為{status_text}',
            'is_public': is_public
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'操作失敗: {str(e)}'}), 500


@admin_bp.post("/api/batch-toggle-visibility")
def batch_toggle_visibility():
    """Batch toggle visibility of keywords."""
    data = request.get_json()
    keyword_ids = data.get('keyword_ids', [])
    is_public = data.get('is_public', True)
    
    if not keyword_ids:
        return jsonify({'success': False, 'message': '未選擇任何關鍵字'}), 400
    
    try:
        # 所有成員都可以批次修改所有關鍵字的可見性
        keywords = LearningKeyword.query.filter(
            LearningKeyword.id.in_(keyword_ids)
        ).all()
        
        if not keywords:
            return jsonify({'success': False, 'message': '未找到可操作的關鍵字'}), 404
        
        for keyword in keywords:
            keyword.is_public = is_public
        
        db.session.commit()
        
        status_text = '公開' if is_public else '隱藏'
        return jsonify({
            'success': True, 
            'message': f'已將 {len(keywords)} 筆關鍵字設為{status_text}',
            'count': len(keywords)
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'操作失敗: {str(e)}'}), 500


@admin_bp.post("/api/batch-delete")
@admin_required
def batch_delete_keywords():
    """Batch delete keywords (admin only)."""
    data = request.get_json()
    keyword_ids = data.get('keyword_ids', [])
    
    if not keyword_ids:
        return jsonify({'success': False, 'message': '未選擇任何關鍵字'}), 400
    
    try:
        keywords = LearningKeyword.query.filter(
            LearningKeyword.id.in_(keyword_ids)
        ).all()
        
        if not keywords:
            return jsonify({'success': False, 'message': '未找到可刪除的關鍵字'}), 404
        
        count = len(keywords)
        for keyword in keywords:
            db.session.delete(keyword)
        
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': f'已刪除 {count} 筆關鍵字',
            'count': count
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'刪除失敗: {str(e)}'}), 500


@admin_bp.post("/api/batch-move")
def batch_move_keywords():
    """Batch move keywords to another category."""
    data = request.get_json()
    keyword_ids = data.get('keyword_ids', [])
    target_category_id = data.get('category_id')
    
    if not keyword_ids:
        return jsonify({'success': False, 'message': '未選擇任何關鍵字'}), 400
    
    if not target_category_id:
        return jsonify({'success': False, 'message': '未指定目標分類'}), 400
    
    try:
        # Check if target category exists
        target_category = KeywordCategory.query.get(target_category_id)
        if not target_category:
            return jsonify({'success': False, 'message': '目標分類不存在'}), 404
        
        # 所有成員都可以移動所有關鍵字
        keywords = LearningKeyword.query.filter(
            LearningKeyword.id.in_(keyword_ids)
        ).all()
        
        if not keywords:
            return jsonify({'success': False, 'message': '未找到可移動的關鍵字'}), 404
        
        for keyword in keywords:
            keyword.category_id = target_category_id
        
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': f'已將 {len(keywords)} 筆關鍵字移動到「{target_category.name}」',
            'count': len(keywords),
            'category_name': target_category.name
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'移動失敗: {str(e)}'}), 500


# ============================================================================
# 成員管理路由
# ============================================================================

@admin_bp.route("/users")
@admin_required
def manage_users():
    """管理系統成員 - 只有管理員可訪問"""
    
    # 獲取所有成員,按註冊時間排序
    users = User.query.order_by(User.created_at.asc()).all()
    
    # 找出當前成員在所有管理員中的註冊排名
    all_admins = User.query.filter_by(role=Role.ADMIN).order_by(User.created_at.asc()).all()
    current_admin_rank = None
    for idx, admin in enumerate(all_admins):
        if admin.id == current_user.id:
            current_admin_rank = idx
            break
    
    # 為每個成員標記是否可以管理
    users_data = []
    for user in users:
        can_manage = True
        reason = None
        
        if user.id == current_user.id:
            can_manage = False
            reason = "無法管理自己"
        elif user.is_admin() and current_admin_rank is not None:
            # 找出目標管理員的排名
            target_admin_rank = None
            for idx, admin in enumerate(all_admins):
                if admin.id == user.id:
                    target_admin_rank = idx
                    break
            
            # 只能管理註冊時間比自己晚的管理員
            if target_admin_rank is not None and target_admin_rank <= current_admin_rank:
                can_manage = False
                reason = "此管理員註冊時間早於或等於您"
        
        # 計算成員的關鍵字數量
        keyword_count = LearningKeyword.query.filter_by(author_id=user.id).count()
        
        users_data.append({
            'user': user,
            'can_manage': can_manage,
            'reason': reason,
            'keyword_count': keyword_count
        })
    
    return render_template(
        "admin/users.html",
        users_data=users_data,
        Role=Role
    )


@admin_bp.route("/users/<int:user_id>/role", methods=["POST"])
@admin_required
def update_user_role(user_id: int):
    """更新成員角色 - AJAX"""
    target_user = User.query.get_or_404(user_id)
    
    # 嘗試解析 JSON 資料
    try:
        data = request.get_json(force=True)
    except Exception as e:
        return jsonify({"success": False, "message": f"JSON 解析失敗: {str(e)}"}), 400
    
    if not data or 'role' not in data:
        return jsonify({"success": False, "message": "無效的請求資料"}), 400
    
    new_role_str = data['role']
    
    # 驗證角色
    try:
        if new_role_str == 'admin':
            new_role = Role.ADMIN
        elif new_role_str == 'user':
            new_role = Role.USER
        else:
            return jsonify({"success": False, "message": "無效的角色"}), 400
    except:
        return jsonify({"success": False, "message": "角色解析失敗"}), 400
    
    # 檢查是否嘗試修改自己
    if target_user.id == current_user.id:
        return jsonify({"success": False, "message": "無法修改自己的角色"}), 403
    
    # 檢查權限 - 只能修改註冊時間比自己晚的管理員
    if target_user.is_admin():
        all_admins = User.query.filter_by(role=Role.ADMIN).order_by(User.created_at.asc()).all()
        current_admin_rank = None
        target_admin_rank = None
        
        for idx, admin in enumerate(all_admins):
            if admin.id == current_user.id:
                current_admin_rank = idx
            if admin.id == target_user.id:
                target_admin_rank = idx
        
        if target_admin_rank is not None and current_admin_rank is not None:
            if target_admin_rank <= current_admin_rank:
                return jsonify({
                    "success": False, 
                    "message": "無法修改註冊時間早於或等於您的管理員"
                }), 403
    
    try:
        old_role = target_user.role
        target_user.role = new_role
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": f"已將 {target_user.username} 的角色從 {old_role.value} 更改為 {new_role.value}",
            "user": {
                "id": target_user.id,
                "username": target_user.username,
                "role": new_role.value
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": f"更新失敗: {str(e)}"}), 500


@admin_bp.route("/users/<int:user_id>/toggle-active", methods=["POST"])
@admin_required
def toggle_user_active(user_id: int):
    """啟用/停用成員帳號 - AJAX"""
    target_user = User.query.get_or_404(user_id)
    
    # 檢查是否嘗試修改自己
    if target_user.id == current_user.id:
        return jsonify({"success": False, "message": "無法停用自己的帳號"}), 403
    
    # 檢查權限 - 只能修改註冊時間比自己晚的管理員
    if target_user.is_admin():
        all_admins = User.query.filter_by(role=Role.ADMIN).order_by(User.created_at.asc()).all()
        current_admin_rank = None
        target_admin_rank = None
        
        for idx, admin in enumerate(all_admins):
            if admin.id == current_user.id:
                current_admin_rank = idx
            if admin.id == target_user.id:
                target_admin_rank = idx
        
        if target_admin_rank is not None and current_admin_rank is not None:
            if target_admin_rank <= current_admin_rank:
                return jsonify({
                    "success": False, 
                    "message": "無法停用註冊時間早於或等於您的管理員"
                }), 403
    
    try:
        target_user.is_active = not target_user.is_active
        db.session.commit()
        
        status = "啟用" if target_user.is_active else "停用"
        return jsonify({
            "success": True,
            "message": f"已{status}用戶 {target_user.username}",
            "user": {
                "id": target_user.id,
                "username": target_user.username,
                "is_active": target_user.is_active
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": f"操作失敗: {str(e)}"}), 500


@admin_bp.route("/users/<int:user_id>/delete", methods=["POST"])
@admin_required
def delete_user(user_id: int):
    """刪除成員 - AJAX"""
    target_user = User.query.get_or_404(user_id)
    
    # 檢查是否嘗試刪除自己
    if target_user.id == current_user.id:
        return jsonify({"success": False, "message": "無法刪除自己的帳號"}), 403
    
    # 檢查權限 - 只能刪除註冊時間比自己晚的管理員
    if target_user.is_admin():
        all_admins = User.query.filter_by(role=Role.ADMIN).order_by(User.created_at.asc()).all()
        current_admin_rank = None
        target_admin_rank = None
        
        for idx, admin in enumerate(all_admins):
            if admin.id == current_user.id:
                current_admin_rank = idx
            if admin.id == target_user.id:
                target_admin_rank = idx
        
        if target_admin_rank is not None and current_admin_rank is not None:
            if target_admin_rank <= current_admin_rank:
                return jsonify({
                    "success": False, 
                    "message": "無法刪除註冊時間早於或等於您的管理員"
                }), 403
    
    try:
        username = target_user.username
        
        # 刪除成員的所有關鍵字
        LearningKeyword.query.filter_by(author_id=target_user.id).delete()
        
        # 刪除成員
        db.session.delete(target_user)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": f"已刪除成員 {username} 及其所有關鍵字"
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": f"刪除失敗: {str(e)}"}), 500


# ==================== 公告橫幅管理 ====================

@admin_bp.post("/announcements/add")
@admin_required
def add_announcement():
    """新增公告橫幅"""
    form = AnnouncementBannerForm()
    
    if form.validate_on_submit():
        announcement = AnnouncementBanner(
            text=form.text.data,
            url=form.url.data or None,
            icon=form.icon.data or "bi-info-circle-fill",
            is_active=form.is_active.data,
            position=form.position.data or 0
        )
        db.session.add(announcement)
        db.session.commit()
        flash("公告橫幅已新增。", "success")
    else:
        flash("新增失敗，請檢查輸入。", "danger")
    
    return redirect(url_for("admin.manage_announcements"))


@admin_bp.post("/announcements/<int:announcement_id>/edit")
@admin_required
def edit_announcement(announcement_id: int):
    """編輯公告橫幅"""
    announcement = AnnouncementBanner.query.get_or_404(announcement_id)
    data = request.get_json()
    
    announcement.text = data.get("text", announcement.text)
    announcement.url = data.get("url") or None
    announcement.icon = data.get("icon", announcement.icon)
    announcement.is_active = data.get("is_active", announcement.is_active)
    announcement.position = data.get("position", announcement.position)
    
    db.session.commit()
    
    return jsonify({"success": True, "message": "公告橫幅已更新。"})


@admin_bp.post("/announcements/<int:announcement_id>/delete")
@admin_required
def delete_announcement(announcement_id: int):
    """刪除公告橫幅"""
    announcement = AnnouncementBanner.query.get_or_404(announcement_id)
    db.session.delete(announcement)
    db.session.commit()
    flash("公告橫幅已刪除。", "success")
    return redirect(url_for("admin.site_settings"))


@admin_bp.post("/announcements/<int:announcement_id>/toggle")
@admin_required
def toggle_announcement(announcement_id: int):
    """切換公告橫幅啟用狀態"""
    announcement = AnnouncementBanner.query.get_or_404(announcement_id)
    announcement.is_active = not announcement.is_active
    db.session.commit()
    
    status = "啟用" if announcement.is_active else "停用"
    return jsonify({"success": True, "message": f"公告橫幅已{status}。", "is_active": announcement.is_active})


@admin_bp.post("/api/reorder-announcements")
@admin_required
def reorder_announcements():
    """重新排序公告橫幅"""
    data = request.get_json()
    order = data.get("order", []) if data else []
    
    for idx, announcement_id in enumerate(order):
        announcement = AnnouncementBanner.query.get(int(announcement_id))
        if announcement:
            announcement.position = idx
    
    db.session.commit()
    return jsonify({"success": True})


# ============================================================================
# 關鍵字目標清單管理
# ============================================================================

@admin_bp.route("/goal-lists")
def manage_goal_lists():
    """管理關鍵字目標清單"""
    goal_lists = KeywordGoalList.query.order_by(KeywordGoalList.created_at.desc()).all()
    return render_template("admin/goal_lists.html", goal_lists=goal_lists)


@admin_bp.route("/goal-lists/new", methods=["GET", "POST"])
def create_goal_list():
    """創建新的關鍵字目標清單"""
    from ..forms import KeywordGoalListForm
    
    form = KeywordGoalListForm()
    
    if form.validate_on_submit():
        # 創建目標清單
        goal_list = KeywordGoalList(
            name=form.name.data,
            description=form.description.data,
            category_name=form.category_name.data,
            created_by=current_user.id
        )
        db.session.add(goal_list)
        db.session.flush()
        
        # 解析關鍵字列表
        keywords_text = form.keywords_text.data or ""
        keywords = [k.strip() for k in keywords_text.split('\n') if k.strip()]
        
        # 創建目標項目
        for idx, keyword_title in enumerate(keywords):
            item = KeywordGoalItem(
                goal_list_id=goal_list.id,
                title=keyword_title,
                position=idx
            )
            db.session.add(item)
        
        db.session.commit()
        
        flash(f"已創建目標清單「{goal_list.name}」,包含 {len(keywords)} 個關鍵字。", "success")
        return redirect(url_for("admin.view_goal_list", list_id=goal_list.id))
    
    return render_template("admin/goal_list_form.html", form=form)


@admin_bp.route("/goal-lists/<int:list_id>")
def view_goal_list(list_id: int):
    """查看目標清單詳情"""
    goal_list = KeywordGoalList.query.get_or_404(list_id)
    return render_template("admin/goal_list_detail.html", goal_list=goal_list)


@admin_bp.post("/goal-lists/<int:list_id>/toggle")
def toggle_goal_list(list_id: int):
    """啟用/停用目標清單"""
    goal_list = KeywordGoalList.query.get_or_404(list_id)
    
    # 只有創建者或管理員可以操作
    if goal_list.created_by != current_user.id and not current_user.is_admin():
        return jsonify({"success": False, "message": "無權限操作"}), 403
    
    goal_list.is_active = not goal_list.is_active
    db.session.commit()
    
    status = "啟用" if goal_list.is_active else "停用"
    return jsonify({"success": True, "message": f"清單已{status}", "is_active": goal_list.is_active})


@admin_bp.post("/goal-lists/<int:list_id>/update")
def update_goal_list(list_id: int):
    """更新目標清單資訊"""
    goal_list = KeywordGoalList.query.get_or_404(list_id)
    
    # 只有創建者或管理員可以編輯
    if goal_list.created_by != current_user.id and not current_user.is_admin():
        return jsonify({"success": False, "message": "無權限編輯"}), 403
    
    data = request.get_json()
    goal_list.name = data.get('name', goal_list.name)
    goal_list.description = data.get('description', goal_list.description)
    goal_list.category_name = data.get('category_name', goal_list.category_name)
    
    db.session.commit()
    
    return jsonify({"success": True, "message": "清單資訊已更新"})


@admin_bp.post("/goal-lists/<int:list_id>/add-items")
def add_goal_list_items(list_id: int):
    """新增目標項目到清單"""
    goal_list = KeywordGoalList.query.get_or_404(list_id)
    
    # 只有創建者或管理員可以新增
    if goal_list.created_by != current_user.id and not current_user.is_admin():
        return jsonify({"success": False, "message": "無權限新增"}), 403
    
    data = request.get_json()
    items = data.get('items', [])
    
    if not items:
        return jsonify({"success": False, "message": "請提供要新增的項目"}), 400
    
    # 獲取當前最大位置
    max_position = db.session.query(db.func.max(KeywordGoalItem.position))\
        .filter(KeywordGoalItem.goal_list_id == list_id).scalar() or -1
    
    # 批量新增項目
    for idx, item_title in enumerate(items):
        item = KeywordGoalItem(
            goal_list_id=list_id,
            title=item_title.strip(),
            position=max_position + idx + 1
        )
        db.session.add(item)
    
    db.session.commit()
    
    return jsonify({"success": True, "message": f"已新增 {len(items)} 個項目", "count": len(items)})


@admin_bp.post("/goal-lists/<int:list_id>/delete")
def delete_goal_list(list_id: int):
    """刪除目標清單"""
    goal_list = KeywordGoalList.query.get_or_404(list_id)
    
    # 只有創建者或管理員可以刪除
    if goal_list.created_by != current_user.id and not current_user.is_admin():
        return jsonify({"success": False, "message": "無權限刪除"}), 403
    
    list_name = goal_list.name
    db.session.delete(goal_list)
    db.session.commit()
    
    return jsonify({"success": True, "message": f"已刪除目標清單「{list_name}」"})


@admin_bp.get("/goal-items/<int:item_id>/prepare-create")
def prepare_create_from_goal(item_id: int):
    """準備從目標項目創建關鍵字 - 跳轉到編輯器預填資料"""
    item = KeywordGoalItem.query.get_or_404(item_id)
    
    # 檢查是否已完成
    if item.is_completed:
        flash("此項目已完成", "warning")
        return redirect(url_for("admin.view_goal_list", list_id=item.goal_list_id))
    
    # 跳轉到新建關鍵字頁面,帶上目標項目資訊
    return redirect(url_for(
        "admin.create_keyword_studio",
        from_goal_item=item_id,
        title=item.title,
        category=item.goal_list.category_name
    ))


@admin_bp.post("/goal-items/<int:item_id>/mark-complete")
def mark_goal_item_complete(item_id: int):
    """手動標記目標項目為完成"""
    item = KeywordGoalItem.query.get_or_404(item_id)
    
    from datetime import datetime
    item.is_completed = True
    item.completed_by = current_user.id
    item.completed_at = datetime.utcnow()
    
    db.session.commit()
    
    return jsonify({"success": True, "message": "已標記為完成"})


@admin_bp.post("/goal-items/<int:item_id>/mark-incomplete")
def mark_goal_item_incomplete(item_id: int):
    """取消完成標記"""
    item = KeywordGoalItem.query.get_or_404(item_id)
    
    item.is_completed = False
    item.completed_by = None
    item.completed_at = None
    
    db.session.commit()
    
    return jsonify({"success": True, "message": "已取消完成標記"})


@admin_bp.post("/goal-items/<int:item_id>/delete")
def delete_goal_item(item_id: int):
    """刪除目標項目"""
    item = KeywordGoalItem.query.get_or_404(item_id)
    
    # 只有清單創建者或管理員可以刪除
    if item.goal_list.created_by != current_user.id and not current_user.is_admin():
        return jsonify({"success": False, "message": "無權限刪除"}), 403
    
    # 不允許刪除已完成的項目
    if item.is_completed:
        return jsonify({"success": False, "message": "無法刪除已完成的項目,請先取消完成標記"}), 400
    
    item_title = item.title
    db.session.delete(item)
    db.session.commit()
    
    return jsonify({"success": True, "message": f"已刪除項目「{item_title}」"})

