<template>
  <div id="app">
    <el-container class="app-shell">
      <el-aside :width="isCollapse ? '72px' : '236px'" class="app-aside">
        <div class="sidebar">
          <div class="logo" :class="{ collapsed: isCollapse }">
            <div class="logo-badge">
              <svg viewBox="0 0 24 24" fill="none" class="logo-svg">
                <path d="M5 12L10 7V10.5H16.5C18.433 10.5 20 12.067 20 14V17H17V14C17 13.7239 16.7761 13.5 16.5 13.5H10V17L5 12Z" fill="currentColor" transform="rotate(180 12.5 12)"/>
                <circle cx="7" cy="17" r="2" fill="currentColor" opacity="0.8"/>
              </svg>
            </div>
            <div v-show="!isCollapse" class="logo-text">
              <h2>SAU 发布中心</h2>
              <span>多平台自动运营</span>
            </div>
          </div>

          <div class="menu-section-label" v-show="!isCollapse">工作台导航</div>
          <el-menu
            :router="true"
            :default-active="activeMenu"
            :collapse="isCollapse"
            :collapse-transition="false"
            class="sidebar-menu"
            background-color="transparent"
            text-color="#94a3b8"
            active-text-color="#ffffff"
          >
            <el-menu-item index="/">
              <el-icon><HomeFilled /></el-icon>
              <span>概览看板</span>
            </el-menu-item>
            <el-menu-item index="/account-management">
              <el-icon><User /></el-icon>
              <span>账号管理</span>
            </el-menu-item>
            <el-menu-item index="/material-management">
              <el-icon><Picture /></el-icon>
              <span>素材管理</span>
            </el-menu-item>
            <el-menu-item index="/publish-center">
              <el-icon><Upload /></el-icon>
              <span>发布中心</span>
            </el-menu-item>
            <el-menu-item index="/about">
              <el-icon><DataAnalysis /></el-icon>
              <span>关于系统</span>
            </el-menu-item>
          </el-menu>

          <div class="sidebar-footer" v-show="!isCollapse">
            <div class="engine-status">
              <span class="status-dot"></span>
              <span>本地发布引擎运行中</span>
            </div>
            <a
              href="http://127.0.0.1:18910"
              target="_blank"
              rel="noopener noreferrer"
              class="workbench-link"
            >
              <span>打开本机综合工作台</span>
              <el-icon><TopRight /></el-icon>
            </a>
          </div>
        </div>
      </el-aside>

      <el-container class="main-shell">
        <el-header class="app-header">
          <div class="header-content">
            <div class="header-left">
              <button type="button" class="toggle-btn" @click="toggleSidebar" :title="isCollapse ? '展开侧边栏' : '收起侧边栏'">
                <el-icon><Expand v-if="isCollapse" /><Fold v-else /></el-icon>
              </button>
              <div class="header-breadcrumb">
                <span class="brand-crumb">SAU Studio</span>
                <span class="crumb-sep">/</span>
                <span class="current-crumb">{{ currentPageTitle }}</span>
              </div>
            </div>
            <div class="header-right">
              <div class="platform-pills">
                <span class="pill douyin">抖音</span>
                <span class="pill kuaishou">快手</span>
                <span class="pill channels">视频号</span>
                <span class="pill xhs">小红书</span>
              </div>
              <el-button
                v-if="activeMenu !== '/publish-center'"
                type="primary"
                size="small"
                class="quick-publish-btn"
                @click="goPublish"
              >
                <el-icon><Upload /></el-icon>
                <span>新建发布</span>
              </el-button>
            </div>
          </div>
        </el-header>
        <el-main class="app-main">
          <div class="main-container">
            <router-view />
          </div>
        </el-main>
      </el-container>
    </el-container>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  HomeFilled, User, DataAnalysis,
  Fold, Expand, Picture, Upload, TopRight
} from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()

// 当前激活的菜单项
const activeMenu = computed(() => {
  return route.path
})

const pageTitleMap = {
  '/': '概览看板',
  '/account-management': '账号管理',
  '/material-management': '素材管理',
  '/publish-center': '发布中心',
  '/about': '关于系统'
}

const currentPageTitle = computed(() => {
  return pageTitleMap[route.path] || '工作台'
})

// 侧边栏折叠状态
const isCollapse = ref(false)

// 切换侧边栏折叠状态
const toggleSidebar = () => {
  isCollapse.value = !isCollapse.value
}

const goPublish = () => {
  router.push('/publish-center')
}
</script>

<style lang="scss" scoped>
@use '@/styles/variables.scss' as *;

#app {
  min-height: 100vh;
}

.app-shell {
  height: 100vh;
  background-color: $bg-color-page;
}

