<template>
  <div class="search-view">
    <el-card class="search-card">
      <template #header>
        <div class="card-header">
          <span>多模态搜索</span>
        </div>
      </template>
      
      <el-tabs v-model="activeTab" class="search-tabs">
        <el-tab-pane label="文本搜索" name="text">
          <el-input
            v-model="textQuery"
            placeholder="请输入搜索关键词"
            clearable
            @keyup.enter="searchByText"
          >
            <template #append>
              <el-button :loading="searching" @click="searchByText">搜索</el-button>
            </template>
          </el-input>
        </el-tab-pane>
        
        <el-tab-pane label="图像搜索" name="image">
          <div class="upload-area" @drop.prevent="handleImageDrop" @dragover.prevent>
            <el-upload
              drag
              action="#"
              :auto-upload="false"
              :show-file-list="false"
              @change="handleImageUpload"
            >
              <el-icon class="el-icon--upload"><upload-filled /></el-icon>
              <div class="el-upload__text">
                拖拽图片到此处或 <em>点击上传</em>
              </div>
              <template #tip>
                <div class="el-upload__tip">
                  支持 jpg/png/gif 等图片格式
                </div>
              </template>
            </el-upload>
          </div>
        </el-tab-pane>
        
        <el-tab-pane label="音频搜索" name="audio">
          <div class="upload-area" @drop.prevent="handleAudioDrop" @dragover.prevent>
            <el-upload
              drag
              action="#"
              :auto-upload="false"
              :show-file-list="false"
              @change="handleAudioUpload"
            >
              <el-icon class="el-icon--upload"><upload-filled /></el-icon>
              <div class="el-upload__text">
                拖拽音频到此处或 <em>点击上传</em>
              </div>
              <template #tip>
                <div class="el-upload__tip">
                  支持 mp3/wav/m4a 等音频格式
                </div>
              </template>
            </el-upload>
          </div>
        </el-tab-pane>
        
        <el-tab-pane label="视频搜索" name="video">
          <div class="upload-area" @drop.prevent="handleVideoDrop" @dragover.prevent>
            <el-upload
              drag
              action="#"
              :auto-upload="false"
              :show-file-list="false"
              @change="handleVideoUpload"
            >
              <el-icon class="el-icon--upload"><upload-filled /></el-icon>
              <div class="el-upload__text">
                拖拽视频到此处或 <em>点击上传</em>
              </div>
              <template #tip>
                <div class="el-upload__tip">
                  支持 mp4/avi/mov 等视频格式
                </div>
              </template>
            </el-upload>
          </div>
        </el-tab-pane>
        
        <el-tab-pane label="多模态搜索" name="multimodal">
          <div class="multimodal-search">
            <el-input
              v-model="multimodalQuery.text"
              placeholder="请输入搜索关键词（可选）"
              clearable
            />
            
            <div class="file-upload-section">
              <div class="upload-group">
                <span class="upload-label">图片（可选）:</span>
                <el-upload
                  action="#"
                  :auto-upload="false"
                  :show-file-list="true"
                  :limit="1"
                  @change="handleMultimodalImageUpload"
                >
                  <el-button size="small">选择图片</el-button>
                </el-upload>
              </div>
              
              <div class="upload-group">
                <span class="upload-label">音频（可选）:</span>
                <el-upload
                  action="#"
                  :auto-upload="false"
                  :show-file-list="true"
                  :limit="1"
                  @change="handleMultimodalAudioUpload"
                >
                  <el-button size="small">选择音频</el-button>
                </el-upload>
              </div>
              
              <div class="upload-group">
                <span class="upload-label">视频（可选）:</span>
                <el-upload
                  action="#"
                  :auto-upload="false"
                  :show-file-list="true"
                  :limit="1"
                  @change="handleMultimodalVideoUpload"
                >
                  <el-button size="small">选择视频</el-button>
                </el-upload>
              </div>
            </div>
            
            <div class="search-button-container">
              <el-button type="primary" :loading="searching" @click="searchMultimodal">
                多模态搜索
              </el-button>
            </div>
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-card>
    
    <!-- 搜索结果 -->
    <el-card class="results-card" v-if="searchResults.length > 0">
      <template #header>
        <div class="card-header">
          <span>搜索结果 ({{ searchResults.length }})</span>
          <el-button type="primary" @click="clearResults">清空</el-button>
        </div>
      </template>
      
      <div class="results-container">
        <el-row :gutter="20">
          <el-col 
            :span="6" 
            v-for="result in searchResults" 
            :key="result.id"
            class="result-item"
          >
            <el-card shadow="hover" @click="viewResult(result)">
              <div class="result-thumbnail">
                <img 
                  v-if="result.file_type === 'image'" 
                  :src="result.thumbnail" 
                  :alt="result.file_path"
                >
                <div v-else-if="result.file_type === 'video'" class="video-placeholder">
                  <video-icon />
                </div>
                <div v-else-if="result.file_type === 'audio'" class="audio-placeholder">
                  <audio-icon />
                </div>
                <div v-else class="default-placeholder">
                  <document-icon />
                </div>
              </div>
              <div class="result-info">
                <div class="file-name">{{ getFileName(result.file_path) }}</div>
                <div class="file-type">{{ result.file_type }}</div>
                <div class="similarity">相似度: {{ (result.score * 100).toFixed(1) }}%</div>
                <div v-if="result.start_time_ms" class="timestamp">
                  时间: {{ formatTimestamp(result.start_time_ms) }}
                </div>
              </div>
            </el-card>
          </el-col>
        </el-row>
      </div>
    </el-card>
    
    <!-- 搜索进度 -->
    <el-card class="progress-card" v-if="searching">
      <template #header>
        <div class="card-header">
          <span>搜索中...</span>
        </div>
      </template>
      <el-progress :percentage="progress" :indeterminate="true" />
      <div class="progress-text">正在处理您的搜索请求，请稍候...</div>
    </el-card>
  </div>
