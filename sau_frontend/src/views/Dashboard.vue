<template>
  <div class="dashboard">
    <div class="hero-banner">
      <div class="hero-copy">
        <div class="hero-badge">CREATOR WORKSPACE</div>
        <h1>自媒体自动化运营工作台</h1>
        <p>集中管理多平台创作者账号、视频素材库与一键定时分发任务</p>
      </div>
      <div class="hero-actions">
        <el-button @click="navigateTo('/account-management')">
          <el-icon><UserFilled /></el-icon>
          <span>管理账号</span>
        </el-button>
        <el-button type="primary" @click="navigateTo('/publish-center')">
          <el-icon><Upload /></el-icon>
          <span>立即发布视频</span>
        </el-button>
      </div>
    </div>

    <div class="dashboard-content">
      <el-row :gutter="20" class="stat-row">
        <!-- 账号统计卡片 -->
        <el-col :xs="24" :sm="8">
          <el-card class="stat-card stat-card--indigo" shadow="never">
            <div class="stat-card-content">
              <div class="stat-icon">
                <el-icon><User /></el-icon>
              </div>
              <div class="stat-info">
                <div class="stat-label">账号总数</div>
                <div class="stat-value">{{ accountStats.total }}</div>
              </div>
            </div>
            <div class="stat-footer">
              <div class="stat-detail">
                <span class="metric-pill normal">
                  <i class="dot"></i>正常 {{ accountStats.normal }}
                </span>
                <span class="metric-pill abnormal">
                  <i class="dot"></i>异常 {{ accountStats.abnormal }}
                </span>
              </div>
            </div>
          </el-card>
        </el-col>

        <!-- 平台统计卡片 -->
        <el-col :xs="24" :sm="8">
          <el-card class="stat-card stat-card--emerald" shadow="never">
            <div class="stat-card-content">
              <div class="stat-icon platform-icon">
                <el-icon><Platform /></el-icon>
              </div>
              <div class="stat-info">
                <div class="stat-label">已接入平台</div>
                <div class="stat-value">{{ platformStats.total }}</div>
              </div>
            </div>
            <div class="stat-footer">
              <div class="stat-detail platform-chips">
                <el-tooltip content="快手账号" placement="top">
                  <span class="mini-chip kuaishou">快手 {{ platformStats.kuaishou }}</span>
                </el-tooltip>
                <el-tooltip content="抖音账号" placement="top">
                  <span class="mini-chip douyin">抖音 {{ platformStats.douyin }}</span>
                </el-tooltip>
                <el-tooltip content="视频号账号" placement="top">
                  <span class="mini-chip channels">视频号 {{ platformStats.channels }}</span>
                </el-tooltip>
                <el-tooltip content="小红书账号" placement="top">
                  <span class="mini-chip xhs">小红书 {{ platformStats.xiaohongshu }}</span>
                </el-tooltip>
              </div>
            </div>
          </el-card>
        </el-col>

        <!-- 素材统计卡片 -->
        <el-col :xs="24" :sm="8">
          <el-card class="stat-card stat-card--sky" shadow="never">
            <div class="stat-card-content">
              <div class="stat-icon content-icon">
                <el-icon><Document /></el-icon>
              </div>
              <div class="stat-info">
                <div class="stat-label">素材总数</div>
                <div class="stat-value">{{ contentStats.total }}</div>
              </div>
            </div>
            <div class="stat-footer">
              <div class="stat-detail">
                <span>视频 <strong>{{ contentStats.videos }}</strong></span>
                <span>图片 <strong>{{ contentStats.images }}</strong></span>
                <span>其他 <strong>{{ contentStats.others }}</strong></span>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>

      <!-- 快捷操作区域 -->
      <div class="quick-actions">
        <div class="section-header">
          <h2>快捷入口</h2>
          <span class="section-sub">常用运营工作流一键直达</span>
        </div>
        <el-row :gutter="16">
          <el-col :xs="12" :md="6">
            <el-card class="action-card" shadow="never" @click="navigateTo('/account-management')">
              <div class="action-icon tone-indigo">
                <el-icon><UserFilled /></el-icon>
              </div>
              <div class="action-body">
                <div class="action-title">账号管理</div>
                <div class="action-desc">扫码绑定与 Cookie 状态维护</div>
              </div>
              <el-icon class="action-arrow"><ArrowRight /></el-icon>
            </el-card>
          </el-col>
          <el-col :xs="12" :md="6">
            <el-card class="action-card" shadow="never" @click="navigateTo('/material-management')">
              <div class="action-icon tone-sky">
                <el-icon><Upload /></el-icon>
              </div>
              <div class="action-body">
                <div class="action-title">素材管理</div>
                <div class="action-desc">批量上传、预览与管理视频</div>
              </div>
              <el-icon class="action-arrow"><ArrowRight /></el-icon>
            </el-card>
          </el-col>
          <el-col :xs="12" :md="6">
            <el-card class="action-card" shadow="never" @click="navigateTo('/publish-center')">
              <div class="action-icon tone-emerald">
                <el-icon><Timer /></el-icon>
              </div>
              <div class="action-body">
                <div class="action-title">发布中心</div>
                <div class="action-desc">多任务并行与定时分发设置</div>
              </div>
              <el-icon class="action-arrow"><ArrowRight /></el-icon>
            </el-card>
          </el-col>
          <el-col :xs="12" :md="6">
            <el-card class="action-card" shadow="never" @click="navigateTo('/about')">
              <div class="action-icon tone-amber">
                <el-icon><DataAnalysis /></el-icon>
              </div>
              <div class="action-body">
                <div class="action-title">关于系统</div>
                <div class="action-desc">支持平台说明与引擎技术栈</div>
              </div>
              <el-icon class="action-arrow"><ArrowRight /></el-icon>
            </el-card>
          </el-col>
        </el-row>
      </div>

      <!-- 素材列表 -->
      <el-card class="recent-tasks-card" shadow="never">
        <div class="section-header">
          <div>
            <h2>最近上传素材</h2>
            <span class="section-sub">展示最新导入的 5 条视频/图文素材</span>
          </div>
          <el-button type="primary" plain size="small" @click="navigateTo('/material-management')">
            进入素材库
          </el-button>
        </div>

        <el-table v-if="loading || recentMaterials.length > 0" :data="recentMaterials" style="width: 100%" v-loading="loading">
          <el-table-column prop="filename" label="文件名" min-width="260" show-overflow-tooltip />
          <el-table-column prop="filesize" label="文件大小" width="130">
            <template #default="scope">
              <span class="tabular-num">{{ scope.row.filesize }} MB</span>
            </template>
          </el-table-column>
          <el-table-column prop="upload_time" label="上传时间" width="210" />
          <el-table-column label="类型" width="110">
            <template #default="scope">
              <el-tag
                :type="getFileTypeTag(scope.row.filename)"
                effect="light"
                size="small"
              >
                {{ getFileType(scope.row.filename) }}
              </el-tag>
            </template>
          </el-table-column>
        </el-table>

        <div v-else class="empty-state-box">
          <el-empty description="还没有上传素材" :image-size="88">
            <el-button type="primary" @click="navigateTo('/material-management')">去上传素材</el-button>
          </el-empty>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  User, UserFilled, Platform, Document,
  Upload, Timer, DataAnalysis, ArrowRight
} from '@element-plus/icons-vue'
import { accountApi } from '@/api/account'
import { materialApi } from '@/api/material'
import { useAccountStore } from '@/stores/account'
import { useAppStore } from '@/stores/app'

