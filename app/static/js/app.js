(function(){
  const toggle = document.querySelector('[data-js="nav-toggle"]');
  const nav = document.querySelector('[data-js="nav"]');
  if (toggle && nav){
    toggle.addEventListener('click', () => {
      nav.classList.toggle('is-open');
    });
  }
})();