</template>

<script>
import { ref, reactive } from 'vue'
import { UploadFilled, Video as VideoIcon, Headset as AudioIcon, Document as DocumentIcon } from '@element-plus/icons-vue'
import api from '../utils/api'

export default {
  name: 'SearchView',
  components: {
    UploadFilled,
    VideoIcon,
    AudioIcon,
    DocumentIcon
  },
  setup() {
    const activeTab = ref('text')
    const textQuery = ref('')
    const searching = ref(false)
    const progress = ref(0)
    const searchResults = ref([])
    
    // 多模态搜索数据
    const multimodalQuery = reactive({
      text: '',
      imageFile: null,
      audioFile: null,
      videoFile: null
    })
    
    // 搜索方法
    const searchByText = async () => {
      if (!textQuery.value.trim()) return
      
      searching.value = true
      progress.value = 0
      
      try {
        const response = await api.searchText(textQuery.value)
        if (response.success) {
          searchResults.value = response.data.results || []
        } else {
          console.error('搜索失败:', response.message)
        }
      } catch (error) {
        console.error('搜索失败:', error)
      } finally {
        searching.value = false
      }
    }
    
    // 文件上传处理
    const handleImageUpload = async (uploadFile) => {
      if (!uploadFile.raw) return
      
      searching.value = true
      progress.value = 0
      
      try {
        const response = await api.searchImage(uploadFile.raw)
        if (response.success) {
          searchResults.value = response.data.results || []
        } else {
          console.error('图片搜索失败:', response.message)
        }
      } catch (error) {
        console.error('图片搜索失败:', error)
      } finally {
        searching.value = false
      }
    }
    
    const handleAudioUpload = async (uploadFile) => {
      if (!uploadFile.raw) return
      
      searching.value = true
      progress.value = 0
      
      try {
        const response = await api.searchAudio(uploadFile.raw)
        if (response.success) {
          searchResults.value = response.data.results || []
        } else {
          console.error('音频搜索失败:', response.message)
        }
      } catch (error) {
        console.error('音频搜索失败:', error)
      } finally {
        searching.value = false
      }
    }
    
    const handleVideoUpload = async (uploadFile) => {
      if (!uploadFile.raw) return
      
      searching.value = true
      progress.value = 0
      
      try {
        const response = await api.searchVideo(uploadFile.raw)
        if (response.success) {
          searchResults.value = response.data.results || []
        } else {
          console.error('视频搜索失败:', response.message)
        }
      } catch (error) {
        console.error('视频搜索失败:', error)
      } finally {
        searching.value = false
      }
    }
    
    // 拖拽处理
    const handleImageDrop = async (e) => {
      e.preventDefault()
      const files = e.dataTransfer.files
      if (files.length === 0) return
      
      const file = files[0]
      if (!file.type.startsWith('image/')) {
        console.error('请上传图片文件')
        return
      }
      
      searching.value = true
      progress.value = 0
      
      try {
        const response = await api.searchImage(file)
        if (response.success) {
          searchResults.value = response.data.results || []
        } else {
          console.error('图片搜索失败:', response.message)
        }
      } catch (error) {
        console.error('图片搜索失败:', error)
      } finally {
        searching.value = false
      }
    }
    
    const handleAudioDrop = async (e) => {
      e.preventDefault()
      const files = e.dataTransfer.files
      if (files.length === 0) return
      
      const file = files[0]
      if (!file.type.startsWith('audio/')) {
        console.error('请上传音频文件')
        return
      }
      
      searching.value = true
      progress.value = 0
      
      try {
        const response = await api.searchAudio(file)
        if (response.success) {
          searchResults.value = response.data.results || []
        } else {
          console.error('音频搜索失败:', response.message)
        }
      } catch (error) {
        console.error('音频搜索失败:', error)
      } finally {
        searching.value = false
      }
    }
    
    const handleVideoDrop = async (e) => {
      e.preventDefault()
      const files = e.dataTransfer.files
      if (files.length === 0) return
      
      const file = files[0]
      if (!file.type.startsWith('video/')) {
        console.error('请上传视频文件')
        return
      }
      
      searching.value = true
      progress.value = 0
      
      try {
        const response = await api.searchVideo(file)
        if (response.success) {
          searchResults.value = response.data.results || []
        } else {
          console.error('视频搜索失败:', response.message)
        }
      } catch (error) {
        console.error('视频搜索失败:', error)
      } finally {
        searching.value = false
      }
    }
    
    // 多模态搜索处理方法
    const handleMultimodalImageUpload = (uploadFile) => {
      multimodalQuery.imageFile = uploadFile.raw
    }
    
    const handleMultimodalAudioUpload = (uploadFile) => {
      multimodalQuery.audioFile = uploadFile.raw
    }
    
    const handleMultimodalVideoUpload = (uploadFile) => {
      multimodalQuery.videoFile = uploadFile.raw
    }
    
    const searchMultimodal = async () => {
      // 检查至少有一个查询条件
      if (!multimodalQuery.text.trim() && 
          !multimodalQuery.imageFile && 
          !multimodalQuery.audioFile && 
          !multimodalQuery.videoFile) {
        console.error('请至少提供一种查询条件')
        return
      }
      
      searching.value = true
      progress.value = 0
      
      try {
        const response = await api.searchMultimodal({
          query_text: multimodalQuery.text || undefined,
          image_file: multimodalQuery.imageFile || undefined,
          audio_file: multimodalQuery.audioFile || undefined,
          video_file: multimodalQuery.videoFile || undefined,
          limit: 20
        })
        
        if (response.success) {
          searchResults.value = response.data.results || []
        } else {
          console.error('多模态搜索失败:', response.message)
        }
      } catch (error) {
        console.error('多模态搜索失败:', error)
      } finally {
        searching.value = false
      }
    }
    
    // 工具方法
    const getFileName = (filePath) => {
      return filePath.split('/').pop()
    }
    
    const formatTimestamp = (ms) => {
      const totalSeconds = Math.floor(ms / 1000)
      const minutes = Math.floor(totalSeconds / 60)
      const seconds = totalSeconds % 60
      return `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`
    }
    
    const clearResults = () => {
      searchResults.value = []
    }
    
    const viewResult = (result) => {
      // 处理查看结果逻辑
      if (result.file_type === 'video') {
        // 如果是视频，可以跳转到时间轴视图
        console.log('跳转到视频时间轴:', result.file_path, result.start_time_ms)
        // 这里可以使用路由跳转到时间轴视图，并传递参数
      } else {
        // 其他类型文件的预览
        console.log('预览文件:', result.file_path)
      }
    }
    
    return {
      activeTab,
      textQuery,
      searching,
      progress,
      searchResults,
      multimodalQuery,
      searchByText,
      handleImageUpload,
      handleAudioUpload,
      handleVideoUpload,
      handleImageDrop,
      handleAudioDrop,
      handleVideoDrop,
      handleMultimodalImageUpload,
      handleMultimodalAudioUpload,
      handleMultimodalVideoUpload,
      searchMultimodal,
      getFileName,
      formatTimestamp,
      clearResults,
      viewResult
    }
  }
}
</script>

