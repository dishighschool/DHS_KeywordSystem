# Icon Picker 和網站設定修正測試指南

## 已修正的問題

### 1. 表單欄位互相覆蓋問題 ✅
**問題描述：**
- 三個分頁（基本設定、頁首設定、頁尾設定）使用同一個表單
- 當提交某個分頁的表單時，其他分頁的空欄位會覆蓋原有資料

**修正方法：**
- 在每個表單中添加隱藏欄位 `form_section`，標識當前提交的是哪個分頁
- 修改後端 `update_site_settings()` 函式，根據 `form_section` 只更新對應的欄位
- 基本設定只更新：`site_title`, `site_subtitle`, `site_title_suffix`, `footer_title`
- 頁首設定只更新：`header_logo_file/url`, `favicon_file`
- 頁尾設定只更新：`footer_logo_file/url`, `footer_description`, `footer_copy`

### 2. Icon Picker 未正確初始化問題 ✅
**問題描述：**
- Icon Picker 的 JavaScript 未正確載入或初始化
- 使用了錯誤的初始化方式

**修正方法：**
- 確保 `icon-picker.css` 和 `icon-picker.js` 都正確載入
- 使用 `new IconPicker(element, options)` 而不是 `window.initIconPicker(element, options)`
- 添加重複初始化檢查，避免在 Modal 中重複創建 Icon Picker

## 測試步驟

### 測試 1：網站設定表單不互相覆蓋

1. 啟動 Flask 應用程式
   ```powershell
   .\.venv\Scripts\Activate.ps1
   flask --app app:create_app --debug run
   ```

2. 登入管理後台並進入「網站設定」頁面

3. **測試基本設定分頁：**
   - 填寫「網站標題」為 "測試標題"
   - 填寫「網站副標題」為 "測試副標題"
   - 點擊「儲存設定」
   - 切換到「頁首設定」分頁，確認導航連結還在
   - 回到「基本設定」，確認剛才填寫的標題仍然存在

4. **測試頁首設定分頁：**
   - 切換到「頁首設定」分頁
   - 上傳一個頁首 Logo 圖片
   - 點擊「儲存設定」
   - 回到「基本設定」分頁，確認網站標題沒有被清空 ✅

5. **測試頁尾設定分頁：**
   - 切換到「頁尾設定」分頁
   - 填寫「頁尾說明文字」
   - 點擊「儲存設定」
   - 回到「基本設定」和「頁首設定」，確認資料沒有被清空 ✅

### 測試 2：Icon Picker 正常運作

1. **在網站設定頁面測試：**
   - 點擊「新增導航連結」按鈕
   - 在「圖示」欄位旁應該會出現一個可點擊的按鈕/區域
   - 點擊圖示欄位，應該會彈出圖示選擇器 ✅
   - 搜尋 "house" 並選擇一個圖示
   - 確認選擇的圖示顯示在輸入框中

2. **在公告橫幅頁面測試：**
   - 進入「公告橫幅管理」頁面
   - 在「新增公告橫幅」表單中點擊「圖示」欄位
   - 應該會出現圖示選擇器 ✅
   - 選擇一個圖示，確認輸入框更新

3. **測試編輯功能：**
   - 點擊現有導航連結或公告的「編輯」按鈕
   - 在編輯 Modal 中的圖示欄位應該也能正常使用 Icon Picker ✅

## 預期結果

✅ 表單分頁之間不會互相覆蓋資料
✅ Icon Picker 在所有頁面正常顯示和運作
✅ 可以搜尋並選擇 Bootstrap Icons
✅ 選擇的圖示正確顯示在輸入框中
✅ Modal 中的 Icon Picker 也能正常運作

## 如果仍有問題

1. **檢查瀏覽器控制台：**
   - 按 F12 打開開發者工具
   - 查看 Console 標籤是否有 JavaScript 錯誤
   - 查看 Network 標籤確認 `icon-picker.js` 和 `icon-picker.css` 已載入

2. **清除瀏覽器快取：**
   - 按 Ctrl+Shift+Delete 清除快取
   - 或按 Ctrl+F5 強制重新載入頁面

3. **檢查檔案路徑：**
   - 確認 `app/static/js/icon-picker.js` 存在
   - 確認 `app/static/css/icon-picker.css` 存在

## 修正的檔案清單

1. `app/templates/admin/site_settings.html` - 添加 form_section 隱藏欄位，修正 Icon Picker 初始化
2. `app/templates/admin/announcements.html` - 修正 Icon Picker 初始化和整合
3. `app/admin/routes.py` - 修改 `update_site_settings()` 函式，根據分頁區段更新資料

## 技術細節

### Icon Picker 初始化方式
```javascript
// ❌ 錯誤的方式
window.initIconPicker(input, options);  // input 是元素，但 initIconPicker 期望選擇器字串

// ✅ 正確的方式
new IconPicker(input, options);  // 直接使用 IconPicker 類別
```

### 表單區段識別
```html
<!-- 每個表單都有獨立的 form_section 標識 -->
<input type="hidden" name="form_section" value="basic">
<input type="hidden" name="form_section" value="header">
<input type="hidden" name="form_section" value="footer">
```

### 後端條件更新
```python
form_section = request.form.get('form_section', 'basic')

if form_section == 'basic':
    # 只更新基本設定欄位
elif form_section == 'header':
    # 只更新頁首相關欄位
elif form_section == 'footer':
    # 只更新頁尾相關欄位
```
