"""Database models for the learning keywords portal."""
from __future__ import annotations

import enum
from datetime import datetime
from typing import Any

from flask_login import UserMixin
from sqlalchemy import event, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .extensions import db


class Role(enum.StrEnum):
    USER = "user"
    ADMIN = "admin"


class BaseModel(db.Model):
    __abstract__ = True

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow, nullable=False, server_default=func.current_timestamp()
    )
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
        server_default=func.current_timestamp(),
    )


class User(UserMixin, TimestampMixin, BaseModel):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    discord_id: Mapped[str] = mapped_column(unique=True, nullable=False, index=True)
    username: Mapped[str] = mapped_column(nullable=False)
    avatar_hash: Mapped[str | None]  # 儲存 Discord avatar hash
    role: Mapped[Role] = mapped_column(default=Role.USER, nullable=False)
    active: Mapped[bool] = mapped_column("is_active", default=True, nullable=False)

    keywords: Mapped[list["LearningKeyword"]] = relationship(
        back_populates="author", cascade="all, delete-orphan", lazy="dynamic"
    )

    def is_admin(self) -> bool:
        return self.role == Role.ADMIN

    @property
    def is_active(self) -> bool:  # type: ignore[override]
        return bool(self.active)

    @is_active.setter
    def is_active(self, value: bool) -> None:
        self.active = bool(value)
    
    def get_avatar_url(self, size: int = 256) -> str:
        """動態從 Discord CDN 取得頭像 URL"""
        if self.avatar_hash:
            # 檢查是否為動態頭像 (animated GIF)
            if self.avatar_hash.startswith('a_'):
                ext = 'gif'
            else:
                ext = 'png'  # 使用 PNG 格式以確保兼容性
            return f"https://cdn.discordapp.com/avatars/{self.discord_id}/{self.avatar_hash}.{ext}"
        # 如果沒有頭像,返回預設頭像
        # 檢查 discord_id 是否為數字
        try:
            avatar_index = int(self.discord_id) % 5
        except (ValueError, TypeError):
            # 如果不是數字，使用用戶名的 hash
            avatar_index = hash(self.discord_id) % 5
        return f"https://cdn.discordapp.com/embed/avatars/{avatar_index}.png"


class KeywordCategory(TimestampMixin, BaseModel):
    __tablename__ = "keyword_categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(unique=True, nullable=False, index=True)
    description: Mapped[str | None]
    position: Mapped[int] = mapped_column(default=0, nullable=False)
    icon: Mapped[str] = mapped_column(default="bi-folder", nullable=False)
    is_public: Mapped[bool] = mapped_column(default=True, nullable=False, index=True)

    keywords: Mapped[list["LearningKeyword"]] = relationship(
        back_populates="category", cascade="all, delete-orphan"
    )


class LearningKeyword(TimestampMixin, BaseModel):
    __tablename__ = "learning_keywords"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(nullable=False, unique=True)
    slug: Mapped[str] = mapped_column(nullable=False, unique=True, index=True)
    description_markdown: Mapped[str] = mapped_column(nullable=False)
    position: Mapped[int] = mapped_column(default=0, nullable=False)
    is_public: Mapped[bool] = mapped_column(default=True, nullable=False, index=True)
    view_count: Mapped[int] = mapped_column(default=0, nullable=False)
    
    # SEO 優化內容
    seo_content: Mapped[str | None] = mapped_column(db.Text, nullable=True)
    seo_auto_generate: Mapped[bool] = mapped_column(default=True, nullable=False)

    category_id: Mapped[int] = mapped_column(db.ForeignKey("keyword_categories.id"), nullable=False)
    author_id: Mapped[int] = mapped_column(db.ForeignKey("users.id"), nullable=False)

    category: Mapped[KeywordCategory] = relationship(back_populates="keywords")
    author: Mapped[User] = relationship(back_populates="keywords")
    videos: Mapped[list["YouTubeVideo"]] = relationship(
        back_populates="keyword", cascade="all, delete-orphan"
    )
    aliases: Mapped[list["KeywordAlias"]] = relationship(
        back_populates="keyword", cascade="all, delete-orphan", order_by="KeywordAlias.title.asc()"
    )


