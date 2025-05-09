/**
 * aiGuider Web调试界面
 * 主要用于与后端AI服务进行交互测试
 */

// DOM元素
const chatMessages = document.getElementById('chat-messages');
const chatForm = document.getElementById('chat-form');
const messageInput = document.getElementById('message-input');
const imageUpload = document.getElementById('image-upload');
const imagePreviewContainer = document.getElementById('image-preview-container');
const imagePreview = document.getElementById('image-preview');
const removeImageBtn = document.getElementById('remove-image');
const clearChatBtn = document.getElementById('clear-chat');
const testConnectionBtn = document.getElementById('test-connection');
const serverUrlInput = document.getElementById('server-url');
const statusValue = document.getElementById('status-value');
const timeValue = document.getElementById('time-value');
const errorContainer = document.getElementById('error-container');
const errorMessage = document.getElementById('error-message');

// 全局变量
let selectedImage = null;
let conversationHistory = [];
let isConnected = false;
let pollingInterval = null;
let sessionId = null;
const API_POLLING_INTERVAL = 20000; // 轮询间隔，毫秒

// 初始化
function init() {
    loadConversationHistory();
    setupEventListeners();
    initSession();
    testConnection();
}

// 设置事件监听器
function setupEventListeners() {
    // 发送消息
    chatForm.addEventListener('submit', (e) => {
        console.log('[Event] 提交聊天表单');
        handleChatSubmit(e);
    });

    // 图片上传
    imageUpload.addEventListener('change', (e) => {
        console.log('[Event] 上传图片');
        handleImageUpload(e);
    });

    // 移除图片
    removeImageBtn.addEventListener('click', (e) => {
        console.log('[Event] 移除图片');
        handleRemoveImage(e);
    });

    // 清除对话
    clearChatBtn.addEventListener('click', async (e) => {
        console.log('[Event] 清除对话');
        await handleClearChat(e);
    });

    // 测试连接
    testConnectionBtn.addEventListener('click', (e) => {
        console.log('[Event] 测试连接');
        testConnection(e);
    });
}

// 初始化会话
async function initSession() {
    console.log('[会话] 初始化会话流程开始');
    // 从localStorage获取会话ID
    sessionId = localStorage.getItem('aiGuider_session_id');
    console.log('[会话] 当前存储的sessionId:', sessionId);

    // 如果没有会话ID，创建新会话
    if (!sessionId) {
        try {
            const apiUrl = serverUrlInput.value.trim();
            console.log('[API] 创建新会话请求', { apiUrl });
            const response = await fetch(`${apiUrl}/session/create`, {
                method: 'POST'
            });

            if (response.ok) {
                const data = await response.json();
                sessionId = data.session_id;
                localStorage.setItem('aiGuider_session_id', sessionId);
                console.log('[API] 创建新会话成功:', sessionId);

                // 创建会话成功后开始轮询
                startPolling();
            }
        } catch (error) {
            console.error('[API] 创建会话失败:', error);
        }
    } else {
        console.log('[API] 使用现有会话:', sessionId);
        startPolling();
    }
}

// 处理聊天表单提交
async function handleChatSubmit(e) {
    e.preventDefault();

    const userMessage = messageInput.value.trim();
    const imageToSend = selectedImage; // 捕获提交时的图片状态

    if (!userMessage && !imageToSend) return; // 使用捕获的状态进行检查

    // 添加用户消息到聊天区
    addMessage(userMessage, 'user', imageToSend);

    // 在将消息添加到UI后，立即清除输入框和预览状态
    messageInput.value = '';
    handleRemoveImage(); // 清除 selectedImage 状态和预览

    let typingIndicator = null;
    try {
        // 显示AI正在输入的提示
        typingIndicator = addTypingIndicator();

        // 发送消息到后端 (使用捕获的 imageToSend)
        const response = await sendMessage(userMessage, imageToSend);

        // 成功后移除输入提示
        if (typingIndicator) chatMessages.removeChild(typingIndicator);

        // 添加AI回复到聊天区
        if (response && response.reply) {
            addMessage(response.reply, 'ai');
        }
    } catch (error) {
        // 失败后移除输入提示
        if (typingIndicator && chatMessages.contains(typingIndicator)) {
             chatMessages.removeChild(typingIndicator);
        }
        showError(`发送消息失败: ${error.message}`);
    }
}

