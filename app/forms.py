"""WTForms definitions for admin CRUD interfaces."""
from __future__ import annotations

from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField
from wtforms import (
    BooleanField,
    FieldList,
    FormField,
    HiddenField,
    IntegerField,
    SelectField,
    StringField,
    SubmitField,
    TextAreaField,
    URLField,
    ValidationError,
)
from wtforms.validators import DataRequired, Length, NumberRange, Optional, URL, ValidationError as WTFormsValidationError


def validate_youtube_url(form, field):
    """驗證是否為有效的 YouTube URL"""
    if not field.data:
        return  # 如果是空的，由 Optional() 處理
    
    from .utils.youtube import extract_youtube_video_id
    if not extract_youtube_video_id(field.data):
        raise ValidationError('必須是有效的 YouTube 影片連結')


class CategoryForm(FlaskForm):
    name = StringField("分類名稱", validators=[DataRequired(), Length(max=120)])
    slug = StringField("URL 代稱 (slug)", validators=[Optional(), Length(max=120)])
    description = TextAreaField("描述", validators=[Optional(), Length(max=2000)])
    icon = StringField("圖示 CSS 類別", validators=[Optional(), Length(max=120)], default="bi-folder")
    is_public = BooleanField("公開顯示", default=True)
    submit = SubmitField("儲存分類")


class NavigationLinkForm(FlaskForm):
    label = StringField("標籤", validators=[DataRequired(), Length(max=120)])
    url = URLField("連結", validators=[DataRequired(), URL()])
    icon = StringField("圖示 CSS", validators=[Optional(), Length(max=120)])
    position = IntegerField("排序權重", validators=[Optional(), NumberRange(min=0, max=9999)])
    submit = SubmitField("儲存導航連結")


class FooterLinkForm(FlaskForm):
    label = StringField("標籤", validators=[DataRequired(), Length(max=120)])
    url = URLField("連結", validators=[DataRequired(), URL()])
    icon = StringField("圖示 CSS", validators=[Optional(), Length(max=120)])
    position = IntegerField("排序權重", validators=[Optional(), NumberRange(min=0, max=9999)])
    submit = SubmitField("儲存底部連結")


class AnnouncementBannerForm(FlaskForm):
    text = StringField("公告內容", validators=[DataRequired(), Length(max=200)])
    url = URLField("連結網址", validators=[Optional(), URL()])
    icon = StringField("圖標", validators=[Optional(), Length(max=50)], default="bi-info-circle-fill")
    is_active = BooleanField("啟用顯示", default=True)
    position = IntegerField("排序權重", validators=[Optional(), NumberRange(min=0, max=9999)])
    submit = SubmitField("儲存公告")


class SiteBrandingForm(FlaskForm):
    site_title = StringField("網站標題", validators=[Optional(), Length(max=100)])
    site_subtitle = StringField("網站副標題", validators=[Optional(), Length(max=200)])
    site_title_suffix = StringField("網頁標題後綴", validators=[Optional(), Length(max=100)])
    footer_title = StringField("頁尾標題", validators=[Optional(), Length(max=100)])
    footer_description = TextAreaField("頁尾描述文字", validators=[Optional(), Length(max=500)])
    header_logo_url = URLField("導航 Logo 連結", validators=[Optional(), URL()])
    header_logo_file = FileField(
        "或上傳 Logo 圖片", 
        validators=[Optional(), FileAllowed(["png", "jpg", "jpeg", "gif", "svg", "webp"], "只允許上傳圖片檔案")]
    )
    footer_logo_url = URLField("底部 Logo 連結", validators=[Optional(), URL()])
    footer_logo_file = FileField(
        "或上傳 Logo 圖片", 
        validators=[Optional(), FileAllowed(["png", "jpg", "jpeg", "gif", "svg", "webp"], "只允許上傳圖片檔案")]
    )
    favicon_file = FileField(
        "網站圖示 (Favicon)", 
        validators=[Optional(), FileAllowed(["ico", "png"], "只允許上傳 .ico 或 .png 檔案")]
    )
    footer_copy = StringField("底部版權文字", validators=[Optional(), Length(max=255)])
    member_api_base_url = URLField("成員頁面 API 基底 URL", validators=[Optional(), URL()], default="http://member.dhs.todothere.com")
    submit = SubmitField("更新品牌設定")


class YouTubeVideoForm(FlaskForm):
    title = StringField("影片標題", validators=[Optional(), Length(max=200)])
    url = URLField("影片連結", validators=[Optional(), URL(), validate_youtube_url])


class KeywordAliasForm(FlaskForm):
    alias_id = HiddenField("ID")
    title = StringField("別名", validators=[Optional(), Length(max=200)])


class KeywordForm(FlaskForm):
    title = StringField("關鍵字標題", validators=[DataRequired(), Length(max=200)])
    category_id = SelectField("分類", coerce=int, validators=[DataRequired()])
    description_markdown = TextAreaField("內容 (Markdown)", validators=[DataRequired()])
    is_public = BooleanField("公開顯示", default=True)
    seo_auto_generate = BooleanField("自動生成 SEO 內容", default=True)
    seo_content = TextAreaField("自訂 SEO 內容 (HTML)", validators=[Optional()])
    videos = FieldList(FormField(YouTubeVideoForm), min_entries=0, max_entries=10)
    aliases = FieldList(FormField(KeywordAliasForm), min_entries=0, max_entries=20)
    submit = SubmitField("儲存關鍵字")
    regenerate_seo = SubmitField("重新生成 SEO 內容")


class RegistrationKeyRequestForm(FlaskForm):
    key = StringField("註冊金鑰", validators=[DataRequired(), Length(max=255)])
    submit = SubmitField("驗證金鑰並登入 Discord")


class RegistrationKeyManagerForm(FlaskForm):
    user_key = StringField("團隊成員金鑰", validators=[DataRequired(), Length(max=255)])
    admin_key = StringField("管理員金鑰", validators=[DataRequired(), Length(max=255)])
    submit = SubmitField("更新金鑰")


class UserProfileForm(FlaskForm):
    username = StringField("顯示名稱", validators=[DataRequired(), Length(min=1, max=200)])
    submit = SubmitField("儲存變更")


class APISettingsForm(FlaskForm):
    member_api_base_url = URLField("成員頁面 API 基底 URL", validators=[DataRequired(), URL()], default="http://member.dhs.todothere.com")
    submit = SubmitField("儲存設定")


class KeywordGoalListForm(FlaskForm):
    name = StringField("清單名稱", validators=[DataRequired(), Length(max=200)])
    description = TextAreaField("描述", validators=[Optional(), Length(max=1000)])
    category_name = StringField("分類名稱", validators=[DataRequired(), Length(max=120)])
    keywords_text = TextAreaField(
        "關鍵字列表 (每行一個)", 
        validators=[DataRequired()],
        render_kw={"rows": 10, "placeholder": "請輸入關鍵字,每行一個\n例如:\n數學\n物理\n化學"}
    )
    submit = SubmitField("建立清單")
