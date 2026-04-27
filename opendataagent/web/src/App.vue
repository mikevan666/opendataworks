<template>
  <div class="flex h-screen min-w-0 flex-col overflow-hidden bg-[#f9fafb] text-gray-900">
    <header class="shrink-0 overflow-hidden bg-white">
      <div class="px-4 sm:px-5 lg:px-6">
        <div class="flex min-h-[76px] min-w-0 flex-wrap items-center gap-4 py-3 lg:flex-nowrap">
          <div class="flex min-w-[210px] shrink-0 items-center gap-3">
            <button
              type="button"
              class="flex h-10 w-10 items-center justify-center rounded-lg bg-blue-700 text-white shadow-sm"
              @click="navigateTo('/chat')"
            >
              <Bot class="h-[18px] w-[18px]" />
            </button>

            <div class="min-w-0">
              <button type="button" class="text-left" @click="navigateTo('/chat')">
                <div class="text-[18px] font-semibold tracking-tight text-gray-900">OpenDataAgent</div>
              </button>
            </div>
          </div>

          <nav class="oda-top-nav min-w-0 flex-1 overflow-hidden lg:flex lg:justify-center" aria-label="主导航">
            <el-menu
              class="oda-top-menu border-none bg-transparent"
              mode="horizontal"
              :default-active="activeMenu"
              :ellipsis="false"
              @select="navigateTo"
            >
              <el-menu-item
                v-for="item in navItems"
                :key="item.to"
                :index="item.to"
              >
                <component :is="item.icon" class="h-4 w-4" />
                <span>{{ item.label }}</span>
              </el-menu-item>
            </el-menu>
          </nav>
        </div>
      </div>
    </header>

    <div class="flex min-h-0 flex-1 flex-col px-4 pb-0 pt-4 sm:px-5 lg:px-6">
      <main class="flex-1 min-h-0 overflow-hidden py-0">
        <RouterView />
      </main>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import {
  Bot,
  Boxes,
  MessageSquareText,
  PlugZap,
  Settings,
  Settings2
} from 'lucide-vue-next'
import { RouterView, useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()
const activeMenu = computed(() => route.path.startsWith('/skills') || route.path === '/skill-market' ? '/skills' : route.path)

const navItems = [
  { to: '/chat', label: 'Agent 对话', icon: MessageSquareText },
  { to: '/skills', label: 'Skills', icon: Boxes },
  { to: '/mcps', label: 'MCP 管理', icon: PlugZap },
  { to: '/models', label: '模型设置', icon: Settings2 },
  { to: '/settings', label: '设置', icon: Settings }
]

const navigateTo = async (target) => {
  if (route.path === target) return
  await router.push(target)
}
</script>

<style scoped>
.oda-top-menu {
  --el-menu-border-color: transparent;
  border-bottom: 0 !important;
  box-shadow: none !important;
  width: auto;
  max-width: 100%;
  justify-content: center;
  background: transparent !important;
  overflow: hidden;
}

.oda-top-menu.el-menu--horizontal {
  border-bottom: 0 !important;
  box-shadow: none !important;
}

.oda-top-menu:deep(.el-menu-item) {
  height: 62px;
  margin: 0 24px;
  padding: 0 8px;
  border: none;
  border-radius: 0;
  color: #4b5563;
  background: transparent;
  line-height: 62px;
  font-size: 18px;
  font-weight: 550;
  white-space: nowrap;
}

.oda-top-menu:deep(.el-menu-item:hover) {
  color: #1d4ed8;
  background: transparent;
}

.oda-top-menu:deep(.el-menu-item.is-active) {
  background: transparent;
  color: #1d4ed8;
}

.oda-top-menu:deep(.el-menu-item.is-active svg) {
  color: #1d4ed8;
}

.oda-top-menu:deep(.el-menu-item svg) {
  width: 19px;
  height: 19px;
  margin-right: 11px;
  color: #6b7280;
}

.oda-top-menu:deep(.el-menu-item.is-active::after) {
  height: 3px;
  border-radius: 999px;
  background-color: #2563eb;
}

@media (max-width: 768px) {
  .oda-top-nav {
    flex: 0 0 100%;
    width: 100%;
  }

  .oda-top-menu {
    width: 100%;
  }

  .oda-top-menu:deep(.el-menu-item) {
    height: 48px;
    margin: 0 3px;
    padding: 0 6px;
    line-height: 48px;
    font-size: 14px;
  }

  .oda-top-menu:deep(.el-menu-item svg) {
    display: none;
    margin-right: 0;
  }
}
</style>
