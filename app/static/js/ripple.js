class RippleEffect {
  constructor() {
    this.init();
  }

  init() {
    document.addEventListener('DOMContentLoaded', () => {
      this.addRippleToElements('.keyword-card-link');
      this.addRippleToElements('.keyword-card-link-flat');
      
      this.addRippleToElements('.btn');
      this.addRippleToElements('.btn-view-all');
      this.addRippleToElements('button');
      this.addRippleToElements('[role="button"]');
      
      
      this.addRippleToElements('.category-btn');
      
      this.addRippleToElements('.nav-link');
      
      this.addRippleToElements('.breadcrumb-item a');
      
      this.addRippleToElements('.other-categories-section .card');
      
      this.addRippleToElements('.related-keywords-section .card');
      
      this.addRippleToElements('#backToTop');
      
      this.addRippleToElements('#mobileSearchBtn');
      
      this.addRippleToElements('#closeMobileSearch');
    });
  }

  addRippleToElements(selector) {
    const elements = document.querySelectorAll(selector);
    
    elements.forEach(element => {
      if (element.classList.contains('mobile-nav-icon') ||
          element.classList.contains('mobile-search-icon') ||
          element.classList.contains('mobile-title-section')) {
        return;
      }
      
      element.addEventListener('mousedown', (e) => {
        this.createRipple(e, element);
      });

      element.addEventListener('touchstart', (e) => {
        this.createRipple(e, element);
      }, { passive: true });

      element.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          this.createRipple(e, element);
        }
      });
    });
  }

  createRipple(event, element) {
    element.classList.remove('ripple-active');
    
    const rect = element.getBoundingClientRect();
    
    let x, y;
    if (event.type === 'keydown') {
      x = rect.width / 2;
      y = rect.height / 2;
    } else if (event.type === 'touchstart') {
      const touch = event.touches[0];
      x = touch.clientX - rect.left;
      y = touch.clientY - rect.top;
    } else {
      x = event.clientX - rect.left;
      y = event.clientY - rect.top;
    }
    
    x = Math.max(0, Math.min(x, rect.width));
    y = Math.max(0, Math.min(y, rect.height));
    
    const xPercent = (x / rect.width) * 100;
    const yPercent = (y / rect.height) * 100;
    
    element.style.setProperty('--ripple-x', `${xPercent}%`);
    element.style.setProperty('--ripple-y', `${yPercent}%`);
    
    requestAnimationFrame(() => {
      element.classList.add('ripple-active');
    });
    
    setTimeout(() => {
      element.classList.remove('ripple-active');
    }, 600);
  }
}

const rippleInstance = new RippleEffect();

window.RippleEffect = RippleEffect;
