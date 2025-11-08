(function() {
  'use strict';
  
  const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
  let batchModeActive = false;
  
  
  document.addEventListener('DOMContentLoaded', function() {
    initializeCollapsibleCategories();
    initializeSortable();
    initializeFilters();
    initializeSearch();
    initializeBatchMode();
    initializeCategoryModal();
    
    document.body.classList.add('view-mode-compact');
  });
  
  
  function initializeCollapsibleCategories() {
  }
  
  window.toggleCategoryContent = function(categoryId) {
    const content = document.getElementById(`category-content-${categoryId}`);
    const chevron = document.getElementById(`chevron-${categoryId}`);
    
    if (!content || !chevron) return;
    
    const isExpanded = content.style.display !== 'none';
    
    if (isExpanded) {
      content.style.display = 'none';
      chevron.classList.remove('bi-chevron-down');
      chevron.classList.add('bi-chevron-right');
      removeExpandedCategory(categoryId);
    } else {
      content.style.display = 'block';
      chevron.classList.add('bi-chevron-down');
      chevron.classList.remove('bi-chevron-right');
      addExpandedCategory(categoryId);
    }
  };
  
  function addExpandedCategory(categoryId) {
    const expanded = JSON.parse(localStorage.getItem('expandedCategories') || '[]');
    if (!expanded.includes(categoryId)) {
      expanded.push(categoryId);
      localStorage.setItem('expandedCategories', JSON.stringify(expanded));
    }
  }
  
  function removeExpandedCategory(categoryId) {
    let expanded = JSON.parse(localStorage.getItem('expandedCategories') || '[]');
    expanded = expanded.filter(id => id !== categoryId);
    localStorage.setItem('expandedCategories', JSON.stringify(expanded));
  }
  
  
  function initializeSortable() {
    if (!window.userIsAdmin) {
      return;
    }
    
    const contentMain = document.getElementById('contentManagerMain');
    if (contentMain) {
      new Sortable(contentMain, {
        animation: 150,
        handle: '.drag-handle-category',
        ghostClass: 'sortable-ghost',
        dragClass: 'sortable-drag',
        onEnd: function(evt) {
          updateCategoryOrder();
        }
      });
    }
    
    document.querySelectorAll('.sortable-keywords').forEach(list => {
      new Sortable(list, {
        group: 'keywords',
        animation: 150,
        handle: '.drag-handle',
        ghostClass: 'sortable-ghost',
        dragClass: 'sortable-drag',
        onEnd: function(evt) {
          handleKeywordMove(evt);
        }
      });
    });
    
    document.querySelectorAll('.category-header').forEach(header => {
      header.addEventListener('dragenter', handleCategoryDragEnter);
      header.addEventListener('dragleave', handleCategoryDragLeave);
      header.addEventListener('drop', handleCategoryDrop);
      header.addEventListener('dragover', function(e) {
        e.preventDefault();
      });
    });
  }
  
  function updateCategoryOrder() {
    const sections = document.querySelectorAll('.category-section');
    const order = Array.from(sections).map(section => 
      parseInt(section.dataset.categoryId)
    );
    
    fetch('/admin/api/reorder-categories', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRF-Token': csrfToken
      },
      body: JSON.stringify({ order: order })
    })
    .then(response => response.json())
    .then(data => {
      if (data.success) {
        showToast('分類順序已更新', 'success');
      } else {
        showToast('更新失敗: ' + data.message, 'danger');
      }
    })
    .catch(error => {
      console.error('Error:', error);
      showToast('更新失敗', 'danger');
    });
  }
  
  function handleKeywordMove(evt) {
    const fromCategoryId = evt.from.dataset.categoryId;
    const toCategoryId = evt.to.dataset.categoryId;
    const keywordId = parseInt(evt.item.dataset.keywordId);
    
    if (fromCategoryId !== toCategoryId) {
      moveKeyword(keywordId, parseInt(toCategoryId), evt);
    } else {
      updateKeywordOrder(evt.to);
    }
  }
  
  let draggedKeywordId = null;
  
  document.addEventListener('dragstart', function(e) {
    if (e.target.classList.contains('keyword-row')) {
      draggedKeywordId = parseInt(e.target.dataset.keywordId);
    }
  });
  
  function handleCategoryDragEnter(e) {
    if (!draggedKeywordId) return;
    e.preventDefault();
    const section = this.closest('.category-section');
    if (section) {
      section.classList.add('drag-over');
      this.classList.add('drag-target');
    }
  }
  
  function handleCategoryDragLeave(e) {
    if (!draggedKeywordId) return;
    const section = this.closest('.category-section');
    if (section && !section.contains(e.relatedTarget)) {
      section.classList.remove('drag-over');
      this.classList.remove('drag-target');
    }
  }
  
  function handleCategoryDrop(e) {
    e.preventDefault();
    if (!draggedKeywordId) return;
    
    const section = this.closest('.category-section');
    const toCategoryId = parseInt(section.dataset.categoryId);
    
    section.classList.remove('drag-over');
    this.classList.remove('drag-target');
    
    moveKeywordToCategory(draggedKeywordId, toCategoryId);
    draggedKeywordId = null;
  }
  
  function moveKeywordToCategory(keywordId, toCategoryId) {
    fetch(`/admin/api/move-keyword/${keywordId}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRF-Token': csrfToken
      },
      body: JSON.stringify({ category_id: toCategoryId })
    })
    .then(response => response.json())
    .then(data => {
      if (data.success) {
        showToast(`已移動到「${data.category_name}」`, 'success');
        setTimeout(() => location.reload(), 800);
      } else {
        showToast('移動失敗: ' + data.message, 'danger');
      }
    })
    .catch(error => {
      console.error('Error:', error);
      showToast('移動失敗', 'danger');
    });
  }
  
  function moveKeyword(keywordId, toCategoryId, evt) {
    fetch(`/admin/api/move-keyword/${keywordId}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRF-Token': csrfToken
      },
      body: JSON.stringify({ category_id: toCategoryId })
    })
    .then(response => response.json())
    .then(data => {
      if (data.success) {
        showToast('關鍵字已移動', 'success');
        updateKeywordOrder(evt.to);
        updateKeywordOrder(evt.from);
      } else {
        showToast('移動失敗: ' + data.message, 'danger');
        evt.from.insertBefore(evt.item, evt.from.children[evt.oldIndex]);
      }
    })
    .catch(error => {
      console.error('Error:', error);
      showToast('移動失敗', 'danger');
      evt.from.insertBefore(evt.item, evt.from.children[evt.oldIndex]);
    });
  }
  
  function updateKeywordOrder(list) {
    const items = list.querySelectorAll('.keyword-row');
    const order = Array.from(items).map(item => parseInt(item.dataset.keywordId));
    
    fetch('/admin/api/reorder-keywords', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRF-Token': csrfToken
      },
      body: JSON.stringify({ order: order })
    })
    .then(response => response.json())
    .then(data => {
      if (!data.success) {
        showToast('順序更新失敗: ' + data.message, 'danger');
      }
    })
    .catch(error => {
      console.error('Error:', error);
    });
  }
  
  
  function initializeFilters() {
    document.querySelectorAll('[data-filter]').forEach(item => {
      item.addEventListener('click', function(e) {
        e.preventDefault();
        const filter = this.dataset.filter;
        applyFilter(filter);
      });
    });
    
    document.querySelectorAll('[data-sort]').forEach(item => {
      item.addEventListener('click', function(e) {
        e.preventDefault();
        const sort = this.dataset.sort;
        applySort(sort);
      });
    });
  }
  
  function applyFilter(filter) {
    const rows = document.querySelectorAll('.keyword-row');
    
    rows.forEach(row => {
      const isPublic = row.dataset.public === 'true';
      let show = true;
      
      if (filter === 'public' && !isPublic) {
        show = false;
      } else if (filter === 'private' && isPublic) {
        show = false;
      }
      
      row.style.display = show ? '' : 'none';
    });
    
    showToast(`篩選: ${getFilterLabel(filter)}`, 'info');
  }
  
  function getFilterLabel(filter) {
    const labels = {
      'all': '全部內容',
      'public': '僅公開',
      'private': '僅隱藏'
    };
    return labels[filter] || filter;
  }
  
  function applySort(sort) {
    showToast('排序功能開發中...', 'info');
  }
  
  
  function initializeSearch() {
    const searchInput = document.getElementById('contentSearch');
    if (!searchInput) return;
    
    let searchTimeout;
    searchInput.addEventListener('input', function() {
      clearTimeout(searchTimeout);
      searchTimeout = setTimeout(() => {
        performSearch(this.value.trim());
      }, 300);
    });
  }
  
  function performSearch(query) {
    const rows = document.querySelectorAll('.keyword-row');
    const lowerQuery = query.toLowerCase();
    let visibleCount = 0;
    
    rows.forEach(row => {
      const titleLink = row.querySelector('.keyword-title-link');
      const title = titleLink ? titleLink.textContent.toLowerCase() : '';
      const description = row.querySelector('.keyword-description-preview');
      const descText = description ? description.textContent.toLowerCase() : '';
      
      const matches = title.includes(lowerQuery) || descText.includes(lowerQuery);
      row.style.display = matches ? '' : 'none';
      
      if (matches) visibleCount++;
    });
    
    document.querySelectorAll('.category-section').forEach(section => {
      const visibleRows = section.querySelectorAll('.keyword-row[style=""], .keyword-row:not([style*="none"])');
      const content = section.querySelector('.category-content');
      if (query && visibleRows.length === 0 && content) {
        section.style.display = 'none';
      } else {
        section.style.display = '';
      }
    });
  }
  
  
  function initializeBatchMode() {
    const btn = document.getElementById('toggleBatchMode');
    if (!btn) return;
    
    btn.addEventListener('click', function() {
      toggleBatchMode();
    });
  }
  
  
  let categoryIconPicker = null;
  
  function initializeCategoryModal() {
    const form = document.getElementById('categoryForm');
    if (form) {
      form.addEventListener('submit', handleCategorySubmit);
    }
    
    const iconInput = document.getElementById('categoryIconInput');
    if (iconInput && typeof IconPicker !== 'undefined') {
      categoryIconPicker = new IconPicker(iconInput, {
        placeholder: '搜尋圖示...',
        showCustomInput: false,
        iconsPerRow: 8,
        maxDisplayed: 80,
        onSelect: (icon) => {
        }
      });
    }
  }
  
  function toggleBatchMode() {
    batchModeActive = !batchModeActive;
    
    if (batchModeActive) {
      document.body.classList.add('batch-mode-active');
      document.getElementById('toggleBatchMode').innerHTML = '<i class="bi bi-x-square me-1"></i> 退出批次操作';
    } else {
      document.body.classList.remove('batch-mode-active');
      document.getElementById('toggleBatchMode').innerHTML = '<i class="bi bi-check-square me-1"></i> 批次操作';
      clearBatchSelection();
    }
  }
  
  window.updateBatchSelection = function() {
    const checkboxes = document.querySelectorAll('.keyword-checkbox:checked');
    const count = checkboxes.length;
    
    document.getElementById('selectedCount').textContent = count;
    document.getElementById('moveCount').textContent = count;
    
    const toolbar = document.getElementById('batchToolbar');
    if (toolbar) {
      toolbar.style.display = count > 0 ? 'block' : 'none';
    }
  };
  
  window.toggleCategorySelection = function(categoryId, checked) {
    const checkboxes = document.querySelectorAll(`[data-category-id="${categoryId}"] .keyword-checkbox`);
    checkboxes.forEach(cb => cb.checked = checked);
    updateBatchSelection();
  };
  
  window.clearBatchSelection = function() {
    document.querySelectorAll('.keyword-checkbox').forEach(cb => cb.checked = false);
    updateBatchSelection();
  };
  
  function getSelectedKeywordIds() {
    const checkboxes = document.querySelectorAll('.keyword-checkbox:checked');
    return Array.from(checkboxes).map(cb => parseInt(cb.value));
  }
  
  window.batchAction = function(action) {
    const ids = getSelectedKeywordIds();
    
    if (ids.length === 0) {
      showToast('請先選擇要操作的項目', 'warning');
      return;
    }
    
    switch(action) {
      case 'publish':
        batchToggleVisibility(ids, true);
        break;
      case 'unpublish':
        batchToggleVisibility(ids, false);
        break;
      case 'move':
        showBatchMoveModal(ids);
        break;
      case 'delete':
        batchDelete(ids);
        break;
    }
  };
  
  function batchToggleVisibility(ids, isPublic) {
    const action = isPublic ? '公開' : '隱藏';
    if (!confirm(`確定要將 ${ids.length} 筆關鍵字設為${action}嗎?`)) {
      return;
    }
    
    fetch('/admin/api/batch-toggle-visibility', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRF-Token': csrfToken
      },
      body: JSON.stringify({ keyword_ids: ids, is_public: isPublic })
    })
    .then(response => response.json())
    .then(data => {
      if (data.success) {
        showToast(data.message, 'success');
        setTimeout(() => location.reload(), 1000);
      } else {
        showToast(data.message, 'danger');
      }
    })
    .catch(error => {
      console.error('Error:', error);
      showToast('操作失敗', 'danger');
    });
  }
  
  function showBatchMoveModal(ids) {
    const modal = new bootstrap.Modal(document.getElementById('batchMoveModal'));
    modal.show();
  }
  
  window.confirmBatchMove = function() {
    const ids = getSelectedKeywordIds();
    const targetId = document.getElementById('batchMoveTarget').value;
    
    if (!targetId) {
      showToast('請選擇目標分類', 'warning');
      return;
    }
    
    fetch('/admin/api/batch-move', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRF-Token': csrfToken
      },
      body: JSON.stringify({ keyword_ids: ids, category_id: parseInt(targetId) })
    })
    .then(response => response.json())
    .then(data => {
      if (data.success) {
        showToast(data.message, 'success');
        const modal = bootstrap.Modal.getInstance(document.getElementById('batchMoveModal'));
        modal.hide();
        setTimeout(() => location.reload(), 1000);
      } else {
        showToast(data.message, 'danger');
      }
    })
    .catch(error => {
      console.error('Error:', error);
      showToast('操作失敗', 'danger');
    });
  };
  
  function batchDelete(ids) {
    if (!confirm(`⚠️ 確定要刪除 ${ids.length} 筆關鍵字嗎?\n\n此操作無法復原!`)) {
      return;
    }
    
    fetch('/admin/api/batch-delete', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRF-Token': csrfToken
      },
      body: JSON.stringify({ keyword_ids: ids })
    })
    .then(response => response.json())
    .then(data => {
      if (data.success) {
        showToast(data.message, 'success');
        setTimeout(() => location.reload(), 1000);
      } else {
        showToast(data.message, 'danger');
      }
    })
    .catch(error => {
      console.error('Error:', error);
      showToast('刪除失敗', 'danger');
    });
  }
  
  
  window.deleteCategory = function(id, name, keywordCount) {
    let message = `確定要刪除分類「${name}」嗎?`;
    if (keywordCount > 0) {
      message += `\n\n⚠️ 此分類下有 ${keywordCount} 筆關鍵字,刪除後這些關鍵字也會一併刪除。\n\n此操作無法復原!`;
    } else {
      message += '\n\n此操作無法復原。';
    }
    
    if (confirm(message)) {
      const form = document.getElementById('deleteForm');
      form.action = `/admin/categories/${id}/delete`;
      form.submit();
    }
  };
  
  window.deleteKeyword = function(id, title) {
    if (confirm(`確定要刪除關鍵字「${title}」嗎?\n\n此操作無法復原。`)) {
      const form = document.getElementById('deleteForm');
      form.action = `/admin/keywords/${id}/delete`;
      form.submit();
    }
  };
  
  
  window.editCategory = function(id) {
    window.location.href = `/admin/categories/${id}/edit`;
  };
  
  window.setDefaultCategory = function(categoryId) {
    const select = document.getElementById('quickCategorySelect');
    if (select) {
      select.value = categoryId;
    }
  };
  
  
  window.changeKeywordVisibility = function(keywordId, newStatus, event) {
    event.preventDefault();
    event.stopPropagation();
    
    fetch('/admin/api/toggle-keyword-visibility', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRF-Token': csrfToken
      },
      body: JSON.stringify({ 
        keyword_id: keywordId,
        is_public: newStatus 
      })
    })
    .then(response => response.json())
    .then(data => {
      if (data.success) {
        const row = document.querySelector(`[data-keyword-id="${keywordId}"]`);
        if (row) {
          const dropdown = row.querySelector('.dropdown');
          const btn = dropdown.querySelector('.status-dropdown-btn');
          const publicOption = dropdown.querySelector('.status-option-public');
          const privateOption = dropdown.querySelector('.status-option-private');
          
          if (btn) {
            btn.dataset.currentStatus = newStatus.toString();
            if (newStatus) {
              btn.className = 'status-dropdown-btn status-public';
              btn.innerHTML = '<i class="bi bi-eye"></i> 公開<i class="bi bi-chevron-down ms-1" style="font-size: 0.7rem;"></i>';
            } else {
              btn.className = 'status-dropdown-btn status-private';
              btn.innerHTML = '<i class="bi bi-eye-slash"></i> 隱藏<i class="bi bi-chevron-down ms-1" style="font-size: 0.7rem;"></i>';
            }
          }
          
          if (publicOption && privateOption) {
            if (newStatus) {
              publicOption.classList.add('active');
              privateOption.classList.remove('active');
              publicOption.innerHTML = '<i class="bi bi-eye text-success me-2"></i>公開<i class="bi bi-check-lg ms-auto text-primary"></i>';
              privateOption.innerHTML = '<i class="bi bi-eye-slash text-warning me-2"></i>隱藏';
            } else {
              publicOption.classList.remove('active');
              privateOption.classList.add('active');
              publicOption.innerHTML = '<i class="bi bi-eye text-success me-2"></i>公開';
              privateOption.innerHTML = '<i class="bi bi-eye-slash text-warning me-2"></i>隱藏<i class="bi bi-check-lg ms-auto text-primary"></i>';
            }
          }
          
          row.dataset.public = newStatus.toString();
        }
        
        showToast(data.message, 'success');
        
        const dropdownElement = event.target.closest('.dropdown').querySelector('[data-bs-toggle="dropdown"]');
        const dropdownInstance = bootstrap.Dropdown.getInstance(dropdownElement);
        if (dropdownInstance) {
          dropdownInstance.hide();
        }
      } else {
        showToast(data.message, 'danger');
      }
    })
    .catch(error => {
      console.error('Error:', error);
      showToast('操作失敗', 'danger');
    });
  };
  
  
  
  window.openCategoryModal = function() {
    const modal = document.getElementById('categoryModal');
    const form = document.getElementById('categoryForm');
    const modalTitle = modal.querySelector('.modal-title');
    const submitBtn = document.getElementById('categorySubmitBtn');
    
    form.reset();
    form.action = '/admin/categories/quick-create';
    document.getElementById('categoryId').value = '';
    
    modalTitle.innerHTML = '<i class="bi bi-folder-plus me-2"></i>新增分類';
    submitBtn.innerHTML = '<i class="bi bi-check-circle me-1"></i>建立分類';
    
    if (categoryIconPicker) {
      categoryIconPicker.selectIcon('');
    }
    
    const bsModal = new bootstrap.Modal(modal);
    bsModal.show();
  };
  
  
  window.editCategory = function(categoryId) {
    fetch(`/admin/categories/${categoryId}/data`)
      .then(response => response.json())
      .then(data => {
        const modal = document.getElementById('categoryModal');
        const form = document.getElementById('categoryForm');
        const modalTitle = modal.querySelector('.modal-title');
        const submitBtn = document.getElementById('categorySubmitBtn');
        
        form.action = `/admin/categories/${categoryId}/update`;
        document.getElementById('categoryId').value = categoryId;
        document.getElementById('categoryName').value = data.name;
        document.getElementById('categoryDescription').value = data.description || '';
        document.getElementById('categoryIsPublic').checked = data.is_public;
        
        modalTitle.innerHTML = '<i class="bi bi-pencil-square me-2"></i>編輯分類';
        submitBtn.innerHTML = '<i class="bi bi-check-circle me-1"></i>儲存變更';
        
        if (categoryIconPicker) {
          categoryIconPicker.selectIcon(data.icon || '');
        }
        
        const bsModal = new bootstrap.Modal(modal);
        bsModal.show();
      })
      .catch(error => {
        console.error('Error loading category:', error);
        showToast('載入分類資料失敗', 'danger');
      });
  };
  
  
  function handleCategorySubmit(event) {
    event.preventDefault();
    
    const form = event.target;
    const formData = new FormData(form);
    const categoryId = document.getElementById('categoryId').value;
    const isEdit = categoryId !== '';
    
    fetch(form.action, {
      method: 'POST',
      body: formData,
      headers: {
        'X-Requested-With': 'XMLHttpRequest'
      }
    })
      .then(response => response.json())
      .then(data => {
        if (data.success) {
          showToast(isEdit ? '分類更新成功' : '分類新增成功', 'success');
          
          const modal = bootstrap.Modal.getInstance(document.getElementById('categoryModal'));
          modal.hide();
          
          setTimeout(() => {
            window.location.reload();
          }, 1000);
        } else {
          showToast(data.message || '操作失敗', 'danger');
        }
      })
      .catch(error => {
        console.error('Error:', error);
        showToast('操作失敗', 'danger');
      });
  }
  
  
  function showToast(message, type = 'success') {
    const toastHtml = `
      <div class="toast align-items-center text-white bg-${type} border-0 position-fixed bottom-0 end-0 m-3" role="alert" style="z-index: 9999;">
        <div class="d-flex">
          <div class="toast-body">${message}</div>
          <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
      </div>
    `;
    document.body.insertAdjacentHTML('beforeend', toastHtml);
    const toastEl = document.body.lastElementChild;
    const toast = new bootstrap.Toast(toastEl, { delay: 3000 });
    toast.show();
    toastEl.addEventListener('hidden.bs.toast', () => toastEl.remove());
  }
  
})();
