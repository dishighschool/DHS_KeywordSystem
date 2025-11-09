# Pterodactyl 自動部署設定檢查清單

快速設定指南，確保所有配置正確。詳細說明請參考 [PTERODACTYL_DEPLOYMENT_GUIDE.md](./PTERODACTYL_DEPLOYMENT_GUIDE.md)。

## ☑️ 前置準備

- [ ] 已有 Pterodactyl 伺服器（使用 Python Generic Egg）
- [ ] 已有 GitHub 倉庫（dishighschool/DHS_KeywordSystem）
- [ ] 有 Pterodactyl Panel 訪問權限

---

## 1️⃣ Pterodactyl 伺服器配置

### Startup 變數設定

前往：**Pterodactyl Panel → 你的伺服器 → Startup**

| 變數 | 值 | 狀態 |
|------|---|------|
| **Git Repo Address** | `https://github.com/dishighschool/DHS_KeywordSystem.git` | [ ] |
| **Git Branch** | `master` | [ ] |
| **Auto Update** | `1` ⚠️ 必須為 1 | [ ] |
| **App py file** | `wsgi.py` | [ ] |
| **Requirements file** | `pyproject.toml` | [ ] |
| **User Uploaded Files** | `0` | [ ] |

### Startup Command

確認或修改為：
```bash
if [[ -d .git ]] && [[ "1" == "1" ]]; then git pull; fi; if [[ -f /home/container/${REQUIREMENTS_FILE} ]]; then pip install -U --prefix .local -r ${REQUIREMENTS_FILE}; fi; export PATH="/home/container/.local/bin:$PATH"; /home/container/.local/bin/gunicorn -w 4 -b 0.0.0.0:5000 wsgi:app
```

- [ ] Startup Command 已更新

### Docker Image

- [ ] 已選擇 **Python 3.11**

---

## 2️⃣ 環境變數配置

### 創建 .env 檔案

前往：**Pterodactyl Panel → Files** 或使用 Console

**必填變數：**
```ini
SECRET_KEY=<執行: python -c "import secrets; print(secrets.token_hex(32))">
FLASK_ENV=production
DATABASE_URL=sqlite:///instance/app.db

DISCORD_CLIENT_ID=你的Discord_Client_ID
DISCORD_CLIENT_SECRET=你的Discord_Client_Secret
DISCORD_REDIRECT_URI=https://你的域名.com/auth/callback
DISCORD_GUILD_ID=你的Discord伺服器ID

ADMIN_ROLE_ID=管理員角色ID
MODERATOR_ROLE_ID=版主角色ID (可選)

SERVER_NAME=你的域名.com
PREFERRED_URL_SCHEME=https
SESSION_COOKIE_SECURE=True
```

- [ ] `.env` 檔案已創建
- [ ] 所有必填變數已設定
- [ ] Discord OAuth 已配置

---

## 3️⃣ 初始化資料庫

在 **Pterodactyl Console** 中執行：

```bash
# 1. 確保 instance 目錄存在
mkdir -p instance

# 2. 設定 PATH
export PATH="/home/container/.local/bin:$PATH"

# 3. 運行資料庫遷移
flask db upgrade

# 4. (可選) 匯入種子資料
flask seed run
```

- [ ] instance 目錄已創建
- [ ] 資料庫遷移已執行
- [ ] 應用程式可以正常啟動

**測試啟動：**
```bash
# 啟動測試
python wsgi.py
# 看到 "Running on http://0.0.0.0:5000" 表示成功
# Ctrl+C 停止
```

---

## 4️⃣ 獲取 Pterodactyl API 憑證

### A. 獲取 Panel URL

從瀏覽器網址列複製（不含 https://）：
```
https://panel.example.com/server/abc123
        ^^^^^^^^^^^^^^^^^^
```

- [ ] Panel URL: `_____________________`

### B. 獲取 Server ID

從瀏覽器網址列複製：
```
https://panel.example.com/server/abc123
                                  ^^^^^^
```

- [ ] Server ID: `_____________________`

### C. 創建 API Key

1. **Pterodactyl Panel** → 右上角頭像 → **Account Settings**
2. **API Credentials** → **Create API Key**
3. Description: `GitHub Actions Deployment`
4. **複製生成的 Key**（格式：`ptlc_...`）

- [ ] API Key 已創建
- [ ] API Key: `ptlc_____________________`

---

## 5️⃣ GitHub Secrets 配置

前往：**GitHub → 倉庫 Settings → Secrets and variables → Actions**

點擊 **New repository secret**，逐一添加：

### Secret 1: PTERODACTYL_PANEL_URL
- Name: `PTERODACTYL_PANEL_URL`
- Value: `panel.example.com` （不含 https://）
- [ ] 已添加

