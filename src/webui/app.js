// 全局状态
const state = {
    currentPage: 'search',
    searchType: 'text',
    searchResults: [],
    tasks: [],
    files: [],
    systemInfo: {}
};

// 页面导航
document.querySelectorAll('.nav-link').forEach(link => {
    link.addEventListener('click', (e) => {
        e.preventDefault();
        const page = e.target.dataset.page;
        navigateTo(page);
    });
});

function navigateTo(page) {
    state.currentPage = page;
    
    // 更新导航状态
    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.remove('active');
        if (link.dataset.page === page) {
            link.classList.add('active');
        }
    });
    
    // 更新页面显示
    document.querySelectorAll('.page').forEach(p => {
        p.classList.remove('active');
    });
    document.getElementById(`page-${page}`).classList.add('active');
    
    // 加载页面数据
    switch(page) {
        case 'search':
            break;
        case 'tasks':
            refreshTasks();
            break;
        case 'files':
            refreshFiles();
            break;
        case 'system':
            loadSystemInfo();
            break;
    }
}

// 搜索功能
document.getElementById('search-type').addEventListener('change', (e) => {
    state.searchType = e.target.value;
});

document.getElementById('search-btn').addEventListener('click', performTextSearch);

async function performTextSearch() {
    const query = document.getElementById('search-input').value.trim();
    if (!query) {
        showToast('请输入搜索内容', 'warning');
        return;
    }
    
    showLoading(true);
    
    try {
        // 根据搜索类型选择不同的 API 端点
        let endpoint = '/api/v1/search/text';
        let requestBody = {
            query: query,
            top_k: 20,
            threshold: 0.0
        };
        
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestBody)
        });
        
        const data = await response.json();
        
        if (data.results && data.results.length > 0) {
            state.searchResults = data.results;
            renderSearchResults(data.results);
        } else {
            state.searchResults = [];
            renderSearchResults([]);
            showToast('未找到相关结果', 'info');
        }
    } catch (error) {
        console.error('搜索失败:', error);
        showToast('搜索失败: ' + error.message, 'error');
    } finally {
        showLoading(false);
    }
}

async function performImageSearch() {
    showToast('图像搜索功能开发中', 'warning');
}

async function performAudioSearch() {
    showToast('音频搜索功能开发中', 'warning');
}

function renderSearchResults(results) {
    const container = document.getElementById('search-results');
    container.innerHTML = '';
    
    if (!results || results.length === 0) {
        container.innerHTML = '<p style="text-align: center; color: #999;">没有找到结果</p>';
        return;
    }
    
    results.forEach(result => {
        const card = document.createElement('div');
        card.className = 'result-card';
        
        const score = result.score || (1 - result._distance);
        const fileName = result.file_name || result.metadata?.file_name || '未知文件';
        const filePath = result.file_path || result.metadata?.file_path || '';
        const thumbnailPath = result.thumbnail_path || result.metadata?.thumbnail_path || '';
        const previewPath = result.preview_path || result.metadata?.preview_path || '';
        const fileType = result.file_type || result.metadata?.file_type || result.modality || 'unknown';
        
        // 判断是否是图像类型
        const isImage = fileType === 'image' || result.modality === 'image' || 
                      fileName.match(/\.(jpg|jpeg|png|gif|bmp|webp)$/i);
        
        // 生成预览图URL
        let previewHtml = '';
        if (isImage && filePath) {
            // 如果是图像文件，直接使用原图作为预览
            previewHtml = `
                <div class="result-preview">
                    <img src="/api/v1/files/preview?path=${encodeURIComponent(filePath)}" 
                         alt="${fileName}" 
                         onerror="this.src='data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxMjAiIGhlaWdodD0iMTIwIiB2aWV3Qm94PSIwIDAgMTIwIDEyMCI+PHJlY3Qgd2lkdGg9IjEyMCIgaGVpZ2h0PSIxMjAiIGZpbGw9IiNjZjZjNmYiLz48dGV4dCB4PSI2MCIgeT0iNjAiIGR5PSI2MCIgZmlsbD0id2hpdGUiIGZvbnQtc2l6ZT0iMTIiIHRleHQtYW5jaG9yPSJtaWRkbGUiPk5vIFByZXZpZXc8L3RleHQ+PC9zdmc+'">
                    <div class="preview-overlay">
                        <span class="preview-type">${fileType.toUpperCase()}</span>
                    </div>
                </div>
            `;
        } else if (thumbnailPath) {
            // 如果有缩略图，使用缩略图
            previewHtml = `
                <div class="result-preview">
                    <img src="/api/v1/files/thumbnail?path=${encodeURIComponent(thumbnailPath)}" 
                         alt="${fileName}" 
                         onerror="this.parentElement.style.display='none'">
                    <div class="preview-overlay">
                        <span class="preview-type">${fileType.toUpperCase()}</span>
                    </div>
                </div>
            `;
        } else {
            // 如果没有预览图，显示占位符
            previewHtml = `
                <div class="result-preview placeholder">
                    <div class="preview-placeholder">
                        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14M14 10l4.586-4.586a2 2 0 012.828 0L4 4" stroke-linecap="round" stroke-linejoin="round"/>
                        </svg>
                        <span class="preview-type">${fileType.toUpperCase()}</span>
                    </div>
                </div>
            `;
        }
        
        card.innerHTML = `
            ${previewHtml}
            <div class="result-info">
                <h4>${fileName}</h4>
                <p class="file-path">${filePath}</p>
                <div class="result-meta">
                    <span class="score">相似度: ${(score * 100).toFixed(2)}%</span>
                    <span class="type">${fileType.toUpperCase()}</span>
                </div>
            </div>
        `;
        
        // 添加点击事件，打开文件
        card.addEventListener('click', () => {
            openFile(filePath);
        });
        
        container.appendChild(card);
    });
}

