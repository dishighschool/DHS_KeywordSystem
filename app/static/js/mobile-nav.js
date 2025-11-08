(function() {
  'use strict';

  document.addEventListener('DOMContentLoaded', function() {
    const navbarToggler = document.querySelector('.navbar-toggler');
    const navbarCollapse = document.querySelector('.navbar-collapse');
    const body = document.body;

    if (!navbarToggler || !navbarCollapse) return;

    navbarCollapse.addEventListener('show.bs.collapse', function() {
      body.classList.add('navbar-open');
      body.style.overflow = 'hidden';
    });

    navbarCollapse.addEventListener('hide.bs.collapse', function() {
      body.classList.remove('navbar-open');
      body.style.overflow = '';
    });

    const navLinks = navbarCollapse.querySelectorAll('.nav-link');
    navLinks.forEach(link => {
      link.addEventListener('click', function() {
        if (window.innerWidth < 768) {
          const bsCollapse = bootstrap.Collapse.getInstance(navbarCollapse);
          if (bsCollapse) {
            bsCollapse.hide();
          }
        }
      });
    });

    document.addEventListener('click', function(event) {
      if (window.innerWidth < 768) {
        const isClickInside = navbarCollapse.contains(event.target) || 
                             navbarToggler.contains(event.target);
        
        if (!isClickInside && navbarCollapse.classList.contains('show')) {
          const bsCollapse = bootstrap.Collapse.getInstance(navbarCollapse);
          if (bsCollapse) {
            bsCollapse.hide();
          }
        }
      }
    });

    document.addEventListener('keydown', function(event) {
      if (event.key === 'Escape' && navbarCollapse.classList.contains('show')) {
        const bsCollapse = bootstrap.Collapse.getInstance(navbarCollapse);
        if (bsCollapse) {
          bsCollapse.hide();
        }
      }
    });
  });
})();
