<template>
  <div class="face-recognition-view">
    <el-card class="management-card">
      <template #header>
        <div class="card-header">
          <span>人脸识别管理</span>
          <div>
            <el-button type="primary" @click="showAddPersonDialog">添加人物</el-button>
            <el-button @click="refreshPersons">刷新</el-button>
          </div>
        </div>
      </template>
      
      <el-row :gutter="20" class="controls">
        <el-col :span="8">
          <el-input
            v-model="searchKeyword"
            placeholder="搜索人物姓名"
            clearable
            @keyup.enter="searchPersons"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </el-col>
        <el-col :span="4">
          <el-button type="primary" @click="searchPersons">搜索</el-button>
        </el-col>
      </el-row>
      
      <!-- 人物列表 -->
      <div class="persons-grid">
        <el-card
          v-for="person in persons"
          :key="person.id"
          class="person-card"
          shadow="hover"
          @click="viewPersonDetails(person)"
        >
          <div class="person-avatar">
            <img v-if="person.avatar" :src="person.avatar" :alt="person.name">
            <div v-else class="avatar-placeholder">
              <user-icon />
            </div>
          </div>
          <div class="person-info">
            <div class="person-name">{{ person.name }}</div>
            <div class="person-aliases" v-if="person.aliases && person.aliases.length > 0">
              别名: {{ person.aliases.join(', ') }}
            </div>
            <div class="person-stats">
              <span>相关文件: {{ person.fileCount }}</span>
              <span>识别准确率: {{ (person.accuracy * 100).toFixed(1) }}%</span>
            </div>
          </div>
        </el-card>
      </div>
    </el-card>
    
    <!-- 人物详情对话框 -->
    <el-dialog
      v-model="personDetailsVisible"
      :title="selectedPerson ? selectedPerson.name : '人物详情'"
      width="800px"
    >
      <div v-if="selectedPerson">
        <el-row :gutter="20">
          <el-col :span="8">
            <div class="person-detail-avatar">
              <img v-if="selectedPerson.avatar" :src="selectedPerson.avatar" :alt="selectedPerson.name">
              <div v-else class="avatar-placeholder">
                <user-icon />
              </div>
            </div>
            <div class="person-detail-info">
              <div class="info-item">
                <label>姓名:</label>
                <span>{{ selectedPerson.name }}</span>
              </div>
              <div class="info-item" v-if="selectedPerson.aliases && selectedPerson.aliases.length > 0">
                <label>别名:</label>
                <span>{{ selectedPerson.aliases.join(', ') }}</span>
              </div>
              <div class="info-item">
                <label>文件数量:</label>
                <span>{{ selectedPerson.fileCount }}</span>
              </div>
              <div class="info-item">
                <label>识别准确率:</label>
                <span>{{ (selectedPerson.accuracy * 100).toFixed(1) }}%</span>
              </div>
              <div class="info-item">
                <label>创建时间:</label>
                <span>{{ formatDateTime(selectedPerson.createdAt) }}</span>
              </div>
            </div>
          </el-col>
          <el-col :span="16">
            <div class="face-images-grid">
              <div
                v-for="image in selectedPerson.faceImages"
                :key="image.id"
                class="face-image-item"
              >
                <img :src="image.url" :alt="`人脸图片 ${image.id}`">
                <div class="image-info">
                  <div class="confidence">置信度: {{ (image.confidence * 100).toFixed(1) }}%</div>
                  <div class="actions">
                    <el-button size="small" @click="viewImageDetails(image)">详情</el-button>
                    <el-button size="small" type="danger" @click="deleteFaceImage(image)">删除</el-button>
                  </div>
                </div>
              </div>
            </div>
          </el-col>
        </el-row>
      </div>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="personDetailsVisible = false">关闭</el-button>
          <el-button type="primary" @click="searchByPerson">以此人名搜索</el-button>
        </span>
      </template>
    </el-dialog>
    
    <!-- 添加人物对话框 -->
    <el-dialog
      v-model="addPersonDialogVisible"
      title="添加人物"
      width="600px"
    >
      <el-form :model="newPersonForm" label-width="80px">
        <el-form-item label="姓名">
          <el-input v-model="newPersonForm.name" placeholder="请输入人物姓名"></el-input>
        </el-form-item>
        <el-form-item label="别名">
          <el-input
            v-model="newPersonForm.aliases"
            placeholder="请输入别名，多个别名用逗号分隔"
          ></el-input>
        </el-form-item>
        <el-form-item label="人脸图片">
          <el-upload
            drag
            action="#"
            :auto-upload="false"
            :show-file-list="false"
            @change="handleFaceImageUpload"
          >
            <el-icon class="el-icon--upload"><upload-filled /></el-icon>
            <div class="el-upload__text">
              拖拽人脸图片到此处或 <em>点击上传</em>
            </div>
            <template #tip>
              <div class="el-upload__tip">
                请上传清晰的人脸正面照片，支持 jpg/png 格式
              </div>
            </template>
          </el-upload>
          
          <!-- 预览上传的图片 -->
          <div v-if="newPersonForm.faceImagePreview" class="image-preview">
            <img :src="newPersonForm.faceImagePreview" alt="预览图片">
          </div>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="addPersonDialogVisible = false">取消</el-button>
          <el-button
            type="primary"
            @click="addPerson"
            :loading="addingPerson"
            :disabled="!newPersonForm.name || !newPersonForm.faceImage"
          >
            添加
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ref, reactive } from 'vue'
import { Search, User as UserIcon, UploadFilled } from '@element-plus/icons-vue'
import api from '../utils/api'