### Secret 2: PTERODACTYL_SERVER_ID
- Name: `PTERODACTYL_SERVER_ID`
- Value: `abc123` （你的 Server ID）
- [ ] 已添加

### Secret 3: PTERODACTYL_API_KEY
- Name: `PTERODACTYL_API_KEY`
- Value: `ptlc_...` （完整的 API Key）
- [ ] 已添加

---

## 6️⃣ Private Repository 設定（如適用）

如果你的倉庫是 **Private**：

### 方案 A：使用 Personal Access Token（推薦）

1. **GitHub** → Settings → Developer settings → Personal access tokens → **Tokens (classic)**
2. Generate new token → 勾選 `repo` 權限
3. 複製 token（格式：`ghp_...`）
4. 在 **Pterodactyl Startup 變數**中設定：
   - `Git Username`: 你的 GitHub 用戶名
   - `Git Access Token`: 剛複製的 token

- [ ] GitHub PAT 已創建
- [ ] Pterodactyl 變數已設定

### 方案 B：修改 Git Repo Address

將 `Git Repo Address` 改為：
```
https://你的用戶名:ghp_token@github.com/dishighschool/DHS_KeywordSystem.git
```

- [ ] Git Repo Address 已更新為含 token 版本

---

## 7️⃣ 測試部署

### 本地測試

```bash
# 確保所有變更已提交
git status

# 測試提交（空提交用於測試）
git commit --allow-empty -m "Test: GitHub Actions deployment"
git push origin master
```

- [ ] 程式碼已推送

### 觀察 GitHub Actions

1. **GitHub** → Actions → 等待 workflow 出現
2. 點擊 "Deploy to Pterodactyl" workflow
3. 查看兩個 jobs：
   - ✅ **Test** - 運行測試
   - ✅ **Deploy** - 觸發 Pterodactyl 重啟

- [ ] GitHub Actions 測試階段通過
- [ ] GitHub Actions 部署階段成功

### 觀察 Pterodactyl Console

1. **Pterodactyl Panel** → Console
2. 應該看到：
   ```
   Already up to date.  (或顯示拉取的提交)
   Installing dependencies...
   Starting application...
   ```

- [ ] Git pull 成功
- [ ] 依賴安裝成功
- [ ] 應用程式啟動成功

### 訪問網站

打開瀏覽器訪問你的網站：

- [ ] 網站可以正常訪問
- [ ] Discord OAuth 登入正常
- [ ] 管理後台可以訪問

---

## 8️⃣ 日常使用

### 部署新版本

```bash
# 1. 修改程式碼
git add .
git commit -m "Add new feature"

# 2. 推送到 master（自動觸發部署）
git push origin master

# 3. 等待 GitHub Actions 完成
# 4. Pterodactyl 會自動重啟並拉取最新程式碼
```

### 手動觸發部署

如果需要手動觸發（不推送程式碼）：

1. **GitHub** → Actions → Deploy to Pterodactyl
2. 點擊 **Run workflow** → Run workflow

---

## ❗ 常見問題快速檢查

### 問題：GitHub Actions 失敗 (401 Unauthorized)

- [ ] 確認 `PTERODACTYL_API_KEY` 格式正確（`ptlc_...`）
- [ ] 確認 API Key 沒有過期
- [ ] 嘗試重新創建 API Key

### 問題：Git pull 失敗 (Private repo)

- [ ] 確認 `Git Username` 和 `Git Access Token` 已設定
- [ ] 確認 PAT 有 `repo` 權限
- [ ] 測試：`git ls-remote https://USERNAME:TOKEN@github.com/...`

### 問題：應用程式無法啟動

- [ ] 檢查 `.env` 檔案是否存在
- [ ] 確認所有必填環境變數已設定
- [ ] 執行 `flask db upgrade`
- [ ] 查看 Console 錯誤訊息

### 問題：資料庫遷移未自動執行

修改 Startup Command 添加 `flask db upgrade`：
```bash
...; export PATH="/home/container/.local/bin:$PATH"; flask db upgrade; /home/container/.local/bin/gunicorn ...
```

---

## ✅ 完成！

當所有項目都打勾時，你的自動部署系統就設定完成了！

**下一步：**
- 📖 閱讀完整指南：[PTERODACTYL_DEPLOYMENT_GUIDE.md](./PTERODACTYL_DEPLOYMENT_GUIDE.md)
- 🔒 設定 HTTPS 和反向代理
- 📊 監控備份和日誌
- 🎉 享受自動部署的便利！

---

**問題回報：**
如遇問題，請查看：
1. GitHub Actions 詳細日誌
2. Pterodactyl Console 輸出
3. [故障排除章節](./PTERODACTYL_DEPLOYMENT_GUIDE.md#故障排除)

**最後更新：** 2025-01-09