class KeywordAlias(TimestampMixin, BaseModel):
    __tablename__ = "keyword_aliases"

    id: Mapped[int] = mapped_column(primary_key=True)
    keyword_id: Mapped[int] = mapped_column(db.ForeignKey("learning_keywords.id"), nullable=False)
    title: Mapped[str] = mapped_column(nullable=False)
    slug: Mapped[str] = mapped_column(nullable=False, unique=True, index=True)

    keyword: Mapped[LearningKeyword] = relationship(back_populates="aliases")


class YouTubeVideo(TimestampMixin, BaseModel):
    __tablename__ = "youtube_videos"

    id: Mapped[int] = mapped_column(primary_key=True)
    keyword_id: Mapped[int] = mapped_column(db.ForeignKey("learning_keywords.id"), nullable=False)
    title: Mapped[str]
    url: Mapped[str] = mapped_column(nullable=False)

    keyword: Mapped[LearningKeyword] = relationship(back_populates="videos")


class NavigationLink(TimestampMixin, BaseModel):
    __tablename__ = "navigation_links"

    id: Mapped[int] = mapped_column(primary_key=True)
    label: Mapped[str] = mapped_column(nullable=False)
    url: Mapped[str] = mapped_column(nullable=False)
    icon: Mapped[str | None]
    position: Mapped[int] = mapped_column(default=0, nullable=False)


class FooterSocialLink(TimestampMixin, BaseModel):
    __tablename__ = "footer_social_links"

    id: Mapped[int] = mapped_column(primary_key=True)
    label: Mapped[str] = mapped_column(nullable=False)
    url: Mapped[str] = mapped_column(nullable=False)
    icon: Mapped[str | None]
    position: Mapped[int] = mapped_column(default=0, nullable=False)


