"""Authentication views for Discord OAuth."""
from __future__ import annotations

from flask import Blueprint, flash, redirect, render_template, request, session, url_for, current_app
from flask_login import current_user, login_required, login_user, logout_user

from flask.typing import ResponseReturnValue

from ..extensions import db, oauth
from ..forms import RegistrationKeyRequestForm
from ..models import Role, SiteSetting, SiteSettingKey, User


auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/register", methods=["GET", "POST"])
def register() -> ResponseReturnValue:
    """Collect a registration key for new users after Discord OAuth."""
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    profile = session.get("pending_profile")
    if not profile:
        flash("請先使用 Discord 登入。", "warning")
        return redirect(url_for("auth.login"))

    form = RegistrationKeyRequestForm()
    if form.validate_on_submit():
        submitted_key = (form.key.data or "").strip()
        admin_key = SiteSetting.get(SiteSettingKey.REGISTRATION_ADMIN_KEY)
        user_key = SiteSetting.get(SiteSettingKey.REGISTRATION_USER_KEY)

        matched_role: Role | None = None
        if admin_key and submitted_key == admin_key:
            matched_role = Role.ADMIN
        elif user_key and submitted_key == user_key:
            matched_role = Role.USER

        if matched_role is None:
            flash("金鑰不正確或已失效。", "danger")
        else:
            user = User(
                discord_id=profile["discord_id"],
                username=profile["username"],
                avatar_hash=profile.get("avatar_hash"),
                role=matched_role,
            )
            db.session.add(user)
            db.session.commit()

            session.pop("pending_profile", None)

            login_user(user, remember=True)
            flash("金鑰驗證成功,已完成註冊。", "success")
            next_url = session.pop("next_url", None) or url_for("main.index")
            return redirect(next_url)

    return render_template("auth/register.html", form=form, profile=profile)


@auth_bp.get("/login")
def login() -> ResponseReturnValue:
    """Kick off the Discord OAuth login flow."""
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    redirect_uri = url_for("auth.discord_callback", _external=True)
    session["next_url"] = request.args.get("next")
    discord = oauth.create_client("discord")
    if discord is None:
        flash("Discord OAuth 尚未正確設定。", "danger")
        return redirect(url_for("main.index"))
    return discord.authorize_redirect(redirect_uri)


@auth_bp.get("/discord/callback")
def discord_callback() -> ResponseReturnValue:  # type: ignore[override]
    """Handle OAuth callback from Discord and sign the user in."""
    discord = oauth.create_client("discord")
    if discord is None:
        flash("Discord OAuth 尚未正確設定。", "danger")
        return redirect(url_for("main.index"))

    token = discord.authorize_access_token()
    if not token:
        flash("無法完成 Discord 登入，請稍後再試。", "danger")
        return redirect(url_for("main.index"))

    response = discord.get("users/@me")
    if not response.ok:
        current_app.logger.warning(
            "Discord user info request failed: %s %s", response.status_code, response.text
        )
        flash("無法取得 Discord 使用者資訊。", "danger")
        return redirect(url_for("main.index"))

    try:
        user_info = response.json()
    except ValueError:  # pragma: no cover - defensive error handling
        current_app.logger.warning("Discord user info response not JSON: %s", response.text)
        flash("Discord 回傳資料格式不正確。", "danger")
        return redirect(url_for("main.index"))
    if not user_info:
        flash("無法取得 Discord 使用者資訊。", "danger")
        return redirect(url_for("main.index"))

    discord_id = str(user_info.get("id"))
    username = user_info.get("global_name") or user_info.get("username")
    if not username:
        username = f"Discord 使用者 {discord_id}"
    avatar_hash = user_info.get("avatar")

    user = User.query.filter_by(discord_id=discord_id).first()
    if user:
        # 只更新頭像 hash,不更新成員名稱
        user.avatar_hash = avatar_hash
        db.session.commit()
        session.pop("pending_profile", None)

        login_user(user, remember=True)
        flash("成功登入。", "success")

        next_url = session.pop("next_url", None) or url_for("main.index")
        return redirect(next_url)

    session["pending_profile"] = {
        "discord_id": discord_id,
        "username": username,
        "avatar_hash": avatar_hash,
    }
    flash("請輸入註冊金鑰以完成首次登入。", "info")
    return redirect(url_for("auth.register"))


@auth_bp.get("/logout")
@login_required
def logout() -> ResponseReturnValue:
    """Log out the current user."""
    logout_user()
    flash("已登出。", "info")
    return redirect(url_for("main.index"))
