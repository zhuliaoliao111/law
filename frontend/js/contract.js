// 智能合同功能JS
let contractText = '';

// 智能合同历史记录本地存储
function getContractHistory() {
  return JSON.parse(localStorage.getItem('contract_review_history') || '[]');
}

function saveContractHistory(history) {
  localStorage.setItem('contract_review_history', JSON.stringify(history));
}

function addContractHistory(item) {
  const history = getContractHistory();
  history.unshift(item);
  if(history.length > 10) history.length = 10; // 最多保存10条
  saveContractHistory(history);
}

function renderContractHistory() {
  const historyListContract = document.getElementById('historyListContract');
  if(!historyListContract) return;
  const history = getContractHistory();
  historyListContract.innerHTML = '';
  if(history.length === 0) {
    historyListContract.innerHTML = '<li style="color:#bbb;">暂无历史记录</li>';
    return;
  }
  history.forEach((h, i) => {
    const li = document.createElement('li');
    li.style.background = '#f7f8fa';
    li.style.borderRadius = '6px';
    li.style.padding = '12px 14px';
    li.style.marginBottom = '10px';
    li.style.cursor = 'pointer';
    li.innerHTML = `<div style='font-size:15px;color:#6f4a8e;font-weight:bold;'>${h.filename||'合同'}</div><div style='font-size:14px;color:#333;margin-top:6px;'>${h.suggestion}</div>`;
    li.onclick = () => {
      const reviewResult = document.getElementById('reviewResult');
      if (reviewResult) {
        reviewResult.innerText = h.suggestion;
      }
    };
    historyListContract.appendChild(li);
  });
}

function handleFile(file) {
  const uploadText = document.getElementById('uploadText');
  const reviewBtn = document.getElementById('reviewBtn');
  
  if(file.type.startsWith('text') || file.name.endsWith('.txt')) {
    const reader = new FileReader();
    reader.onload = function(e) {
      contractText = e.target.result;
      uploadText.innerText = '已上传：' + file.name;
      reviewBtn.disabled = false;
    };
    reader.readAsText(file);
  } else {
    uploadText.innerText = '仅支持txt文本文件';
    reviewBtn.disabled = true;
  }
}

// 初始化智能合同功能
function initContract() {
  const fileInput = document.getElementById('contractFile');
  const reviewBtn = document.getElementById('reviewBtn');
  const reviewResult = document.getElementById('reviewResult');
  const uploadBox = document.getElementById('uploadBox');
  const uploadText = document.getElementById('uploadText');

  if(fileInput && reviewBtn && reviewResult && uploadBox) {
    // 文件上传事件
    uploadBox.addEventListener('click', () => fileInput.click());
    
    // 拖拽事件
    uploadBox.addEventListener('dragover', e => { 
      e.preventDefault(); 
      uploadBox.style.borderColor = '#4f7cff'; 
    });
    
    uploadBox.addEventListener('dragleave', e => { 
      e.preventDefault(); 
      uploadBox.style.borderColor = '#a0a0ff'; 
    });
    
    uploadBox.addEventListener('drop', async e => {
      e.preventDefault();
      uploadBox.style.borderColor = '#a0a0ff';
      if(e.dataTransfer.files.length) {
        fileInput.files = e.dataTransfer.files;
        handleFile(fileInput.files[0]);
      }
    });
    
    // 文件选择事件
    fileInput.addEventListener('change', e => {
      if(e.target.files[0]) handleFile(e.target.files[0]);
    });
    
    // 审查按钮事件
    reviewBtn.addEventListener('click', async () => {
      reviewResult.innerText = '正在生成审查建议...';
      try {
        const res = await fetch('http://localhost:8000/contract_review', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ text: contractText })
        });
        const data = await res.json();
        reviewResult.innerText = data.suggestion || '未获取到建议';
        // 保存历史
        addContractHistory({
          filename: uploadText.innerText.replace('已上传：',''), 
          suggestion: data.suggestion || '未获取到建议'
        });
        renderContractHistory();
      } catch {
        reviewResult.innerText = '服务器暂时无法响应。';
      }
    });
    
    // 初始化历史
    renderContractHistory();
  }
}

// 页面加载完成后初始化智能合同功能
document.addEventListener('DOMContentLoaded', function() {
  initContract();
}); 