<template>
  <div class="config-view">
    <el-tabs v-model="activeTab" class="config-tabs">
      <!-- 系统配置 -->
      <el-tab-pane label="系统配置" name="system">
        <el-card class="config-card">
          <template #header>
            <div class="card-header">
              <span>系统配置</span>
              <el-button type="primary" @click="saveSystemConfig" :loading="saving">保存配置</el-button>
            </div>
          </template>
          
          <el-form :model="systemConfig" label-width="120px">
            <el-form-item label="硬件模式">
              <el-radio-group v-model="systemConfig.hardware_mode">
                <el-radio label="cpu">CPU模式</el-radio>
                <el-radio label="openvino">OpenVINO模式</el-radio>
                <el-radio label="cuda">CUDA模式</el-radio>
              </el-radio-group>
              <div class="form-tip">选择适合您硬件的推理模式</div>
            </el-form-item>
            
            <el-form-item label="监控目录">
              <div class="directory-list">
                <div 
                  v-for="(dir, index) in systemConfig.watch_directories" 
                  :key="index"
                  class="directory-item"
                >
                  <el-input v-model="systemConfig.watch_directories[index]" placeholder="目录路径">
                    <template #append>
                      <el-button @click="selectDirectory(index)">选择</el-button>
                      <el-button @click="removeDirectory(index)" :icon="Delete">删除</el-button>
                    </template>
                  </el-input>
                </div>
                <el-button @click="addDirectory" :icon="Plus">添加目录</el-button>
              </div>
              <div class="form-tip">添加需要监控的目录，系统将自动索引新文件</div>
            </el-form-item>
            
            <el-form-item label="数据库路径">
              <el-input v-model="systemConfig.sqlite_db_path" placeholder="SQLite数据库文件路径">
                <template #append>
                  <el-button @click="selectDatabasePath">选择</el-button>
                </template>
              </el-input>
              <div class="form-tip">SQLite数据库文件存储路径</div>
            </el-form-item>
            
            <el-form-item label="日志级别">
              <el-select v-model="systemConfig.log_level" placeholder="选择日志级别">
                <el-option label="DEBUG" value="DEBUG"></el-option>
                <el-option label="INFO" value="INFO"></el-option>
                <el-option label="WARNING" value="WARNING"></el-option>
                <el-option label="ERROR" value="ERROR"></el-option>
              </el-select>
              <div class="form-tip">系统日志记录级别</div>
            </el-form-item>
          </el-form>
        </el-card>
      </el-tab-pane>
      
      <!-- 搜索配置 -->
      <el-tab-pane label="搜索配置" name="search">
        <el-card class="config-card">
          <template #header>
            <div class="card-header">
              <span>搜索配置</span>
              <el-button type="primary" @click="saveSearchConfig" :loading="saving">保存配置</el-button>
            </div>
          </template>
          
          <el-form :model="searchConfig" label-width="120px">
            <el-form-item label="默认结果数">
              <el-input-number v-model="searchConfig.default_results" :min="1" :max="100" />
              <div class="form-tip">每次搜索返回的默认结果数量</div>
            </el-form-item>
            
            <el-form-item label="相似度阈值">
              <el-slider
                v-model="searchConfig.similarity_threshold"
                :min="0"
                :max="1"
                :step="0.01"
                show-input
                :format-tooltip="formatPercentage"
              />
              <div class="form-tip">搜索结果的最低相似度要求</div>
            </el-form-item>
            
            <el-form-item label="多模态权重">
              <div class="weight-settings">
                <div class="weight-item">
                  <label>文本权重:</label>
                  <el-slider
                    v-model="searchConfig.text_weight"
                    :min="0"
                    :max="1"
                    :step="0.01"
                    show-input
                    :format-tooltip="formatPercentage"
                  />
                </div>
                <div class="weight-item">
                  <label>图像权重:</label>
                  <el-slider
                    v-model="searchConfig.image_weight"
                    :min="0"
                    :max="1"
                    :step="0.01"
                    show-input
                    :format-tooltip="formatPercentage"
                  />
                </div>
                <div class="weight-item">
                  <label>音频权重:</label>
                  <el-slider
                    v-model="searchConfig.audio_weight"
                    :min="0"
                    :max="1"
                    :step="0.01"
                    show-input
                    :format-tooltip="formatPercentage"
                  />
                </div>
              </div>
              <div class="form-tip">多模态搜索时各模态的权重分配</div>
            </el-form-item>
            
            <el-form-item label="智能检索">
              <el-switch v-model="searchConfig.smart_retrieval" />
              <div class="form-tip">启用智能检索，自动识别查询类型并优化搜索策略</div>
            </el-form-item>
          </el-form>
        </el-card>
      </el-tab-pane>
      
      <!-- 人脸识别配置 -->
      <el-tab-pane label="人脸识别" name="face">
        <el-card class="config-card">
          <template #header>
            <div class="card-header">
              <span>人脸识别配置</span>
              <el-button type="primary" @click="saveFaceConfig" :loading="saving">保存配置</el-button>
            </div>
          </template>
          
          <el-form :model="faceConfig" label-width="120px">
            <el-form-item label="启用人脸识别">
              <el-switch v-model="faceConfig.enabled" />
              <div class="form-tip">是否启用人脸识别功能</div>
            </el-form-item>
            
            <el-form-item label="人脸检测阈值">
              <el-slider
                v-model="faceConfig.detection_threshold"
                :min="0"
                :max="1"
                :step="0.01"
                show-input
                :format-tooltip="formatPercentage"
              />
              <div class="form-tip">人脸检测的置信度阈值</div>
            </el-form-item>
            
            <el-form-item label="人脸识别阈值">
              <el-slider
                v-model="faceConfig.recognition_threshold"
                :min="0"
                :max="1"
                :step="0.01"
                show-input
                :format-tooltip="formatPercentage"
              />
              <div class="form-tip">人脸识别的相似度阈值</div>
            </el-form-item>
            
            <el-form-item label="视频采样间隔">
              <el-input-number v-model="faceConfig.video_sample_interval" :min="1" :max="60" />
              <span class="unit">秒</span>
              <div class="form-tip">视频中人脸检测的采样间隔（秒）</div>
            </el-form-item>
          </el-form>
          
          <!-- 人脸库管理 -->
          <el-divider content-position="left">人脸库管理</el-divider>
          
          <div class="face-database-section">
            <el-button type="primary" @click="showPersonDialog">添加人物</el-button>
            <el-button @click="refreshFaceDatabase">刷新</el-button>
            
            <el-table :data="faceDatabase" style="width: 100%; margin-top: 20px;">
              <el-table-column prop="name" label="姓名" width="150" />
              <el-table-column prop="aliases" label="别名" width="200">
                <template #default="scope">
                  {{ Array.isArray(scope.row.aliases) ? scope.row.aliases.join(', ') : scope.row.aliases }}
                </template>
              </el-table-column>
              <el-table-column prop="description" label="描述" />
              <el-table-column label="操作" width="150">
                <template #default="scope">
                  <el-button size="small" @click="editPerson(scope.row)">编辑</el-button>
                  <el-button size="small" type="danger" @click="deletePerson(scope.row)">删除</el-button>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </el-card>
      </el-tab-pane>
      
      <!-- 系统状态 -->
      <el-tab-pane label="系统状态" name="status">
        <el-card class="config-card">
          <template #header>
            <div class="card-header">
              <span>系统状态</span>
              <el-button @click="refreshStatus" :loading="loading">刷新</el-button>
            </div>
          </template>
          
          <el-row :gutter="20">
            <el-col :span="12">
              <el-descriptions title="系统资源" :column="1" border>
                <el-descriptions-item label="CPU使用率">
                  <el-progress :percentage="systemStatus.cpu_usage" :show-text="false" :stroke-width="6" />
                  <span class="status-text">{{ systemStatus.cpu_usage }}</span>
                </el-descriptions-item>
                <el-descriptions-item label="内存使用率">
                  <el-progress :percentage="systemStatus.memory_usage" :show-text="false" :stroke-width="6" />
                  <span class="status-text">{{ systemStatus.memory_usage }}</span>
                </el-descriptions-item>
                <el-descriptions-item label="可用内存">
                  {{ systemStatus.memory_available }}
                </el-descriptions-item>
                <el-descriptions-item label="磁盘使用率">
                  <el-progress :percentage="systemStatus.disk_usage" :show-text="false" :stroke-width="6" />
                  <span class="status-text">{{ systemStatus.disk_usage }}</span>
                </el-descriptions-item>
                <el-descriptions-item label="可用磁盘">
                  {{ systemStatus.disk_available }}
                </el-descriptions-item>
              </el-descriptions>
            </el-col>
            
            <el-col :span="12">
              <el-descriptions title="服务状态" :column="1" border>
                <el-descriptions-item label="API服务">
                  <el-tag type="success">运行中</el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="SQLite数据库">
                  <el-tag :type="systemStatus.sqlite_connected ? 'success' : 'danger'">
                    {{ systemStatus.sqlite_connected ? '已连接' : '未连接' }}
                  </el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="Qdrant向量数据库">
                  <el-tag :type="systemStatus.qdrant_connected ? 'success' : 'danger'">
                    {{ systemStatus.qdrant_connected ? '已连接' : '未连接' }}
                  </el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="文件监控">
                  <el-tag :type="monitoringStatus.running ? 'success' : 'info'">
                    {{ monitoringStatus.running ? '运行中' : '已停止' }}
                  </el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="监控目录数">
                  {{ monitoringStatus.watched_directories }}
                </el-descriptions-item>
                <el-descriptions-item label="已索引文件数">
                  {{ monitoringStatus.indexed_files }}
                </el-descriptions-item>
              </el-descriptions>
            </el-col>
          </el-row>
          
          <div class="status-actions">
            <el-button type="primary" @click="startMonitoring" :disabled="monitoringStatus.running">
              启动文件监控
            </el-button>
            <el-button @click="stopMonitoring" :disabled="!monitoringStatus.running">
              停止文件监控
            </el-button>
            <el-button type="warning" @click="showResetDialog">系统重置</el-button>
          </div>
        </el-card>
      </el-tab-pane>
    </el-tabs>
    
    <!-- 添加/编辑人物对话框 -->
    <el-dialog v-model="personDialogVisible" :title="personDialogTitle" width="500px">
      <el-form :model="personForm" label-width="80px">
        <el-form-item label="姓名">
          <el-input v-model="personForm.name" />
        </el-form-item>
        <el-form-item label="别名">
          <el-input v-model="personForm.aliases" placeholder="多个别名用逗号分隔" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="personForm.description" type="textarea" />
        </el-form-item>
        <el-form-item label="照片">
          <el-upload
            action="#"
            :auto-upload="false"
            :show-file-list="true"
            :on-change="handlePhotoChange"
            :on-remove="handlePhotoRemove"
            multiple
            list-type="picture-card"
          >
            <el-icon><Plus /></el-icon>
          </el-upload>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="personDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="savePerson" :loading="saving">保存</el-button>
        </span>
      </template>
    </el-dialog>
    
    <!-- 系统重置对话框 -->
    <el-dialog v-model="resetDialogVisible" title="系统重置" width="400px">
      <el-alert
        title="警告"
        description="系统重置将删除所有索引数据和配置，请确认是否继续"
        type="warning"
        show-icon
        :closable="false"
      />
      
      <el-form style="margin-top: 20px;">
        <el-form-item label="重置类型">
          <el-radio-group v-model="resetType">
            <el-radio label="all">全部重置</el-radio>
            <el-radio label="database">仅数据库</el-radio>
            <el-radio label="index">仅索引</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="resetDialogVisible = false">取消</el-button>
          <el-button type="danger" @click="resetSystem" :loading="saving">确认重置</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Delete } from '@element-plus/icons-vue'
