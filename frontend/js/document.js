// 文书生成功能JS
let currentDocType = '民事起诉状'; // 默认文书类型
let documentHistory = []; // 文书生成历史记录

// 文书生成历史记录本地存储
function getDocumentHistory() {
  return JSON.parse(localStorage.getItem('document_generation_history') || '[]');
}

function saveDocumentHistory(history) {
  localStorage.setItem('document_generation_history', JSON.stringify(history));
}

function addDocumentHistory(item) {
  const history = getDocumentHistory();
  // 添加时间戳
  const historyItem = {
    ...item,
    timestamp: new Date().toLocaleString('zh-CN')
  };
  history.unshift(historyItem);
  if(history.length > 10) history.length = 10; // 最多保存10条
  saveDocumentHistory(history);
}

// 文书历史记录显示
function renderDocumentHistory() {
  const historyList = document.getElementById('documentHistoryList');
  if(!historyList) return;
  const history = getDocumentHistory();
  historyList.innerHTML = '';
  if(history.length === 0) {
    historyList.innerHTML = '<div style="color:#bbb;text-align:center;padding:20px;">暂无历史记录</div>';
    return;
  }
  history.forEach((h, i) => {
    const div = document.createElement('div');
    div.style.background = '#f7f8fa';
    div.style.borderRadius = '6px';
    div.style.padding = '12px 14px';
    div.style.marginBottom = '10px';
    div.style.cursor = 'pointer';
    div.style.border = '1px solid #eee';
    div.innerHTML = `
      <div style='font-size:15px;color:#6f4a8e;font-weight:bold;margin-bottom:4px;'>${h.docType || '文书'}</div>
      <div style='font-size:12px;color:#666;'>${h.timestamp || '未知时间'}</div>
    `;
    div.onclick = () => {
      showDocumentPopup(h.content, h.docType);
    };
    historyList.appendChild(div);
  });
}

// 文书生成弹出页面控制
function showDocumentPopup(content, docType) {
  const popup = document.getElementById('documentPopup');
  const contentDiv = document.getElementById('documentContent');
  const titleDiv = document.getElementById('documentTitle');
  
  if(popup && contentDiv && titleDiv) {
    titleDiv.textContent = docType || '法律文书';
    contentDiv.innerHTML = content.replace(/\n/g, '<br>');
    popup.style.display = 'flex';
  }
}

function closeDocumentPopup() {
  const popup = document.getElementById('documentPopup');
  if(popup) {
    popup.style.display = 'none';
  }
}

// 解析用户输入的文本，提取关键信息
function parseUserInput(text) {
  // 简单的信息提取逻辑，可以根据需要优化
  const info = {
    plaintiff: {
      name: '',
      id_type: '身份证',
      id_number: '',
      address: '',
      contact: ''
    },
    defendant: {
      name: '',
      id_type: '身份证', 
      id_number: '',
      address: '',
      contact: ''
    },
    case_info: {
      case_type: '民间借贷',
      facts: text,
      legal_basis: ''
    },
    claims: [],
    court: 'XX人民法院'
  };
  
  // 尝试从文本中提取原告和被告信息
  const lines = text.split('\n');
  for(let line of lines) {
    line = line.trim();
    if(line.includes('原告') || line.includes('我') || line.includes('本人')) {
      // 提取原告信息
      if(line.includes('姓名') || line.includes('叫')) {
        const nameMatch = line.match(/[姓名叫]([^\s，。]+)/);
        if(nameMatch) info.plaintiff.name = nameMatch[1];
      }
    }
    if(line.includes('被告') || line.includes('对方') || line.includes('他')) {
      // 提取被告信息
      if(line.includes('姓名') || line.includes('叫')) {
        const nameMatch = line.match(/[姓名叫]([^\s，。]+)/);
        if(nameMatch) info.defendant.name = nameMatch[1];
      }
    }
  }
  
  // 如果没有提取到姓名，使用默认值
  if(!info.plaintiff.name) info.plaintiff.name = '原告';
  if(!info.defendant.name) info.defendant.name = '被告';
  
  // 根据案件类型生成诉讼请求
  if(info.case_info.case_type === '民间借贷') {
    info.claims = [
      '判令被告偿还借款本金及利息',
      '判令被告承担本案诉讼费用'
    ];
  } else {
    info.claims = [
      '判令被告承担相应法律责任',
      '判令被告承担本案诉讼费用'
    ];
  }
  
  return info;
}

