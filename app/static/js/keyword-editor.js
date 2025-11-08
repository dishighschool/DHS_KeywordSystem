let formChanged = false;

function initKeywordEditor() {
  const navItems = document.querySelectorAll('.editor-nav-item');
  const sections = document.querySelectorAll('.editor-section');

  navItems.forEach(item => {
    item.addEventListener('click', function(e) {
      e.preventDefault();
      
      const targetSection = this.dataset.section;
      
      navItems.forEach(nav => nav.classList.remove('active'));
      this.classList.add('active');
      
      sections.forEach(section => {
        if (section.id === `section-${targetSection}`) {
          section.classList.add('active');
          document.querySelector('.editor-content').scrollTop = 0;
        } else {
          section.classList.remove('active');
        }
      });
      
      window.location.hash = targetSection;
    });
  });

  const hash = window.location.hash.substring(1);
  if (hash) {
    const targetNav = document.querySelector(`[data-section="${hash}"]`);
    if (targetNav) {
      targetNav.click();
    }
  }

  initMarkdownEditor();

  const form = document.getElementById('keywordForm');
  if (form) {
    form.addEventListener('change', function() {
      formChanged = true;
    });
    
    form.addEventListener('input', function() {
      formChanged = true;
    });

    window.addEventListener('beforeunload', function(e) {
      if (formChanged) {
        e.preventDefault();
        e.returnValue = '';
        return '';
      }
    });
  }
}

function initMarkdownEditor() {
  const textarea = document.getElementById('description_markdown');
  const container = document.getElementById('markdown-container');
  const previewContent = document.querySelector('.preview-content');
  
  if (!textarea || !container || !previewContent) return;

  if (typeof marked !== 'undefined') {
    marked.setOptions({
      breaks: true,
      gfm: true,
      headerIds: true,
      mangle: false
    });
  }

  const modeEdit = document.getElementById('mode-edit');
  const modeSplit = document.getElementById('mode-split');
  const modePreview = document.getElementById('mode-preview');

  if (modeEdit) {
    modeEdit.addEventListener('change', function() {
      if (this.checked) {
        container.classList.remove('split-mode', 'preview-mode');
      }
    });
  }

  if (modeSplit) {
    modeSplit.addEventListener('change', function() {
      if (this.checked) {
        container.classList.add('split-mode');
        container.classList.remove('preview-mode');
        updatePreview();
      }
    });
  }

  if (modePreview) {
    modePreview.addEventListener('change', function() {
      if (this.checked) {
        container.classList.add('preview-mode');
        container.classList.remove('split-mode');
        updatePreview();
      }
    });
  }

  let updateTimer;
  textarea.addEventListener('input', function() {
    clearTimeout(updateTimer);
    updateTimer = setTimeout(() => {
      updatePreview();
      updateStats();
    }, 300);
  });

  updatePreview();
  updateStats();

  function updatePreview() {
    if (!container.classList.contains('split-mode') && 
        !container.classList.contains('preview-mode')) {
      return;
    }

    const markdown = textarea.value;
    if (typeof marked !== 'undefined') {
      previewContent.innerHTML = marked.parse(markdown);
    } else {
      previewContent.innerHTML = '<p class="text-muted">載入 Markdown 解析器中...</p>';
    }
  }

  function updateStats() {
    const text = textarea.value;
    const charCount = text.length;
    const wordCount = text.trim() ? text.trim().split(/\s+/).length : 0;
    const lineCount = text.split('\n').length;

    const charElement = document.getElementById('char-count');
    const wordElement = document.getElementById('word-count');
    const lineElement = document.getElementById('line-count');

    if (charElement) charElement.textContent = charCount;
    if (wordElement) wordElement.textContent = wordCount;
    if (lineElement) lineElement.textContent = lineCount;
  }

  textarea.addEventListener('keydown', function(e) {
    if (e.key === 'Tab') {
      e.preventDefault();
      const start = this.selectionStart;
      const end = this.selectionEnd;
      const value = this.value;
      
      this.value = value.substring(0, start) + '  ' + value.substring(end);
      this.selectionStart = this.selectionEnd = start + 2;
      
      this.dispatchEvent(new Event('input'));
    }
  });

  textarea.addEventListener('scroll', function() {
    if (container.classList.contains('split-mode')) {
      const previewPane = document.querySelector('.markdown-preview-pane');
      if (previewPane) {
        const scrollPercentage = this.scrollTop / (this.scrollHeight - this.clientHeight);
        previewPane.scrollTop = scrollPercentage * (previewPane.scrollHeight - previewPane.clientHeight);
      }
    }
  });
}

function saveKeyword() {
  const form = document.getElementById('keywordForm');
  if (!form) return;

  if (!form.checkValidity()) {
    form.reportValidity();
    return;
  }

  formChanged = false;

  showLoadingOverlay('正在儲存...');

  form.submit();
}

