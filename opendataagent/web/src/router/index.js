import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    redirect: '/chat'
  },
  {
    path: '/chat',
    component: () => import('@/views/chat/ChatRouteView.vue'),
    meta: {
      title: 'Agent 对话',
      subtitle: '多话题对话、任务流、Skill 与 MCP 运行轨迹'
    }
  },
  {
    path: '/skill-market',
    redirect: '/skills'
  },
  {
    path: '/skills/manage',
    redirect: '/skills'
  },
  {
    path: '/skills/market',
    redirect: '/skills'
  },
  {
    path: '/skills',
    component: () => import('@/views/market/SkillMarketView.vue'),
    meta: {
      title: 'Skills',
      subtitle: '统一浏览、安装和进入 Skill 详情页'
    }
  },
  {
    path: '/skills/detail/:folder',
    component: () => import('@/views/skills/SkillDetailView.vue'),
    meta: {
      title: 'Skill 详情',
      subtitle: '文件树、文件详情和版本管理'
    }
  },
  {
    path: '/mcps',
    component: () => import('@/views/mcps/McpManagerView.vue'),
    meta: {
      title: 'MCP 管理',
      subtitle: 'Server 配置、连通性测试与启停'
    }
  },
  {
    path: '/models',
    component: () => import('@/views/settings/AgentSettingsView.vue'),
    meta: {
      title: '模型设置',
      subtitle: '供应商、模型和新会话默认值'
    }
  },
  {
    path: '/settings',
    component: () => import('@/views/settings/RuntimeSettingsView.vue'),
    meta: {
      title: '设置',
      subtitle: '目录、访问控制和运行参数'
    }
  }
]

export default createRouter({
  history: createWebHistory(),
  routes
})