export default {
  name: 'FaceRecognitionView',
  components: {
    Search,
    UserIcon,
    UploadFilled
  },
  setup() {
    const searchKeyword = ref('')
    const persons = ref([])
    const personDetailsVisible = ref(false)
    const selectedPerson = ref(null)
    const addPersonDialogVisible = ref(false)
    const addingPerson = ref(false)
    
    // 新人物表单
    const newPersonForm = reactive({
      name: '',
      aliases: '',
      faceImage: null,
      faceImagePreview: null
    })
    
    // 模拟人物数据
    const mockPersons = [
      {
        id: 1,
        name: '张三',
        aliases: ['小张', '张总'],
        avatar: null,
        fileCount: 25,
        accuracy: 0.95,
        createdAt: '2024-01-01T10:00:00Z',
        faceImages: [
          {
            id: 1,
            url: null,
            confidence: 0.98
          },
          {
            id: 2,
            url: null,
            confidence: 0.95
          }
        ]
      },
      {
        id: 2,
        name: '李四',
        aliases: ['李经理'],
        avatar: null,
        fileCount: 18,
        accuracy: 0.92,
        createdAt: '2024-01-02T14:30:00Z',
        faceImages: [
          {
            id: 3,
            url: null,
            confidence: 0.94
          }
        ]
      }
    ]
    
    // 初始化数据
    persons.value = mockPersons
    
    // 搜索人物
    const searchPersons = () => {
      console.log('搜索人物:', searchKeyword.value)
      // 这里应该调用API进行搜索
    }
    
    // 刷新人物列表
    const refreshPersons = () => {
      persons.value = mockPersons
    }
    
    // 查看人物详情
    const viewPersonDetails = (person) => {
      selectedPerson.value = person
      personDetailsVisible.value = true
    }
    
    // 显示添加人物对话框
    const showAddPersonDialog = () => {
      // 重置表单
      newPersonForm.name = ''
      newPersonForm.aliases = ''
      newPersonForm.faceImage = null
      newPersonForm.faceImagePreview = null
      addPersonDialogVisible.value = true
    }
    
    // 人脸图片上传处理
    const handleFaceImageUpload = (file) => {
      newPersonForm.faceImage = file.raw
      // 生成预览URL
      newPersonForm.faceImagePreview = URL.createObjectURL(file.raw)
    }
    
    // 添加人物
    const addPerson = async () => {
      if (!newPersonForm.name || !newPersonForm.faceImage) {
        return
      }
      
      addingPerson.value = true
      
      try {
        // 模拟API调用
        await new Promise(resolve => setTimeout(resolve, 1500))
        
        // 添加到列表
        const aliases = newPersonForm.aliases
          .split(',')
          .map(alias => alias.trim())
          .filter(alias => alias)
          
        const newPerson = {
          id: persons.value.length + 1,
          name: newPersonForm.name,
          aliases: aliases,
          avatar: newPersonForm.faceImagePreview,
          fileCount: 0,
          accuracy: 0.90,
          createdAt: new Date().toISOString(),
          faceImages: [
            {
              id: persons.value.length * 10 + 1,
              url: newPersonForm.faceImagePreview,
              confidence: 0.95
            }
          ]
        }
        
        persons.value.push(newPerson)
        addPersonDialogVisible.value = false
      } catch (error) {
        console.error('添加人物失败:', error)
      } finally {
        addingPerson.value = false
      }
    }
    
    // 删除人脸图片
    const deleteFaceImage = (image) => {
      console.log('删除人脸图片:', image)
    }
    
    // 查看图片详情
    const viewImageDetails = (image) => {
      console.log('查看图片详情:', image)
    }
    
    // 以此人名搜索
    const searchByPerson = () => {
      if (selectedPerson.value) {
        console.log('以此人名搜索:', selectedPerson.value.name)
        personDetailsVisible.value = false
        // 这里应该跳转到搜索页面并执行搜索
      }
    }
    
    // 工具方法
    const formatDateTime = (dateString) => {
      const date = new Date(dateString)
      return date.toLocaleString('zh-CN')
    }
    
    return {
      searchKeyword,
      persons,
      personDetailsVisible,
      selectedPerson,
      addPersonDialogVisible,
      addingPerson,
      newPersonForm,
      searchPersons,
      refreshPersons,
      viewPersonDetails,
      showAddPersonDialog,
      handleFaceImageUpload,
      addPerson,
      deleteFaceImage,
      viewImageDetails,
      searchByPerson,
      formatDateTime
    }
  }
}
</script>

