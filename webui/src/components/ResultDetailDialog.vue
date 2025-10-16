<template>
  <el-dialog
    v-model="visible"
    :title="dialogTitle"
    width="80%"
    :before-close="handleClose"
    class="result-detail-dialog"
  >
    <div class="detail-container">
      <el-row :gutter="20">
        <!-- 左侧预览区域 -->
        <el-col :span="12">
          <div class="preview-section">
            <h4>预览</h4>
            <div class="preview-content">
              <!-- 图片预览 -->
              <div v-if="result.file_type === 'image'" class="image-preview">
                <img :src="previewUrl" :alt="result.file_path" />
              </div>
              
              <!-- 视频预览 -->
              <div v-else-if="result.file_type === 'video'" class="video-preview">
                <TimelinePlayer
                  :title="getFileName(result.file_path)"
                  :video-url="previewUrl"
                  :search-results="relatedResults"
                />
              </div>
              
              <!-- 音频预览 -->
              <div v-else-if="result.file_type === 'audio'" class="audio-preview">
                <audio :src="previewUrl" controls />
                <div class="audio-info">
                  <p>文件: {{ getFileName(result.file_path) }}</p>
                  <p v-if="result.metadata && result.metadata.transcribed_text">
                    转录文本: {{ result.metadata.transcribed_text }}
                  </p>
                </div>
              </div>
              
              <!-- 文本预览 -->
              <div v-else class="text-preview">
                <div class="text-content">
                  {{ previewText || '暂无预览内容' }}
                </div>
              </div>
            </div>
          </div>
        </el-col>
        
        <!-- 右侧信息区域 -->
        <el-col :span="12">
          <div class="info-section">
            <h4>详细信息</h4>
            <el-descriptions :column="1" border>
              <el-descriptions-item label="文件路径">
                {{ result.file_path }}
              </el-descriptions-item>
              <el-descriptions-item label="文件类型">
                {{ result.file_type }}
              </el-descriptions-item>
              <el-descriptions-item label="相似度">
                <el-progress
                  :percentage="result.score * 100"
                  :show-text="false"
                  :stroke-width="6"
                />
                <span class="similarity-text">{{ (result.score * 100).toFixed(1) }}%</span>
              </el-descriptions-item>
              <el-descriptions-item label="时间戳" v-if="result.start_time_ms">
                {{ formatTimestamp(result.start_time_ms) }}
                <span v-if="result.end_time_ms">
                  - {{ formatTimestamp(result.end_time_ms) }}
                </span>
              </el-descriptions-item>
              <el-descriptions-item label="创建时间" v-if="result.created_at">
                {{ formatDateTime(result.created_at) }}
              </el-descriptions-item>
            </el-descriptions>
            
            <!-- 元数据信息 -->
            <div v-if="result.metadata" class="metadata-section">
              <h4>元数据</h4>
              <el-descriptions :column="1" border>
                <el-descriptions-item 
                  v-for="(value, key) in displayMetadata" 
                  :key="key"
                  :label="key"
                >
                  {{ value }}
                </el-descriptions-item>
              </el-descriptions>
            </div>
            
            <!-- 操作按钮 -->
            <div class="action-buttons">
              <el-button type="primary" @click="openFile">打开文件</el-button>
              <el-button @click="openFolder">打开文件夹</el-button>
              <el-button @click="copyPath">复制路径</el-button>
            </div>
          </div>
        </el-col>
      </el-row>
      
      <!-- 相关结果 -->
      <div v-if="relatedResults.length > 0" class="related-results">
        <h4>相关结果</h4>
        <el-row :gutter="15">
          <el-col 
            :span="6" 
            v-for="relatedResult in relatedResults" 
            :key="relatedResult.id"
            class="related-result-item"
          >
            <el-card shadow="hover" @click="switchToResult(relatedResult)">
              <div class="related-thumbnail">
                <img 
                  v-if="relatedResult.file_type === 'image'" 
                  :src="relatedResult.thumbnail" 
                  :alt="relatedResult.file_path"
                >
                <div v-else class="related-placeholder">
                  <video-icon v-if="relatedResult.file_type === 'video'" />
                  <audio-icon v-else-if="relatedResult.file_type === 'audio'" />
                  <image-icon v-else-if="relatedResult.file_type === 'image'" />
                  <document-icon v-else />
                </div>
              </div>
              <div class="related-info">
                <div class="related-title">{{ getFileName(relatedResult.file_path) }}</div>
                <div class="related-score">{{ (relatedResult.score * 100).toFixed(1) }}%</div>
                <div v-if="relatedResult.start_time_ms" class="related-time">
                  {{ formatTimestamp(relatedResult.start_time_ms) }}
                </div>
              </div>
            </el-card>
          </el-col>
        </el-row>
      </div>
    </div>
  </el-dialog>
</template>

<script>
import { ref, computed, watch } from 'vue'
import { Video as VideoIcon, Headset as AudioIcon, Picture as ImageIcon, Document as DocumentIcon } from '@element-plus/icons-vue'
import TimelinePlayer from './TimelinePlayer.vue'