function addVideoEntry() {
  const container = document.getElementById('videos-container');
  const entries = container.querySelectorAll('.video-entry');
  const newIndex = entries.length;

  const videoHTML = `
    <div class="video-entry card mb-3">
      <div class="card-body">
        <div class="d-flex justify-content-between align-items-start mb-3">
          <h5 class="card-title mb-0">影片 #${newIndex + 1}</h5>
          <button type="button" class="btn btn-sm btn-outline-danger" onclick="removeVideoEntry(this)">
            <i class="bi bi-trash"></i>
          </button>
        </div>
        <div class="row g-3">
          <div class="col-md-6">
            <label class="form-label">YouTube 網址</label>
            <input type="text" name="videos-${newIndex}-url" class="form-control" placeholder="https://www.youtube.com/watch?v=...">
          </div>
          <div class="col-md-6">
            <label class="form-label">影片標題</label>
            <input type="text" name="videos-${newIndex}-title" class="form-control" placeholder="影片標題">
          </div>
        </div>
      </div>
    </div>
  `;

  container.insertAdjacentHTML('beforeend', videoHTML);
  
  const newEntry = container.lastElementChild;
  newEntry.style.opacity = '0';
  newEntry.style.transform = 'translateY(-10px)';
  setTimeout(() => {
    newEntry.style.transition = 'all 0.3s ease';
    newEntry.style.opacity = '1';
    newEntry.style.transform = 'translateY(0)';
  }, 10);
}

function removeVideoEntry(button) {
  const entry = button.closest('.video-entry');
  if (!entry) return;

  if (confirm('確定要移除這個影片嗎?')) {
    entry.style.transition = 'all 0.3s ease';
    entry.style.opacity = '0';
    entry.style.transform = 'translateX(-20px)';
    setTimeout(() => {
      entry.remove();
      updateVideoNumbers();
    }, 300);
  }
}

function updateVideoNumbers() {
  const entries = document.querySelectorAll('.video-entry');
  entries.forEach((entry, index) => {
    const title = entry.querySelector('.card-title');
    if (title) {
      title.textContent = `影片 #${index + 1}`;
    }
  });
}

function addAliasEntry() {
  const container = document.getElementById('aliases-container');
  const entries = container.querySelectorAll('.alias-entry');
  const newIndex = entries.length;

  const aliasHTML = `
    <div class="alias-entry mb-2">
      <input type="hidden" name="aliases-${newIndex}-alias_id" value="">
      <div class="input-group">
        <input type="text" name="aliases-${newIndex}-title" class="form-control" placeholder="輸入別名">
        <button type="button" class="btn btn-outline-danger" onclick="removeAliasEntry(this)">
          <i class="bi bi-x-lg"></i>
        </button>
      </div>
    </div>
  `;

  container.insertAdjacentHTML('beforeend', aliasHTML);
  
  const newInput = container.lastElementChild.querySelector('input[type="text"]');
  if (newInput) {
    newInput.focus();
  }
}

function removeAliasEntry(button) {
  const entry = button.closest('.alias-entry');
  if (!entry) return;

  entry.style.transition = 'all 0.2s ease';
  entry.style.opacity = '0';
  entry.style.transform = 'translateX(-10px)';
  setTimeout(() => {
    entry.remove();
  }, 200);
}

function insertMarkdown(prefix, suffix) {
  const textarea = document.getElementById('description_markdown');
  if (!textarea) return;

  const start = textarea.selectionStart;
  const end = textarea.selectionEnd;
  const selectedText = textarea.value.substring(start, end);
  const beforeText = textarea.value.substring(0, start);
  const afterText = textarea.value.substring(end);

  const newText = beforeText + prefix + selectedText + suffix + afterText;
  textarea.value = newText;

  const newCursorPos = start + prefix.length + selectedText.length;
  textarea.setSelectionRange(newCursorPos, newCursorPos);
  textarea.focus();
  
  textarea.dispatchEvent(new Event('input'));
}

function insertTable() {
  const tableMarkdown = `
| 標題1 | 標題2 | 標題3 |
| ----- | ----- | ----- |
| 內容1 | 內容2 | 內容3 |
| 內容4 | 內容5 | 內容6 |
`;
  
  const textarea = document.getElementById('description_markdown');
  if (!textarea) return;

  const start = textarea.selectionStart;
  const beforeText = textarea.value.substring(0, start);
  const afterText = textarea.value.substring(start);

  textarea.value = beforeText + tableMarkdown + afterText;
  textarea.setSelectionRange(start, start + tableMarkdown.length);
  textarea.focus();
  
  textarea.dispatchEvent(new Event('input'));
}

