# Pterodactyl 自動部署指引

本指引說明如何設定 GitHub Actions 自動部署到 Pterodactyl 伺服器（使用 Python Generic Egg）。

## 📋 目錄

1. [前置需求](#前置需求)
2. [Pterodactyl 伺服器設定](#pterodactyl-伺服器設定)
3. [GitHub 設定](#github-設定)
4. [部署流程](#部署流程)
5. [故障排除](#故障排除)
6. [手動部署與管理](#手動部署與管理)

---

## 🔧 前置需求

### 本地環境
- Git 已安裝並配置
- 有 GitHub 倉庫的寫入權限
- （可選）Pterodactyl Panel 管理員訪問權限

### Pterodactyl 伺服器
- 使用 **Python Generic Egg**
- Python 3.11 Docker 映像
- Git 自動更新功能已啟用（Auto Update = 1）
- 足夠的磁碟空間（建議至少 2GB）
- 已配置 Pterodactyl API 訪問

### 必要資訊
- Pterodactyl Panel URL（例如：`panel.yourdomain.com`）
- Pterodactyl Server ID（在伺服器 URL 中可見）
- Pterodactyl API Key（Client API Key）
- GitHub 倉庫 URL（`https://github.com/dishighschool/DHS_KeywordSystem.git`）

---

## 🖥️ Pterodactyl 伺服器設定

### 1. 創建 Python 伺服器

在 Pterodactyl Panel 中創建新伺服器：

**基本設定：**
- Server Name: `Learning Keywords Portal`
- Egg: `Python Generic`
- Docker Image: `Python 3.11`

### 2. 配置 Startup 設定

在 Pterodactyl Panel → 你的伺服器 → Startup 頁面：

**Startup Command:**
```bash
if [[ -d .git ]] && [[ "1" == "1" ]]; then git pull; fi; if [[ ! -z "" ]]; then pip install -U --prefix .local ; fi; if [[ -f /home/container/${REQUIREMENTS_FILE} ]]; then pip install -U --prefix .local -r ${REQUIREMENTS_FILE}; fi; /usr/local/bin/python /home/container/wsgi.py
```

**重要變數設定：**

| 變數名稱 | 值 | 說明 |
|---------|---|------|
| `Git Repo Address` | `https://github.com/dishighschool/DHS_KeywordSystem.git` | 您的 GitHub 倉庫 URL |
| `Git Branch` | `master` | 要部署的分支 |
| `Auto Update` | `1` | 啟用自動 Git pull（重要！） |
| `App py file` | `wsgi.py` | 應用程式入口檔案 |
| `Requirements file` | `pyproject.toml` | 依賴檔案 |
| `User Uploaded Files` | `0` | 使用 Git 而非手動上傳 |
| `Git Username` | （留空或填入） | 如果是 public repo 可留空 |
| `Git Access Token` | （留空或填入） | Private repo 需要 GitHub PAT |

⚠️ **關鍵設定：** `Auto Update = 1` 會在每次伺服器重啟時自動執行 `git pull`

### 3. 配置應用程式啟動檔案

確保您的 `wsgi.py` 可以直接運行：

**檢查 wsgi.py 內容：**
```python
# wsgi.py
from app import create_app

app = create_app()

if __name__ == "__main__":
    # For Pterodactyl direct execution
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
```

或者使用 Gunicorn（推薦用於生產環境）：

**修改 Startup Command 使用 Gunicorn：**
```bash
if [[ -d .git ]] && [[ "1" == "1" ]]; then git pull; fi; if [[ -f /home/container/${REQUIREMENTS_FILE} ]]; then pip install -U --prefix .local -r ${REQUIREMENTS_FILE}; fi; /home/container/.local/bin/gunicorn -w 4 -b 0.0.0.0:5000 wsgi:app
```

### 4. 配置環境變數

在 Pterodactyl 伺服器檔案管理中創建 `.env` 檔案：

在 Pterodactyl Files 中創建 `.env` 檔案（或透過 Console）：

```bash
# 在 Pterodactyl Console 中執行
cat > .env << 'EOF'
SECRET_KEY=<使用 python -c "import secrets; print(secrets.token_hex(32))" 生成>
FLASK_ENV=production
DATABASE_URL=sqlite:///instance/app.db

DISCORD_CLIENT_ID=<你的 Discord Client ID>
DISCORD_CLIENT_SECRET=<你的 Discord Client Secret>
DISCORD_REDIRECT_URI=https://yourdomain.com/auth/callback
DISCORD_GUILD_ID=<你的 Discord 伺服器 ID>
ADMIN_ROLE_ID=<管理員角色 ID>
MODERATOR_ROLE_ID=<版主角色 ID>

SERVER_NAME=yourdomain.com
PREFERRED_URL_SCHEME=https
SESSION_COOKIE_SECURE=True
EOF
```

### 5. 初始化資料庫

在 Pterodactyl Console 中執行：

```bash
# 確保 instance 目錄存在
mkdir -p instance

# 安裝依賴（如果還沒安裝）
pip install --prefix .local -e .

# 設定 PATH 使用本地安裝的包
export PATH="/home/container/.local/bin:$PATH"

# 運行資料庫遷移
flask db upgrade

# （可選）匯入種子資料
flask seed run
```

### 6. 獲取 Pterodactyl API Key

**創建 Client API Key：**

1. 登入 Pterodactyl Panel
2. 右上角 → Account Settings → API Credentials
3. 點擊 "Create API Key"
4. 描述：`GitHub Actions Deploy`
5. 允許的 IP：留空（或限制為 GitHub Actions IP）
6. 複製生成的 API Key（只會顯示一次！）

**查找 Server ID：**

在瀏覽器中打開您的伺服器頁面，URL 類似：
```
https://panel.yourdomain.com/server/a1b2c3d4
                                        ^^^^^^^^
                                        這就是 Server ID
```

---

## 🔐 GitHub 設定

### 1. 設定 GitHub Secrets

在 GitHub 倉庫中：**Settings → Secrets and variables → Actions → New repository secret**

添加以下 Secrets：

| Secret 名稱 | 說明 | 範例值 | 如何獲取 |
|------------|------|--------|---------|
| `PTERODACTYL_PANEL_URL` | Pterodactyl Panel 網址 | `panel.yourdomain.com` | 您的 Panel 域名（不含 https://） |
| `PTERODACTYL_SERVER_ID` | 伺服器 ID | `a1b2c3d4` | 從伺服器頁面 URL 中複製 |
| `PTERODACTYL_API_KEY` | Client API Key | `ptlc_xxxxxxxxxxxx` | 從 Account Settings → API Credentials 創建 |

**獲取 PTERODACTYL_PANEL_URL：**
```
https://panel.example.com/server/abc123
        ^^^^^^^^^^^^^^^^^^
        這部分就是 PANEL_URL（不要包含 https://）
```

**獲取 PTERODACTYL_SERVER_ID：**
```
https://panel.example.com/server/abc123
                                  ^^^^^^
                                  這就是 SERVER_ID
```

**獲取 PTERODACTYL_API_KEY：**
1. Pterodactyl Panel → 右上角帳號 → API Credentials
2. Create API Key
3. 描述填寫：`GitHub Actions Deployment`
4. 複製生成的 API Key（格式：`ptlc_...`）

### 2. 配置 GitHub Repository（Private Repo）

如果您的倉庫是 Private：

**方案 A：使用 Personal Access Token（推薦）**

1. GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Generate new token → 勾選 `repo` 權限
3. 複製 token（格式：`ghp_...`）
4. 在 Pterodactyl 變數中設定：
   - `Git Username`: 您的 GitHub 用戶名
   - `Git Access Token`: 剛複製的 PAT

**方案 B：使用 Deploy Key**

1. 在 GitHub 倉庫：Settings → Deploy keys → Add deploy key
2. Title: `Pterodactyl Server`
3. Key: 在 Pterodactyl console 執行 `ssh-keygen -t ed25519` 生成，貼上 public key
4. 不勾選 "Allow write access"

### 3. 確認 Git 設定

在 Pterodactyl Console 中測試 Git 訪問：

```bash
# Public repo
git ls-remote https://github.com/dishighschool/DHS_KeywordSystem.git

# Private repo with PAT
git ls-remote https://<USERNAME>:<TOKEN>@github.com/dishighschool/DHS_KeywordSystem.git
```

如果成功，會列出所有分支。

---

## 🚀 部署流程

### 工作原理

**Pterodactyl 自動部署機制：**

1. GitHub Actions 觸發（推送到 master）
2. 運行測試確保程式碼品質
3. 透過 Pterodactyl API 發送 "restart" 信號
4. Pterodactyl 執行 Startup Command：
   - `git pull` 拉取最新程式碼（因為 Auto Update = 1）
   - `pip install` 安裝/更新依賴
   - 重啟應用程式

### 自動部署觸發條件

1. **推送到 master 或 main 分支**
   ```bash
   git add .
   git commit -m "Update feature"
   git push origin master
   ```
   
   → 自動觸發 GitHub Actions → 測試 → Pterodactyl 重啟

2. **手動觸發部署**
   - 前往 GitHub → Actions → Deploy to Pterodactyl
   - 點擊 "Run workflow" → Run workflow

### 部署步驟說明

**GitHub Actions 工作流程：**

```
┌─────────────────────────────────────────┐
│  1. 測試階段 (Test Job)                  │
│  ✓ Checkout 程式碼                       │
│  ✓ 設定 Python 3.11                      │
│  ✓ 安裝依賴                              │
│  ✓ 運行 pytest                           │
└───────────────┬─────────────────────────┘
                │ 測試通過
                ▼
┌─────────────────────────────────────────┐
│  2. 部署階段 (Deploy Job)                │
│  ✓ 呼叫 Pterodactyl API                  │
│  ✓ 發送 restart 信號                     │
└───────────────┬─────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────┐
│  3. Pterodactyl 自動執行                 │
│  ✓ git pull (自動拉取最新程式碼)          │
│  ✓ pip install (更新依賴)                │
│  ✓ python wsgi.py (重啟應用)             │
└─────────────────────────────────────────┘
```

### 監控部署狀態

**GitHub Actions 日誌：**
- 前往 **GitHub → Actions** 標籤
- 查看最新的 workflow 運行狀態
- 點擊具體的 workflow 查看詳細日誌

**Pterodactyl 日誌：**
- Pterodactyl Panel → 你的伺服器 → Console
- 觀察 `git pull` 和應用程式啟動輸出

### 首次部署

第一次設定完成後：

```bash
# 1. 確認所有設定正確
# 2. 推送一個測試提交
git commit --allow-empty -m "Test deployment"
git push origin master

# 3. 觀察 GitHub Actions
# 4. 檢查 Pterodactyl Console 輸出
# 5. 訪問網站確認更新
```

---

## 🔍 故障排除

### 常見問題

#### 1. Pterodactyl API 呼叫失敗

**錯誤訊息：**
```
HTTP request failed with status 401
```

**解決方案：**
- 確認 `PTERODACTYL_API_KEY` 是正確的 Client API Key（格式：`ptlc_...`）
- 不要使用 Application API Key（格式：`ptla_...`）
- 重新生成 API Key 並更新 GitHub Secret
- 確認 API Key 沒有過期

**測試 API 連接：**
```bash
curl -X GET "https://panel.yourdomain.com/api/client/servers/YOUR_SERVER_ID" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Accept: application/json"
```

#### 2. Git Pull 失敗

**錯誤訊息（在 Pterodactyl Console）：**
```
fatal: could not read Username
```

**解決方案：**

**對於 Private Repository：**
- 在 Pterodactyl Startup 變數中設定 `Git Username` 和 `Git Access Token`
- 或修改 `Git Repo Address` 為：`https://USERNAME:TOKEN@github.com/dishighschool/DHS_KeywordSystem.git`

**對於 Public Repository：**
- 確認倉庫 URL 正確：`https://github.com/dishighschool/DHS_KeywordSystem.git`
- 確認沒有設定不必要的 Git credentials

#### 3. 依賴安裝失敗

**錯誤訊息：**
```
ERROR: Could not find a version that satisfies the requirement...
```

**解決方案：**

在 Pterodactyl Console 中手動測試：
```bash
# 清除舊的安裝
rm -rf .local/lib/python3.11/site-packages/*

# 重新安裝
pip install --prefix .local -e .

# 確認安裝
pip list
```

確認 `pyproject.toml` 中的依賴版本正確。

#### 4. 資料庫遷移問題

**問題：** 資料庫沒有自動遷移

**解決方案：**

Pterodactyl Startup Command 預設不執行 `flask db upgrade`。需要手動執行或修改啟動腳本：

**方案 A：修改 Startup Command（推薦）**
```bash
if [[ -d .git ]] && [[ "1" == "1" ]]; then git pull; fi; if [[ -f /home/container/${REQUIREMENTS_FILE} ]]; then pip install -U --prefix .local -r ${REQUIREMENTS_FILE}; fi; export PATH="/home/container/.local/bin:$PATH"; flask db upgrade; /home/container/.local/bin/gunicorn -w 4 -b 0.0.0.0:5000 wsgi:app
```

**方案 B：手動執行**
```bash
# 在 Pterodactyl Console
export PATH="/home/container/.local/bin:$PATH"
flask db upgrade
```

#### 5. 應用程式無法訪問

**問題：** 伺服器啟動但無法訪問網站

**檢查清單：**

1. **檢查端口綁定：**
   ```bash
   # 在 Pterodactyl Console
   netstat -tlnp | grep 5000
   ```

2. **檢查 Pterodactyl 端口分配：**
   - Pterodactyl Panel → Settings → Network
   - 確認端口已分配並且狀態為 "Online"

3. **檢查防火牆規則：**
   - 確認 Pterodactyl 主機允許該端口

4. **檢查應用程式日誌：**
   - Pterodactyl Console 中查看錯誤訊息

#### 6. 測試階段失敗

**錯誤訊息：**
```
pytest failed with exit code 1
```

**解決方案：**
```bash
# 在本地運行測試
pytest tests/ -v

# 跳過特定測試（臨時方案）
pytest tests/ -v -k "not test_name"

# 查看詳細錯誤
pytest tests/ -vv --tb=long
```

如果是環境差異導致：
- 在 `.github/workflows/deploy.yml` 中調整測試環境變數
- 或在測試中添加條件跳過（`@pytest.mark.skipif`）

### 查看日誌

#### GitHub Actions 日誌
```
GitHub → Actions → 選擇 workflow run → 點擊 job → 展開步驟
```

#### Pterodactyl Console 日誌
```
Pterodactyl Panel → 你的伺服器 → Console
```
即時查看：
- Git pull 輸出
- Pip install 進度
- 應用程式啟動訊息
- 錯誤追蹤

#### 應用程式運行日誌

如果需要持久化日誌，修改 Startup Command 添加輸出重導向：
```bash
... gunicorn -w 4 -b 0.0.0.0:5000 wsgi:app --access-logfile access.log --error-logfile error.log
```

然後查看：
```bash
tail -f access.log
tail -f error.log
```

---

## 🛠️ 手動部署與管理

### 透過 Pterodactyl Panel 手動更新

**最簡單的方法：重啟伺服器**

1. Pterodactyl Panel → 你的伺服器
2. 點擊 **Restart** 按鈕
3. 觀察 Console 輸出：
   ```
   Already up to date.  ← Git pull 成功
   Installing dependencies...
   Starting application...
   ```

**為什麼這樣可行？**
- 因為 `Auto Update = 1`，每次重啟都會自動 `git pull`
- Startup Command 會自動安裝依賴
- 無需 SSH 訪問

### 透過 Console 手動操作

#### 1. 更新程式碼

在 Pterodactyl Console 中：
```bash
# 拉取最新程式碼
git pull origin master

# 查看變更
git log -3 --oneline
```

#### 2. 更新依賴

```bash
# 安裝/更新依賴
pip install --prefix .local -e .

# 列出已安裝的包
pip list
```

#### 3. 運行資料庫遷移

```bash
# 設定 PATH
export PATH="/home/container/.local/bin:$PATH"

# 檢查待遷移
flask db current
flask db heads

# 執行遷移
flask db upgrade

# 確認遷移成功
flask db current
```

#### 4. 管理應用程式

```bash
# 查看運行中的進程
ps aux | grep python

# 重啟（方法 1：使用 Pterodactyl Restart 按鈕）
# 重啟（方法 2：在 Console 手動）
pkill -f python
# 然後點擊 Pterodactyl 的 Start 按鈕
```

### 回滾到特定版本

```bash
# 查看提交歷史
git log --oneline -10

# 回滾到特定提交
git reset --hard abc1234

# 或回滾到上一個版本
git reset --hard HEAD~1

# 重啟應用程式
# 使用 Pterodactyl Restart 按鈕
```

### 備份與恢復

#### 手動備份資料庫

```bash
# 創建備份
cp instance/app.db instance/app.db.manual.$(date +%Y%m%d_%H%M%S)

# 列出所有備份
ls -lh instance/*.db*
```

#### 使用內建備份功能

```bash
# 透過 Flask CLI 創建備份
export PATH="/home/container/.local/bin:$PATH"
flask shell
>>> from app.utils.backup_service import BackupService
>>> BackupService.create_backup(backup_type='manual', description='Before major update')
>>> exit()
```

#### 恢復資料庫

```bash
# 列出可用備份
ls -lh instance/app.db.backup.*

# 停止應用程式（使用 Pterodactyl Stop 按鈕）

# 恢復備份
cp instance/app.db instance/app.db.before_restore  # 先備份當前版本
cp instance/app.db.backup.20250109_120000 instance/app.db

# 重啟應用程式（使用 Pterodactyl Start 按鈕）
```

### 查看應用程式狀態

```bash
# 檢查進程
ps aux | grep python
ps aux | grep gunicorn

# 檢查端口
netstat -tlnp | grep 5000

# 查看環境變數
env | grep FLASK
env | grep DISCORD

# 測試應用程式
curl http://localhost:5000/
```

### 檔案管理

**透過 Pterodactyl File Manager：**
1. Pterodactyl Panel → Files
2. 瀏覽、編輯、上傳、下載檔案
3. 編輯 `.env` 環境變數
4. 下載資料庫備份

**常用路徑：**
- 應用程式：`/home/container/`
- 資料庫：`/home/container/instance/app.db`
- 備份：`/home/container/backups/`
- 日誌：`/home/container/*.log`

---

## 📝 維護建議

### 定期維護任務

#### 每週檢查

**在 GitHub：**
- 查看 Actions 運行歷史
- 確認自動部署成功率

**在 Pterodactyl：**
```bash
# 檢查磁碟空間
df -h

# 查看備份數量和大小
ls -lh backups/ | wc -l
du -sh backups/

# 清理舊備份（如果需要）
cd backups && ls -t system_backup_*.json | tail -n +31 | xargs rm
```

#### 每月檢查

**更新依賴：**
```bash
# 查看過時的套件
pip list --outdated

# 更新特定套件（謹慎！）
pip install --upgrade Flask

# 或更新所有（測試後再部署）
pip install --upgrade -r <(pip freeze)
```

**檢查日誌異常：**
```bash
# 在 Pterodactyl Console
grep -i error *.log | tail -20
grep -i warning *.log | tail -20
```

**資料庫維護：**
```bash
# 檢查資料庫大小
ls -lh instance/app.db

# 執行 VACUUM（壓縮資料庫）
sqlite3 instance/app.db "VACUUM;"
```

#### 備份策略

**自動備份：**
- ✅ 系統每天 1:00 AM 自動備份
- ✅ 保留 30 天（每天 2:00 AM 清理）
- ✅ 備份儲存在 `backups/` 目錄

**手動備份重要時刻：**
```bash
# 大更新前
cp instance/app.db instance/app.db.before_major_update

# 或使用內建功能（在管理後台）
# 資料管理 & 備份 → 創建手動備份
```

**下載備份到本地：**
1. Pterodactyl Panel → Files → backups/
2. 右鍵備份檔案 → Download
3. 儲存到本地安全位置

### 安全建議

#### 環境變數安全

**必做：**
- ✅ `.env` 已在 `.gitignore` 中（不會提交到 Git）
- ✅ 使用強隨機 `SECRET_KEY`（32+ 字元）
- ✅ Discord OAuth Secret 不要共享

**定期更換 SECRET_KEY：**
```bash
# 生成新的 SECRET_KEY
python -c "import secrets; print(secrets.token_hex(32))"

# 在 Pterodactyl Files 中編輯 .env
# 更新 SECRET_KEY=新的值

# 重啟應用程式（所有使用者需要重新登入）
```

#### Pterodactyl API 安全

**保護 API Key：**
- ✅ 只儲存在 GitHub Secrets（加密）
- ✅ 定期 rotate API Key
- ⚠️ 不要在程式碼或文件中明文寫出

**Rotate API Key 步驟：**
1. Pterodactyl → API Credentials → Delete 舊 Key
2. Create New API Key
3. 更新 GitHub Secret: `PTERODACTYL_API_KEY`

#### 應用程式安全

**依賴安全：**
```bash
# 檢查安全漏洞（需要先安裝 safety）
pip install --prefix .local safety
safety check

# 或使用 GitHub Dependabot（自動）
# Settings → Security → Dependabot → Enable
```

**訪問控制：**
- 定期審查 Discord 角色權限
- 移除不活躍的管理員
- 在後台檢查「編輯歷史」

**HTTPS 設定（重要！）：**

如果使用反向代理（Nginx/Caddy）：
```nginx
# Nginx 範例
server {
    listen 443 ssl http2;
    server_name yourdomain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

並更新 `.env`：
```ini
PREFERRED_URL_SCHEME=https
SESSION_COOKIE_SECURE=True
```

### 效能監控

**資源使用：**
```bash
# 在 Pterodactyl Console
# CPU 和記憶體
top -b -n 1 | head -15

# 查看 Python 進程
ps aux | grep python
```

**應用程式效能：**
- 監控頁面載入時間
- 檢查資料庫查詢效率
- 優化圖片和靜態資源

**Gunicorn Workers 調整：**

如果需要更多並發：
```bash
# 修改 Startup Command 中的 -w 參數
# -w 4  → 4 個 workers
# -w 8  → 8 個 workers（需要更多 RAM）

# 建議：workers = (CPU cores * 2) + 1
```

---

## 📞 支援

如遇到問題：

1. 查看 [GitHub Issues](https://github.com/dishighschool/DHS_KeywordSystem/issues)
2. 檢查 GitHub Actions 運行日誌
3. 查看伺服器應用程式日誌
4. 參考本文檔的故障排除章節

---

## 📚 相關文件

- [Flask 部署指南](https://flask.palletsprojects.com/en/3.0.x/deploying/)
- [Gunicorn 文件](https://docs.gunicorn.org/)
- [GitHub Actions 文件](https://docs.github.com/en/actions)
- [Pterodactyl 文件](https://pterodactyl.io/project/introduction.html)

---

**最後更新：** 2025-01-09  
**版本：** 1.0.0
