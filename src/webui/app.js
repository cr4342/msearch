// 全局状态
const state = {
    currentPage: 'search',
    searchType: 'text',
    searchResults: [],
    tasks: [],
    files: [],
    systemInfo: {},
    topK: 10,
    threshold: 0.0
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
    updateSearchUI();
});

document.getElementById('search-btn').addEventListener('click', performSearch);

// 滑块控制
document.getElementById('top-k-slider').addEventListener('input', (e) => {
    state.topK = parseInt(e.target.value);
    document.getElementById('top-k-value').textContent = state.topK;
});

document.getElementById('threshold-slider').addEventListener('input', (e) => {
    state.threshold = parseFloat(e.target.value);
    document.getElementById('threshold-value').textContent = state.threshold.toFixed(2);
});

function updateSearchUI() {
    const searchType = state.searchType;
    const textInput = document.getElementById('search-input-text');
    const fileInput = document.getElementById('search-input-file');
    
    if (searchType === 'text') {
        textInput.style.display = 'block';
        fileInput.style.display = 'none';
        textInput.placeholder = '描述你想找的内容...';
    } else if (searchType === 'image') {
        textInput.style.display = 'none';
        fileInput.style.display = 'block';
        fileInput.accept = 'image/*';
    } else if (searchType === 'audio') {
        textInput.style.display = 'none';
        fileInput.style.display = 'block';
        fileInput.accept = 'audio/*';
    }
}

// 辅助函数：获取搜索输入
function getSearchInput() {
    const searchType = state.searchType;
    
    if (searchType === 'text') {
        return {
            type: 'text',
            value: document.getElementById('search-input-text').value.trim()
        };
    } else {
        const fileInput = document.getElementById('search-input-file');
        return {
            type: 'file',
            file: fileInput.files[0]
        };
    }
}

async function performSearch() {
    const searchType = state.searchType;
    
    if (searchType === 'text') {
        await performTextSearch();
    } else if (searchType === 'image') {
        await performImageSearch();
    } else if (searchType === 'audio') {
        await performAudioSearch();
    }
}