function regenerateSEO() {
  const isCreating = window.location.pathname.includes('/create');
  
  if (isCreating) {
    showNotification('請先儲存關鍵字後再生成 SEO 內容', 'warning');
    return;
  }
  
  if (!confirm('確定要重新生成 SEO 內容嗎?這將覆蓋現有的自訂內容。')) {
    return;
  }

  showLoadingOverlay('正在生成 SEO 內容...');

  const keywordId = window.location.pathname.split('/').filter(Boolean).pop();
  
  fetch(`/admin/keywords/${keywordId}/regenerate-seo`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': document.querySelector('meta[name="csrf-token"]')?.content || ''
    }
  })
  .then(response => response.json())
  .then(data => {
    hideLoadingOverlay();
    if (data.success) {
      const seoContent = document.getElementById('seo_content');
      if (seoContent && data.seo_content) {
        seoContent.value = data.seo_content;
      }
      
      const autoGenerate = document.getElementById('seo_auto_generate');
      if (autoGenerate) {
        autoGenerate.checked = true;
        autoGenerate.dispatchEvent(new Event('change'));
      }
      
      showNotification('SEO 內容已重新生成', 'success');
    } else {
      showNotification(data.message || '生成失敗', 'error');
    }
  })
  .catch(error => {
    hideLoadingOverlay();
    console.error('Error:', error);
    showNotification('生成 SEO 內容時發生錯誤', 'error');
  });
}

function showLoadingOverlay(message = '載入中...') {
  let overlay = document.querySelector('.loading-overlay');
  if (!overlay) {
    overlay = document.createElement('div');
    overlay.className = 'loading-overlay';
    overlay.innerHTML = `
      <div class="text-center">
        <div class="loading-spinner mx-auto mb-3"></div>
        <p class="loading-message text-muted">${message}</p>
      </div>
    `;
    document.body.appendChild(overlay);
  } else {
    const messageEl = overlay.querySelector('.loading-message');
    if (messageEl) {
      messageEl.textContent = message;
    }
    overlay.style.display = 'flex';
  }
}

function hideLoadingOverlay() {
  const overlay = document.querySelector('.loading-overlay');
  if (overlay) {
    overlay.style.display = 'none';
  }
}

function showNotification(message, type = 'info') {
  const alertClass = {
    'success': 'alert-success',
    'error': 'alert-danger',
    'warning': 'alert-warning',
    'info': 'alert-info'
  }[type] || 'alert-info';

  const notification = document.createElement('div');
  notification.className = `alert ${alertClass} alert-dismissible fade show`;
  notification.style.position = 'fixed';
  notification.style.top = '20px';
  notification.style.right = '20px';
  notification.style.zIndex = '10000';
  notification.style.minWidth = '300px';
  notification.innerHTML = `
    ${message}
    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
  `;

  document.body.appendChild(notification);

  setTimeout(() => {
    notification.classList.remove('show');
    setTimeout(() => notification.remove(), 300);
  }, 3000);
}

document.addEventListener('keydown', function(e) {
  if ((e.ctrlKey || e.metaKey) && e.key === 's') {
    e.preventDefault();
    saveKeyword();
  }

  if (e.key === 'Escape') {
    const backButton = document.querySelector('.btn-back');
    if (backButton) {
      if (formChanged) {
        if (confirm('確定要離開編輯頁面嗎?未儲存的變更將會遺失。')) {
          formChanged = false;
          backButton.click();
        }
      } else {
        backButton.click();
      }
    }
  }
});

let autoSaveTimer;
function enableAutoSave() {
  const form = document.getElementById('keywordForm');
  if (!form) return;

  form.addEventListener('input', function() {
    clearTimeout(autoSaveTimer);
    autoSaveTimer = setTimeout(() => {
      saveDraft();
    }, 30000);
  });
}

function saveDraft() {
  const form = document.getElementById('keywordForm');
  if (!form) return;

  const formData = new FormData(form);
  const keywordId = window.location.pathname.split('/').filter(Boolean).pop();

  fetch(`/admin/keywords/${keywordId}/save-draft`, {
    method: 'POST',
    headers: {
      'X-CSRFToken': document.querySelector('meta[name="csrf-token"]')?.content || ''
    },
    body: formData
  })
  .then(response => response.json())
  .then(data => {
    if (data.success) {
    }
  })
  .catch(error => {
    console.error('自動儲存失敗:', error);
  });
}

window.keywordEditor = {
  init: initKeywordEditor,
  save: saveKeyword,
  addVideo: addVideoEntry,
  removeVideo: removeVideoEntry,
  addAlias: addAliasEntry,
  removeAlias: removeAliasEntry,
  insertMarkdown: insertMarkdown,
  regenerateSEO: regenerateSEO
};