// 发送消息到后端
async function sendMessage(text, image = null) {
    console.log('[API] 准备发送消息到后端', { text, image: image ? '有图片' : '无图片' });
    const apiUrl = serverUrlInput.value.trim();
    if (!apiUrl) {
        throw new Error('请输入有效的后端服务地址');
    }

    const formData = new FormData();

    if (text) {
        formData.append('message', text);
    }

    if (image) {
        formData.append('image', image);
    }

    // 添加对话历史
    formData.append('conversation_history', JSON.stringify(conversationHistory));

    const startTime = Date.now();

    try {
        const headers = {};
        if (sessionId) {
            headers['X-Session-ID'] = sessionId;
        }

        console.log('[API] 发送消息会话ID:', sessionId);
        const response = await fetch(`${apiUrl}/chat`, {
            method: 'POST',
            headers: headers,
            body: formData
        });

        const endTime = Date.now();
        updateResponseTime(endTime - startTime);

        if (!response.ok) {
            throw new Error(`HTTP错误 ${response.status}`);
        }

        const data = await response.json();

        // 更新会话ID（如果后端返回了新的会话ID）
        if (data.session_id && data.session_id !== sessionId) {
            sessionId = data.session_id;
            localStorage.setItem('aiGuider_session_id', sessionId);
        }

        // 更新对话历史
        if (text) {
            conversationHistory.push({ role: 'user', content: text });
        }

        if (data.reply) {
            conversationHistory.push({ role: 'assistant', content: data.reply });
        }

        saveConversationHistory();
        return data;
    } catch (error) {
        throw error;
    }
}