const router = useRouter()
const accountStore = useAccountStore()
const appStore = useAppStore()
const loading = ref(false)

// 账号统计数据 - 从真实数据计算
const accountStats = computed(() => {
  const accounts = accountStore.accounts
  const normal = accounts.filter(a => a.status === '正常').length
  const abnormal = accounts.filter(a => a.status !== '正常' && a.status !== '验证中').length
  return {
    total: accounts.length,
    normal,
    abnormal
  }
})

// 平台统计数据 - 从真实数据计算
const platformStats = computed(() => {
  const accounts = accountStore.accounts
  const kuaishou = accounts.filter(a => a.platform === '快手').length
  const douyin = accounts.filter(a => a.platform === '抖音').length
  const channels = accounts.filter(a => a.platform === '视频号').length
  const xiaohongshu = accounts.filter(a => a.platform === '小红书').length
  // 统计有账号的平台数量
  const total = [kuaishou, douyin, channels, xiaohongshu].filter(n => n > 0).length
  return { total, kuaishou, douyin, channels, xiaohongshu }
})

// 素材统计数据 - 从真实数据计算
const videoExtensions = ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.mkv']
const imageExtensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']

const contentStats = computed(() => {
  const materials = appStore.materials
  const videos = materials.filter(m => videoExtensions.some(ext => m.filename.toLowerCase().endsWith(ext))).length
  const images = materials.filter(m => imageExtensions.some(ext => m.filename.toLowerCase().endsWith(ext))).length
  return {
    total: materials.length,
    videos,
    images,
    others: materials.length - videos - images
  }
})

