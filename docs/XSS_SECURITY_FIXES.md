# XSS 安全性修復文檔

## 問題描述
關鍵字編輯頁面 (`keyword_editor.html`) 的 Markdown 預覽功能存在 XSS (跨網站指令碼) 注入漏洞。

### 原始問題
在 `keyword-editor.js` 中，使用了以下不安全的方式來設置預覽內容：
```javascript
// ❌ 不安全 - 直接使用 innerHTML
previewContent.innerHTML = marked.parse(markdown);
```

這會導致用戶在 Markdown 中輸入的 JavaScript 代碼被執行，例如：
```markdown
<img src=x onerror="alert('XSS')">
<script>alert('XSS')</script>
```

## 修復方案

### 1. 前端 JavaScript 安全性改進

#### a. 引入 DOMPurify 庫
在 `keyword_editor.html` 中添加了 DOMPurify 庫：
```html
<script src="https://cdn.jsdelivr.net/npm/dompurify@3.0.6/dist/purify.min.js"></script>
```

DOMPurify 是業界標準的 XSS 防護庫，能夠：
- 移除所有危險的 HTML 標籤和屬性
- 防止 JavaScript 注入
- 保留安全的內容格式

#### b. 自訂 Marked 渲染器
配置了 `marked` 庫的自訂 renderer 來增加額外的安全性：

```javascript
const renderer = new marked.Renderer();

// 禁止渲染原始 HTML
renderer.html = function(text) {
  return '<p class="text-danger"><small>[HTML 標籤已被移除以確保安全]</small></p>';
};

// 驗證圖片 URL 安全性
renderer.image = function(href, title, text) {
  if (!href || !isValidImageUrl(href)) return '';
  return `<img src="${escapeHtml(href)}" alt="${escapeHtml(text)}" loading="lazy">`;
};

// 驗證連結 URL 安全性
renderer.link = function(href, title, text) {
  if (!href || !isValidUrl(href)) return text;
  return `<a href="${escapeHtml(href)}" target="_blank" rel="noopener noreferrer">${escapeHtml(text)}</a>`;
};
```

#### c. 安全的預覽更新
```javascript
function updatePreview() {
  const html = marked.parse(markdown);
  
  if (typeof DOMPurify !== 'undefined') {
    // 使用 DOMPurify 清理 HTML
    previewContent.innerHTML = DOMPurify.sanitize(html, {
      ALLOWED_TAGS: ['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'br', 'strong', 
                     'em', 'u', 'del', 'code', 'pre', 'ol', 'ul', 'li', 
                     'blockquote', 'a', 'img', 'table', 'thead', 'tbody', 
                     'tr', 'th', 'td', 'hr', 'span'],
      ALLOWED_ATTR: ['href', 'title', 'alt', 'src', 'loading', 'style', 
                     'target', 'rel'],
      ALLOW_DATA_ATTR: false
    });
  } else {
    // 備用方案:使用手動清理
    sanitizeAndSetContent(previewContent, html);
  }
}
```

#### d. 輔助安全函數
- `escapeHtml()`: 轉義 HTML 特殊字符
- `isValidUrl()`: 驗證 URL 協議 (http, https, mailto)
- `isValidImageUrl()`: 驗證圖片 URL,防止 javascript: 協議
- `sanitizeAndSetContent()`: 手動清理元素的備用方案
- `cleanElement()`: 遞歸清理所有不安全的標籤和屬性

### 2. 後端安全性確認

後端已正確使用 `markdown2` 庫的安全模式：
```python
html_description = markdown(
  keyword.description_markdown, 
  extras=["fenced-code-blocks"], 
  safe_mode="escape"  # ✅ 啟用安全模式
)
```

`safe_mode="escape"` 會將所有 HTML 標籤轉義為實體符號,防止執行。

## 安全測試清單

### ✅ 已測試的 XSS 攻擊向量

1. **直接 Script 標籤**
   ```markdown
   <script>alert('XSS')</script>
   ```
   ✅ 被阻止

2. **事件處理器注入**
   ```markdown
   <img src=x onerror="alert('XSS')">
   ```
   ✅ 被阻止

3. **JavaScript 協議**
   ```markdown
   <a href="javascript:alert('XSS')">Click</a>
   ```
   ✅ 被阻止

4. **Data URL 攻擊**
   ```markdown
   <img src="data:text/html,<script>alert('XSS')</script>">
   ```
   ✅ 被阻止

5. **SVG 中的 Script**
   ```markdown
   <svg onload="alert('XSS')"></svg>
   ```
   ✅ 被阻止

6. **動態生成的屬性**
   ```markdown
   <div onclick="alert('XSS')">Click</div>
   ```
   ✅ 被阻止

## 使用者影響

### 允許的功能
- 基本 Markdown 格式 (標題、粗體、斜體等)
- 代碼塊和行內代碼
- 表格
- 列表 (有序和無序)
- 引用塊
- 圖片 (使用安全的 HTTP/HTTPS URL)
- 超連結 (使用安全的 HTTP/HTTPS/mailto)

### 限制的功能
- 不支援嵌入原始 HTML
- 不支援 JavaScript 協議連結
- 不支援不安全的數據 URL

## 維護建議

1. **定期更新依賴**
   - 定期更新 `marked` 和 `dompurify` 庫
   - 檢查安全更新

2. **監控和日誌**
   - 記錄被阻止的 HTML 標籤嘗試
   - 設置安全告警

3. **使用者教育**
   - 說明不支援嵌入 HTML
   - 提供安全的 Markdown 語法指南

## 參考資源

- [OWASP XSS 防護備忘單](https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html)
- [DOMPurify 官方文檔](https://github.com/cure53/DOMPurify)
- [Marked.js 官方文檔](https://marked.js.org/)
- [markdown2 安全模式](https://github.com/trentm/python-markdown2)

## 修改文件清單

1. ✅ `app/static/js/keyword-editor.js` - 增強安全性
2. ✅ `app/templates/admin/keyword_editor.html` - 添加 DOMPurify 庫
3. 📄 `docs/XSS_SECURITY_FIXES.md` - 本文檔

## 版本記錄

- **v1.0** (2025-11-09)
  - 初始安全性修復
  - 添加 DOMPurify 集成
  - 實現自訂 Markdown 渲染器
  - 添加 URL 驗證函數
