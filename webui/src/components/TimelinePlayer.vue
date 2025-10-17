<template>
  <div class="timeline-player">
    <div class="player-header">
      <h3>{{ title }}</h3>
      <div class="player-controls">
        <el-button @click="play" :icon="PlayIcon" circle />
        <el-button @click="pause" :icon="PauseIcon" circle />
        <el-button @click="stop" :icon="StopIcon" circle />
      </div>
    </div>
    
    <div class="video-container" v-if="videoUrl">
      <video 
        ref="videoRef"
        :src="videoUrl" 
        @timeupdate="handleTimeUpdate"
        @loadedmetadata="handleLoadedMetadata"
        controls
      />
    </div>
    
    <div class="timeline-container">
      <div class="timeline-track" ref="timelineRef" @click="handleTimelineClick">
        <div class="timeline-progress" :style="{ width: progressPercentage + '%' }"></div>
        
        <!-- 时间戳标记 -->
        <div 
          v-for="marker in markers" 
          :key="marker.id"
          class="timeline-marker"
          :style="{ left: getMarkerPosition(marker) + '%' }"
          @click="handleMarkerClick(marker)"
          :class="{ active: isMarkerActive(marker) }"
          :title="marker.description"
        >
          <div class="marker-dot"></div>
          <div class="marker-tooltip" v-if="marker.description">
            {{ marker.description }}
          </div>
        </div>
      </div>
      
      <div class="timeline-scale">
        <div 
          v-for="tick in timelineTicks" 
          :key="tick.time"
          class="scale-tick"
          :style="{ left: (tick.time / duration) * 100 + '%' }"
        >
          {{ formatTime(tick.time) }}
        </div>
      </div>
    </div>
    
    <div class="player-info">
      <span class="current-time">{{ formatTime(currentTime) }}</span>
      <span class="duration">{{ formatTime(duration) }}</span>
    </div>
    
    <!-- 搜索结果列表 -->
    <div class="search-results" v-if="searchResults.length > 0">
      <h4>搜索结果时间点</h4>
      <div class="result-list">
        <div 
          v-for="result in searchResults" 
          :key="result.id"
          class="result-item"
          :class="{ active: isResultActive(result) }"
          @click="jumpToResult(result)"
        >
          <div class="result-time">{{ formatTime(result.start_time_ms / 1000) }}</div>
          <div class="result-score">相似度: {{ (result.score * 100).toFixed(1) }}%</div>
          <div class="result-description" v-if="result.metadata && result.metadata.transcribed_text">
            {{ result.metadata.transcribed_text }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { VideoPlay as PlayIcon, VideoPause as PauseIcon, VideoStop as StopIcon } from '@element-plus/icons-vue'

export default {
  name: 'TimelinePlayer',
  components: {
    PlayIcon,
    PauseIcon,
    StopIcon
  },
  props: {
    title: {
      type: String,
      default: '时间轴播放器'
    },
    videoUrl: {
      type: String,
      default: ''
    },
    markers: {
      type: Array,
      default: () => []
    },
    searchResults: {
      type: Array,
      default: () => []
    }
  },
  setup(props) {
    const videoRef = ref(null)
    const timelineRef = ref(null)
    const currentTime = ref(0)
    const duration = ref(0)
    const isPlaying = ref(false)
    
    // 计算属性
    const progressPercentage = computed(() => {
      return duration.value > 0 ? (currentTime.value / duration.value) * 100 : 0
    })
    
    // 时间轴刻度
    const timelineTicks = computed(() => {
      if (duration.value <= 0) return []
      
      const ticks = []
      const tickCount = 10 // 显示10个刻度
      
      for (let i = 0; i <= tickCount; i++) {
        const time = (duration.value / tickCount) * i
        ticks.push({ time })
      }
      
      return ticks
    })
    
    // 方法
    const play = () => {
      if (videoRef.value) {
        videoRef.value.play()
        isPlaying.value = true
      }
    }
    
    const pause = () => {
      if (videoRef.value) {
        videoRef.value.pause()
        isPlaying.value = false
      }
    }
    
    const stop = () => {
      if (videoRef.value) {
        videoRef.value.pause()
        videoRef.value.currentTime = 0
        currentTime.value = 0
        isPlaying.value = false
      }
    }
    
    const handleTimeUpdate = () => {
      if (videoRef.value) {
        currentTime.value = videoRef.value.currentTime
      }
    }
    
    const handleLoadedMetadata = () => {
      if (videoRef.value) {
        duration.value = videoRef.value.duration
      }
    }
    
    const handleTimelineClick = (event) => {
      if (!timelineRef.value || !videoRef.value) return
      
      const rect = timelineRef.value.getBoundingClientRect()
      const clickX = event.clientX - rect.left
      const percentage = clickX / rect.width
      const targetTime = duration.value * percentage
      
      videoRef.value.currentTime = targetTime
      currentTime.value = targetTime
    }
    
    const getMarkerPosition = (marker) => {
      return duration.value > 0 ? (marker.time / duration.value) * 100 : 0
    }
    
    const handleMarkerClick = (marker) => {
      if (videoRef.value) {
        videoRef.value.currentTime = marker.time
        currentTime.value = marker.time
      }
    }
    
    const isMarkerActive = (marker) => {
      // 检查当前时间是否在标记附近（1秒范围内）
      return Math.abs(currentTime.value - marker.time) < 1
    }
    
    const jumpToResult = (result) => {
      if (videoRef.value && result.start_time_ms) {
        const targetTime = result.start_time_ms / 1000
        videoRef.value.currentTime = targetTime
        currentTime.value = targetTime
        
        // 如果视频未播放，则自动播放
        if (!isPlaying.value) {
          play()
        }
      }
    }
    
    const isResultActive = (result) => {
      if (!result.start_time_ms) return false
      
      const resultTime = result.start_time_ms / 1000
      const resultEndTime = result.end_time_ms ? result.end_time_ms / 1000 : resultTime + 5
      
      // 检查当前时间是否在结果时间范围内
      return currentTime.value >= resultTime && currentTime.value <= resultEndTime
    }
    
    const formatTime = (seconds) => {
      if (!seconds || isNaN(seconds)) return '00:00'
      
      const mins = Math.floor(seconds / 60)
      const secs = Math.floor(seconds % 60)
      return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
    }
    
    return {
      videoRef,
      timelineRef,
      currentTime,
      duration,
      isPlaying,
      progressPercentage,
      timelineTicks,
      play,
      pause,
      stop,
      handleTimeUpdate,
      handleLoadedMetadata,
      handleTimelineClick,
      getMarkerPosition,
      handleMarkerClick,
      isMarkerActive,
      jumpToResult,
      isResultActive,
      formatTime,
      PlayIcon,
      PauseIcon,
      StopIcon
    }
  }
}
</script>

<style scoped>
.timeline-player {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.player-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.player-header h3 {
  margin: 0;
  font-size: 18px;
  color: #303133;
}

.player-controls {
  display: flex;
  gap: 10px;
}

.video-container {
  margin-bottom: 20px;
}

.video-container video {
  width: 100%;
  max-height: 400px;
  border-radius: 4px;
}

.timeline-container {
  margin-bottom: 15px;
}

.timeline-track {
  position: relative;
  height: 12px;
  background: #e4e7ed;
  border-radius: 6px;
  cursor: pointer;
  margin-bottom: 5px;
}

.timeline-progress {
  position: absolute;
  top: 0;
  left: 0;
  height: 100%;
  background: #409eff;
  border-radius: 6px;
  transition: width 0.1s;
}

.timeline-marker {
  position: absolute;
  top: -6px;
  width: 24px;
  height: 24px;
  transform: translateX(-50%);
  cursor: pointer;
  z-index: 2;
}

.timeline-marker:hover .marker-tooltip {
  opacity: 1;
  transform: translateY(-5px);
}

.timeline-marker.active {
  z-index: 3;
}

.marker-dot {
  width: 12px;
  height: 12px;
  background: #f56c6c;
  border-radius: 50%;
  margin: 6px auto;
  border: 2px solid #fff;
  box-shadow: 0 0 0 1px #f56c6c;
}

.timeline-marker.active .marker-dot {
  background: #409eff;
  box-shadow: 0 0 0 1px #409eff;
  transform: scale(1.2);
}

.marker-tooltip {
  position: absolute;
  bottom: 100%;
  left: 50%;
  transform: translateX(-50%);
  background: rgba(0, 0, 0, 0.8);
  color: #fff;
  padding: 5px 10px;
  border-radius: 4px;
  font-size: 12px;
  white-space: nowrap;
  opacity: 0;
  transition: opacity 0.2s, transform 0.2s;
  pointer-events: none;
  margin-bottom: 5px;
}

.timeline-scale {
  position: relative;
  height: 20px;
  border-top: 1px solid #e4e7ed;
}

.scale-tick {
  position: absolute;
  top: 0;
  transform: translateX(-50%);
  font-size: 10px;
  color: #909399;
  white-space: nowrap;
}

.player-info {
  display: flex;
  justify-content: space-between;
  font-size: 14px;
  color: #606266;
  margin-bottom: 20px;
}

.search-results {
  border-top: 1px solid #e4e7ed;
  padding-top: 20px;
}

.search-results h4 {
  margin: 0 0 15px 0;
  font-size: 16px;
  color: #303133;
}

.result-list {
  max-height: 200px;
  overflow-y: auto;
}

.result-item {
  display: flex;
  align-items: center;
  padding: 8px 12px;
  margin-bottom: 5px;
  background: #f5f7fa;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.result-item:hover {
  background: #ecf5ff;
}

.result-item.active {
  background: #ecf5ff;
  border-left: 3px solid #409eff;
}

.result-time {
  font-weight: bold;
  margin-right: 15px;
  color: #409eff;
}

.result-score {
  font-size: 12px;
  color: #909399;
  margin-right: 15px;
}

.result-description {
  flex: 1;
  font-size: 14px;
  color: #606266;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>