// 最近上传的素材（最多显示5条）
const recentMaterials = computed(() => {
  return [...appStore.materials]
    .sort((a, b) => new Date(b.upload_time) - new Date(a.upload_time))
    .slice(0, 5)
})

// 获取文件类型
const getFileType = (filename) => {
  if (videoExtensions.some(ext => filename.toLowerCase().endsWith(ext))) return '视频'
  if (imageExtensions.some(ext => filename.toLowerCase().endsWith(ext))) return '图片'
  return '其他'
}

// 获取文件类型标签颜色
const getFileTypeTag = (filename) => {
  const type = getFileType(filename)
  return { '视频': 'success', '图片': 'warning', '其他': 'info' }[type] || 'info'
}

// 导航到指定路由
const navigateTo = (path) => {
  router.push(path)
}

// 加载数据
const fetchDashboardData = async () => {
  loading.value = true
  try {
    // 并行获取账号和素材数据
    const [accountRes, materialRes] = await Promise.allSettled([
      accountApi.getAccounts(),
      materialApi.getAllMaterials()
    ])

    if (accountRes.status === 'fulfilled' && accountRes.value.code === 200) {
      accountStore.setAccounts(accountRes.value.data)
    }
    if (materialRes.status === 'fulfilled' && materialRes.value.code === 200) {
      appStore.setMaterials(materialRes.value.data)
    }
  } catch (error) {
    console.error('获取仪表盘数据失败:', error)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchDashboardData()
})
</script>

<style lang="scss" scoped>
@use '@/styles/variables.scss' as *;

