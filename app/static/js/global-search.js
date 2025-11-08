(function() {
  'use strict';

  let searchData = [];
  let searchTimeout = null;
  const DEBOUNCE_DELAY = 300;

  const searchInput = document.getElementById('globalSearch');
  const searchResults = document.getElementById('searchResults');
  const searchResultsList = document.getElementById('searchResultsList');
  const searchLoading = document.getElementById('searchLoading');

  if (!searchInput || !searchResults || !searchResultsList) {
    return;
  }

  
  async function loadSearchData() {
    try {
      const response = await fetch('/api/search');
      if (!response.ok) {
        throw new Error('Failed to load search data');
      }
      searchData = await response.json();
    } catch (error) {
      console.error('Error loading search data:', error);
      searchData = [];
    }
  }

  
  function normalizeText(text) {
    return text.toLowerCase().trim();
  }

  
  function performSearch(query) {
    if (!query || query.length < 1) {
      return [];
    }

    const normalizedQuery = normalizeText(query);
    
    return searchData.filter(item => {
      const titleMatch = normalizeText(item.title).includes(normalizedQuery);
      const descriptionMatch = normalizeText(item.description).includes(normalizedQuery);
      const categoryMatch = normalizeText(item.category).includes(normalizedQuery);
      const mainKeywordMatch = item.main_keyword && normalizeText(item.main_keyword).includes(normalizedQuery);
      
      return titleMatch || descriptionMatch || categoryMatch || mainKeywordMatch;
    }).slice(0, 20);
  }

  
  function highlightText(text, query) {
    if (!query) return text;
    
    const regex = new RegExp(`(${query})`, 'gi');
    return text.replace(regex, '<mark class="bg-warning bg-opacity-50">$1</mark>');
  }

  
  function renderResults(results, query) {
    const isMobile = window.innerWidth < 768;
    
    if (results.length === 0) {
      searchResultsList.innerHTML = `
        <div class="p-4 text-center text-muted">
          <i class="bi bi-search ${isMobile ? 'fs-2' : 'fs-3'} mb-2 d-block"></i>
          <p class="mb-0 ${isMobile ? 'small' : ''}">找不到符合「${query}」的結果</p>
        </div>
      `;
      return;
    }

    const html = results.map(item => {
      const titleHtml = highlightText(item.title, query);
      const descriptionHtml = highlightText(item.description, query);
      const categoryBadge = `<span class="badge bg-primary-subtle text-primary ${isMobile ? 'me-1' : 'me-2'}">
        <i class="${item.category_icon} me-1"></i>${item.category}
      </span>`;
      
      const aliasBadge = item.type === 'alias' 
        ? `<span class="badge bg-secondary-subtle text-secondary">
            <i class="bi bi-arrow-return-right me-1"></i>別名
           </span>`
        : '';

      return `
        <a href="${item.url}" class="search-result-item d-block text-decoration-none p-3 border-bottom">
          <div class="d-flex align-items-start">
            <div class="flex-grow-1">
              <div class="mb-1">
                ${categoryBadge}
                ${aliasBadge}
              </div>
              <h6 class="mb-1 text-dark fw-bold ${isMobile ? 'fs-6' : ''}">${titleHtml}</h6>
              ${item.type === 'alias' && item.main_keyword ? 
                `<p class="text-muted small mb-1"><i class="bi bi-link-45deg me-1"></i>連結至：${item.main_keyword}</p>` : ''
              }
              ${!isMobile || results.length < 5 ? `<p class="text-muted small mb-0">${descriptionHtml}...</p>` : ''}
            </div>
            <div class="ms-2 ${isMobile ? 'ms-2' : 'ms-3'}">
              <i class="bi bi-chevron-right text-muted ${isMobile ? 'fs-6' : ''}"></i>
            </div>
          </div>
        </a>
      `;
    }).join('');

    searchResultsList.innerHTML = html;
  }

  
  function showResults() {
    searchResults.classList.remove('d-none');
  }

  
  function hideResults() {
    searchResults.classList.add('d-none');
  }

  
  function showLoading() {
    searchLoading.classList.remove('d-none');
    searchResultsList.innerHTML = '';
  }

  
  function hideLoading() {
    searchLoading.classList.add('d-none');
  }

  
  function handleSearch() {
    const query = searchInput.value.trim();

    if (searchTimeout) {
      clearTimeout(searchTimeout);
    }

    if (!query) {
      hideResults();
      return;
    }

    showResults();
    showLoading();

    searchTimeout = setTimeout(() => {
      hideLoading();
      const results = performSearch(query);
      renderResults(results, query);
    }, DEBOUNCE_DELAY);
  }

  
  function handleClickOutside(event) {
    const isMobile = window.innerWidth < 768;
    const clickedElement = event.target;
    
    const isSearchInput = searchInput.contains(clickedElement);
    const isSearchResults = searchResults.contains(clickedElement);
    const isSearchResultItem = clickedElement.closest('.search-result-item');
    
    if (!isSearchInput && !isSearchResults && !isSearchResultItem) {
      hideResults();
    }
  }

  
  async function init() {
    await loadSearchData();

    searchInput.addEventListener('input', handleSearch);
    searchInput.addEventListener('focus', () => {
      if (searchInput.value.trim()) {
        showResults();
      }
    });
    
    setTimeout(() => {
      document.addEventListener('click', handleClickOutside);
    }, 100);

    document.addEventListener('keydown', (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        searchInput.focus();
        
        if (window.innerWidth < 768) {
          const navbarCollapse = document.querySelector('.navbar-collapse');
          if (navbarCollapse && !navbarCollapse.classList.contains('show')) {
            const bsCollapse = new bootstrap.Collapse(navbarCollapse, { toggle: true });
          }
        }
      }
      
      if (e.key === 'Escape') {
        hideResults();
        searchInput.blur();
      }
    });

    searchResults.addEventListener('click', (e) => {
      if (e.target.closest('.search-result-item')) {
        setTimeout(() => {
          hideResults();
        }, 100);
      }
    });

    searchResults.addEventListener('scroll', (e) => {
      e.stopPropagation();
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
