<template>
  <div class="file-manager-view">
    <el-card class="control-card">
      <template #header>
        <div class="card-header">
          <span>文件管理</span>
          <div>
            <el-button type="primary" @click="refreshFiles">刷新</el-button>
            <el-button @click="showUploadDialog">上传文件</el-button>
          </div>
        </div>
      </template>
      
      <el-row :gutter="20" class="controls">
        <el-col :span="6">
          <el-input
            v-model="searchKeyword"
            placeholder="搜索文件名"
            clearable
            @keyup.enter="searchFiles"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </el-col>
        <el-col :span="4">
          <el-select v-model="fileTypeFilter" placeholder="文件类型" clearable>
            <el-option label="全部" value=""></el-option>
            <el-option label="图片" value="image"></el-option>
            <el-option label="视频" value="video"></el-option>
            <el-option label="音频" value="audio"></el-option>
            <el-option label="文档" value="document"></el-option>
          </el-select>
        </el-col>
        <el-col :span="4">
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            clearable
          />
        </el-col>
        <el-col :span="4">
          <el-button type="primary" @click="searchFiles">搜索</el-button>
        </el-col>
      </el-row>
    </el-card>
    
    <!-- 文件列表 -->
    <el-card class="files-card">
      <template #header>
        <div class="card-header">
          <span>文件列表</span>
          <div>
            <el-tag>总计: {{ fileList.length }} 个文件</el-tag>
          </div>
        </div>
      </template>
      
      <el-table
        :data="fileList"
        style="width: 100%"
        v-loading="loading"
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="55" />
        <el-table-column prop="name" label="文件名" width="250">
          <template #default="scope">
            <div class="file-name-cell">
              <div class="file-icon">
                <img v-if="scope.row.type === 'image'" src="@/assets/icons/image.png" alt="图片">
                <img v-else-if="scope.row.type === 'video'" src="@/assets/icons/video.png" alt="视频">
                <img v-else-if="scope.row.type === 'audio'" src="@/assets/icons/audio.png" alt="音频">
                <img v-else src="@/assets/icons/file.png" alt="文件">
              </div>
              <span>{{ scope.row.name }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="type" label="类型" width="100" />
        <el-table-column prop="size" label="大小" width="120">
          <template #default="scope">
            {{ formatFileSize(scope.row.size) }}
          </template>
        </el-table-column>
        <el-table-column prop="modified" label="修改时间" width="180">
          <template #default="scope">
            {{ formatDateTime(scope.row.modified) }}
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="scope">
            <el-tag :type="getFileStatusType(scope.row.status)">
              {{ getFileStatusText(scope.row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200">
          <template #default="scope">
            <el-button size="small" @click="viewFile(scope.row)">查看</el-button>
            <el-button size="small" type="danger" @click="deleteFile(scope.row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="totalFiles"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>
    
    <!-- 上传对话框 -->
    <el-dialog v-model="uploadDialogVisible" title="上传文件" width="500px">
      <el-upload
        drag
        action="#"
        :auto-upload="false"
        :show-file-list="true"
        :on-change="handleFileChange"
        :on-remove="handleFileRemove"
        multiple
      >
        <el-icon class="el-icon--upload"><upload-filled /></el-icon>
        <div class="el-upload__text">
          拖拽文件到此处或 <em>点击上传</em>
        </div>
        <template #tip>
          <div class="el-upload__tip">
            支持多种文件格式，包括图片、视频、音频等
          </div>
        </template>
      </el-upload>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="uploadDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="uploadFiles" :loading="uploading">上传</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ref, reactive, onMounted } from 'vue'
import { Search, UploadFilled } from '@element-plus/icons-vue'
import api from '../utils/api'

export default {
  name: 'FileManagerView',
  components: {
    Search,
    UploadFilled
  },
  setup() {
    const searchKeyword = ref('')
    const fileTypeFilter = ref('')
    const dateRange = ref('')
    const loading = ref(false)
    const uploadDialogVisible = ref(false)
    const uploading = ref(false)
    const fileList = ref([])
    const selectedFiles = ref([])
    const currentPage = ref(1)
    const pageSize = ref(20)
    const totalFiles = ref(0)
    
    // 模拟文件数据
    const mockFiles = [
      {
        id: 1,
        name: 'vacation_photos.jpg',
        type: 'image',
        size: 2048576,
        modified: '2024-01-15T10:30:00Z',
        status: 'indexed'
      },
      {
        id: 2,
        name: 'meeting_recording.mp4',
        type: 'video',
        size: 104857600,
        modified: '2024-01-14T14:20:00Z',
        status: 'processing'
      },
      {
        id: 3,
        name: 'interview_audio.wav',
        type: 'audio',
        size: 52428800,
        modified: '2024-01-13T09:15:00Z',
        status: 'indexed'
      }
    ]
    
    // 初始化数据
    onMounted(() => {
      loadFiles()
    })
    
    // 加载文件列表
    const loadFiles = () => {
      loading.value = true
      // 模拟API调用
      setTimeout(() => {
        fileList.value = mockFiles
        totalFiles.value = mockFiles.length
        loading.value = false
      }, 500)
    }
    
    // 搜索文件
    const searchFiles = () => {
      console.log('搜索文件:', {
        keyword: searchKeyword.value,
        type: fileTypeFilter.value,
        dateRange: dateRange.value
      })
      loadFiles()
    }
    
    // 刷新文件列表
    const refreshFiles = () => {
      loadFiles()
    }
    
    // 显示上传对话框
    const showUploadDialog = () => {
      uploadDialogVisible.value = true
    }
    
    // 文件选择变化
    const handleSelectionChange = (selection) => {
      selectedFiles.value = selection
    }
    
    // 文件上传处理
    const handleFileChange = (file, fileList) => {
      console.log('文件变化:', file, fileList)
    }
    
    const handleFileRemove = (file, fileList) => {
      console.log('文件移除:', file, fileList)
    }
    
    const uploadFiles = () => {
      uploading.value = true
      // 模拟上传过程
      setTimeout(() => {
        uploading.value = false
        uploadDialogVisible.value = false
        loadFiles() // 重新加载文件列表
      }, 2000)
    }
    
    // 查看文件
    const viewFile = (file) => {
      console.log('查看文件:', file)
    }
    
    // 删除文件
    const deleteFile = (file) => {
      console.log('删除文件:', file)
    }
    
    // 分页处理
    const handleSizeChange = (val) => {
      pageSize.value = val
      loadFiles()
    }
    
    const handleCurrentChange = (val) => {
      currentPage.value = val
      loadFiles()
    }
    
    // 工具方法
    const formatFileSize = (bytes) => {
      if (bytes === 0) return '0 Bytes'
      const k = 1024
      const sizes = ['Bytes', 'KB', 'MB', 'GB']
      const i = Math.floor(Math.log(bytes) / Math.log(k))
      return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
    }
    
    const formatDateTime = (dateString) => {
      const date = new Date(dateString)
      return date.toLocaleString('zh-CN')
    }
    
    const getFileStatusType = (status) => {
      switch (status) {
        case 'indexed': return 'success'
        case 'processing': return 'warning'
        case 'error': return 'danger'
        default: return 'info'
      }
    }
    
    const getFileStatusText = (status) => {
      switch (status) {
        case 'indexed': return '已索引'
        case 'processing': return '处理中'
        case 'error': return '错误'
        default: return '未知'
      }
    }
    
    return {
      searchKeyword,
      fileTypeFilter,
      dateRange,
      loading,
      uploadDialogVisible,
      uploading,
      fileList,
      selectedFiles,
      currentPage,
      pageSize,
      totalFiles,
      loadFiles,
      searchFiles,
      refreshFiles,
      showUploadDialog,
      handleSelectionChange,
      handleFileChange,
      handleFileRemove,
      uploadFiles,
      viewFile,
      deleteFile,
      handleSizeChange,
      handleCurrentChange,
      formatFileSize,
      formatDateTime,
      getFileStatusType,
      getFileStatusText
    }
  }
}
</script>

<style scoped>
.file-manager-view {
  padding: 20px;
}

.control-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.controls {
  margin-top: 20px;
}

.files-card {
  margin-bottom: 20px;
}

.file-name-cell {
  display: flex;
  align-items: center;
}

.file-icon {
  width: 20px;
  height: 20px;
  margin-right: 10px;
}

.file-icon img {
  width: 100%;
  height: 100%;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}
</style>