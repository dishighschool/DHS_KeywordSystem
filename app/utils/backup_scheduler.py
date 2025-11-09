"""排程工作管理 - 自動備份和清理舊備份"""
from __future__ import annotations

from logging import getLogger
from typing import TYPE_CHECKING

from apscheduler.schedulers.background import BackgroundScheduler
from flask import current_app

if TYPE_CHECKING:
    from flask import Flask

logger = getLogger(__name__)


class BackupScheduler:
    """備份排程管理器"""

    scheduler: BackgroundScheduler | None = None
    _initialized = False

    @classmethod
    def init_app(cls, app: Flask) -> None:
        """初始化排程器"""
        if cls._initialized:
            return

        cls.scheduler = BackgroundScheduler(daemon=True)

        # 新增每天午夜 1:00 的自動備份工作
        cls.scheduler.add_job(
            cls._create_daily_backup,
            "cron",
            hour=1,
            minute=0,
            id="backup_daily",
            name="Daily System Backup",
            replace_existing=True,
        )

        # 新增每天午夜 2:00 的清理工作
        cls.scheduler.add_job(
            cls._cleanup_old_backups,
            "cron",
            hour=2,
            minute=0,
            id="cleanup_old_backups",
            name="Cleanup Old Backups",
            replace_existing=True,
        )

        cls.scheduler.start()
        cls._initialized = True

        logger.info("Backup scheduler initialized")

    @staticmethod
    def _create_daily_backup() -> None:
        """執行每日備份"""
        try:
            from .backup_service import BackupService

            with current_app.app_context():
                backup = BackupService.create_backup(
                    backup_type="auto",
                    description="自動每日備份",
                )

                if backup:
                    logger.info(
                        f"Daily backup completed: {backup.filename} ({backup.get_display_size()})"
                    )
                else:
                    logger.error("Daily backup failed")

        except Exception as e:
            logger.error(f"Error during daily backup: {e}", exc_info=True)

    @staticmethod
    def _cleanup_old_backups() -> None:
        """清理舊備份"""
        try:
            from .backup_service import BackupService

            with current_app.app_context():
                count = BackupService.cleanup_old_backups(retention_days=30)
                logger.info(f"Cleaned up {count} old backups")

        except Exception as e:
            logger.error(f"Error during backup cleanup: {e}", exc_info=True)

    @classmethod
    def get_jobs(cls) -> list:
        """取得所有排程工作"""
        if not cls.scheduler:
            return []
        return cls.scheduler.get_jobs()

    @classmethod
    def shutdown(cls) -> None:
        """關閉排程器"""
        if cls.scheduler and cls.scheduler.running:
            cls.scheduler.shutdown()
            logger.info("Backup scheduler shutdown")
