// SPA导航切换
const navs = [
  {btn: 'nav-home', page: 'page-home'},
  {btn: 'nav-ai', page: 'page-ai'},
  {btn: 'nav-contract', page: 'page-contract'},
  {btn: 'nav-doc', page: 'page-doc'},
  {btn: 'nav-quiz', page: 'page-quiz'},
  {btn: 'nav-court', page: 'page-court'}
];

// 初始化导航
function initNavigation() {
  navs.forEach(({btn, page}) => {
    document.getElementById(btn).onclick = function() {
      navs.forEach(({btn, page}) => {
        document.getElementById(btn).classList.remove('active');
        document.getElementById(page).style.display = 'none';
      });
      this.classList.add('active');
      document.getElementById(page).style.display = '';
    };
  });
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
  initNavigation();
}); 