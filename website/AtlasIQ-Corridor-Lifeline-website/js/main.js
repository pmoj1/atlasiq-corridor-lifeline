/* AtlasIQ — native progressive enhancement, with no external dependencies. */
(() => {
  'use strict';
  document.documentElement.classList.add('js');
  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  const nav = document.getElementById('nav');
  const year = document.getElementById('copyrightYear');
  if (year) year.textContent = new Date().getFullYear();

  // Mobile menu: keyboard escape, contained focus and focus restoration.
  const toggle = document.querySelector('.menu-toggle');
  const menu = document.getElementById('mobile-menu');
  let lastFocus = null;
  const closeMenu = (restore = true) => {
    if (!menu || menu.hidden) return;
    menu.hidden = true;
    toggle.setAttribute('aria-expanded', 'false');
    toggle.setAttribute('aria-label', 'Open navigation');
    document.body.classList.remove('menu-open');
    if (restore && lastFocus) lastFocus.focus();
  };
  if (toggle && menu) {
    toggle.addEventListener('click', () => {
      if (!menu.hidden) return closeMenu();
      lastFocus = document.activeElement;
      menu.hidden = false;
      toggle.setAttribute('aria-expanded', 'true');
      toggle.setAttribute('aria-label', 'Close navigation');
      document.body.classList.add('menu-open');
      menu.querySelector('a').focus();
    });
    document.addEventListener('keydown', (event) => {
      if (menu.hidden) return;
      if (event.key === 'Escape') { event.preventDefault(); closeMenu(); }
      if (event.key === 'Tab') {
        const items = [toggle, ...menu.querySelectorAll('a')];
        const index = items.indexOf(document.activeElement);
        if (event.shiftKey && index === 0) { event.preventDefault(); items.at(-1).focus(); }
        else if (!event.shiftKey && index === items.length - 1) { event.preventDefault(); toggle.focus(); }
      }
    });
    menu.querySelectorAll('a').forEach(link => link.addEventListener('click', () => closeMenu(false)));
    window.matchMedia('(min-width: 761px)').addEventListener('change', event => { if(event.matches) closeMenu(); });
  }

  // Native anchors honour the fixed navigation and maintain URL/history semantics.
  function goToHash(hash, immediate = false, focus = false) {
    let id;
    try { id = decodeURIComponent(hash.slice(1)); } catch (_) { return; }
    const target = document.getElementById(id);
    if (!target) return;
    const offset = (nav?.offsetHeight || 0) + 20;
    window.scrollTo({top: Math.max(0, target.getBoundingClientRect().top + window.scrollY - offset), behavior: immediate || reduceMotion.matches ? 'instant' : 'smooth'});
    if (focus) {
      if (!target.hasAttribute('tabindex')) { target.setAttribute('tabindex', '-1'); target.addEventListener('blur', () => target.removeAttribute('tabindex'), {once:true}); }
      target.focus({preventScroll:true});
    }
  }
  document.addEventListener('click', event => {
    const link = event.target.closest?.('a[href^="#"]');
    if (!link || event.defaultPrevented || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
    const hash = link.getAttribute('href');
    let target;
    try { target = document.getElementById(decodeURIComponent(hash.slice(1))); } catch (_) { return; }
    if (!target) return;
    event.preventDefault();
    closeMenu(false);
    if (window.location.hash !== hash) history.pushState(null, '', hash);
    goToHash(hash, false, true);
  });
  window.addEventListener('popstate', () => goToHash(window.location.hash || '#top'));
  window.addEventListener('hashchange', () => goToHash(window.location.hash));
  window.addEventListener('load', () => { if(window.location.hash) goToHash(window.location.hash, true); }, {once:true});

  // Accessible, keyboard-operated chapters. Every chapter remains readable without JS.
  const tabs = [...document.querySelectorAll('[role="tab"]')];
  const panels = [...document.querySelectorAll('[role="tabpanel"]')];
  function selectTab(index, focus = false) {
    tabs.forEach((tab, i) => {
      const selected = i === index;
      tab.setAttribute('aria-selected', String(selected));
      tab.tabIndex = selected ? 0 : -1;
      tab.classList.toggle('is-selected', selected);
      panels[i].hidden = !selected;
      panels[i].classList.remove('is-entering');
    });
    if (!reduceMotion.matches) {
      void panels[index].offsetWidth;
      panels[index].classList.add('is-entering');
    }
    if (focus) tabs[index].focus();
  }
  tabs.forEach((tab, index) => {
    tab.addEventListener('click', () => selectTab(index));
    tab.addEventListener('keydown', event => {
      let next = index;
      if (event.key === 'ArrowRight' || event.key === 'ArrowDown') next = (index + 1) % tabs.length;
      else if (event.key === 'ArrowLeft' || event.key === 'ArrowUp') next = (index - 1 + tabs.length) % tabs.length;
      else if (event.key === 'Home') next = 0;
      else if (event.key === 'End') next = tabs.length - 1;
      else return;
      event.preventDefault(); selectTab(next, true);
    });
  });
  if (tabs.length) selectTab(0);

  // Reveals run once; never hide content if observer support is unavailable.
  const reveals = document.querySelectorAll('[data-reveal]');
  if ('IntersectionObserver' in window && !reduceMotion.matches) {
    const observer = new IntersectionObserver(entries => entries.forEach(entry => {
      if (!entry.isIntersecting) return;
      entry.target.classList.add('is-visible');
      entry.target.classList.remove('will-reveal');
      observer.unobserve(entry.target);
    }), {threshold:.08, rootMargin:'0px 0px -20px 0px'});
    reveals.forEach(element => { element.classList.add('will-reveal'); observer.observe(element); });
    reduceMotion.addEventListener('change', event => {
      if(event.matches) { observer.disconnect(); reveals.forEach(element => {element.classList.remove('will-reveal');element.classList.add('is-visible');}); }
    });
  } else reveals.forEach(element => element.classList.add('is-visible'));

  // Scroll-driven motion stops as soon as scrolling does. No autonomous loops.
  const progress = document.querySelector('.scroll-progress');
  const images = [...document.querySelectorAll('[data-parallax]')];
  let ticking = false;
  function paintScroll() {
    const y = window.scrollY;
    nav?.classList.toggle('is-scrolled', y > 30);
    const extent = document.documentElement.scrollHeight - window.innerHeight;
    if (progress) progress.style.transform = `scaleX(${extent > 0 ? Math.min(1, y / extent) : 0})`;
    images.forEach(image => {
      if(reduceMotion.matches) { image.style.transform = ''; return; }
      const section = image.parentElement.getBoundingClientRect();
      if(section.bottom < 0 || section.top > window.innerHeight) return;
      const offset = Math.max(-35, Math.min(35, -section.top * Number(image.dataset.parallax)));
      image.style.transform = `translate3d(0,${offset}px,0)`;
    });
    ticking = false;
  }
  window.addEventListener('scroll', () => {if(!ticking){ticking=true;requestAnimationFrame(paintScroll);}}, {passive:true});
  window.addEventListener('resize', paintScroll, {passive:true});
  reduceMotion.addEventListener('change', paintScroll);
  paintScroll();
})();
