import axios from 'axios'

// 创建axios实例
const api = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
api.interceptors.request.use(
  config => {
    // 可以在这里添加认证token等
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  response => {
    return response.data
  },
  error => {
    console.error('API请求错误:', error)
    return Promise.reject(error)
  }
)

// API方法
export default {
  // 健康检查
  healthCheck() {
    return api.get('/health')
  },
  
  // 文本搜索
  searchText(query, limit = 20) {
    return api.post('/search/text', { query, limit })
  },
  
  // 图像搜索
  searchImage(file) {
    const formData = new FormData()
    formData.append('file', file)
    return api.post('/search/image', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },
  
  // 音频搜索
  searchAudio(file) {
    const formData = new FormData()
    formData.append('file', file)
    return api.post('/search/audio', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },
  
  // 视频搜索
  searchVideo(file) {
    const formData = new FormData()
    formData.append('file', file)
    return api.post('/search/video', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },
  
  // 多模态搜索
  searchMultimodal(data) {
    const formData = new FormData()
    
    if (data.query_text) {
      formData.append('query_text', data.query_text)
    }
    
    if (data.image_file) {
      formData.append('image_file', data.image_file)
    }
    
    if (data.audio_file) {
      formData.append('audio_file', data.audio_file)
    }
    
    if (data.video_file) {
      formData.append('video_file', data.video_file)
    }
    
    if (data.limit) {
      formData.append('limit', data.limit)
    }
    
    return api.post('/search/multimodal', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },
  
  // 时间线搜索
  searchTimeline(query, timeRange, fileTypes, limit = 20) {
    return api.post('/search/timeline', {
      query,
      time_range: timeRange,
      file_types: fileTypes,
      limit
    })
  },
  
  // 获取系统状态
  getSystemStatus() {
    return api.get('/system/status')
  },
  
  // 获取系统配置
  getSystemConfig() {
    return api.get('/config')
  },
  
  // 更新系统配置
  updateSystemConfig(config) {
    return api.put('/config', config)
  },
  
  // 系统重置
  systemReset(resetType = 'all') {
    return api.post('/system/reset', { reset_type: resetType })
  },
  
  // 获取文件监控状态
  getMonitoringStatus() {
    return api.get('/monitoring/status')
  },
  
  // 启动文件监控
  startMonitoring() {
    return api.post('/monitoring/start')
  },
  
  // 停止文件监控
  stopMonitoring() {
    return api.post('/monitoring/stop')
  },
  
  // 人脸识别API
  // 获取所有人名列表
  getFacePersons() {
    return api.get('/face/persons')
  },
  
  // 添加人物到人脸库
  addPersonToFaceDatabase(formData) {
    return api.post('/face/persons', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },
  
  // 人脸搜索
  searchFaces(file) {
    const formData = new FormData()
    formData.append('image_file', file)
    return api.post('/face/search', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  }
}