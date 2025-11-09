# 學習關鍵字查詢系統

以 Flask 打造的全端網站，提供學習關鍵字的搜尋、瀏覽與管理功能，並整合 Discord OAuth 做為唯一的登入機制。系統包含前台與後台，支援分類篩選、Markdown 內容呈現、YouTube 影音嵌入與網站品牌自訂。

## 功能特色

- 🔍 **前台搜尋體驗**:
  - 首頁提供即時搜尋與分類篩選,不需重新整理即可篩選結果
  - **全域搜尋**: 導航欄右側的搜尋框可即時搜尋所有關鍵字,顯示下拉式結果列表
  - 支援關鍵字與別名同步搜尋
- 📘 **SEO 友善的關鍵字頁面**:以大字版面呈現內容並支援 Markdown,完整列出相關 YouTube 影片。
- 🔗 **關鍵字自動連結**:內容中提及的其他關鍵字自動轉為超連結,建立完整的知識網絡。
- 🏷️ **關鍵字別名系統**:為關鍵字設定多個別名,方便使用者以不同名稱搜尋到相同內容。
- 👁️ **觀看次數統計**:自動追蹤每個關鍵字的瀏覽次數,了解內容受歡迎程度。
- 🎨 **美觀的錯誤頁面**:
  - **404 頁面**: 提供搜尋功能和熱門分類推薦
  - **403 頁面**: 清楚說明權限不足原因
  - **500 頁面**: 提供錯誤 ID 追蹤和重試建議
- 🗺️ **自動 Sitemap 生成**:動態生成 sitemap.xml 和 robots.txt,支援搜尋引擎優化和索引管理。
- 🛡️ **內容可見性控制**:
  - 分類與關鍵字可設定為「公開」或「隱藏」狀態
  - 隱藏內容僅在後台顯示,不會出現在前台
- 🗂️ **後台管理**:
  - Discord OAuth 登入,並區分 **管理員** 與 **團隊成員** 權限。
  - 團隊成員可建立/編輯/刪除自己的學習關鍵字。
  - **批次操作功能**: 可同時對多個關鍵字進行:
    - 切換公開/隱藏狀態
    - 批次刪除
    - 批次移動到其他分類
  - 管理員可額外管理分類、導航列、頁尾資訊、品牌設定、Sitemap 與關鍵字連結。
- 🧭 **自訂導覽與頁尾**:Logo、導覽連結與社群連結皆可透過後台調整。

## 系統需求

- Python 3.11 以上
- Discord 開發者平台建立的 OAuth2 應用（取得 Client ID、Client Secret）

## 快速開始

1. **複製專案並建立虛擬環境**

  ```pwsh
  python -m venv .venv
  .\.venv\Scripts\Activate.ps1
  pip install -r requirements-dev.txt
  ```

2. **建立設定檔**

   ```pwsh
   copy .env.example .env
   ```

   將 `.env` 內的 `DISCORD_CLIENT_ID`、`DISCORD_CLIENT_SECRET` 與 `DISCORD_REDIRECT_URI` 更新為你在 Discord 開發者平台上的設定。

3. **初始化資料庫**

   ```pwsh
   flask --app app:create_app db init
   flask --app app:create_app db migrate -m "init"
   flask --app app:create_app db upgrade
   flask --app app:create_app seed
   ```

4. **啟動開發伺服器**

   ```pwsh
   flask --app app:create_app --debug run
   ```

   預設會在 <http://localhost:5000> 提供服務。

## 測試

```pwsh
pytest
```

## Docker 執行

```pwsh
docker build -t learning-keywords .
docker run --rm -p 5000:5000 --env-file .env learning-keywords
```

## 專案維運與安全

- `.gitignore` 已完整覆蓋：
  - 隱藏 `.env`、`.env.*`、`.github/`、`.vscode/`、`__pycache__/`、`.pytest_cache/`、`static/uploads/`、`instance/*.db`、`instance/*.sqlite3` 等敏感或暫存檔案。
  - `.env.example` 為公開範本，實際 `.env` 不會被追蹤。
- 所有快取、資料庫檔案已從 git 追蹤移除，確保敏感資料不外洩。
- 請勿將真實 OAuth 憑證、密碼、API 金鑰等資訊提交至版本控制。

## seed.py 資料結構

- `app/seed.py` 已依據最新 `models.py` 結構重寫，支援分類、關鍵字、別名、觀看次數、YouTube 影片、狀態等欄位。
- 執行 `flask --app app:create_app seed` 可初始化測試資料。

## 依賴管理

- 依據實際 import，`pyproject.toml` 僅保留必要依賴：
  - Flask, Flask-SQLAlchemy, Flask-Migrate, Flask-WTF, Flask-Login, Authlib, requests, python-dotenv, markdown2, WTForms[email], pypinyin, email_validator
  - 開發/測試：pytest, pytest-flask, black, flake8
- 安裝方式：`pip install -e .[dev]`

## 最新維運與開發指南