.app-aside {
  background: linear-gradient(180deg, #0f172a 0%, #111c33 100%);
  color: #fff;
  height: 100vh;
  overflow: hidden;
  transition: width 0.24s cubic-bezier(0.4, 0, 0.2, 1);
  border-right: 1px solid rgba(255, 255, 255, 0.06);
  flex-shrink: 0;

  .sidebar {
    display: flex;
    flex-direction: column;
    height: 100%;
    padding: 14px 12px;

    .logo {
      height: 56px;
      padding: 0 8px;
      display: flex;
      align-items: center;
      gap: 12px;
      margin-bottom: 16px;
      overflow: hidden;

      &.collapsed {
        justify-content: center;
        padding: 0;
      }

      .logo-badge {
        width: 38px;
        height: 38px;
        border-radius: 11px;
        background: linear-gradient(135deg, #6366f1 0%, #4f46e5 55%, #0ea5e9 100%);
        display: flex;
        align-items: center;
        justify-content: center;
        color: #fff;
        flex-shrink: 0;
        box-shadow: 0 6px 16px rgba(79, 70, 229, 0.35);

        .logo-svg {
          width: 20px;
          height: 20px;
        }
      }

      .logo-text {
        min-width: 0;

        h2 {
          color: #f8fafc;
          font-size: 15px;
          font-weight: 700;
          letter-spacing: -0.01em;
          white-space: nowrap;
          margin: 0;
          line-height: 1.25;
        }

        span {
          display: block;
          color: #64748b;
          font-size: 11px;
          white-space: nowrap;
          margin-top: 2px;
        }
      }
    }

    .menu-section-label {
      padding: 0 12px 8px;
      font-size: 11px;
      font-weight: 600;
      letter-spacing: 0.06em;
      color: #475569;
      text-transform: uppercase;
    }

    .sidebar-menu {
      border-right: none;
      flex: 1;
      background: transparent;

      :deep(.el-menu-item) {
        height: 44px;
        line-height: 44px;
        border-radius: 10px;
        margin-bottom: 6px;
        padding: 0 14px !important;
        font-size: 14px;
        font-weight: 500;
        display: flex;
        align-items: center;
        transition: all 0.18s ease;

        .el-icon {
          margin-right: 10px;
          font-size: 18px;
        }

        &:hover {
          background-color: rgba(255, 255, 255, 0.06) !important;
          color: #e2e8f0 !important;
        }

        &.is-active {
          background: linear-gradient(135deg, #4f46e5 0%, #6366f1 100%) !important;
          color: #ffffff !important;
          box-shadow: 0 6px 16px -4px rgba(79, 70, 229, 0.55);
        }
      }

      &.el-menu--collapse {
        width: 100%;

        :deep(.el-menu-item) {
          justify-content: center;
          padding: 0 !important;

          .el-icon {
            margin-right: 0;
          }
        }
      }
    }

    .sidebar-footer {
      margin-top: auto;
      padding: 12px;
      border-radius: 12px;
      background: rgba(255, 255, 255, 0.04);
      border: 1px solid rgba(255, 255, 255, 0.07);

      .engine-status {
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 12px;
        color: #cbd5e1;
        margin-bottom: 10px;

        .status-dot {
          width: 8px;
          height: 8px;
          border-radius: 50%;
          background-color: #10b981;
          box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.2);
          flex-shrink: 0;
        }
      }

      .workbench-link {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 7px 10px;
        border-radius: 8px;
        font-size: 12px;
        font-weight: 500;
        color: #93c5fd;
        background: rgba(59, 130, 246, 0.1);
        text-decoration: none;
        transition: all 0.18s ease;

        &:hover {
          background: rgba(59, 130, 246, 0.2);
          color: #dbeafe;
        }
      }
    }
  }
}

.main-shell {
  min-width: 0;
  background: radial-gradient(circle at top right, rgba(79, 70, 229, 0.045), transparent 36%),
    $bg-color-page;
}

.app-header {
  background-color: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid $border-light;
  padding: 0;
  height: 62px;
  position: sticky;
  top: 0;
  z-index: 20;

  .header-content {
    display: flex;
    justify-content: space-between;
    align-items: center;
    height: 100%;
    padding: 0 24px;

    .header-left {
      display: flex;
      align-items: center;
      gap: 14px;

      .toggle-btn {
        width: 34px;
        height: 34px;
        border: 1px solid $border-light;
        background: #fff;
        border-radius: 8px;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-size: 17px;
        cursor: pointer;
        color: $text-regular;
        transition: all 0.18s ease;

        &:hover {
          color: $primary-color;
          border-color: rgba($primary-color, 0.35);
          background: $primary-light;
        }
      }

      .header-breadcrumb {
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 14px;

        .brand-crumb {
          color: $text-secondary;
          font-weight: 500;
        }

        .crumb-sep {
          color: $border-base;
        }

        .current-crumb {
          color: $text-primary;
          font-weight: 600;
        }
      }
    }

    .header-right {
      display: flex;
      align-items: center;
      gap: 14px;

      .platform-pills {
        display: flex;
        align-items: center;
        gap: 6px;

        .pill {
          font-size: 12px;
          font-weight: 500;
          padding: 3px 9px;
          border-radius: 999px;
          border: 1px solid transparent;

          &.douyin {
            color: #be123c;
            background: #fff1f2;
            border-color: #ffe4e6;
          }

          &.kuaishou {
            color: #c2410c;
            background: #fff7ed;
            border-color: #ffedd5;
          }

          &.channels {
            color: #b45309;
            background: #fffbeb;
            border-color: #fef3c7;
          }

          &.xhs {
            color: #e11d48;
            background: #fdf2f8;
            border-color: #fce7f3;
          }
        }
      }

      .quick-publish-btn {
        box-shadow: 0 4px 12px -2px rgba($primary-color, 0.4);

        .el-icon {
          margin-right: 4px;
        }
      }
    }
  }
}

.app-main {
  background-color: transparent;
  padding: 24px 28px 36px;
  overflow-y: auto;

  .main-container {
    max-width: 1360px;
    margin: 0 auto;
  }
}

@media (max-width: 900px) {
  .app-header .header-content .header-right .platform-pills {
    display: none;
  }
}
</style>