// 添加消息到聊天界面
function addMessage(message, sender, image = null) {
    const messageElement = document.createElement('div');
    messageElement.className = `message ${sender}`;

    // 添加文本内容
    if (message) {
        const textElement = document.createElement('div');
        textElement.className = 'message-text';
        textElement.textContent = message;
        messageElement.appendChild(textElement);
    }

    // 添加图片（如果有）
    if (image) {
        const reader = new FileReader();
        reader.onload = function(e) {
            const imgElement = document.createElement('img');
            imgElement.src = e.target.result;
            imgElement.className = 'message-image';
            imgElement.alt = '用户上传的图片';
            messageElement.appendChild(imgElement);
        }
        reader.readAsDataURL(image);
    }

    // 添加时间
    const timeElement = document.createElement('div');
    timeElement.className = 'message-time';
    timeElement.textContent = new Date().toLocaleTimeString();
    messageElement.appendChild(timeElement);

    chatMessages.appendChild(messageElement);

    // 滚动到底部
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// 添加"AI正在输入"的提示
function addTypingIndicator() {
    const typingElement = document.createElement('div');
    typingElement.className = 'message ai typing';

    const dotsElement = document.createElement('div');
    dotsElement.className = 'typing-dots';
    dotsElement.innerHTML = '<span></span><span></span><span></span>';

    typingElement.appendChild(dotsElement);
    chatMessages.appendChild(typingElement);

    // 滚动到底部
    chatMessages.scrollTop = chatMessages.scrollHeight;

    return typingElement;
}

// 处理图片上传
function handleImageUpload(e) {
    const file = e.target.files[0];
    if (!file) return;

    // 检查文件类型
    if (!file.type.startsWith('image/')) {
        showError('请上传图片文件');
        return;
    }

    // 检查文件大小（限制为5MB）
    if (file.size > 5 * 1024 * 1024) {
        showError('图片大小不能超过5MB');
        return;
    }

    selectedImage = file;

    // 显示图片预览
    const reader = new FileReader();
    reader.onload = function(e) {
        imagePreview.src = e.target.result;
        imagePreviewContainer.classList.remove('hidden');
    }
    reader.readAsDataURL(file);
}

// 移除上传的图片
function handleRemoveImage() {
    selectedImage = null;
    imageUpload.value = '';
    imagePreview.src = '';
    imagePreviewContainer.classList.add('hidden');
}

// 清除对话
async function handleClearChat(e) {
    // 确认框
    if (confirm('确定要清除所有对话记录吗？')) {
        chatMessages.innerHTML = '';
        conversationHistory = [];
        saveConversationHistory();

        // 重置会话ID并重新初始化
        sessionId = null;
        localStorage.removeItem('aiGuider_session_id');
        console.log('[会话] 已清除旧会话ID');

        // 创建新会话
        await initSession();

        // 清除后重新启动轮询
        if (isConnected && sessionId) {
            startPolling();
        }
    }
}

// 测试后端连接
async function testConnection() {
    const apiUrl = serverUrlInput.value.trim();
    if (!apiUrl) {
        updateConnectionStatus(false);
        showError('请输入有效的后端服务地址');
        return;
    }

    try {
        const startTime = Date.now();
        const response = await fetch(`${apiUrl}/health`, {
            method: 'GET'
        });
        const endTime = Date.now();

        if (response.ok) {
            updateConnectionStatus(true);
            updateResponseTime(endTime - startTime);
            hideError();

            // 如果连接成功但尚未初始化会话，则初始化会话
            if (!sessionId) {
                await initSession();
            }

            // 确保轮询已启动
            if (isConnected && !pollingInterval) {
                startPolling();
            }
        } else {
            updateConnectionStatus(false);
            showError(`连接失败: HTTP ${response.status}`);
        }
    } catch (error) {
        updateConnectionStatus(false);
        showError(`连接失败: ${error.message}`);
    }
}

// 更新连接状态显示
function updateConnectionStatus(connected) {
    isConnected = connected;
    statusValue.textContent = connected ? '已连接' : '未连接';
    statusValue.className = connected ? 'status-value connected' : 'status-value disconnected';

    // 连接断开时停止轮询
    if (!connected && pollingInterval) {
        clearInterval(pollingInterval);
        pollingInterval = null;
    }
}

// 更新响应时间显示
function updateResponseTime(timeMs) {
    timeValue.textContent = `${timeMs}ms`;
}

// 显示错误信息
function showError(message) {
    errorMessage.textContent = message;
    errorContainer.classList.remove('hidden');

    // 5秒后自动隐藏
    setTimeout(() => {
        hideError();
    }, 5000);
}

// 隐藏错误信息
function hideError() {
    errorContainer.classList.add('hidden');
}

// 保存对话历史到localStorage
function saveConversationHistory() {
    // 限制对话历史长度
    if (conversationHistory.length > 50) {
        conversationHistory = conversationHistory.slice(-50);
    }

    localStorage.setItem('aiGuider_conversation', JSON.stringify(conversationHistory));
}

// 从localStorage加载对话历史
function loadConversationHistory() {
    const savedHistory = localStorage.getItem('aiGuider_conversation');
    if (savedHistory) {
        try {
            conversationHistory = JSON.parse(savedHistory);

            // 恢复聊天界面
            conversationHistory.forEach(item => {
                if (item.role === 'user') {
                    addMessage(item.content, 'user');
                } else if (item.role === 'assistant') {
                    addMessage(item.content, 'ai');
                }
            });
        } catch (error) {
            console.error('加载对话历史失败:', error);
            conversationHistory = [];
        }
    }
}

// 开始轮询后端主动消息
function startPolling() {
    // 清除现有轮询
    if (pollingInterval) {
        clearInterval(pollingInterval);
        pollingInterval = null;
    }

    // 仅在连接有效时启动新轮询
    if (isConnected && sessionId) {
        pollingInterval = setInterval(async () => {
            try {
                const apiUrl = serverUrlInput.value.trim();
                const headers = {};

                if (sessionId) {
                    headers['X-Session-ID'] = sessionId;
                }

                console.log('[轮询] 请求消息接口', { time: new Date().toISOString(), sessionId });
                const response = await fetch(`${apiUrl}/messages`, {
                    method: 'GET',
                    headers: headers
                });
                console.log('[轮询] 收到响应', { status: response.status });

                if (response.ok) {
                    const data = await response.json();

                    if (data.messages && data.messages.length > 0) {
                        console.log('[轮询] 收到消息', {
                            count: data.messages.length,
                            sample: data.messages[0].content.substring(0, 50)
                        });
                        // 处理后端主动发送的消息
                        data.messages.forEach(msg => {
                            addMessage(msg.content, 'ai');
                            conversationHistory.push({ role: 'assistant', content: msg.content });
                        });

                        saveConversationHistory();
                    } else {
                        console.log('[轮询] 没有新消息');
                    }
                } else if (response.status === 404) {
                    // 会话不存在或已过期，需要创建新会话
                    console.warn('[轮询] 会话ID无效或已过期，重新初始化会话');
                    // 清除本地存储的会话ID
                    localStorage.removeItem('aiGuider_session_id');
                    sessionId = null;
                    // 重新初始化会话
                    await initSession();
                } else if (response.status === 400) {
                    // 未提供会话ID
                    console.warn('[轮询] 未提供会话ID，重新初始化会话');
                    // 重新初始化会话
                    await initSession();
                } else {
                    console.error('[轮询] 请求失败', { status: response.status });
                }
            } catch (error) {
                console.error('轮询消息失败:', error);
            }
        }, API_POLLING_INTERVAL);
    }
}

// 启动
document.addEventListener('DOMContentLoaded', init);