<style scoped>
.search-view {
  padding: 20px;
}

.search-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.search-tabs {
  margin-top: 20px;
}

.upload-area {
  padding: 20px 0;
}

.results-card {
  margin-bottom: 20px;
}

.results-container {
  min-height: 200px;
}

.result-item {
  margin-bottom: 20px;
}

.result-thumbnail {
  height: 120px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #f5f5f5;
  border-radius: 4px;
  margin-bottom: 10px;
}

.result-thumbnail img {
  max-width: 100%;
  max-height: 100%;
  object-fit: cover;
}

.result-info {
  text-align: center;
}

.file-name {
  font-weight: bold;
  font-size: 14px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.file-type {
  font-size: 12px;
  color: #999;
  margin: 5px 0;
}

.similarity {
  font-size: 12px;
  color: #409EFF;
}

.timestamp {
  font-size: 12px;
  color: #666;
}

.progress-card {
  margin-top: 20px;
}

.progress-text {
  text-align: center;
  margin-top: 10px;
  color: #666;
}

.multimodal-search {
  padding: 20px 0;
}

.file-upload-section {
  margin: 20px 0;
}

.upload-group {
  display: flex;
  align-items: center;
  margin-bottom: 15px;
}

.upload-label {
  width: 100px;
  font-size: 14px;
  color: #606266;
}

.search-button-container {
  text-align: center;
  margin-top: 20px;
}
</style>