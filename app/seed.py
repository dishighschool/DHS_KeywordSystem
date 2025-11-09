
"""
Database seed utilities for DHS Keyword System.
自動填充初始資料，確保所有主表結構完整。
"""
from __future__ import annotations
from dataclasses import dataclass
from sqlalchemy.orm import Session, scoped_session
from .models import (
    FooterSocialLink, KeywordCategory, LearningKeyword, NavigationLink, Role,
    SiteSetting, SiteSettingKey, User, YouTubeVideo, KeywordAlias,
    AnnouncementBanner, KeywordGoalList, KeywordGoalItem, slugify
)

@dataclass
class SeedService:
    session: Session | scoped_session

    def run(self) -> None:
        """Populate baseline content if missing."""
        self._ensure_admin_user()
        self._ensure_categories_and_keywords()
        self._ensure_navigation()
        self._ensure_footer()
        self._ensure_branding()
        self._ensure_registration_keys()
        self._ensure_announcements()
        self._ensure_goal_list()

    def _ensure_admin_user(self) -> None:
        admin = User.query.filter_by(role=Role.ADMIN).first()
        if not admin:
            admin = User(discord_id="admin-placeholder", username="Admin", role=Role.ADMIN)
            self.session.add(admin)
            self.session.commit()

    def _ensure_categories_and_keywords(self) -> None:
        # 建立預設分類
        physics = KeywordCategory.query.filter_by(name="物理學").first()
        if not physics:
            physics = KeywordCategory(
                name="物理學",
                slug=slugify("物理學"),
                description="經典力學相關內容",
                position=0,
                icon="bi-folder",
                is_public=True,
            )
            self.session.add(physics)
            self.session.commit()

        # 建立預設關鍵字
        if not LearningKeyword.query.first():
            admin = User.query.filter_by(role=Role.ADMIN).first()
            if admin is None:
                return
            keyword = LearningKeyword(
                title="牛頓第一運動定律",
                slug=slugify("牛頓第一運動定律"),
                description_markdown="牛頓第一運動定律指出，若一物體所受的外力為零，則該物體將維持靜止或等速直線運動的狀態。",
                category_id=physics.id,
                author_id=admin.id,
                position=0,
                is_public=True,
                view_count=0,
                seo_content=None,
                seo_auto_generate=True,
            )
            # 關聯影片
            keyword.videos.append(
                YouTubeVideo(
                    title="Newton's First Law",
                    url="https://www.youtube.com/watch?v=Fs__SMSxApw",
                )
            )
            # 關聯別名
            keyword.aliases.append(
                KeywordAlias(
                    title="慣性定律",
                    slug=slugify("慣性定律"),
                )
            )
            self.session.add(keyword)
            self.session.commit()

    def _ensure_navigation(self) -> None:
        if not NavigationLink.query.first():
            home_link = NavigationLink(label="搜尋", url="/", icon="bi-search", position=0)
            self.session.add(home_link)
            self.session.commit()

    def _ensure_footer(self) -> None:
        if not FooterSocialLink.query.first():
            self.session.add(
                FooterSocialLink(
                    label="Discord 社群",
                    url="https://discord.com",
                    icon="bi-discord",
                    position=0,
                )
            )
            self.session.commit()

    def _ensure_branding(self) -> None:
        if not SiteSetting.get(SiteSettingKey.FOOTER_COPY):
            SiteSetting.set(SiteSettingKey.FOOTER_COPY, "© 2025 學習關鍵字平台")
        # 可以設定預設 favicon（如果有預設檔案的話）
        # if not SiteSetting.get(SiteSettingKey.FAVICON_FILE):
        #     SiteSetting.set(SiteSettingKey.FAVICON_FILE, "/static/favicon.ico")

    def _ensure_registration_keys(self) -> None:
        if not SiteSetting.get(SiteSettingKey.REGISTRATION_USER_KEY):
            SiteSetting.set(SiteSettingKey.REGISTRATION_USER_KEY, "4PTH4VXXT3XRFQKHLY5K1D7J")
        if not SiteSetting.get(SiteSettingKey.REGISTRATION_ADMIN_KEY):
            SiteSetting.set(SiteSettingKey.REGISTRATION_ADMIN_KEY, "PMKCCL6APU5IHIYNBNUGQVQ8")

    def _ensure_announcements(self) -> None:
        if not AnnouncementBanner.query.first():
            self.session.add(
                AnnouncementBanner(
                    text="歡迎使用 DHS 學習關鍵字平台！",
                    url=None,
                    icon="bi-info-circle-fill",
                    is_active=True,
                    position=0,
                )
            )
            self.session.commit()

    def _ensure_goal_list(self) -> None:
        if not KeywordGoalList.query.first():
            admin = User.query.filter_by(role=Role.ADMIN).first()
            if admin is None:
                return
            goal_list = KeywordGoalList(
                name="物理學關鍵字目標清單",
                description="協同完成物理學相關關鍵字整理",
                category_name="物理學",
                is_active=True,
                created_by=admin.id,
            )
            goal_list.items.append(
                KeywordGoalItem(
                    title="完成牛頓三大運動定律",
                    position=0,
                    is_completed=False,
                )
            )
            self.session.add(goal_list)
            self.session.commit()