// 生成文书
async function generateDocument(docType) {
  const textarea = document.getElementById('docTextarea');
  if(!textarea) {
    alert('找不到输入框');
    return;
  }
  
  const userInput = textarea.value.trim();
  if(!userInput) {
    alert('请先输入案件描述');
    return;
  }
  
  try {
    // 显示加载状态
    const generateBtn = docType === '民事起诉状' ? document.getElementById('lawsuitBtn') : document.getElementById('defenseBtn');
    if(generateBtn) {
      generateBtn.textContent = '生成中...';
      generateBtn.disabled = true;
    }
    
    // 解析用户输入
    const parsedInfo = parseUserInput(userInput);
    
    // 调用API
    const endpoint = docType === '民事起诉状' ? '/generate_lawsuit' : '/generate_defense';
    const response = await fetch(`http://localhost:8000${endpoint}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(parsedInfo)
    });
    
    if(!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const data = await response.json();
    
    if(data.success) {
      // 保存历史
      addDocumentHistory({
        docType: docType,
        content: data.content,
        userInput: userInput
      });
      renderDocumentHistory();
      
      // 显示结果
      showDocumentPopup(data.content, docType);
    } else {
      throw new Error(data.error || '生成失败');
    }
    
  } catch(error) {
    console.error('生成文书失败:', error);
    alert('生成文书失败，请稍后重试。错误信息：' + error.message);
  } finally {
    // 恢复按钮状态
    const generateBtn = docType === '民事起诉状' ? document.getElementById('lawsuitBtn') : document.getElementById('defenseBtn');
    if(generateBtn) {
      generateBtn.textContent = docType;
      generateBtn.disabled = false;
    }
  }
}

// 选项按钮切换与placeholder动态切换
function updateDocTypeUI(selectedType) {
  const lawsuitBtn = document.getElementById('lawsuitBtn');
  const defenseBtn = document.getElementById('defenseBtn');
  const textarea = document.getElementById('docTextarea');
  if (selectedType === '民事起诉状') {
    lawsuitBtn.classList.add('selected');
    lawsuitBtn.style.background = '#4f7cff';
    lawsuitBtn.style.color = '#fff';
    lawsuitBtn.style.border = 'none';
    defenseBtn.classList.remove('selected');
    defenseBtn.style.background = '#fff';
    defenseBtn.style.color = '#4f7cff';
    defenseBtn.style.border = '2px solid #4f7cff';
    textarea.placeholder = '请简要描述您的案件事实、诉讼请求等信息……';
  } else {
    defenseBtn.classList.add('selected');
    defenseBtn.style.background = '#4f7cff';
    defenseBtn.style.color = '#fff';
    defenseBtn.style.border = 'none';
    lawsuitBtn.classList.remove('selected');
    lawsuitBtn.style.background = '#fff';
    lawsuitBtn.style.color = '#4f7cff';
    lawsuitBtn.style.border = '2px solid #4f7cff';
    textarea.placeholder = '请简要描述您对起诉内容的答辩理由、事实等信息……';
  }
  window.currentDocType = selectedType;
}

function initDocument() {
  // 绑定类型按钮
  const lawsuitBtn = document.getElementById('lawsuitBtn');
  const defenseBtn = document.getElementById('defenseBtn');
  if (lawsuitBtn && defenseBtn) {
    lawsuitBtn.onclick = () => updateDocTypeUI('民事起诉状');
    defenseBtn.onclick = () => updateDocTypeUI('民事答辩状');
  }
  // 绑定生成按钮
  const generateBtn = document.getElementById('generateDocBtn');
  if (generateBtn) {
    generateBtn.onclick = () => {
      generateDocument(window.currentDocType || '民事起诉状');
    };
  }
  // 历史侧边栏
  const historyBtn = document.getElementById('docHistoryBtn');
  if(historyBtn) {
    historyBtn.onclick = () => {
      const sidebar = document.getElementById('documentHistorySidebar');
      if(sidebar) {
        const isOpen = sidebar.style.right === '0px';
        sidebar.style.right = isOpen ? '-300px' : '0px';
      }
    };
  }
  // 弹窗关闭
  const popup = document.getElementById('documentPopup');
  if(popup) {
    popup.addEventListener('click', function(e) {
      if(e.target === this) {
        closeDocumentPopup();
      }
    });
  }
  // 初始化历史
  renderDocumentHistory();
  // 默认选中起诉状
  window.currentDocType = '民事起诉状';
  updateDocTypeUI('民事起诉状');
}

document.addEventListener('DOMContentLoaded', function() {
  initDocument();
}); 