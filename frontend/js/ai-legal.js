// AI懂法历史侧栏逻辑
function toggleHistorySidebar() {
  document.getElementById('historySidebar').classList.add('open');
  renderHistory();
}

function closeHistorySidebar() {
  document.getElementById('historySidebar').classList.remove('open');
}

function getHistory() {
  return JSON.parse(localStorage.getItem('ai_legal_history') || '[]');
}

function saveHistory(history) {
  localStorage.setItem('ai_legal_history', JSON.stringify(history));
}

function addToHistory(item) {
  const history = getHistory();
  history.unshift(item);
  saveHistory(history);
}

function renderHistory() {
  const list = document.getElementById('historyList');
  const history = getHistory();
  const search = document.getElementById('historySearch').value.trim();
  list.innerHTML = '';
  history.filter(h => !search || h.question.includes(search)).forEach(h => {
    const div = document.createElement('div');
    div.className = 'history-item';
    div.innerText = h.question;
    div.onclick = () => {
      document.getElementById('userInput').value = h.question;
      closeHistorySidebar();
    };
    list.appendChild(div);
  });
}

function fillAndSend(text) {
  document.getElementById('userInput').value = text;
  sendQuestion();
}

let currentModel = '通义千问'; // 统一用后端识别的英文key

function toggleModelMenu() {
  const menu = document.getElementById('modelMenu');
  menu.style.display = (menu.style.display === 'none' || menu.style.display === '') ? 'block' : 'none';
}

function selectModel(model) {
  currentModel = model;
  let showName = model;
  if(model==='通义千问') showName='通义千问';
  if(model==='星火大模型') showName='星火大模型';
  if(model==='deepseek') showName='DeepSeek';
  if(model==='智谱') showName='智谱';
  document.getElementById('currentModel').innerText = '当前模型：' + showName;
  document.getElementById('modelMenu').style.display = 'none';
}

function sendQuestion() {
  const input = document.getElementById('userInput');
  const question = input.value.trim();
  if (!question) return;
  appendChatBubble('user', question);
  input.value = '';
  fetch('http://localhost:8000/ai_legal_qa', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question, model: currentModel })
  })
  .then(res => res.json())
  .then(data => {
    const answer =
      `<strong>法律条文依据：</strong><br>${data.law}<br><br>` +
      `<strong>参考案例：</strong><br>${data.case}<br><br>` +
      `<strong>实际解决办法：</strong><br>${data.solution}<br><br>`+
      `<strong>总结回答：</strong><br>${data.summary}`;
    appendChatBubble('ai', answer);
    addToHistory({ question, answer: data });
  })
  .catch(() => {
    appendChatBubble('ai', '抱歉，服务器暂时无法响应。');
  });
}

function appendChatBubble(role, text) {
  const chat = document.getElementById('chatHistory');
  const div = document.createElement('div');
  div.className = 'chat-bubble ' + role;
  div.innerHTML = text.replace(/\n/g, '<br>');
  chat.appendChild(div);
  chat.scrollTop = chat.scrollHeight;
}

function startNewConversation() {
  document.getElementById('chatHistory').innerHTML = '';
  fetch('http://localhost:8000/reset_ai_memory', { method: 'POST' })
  .then(() => {
    // 可以在这里解锁输入框，允许用户输入新问题
  });
}

// 初始化AI懂法功能
function initAILegal() {
  // 绑定历史搜索事件
  const historySearch = document.getElementById('historySearch');
  if (historySearch) {
    historySearch.oninput = renderHistory;
  }
  
  // 绑定模型菜单点击事件
  document.body.addEventListener('click', function(e) {
    if (!e.target.closest('#modelBtn') && !e.target.closest('#modelMenu')) {
      document.getElementById('modelMenu').style.display = 'none';
    }
  });
  
  // 绑定回车发送事件
  const userInput = document.getElementById('userInput');
  if (userInput) {
    userInput.addEventListener('keydown', function(e) {
      if (e.key === 'Enter') {
        sendQuestion();
      }
    });
  }
}

// 页面加载完成后初始化AI懂法功能
document.addEventListener('DOMContentLoaded', function() {
  initAILegal();
}); 