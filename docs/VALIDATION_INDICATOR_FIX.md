# 關鍵字編輯器驗證指示器修正

## 需求

在關鍵字編輯頁面（keyword_editor.html）中，調整必填欄位的視覺反饋方式：

- **初始狀態**（未提交）：隱藏綠色勾勾 → **無色**
- **提交時驗證失敗**：顯示紅色邊框 → **紅色**
- **填入後**：移除紅色邊框 → **無色**

## 問題

原先的實現會在欄位有效時立即添加 `is-valid` 類別，導致顯示綠色勾勾，這會造成視覺上的混亂。

## 解決方案

### 1. 修改 `checkRequiredFields()` 函式

**策略：** 使用 `has-submitted` 標籤來控制何時顯示紅色錯誤

**修改前：**
```javascript
// ❌ 任何時候都顯示綠色勾勾
if (isValid) {
  element.classList.remove('is-invalid');
  element.classList.add('is-valid');  // ← 無條件添加綠色
} else {
  element.classList.remove('is-valid');
  element.classList.add('is-invalid');  // ← 任何時候都顯示紅色
}
```

**修改後：**
```javascript
// ✅ 只在適當時機顯示顏色
if (isValid) {
  element.classList.remove('is-invalid');
  element.classList.remove('is-valid');  // ← 移除綠色，保持無色
} else {
  // 只有在已提交時（有 has-submitted 標籤）才顯示紅色
  if (element.closest('form')?.classList.contains('has-submitted')) {
    element.classList.add('is-invalid');
  } else {
    element.classList.remove('is-invalid');
  }
  element.classList.remove('is-valid');
}
```

### 2. 修改 `saveKeyword()` 函式

**策略：** 在提交時添加 `has-submitted` 標籤，以觸發紅色錯誤顯示

**修改前：**
```javascript
function saveKeyword() {
  if (!validateAndNavigateToMissing()) {
    showNotification('請先填寫所有必填欄位', 'warning');
    return;  // ← 此時沒有紅色指示，用戶會困惑
  }
  // ...
}
```

**修改後：**
```javascript
function saveKeyword() {
  const form = document.getElementById('keywordForm');
  if (!form) return;
  
  // ✅ 先標記表單已提交
  form.classList.add('has-submitted');
  
  // ✅ 重新檢查會觸發紅色錯誤顯示
  checkRequiredFields();
  
  if (!validateAndNavigateToMissing()) {
    showNotification('請先填寫所有必填欄位', 'warning');
    return;  // ← 現在會顯示紅色
  }
  // ...
}
```

### 3. 修改 `initKeywordEditor()` 中的表單監聽

**策略：** 當用戶修改表單後，移除 `has-submitted` 標籤，返回無色狀態

**修改前：**
```javascript
form.addEventListener('change', function() {
  formChanged = true;
  checkRequiredFields();  // ← 但仍保持已提交狀態
});
```

**修改後：**
```javascript
form.addEventListener('change', function() {
  formChanged = true;
  // ✅ 用戶開始修改後，返回無色狀態
  form.classList.remove('has-submitted');
  checkRequiredFields();
});
```

## 行為流程

```
初始狀態
├─ 欄位：無色（無 is-valid 也無 is-invalid）
├─ 別名：「此分頁含必填欄位」紅色徽章隱藏
└─ 警告：「必填欄位提示」隱藏

│
↓ 用戶點擊「儲存」

驗證檢查 (form.classList.add('has-submitted'))
├─ 缺失欄位 → 顯示紅色邊框（is-invalid）
├─ 導航徽章 → 顯示紅色「此分頁含必填欄位」
├─ 警告框 → 顯示「必填欄位提示」
└─ 通知 → 顯示「請先填寫所有必填欄位」

│
↓ 用戶開始填入欄位（form.classList.remove('has-submitted'))

即時反饋
├─ 已填欄位 → 移除紅色，顯示無色
├─ 導航徽章 → 如果該分頁所有欄位都已填，隱藏徽章
└─ 警告框 → 如果所有欄位都已填，隱藏警告

│
↓ 用戶再次點擊「儲存」

驗證成功 → 提交表單
```

## 修改的檔案

- **app/static/js/keyword-editor.js**
  - Line 97-130: 修改 `checkRequiredFields()` 函式
  - Line 71-89: 修改 `initKeywordEditor()` 中的表單監聽
  - Line 567-591: 修改 `saveKeyword()` 函式

## 測試清單

- [ ] 進入編輯頁面，欄位顯示為無色（無綠色勾勾）
- [ ] 不填寫任何欄位，直接點擊「儲存」
  - [ ] 欄位顯示紅色邊框
  - [ ] 導航項上顯示紅色「此分頁含必填欄位」徽章
  - [ ] 頁面頂部顯示「必填欄位提示」警告框
- [ ] 在紅色狀態下，開始填寫欄位
  - [ ] 填寫欄位後紅色應消失，回到無色
  - [ ] 如果所有必填欄位都已填，紅色徽章應隱藏
- [ ] 檢查其他欄位（非必填）保持無色
- [ ] 成功填寫所有必填欄位後，「儲存」應正常提交

## 相關 CSS 類別

- **`is-valid`**：Bootstrap 的綠色驗證狀態（已移除使用）
- **`is-invalid`**：Bootstrap 的紅色驗證狀態（只在 has-submitted 時添加）
- **`has-submitted`**：自訂標籤，標記表單已提交過驗證檢查

## 備註

此修正保持與 Bootstrap 5 的驗證 API 相容，同時提供更友好的使用體驗：
- 用戶在編輯頁面時不會被立即的驗證狀態打擾
- 只有在明確嘗試提交時才會獲得驗證反饋
- 填寫欄位後立即得到正反饋（移除紅色）
