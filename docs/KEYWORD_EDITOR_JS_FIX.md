"""Test the keyword editor (marked.js) table rendering fix."""

# 這個檔案記錄了 keyword-editor.js 中 marked.js renderer 的修正

## 問題描述

在使用 marked.js 渲染 Markdown 表格時，自訂的 renderer 函式會拋出錯誤：

```
TypeError: Cannot read properties of undefined (reading 'header')
    at renderer.tablerow (keyword-editor.js:368:27)
```

## 原因

marked.js 的 renderer API 中，`tablerow` 和 `tablecell` 函式接收的 `flags` 參數
在某些情況下可能是 `undefined` 或不包含預期的屬性。這取決於 marked.js 的版本。

## 修正方案

在 `app/static/js/keyword-editor.js` 中，為所有訪問 `flags` 屬性的地方加入防禦性檢查：

### 修改前（會產生錯誤）

```javascript
renderer.tablerow = function(content, flags) {
  const style = flags.header ? 'background: #667eea; ...' : 'background: #f8f9fa;';
  return `<tr style="${style}">${content}</tr>\n`;
};

renderer.tablecell = function(content, flags) {
  const align = flags.align ? `text-align: ${flags.align};` : 'text-align: left;';
  const style = flags.header ? '...' : '...';
  const tag = flags.header ? 'th' : 'td';
  return `<${tag} style="${style}">${content}</${tag}>`;
};
```

### 修改後（安全且穩定）

```javascript
renderer.tablerow = function(content, flags) {
  // 防禦性檢查：flags 可能是 undefined
  const isHeader = flags && flags.header === true;
  const style = isHeader ? 'background: #667eea; ...' : 'background: #f8f9fa;';
  return `<tr style="${style}">${content}</tr>\n`;
};

renderer.tablecell = function(content, flags) {
  // 安全地訪問可能不存在的屬性
  const align = (flags && flags.align) ? `text-align: ${flags.align};` : 'text-align: left;';
  const isHeader = flags && flags.header === true;
  const style = isHeader ? '...' : '...';
  const tag = isHeader ? 'th' : 'td';
  return `<${tag} style="${style}">${content}</${tag}>`;
};
```

## 驗證方式

### 手動測試步驟

1. 登入管理介面
2. 進入「內容管理器」(`/admin/content-manager`)
3. 選擇任一關鍵字進入編輯模式（使用 keyword_editor.html）
4. 在 Markdown 編輯區輸入表格：

```markdown
| 欄位 1 | 欄位 2 | 欄位 3 |
| ------ | ------ | ------ |
| 資料 A | 資料 B | 資料 C |
| 資料 D | 資料 E | 資料 F |
```

5. 點擊「並排預覽」按鈕
6. **預期結果：**
   - ✅ 預覽區正確顯示表格
   - ✅ Console 沒有 TypeError 錯誤
   - ✅ 表頭有紫色背景 (#667eea)
   - ✅ 表格內容有灰色背景 (#f8f9fa)

### 瀏覽器 Console 檢查

**修正前（錯誤）：**
```
❌ Markdown 解析錯誤: TypeError: Cannot read properties of undefined (reading 'header')
   at renderer.tablerow (keyword-editor.js:368:27)
```

**修正後（正常）：**
```
✅ 無錯誤訊息
✅ 表格正確渲染
```

## 影響範圍

此修正僅影響使用 `keyword-editor.js` 的頁面：
- `/admin/keywords/create` - 新增關鍵字（編輯器模式）
- `/admin/keywords/<id>/editor` - 編輯關鍵字（編輯器模式）

**不影響：**
- `keyword_form.html`（使用 EasyMDE，已透過後端 API 修正）
- 前台關鍵字頁面（已在 `app/main/routes.py` 修正）

## 相關技術說明

### marked.js Renderer API

marked.js 的 renderer 函式簽章：

```typescript
// marked.js v4+ 的 API
interface Renderer {
  tablerow(content: string, flags: { header: boolean }): string;
  tablecell(content: string, flags: { 
    header: boolean;
    align: 'center' | 'left' | 'right' | null;
  }): string;
}
```

但實際使用時，`flags` 可能：
1. 是 `undefined`（某些 marked.js 版本）
2. 缺少某些屬性（不同的渲染上下文）
3. 結構不同（API 變更）

因此，**防禦性編程**是必要的：

```javascript
// ❌ 假設 flags 總是存在且包含所需屬性
const isHeader = flags.header;

// ✅ 安全檢查
const isHeader = flags && flags.header === true;

// ✅ 使用可選鏈（如果支援 ES2020+）
const isHeader = flags?.header === true;
```

## 替代方案（未採用）

### 方案 A：升級 marked.js 到最新版本
- **優點：** 可能有更穩定的 API
- **缺點：** 可能引入 breaking changes，需要大量測試

### 方案 B：完全移除自訂 renderer
- **優點：** 減少維護負擔
- **缺點：** 失去自訂樣式，表格不夠美觀

### 方案 C：改用後端 API 渲染（類似 EasyMDE）
- **優點：** 與前台完全一致
- **缺點：** 增加網路請求，可能影響即時預覽體驗

**最終選擇：** 保留自訂 renderer，加入防禦性檢查（本次修正）
- ✅ 最小改動
- ✅ 保留美觀的表格樣式
- ✅ 向後相容
- ✅ 不影響效能

## 檔案變更

- **修改：** `app/static/js/keyword-editor.js`
  - Line 367-380: 修改 `renderer.tablerow` 和 `renderer.tablecell`
  
## 測試清單

- [x] 修改 keyword-editor.js 加入防禦性檢查
- [x] 更新技術文件 (MARKDOWN_PREVIEW_FIX.md)
- [ ] 手動測試：在編輯器中輸入表格並預覽
- [ ] 手動測試：確認 Console 無錯誤
- [ ] 手動測試：表格樣式正確顯示
- [ ] 回歸測試：其他 Markdown 語法（標題、清單、程式碼等）