<style scoped>
.face-recognition-view {
  padding: 20px;
}

.management-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.controls {
  margin-top: 20px;
  margin-bottom: 20px;
}

.persons-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 20px;
  margin-top: 20px;
}

.person-card {
  cursor: pointer;
  transition: transform 0.2s;
}

.person-card:hover {
  transform: translateY(-5px);
}

.person-avatar {
  width: 100%;
  height: 150px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #f5f5f5;
  border-radius: 4px;
  margin-bottom: 15px;
}

.person-avatar img {
  max-width: 100%;
  max-height: 100%;
  object-fit: cover;
  border-radius: 4px;
}

.avatar-placeholder {
  font-size: 48px;
  color: #c0c4cc;
}

.person-info {
  text-align: center;
}

.person-name {
  font-size: 18px;
  font-weight: bold;
  margin-bottom: 5px;
}

.person-aliases {
  font-size: 12px;
  color: #606266;
  margin-bottom: 10px;
}

.person-stats {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: #909399;
}

.person-detail-avatar {
  width: 100%;
  height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #f5f5f5;
  border-radius: 4px;
  margin-bottom: 20px;
}

.person-detail-avatar img {
  max-width: 100%;
  max-height: 100%;
  object-fit: cover;
  border-radius: 4px;
}

.person-detail-info {
  padding: 0 10px;
}

.info-item {
  display: flex;
  justify-content: space-between;
  margin-bottom: 10px;
  font-size: 14px;
}

.info-item label {
  font-weight: bold;
  color: #606266;
}

.face-images-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
  gap: 15px;
}

.face-image-item {
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  overflow: hidden;
}

.face-image-item img {
  width: 100%;
  height: 120px;
  object-fit: cover;
}

.image-info {
  padding: 5px;
  font-size: 12px;
}

.confidence {
  color: #606266;
  margin-bottom: 5px;
}

.actions {
  display: flex;
  gap: 5px;
}

.actions .el-button {
  padding: 2px 6px;
  font-size: 12px;
}

.image-preview {
  margin-top: 15px;
  text-align: center;
}

.image-preview img {
  max-width: 100%;
  max-height: 200px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
}
</style>