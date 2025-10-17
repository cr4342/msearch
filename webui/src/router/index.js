import { createRouter, createWebHistory } from 'vue-router'
import SearchView from '../views/SearchView.vue'
import FileManagerView from '../views/FileManagerView.vue'
import TimelineView from '../views/TimelineView.vue'
import FaceRecognitionView from '../views/FaceRecognitionView.vue'
import ConfigView from '../views/ConfigView.vue'

const routes = [
  {
    path: '/',
    redirect: '/search'
  },
  {
    path: '/search',
    name: 'Search',
    component: SearchView
  },
  {
    path: '/files',
    name: 'FileManager',
    component: FileManagerView
  },
  {
    path: '/timeline',
    name: 'Timeline',
    component: TimelineView
  },
  {
    path: '/faces',
    name: 'FaceRecognition',
    component: FaceRecognitionView
  },
  {
    path: '/config',
    name: 'Config',
    component: ConfigView
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router