export default {
  name: 'ResultDetailDialog',
  components: {
    VideoIcon,
    AudioIcon,
    ImageIcon,
    DocumentIcon,
    TimelinePlayer
  },
  props: {
    modelValue: {
      type: Boolean,
      default: false
    },
    result: {
      type: Object,
      default: () => ({})
    },
    relatedResults: {
      type: Array,
      default: () => []
    }
  },
  emits: ['update:modelValue', 'switch-result'],
  setup(props, { emit }) {
    const visible = computed({
      get: () => props.modelValue,
      set: (value) => emit('update:modelValue', value)
    })
    
    const dialogTitle = computed(() => {
      return `详情 - ${getFileName(props.result.file_path)}`
    })
    
    const previewUrl = ref('')
    const previewText = ref('')
    
    // 计算显示的元数据
    const displayMetadata = computed(() => {
      if (!props.result.metadata) return {}
      
      const metadata = { ...props.result.metadata }
      // 过滤掉不需要显示的元数据
      const excludeKeys = ['file_id', 'segment_type']
      excludeKeys.forEach(key => delete metadata[key])
      
      return metadata
    })
    
    // 监听结果变化，更新预览
    watch(() => props.result, (newResult) => {
      if (newResult.file_path) {
        updatePreview(newResult)
      }
    }, { immediate: true })
    
    // 更新预览内容
    const updatePreview = async (result) => {
      try {
        // 这里应该调用API获取预览URL或内容
        // 目前使用模拟数据
        
        if (result.file_type === 'image') {
          // 图片预览URL
          previewUrl.value = `/api/v1/files/thumbnail?path=${encodeURIComponent(result.file_path)}`
        } else if (result.file_type === 'video') {
          // 视频预览URL
          previewUrl.value = `/api/v1/files/stream?path=${encodeURIComponent(result.file_path)}`
        } else if (result.file_type === 'audio') {
          // 音频预览URL
          previewUrl.value = `/api/v1/files/stream?path=${encodeURIComponent(result.file_path)}`
        } else if (result.file_type === 'text') {
          // 文本预览内容
          previewText.value = result.metadata?.content || '暂无预览内容'
        }
      } catch (error) {
        console.error('获取预览失败:', error)
      }
    }
    
    // 工具方法
    const getFileName = (filePath) => {
      if (!filePath) return ''
      return filePath.split('/').pop()
    }
    
    const formatTimestamp = (ms) => {
      const totalSeconds = Math.floor(ms / 1000)
      const minutes = Math.floor(totalSeconds / 60)
      const seconds = totalSeconds % 60
      return `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`
    }
    
    const formatDateTime = (dateString) => {
      const date = new Date(dateString)
      return date.toLocaleString('zh-CN')
    }
    
    // 事件处理
    const handleClose = () => {
      visible.value = false
    }
    
    const openFile = () => {
      // 调用系统默认程序打开文件
      console.log('打开文件:', props.result.file_path)
      // 这里应该调用API打开文件
    }
    
    const openFolder = () => {
      // 打开文件所在文件夹
      console.log('打开文件夹:', props.result.file_path)
      // 这里应该调用API打开文件夹
    }
    
    const copyPath = () => {
      // 复制文件路径到剪贴板
      if (navigator.clipboard) {
        navigator.clipboard.writeText(props.result.file_path)
          .then(() => {
            // 显示复制成功提示
            console.log('路径复制成功')
          })
          .catch(err => {
            console.error('复制失败:', err)
          })
      }
    }
    
    const switchToResult = (relatedResult) => {
      emit('switch-result', relatedResult)
    }
    
    return {
      visible,
      dialogTitle,
      previewUrl,
      previewText,
      displayMetadata,
      handleClose,
      openFile,
      openFolder,
      copyPath,
      switchToResult,
      getFileName,
      formatTimestamp,
      formatDateTime
    }
  }
}
</script>

<style scoped>
.result-detail-dialog {
  --el-dialog-padding-primary: 20px;
}

.detail-container {
  max-height: 70vh;
  overflow-y: auto;
}

.preview-section, .info-section, .metadata-section {
  margin-bottom: 20px;
}

.preview-section h4, .info-section h4, .metadata-section h4 {
  margin: 0 0 15px 0;
  font-size: 16px;
  color: #303133;
  border-bottom: 1px solid #e4e7ed;
  padding-bottom: 8px;
}

.preview-content {
  background: #f5f7fa;
  border-radius: 4px;
  padding: 15px;
  min-height: 200px;
}

.image-preview img {
  max-width: 100%;
  max-height: 300px;
  border-radius: 4px;
}

.audio-preview audio {
  width: 100%;
  margin-bottom: 15px;
}

.audio-info p {
  margin: 5px 0;
  font-size: 14px;
  color: #606266;
}

.text-preview {
  height: 300px;
}

.text-content {
  height: 100%;
  padding: 15px;
  background: #fff;
  border-radius: 4px;
  overflow-y: auto;
  white-space: pre-wrap;
  font-family: monospace;
  font-size: 14px;
  line-height: 1.5;
}

.similarity-text {
  margin-left: 10px;
  font-size: 14px;
  color: #606266;
}

.action-buttons {
  margin-top: 20px;
  display: flex;
  gap: 10px;
}

.related-results {
  margin-top: 30px;
  border-top: 1px solid #e4e7ed;
  padding-top: 20px;
}

.related-results h4 {
  margin: 0 0 15px 0;
  font-size: 16px;
  color: #303133;
}

.related-result-item {
  margin-bottom: 15px;
  cursor: pointer;
}

.related-thumbnail {
  height: 80px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #f5f5f5;
  border-radius: 4px;
  margin-bottom: 10px;
}

.related-thumbnail img {
  max-width: 100%;
  max-height: 100%;
  object-fit: cover;
  border-radius: 4px;
}

.related-placeholder {
  font-size: 24px;
  color: #c0c4cc;
}

.related-info {
  text-align: center;
}

.related-title {
  font-size: 12px;
  font-weight: bold;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  margin-bottom: 5px;
}

.related-score {
  font-size: 12px;
  color: #409EFF;
  margin-bottom: 5px;
}

.related-time {
  font-size: 12px;
  color: #909399;
}
</style>