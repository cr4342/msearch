<template>
  <div class="timeline-view">
    <el-card class="search-card">
      <template #header>
        <div class="card-header">
          <span>时间线搜索</span>
        </div>
      </template>
      
      <el-row :gutter="20" class="search-controls">
        <el-col :span="8">
          <el-input
            v-model="searchQuery"
            placeholder="搜索关键词"
            clearable
            @keyup.enter="searchTimeline"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </el-col>
        <el-col :span="6">
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            value-format="YYYY-MM-DD"
            clearable
          />
        </el-col>
        <el-col :span="4">
          <el-select v-model="fileTypes" multiple placeholder="文件类型" clearable>
            <el-option label="图片" value="image"></el-option>
            <el-option label="视频" value="video"></el-option>
            <el-option label="音频" value="audio"></el-option>
          </el-select>
        </el-col>
        <el-col :span="3">
          <el-button type="primary" @click="searchTimeline">搜索</el-button>
        </el-col>
        <el-col :span="3">
          <el-button @click="clearSearch">清空</el-button>
        </el-col>
      </el-row>
    </el-card>
    
    <!-- 时间线视图 -->
    <el-card class="timeline-card">
      <template #header>
        <div class="card-header">
          <span>时间线视图</span>
          <div>
            <el-button @click="zoomIn">放大</el-button>
            <el-button @click="zoomOut">缩小</el-button>
            <el-button @click="resetView">重置</el-button>
          </div>
        </div>
      </template>
      
      <div class="timeline-container" ref="timelineContainer">
        <!-- 时间轴 -->
        <div class="timeline-axis">
          <div 
            v-for="timePoint in timePoints" 
            :key="timePoint.id"
            class="time-point"
            :style="{ left: timePoint.position + '%' }"
          >
            <div class="time-label">{{ timePoint.label }}</div>
            <div class="time-marker"></div>
          </div>
        </div>
        
        <!-- 事件条 -->
        <div class="events-container">
          <div 
            v-for="event in timelineEvents" 
            :key="event.id"
            class="event-bar"
            :class="event.type"
            :style="{
              left: event.startPosition + '%',
              width: event.width + '%',
              top: event.row * 40 + 'px'
            }"
            @click="viewEventDetails(event)"
          >
            <div class="event-content">
              <div class="event-thumbnail">
                <img v-if="event.thumbnail" :src="event.thumbnail" :alt="event.title">
                <div v-else class="placeholder-icon">
                  <video-icon v-if="event.type === 'video'" />
                  <audio-icon v-else-if="event.type === 'audio'" />
                  <image-icon v-else-if="event.type === 'image'" />
                  <document-icon v-else />
                </div>
              </div>
              <div class="event-info">
                <div class="event-title">{{ event.title }}</div>
                <div class="event-time">{{ formatEventTime(event.startTime) }}</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </el-card>
    
    <!-- 搜索结果列表 -->
    <el-card class="results-card">
      <template #header>
        <div class="card-header">
          <span>搜索结果 ({{ searchResults.length }})</span>
        </div>
      </template>
      
      <el-table
        :data="searchResults"
        style="width: 100%"
        v-loading="loading"
        @row-click="viewResultDetails"
      >
        <el-table-column prop="title" label="标题" width="250">
          <template #default="scope">
            <div class="result-title-cell">
              <div class="result-thumbnail">
                <img v-if="scope.row.thumbnail" :src="scope.row.thumbnail" :alt="scope.row.title">
                <div v-else class="placeholder-icon">
                  <video-icon v-if="scope.row.type === 'video'" />
                  <audio-icon v-else-if="scope.row.type === 'audio'" />
                  <image-icon v-else-if="scope.row.type === 'image'" />
                  <document-icon v-else />
                </div>
              </div>
              <span>{{ scope.row.title }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="type" label="类型" width="100" />
        <el-table-column prop="startTime" label="时间" width="180">
          <template #default="scope">
            {{ formatDateTime(scope.row.startTime) }}
          </template>
        </el-table-column>
        <el-table-column prop="similarity" label="相似度" width="120">
          <template #default="scope">
            <el-progress
              :percentage="scope.row.similarity * 100"
              :show-text="false"
              :stroke-width="6"
            />
            <div class="similarity-text">{{ (scope.row.similarity * 100).toFixed(1) }}%</div>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150">
          <template #default="scope">
            <el-button size="small" @click.stop="playMedia(scope.row)">播放</el-button>
            <el-button size="small" type="primary" @click.stop="viewDetails(scope.row)">详情</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script>
import { ref, reactive, onMounted, nextTick } from 'vue'
import { Search, Video as VideoIcon, Headset as AudioIcon, Picture as ImageIcon, Document as DocumentIcon } from '@element-plus/icons-vue'
import api from '../utils/api'

export default {
  name: 'TimelineView',
  components: {
    Search,
    VideoIcon,
    AudioIcon,
    ImageIcon,
    DocumentIcon
  },
  setup() {
    const searchQuery = ref('')
    const dateRange = ref('')
    const fileTypes = ref([])
    const loading = ref(false)
    const timelineContainer = ref(null)
    
    // 模拟时间点数据
    const timePoints = ref([
      { id: 1, label: '01-01', position: 0 },
      { id: 2, label: '01-05', position: 20 },
      { id: 3, label: '01-10', position: 40 },
      { id: 4, label: '01-15', position: 60 },
      { id: 5, label: '01-20', position: 80 },
      { id: 6, label: '01-25', position: 100 }
    ])
    
    // 模拟时间线事件数据
    const timelineEvents = ref([
      {
        id: 1,
        title: '会议记录视频',
        type: 'video',
        startTime: '2024-01-05T10:00:00Z',
        endTime: '2024-01-05T11:30:00Z',
        startPosition: 15,
        width: 25,
        row: 0,
        thumbnail: null
      },
      {
        id: 2,
        title: '项目讨论音频',
        type: 'audio',
        startTime: '2024-01-10T14:00:00Z',
        endTime: '2024-01-10T15:00:00Z',
        startPosition: 35,
        width: 15,
        row: 1,
        thumbnail: null
      },
      {
        id: 3,
        title: '度假照片',
        type: 'image',
        startTime: '2024-01-15T09:00:00Z',
        endTime: '2024-01-15T09:00:00Z',
        startPosition: 55,
        width: 5,
        row: 0,
        thumbnail: null
      }
    ])
    
    // 搜索结果
    const searchResults = ref([
      {
        id: 1,
        title: '项目启动会议.mp4',
        type: 'video',
        startTime: '2024-01-05T10:00:00Z',
        similarity: 0.92,
        thumbnail: null
      },
      {
        id: 2,
        title: '团队讨论录音.wav',
        type: 'audio',
        startTime: '2024-01-10T14:00:00Z',
        similarity: 0.85,
        thumbnail: null
      }
    ])
    
    // 搜索时间线
    const searchTimeline = async () => {
      loading.value = true
      
      try {
        // 准备时间范围参数
        let timeRange = null
        if (dateRange.value && dateRange.value.length === 2) {
          timeRange = {
            start: new Date(dateRange.value[0]).toISOString(),
            end: new Date(dateRange.value[1]).toISOString()
          }
        }
        
        // 调用API进行时间线搜索
        const response = await api.searchTimeline(
          searchQuery.value || undefined,
          timeRange,
          fileTypes.value.length > 0 ? fileTypes.value : undefined,
          50
        )
        
        if (response.success) {
          // 更新搜索结果
          searchResults.value = response.data.results || []
          
          // 更新时间线事件
          updateTimelineEvents(searchResults.value)
        } else {
          console.error('时间线搜索失败:', response.message)
        }
      } catch (error) {
        console.error('时间线搜索失败:', error)
      } finally {
        loading.value = false
      }
    }
    
    // 更新时间线事件
    const updateTimelineEvents = (results) => {
      if (!results || results.length === 0) {
        timelineEvents.value = []
        return
      }
      
      // 找出最早和最晚的时间
      const timestamps = results.map(r => new Date(r.created_at || r.start_time_ms).getTime())
      const minTime = Math.min(...timestamps)
      const maxTime = Math.max(...timestamps)
      const timeRange = maxTime - minTime || 1
      
      // 将结果转换为时间线事件
      const events = results.map((result, index) => {
        const eventTime = new Date(result.created_at || result.start_time_ms).getTime()
        const position = ((eventTime - minTime) / timeRange) * 100
        
        return {
          id: result.id,
          title: getFileName(result.file_path),
          type: result.file_type,
          startTime: result.created_at || new Date(result.start_time_ms).toISOString(),
          endTime: result.created_at || new Date(result.start_time_ms).toISOString(),
          startPosition: position,
          width: Math.max(2, 100 / results.length), // 最小宽度2%
          row: index % 5, // 最多5行
          thumbnail: null,
          score: result.score,
          file_path: result.file_path,
          start_time_ms: result.start_time_ms,
          end_time_ms: result.end_time_ms
        }
      })
      
      timelineEvents.value = events
      
      // 更新时间点标签
      updateTimePoints(minTime, maxTime)
    }
    
    // 更新时间点标签
    const updateTimePoints = (minTime, maxTime) => {
      const startDate = new Date(minTime)
      const endDate = new Date(maxTime)
      const points = []
      
      // 生成5个时间点
      for (let i = 0; i <= 4; i++) {
        const position = (i / 4) * 100
        const time = new Date(minTime + (maxTime - minTime) * (i / 4))
        const label = `${time.getMonth() + 1}-${time.getDate()}`
        
        points.push({
          id: i + 1,
          label,
          position
        })
      }
      
      timePoints.value = points
    }
    
    // 清空搜索
    const clearSearch = () => {
      searchQuery.value = ''
      dateRange.value = ''
      fileTypes.value = []
      searchResults.value = []
    }
    
    // 视图控制
    const zoomIn = () => {
      console.log('放大时间线')
    }
    
    const zoomOut = () => {
      console.log('缩小时间线')
    }
    
    const resetView = () => {
      console.log('重置时间线视图')
    }
    
    // 事件处理
    const viewEventDetails = (event) => {
      // 处理查看事件详情逻辑
      if (event.type === 'video' && event.start_time_ms) {
        // 如果是视频且有时间戳，可以跳转到视频播放器并定位到特定时间
        console.log('跳转到视频时间轴:', event.file_path, event.start_time_ms)
      } else {
        // 其他类型文件的预览
        console.log('预览文件:', event.file_path)
      }
    }
    
    const viewResultDetails = (result) => {
      // 处理查看结果详情逻辑
      if (result.file_type === 'video' && result.start_time_ms) {
        // 如果是视频且有时间戳，可以跳转到视频播放器并定位到特定时间
        console.log('跳转到视频时间轴:', result.file_path, result.start_time_ms)
      } else {
        // 其他类型文件的预览
        console.log('预览文件:', result.file_path)
      }
    }
    
    const playMedia = (item) => {
      // 处理播放媒体逻辑
      if (item.file_type === 'video' && item.start_time_ms) {
        // 如果是视频且有时间戳，可以跳转到视频播放器并定位到特定时间
        console.log('播放视频并定位到时间戳:', item.file_path, item.start_time_ms)
      } else if (item.file_type === 'audio' && item.start_time_ms) {
        // 如果是音频且有时间戳，可以跳转到音频播放器并定位到特定时间
        console.log('播放音频并定位到时间戳:', item.file_path, item.start_time_ms)
      } else {
        // 其他类型文件的预览
        console.log('播放媒体:', item.file_path)
      }
    }
    
    const viewDetails = (item) => {
      // 处理查看详情逻辑
      console.log('查看详情:', item)
    }
    
    // 工具方法
    const formatEventTime = (timeString) => {
      const date = new Date(timeString)
      return `${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`
    }
    
    const formatDateTime = (dateString) => {
      const date = new Date(dateString)
      return date.toLocaleString('zh-CN')
    }
    
    const getFileName = (filePath) => {
      if (!filePath) return ''
      return filePath.split('/').pop()
    }
    
    return {
      searchQuery,
      dateRange,
      fileTypes,
      loading,
      timelineContainer,
      timePoints,
      timelineEvents,
      searchResults,
      searchTimeline,
      clearSearch,
      zoomIn,
      zoomOut,
      resetView,
      viewEventDetails,
      viewResultDetails,
      playMedia,
      viewDetails,
      formatEventTime,
      formatDateTime,
      getFileName
    }
  }
}
</script>

<style scoped>
.timeline-view {
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

.search-controls {
  margin-top: 20px;
}

.timeline-card {
  margin-bottom: 20px;
}

.timeline-container {
  position: relative;
  height: 300px;
  background-color: #f9f9f9;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  overflow: hidden;
}

.timeline-axis {
  position: absolute;
  top: 20px;
  left: 0;
  right: 0;
  height: 20px;
  border-bottom: 1px solid #dcdfe6;
}

.time-point {
  position: absolute;
  transform: translateX(-50%);
}

.time-label {
  font-size: 12px;
  color: #606266;
  text-align: center;
  margin-bottom: 5px;
}

.time-marker {
  width: 2px;
  height: 10px;
  background-color: #409eff;
  margin: 0 auto;
}

.events-container {
  position: absolute;
  top: 50px;
  left: 0;
  right: 0;
  bottom: 0;
  padding: 10px;
}

.event-bar {
  position: absolute;
  height: 30px;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.event-bar:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
}

.event-bar.video {
  background-color: #409eff;
  border-left: 3px solid #1a73e8;
}

.event-bar.audio {
  background-color: #67c23a;
  border-left: 3px solid #4caf50;
}

.event-bar.image {
  background-color: #e6a23c;
  border-left: 3px solid #f56c6c;
}

.event-content {
  display: flex;
  align-items: center;
  height: 100%;
  padding: 0 10px;
  color: white;
  font-size: 12px;
}

.event-thumbnail {
  width: 20px;
  height: 20px;
  margin-right: 8px;
  background-color: rgba(255, 255, 255, 0.2);
  border-radius: 2px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.event-thumbnail img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 2px;
}

.placeholder-icon {
  font-size: 14px;
}

.event-info {
  flex: 1;
  overflow: hidden;
}

.event-title {
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.event-time {
  font-size: 10px;
  opacity: 0.8;
}

.results-card {
  margin-bottom: 20px;
}

.result-title-cell {
  display: flex;
  align-items: center;
}

.result-thumbnail {
  width: 30px;
  height: 30px;
  margin-right: 10px;
  background-color: #f5f5f5;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.result-thumbnail img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 4px;
}

.similarity-text {
  font-size: 12px;
  color: #606266;
  text-align: center;
  margin-top: 2px;
}
</style>