class AnnouncementBanner(TimestampMixin, BaseModel):
    __tablename__ = "announcement_banners"

    id: Mapped[int] = mapped_column(primary_key=True)
    text: Mapped[str] = mapped_column(nullable=False)
    url: Mapped[str | None]
    icon: Mapped[str] = mapped_column(default="bi-info-circle-fill", nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    position: Mapped[int] = mapped_column(default=0, nullable=False)


class SiteSettingKey(enum.StrEnum):
    SITE_TITLE = "site_title"
    SITE_SUBTITLE = "site_subtitle"
    SITE_TITLE_SUFFIX = "site_title_suffix"
    FOOTER_TITLE = "footer_title"
    FOOTER_DESCRIPTION = "footer_description"
    HEADER_LOGO_URL = "header_logo_url"
    HEADER_LOGO_FILE = "header_logo_file"
    FOOTER_LOGO_URL = "footer_logo_url"
    FOOTER_LOGO_FILE = "footer_logo_file"
    FOOTER_COPY = "footer_copy"
    FAVICON_FILE = "favicon_file"
    REGISTRATION_USER_KEY = "registration_user_key"
    REGISTRATION_ADMIN_KEY = "registration_admin_key"


class SiteSetting(TimestampMixin, BaseModel):
    __tablename__ = "site_settings"

    key: Mapped[str] = mapped_column(primary_key=True)
    value: Mapped[str] = mapped_column(nullable=False)

    @classmethod
    def get(cls, key: SiteSettingKey, default: str | None = None) -> str | None:
        record = cls.query.filter_by(key=key.value).first()
        return record.value if record else default

    @classmethod
    def set(cls, key: SiteSettingKey, value: str) -> None:
        record = cls.query.filter_by(key=key.value).first()
        if record:
            record.value = value
        else:
            record = cls(key=key.value, value=value)
            db.session.add(record)
        db.session.commit()

    @classmethod
    def as_dict(cls) -> dict[str, str]:  # pragma: no cover - simple mapping
        return {row.key: row.value for row in cls.query.all()}


class EditLogAction(enum.StrEnum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    PUBLISH = "publish"
    UNPUBLISH = "unpublish"
    MOVE = "move"
    REORDER = "reorder"


class EditLogTarget(enum.StrEnum):
    KEYWORD = "keyword"
    CATEGORY = "category"
    USER = "user"
    ANNOUNCEMENT = "announcement"
    NAVIGATION = "navigation"
    FOOTER = "footer"
    SITE_SETTING = "site_setting"


class EditLog(TimestampMixin, BaseModel):
    __tablename__ = "edit_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(db.ForeignKey("users.id"), nullable=False, index=True)
    action: Mapped[EditLogAction] = mapped_column(nullable=False, index=True)
    target_type: Mapped[EditLogTarget] = mapped_column(nullable=False, index=True)
    target_id: Mapped[int | None] = mapped_column(nullable=True)
    target_name: Mapped[str | None] = mapped_column(nullable=True)
    description: Mapped[str | None] = mapped_column(db.Text, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(nullable=True)
    user_agent: Mapped[str | None] = mapped_column(db.Text, nullable=True)

    user: Mapped[User] = relationship(backref="edit_logs")


class KeywordGoalList(TimestampMixin, BaseModel):
    """關鍵字目標清單 - 用於協同完成大量關鍵字創建"""
    __tablename__ = "keyword_goal_lists"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(nullable=False)
    description: Mapped[str | None] = mapped_column(db.Text, nullable=True)
    category_name: Mapped[str] = mapped_column(nullable=False)  # 自動創建的分類名稱
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    created_by: Mapped[int] = mapped_column(db.ForeignKey("users.id"), nullable=False)

    creator: Mapped[User] = relationship(backref="created_goal_lists")
    items: Mapped[list["KeywordGoalItem"]] = relationship(
        back_populates="goal_list", 
        cascade="all, delete-orphan", 
        order_by="(KeywordGoalItem.is_completed.asc(), KeywordGoalItem.position.asc())"
    )

    @property
    def total_items(self) -> int:
        return len(self.items)

    @property
    def completed_items(self) -> int:
        return sum(1 for item in self.items if item.is_completed)

    @property
    def completion_rate(self) -> float:
        if self.total_items == 0:
            return 0.0
        return (self.completed_items / self.total_items) * 100


class SystemBackup(TimestampMixin, BaseModel):
    """系統備份記錄"""
    __tablename__ = "system_backups"

    id: Mapped[int] = mapped_column(primary_key=True)
    filename: Mapped[str] = mapped_column(nullable=False, unique=True, index=True)
    filepath: Mapped[str] = mapped_column(nullable=False)
    file_size: Mapped[int] = mapped_column(default=0, nullable=False)  # 檔案大小（字節）
    backup_type: Mapped[str] = mapped_column(default="auto", nullable=False)  # auto = 自動, manual = 手動
    created_by: Mapped[int | None] = mapped_column(db.ForeignKey("users.id"), nullable=True)
    description: Mapped[str | None]  # 備份說明
    is_compressed: Mapped[bool] = mapped_column(default=False, nullable=False)  # 是否已壓縮

    creator: Mapped[User | None] = relationship(backref="backups")

    def get_display_size(self) -> str:
        """取得格式化的檔案大小"""
        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.2f} {unit}"
            size /= 1024
        return f"{size:.2f} TB"

    def is_older_than_days(self, days: int) -> bool:
        """檢查備份是否超過指定天數"""
        age = datetime.utcnow() - self.created_at
        return age.days >= days


class KeywordGoalItem(TimestampMixin, BaseModel):
    """關鍵字目標項目"""
    __tablename__ = "keyword_goal_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    goal_list_id: Mapped[int] = mapped_column(db.ForeignKey("keyword_goal_lists.id"), nullable=False)
    title: Mapped[str] = mapped_column(nullable=False)
    position: Mapped[int] = mapped_column(default=0, nullable=False)
    is_completed: Mapped[bool] = mapped_column(default=False, nullable=False)
    keyword_id: Mapped[int | None] = mapped_column(db.ForeignKey("learning_keywords.id"), nullable=True)
    completed_by: Mapped[int | None] = mapped_column(db.ForeignKey("users.id"), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(nullable=True)

    goal_list: Mapped[KeywordGoalList] = relationship(back_populates="items")
    keyword: Mapped[LearningKeyword | None] = relationship(backref="goal_items")
    completer: Mapped[User | None] = relationship(backref="completed_goal_items")


def slugify(value: str) -> str:
    """Convert a string into a URL-friendly slug."""
    slug = value.lower().strip()
    allowed = [(ch if ch.isalnum() else "-") for ch in slug]
    condensed = "".join(allowed)
    while "--" in condensed:
        condensed = condensed.replace("--", "-")
    return condensed.strip("-")


@event.listens_for(LearningKeyword.title, "set", retval=True)
def set_slugifier(target: LearningKeyword, value: str, oldvalue: str, initiator: Any) -> str:
    target.slug = slugify(value)
    return value
