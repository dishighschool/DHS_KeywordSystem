"""Database seed utilities."""
from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session, scoped_session

from .models import (
    FooterSocialLink,
    KeywordCategory,
    LearningKeyword,
    NavigationLink,
    Role,
    SiteSetting,
    SiteSettingKey,
    User,
    YouTubeVideo,
    slugify,
)


@dataclass
class SeedService:
    session: Session | scoped_session

    def run(self) -> None:
        """Populate baseline content if missing."""
        self._ensure_admin_user()
        self._ensure_categories()
        self._ensure_navigation()
        self._ensure_footer()
        self._ensure_branding()
        self._ensure_registration_keys()

    def _ensure_admin_user(self) -> None:
        admin = User.query.filter_by(role=Role.ADMIN).first()
        if not admin:
            admin = User(discord_id="admin-placeholder", username="Admin", role=Role.ADMIN)
            self.session.add(admin)
            self.session.commit()

    def _ensure_categories(self) -> None:
        physics = KeywordCategory.query.filter_by(name="物理學").first()
        if not physics:
            physics = KeywordCategory(
                name="物理學",
                slug=slugify("物理學"),
                description="經典力學相關內容",
            )
            self.session.add(physics)
            self.session.commit()

        if not LearningKeyword.query.first():
            admin = User.query.filter_by(role=Role.ADMIN).first()
            if admin is None:
                return
            keyword = LearningKeyword(
                title="牛頓第一運動定律",
                description_markdown=(
                    "牛頓第一運動定律指出，若一物體所受的外力為零，"
                    "則該物體將維持靜止或等速直線運動的狀態。"
                ),
                category_id=physics.id,
                author_id=admin.id,
            )
            keyword.videos.append(
                YouTubeVideo(
                    title="Newton's First Law",
                    url="https://www.youtube.com/watch?v=Fs__SMSxApw",
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

    def _ensure_registration_keys(self) -> None:
        if not SiteSetting.get(SiteSettingKey.REGISTRATION_USER_KEY):
            SiteSetting.set(SiteSettingKey.REGISTRATION_USER_KEY, "4PTH4VXXT3XRFQKHLY5K1D7J")
        if not SiteSetting.get(SiteSettingKey.REGISTRATION_ADMIN_KEY):
            SiteSetting.set(SiteSettingKey.REGISTRATION_ADMIN_KEY, "PMKCCL6APU5IHIYNBNUGQVQ8")
