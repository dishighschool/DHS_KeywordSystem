"""備份服務 - 管理系統資料備份"""
from __future__ import annotations

import gzip
import json
import os
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from flask import current_app

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

from ..extensions import db
from ..models import (
    AnnouncementBanner,
    EditLog,
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
    SystemBackup,
    User,
    YouTubeVideo,
)


class BackupService:
    """系統備份服務"""

    # 備份目錄
    BACKUP_DIR = Path(__file__).parent.parent.parent / "backups"

    # 保留備份天數
    RETENTION_DAYS = 30

    # 備份檔案字首
    BACKUP_PREFIX = "system_backup"

    # Discord Webhook 上傳限制 (Discord API 上限為 25 MB)
    DISCORD_UPLOAD_LIMIT = 25 * 1024 * 1024

    def __init__(self, session=None):
        """初始化備份服務"""
        self.session = session or db.session
        self._ensure_backup_dir()

    @classmethod
    def _ensure_backup_dir(cls) -> Path:
        """確保備份目錄存在"""
        backup_dir = cls.BACKUP_DIR
        backup_dir.mkdir(parents=True, exist_ok=True)
        return backup_dir

    @classmethod
    def create_backup(
        cls,
        session=None,
        created_by=None,
        backup_type: str = "auto",
        description: str | None = None,
    ) -> Optional[SystemBackup]:
        """
        建立系統備份

        Args:
            session: 資料庫會話
            created_by: 建立者 ID
            backup_type: 備份類型 ('auto' 或 'manual')
            description: 備份說明

        Returns:
            SystemBackup 物件或 None (如果建立失敗)
        """
        if session is None:
            session = db.session

        try:
            service = cls(session)

            # 收集所有資料
            data = {
                "export_info": {
                    "version": "1.0",
                    "exported_at": datetime.utcnow().isoformat(),
                    "exported_by_id": created_by,
                },
                "users": [],
                "categories": [],
                "keywords": [],
                "aliases": [],
                "videos": [],
                "navigation_links": [],
                "footer_links": [],
                "announcements": [],
                "site_settings": [],
                "goal_lists": [],
                "goal_items": [],
            }

            # 匯出用戶 (不包含敏感資訊)
            for user in session.query(User).all():
                data["users"].append({
                    "id": user.id,
                    "discord_id": user.discord_id,
                    "username": user.username,
                    "avatar_hash": user.avatar_hash,
                    "role": user.role.value,
                    "is_active": user.is_active,
                    "created_at": user.created_at.isoformat(),
                })

            # 匯出分類
            for category in session.query(KeywordCategory).order_by(KeywordCategory.position).all():
                data["categories"].append({
                    "id": category.id,
                    "name": category.name,
                    "slug": category.slug,
                    "description": category.description,
                    "position": category.position,
                    "icon": category.icon,
                    "is_public": category.is_public,
                    "created_at": category.created_at.isoformat(),
                })

            # 匯出關鍵字
            for keyword in session.query(LearningKeyword).order_by(
                LearningKeyword.category_id, LearningKeyword.position
            ).all():
                data["keywords"].append({
                    "id": keyword.id,
                    "title": keyword.title,
                    "slug": keyword.slug,
                    "description_markdown": keyword.description_markdown,
                    "position": keyword.position,
                    "is_public": keyword.is_public,
                    "view_count": keyword.view_count,
                    "seo_content": keyword.seo_content,
                    "seo_auto_generate": keyword.seo_auto_generate,
                    "category_id": keyword.category_id,
                    "author_id": keyword.author_id,
                    "created_at": keyword.created_at.isoformat(),
                    "updated_at": keyword.updated_at.isoformat(),
                })

            # 匯出別名
            for alias in session.query(KeywordAlias).all():
                data["aliases"].append({
                    "id": alias.id,
                    "keyword_id": alias.keyword_id,
                    "title": alias.title,
                    "slug": alias.slug,
                    "created_at": alias.created_at.isoformat(),
                })

            # 匯出影片
            for video in session.query(YouTubeVideo).all():
                data["videos"].append({
                    "id": video.id,
                    "keyword_id": video.keyword_id,
                    "title": video.title,
                    "url": video.url,
                    "created_at": video.created_at.isoformat(),
                })

            # 匯出導航連結
            for nav in session.query(NavigationLink).order_by(NavigationLink.position).all():
                data["navigation_links"].append({
                    "id": nav.id,
                    "label": nav.label,
                    "url": nav.url,
                    "icon": nav.icon,
                    "position": nav.position,
                    "created_at": nav.created_at.isoformat(),
                })

            # 匯出底部連結
            for footer in session.query(FooterSocialLink).order_by(FooterSocialLink.position).all():
                data["footer_links"].append({
                    "id": footer.id,
                    "label": footer.label,
                    "url": footer.url,
                    "icon": footer.icon,
                    "position": footer.position,
                    "created_at": footer.created_at.isoformat(),
                })

            # 匯出公告橫幅
            for announcement in session.query(AnnouncementBanner).order_by(
                AnnouncementBanner.position
            ).all():
                data["announcements"].append({
                    "id": announcement.id,
                    "text": announcement.text,
                    "url": announcement.url,
                    "icon": announcement.icon,
                    "is_active": announcement.is_active,
                    "position": announcement.position,
                    "created_at": announcement.created_at.isoformat(),
                })

            # 匯出網站設定
            for setting in session.query(SiteSetting).all():
                data["site_settings"].append({
                    "key": setting.key,
                    "value": setting.value,
                    "updated_at": setting.updated_at.isoformat(),
                })

            # 匯出目標清單
            for goal_list in session.query(KeywordGoalList).all():
                data["goal_lists"].append({
                    "id": goal_list.id,
                    "name": goal_list.name,
                    "description": goal_list.description,
                    "category_name": goal_list.category_name,
                    "is_active": goal_list.is_active,
                    "created_by": goal_list.created_by,
                    "created_at": goal_list.created_at.isoformat(),
                })

            # 匯出目標項目
            for goal_item in session.query(KeywordGoalItem).all():
                data["goal_items"].append({
                    "id": goal_item.id,
                    "goal_list_id": goal_item.goal_list_id,
                    "title": goal_item.title,
                    "position": goal_item.position,
                    "is_completed": goal_item.is_completed,
                    "keyword_id": goal_item.keyword_id,
                    "completed_by": goal_item.completed_by,
                    "completed_at": goal_item.completed_at.isoformat()
                    if goal_item.completed_at
                    else None,
                    "created_at": goal_item.created_at.isoformat(),
                })

            # 生成檔案名稱和路徑
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")[:-3]  # 包含毫秒
            filename = f"{cls.BACKUP_PREFIX}_{timestamp}.json.gz"
            filepath = cls.BACKUP_DIR / filename

            # 寫入壓縮檔案
            json_data = json.dumps(data, ensure_ascii=False, indent=2)
            with gzip.open(filepath, "wt", encoding="utf-8") as f:
                f.write(json_data)

            # 取得檔案大小
            file_size = filepath.stat().st_size

            # 記錄到資料庫
            backup_record = SystemBackup(
                filename=filename,
                filepath=str(filepath),
                file_size=file_size,
                backup_type=backup_type,
                created_by=created_by,
                description=description,
                is_compressed=True,
            )
            session.add(backup_record)
            session.commit()

            current_app.logger.info(
                f"Backup created: {filename} ({service._format_size(file_size)})"
            )

            # 傳送備份通知到 Discord（如果有設定 webhook）
            cls._notify_discord_webhook(backup_record)

            return backup_record

        except Exception as e:
            current_app.logger.error(f"Backup creation failed: {e}")
            return None

    @classmethod
    def get_backup_list(
        cls,
        session=None,
        limit: int | None = None,
    ) -> list:
        """
        取得備份列表

        Args:
            session: 資料庫會話
            limit: 限制數量

        Returns:
            備份列表，按建立時間倒序
        """
        if session is None:
            session = db.session

        query = session.query(SystemBackup).order_by(SystemBackup.created_at.desc())

        if limit:
            query = query.limit(limit)

        return query.all()

    @classmethod
    def delete_backup(cls, backup_id: int, session=None) -> bool:
        """
        刪除備份

        Args:
            backup_id: 備份 ID
            session: 資料庫會話

        Returns:
            是否刪除成功
        """
        if session is None:
            session = db.session

        try:
            backup = session.query(SystemBackup).get(backup_id)
            if not backup:
                return False

            # 刪除檔案
            filepath = Path(backup.filepath)
            if filepath.exists():
                filepath.unlink()

            # 刪除記錄
            session.delete(backup)
            session.commit()

            current_app.logger.info(f"Backup deleted: {backup.filename}")
            return True

        except Exception as e:
            current_app.logger.error(f"Backup deletion failed: {e}")
            return False

    @classmethod
    def cleanup_old_backups(
        cls,
        retention_days: int | None = None,
        session=None,
    ) -> int:
        """
        清理舊備份（超過保留天數）

        Args:
            retention_days: 保留天數（預設為 RETENTION_DAYS）
            session: 資料庫會話

        Returns:
            刪除的備份數量
        """
        if retention_days is None:
            retention_days = cls.RETENTION_DAYS

        if session is None:
            session = db.session

        try:
            cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
            old_backups = session.query(SystemBackup).filter(
                SystemBackup.created_at < cutoff_date
            ).all()

            deleted_count = 0

            for backup in old_backups:
                try:
                    # 刪除檔案
                    filepath = Path(backup.filepath)
                    if filepath.exists():
                        filepath.unlink()

                    # 刪除記錄
                    session.delete(backup)
                    deleted_count += 1
                except Exception as e:
                    current_app.logger.error(f"Failed to delete backup {backup.filename}: {e}")

            session.commit()

            if deleted_count > 0:
                current_app.logger.info(f"Cleaned up {deleted_count} old backups")

            return deleted_count

        except Exception as e:
            current_app.logger.error(f"Backup cleanup failed: {e}")
            return 0

    @classmethod
    def get_backup_by_id(
        cls, backup_id: int, session=None
    ) -> Optional[SystemBackup]:
        """取得指定 ID 的備份"""
        if session is None:
            session = db.session

        return session.query(SystemBackup).get(backup_id)

    @classmethod
    def get_backup_stats(cls, session=None) -> dict:
        """
        取得備份統計資訊

        Returns:
            備份統計資訊字典
        """
        if session is None:
            session = db.session

        try:
            backups = session.query(SystemBackup).all()

            total_size = sum(b.file_size for b in backups)
            auto_backups = sum(1 for b in backups if b.backup_type == "auto")
            manual_backups = sum(1 for b in backups if b.backup_type == "manual")

            return {
                "total_backups": len(backups),
                "auto_backups": auto_backups,
                "manual_backups": manual_backups,
                "total_size": total_size,
                "total_size_formatted": cls._format_size(total_size),
                "oldest_backup": min((b.created_at for b in backups), default=None),
                "newest_backup": max((b.created_at for b in backups), default=None),
            }
        except Exception as e:
            current_app.logger.error(f"Failed to get backup stats: {e}")
            return {
                "total_backups": 0,
                "auto_backups": 0,
                "manual_backups": 0,
                "total_size": 0,
                "total_size_formatted": "0 B",
            }

    @staticmethod
    def _format_size(size: float) -> str:
        """格式化檔案大小"""
        size = float(size)
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024:
                return f"{size:.2f} {unit}"
            size /= 1024
        return f"{size:.2f} TB"

    @classmethod
    def _notify_discord_webhook(cls, backup: SystemBackup) -> None:
        """將備份資訊推送到 Discord Webhook（如果已設定）。"""
        try:
            webhook_url = SiteSetting.get(SiteSettingKey.BACKUP_DISCORD_WEBHOOK_URL)
        except Exception as exc:  # pragma: no cover - defensive guard
            current_app.logger.warning(f"Failed to load Discord webhook setting: {exc}")
            return

        if not webhook_url:
            return

        normalized_url = webhook_url.strip()
        if not normalized_url.startswith("https://discord.com/api/webhooks/") and not normalized_url.startswith(
            "https://discordapp.com/api/webhooks/"
        ):
            current_app.logger.warning("Discord webhook URL 格式不正確，已略過通知")
            return

        file_path = Path(backup.filepath)
        if not file_path.exists():
            current_app.logger.warning(
                "Backup file missing when attempting Discord notification: %s", backup.filename
            )
            return

        # 準備訊息內容
        initiator = backup.creator.username if backup.creator else "系統排程"
        backup_type_label = "自動備份" if backup.backup_type == "auto" else "手動備份"
        timestamp = backup.created_at.replace(microsecond=0).isoformat() + "Z"

        embed = {
            "title": backup.filename,
            "color": 0x5865F2,
            "fields": [
                {"name": "備份類型", "value": backup_type_label, "inline": True},
                {"name": "檔案大小", "value": backup.get_display_size(), "inline": True},
                {"name": "建立者", "value": initiator, "inline": True},
            ],
            "timestamp": timestamp,
        }

        if backup.description:
            embed["description"] = backup.description

        attach_file = backup.file_size <= cls.DISCORD_UPLOAD_LIMIT

        if not attach_file:
            embed["fields"].append(
                {
                    "name": "附件狀態",
                    "value": "檔案超過 25MB，請至系統後台下載備份。",
                    "inline": False,
                }
            )

        payload = {
            "content": f"🛡️ {backup_type_label}完成：{backup.filename}",
            "embeds": [embed],
        }

        try:
            import requests
        except ModuleNotFoundError:  # pragma: no cover - environment guard
            current_app.logger.error("requests 套件不存在，無法推送 Discord Webhook")
            return

        try:
            if attach_file:
                with file_path.open("rb") as fh:
                    response = requests.post(
                        normalized_url,
                        data={"payload_json": json.dumps(payload, ensure_ascii=False)},
                        files={"file": (backup.filename, fh, "application/gzip")},
                        timeout=30,
                    )
            else:
                response = requests.post(normalized_url, json=payload, timeout=15)

            if response.status_code not in (200, 204):
                current_app.logger.warning(
                    "Discord webhook 回應非預期狀態 %s: %s",
                    response.status_code,
                    response.text[:2000],
                )
        except Exception as exc:  # pragma: no cover - network call
            current_app.logger.error(f"Failed to send backup notification to Discord: {exc}")