.dashboard {
  .hero-banner {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 20px;
    padding: 24px 28px;
    margin-bottom: 22px;
    border-radius: 16px;
    background: linear-gradient(135deg, #ffffff 0%, #f5f7ff 55%, #eef2ff 100%);
    border: 1px solid #e0e7ff;
    box-shadow: $box-shadow-light;
    flex-wrap: wrap;

    .hero-copy {
      .hero-badge {
        display: inline-block;
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.08em;
        color: $primary-color;
        background: rgba($primary-color, 0.1);
        padding: 4px 10px;
        border-radius: 999px;
        margin-bottom: 10px;
      }

      h1 {
        font-size: 24px;
        font-weight: 700;
        letter-spacing: -0.02em;
        color: $text-primary;
        margin: 0 0 6px 0;
      }

      p {
        font-size: 14px;
        color: $text-secondary;
        margin: 0;
      }
    }

    .hero-actions {
      display: flex;
      gap: 10px;
      flex-wrap: wrap;

      .el-icon {
        margin-right: 4px;
      }
    }
  }

  .dashboard-content {
    .stat-row {
      row-gap: 16px;
    }

    .stat-card {
      height: 100%;
      position: relative;
      overflow: hidden;

      &::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
      }

      &.stat-card--indigo::before {
        background: linear-gradient(90deg, #4f46e5, #818cf8);
      }

      &.stat-card--emerald::before {
        background: linear-gradient(90deg, #10b981, #34d399);
      }

      &.stat-card--sky::before {
        background: linear-gradient(90deg, #0ea5e9, #38bdf8);
      }

      :deep(.el-card__body) {
        padding: 20px 22px 16px;
      }

      .stat-card-content {
        display: flex;
        align-items: center;
        margin-bottom: 16px;

        .stat-icon {
          width: 52px;
          height: 52px;
          border-radius: 14px;
          background-color: rgba($primary-color, 0.1);
          display: flex;
          justify-content: center;
          align-items: center;
          margin-right: 16px;
          flex-shrink: 0;

          .el-icon {
            font-size: 25px;
            color: $primary-color;
          }

          &.platform-icon {
            background-color: rgba($success-color, 0.1);

            .el-icon {
              color: $success-color;
            }
          }

          &.content-icon {
            background-color: rgba($accent-color, 0.12);

            .el-icon {
              color: $accent-color;
            }
          }
        }

        .stat-info {
          .stat-label {
            font-size: 13px;
            color: $text-secondary;
            margin-bottom: 4px;
          }

          .stat-value {
            font-size: 28px;
            font-weight: 700;
            color: $text-primary;
            line-height: 1.15;
            font-variant-numeric: tabular-nums;
          }
        }
      }

      .stat-footer {
        border-top: 1px solid $border-lighter;
        padding-top: 12px;

        .stat-detail {
          display: flex;
          justify-content: space-between;
          align-items: center;
          flex-wrap: wrap;
          gap: 6px;
          color: $text-secondary;
          font-size: 13px;

          strong {
            color: $text-primary;
            font-weight: 600;
          }

          .metric-pill {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 3px 10px;
            border-radius: 999px;
            font-size: 12px;
            font-weight: 500;

            .dot {
              width: 6px;
              height: 6px;
              border-radius: 50%;
              display: inline-block;
            }

            &.normal {
              background: #ecfdf5;
              color: #047857;

              .dot {
                background: #10b981;
              }
            }

            &.abnormal {
              background: #fef2f2;
              color: #b91c1c;

              .dot {
                background: #ef4444;
              }
            }
          }

          &.platform-chips {
            justify-content: flex-start;
          }

          .mini-chip {
            padding: 2px 8px;
            border-radius: 6px;
            font-size: 12px;
            font-weight: 500;

            &.kuaishou {
              background: #fff7ed;
              color: #c2410c;
            }

            &.douyin {
              background: #fff1f2;
              color: #be123c;
            }

            &.channels {
              background: #fffbeb;
              color: #b45309;
            }

            &.xhs {
              background: #fdf2f8;
              color: #db2777;
            }
          }
        }
      }
    }

    .section-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 14px;

      h2 {
        font-size: 17px;
        font-weight: 600;
        color: $text-primary;
        margin: 0;
      }

      .section-sub {
        font-size: 13px;
        color: $text-secondary;
      }
    }

    .quick-actions {
      margin: 24px 0;

      .el-row {
        row-gap: 14px;
      }

      .action-card {
        cursor: pointer;
        height: 100%;

        :deep(.el-card__body) {
          display: flex;
          align-items: center;
          gap: 14px;
          padding: 18px;
        }

        &:hover {
          transform: translateY(-3px);
          border-color: rgba($primary-color, 0.35) !important;
          box-shadow: $box-shadow-dark !important;

          .action-arrow {
            transform: translateX(3px);
            color: $primary-color;
          }
        }

        .action-icon {
          width: 44px;
          height: 44px;
          border-radius: 12px;
          display: flex;
          justify-content: center;
          align-items: center;
          flex-shrink: 0;

          .el-icon {
            font-size: 21px;
          }

          &.tone-indigo {
            background: rgba($primary-color, 0.1);
            color: $primary-color;
          }

          &.tone-sky {
            background: rgba($accent-color, 0.12);
            color: $accent-color;
          }

          &.tone-emerald {
            background: rgba($success-color, 0.12);
            color: $success-color;
          }

          &.tone-amber {
            background: rgba($warning-color, 0.14);
            color: $warning-color;
          }
        }

        .action-body {
          flex: 1;
          min-width: 0;

          .action-title {
            font-size: 15px;
            font-weight: 600;
            color: $text-primary;
            margin-bottom: 3px;
          }

          .action-desc {
            font-size: 12px;
            color: $text-secondary;
            line-height: 1.4;
          }
        }

        .action-arrow {
          color: $text-placeholder;
          font-size: 15px;
          transition: all 0.2s ease;
        }
      }
    }

    .recent-tasks-card {
      :deep(.el-card__body) {
        padding: 20px 22px;
      }

      .section-header {
        margin-bottom: 16px;
      }

      .tabular-num {
        font-variant-numeric: tabular-nums;
      }

      .empty-state-box {
        padding: 16px 0;
      }
    }
  }
}
</style>
