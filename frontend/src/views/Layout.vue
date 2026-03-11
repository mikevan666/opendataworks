<template>
  <el-container class="layout-container">
    <el-header height="60px">
      <div class="header-wrapper">
        <div class="logo">
          <picture class="logo-icon">
            <source srcset="/opendataworks-icon-dark.svg" media="(prefers-color-scheme: dark)">
            <img src="/opendataworks-icon-light.svg" alt="OpenDataWorks 图标">
          </picture>
          <h2>数据门户</h2>
          <el-tag v-if="isDemoMode" size="small" effect="dark" class="demo-tag">演示环境</el-tag>
        </div>
        <el-menu
          :default-active="activeMenu"
          router
          mode="horizontal"
          class="menu"
        >
          <el-menu-item v-for="item in menuItems" :key="item.index" :index="item.index">
            <el-icon><component :is="item.icon" /></el-icon>
            <span>{{ item.label }}</span>
          </el-menu-item>
        </el-menu>
      </div>
    </el-header>

    <el-main>
      <router-view />
    </el-main>
  </el-container>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { DataBoard, DataLine, Connection, Collection, Warning, Setting, Share, Link, Message } from '@element-plus/icons-vue'
import { isDemoMode } from '@/demo/runtime'

const route = useRoute()
const menuItems = computed(() => {
  const items = [
    { index: '/dashboard', label: '控制台', icon: DataBoard },
    { index: '/intelligent-query', label: '智能问数', icon: Message },
    { index: '/datastudio', label: 'Data Studio', icon: DataLine },
    { index: '/workflows', label: '任务调度', icon: Share },
    { index: '/domains', label: '数据建模', icon: Collection },
    { index: '/lineage', label: '数据血缘', icon: Connection },
    { index: '/inspection', label: '数据质量', icon: Warning },
    { index: '/integration', label: '数据集成', icon: Link },
    { index: '/settings', label: '管理员', icon: Setting }
  ]
  if (!isDemoMode) {
    return items
  }
  return items.filter((item) => ['/datastudio', '/workflows', '/lineage'].includes(item.index))
})
const activeMenu = computed(() => {
  const path = route.path
  if (path.startsWith('/dashboard')) {
    return '/dashboard'
  }
  if (path.startsWith('/intelligent-query') || path.startsWith('/nl2sql')) {
    return '/intelligent-query'
  }
  if (path.startsWith('/datastudio')) {
    return '/datastudio'
  }
  if (path.startsWith('/workflows') || path.startsWith('/tasks')) {
    return '/workflows'
  }
  if (path.startsWith('/domains')) {
    return '/domains'
  }
  if (path.startsWith('/lineage')) {
    return '/lineage'
  }
  if (path.startsWith('/inspection')) {
    return '/inspection'
  }
  if (path.startsWith('/integration')) {
    return '/integration'
  }
  if (path.startsWith('/settings')) {
    return '/settings'
  }
  return path
})
</script>

<style scoped>
.layout-container {
  height: 100vh;
  display: flex;
  flex-direction: column;
}

.el-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 0;
  box-shadow: 0 2px 12px rgba(102, 126, 234, 0.15);
  position: relative;
  z-index: 100;
}

.header-wrapper {
  display: flex;
  align-items: center;
  height: 100%;
}

.logo {
  height: 60px;
  min-width: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.1);
  backdrop-filter: blur(10px);
}

.logo-icon {
  width: 44px;
  height: 44px;
  margin-right: 12px;
  display: inline-flex;
}

.logo-icon img {
  width: 100%;
  height: 100%;
}

.logo h2 {
  color: #fff;
  font-size: 20px;
  font-weight: 600;
  margin: 0;
  letter-spacing: 1px;
}

.demo-tag {
  margin-left: 12px;
  border: none;
  background: rgba(255, 255, 255, 0.18);
  color: #fff;
}

.menu {
  flex: 1;
  border: none;
  background: transparent;
}

.el-menu--horizontal {
  border-bottom: none;
}

.el-menu-item {
  color: rgba(255, 255, 255, 0.85);
  border-bottom: none;
  transition: all 0.3s ease;
  font-weight: 500;
}

.el-menu-item:hover {
  background-color: rgba(255, 255, 255, 0.1) !important;
  color: #fff !important;
  border-bottom: none;
  transform: translateY(-2px);
}

.el-menu-item.is-active {
  background-color: rgba(255, 255, 255, 0.15) !important;
  color: #fff !important;
  border-bottom: 3px solid rgba(255, 255, 255, 0.9);
  font-weight: 600;
}

.el-main {
  background-color: #f8fafc;
  padding: 4px;
  flex: 1;
  overflow-y: auto;
  min-height: 0;
}
</style>