// 打开文件
function openFile(filePath) {
    if (!filePath) {
        showToast('文件路径不存在', 'warning');
        return;
    }
    
    // 使用API打开文件预览
    window.open(`/api/v1/files/preview?path=${encodeURIComponent(filePath)}`, '_blank');
}

// 任务管理
async function refreshTasks() {
    try {
        const response = await fetch('/api/v1/tasks');
        const data = await response.json();
        
        if (data.success) {
            state.tasks = data.tasks;
            renderTasks(data.tasks);
        }
    } catch (error) {
        console.error('获取任务列表失败:', error);
    }
}

function renderTasks(tasks) {
    const container = document.getElementById('task-list');
    container.innerHTML = '';
    
    if (!tasks || tasks.length === 0) {
        container.innerHTML = '<p style="text-align: center; color: #999;">暂无任务</p>';
        return;
    }
    
    tasks.forEach(task => {
        const item = document.createElement('div');
        item.className = 'task-item';
        item.innerHTML = `
            <span>${task.task_type}</span>
            <span>${task.status}</span>
        `;
        container.appendChild(item);
    });
}

// 文件管理
async function refreshFiles() {
    try {
        const response = await fetch('/api/v1/files');
        const data = await response.json();
        
        if (data.success) {
            state.files = data.files;
            renderFiles(data.files);
        }
    } catch (error) {
        console.error('获取文件列表失败:', error);
    }
}

function renderFiles(files) {
    const container = document.getElementById('file-list');
    container.innerHTML = '';
    
    if (!files || files.length === 0) {
        container.innerHTML = '<p style="text-align: center; color: #999;">暂无文件</p>';
        return;
    }
    
    files.forEach(file => {
        const item = document.createElement('div');
        item.className = 'file-item';
        item.innerHTML = `
            <span>${file.file_name}</span>
            <span>${file.file_type}</span>
        `;
        container.appendChild(item);
    });
}

// 系统信息
async function loadSystemInfo() {
    try {
        const response = await fetch('/api/v1/system/info');
        const data = await response.json();
        
        if (data.success) {
            state.systemInfo = data.info;
            renderSystemInfo(data.info);
        }
    } catch (error) {
        console.error('获取系统信息失败:', error);
    }
}

function renderSystemInfo(info) {
    const container = document.getElementById('system-info');
    container.innerHTML = '';
    
    const stats = [
        { label: '待处理任务', value: info.pending_tasks || 0 },
        { label: '运行中任务', value: info.running_tasks || 0 },
        { label: '已完成任务', value: info.completed_tasks || 0 },
        { label: '失败任务', value: info.failed_tasks || 0 }
    ];
    
    stats.forEach(stat => {
        const card = document.createElement('div');
        card.className = 'stat-card';
        card.innerHTML = `
            <div class="stat-value">${stat.value}</div>
            <div class="stat-label">${stat.label}</div>
        `;
        container.appendChild(card);
    });
}

// UI工具函数
function showLoading(show) {
    const overlay = document.getElementById('loading-overlay');
    if (show) {
        overlay.classList.remove('hidden');
    } else {
        overlay.classList.add('hidden');
    }
}

function showToast(message, type = 'info') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = 'toast';
    toast.classList.add(type);
    toast.classList.remove('hidden');
    
    setTimeout(() => {
        toast.classList.add('hidden');
    }, 3000);
}

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    console.log('msearch WebUI initialized');
});