async function performTextSearch() {
    const query = document.getElementById('search-input-text').value.trim();
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
            top_k: state.topK,
            threshold: state.threshold
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
    const fileInput = document.getElementById('search-input-file');
    const file = fileInput.files[0];
    
    if (!file) {
        showToast('请选择图像文件', 'warning');
        return;
    }
    
    showLoading(true);
    
    try {
        // 创建FormData
        const formData = new FormData();
        formData.append('file', file);
        
        // 直接使用FormData调用图像搜索API
        const response = await fetch('/api/v1/search/image', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (data.results && data.results.length > 0) {
            state.searchResults = data.results;
            renderSearchResults(data.results);
            showToast(`找到 ${data.results.length} 个结果`, 'success');
        } else {
            state.searchResults = [];
            renderSearchResults([]);
            showToast('未找到相关结果', 'info');
        }
    } catch (error) {
        console.error('图像搜索失败:', error);
        showToast('图像搜索失败: ' + error.message, 'error');
    } finally {
        showLoading(false);
    }
}

async function performAudioSearch() {
    const fileInput = document.getElementById('search-input-file');
    const file = fileInput.files[0];
    
    if (!file) {
        showToast('请选择音频文件', 'warning');
        return;
    }
    
    showLoading(true);
    
    try {
        // 创建FormData
        const formData = new FormData();
        formData.append('file', file);
        
        // 直接使用FormData调用音频搜索API
        const response = await fetch('/api/v1/search/audio', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (data.results && data.results.length > 0) {
            state.searchResults = data.results;
            renderSearchResults(data.results);
            showToast(`找到 ${data.results.length} 个结果`, 'success');
        } else {
            state.searchResults = [];
            renderSearchResults([]);
            showToast('未找到相关结果', 'info');
        }
    } catch (error) {
        console.error('音频搜索失败:', error);
        showToast('音频搜索失败: ' + error.message, 'error');
    } finally {
        showLoading(false);
    }
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
        const response = await fetch('/api/v1/tasks?limit=100');
        const data = await response.json();
        
        if (data.tasks) {
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
    
    const table = document.createElement('table');
    table.className = 'task-table';
    table.innerHTML = `
        <thead>
            <tr>
                <th>任务ID</th>
                <th>类型</th>
                <th>状态</th>
                <th>优先级</th>
                <th>进度</th>
                <th>创建时间</th>
            </tr>
        </thead>
        <tbody>
            ${tasks.map(task => {
                // 处理不同的时间戳格式
                let createdTime;
                if (task.created_at) {
                    if (typeof task.created_at === 'number') {
                        createdTime = new Date(task.created_at * 1000).toLocaleString();
                    } else if (typeof task.created_at === 'string') {
                        createdTime = new Date(task.created_at).toLocaleString();
                    }
                } else {
                    createdTime = '未知';
                }
                
                return `
                    <tr>
                        <td><code>${task.task_id ? task.task_id.substring(0, 8) + '...' : '未知'}</code></td>
                        <td>${task.task_type || '未知'}</td>
                        <td><span class="status-badge status-${task.status}">${task.status}</span></td>
                        <td>${task.priority || 0}</td>
                        <td>
                            <div class="progress-bar">
                                <div class="progress-fill" style="width: ${(task.progress || 0) * 100}%"></div>
                            </div>
                        </td>
                        <td>${createdTime}</td>
                    </tr>
                `;
            }).join('')}
        </tbody>
    `;
    
    container.appendChild(table);
}

// 文件管理
async function refreshFiles() {
    try {
        const response = await fetch('/api/v1/files/list?limit=100');
        const data = await response.json();
        
        if (data.files) {
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
    
    const table = document.createElement('table');
    table.className = 'file-table';
    table.innerHTML = `
        <thead>
            <tr>
                <th>文件名</th>
                <th>类型</th>
                <th>大小</th>
                <th>状态</th>
                <th>创建时间</th>
            </tr>
        </thead>
        <tbody>
            ${files.map(file => `
                <tr>
                    <td>${file.file_name}</td>
                    <td>${file.file_type}</td>
                    <td>${formatFileSize(file.file_size)}</td>
                    <td><span class="status-badge status-${file.indexed ? 'indexed' : 'pending'}">${file.indexed ? '已索引' : '未索引'}</span></td>
                    <td>${new Date(file.created_at).toLocaleString()}</td>
                </tr>
            `).join('')}
        </tbody>
    `;
    
    container.appendChild(table);
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// 系统信息
async function loadSystemInfo() {
    try {
        // 获取系统统计
        const statsResponse = await fetch('/api/v1/system/stats');
        const statsData = await statsResponse.json();
        
        // 获取向量统计
        const vectorResponse = await fetch('/api/v1/vector/stats');
        const vectorData = await vectorResponse.json();
        
        // 获取任务统计
        const taskResponse = await fetch('/api/v1/tasks/stats');
        const taskData = await taskResponse.json();
        
        if (statsData || vectorData || taskData) {
            state.systemInfo = {
                stats: statsData,
                vector: vectorData,
                task: taskData
            };
            renderSystemInfo(statsData, vectorData, taskData);
        }
    } catch (error) {
        console.error('获取系统信息失败:', error);
    }
}

function renderSystemInfo(statsData, vectorData, taskData) {
    // 更新资源使用
    if (statsData && statsData.memory_usage) {
        const memoryPercent = statsData.memory_usage.percent;
        document.getElementById('memory-usage').textContent = `${memoryPercent.toFixed(1)}%`;
        document.getElementById('memory-progress').style.width = `${memoryPercent}%`;
    }
    
    // 更新CPU使用
    if (taskData && taskData.resource_usage) {
        const cpuPercent = taskData.resource_usage.cpu_percent;
        document.getElementById('cpu-usage').textContent = `${cpuPercent.toFixed(1)}%`;
        document.getElementById('cpu-progress').style.width = `${cpuPercent}%`;
    }
    
    // 更新GPU使用
    if (taskData && taskData.resource_usage) {
        const gpuPercent = taskData.resource_usage.gpu_percent;
        document.getElementById('gpu-usage').textContent = `${gpuPercent.toFixed(1)}%`;
        document.getElementById('gpu-progress').style.width = `${gpuPercent}%`;
    }
    
    // 更新向量统计
    if (vectorData) {
        document.getElementById('vector-count').textContent = (vectorData.total_vectors || 0).toLocaleString();
        document.getElementById('vector-dimension').textContent = vectorData.vector_dimension || '未知';
    }
    
    // 更新文件统计
    if (statsData) {
        document.getElementById('file-count').textContent = (statsData.total_files || 0).toLocaleString();
    }
    
    // 更新任务统计
    if (taskData && taskData.task_stats && taskData.task_stats.overall) {
        const overall = taskData.task_stats.overall;
        document.getElementById('stat-total').textContent = overall.total || 0;
        document.getElementById('stat-pending').textContent = overall.pending || 0;
        document.getElementById('stat-running').textContent = overall.running || 0;
        document.getElementById('stat-completed').textContent = overall.completed || 0;
        document.getElementById('stat-failed').textContent = overall.failed || 0;
    }
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

// 刷新按钮
document.getElementById('refresh-tasks-btn').addEventListener('click', refreshTasks);
document.getElementById('refresh-system-btn').addEventListener('click', loadSystemInfo);

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    console.log('msearch WebUI initialized');
    updateSearchUI();
});
