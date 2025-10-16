<template>
  <div id="app">
    <el-container style="height: 100vh;">
      <el-header style="background-color: #409EFF; color: white; display: flex; align-items: center; justify-content: space-between;">
        <div style="display: flex; align-items: center;">
          <h1 style="margin: 0;">mSearch</h1>
          <span style="margin-left: 10px; font-size: 14px;">多模态智能检索系统</span>
        </div>
        <div>
          <el-button type="primary" @click="showSettings">设置</el-button>
        </div>
      </el-header>
      
      <el-container>
        <el-aside width="200px" style="background-color: #f5f5f5; padding: 20px;">
          <el-menu
            default-active="1"
            class="el-menu-vertical-demo"
            @select="handleMenuSelect"
          >
            <el-menu-item index="1">
              <el-icon><Search /></el-icon>
              <span>搜索</span>
            </el-menu-item>
            <el-menu-item index="2">
              <el-icon><Document /></el-icon>
              <span>文件管理</span>
            </el-menu-item>
            <el-menu-item index="3">
              <el-icon><VideoCamera /></el-icon>
              <span>时间线</span>
            </el-menu-item>
            <el-menu-item index="4">
              <el-icon><User /></el-icon>
              <span>人脸识别</span>
            </el-menu-item>
            <el-menu-item index="5">
              <el-icon><Setting /></el-icon>
              <span>系统配置</span>
            </el-menu-item>
          </el-menu>
        </el-aside>
        
        <el-main>
          <router-view />
        </el-main>
      </el-container>
    </el-container>
    
    <!-- 设置对话框 -->
    <el-dialog v-model="settingsVisible" title="系统设置" width="600px">
      <el-form :model="settingsForm" label-width="120px">
        <el-form-item label="监控目录">
          <el-input v-model="settingsForm.watchDirectories" type="textarea" placeholder="请输入监控目录，每行一个"></el-input>
        </el-form-item>
        <el-form-item label="硬件模式">
          <el-select v-model="settingsForm.hardwareMode" placeholder="请选择硬件模式">
            <el-option label="CPU" value="cpu"></el-option>
            <el-option label="OpenVINO" value="openvino"></el-option>
            <el-option label="CUDA" value="cuda"></el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="最大结果数">
          <el-input-number v-model="settingsForm.maxResults" :min="1" :max="100"></el-input-number>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="settingsVisible = false">取消</el-button>
          <el-button type="primary" @click="saveSettings">保存</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { Search, Document, VideoCamera, User, Setting } from '@element-plus/icons-vue'

export default {
  name: 'App',
  components: {
    Search,
    Document,
    VideoCamera,
    User,
    Setting
  },
  setup() {
    const router = useRouter()
    const settingsVisible = ref(false)
    const settingsForm = ref({
      watchDirectories: '',
      hardwareMode: 'cpu',
      maxResults: 20
    })

    const showSettings = () => {
      settingsVisible.value = true
    }

    const saveSettings = () => {
      // 保存设置逻辑
      console.log('保存设置:', settingsForm.value)
      settingsVisible.value = false
    }

    const handleMenuSelect = (index) => {
      switch (index) {
        case '1':
          router.push('/search')
          break
        case '2':
          router.push('/files')
          break
        case '3':
          router.push('/timeline')
          break
        case '4':
          router.push('/faces')
          break
        case '5':
          router.push('/config')
          break
        default:
          console.log('未知菜单项:', index)
      }
    }

    return {
      settingsVisible,
      settingsForm,
      showSettings,
      saveSettings,
      handleMenuSelect
    }
  }
}
</script>

<style>
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  color: #2c3e50;
}

.el-header {
  box-shadow: 0 2px 4px rgba(0,0,0,.1);
}
</style>