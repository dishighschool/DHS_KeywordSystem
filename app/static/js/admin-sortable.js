function initSortable(listId, apiEndpoint, options = {}) {
  const list = document.getElementById(listId);
  
  if (!list) {
    console.warn(`Element with id "${listId}" not found`);
    return;
  }

  const defaultOptions = {
    animation: 150,
    handle: '.drag-handle',
    ghostClass: 'sortable-ghost',
    dragClass: 'sortable-drag',
    onEnd: function(evt) {
      updateOrder(list, apiEndpoint, options.onSuccess, options.onError);
    }
  };

  new Sortable(list, { ...defaultOptions, ...options });
}

function updateOrder(list, apiEndpoint, onSuccess, onError) {
  const items = list.querySelectorAll('.draggable-item');
  const order = Array.from(items).map(item => parseInt(item.dataset.id));
  
  fetch(apiEndpoint, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': getCsrfToken()
    },
    body: JSON.stringify({ order: order })
  })
  .then(response => response.json())
  .then(data => {
    if (data.success) {
      showToast('順序已更新', 'success');
      items.forEach((item, index) => {
        const badge = item.querySelector('.badge');
        if (badge) {
          badge.textContent = `位置: ${index}`;
        }
      });
      if (onSuccess) onSuccess(data);
    } else {
      showToast('更新失敗: ' + data.message, 'danger');
      if (onError) onError(data);
    }
  })
  .catch(error => {
    showToast('更新失敗: ' + error, 'danger');
    if (onError) onError(error);
  });
}

function getCsrfToken() {
  return document.querySelector('meta[name="csrf-token"]')?.content || '';
}

function showToast(message, type = 'info') {
  const toastContainer = document.querySelector('.toast-container') || createToastContainer();
  const toast = document.createElement('div');
  toast.className = `toast align-items-center text-white bg-${type} border-0`;
  toast.setAttribute('role', 'alert');
  toast.setAttribute('aria-live', 'assertive');
  toast.setAttribute('aria-atomic', 'true');
  
  const icon = type === 'success' ? 'check-circle' : 
               type === 'danger' ? 'exclamation-circle' : 
               type === 'warning' ? 'exclamation-triangle' : 'info-circle';
  
  toast.innerHTML = `
    <div class="d-flex">
      <div class="toast-body">
        <i class="bi bi-${icon} me-2"></i>${message}
      </div>
      <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
    </div>
  `;
  
  toastContainer.appendChild(toast);
  const bsToast = new bootstrap.Toast(toast, { delay: 3000 });
  bsToast.show();
  toast.addEventListener('hidden.bs.toast', () => toast.remove());
}

function createToastContainer() {
  const container = document.createElement('div');
  container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
  container.style.zIndex = '9999';
  document.body.appendChild(container);
  return container;
}

function addSortableStyles() {
  if (document.getElementById('sortable-styles')) return;
  
  const style = document.createElement('style');
  style.id = 'sortable-styles';
  style.textContent = `
    .sortable-ghost {
      opacity: 0.4;
      background-color: #f8f9fa;
    }
    
    .sortable-drag {
      opacity: 0.8;
      cursor: grabbing !important;
    }
    
    .draggable-item {
      transition: all 0.2s ease;
    }
    
    .draggable-item:hover {
      background-color: rgba(102, 126, 234, 0.05);
    }
    
    .drag-handle {
      opacity: 0.3;
      transition: opacity 0.2s;
      cursor: grab;
      user-select: none;
    }
    
    .draggable-item:hover .drag-handle {
      opacity: 1;
    }
    
    .drag-handle:active {
      cursor: grabbing;
    }
  `;
  document.head.appendChild(style);
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', addSortableStyles);
} else {
  addSortableStyles();
}