import api from '../utils/api'

export default {
  name: 'ConfigView',
  components: {
    Plus,
    Delete
  },
  setup() {
    const activeTab = ref('system')
    const saving = ref(false)
    const loading = ref(false)
    
    // 系统配置
    const systemConfig = reactive({
      hardware_mode: 'cpu',
      watch_directories: [''],
      sqlite_db_path: '',
      log_level: 'INFO'
    })
    
    // 搜索配置
    const searchConfig = reactive({
      default_results: 20,
      similarity_threshold: 0.7,
      text_weight: 0.5,
      image_weight: 0.3,
      audio_weight: 0.2,
      smart_retrieval: true
    })
    
    // 人脸识别配置
    const faceConfig = reactive({
      enabled: true,
      detection_threshold: 0.7,
      recognition_threshold: 0.6,
      video_sample_interval: 5
    })
    
    // 系统状态
    const systemStatus = reactive({
      cpu_usage: '0%',
      memory_usage: '0%',
      memory_available: '0 GB',
      disk_usage: '0%',
      disk_available: '0 GB',
      sqlite_connected: false,
      qdrant_connected: false
    })
    
    // 监控状态
    const monitoringStatus = reactive({
      running: false,
      watched_directories: 0,
      indexed_files: 0,
      pending_files: 0
    })
    
    // 人脸库
    const faceDatabase = ref([])
    
    // 人物对话框
    const personDialogVisible = ref(false)
    const personDialogTitle = ref('添加人物')
    const personForm = reactive({
      id: null,
      name: '',
      aliases: '',
      description: '',
      photos: []
    })
    
    // 系统重置对话框
    const resetDialogVisible = ref(false)
    const resetType = ref('all')
    
    // 初始化
    onMounted(() => {
      loadConfigs()
      loadSystemStatus()
      loadMonitoringStatus()
      loadFaceDatabase()
    })
    
    // 加载配置
    const loadConfigs = async () => {
      try {
        const response = await api.getSystemConfig()
        if (response.success) {
          const config = response.data
          
          // 更新系统配置
          systemConfig.hardware_mode = config.hardware_mode || 'cpu'
          systemConfig.watch_directories = config.paths?.watch_directories || ['']
          systemConfig.sqlite_db_path = config.paths?.sqlite_db_path || ''
          systemConfig.log_level = config.system?.log_level || 'INFO'
          
          // 更新搜索配置
          searchConfig.default_results = config.search?.default_results || 20
          searchConfig.similarity_threshold = config.search?.similarity_threshold || 0.7
          searchConfig.text_weight = config.search?.text_weight || 0.5
          searchConfig.image_weight = config.search?.image_weight || 0.3
          searchConfig.audio_weight = config.search?.audio_weight || 0.2
          searchConfig.smart_retrieval = config.search?.smart_retrieval !== false
          
          // 更新人脸识别配置
          faceConfig.enabled = config.face?.enabled !== false
          faceConfig.detection_threshold = config.face?.detection_threshold || 0.7
          faceConfig.recognition_threshold = config.face?.recognition_threshold || 0.6
          faceConfig.video_sample_interval = config.face?.video_sample_interval || 5
        }
      } catch (error) {
        console.error('加载配置失败:', error)
      }
    }
    
    // 保存系统配置
    const saveSystemConfig = async () => {
      saving.value = true
      try {
        const configUpdates = {
          hardware_mode: systemConfig.hardware_mode,
          paths: {
            watch_directories: systemConfig.watch_directories.filter(dir => dir.trim() !== ''),
            sqlite_db_path: systemConfig.sqlite_db_path
          },
          system: {
            log_level: systemConfig.log_level
          }
        }
        
        const response = await api.updateSystemConfig(configUpdates)
        if (response.success) {
          ElMessage.success('系统配置保存成功')
        } else {
          ElMessage.error(`保存失败: ${response.message}`)
        }
      } catch (error) {
        console.error('保存系统配置失败:', error)
        ElMessage.error('保存系统配置失败')
      } finally {
        saving.value = false
      }
    }
    
    // 保存搜索配置
    const saveSearchConfig = async () => {
      saving.value = true
      try {
        const configUpdates = {
          search: {
            default_results: searchConfig.default_results,
            similarity_threshold: searchConfig.similarity_threshold,
            text_weight: searchConfig.text_weight,
            image_weight: searchConfig.image_weight,
            audio_weight: searchConfig.audio_weight,
            smart_retrieval: searchConfig.smart_retrieval
          }
        }
        
        const response = await api.updateSystemConfig(configUpdates)
        if (response.success) {
          ElMessage.success('搜索配置保存成功')
        } else {
          ElMessage.error(`保存失败: ${response.message}`)
        }
      } catch (error) {
        console.error('保存搜索配置失败:', error)
        ElMessage.error('保存搜索配置失败')
      } finally {
        saving.value = false
      }
    }
    
    // 保存人脸识别配置
    const saveFaceConfig = async () => {
      saving.value = true
      try {
        const configUpdates = {
          face: {
            enabled: faceConfig.enabled,
            detection_threshold: faceConfig.detection_threshold,
            recognition_threshold: faceConfig.recognition_threshold,
            video_sample_interval: faceConfig.video_sample_interval
          }
        }
        
        const response = await api.updateSystemConfig(configUpdates)
        if (response.success) {
          ElMessage.success('人脸识别配置保存成功')
        } else {
          ElMessage.error(`保存失败: ${response.message}`)
        }
      } catch (error) {
        console.error('保存人脸识别配置失败:', error)
        ElMessage.error('保存人脸识别配置失败')
      } finally {
        saving.value = false
      }
    }
    
    // 加载系统状态
    const loadSystemStatus = async () => {
      try {
        const response = await api.getSystemStatus()
        if (response.success) {
          Object.assign(systemStatus, response.data)
        }
      } catch (error) {
        console.error('加载系统状态失败:', error)
      }
    }
    
    // 加载监控状态
    const loadMonitoringStatus = async () => {
      try {
        const response = await api.getMonitoringStatus()
        if (response.success) {
          Object.assign(monitoringStatus, response.data)
        }
      } catch (error) {
        console.error('加载监控状态失败:', error)
      }
    }
    
    // 加载人脸库
    const loadFaceDatabase = async () => {
      try {
        const response = await api.getFacePersons()
        if (response.success) {
          faceDatabase.value = response.data || []
        }
      } catch (error) {
        console.error('加载人脸库失败:', error)
      }
    }
    
    // 刷新状态
    const refreshStatus = async () => {
      loading.value = true
      try {
        await Promise.all([
          loadSystemStatus(),
          loadMonitoringStatus()
        ])
      } finally {
        loading.value = false
      }
    }
    
    // 目录管理
    const addDirectory = () => {
      systemConfig.watch_directories.push('')
    }
    
    const removeDirectory = (index) => {
      if (systemConfig.watch_directories.length > 1) {
        systemConfig.watch_directories.splice(index, 1)
      }
    }
    
    const selectDirectory = (index) => {
      // 这里应该调用系统目录选择对话框
      console.log('选择目录:', index)
    }
    
    const selectDatabasePath = () => {
      // 这里应该调用系统文件选择对话框
      console.log('选择数据库路径')
    }
    
    // 监控控制
    const startMonitoring = async () => {
      try {
        const response = await api.startMonitoring()
        if (response.success) {
          ElMessage.success('文件监控已启动')
          await loadMonitoringStatus()
        } else {
          ElMessage.error(`启动失败: ${response.message}`)
        }
      } catch (error) {
        console.error('启动文件监控失败:', error)
        ElMessage.error('启动文件监控失败')
      }
    }
    
    const stopMonitoring = async () => {
      try {
        const response = await api.stopMonitoring()
        if (response.success) {
          ElMessage.success('文件监控已停止')
          await loadMonitoringStatus()
        } else {
          ElMessage.error(`停止失败: ${response.message}`)
        }
      } catch (error) {
        console.error('停止文件监控失败:', error)
        ElMessage.error('停止文件监控失败')
      }
    }
    
    // 人脸库管理
    const showPersonDialog = (person = null) => {
      if (person) {
        personDialogTitle.value = '编辑人物'
        Object.assign(personForm, {
          id: person.id,
          name: person.name,
          aliases: Array.isArray(person.aliases) ? person.aliases.join(', ') : person.aliases,
          description: person.description || '',
          photos: []
        })
      } else {
        personDialogTitle.value = '添加人物'
        Object.assign(personForm, {
          id: null,
          name: '',
          aliases: '',
          description: '',
          photos: []
        })
      }
      personDialogVisible.value = true
    }
    
    const editPerson = (person) => {
      showPersonDialog(person)
    }
    
    const savePerson = async () => {
      saving.value = true
      try {
        const aliases = personForm.aliases ? personForm.aliases.split(',').map(a => a.trim()).filter(a => a) : []
        
        if (personForm.id) {
          // 更新人物
          console.log('更新人物:', personForm.id)
          ElMessage.success('人物信息更新成功')
        } else {
          // 添加人物
          console.log('添加人物:', personForm.name)
          ElMessage.success('人物添加成功')
        }
        
        personDialogVisible.value = false
        await loadFaceDatabase()
      } catch (error) {
        console.error('保存人物失败:', error)
        ElMessage.error('保存人物失败')
      } finally {
        saving.value = false
      }
    }
    
    const deletePerson = async (person) => {
      try {
        await ElMessageBox.confirm(`确定要删除人物 "${person.name}" 吗？`, '确认删除', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        })
        
        console.log('删除人物:', person.id)
        ElMessage.success('人物删除成功')
        await loadFaceDatabase()
      } catch (error) {
        if (error !== 'cancel') {
          console.error('删除人物失败:', error)
          ElMessage.error('删除人物失败')
        }
      }
    }
    
    const refreshFaceDatabase = async () => {
      await loadFaceDatabase()
    }
    
    const handlePhotoChange = (file, fileList) => {
      personForm.photos = fileList
    }
    
    const handlePhotoRemove = (file, fileList) => {
      personForm.photos = fileList
    }
    
    // 系统重置
    const showResetDialog = () => {
      resetDialogVisible.value = true
    }
    
    const resetSystem = async () => {
      saving.value = true
      try {
        const response = await api.systemReset(resetType.value)
        if (response.success) {
          ElMessage.success('系统重置成功')
          resetDialogVisible.value = false
          // 重新加载配置和状态
          await loadConfigs()
          await loadSystemStatus()
          await loadMonitoringStatus()
        } else {
          ElMessage.error(`重置失败: ${response.message}`)
        }
      } catch (error) {
        console.error('系统重置失败:', error)
        ElMessage.error('系统重置失败')
      } finally {
        saving.value = false
      }
    }
    
    // 工具方法
    const formatPercentage = (value) => {
      return `${(value * 100).toFixed(0)}%`
    }
    
    return {
      activeTab,
      saving,
      loading,
      systemConfig,
      searchConfig,
      faceConfig,
      systemStatus,
      monitoringStatus,
      faceDatabase,
      personDialogVisible,
      personDialogTitle,
      personForm,
      resetDialogVisible,
      resetType,
      loadConfigs,
      saveSystemConfig,
      saveSearchConfig,
      saveFaceConfig,
      loadSystemStatus,
      loadMonitoringStatus,
      loadFaceDatabase,
      refreshStatus,
      addDirectory,
      removeDirectory,
      selectDirectory,
      selectDatabasePath,
      startMonitoring,
      stopMonitoring,
      showPersonDialog,
      editPerson,
      savePerson,
      deletePerson,
      refreshFaceDatabase,
      handlePhotoChange,
      handlePhotoRemove,
      showResetDialog,
      resetSystem,
      formatPercentage
    }
  }
}
</script>

<style scoped>
.config-view {
  padding: 20px;
}

.config-tabs {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.config-card {
  margin-top: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 5px;
  line-height: 1.4;
}

.directory-list {
  width: 100%;
}

.directory-item {
  margin-bottom: 10px;
}

.weight-settings {
  width: 100%;
}

.weight-item {
  margin-bottom: 15px;
  display: flex;
  align-items: center;
}

.weight-item label {
  width: 80px;
  margin-right: 15px;
  color: #606266;
}

.unit {
  margin-left: 10px;
  color: #909399;
}

.face-database-section {
  margin-top: 20px;
}

.status-text {
  margin-left: 10px;
  font-size: 14px;
  color: #606266;
}

.status-actions {
  margin-top: 20px;
  text-align: center;
}

.status-actions .el-button {
  margin: 0 10px;
}
</style>