- 所有舊版 docs/* 文件已刪除，統一整合於 `docs/PYTHON_MODULE_MAINTENANCE_GUIDE.md`。
- 其他功能說明請見 `docs/` 目錄下各主題文件。

## 狀態與貢獻

- 專案已完成安全性、依賴、資料結構、文檔、gitignore、敏感檔案等全面排查。
- 歡迎依照維運指南進行二次開發或部署。

## 專案結構

```
app/
  admin/            # 後台藍圖與管理頁面 (含批次操作 API)
  auth/             # Discord OAuth 流程
  main/             # 前台頁面 (含全域搜尋 API)
  templates/        # Jinja2 模板
    admin/          # 後台管理頁面
    auth/           # 登入相關頁面
    errors/         # 錯誤頁面 (403, 404, 500)
    main/           # 前台頁面
  static/           # CSS / JS 靜態資源
    css/            # 自訂樣式
    js/             # 前端 JavaScript (含全域搜尋)
  models.py         # SQLAlchemy 模型定義 (含別名、狀態、觀看次數)
  forms.py          # Flask-WTF 表單
  seed.py           # CLI 資料初始化
migrations/         # Flask-Migrate 資料庫遷移檔案
instance/
  app.db            # 預設 SQLite 資料庫位置 (於執行時建立)
```

## 部署建議

### 生產環境部署

- 以 `wsgi.py` 作為入口，搭配 Gunicorn 或其他 WSGI Server。
- 將 `SECRET_KEY`、Discord OAuth 憑證與資料庫連線字串設定於環境變數。
- 建議搭配 HTTPS 與反向代理 (如 Nginx) 提供服務。

**使用 Gunicorn：**
```bash
gunicorn -w 4 -b 0.0.0.0:5000 wsgi:app
```

### Pterodactyl 自動部署

本專案支援透過 GitHub Actions 自動部署到 Pterodactyl 伺服器：

1. **完整設定指南**：請參考 [Pterodactyl 部署指引](docs/PTERODACTYL_DEPLOYMENT_GUIDE.md)
2. **快速設定檢查清單**：參考 [部署檢查清單](docs/DEPLOYMENT_CHECKLIST.md)

**特色：**
- ✅ 推送程式碼自動部署
- ✅ 自動運行測試確保品質
- ✅ 自動 Git pull 和依賴更新
- ✅ 零停機時間部署
- ✅ 資料庫自動備份（每日 1:00 AM，保留 30 天）

**工作流程：**
```
git push origin master
    ↓
GitHub Actions 運行測試
    ↓
測試通過 → 觸發 Pterodactyl 重啟
    ↓
Pterodactyl 自動 git pull
    ↓
更新依賴並重啟應用
    ↓
✅ 部署完成！
```

## 取得 Discord OAuth 憑證

1. 前往 [Discord Developer Portal](https://discord.com/developers/applications) 建立應用程式。
2. 在 **OAuth2 → General** 設定內新增 Redirect URI，例如 `http://localhost:5000/auth/discord/callback`。
3. 取得 **Client ID** 與 **Client Secret**，填入 `.env`。

## 常見問題

- **為何登入後重新導回首頁？**
  - 未帶 `next` 參數時預設導向首頁。若需要導回後台，可連到 `/auth/login?next=%2Fadmin`。
- **團隊成員看不到導航管理？**
  - 導航、頁尾與品牌設定僅限管理員，符合需求描述。
- **如何新增更多 YouTube 影片欄位？**
  - 在新增/編輯頁面點選「新增影片欄位」，頁面會重新載入並提供新的輸入區塊。
- **如何提交 Sitemap 到搜尋引擎？**
  - 訪問 `/sitemap.xml` 查看自動生成的 sitemap,然後在 Google Search Console 或 Bing Webmaster Tools 提交此 URL。詳見 [Sitemap 功能說明](docs/SITEMAP.md)。
- **如何使用批次操作功能？**
  - 在後台關鍵字管理頁面,點選「批次操作」按鈕,選擇要操作的關鍵字,然後執行批次切換狀態、刪除或移動。
- **隱藏的分類或關鍵字會出現在前台嗎？**
  - 不會。設定為「隱藏」的分類或關鍵字僅在後台顯示,前台與 API 搜尋結果皆會過濾掉隱藏內容。
- **如何追蹤關鍵字的觀看次數？**
  - 系統會自動記錄每次有人訪問關鍵字詳細頁面的次數,在後台關鍵字列表與編輯頁面都可看到觀看統計。
- **404 頁面的搜尋功能如何運作？**
  - 404 錯誤頁面整合了全域搜尋,可以直接在錯誤頁面搜尋關鍵字,並顯示熱門分類供快速導航。

## 相關文檔

- [維運與開發指南](docs/MAINTENANCE_GUIDE.md) - 完整架構、部署與維運手冊
- [Sitemap 功能說明](docs/SITEMAP.md) - SEO 優化與搜尋引擎提交指南
- [關鍵字自動連結](docs/KEYWORD_LINKING.md) - 自動建立內部連結的知識網絡
- [行動裝置優化說明](docs/MOBILE_OPTIMIZATION.md) - 響應式體驗與設計細節

## 授權

此專案可依需求自行延伸與調整，請記得保護使用者個資與憑證安全。
