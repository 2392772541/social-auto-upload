<template>
  <div class="publish-center">
    <div class="studio-page-header">
      <div class="header-titles">
        <h1>发布中心</h1>
        <p>直传视频或从素材库直选 · 一键复制多平台 · 草稿自动防丢失 · 定时排期预览</p>
      </div>
      <div class="header-actions">
        <el-button @click="openHistoryDrawer">
          <el-icon><Clock /></el-icon>
          <span>发布历史</span>
          <el-badge v-if="publishHistory.length > 0" :value="publishHistory.length" :max="99" class="history-badge" />
        </el-button>
        <el-button type="primary" plain @click="openSyncModal">
          <el-icon><CopyDocument /></el-icon>
          <span>一键同步多平台</span>
        </el-button>
      </div>
    </div>

    <!-- Tab管理区域 -->
    <div class="tab-management">
      <div class="tab-header">
        <div class="tab-list">
          <div
            v-for="tab in tabs"
            :key="tab.name"
            :class="['tab-item', { active: activeTab === tab.name }]"
            @click="activeTab = tab.name"
          >
            <span class="tab-plat-dot" :class="getPlatformClass(tab.selectedPlatform)"></span>
            <span>{{ tab.label }} · {{ getPlatformName(tab.selectedPlatform) }}</span>
            <span v-if="tab.fileList.length > 0" class="tab-file-pill">{{ tab.fileList.length }}视频</span>
            <el-icon
              v-if="tabs.length > 1"
              class="close-icon"
              @click.stop="removeTab(tab.name)"
            >
              <Close />
            </el-icon>
          </div>
        </div>
        <div class="tab-actions">
          <el-button
            type="primary"
            plain
            size="small"
            @click="addTab"
            class="add-tab-btn"
          >
            <el-icon><Plus /></el-icon>
            新建发布任务
          </el-button>
          <el-button
            type="success"
            size="small"
            @click="batchPublish"
            :loading="batchPublishing"
            class="batch-publish-btn"
          >
            批量发布全部 ({{ tabs.length }})
          </el-button>
        </div>
      </div>
    </div>

    <!-- 内容区域 -->
    <div class="publish-content">
      <div class="tab-content-wrapper">
        <div
          v-for="tab in tabs"
          :key="tab.name"
          v-show="activeTab === tab.name"
          class="tab-content"
        >
          <!-- 发布状态提示 -->
          <div v-if="tab.publishStatus" class="publish-status">
            <el-alert
              :title="tab.publishStatus.message"
              :type="tab.publishStatus.type"
              closable
              show-icon
              @close="tab.publishStatus = null"
            />
          </div>

          <!-- 1. 目标平台与账号选择 -->
          <div class="section-card">
            <div class="section-head">
              <h3>1. 选择发布平台与账号</h3>
              <el-button link type="primary" size="small" @click="goAccountPage">去管理/添加账号</el-button>
            </div>

            <div class="platform-cards">
              <button
                v-for="platform in platforms"
                :key="platform.key"
                type="button"
                :class="['platform-card-btn', getPlatformClass(platform.key), { active: tab.selectedPlatform === platform.key }]"
                @click="selectPlatform(tab, platform.key)"
              >
                <span class="plat-dot"></span>
                <span class="plat-name">{{ platform.name }}</span>
                <span class="plat-count">{{ getAccountsByPlatform(platform.key).length }}号</span>
              </button>
            </div>

            <div class="inline-accounts-box">
              <div class="inline-accounts-label">
                <span>可用「{{ getPlatformName(tab.selectedPlatform) }}」账号：</span>
                <el-button
                  v-if="getAccountsByPlatform(tab.selectedPlatform).length > 0"
                  link
                  type="primary"
                  size="small"
                  @click="selectAllPlatformAccounts(tab)"
                >
                  全选正常账号
                </el-button>
              </div>

              <div v-if="getAccountsByPlatform(tab.selectedPlatform).length > 0" class="account-chip-list">
                <button
                  v-for="acc in getAccountsByPlatform(tab.selectedPlatform)"
                  :key="acc.id"
                  type="button"
                  :class="['account-chip', { selected: tab.selectedAccounts.includes(acc.id), abnormal: acc.status !== '正常' }]"
                  @click="toggleAccount(tab, acc.id)"
                >
                  <span class="acc-avatar">{{ (acc.name || '?').slice(0, 1).toUpperCase() }}</span>
                  <span class="acc-name">{{ acc.name }}</span>
                  <span :class="['acc-status', acc.status === '正常' ? 'ok' : 'warn']">{{ acc.status }}</span>
                </button>
              </div>

              <div v-else class="no-account-tip">
                <span>暂无「{{ getPlatformName(tab.selectedPlatform) }}」账号。</span>
                <el-button type="primary" size="small" plain @click="goAccountPage">去扫码绑定</el-button>
              </div>
            </div>
          </div>

          <!-- 2. 视频素材 -->
          <div class="section-card">
            <div class="section-head">
              <h3>2. 选择或上传视频</h3>
              <div class="video-head-actions">
                <el-button type="success" plain size="small" @click="openMaterialLibrary(tab)">
                  <el-icon><Folder /></el-icon>
                  <span>从素材库挑选 ({{ materials.length }})</span>
                </el-button>
              </div>
            </div>

            <el-upload
              class="inline-video-upload"
              drag
              :auto-upload="true"
              :action="`${apiBaseUrl}/upload`"
              :on-success="(response, file) => handleUploadSuccess(response, file, tab)"
              :on-error="handleUploadError"
              :show-file-list="false"
              multiple
              accept="video/*"
              :headers="authHeaders"
            >
              <el-icon class="el-icon--upload"><Upload /></el-icon>
              <div class="el-upload__text">
                将视频拖拽到此处直接上传，或 <em>点击选择本地视频</em>
              </div>
              <template #tip>
                <div class="el-upload__tip">
                  支持 MP4 / MOV / AVI 等格式（单文件上限 160MB），也可直接点右上角从已有素材库选取
                </div>
              </template>
            </el-upload>

            <div v-if="tab.fileList.length > 0" class="uploaded-files">
              <h4>待发布视频列表（{{ tab.fileList.length }} 个）：</h4>
              <div class="file-list">
                <div v-for="(file, index) in tab.fileList" :key="index" class="file-item">
                  <el-icon class="file-icon"><VideoCamera /></el-icon>
                  <el-link :href="file.url" target="_blank" type="primary">{{ file.name }}</el-link>
                  <span class="file-size">{{ ((file.size || 0) / 1024 / 1024).toFixed(2) }} MB</span>
                  <el-button type="danger" plain size="small" @click="removeFile(tab, index)">移除</el-button>
                </div>
              </div>
            </div>
          </div>

          <!-- 3. 标题、文案模板与话题 -->
          <div class="section-card">
            <div class="section-head">
              <h3>3. 标题、文案与话题标签</h3>
              <div class="template-pills">
                <span class="tpl-hint">快速套用模板：</span>
                <el-button
                  v-for="tpl in titleTemplates"
                  :key="tpl.name"
                  size="small"
                  plain
                  @click="applyTitleTemplate(tab, tpl)"
                >
                  {{ tpl.name }}
                </el-button>
              </div>
            </div>

            <div class="title-block">
              <el-input
                v-model="tab.title"
                type="textarea"
                :rows="3"
                placeholder="请输入吸引眼球的视频标题/描述（支持换行，最多100字）"
                maxlength="100"
                show-word-limit
              />
            </div>

            <div class="topic-display">
              <div class="topic-row-header">
                <span class="sub-label">话题标签（建议 3~5 个）</span>
                <el-button type="primary" plain size="small" @click="openTopicDialog(tab)">
                  <el-icon><Plus /></el-icon>
                  <span>选择 / 添加话题</span>
                </el-button>
              </div>
              <div class="selected-topics" v-if="tab.selectedTopics.length > 0">
                <el-tag
                  v-for="(topic, index) in tab.selectedTopics"
                  :key="index"
                  closable
                  @close="removeTopic(tab, index)"
                  class="topic-tag"
                >
                  #{{ topic }}
                </el-tag>
              </div>
              <div v-else class="empty-topic-hint">暂未添加话题标签，点击右上角快速添加</div>
            </div>

            <div class="platform-extras">
              <el-checkbox v-model="tab.isOriginal" label="声明原创" />
              <el-checkbox
                v-if="tab.selectedPlatform === 2"
                v-model="tab.isDraft"
                label="视频号仅保存草稿（随后在手机端确认发布）"
              />
            </div>

            <div v-if="tab.selectedPlatform === 3" class="product-section">
              <div class="sub-label">抖音商品橱窗挂载（选填）</div>
              <div class="product-grid">
                <el-input v-model="tab.productTitle" placeholder="商品名称（选填）" maxlength="200" />
                <el-input v-model="tab.productLink" placeholder="商品链接（选填）" maxlength="200" />
              </div>
            </div>
          </div>

          <!-- 4. 定时排期与提交 -->
          <div class="section-card">
            <div class="section-head">
              <h3>4. 发布时间设置</h3>
              <el-switch
                v-model="tab.scheduleEnabled"
                active-text="开启定时排期"
                inactive-text="立即发布"
              />
            </div>

            <div v-if="tab.scheduleEnabled" class="schedule-settings">
              <div class="schedule-grid">
                <div class="schedule-item">
                  <span class="label">每天发布条数</span>
                  <el-select v-model="tab.videosPerDay" placeholder="选择数量" style="width: 120px" @change="syncDailyTimes(tab)">
                    <el-option v-for="num in 10" :key="num" :label="`${num} 条/天`" :value="num" />
                  </el-select>
                </div>
                <div class="schedule-item">
                  <span class="label">起始日期</span>
                  <el-select v-model="tab.startDays" placeholder="选择开始天数" style="width: 140px">
                    <el-option label="明天开始" :value="0" />
                    <el-option label="后天开始" :value="1" />
                    <el-option label="3天后开始" :value="2" />
                  </el-select>
                </div>
              </div>

              <div class="schedule-times-row">
                <span class="label">每天发布时间点：</span>
                <div class="times-wrap">
                  <el-time-select
                    v-for="(time, index) in tab.dailyTimes"
                    :key="index"
                    v-model="tab.dailyTimes[index]"
                    start="00:00"
                    step="00:30"
                    end="23:30"
                    placeholder="选择时间"
                    style="width: 125px"
                  />
                  <el-button
                    v-if="tab.dailyTimes.length < tab.videosPerDay"
                    type="primary"
                    plain
                    size="small"
                    @click="tab.dailyTimes.push('18:00')"
                  >
                    + 添加时间点
                  </el-button>
                </div>
              </div>

              <div class="schedule-preview" v-if="getSchedulePreview(tab).length > 0">
                <span class="preview-title">排期预览：</span>
                <el-tag
                  v-for="(slot, idx) in getSchedulePreview(tab)"
                  :key="idx"
                  size="small"
                  effect="light"
                >
                  第{{ idx + 1 }}条：{{ slot }}
                </el-tag>
              </div>
            </div>
            <div v-else class="immediate-tip">
              提交后将立即启动后台发布流程；如果是多条视频，建议开启定时排期避免集中刷屏。
            </div>
          </div>

          <!-- 操作按钮 -->
          <div class="action-buttons">
            <el-button @click="resetTab(tab)">清空当前任务</el-button>
            <el-button type="primary" plain @click="openSyncModal">一键同步到其他平台</el-button>
            <el-button
              type="primary"
              @click="confirmPublish(tab)"
              :loading="tab.publishing || false"
            >
              {{ tab.publishing ? '提交发布中...' : '立即提交发布' }}
            </el-button>
          </div>
        </div>
      </div>
    </div>

    <!-- 素材库选择对话框 -->
    <el-dialog v-model="materialLibraryVisible" title="从素材库选择视频" width="720px">
      <div class="material-library-content">
        <div v-if="materials.length === 0" class="empty-material">
          <el-empty description="素材库还没有视频，你可以直接在发布页上方拖拽上传，或前往素材管理上传" :image-size="80" />
        </div>
        <el-checkbox-group v-else v-model="selectedMaterials">
          <div class="material-list">
            <el-checkbox
              v-for="material in materials"
              :key="material.id"
              :value="material.id"
              class="material-item"
            >
              <div class="material-info">
                <div class="material-name">{{ material.filename }}</div>
                <div class="material-details">
                  <span class="file-size">{{ material.filesize }} MB</span>
                  <span class="upload-time">{{ material.upload_time }}</span>
                </div>
              </div>
            </el-checkbox>
          </div>
        </el-checkbox-group>
      </div>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="materialLibraryVisible = false">取消</el-button>
          <el-button type="primary" @click="confirmMaterialSelection">添加选中素材</el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 一键同步到多平台弹窗 -->
    <el-dialog v-model="syncDialogVisible" title="一键同步生成多平台发布任务" width="480px">
      <div class="sync-dialog-body">
        <p class="sync-tip">将当前任务的「视频、标题、话题与定时设置」一键复制到选中的平台，自动为您匹配各平台第一个正常账号。</p>
        <el-checkbox-group v-model="syncTargetPlatforms" class="sync-plat-group">
          <el-checkbox
            v-for="plat in platforms"
            :key="plat.key"
            :value="plat.key"
            :disabled="currentActiveTabObj?.selectedPlatform === plat.key"
          >
            {{ plat.name }}
            <span class="sync-acc-count">（{{ getAccountsByPlatform(plat.key).length }}个账号）</span>
          </el-checkbox>
        </el-checkbox-group>
      </div>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="syncDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="confirmSyncPlatforms">生成对应发布 Tab</el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 添加话题弹窗 -->
    <el-dialog v-model="topicDialogVisible" title="添加话题标签" width="560px" class="topic-dialog">
      <div class="topic-dialog-content">
        <div class="custom-topic-input">
          <el-input v-model="customTopic" placeholder="输入自定义话题，回车添加" class="custom-input" @keyup.enter="addCustomTopic">
            <template #prepend>#</template>
          </el-input>
          <el-button type="primary" @click="addCustomTopic">添加</el-button>
        </div>
        <div class="recommended-topics">
          <h4>常用热门话题</h4>
          <div class="topic-grid">
            <el-button
              v-for="topic in recommendedTopics"
              :key="topic"
              :type="currentTab?.selectedTopics?.includes(topic) ? 'primary' : 'default'"
              @click="toggleRecommendedTopic(topic)"
              class="topic-btn"
            >
              # {{ topic }}
            </el-button>
          </div>
        </div>
      </div>
      <template #footer>
        <div class="dialog-footer">
          <el-button type="primary" @click="confirmTopicSelection">完成</el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 批量发布进度对话框 -->
    <el-dialog
      v-model="batchPublishDialogVisible"
      title="批量发布进度"
      width="500px"
      :close-on-click-modal="false"
      :close-on-press-escape="false"
      :show-close="false"
    >
      <div class="publish-progress">
        <el-progress :percentage="publishProgress" :status="publishProgress === 100 ? 'success' : ''" />
        <div v-if="currentPublishingTab" class="current-publishing">
          正在发布：{{ currentPublishingTab.label }}
        </div>
        <div class="publish-results" v-if="publishResults.length > 0">
          <div v-for="(result, index) in publishResults" :key="index" :class="['result-item', result.status]">
            <el-icon v-if="result.status === 'success'"><Check /></el-icon>
            <el-icon v-else-if="result.status === 'error'"><Close /></el-icon>
            <el-icon v-else><Warning /></el-icon>
            <span class="label">{{ result.label }}</span>
            <span class="message">{{ result.message }}</span>
          </div>
        </div>
      </div>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="cancelBatchPublish" v-if="batchPublishing">取消剩余任务</el-button>
          <el-button type="primary" @click="batchPublishDialogVisible = false" v-else>关闭</el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 发布历史抽屉 -->
    <el-drawer v-model="historyDrawerVisible" title="发布历史记录" size="520px">
      <div class="history-drawer-body">
        <div class="history-toolbar">
          <span class="history-sub">自动记录最近提交的任务，支持一键复用标题与视频重发</span>
          <el-button size="small" @click="fetchPublishHistory" :loading="historyLoading">刷新</el-button>
        </div>
        <el-empty v-if="!historyLoading && publishHistory.length === 0" description="还没有发布记录" :image-size="80" />
        <div v-else class="history-list" v-loading="historyLoading">
          <div v-for="item in publishHistory" :key="item.id" class="history-item">
            <div class="history-top">
              <div class="history-badges">
                <el-tag size="small" effect="light">{{ item.platform_name }}</el-tag>
                <el-tag size="small" :type="item.status === 'success' ? 'success' : 'danger'" effect="light">
                  {{ item.status === 'success' ? '已提交' : '失败' }}
                </el-tag>
                <span class="history-schedule">{{ item.schedule_summary }}</span>
              </div>
              <span class="history-time">{{ item.created_at }}</span>
            </div>
            <div class="history-title">{{ item.title || '（无标题）' }}</div>
            <div class="history-meta">
              <span>视频数：{{ (item.file_list || []).length }}</span>
              <span>账号数：{{ (item.account_list || []).length }}</span>
              <span v-if="item.tags && item.tags.length">话题：{{ item.tags.map(t => '#' + t).join(' ') }}</span>
            </div>
            <div v-if="item.status !== 'success' && item.message" class="history-err">
              失败原因：{{ item.message }}
            </div>
            <div class="history-actions">
              <el-button size="small" type="primary" plain @click="reuseHistoryItem(item)">一键复用参数</el-button>
              <el-button size="small" type="danger" link @click="deleteHistoryItem(item.id)">删除记录</el-button>
            </div>
          </div>
        </div>
      </div>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { Upload, Plus, Close, Folder, Check, Warning, VideoCamera, Clock, CopyDocument } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useAccountStore } from '@/stores/account'
import { useAppStore } from '@/stores/app'
import { accountApi } from '@/api/account'
import { materialApi } from '@/api/material'
import { publishApi } from '@/api/publish'
import { http } from '@/utils/request'

const router = useRouter()
const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5409'
const DRAFT_STORAGE_KEY = 'sau_publish_center_draft_v2'

const authHeaders = computed(() => ({
  'Authorization': `Bearer ${localStorage.getItem('token') || ''}`
}))

const activeTab = ref('tab1')
let tabCounter = 1

const appStore = useAppStore()
const accountStore = useAccountStore()

const materialLibraryVisible = ref(false)
const currentUploadTab = ref(null)
const selectedMaterials = ref([])
const materials = computed(() => appStore.materials)
const batchPublishing = ref(false)

const platforms = [
  { key: 3, name: '抖音' },
  { key: 4, name: '快手' },
  { key: 2, name: '视频号' },
  { key: 1, name: '小红书' }
]

const titleTemplates = [
  { name: '干货拆解', text: '【干货必看】3分钟讲清楚核心逻辑，建议先收藏再慢慢看！', topics: ['干货分享', '效率提升'] },
  { name: '好物测评', text: '真实体验一周后才敢说实话：到底值不值得入手？', topics: ['好物推荐', '真实测评'] },
  { name: '日常Vlog', text: '记录生活里的小确幸，今天也请继续加油呀！', topics: ['日常', 'Vlog'] },
  { name: '教程实操', text: '保姆级手把手教学，跟着做一遍就能学会！', topics: ['教程', '新手必看'] }
]

const defaultTabInit = {
  name: 'tab1',
  label: '发布1',
  fileList: [],
  displayFileList: [],
  selectedAccounts: [],
  selectedPlatform: 3,
  title: '',
  productLink: '',
  productTitle: '',
  selectedTopics: [],
  scheduleEnabled: false,
  videosPerDay: 1,
  dailyTimes: ['10:00'],
  startDays: 0,
  publishStatus: null,
  publishing: false,
  isDraft: false,
  isOriginal: false
}

const makeNewTab = () => {
  try {
    return typeof structuredClone === 'function' ? structuredClone(defaultTabInit) : JSON.parse(JSON.stringify(defaultTabInit))
  } catch (e) {
    return JSON.parse(JSON.stringify(defaultTabInit))
  }
}

const tabs = reactive([makeNewTab()])
const currentActiveTabObj = computed(() => tabs.find(t => t.name === activeTab.value) || tabs[0])

const saveDraftToStorage = () => {
  try {
    const snapshot = tabs.map(t => ({ ...t, publishing: false, publishStatus: null }))
    localStorage.setItem(DRAFT_STORAGE_KEY, JSON.stringify({ activeTab: activeTab.value, tabCounter, tabs: snapshot }))
  } catch (e) {}
}

const restoreDraftFromStorage = () => {
  try {
    const raw = localStorage.getItem(DRAFT_STORAGE_KEY)
    if (!raw) return
    const parsed = JSON.parse(raw)
    if (Array.isArray(parsed?.tabs) && parsed.tabs.length > 0) {
      tabs.splice(0, tabs.length, ...parsed.tabs.map(t => ({ ...makeNewTab(), ...t, publishing: false })))
      tabCounter = Math.max(Number(parsed.tabCounter || tabs.length), tabs.length)
      if (parsed.activeTab && tabs.some(t => t.name === parsed.activeTab)) {
        activeTab.value = parsed.activeTab
      }
    }
  } catch (e) {}
}

watch(tabs, saveDraftToStorage, { deep: true })
watch(activeTab, saveDraftToStorage)

const getPlatformName = (key) => platforms.find(p => p.key === key)?.name || '未知平台'
const getPlatformClass = (key) => ({ 3: 'douyin', 4: 'kuaishou', 2: 'channels', 1: 'xiaohongshu' }[key] || 'douyin')
const getAccountsByPlatform = (platformKey) => {
  const name = getPlatformName(platformKey)
  return accountStore.accounts.filter(acc => acc.platform === name)
}

const selectPlatform = (tab, platformKey) => {
  if (tab.selectedPlatform === platformKey) return
  tab.selectedPlatform = platformKey
  const validIds = new Set(getAccountsByPlatform(platformKey).map(a => a.id))
  tab.selectedAccounts = tab.selectedAccounts.filter(id => validIds.has(id))
  if (tab.selectedAccounts.length === 0) {
    const firstNormal = getAccountsByPlatform(platformKey).find(a => a.status === '正常') || getAccountsByPlatform(platformKey)[0]
    if (firstNormal) tab.selectedAccounts.push(firstNormal.id)
  }
}

const toggleAccount = (tab, accountId) => {
  const idx = tab.selectedAccounts.indexOf(accountId)
  if (idx > -1) tab.selectedAccounts.splice(idx, 1)
  else tab.selectedAccounts.push(accountId)
}

const selectAllPlatformAccounts = (tab) => {
  const list = getAccountsByPlatform(tab.selectedPlatform)
  const normals = list.filter(a => a.status === '正常')
  tab.selectedAccounts = (normals.length > 0 ? normals : list).map(a => a.id)
}

const goAccountPage = () => router.push('/account-management')

const applyTitleTemplate = (tab, tpl) => {
  tab.title = tpl.text
  tpl.topics.forEach(t => { if (!tab.selectedTopics.includes(t)) tab.selectedTopics.push(t) })
  ElMessage.success(`已套用「${tpl.name}」模板`)
}

const syncDailyTimes = (tab) => {
  while (tab.dailyTimes.length < tab.videosPerDay) tab.dailyTimes.push('18:00')
  if (tab.dailyTimes.length > tab.videosPerDay) tab.dailyTimes.splice(tab.videosPerDay)
}

const getSchedulePreview = (tab) => {
  if (!tab.scheduleEnabled) return []
  const count = Math.max(tab.fileList.length || 1, 1)
  const perDay = Math.max(Number(tab.videosPerDay || 1), 1)
  const times = tab.dailyTimes.length > 0 ? tab.dailyTimes : ['10:00']
  const baseDate = new Date()
  baseDate.setDate(baseDate.getDate() + 1 + Number(tab.startDays || 0))
  const slots = []
  for (let i = 0; i < Math.min(count, 6); i++) {
    const dayOffset = Math.floor(i / perDay)
    const timeStr = times[i % perDay] || times[0]
    const d = new Date(baseDate)
    d.setDate(baseDate.getDate() + dayOffset)
    const mm = String(d.getMonth() + 1).padStart(2, '0')
    const dd = String(d.getDate()).padStart(2, '0')
    slots.push(`${mm}-${dd} ${timeStr}`)
  }
  if (count > 6) slots.push(`...共${count}条`)
  return slots
}

const topicDialogVisible = ref(false)
const currentTab = ref(null)
const customTopic = ref('')
const recommendedTopics = [
  '游戏', '电影', '音乐', '美食', '旅行', '文化',
  '科技', '生活', '娱乐', '体育', '教育', '艺术',
  '健康', '时尚', '美妆', '摄影', '宠物', '汽车'
]

const addTab = () => {
  tabCounter++
  const newTab = makeNewTab()
  newTab.name = `tab${tabCounter}`
  newTab.label = `发布${tabCounter}`
  tabs.push(newTab)
  activeTab.value = newTab.name
}

const removeTab = (tabName) => {
  const index = tabs.findIndex(tab => tab.name === tabName)
  if (index > -1) {
    tabs.splice(index, 1)
    if (activeTab.value === tabName && tabs.length > 0) activeTab.value = tabs[0].name
  }
}

const syncDialogVisible = ref(false)
const syncTargetPlatforms = ref([])

const openSyncModal = () => {
  const cur = currentActiveTabObj.value
  if (!cur) return
  if (cur.fileList.length === 0) {
    ElMessage.warning('请先在当前任务里上传或选择至少 1 个视频')
    return
  }
  syncTargetPlatforms.value = platforms.filter(p => p.key !== cur.selectedPlatform).map(p => p.key)
  syncDialogVisible.value = true
}

const confirmSyncPlatforms = () => {
  const cur = currentActiveTabObj.value
  if (!cur) return
  if (syncTargetPlatforms.value.length === 0) {
    ElMessage.warning('请至少选择一个目标平台')
    return
  }
  syncTargetPlatforms.value.forEach(platKey => {
    tabCounter++
    const cloned = makeNewTab()
    cloned.name = `tab${tabCounter}`
    cloned.label = `同步${tabCounter}`
    cloned.selectedPlatform = platKey
    cloned.fileList = JSON.parse(JSON.stringify(cur.fileList))
    cloned.displayFileList = JSON.parse(JSON.stringify(cur.displayFileList))
    cloned.title = cur.title
    cloned.selectedTopics = [...cur.selectedTopics]
    cloned.isOriginal = cur.isOriginal
    cloned.scheduleEnabled = cur.scheduleEnabled
    cloned.videosPerDay = cur.videosPerDay
    cloned.dailyTimes = [...cur.dailyTimes]
    cloned.startDays = cur.startDays
    const accs = getAccountsByPlatform(platKey)
    const firstNormal = accs.find(a => a.status === '正常') || accs[0]
    if (firstNormal) cloned.selectedAccounts = [firstNormal.id]
    tabs.push(cloned)
  })
  syncDialogVisible.value = false
  ElMessage.success(`已为 ${syncTargetPlatforms.value.length} 个平台生成发布任务`)
}

const handleUploadSuccess = (response, file, tab) => {
  if (response.code === 200) {
    const filePath = response.data.path || response.data
    const filename = filePath.split('/').pop()
    const fileInfo = {
      name: file.name,
      url: materialApi.getMaterialPreviewUrl(filename),
      path: filePath,
      size: file.size,
      type: file.type
    }
    tab.fileList.push(fileInfo)
    tab.displayFileList = tab.fileList.map(item => ({ name: item.name, url: item.url }))
    ElMessage.success('视频上传成功')
  } else {
    ElMessage.error(response.msg || '上传失败')
  }
}

const handleUploadError = () => ElMessage.error('视频上传失败，请检查文件大小或网络')

const removeFile = (tab, index) => {
  tab.fileList.splice(index, 1)
  tab.displayFileList = tab.fileList.map(item => ({ name: item.name, url: item.url }))
}

const openTopicDialog = (tab) => {
  currentTab.value = tab
  topicDialogVisible.value = true
}

const addCustomTopic = () => {
  if (!customTopic.value.trim()) {
    ElMessage.warning('请输入话题内容')
    return
  }
  const clean = customTopic.value.trim().replace(/^#+/, '')
  if (currentTab.value && !currentTab.value.selectedTopics.includes(clean)) {
    currentTab.value.selectedTopics.push(clean)
    customTopic.value = ''
    ElMessage.success('话题添加成功')
  } else {
    ElMessage.warning('话题已存在')
  }
}

const toggleRecommendedTopic = (topic) => {
  if (!currentTab.value) return
  const index = currentTab.value.selectedTopics.indexOf(topic)
  if (index > -1) currentTab.value.selectedTopics.splice(index, 1)
  else currentTab.value.selectedTopics.push(topic)
}

const removeTopic = (tab, index) => tab.selectedTopics.splice(index, 1)

const confirmTopicSelection = () => {
  topicDialogVisible.value = false
  customTopic.value = ''
  currentTab.value = null
}

const resetTab = (tab) => {
  tab.fileList = []
  tab.displayFileList = []
  tab.title = ''
  tab.selectedTopics = []
  tab.selectedAccounts = []
  tab.productTitle = ''
  tab.productLink = ''
  tab.scheduleEnabled = false
  tab.publishStatus = null
  ElMessage.info('已清空当前任务')
}

const confirmPublish = async (tab) => {
  if (tab.publishing) throw new Error('正在发布中，请稍候...')
  tab.publishing = true
  if (tab.fileList.length === 0) {
    ElMessage.error('请先上传或选择视频文件')
    tab.publishing = false
    throw new Error('请先上传视频文件')
  }
  if (!tab.title.trim()) {
    ElMessage.error('请输入视频标题')
    tab.publishing = false
    throw new Error('请输入标题')
  }
  if (!tab.selectedPlatform) {
    ElMessage.error('请选择发布平台')
    tab.publishing = false
    throw new Error('请选择发布平台')
  }
  if (tab.selectedAccounts.length === 0) {
    ElMessage.error('请选择至少一个发布账号')
    tab.publishing = false
    throw new Error('请选择发布账号')
  }

  const publishData = {
    type: tab.selectedPlatform,
    title: tab.title,
    tags: tab.selectedTopics,
    fileList: tab.fileList.map(file => file.path),
    accountList: tab.selectedAccounts.map(accountId => {
      const account = accountStore.accounts.find(acc => acc.id === accountId)
      return account ? account.filePath : accountId
    }),
    enableTimer: tab.scheduleEnabled ? 1 : 0,
    videosPerDay: tab.scheduleEnabled ? tab.videosPerDay || 1 : 1,
    dailyTimes: tab.scheduleEnabled ? tab.dailyTimes || ['10:00'] : ['10:00'],
    startDays: tab.scheduleEnabled ? tab.startDays || 0 : 0,
    category: tab.isOriginal ? 1 : 0,
    productLink: tab.productLink.trim() || '',
    productTitle: tab.productTitle.trim() || '',
    isDraft: tab.isDraft
  }

  try {
    await http.post('/postVideo', publishData)
    tab.publishStatus = {
      message: '发布任务已提交并开始执行，可在右上角「发布历史」中查看详情',
      type: 'success'
    }
    tab.fileList = []
    tab.displayFileList = []
    tab.title = ''
    tab.selectedTopics = []
    tab.selectedAccounts = []
    tab.scheduleEnabled = false
    void fetchPublishHistory()
  } catch (error) {
    tab.publishStatus = {
      message: `发布失败：${error.message || '请检查网络连接或账号状态'}`,
      type: 'error'
    }
    void fetchPublishHistory()
    throw error
  } finally {
    tab.publishing = false
  }
}

const openMaterialLibrary = async (tab) => {
  currentUploadTab.value = tab
  try {
    const response = await materialApi.getAllMaterials()
    if (response.code === 200) appStore.setMaterials(response.data || [])
  } catch (error) {
    console.error('获取素材列表出错:', error)
  }
  selectedMaterials.value = []
  materialLibraryVisible.value = true
}

const confirmMaterialSelection = () => {
  if (selectedMaterials.value.length === 0) {
    ElMessage.warning('请选择至少一个素材')
    return
  }
  if (currentUploadTab.value) {
    selectedMaterials.value.forEach(materialId => {
      const material = materials.value.find(m => m.id === materialId)
      if (material) {
        const fileInfo = {
          name: material.filename,
          url: materialApi.getMaterialPreviewUrl(material.file_path.split('/').pop()),
          path: material.file_path,
          size: material.filesize * 1024 * 1024,
          type: 'video/mp4'
        }
        if (!currentUploadTab.value.fileList.some(file => file.path === fileInfo.path)) {
          currentUploadTab.value.fileList.push(fileInfo)
        }
      }
    })
    currentUploadTab.value.displayFileList = currentUploadTab.value.fileList.map(item => ({ name: item.name, url: item.url }))
  }
  const addedCount = selectedMaterials.value.length
  materialLibraryVisible.value = false
  selectedMaterials.value = []
  currentUploadTab.value = null
  ElMessage.success(`已添加 ${addedCount} 个素材`)
}

const batchPublishDialogVisible = ref(false)
const currentPublishingTab = ref(null)
const publishProgress = ref(0)
const publishResults = ref([])
const isCancelled = ref(false)

const cancelBatchPublish = () => {
  isCancelled.value = true
  ElMessage.info('正在取消后续任务...')
}

const batchPublish = async () => {
  if (batchPublishing.value) return
  batchPublishing.value = true
  currentPublishingTab.value = null
  publishProgress.value = 0
  publishResults.value = []
  isCancelled.value = false
  batchPublishDialogVisible.value = true
  try {
    for (let i = 0; i < tabs.length; i++) {
      if (isCancelled.value) {
        publishResults.value.push({ label: tabs[i].label, status: 'cancelled', message: '已取消' })
        continue
      }
      const tab = tabs[i]
      currentPublishingTab.value = tab
      publishProgress.value = Math.floor((i / tabs.length) * 100)
      try {
        await confirmPublish(tab)
        publishResults.value.push({ label: tab.label, status: 'success', message: '发布成功' })
      } catch (error) {
        publishResults.value.push({ label: tab.label, status: 'error', message: error.message })
      }
    }
    publishProgress.value = 100
  } finally {
    batchPublishing.value = false
    isCancelled.value = false
  }
}

const historyDrawerVisible = ref(false)
const historyLoading = ref(false)
const publishHistory = ref([])

const fetchPublishHistory = async () => {
  historyLoading.value = true
  try {
    const res = await publishApi.getPublishHistory(50)
    if (res.code === 200) publishHistory.value = res.data || []
  } catch (e) {} finally {
    historyLoading.value = false
  }
}

const openHistoryDrawer = () => {
  historyDrawerVisible.value = true
  void fetchPublishHistory()
}

const deleteHistoryItem = async (id) => {
  try {
    await publishApi.deletePublishRecord(id)
    publishHistory.value = publishHistory.value.filter(i => i.id !== id)
    ElMessage.success('记录已删除')
  } catch (e) {
    ElMessage.error('删除失败')
  }
}

const reuseHistoryItem = (item) => {
  const cur = currentActiveTabObj.value
  if (!cur) return
  cur.selectedPlatform = item.platform_type || 3
  cur.title = item.title || ''
  cur.selectedTopics = Array.isArray(item.tags) ? [...item.tags] : []
  cur.isDraft = Boolean(item.is_draft)
  cur.fileList = (item.file_list || []).map(fp => {
    const filename = String(fp).split(/[/\\]/).pop()
    const matchedMat = materials.value.find(m => m.file_path === fp)
    return {
      name: matchedMat?.filename || filename,
      url: materialApi.getMaterialPreviewUrl(filename),
      path: fp,
      size: matchedMat ? matchedMat.filesize * 1024 * 1024 : 0,
      type: 'video/mp4'
    }
  })
  cur.displayFileList = cur.fileList.map(f => ({ name: f.name, url: f.url }))
  cur.selectedAccounts = accountStore.accounts
    .filter(a => (item.account_list || []).includes(a.filePath) || (item.account_list || []).includes(a.id))
    .map(a => a.id)
  historyDrawerVisible.value = false
  ElMessage.success('已把该历史任务的参数回填到当前编辑区')
}

const initData = async () => {
  const [accRes, matRes] = await Promise.allSettled([
    accountApi.getAccounts(),
    materialApi.getAllMaterials()
  ])
  if (accRes.status === 'fulfilled' && accRes.value.code === 200) {
    accountStore.setAccounts(accRes.value.data || [])
  }
  if (matRes.status === 'fulfilled' && matRes.value.code === 200) {
    appStore.setMaterials(matRes.value.data || [])
  }
  void fetchPublishHistory()
}

onMounted(() => {
  restoreDraftFromStorage()
  void initData()
})
</script>

<style lang="scss" scoped>
@use '@/styles/variables.scss' as *;

.publish-center {
  display: flex;
  flex-direction: column;
  height: 100%;

  .header-actions {
    display: flex;
    gap: 10px;
    align-items: center;
    .history-badge {
      margin-left: 4px;
    }
  }

  .tab-management {
    background-color: #fff;
    border-radius: $border-radius-lg;
    border: 1px solid $border-light;
    box-shadow: $box-shadow-light;
    margin-bottom: 18px;
    padding: 14px 18px;

    .tab-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 14px;
      flex-wrap: wrap;

      .tab-list {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        flex: 1;
        min-width: 0;

        .tab-item {
          display: inline-flex;
          align-items: center;
          gap: 7px;
          padding: 6px 13px;
          background-color: #f8fafc;
          border: 1px solid $border-light;
          border-radius: 9px;
          cursor: pointer;
          transition: all 0.18s ease;
          font-size: 13px;
          font-weight: 500;
          color: $text-regular;
          height: 34px;

          .tab-plat-dot {
            width: 7px;
            height: 7px;
            border-radius: 50%;
            &.douyin { background: #f43f5e; }
            &.kuaishou { background: #f97316; }
            &.channels { background: #f59e0b; }
            &.xiaohongshu { background: #ec4899; }
          }

          .tab-file-pill {
            font-size: 11px;
            padding: 1px 6px;
            border-radius: 999px;
            background: rgba(15, 23, 42, 0.08);
          }

          &:hover {
            background-color: $primary-light;
            border-color: rgba($primary-color, 0.3);
            color: $primary-color;
          }

          &.active {
            background: linear-gradient(135deg, #4f46e5, #6366f1);
            border-color: transparent;
            color: #fff;
            box-shadow: 0 4px 10px -2px rgba($primary-color, 0.45);

            .tab-file-pill {
              background: rgba(255, 255, 255, 0.22);
              color: #fff;
            }

            .close-icon {
              color: #fff;
              &:hover { background-color: rgba(255, 255, 255, 0.2); }
            }
          }

          .close-icon {
            padding: 2px;
            border-radius: 4px;
            font-size: 12px;
            &:hover { background-color: rgba(0, 0, 0, 0.1); }
          }
        }
      }

      .tab-actions {
        display: flex;
        gap: 8px;
        flex-shrink: 0;
      }
    }
  }

  .publish-content {
    flex: 1;
    background-color: #fff;
    border-radius: $border-radius-lg;
    border: 1px solid $border-light;
    box-shadow: $box-shadow-light;
    padding: 24px 28px;

    .tab-content-wrapper {
      display: flex;
      justify-content: center;

      .tab-content {
        width: 100%;
        max-width: 920px;

        .publish-status { margin-bottom: 18px; }

        .section-card {
          margin-bottom: 18px;
          padding: 18px 20px;
          border-radius: 12px;
          background: #f8fafc;
          border: 1px solid $border-lighter;

          .section-head {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 12px;
            flex-wrap: wrap;
            margin-bottom: 14px;

            h3 {
              font-size: 15px;
              font-weight: 600;
              color: $text-primary;
              margin: 0;
              display: flex;
              align-items: center;
              gap: 8px;

              &::before {
                content: '';
                width: 3px;
                height: 15px;
                border-radius: 999px;
                background: $primary-color;
                display: inline-block;
              }
            }
          }
        }

        .platform-cards {
          display: flex;
          flex-wrap: wrap;
          gap: 10px;
          margin-bottom: 14px;

          .platform-card-btn {
            border: 1px solid $border-light;
            background: #ffffff;
            border-radius: 10px;
            padding: 9px 14px;
            display: inline-flex;
            align-items: center;
            gap: 8px;
            cursor: pointer;
            font-size: 13px;
            font-weight: 600;
            color: $text-regular;
            transition: all 0.18s ease;

            .plat-dot { width: 8px; height: 8px; border-radius: 50%; }
            &.douyin .plat-dot { background: #f43f5e; }
            &.kuaishou .plat-dot { background: #f97316; }
            &.channels .plat-dot { background: #f59e0b; }
            &.xiaohongshu .plat-dot { background: #ec4899; }

            .plat-count {
              font-size: 11px;
              padding: 1px 6px;
              border-radius: 999px;
              background: #f1f5f9;
              color: $text-secondary;
            }

            &:hover { border-color: rgba($primary-color, 0.4); }
            &.active {
              border-color: $primary-color;
              background: $primary-light;
              color: $primary-color;
              box-shadow: 0 0 0 2px rgba($primary-color, 0.12);
              .plat-count { background: rgba($primary-color, 0.14); color: $primary-color; }
            }
          }
        }

        .inline-accounts-box {
          padding: 12px 14px;
          background: #ffffff;
          border: 1px solid $border-light;
          border-radius: 10px;

          .inline-accounts-label {
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 12px;
            color: $text-secondary;
            margin-bottom: 10px;
          }

          .account-chip-list {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;

            .account-chip {
              display: inline-flex;
              align-items: center;
              gap: 8px;
              padding: 6px 12px;
              border-radius: 9px;
              border: 1px solid $border-light;
              background: #f8fafc;
              cursor: pointer;
              font-size: 13px;
              color: $text-primary;
              transition: all 0.16s ease;

              .acc-avatar {
                width: 22px;
                height: 22px;
                border-radius: 6px;
                background: #64748b;
                color: #fff;
                font-size: 11px;
                font-weight: 700;
                display: inline-flex;
                align-items: center;
                justify-content: center;
              }

              .acc-status {
                font-size: 11px;
                padding: 1px 6px;
                border-radius: 999px;
                &.ok { background: #ecfdf5; color: #047857; }
                &.warn { background: #fef2f2; color: #b91c1c; }
              }

              &.selected {
                border-color: $primary-color;
                background: $primary-light;
                .acc-avatar { background: $primary-color; }
              }
            }
          }

          .no-account-tip {
            display: flex;
            align-items: center;
            gap: 10px;
            font-size: 13px;
            color: $text-secondary;
          }
        }

        .inline-video-upload {
          width: 100%;
          :deep(.el-upload-dragger) { padding: 22px 16px; }
        }

        .uploaded-files {
          margin-top: 14px;
          h4 { font-size: 13px; font-weight: 600; color: $text-regular; margin-bottom: 8px; }
          .file-list {
            display: flex;
            flex-direction: column;
            gap: 8px;
            .file-item {
              display: flex;
              align-items: center;
              gap: 10px;
              padding: 10px 14px;
              background: #ffffff;
              border: 1px solid $border-light;
              border-radius: 10px;
              .file-icon { color: $success-color; font-size: 17px; }
              .file-size { color: $text-secondary; font-size: 12px; margin-left: auto; }
            }
          }
        }

        .template-pills {
          display: flex;
          align-items: center;
          gap: 6px;
          flex-wrap: wrap;
          .tpl-hint { font-size: 12px; color: $text-secondary; }
        }

        .title-block { margin-bottom: 14px; }

        .topic-display {
          padding: 12px 14px;
          border-radius: 10px;
          background: #ffffff;
          border: 1px solid $border-light;
          margin-bottom: 12px;

          .topic-row-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
          }
          .sub-label { font-size: 13px; font-weight: 500; color: $text-regular; }
          .selected-topics { display: flex; flex-wrap: wrap; gap: 8px; }
          .empty-topic-hint { font-size: 12px; color: $text-placeholder; }
        }

        .platform-extras { display: flex; gap: 20px; flex-wrap: wrap; margin-top: 8px; }

        .product-section {
          margin-top: 14px;
          padding-top: 12px;
          border-top: 1px dashed $border-light;
          .sub-label { font-size: 13px; font-weight: 500; color: $text-regular; margin-bottom: 8px; }
          .product-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
        }

        .schedule-settings {
          padding: 14px;
          background: #ffffff;
          border: 1px solid $border-light;
          border-radius: 10px;

          .schedule-grid {
            display: flex;
            gap: 20px;
            flex-wrap: wrap;
            margin-bottom: 12px;
            .schedule-item {
              display: flex;
              align-items: center;
              gap: 8px;
              .label { font-size: 13px; color: $text-regular; }
            }
          }

          .schedule-times-row {
            display: flex;
            align-items: center;
            gap: 10px;
            flex-wrap: wrap;
            margin-bottom: 12px;
            .label { font-size: 13px; color: $text-regular; }
            .times-wrap { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; }
          }

          .schedule-preview {
            display: flex;
            align-items: center;
            flex-wrap: wrap;
            gap: 6px;
            padding-top: 10px;
            border-top: 1px solid $border-lighter;
            .preview-title { font-size: 12px; font-weight: 600; color: $text-secondary; }
          }
        }

        .immediate-tip { font-size: 13px; color: $text-secondary; }

        .action-buttons {
          display: flex;
          justify-content: flex-end;
          gap: 10px;
          margin-top: 20px;
          padding-top: 18px;
          border-top: 1px solid $border-light;
        }
      }
    }
  }

  .material-library-content {
    max-height: 420px;
    overflow-y: auto;
    .material-list {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
      gap: 10px;
      .material-item {
        margin-right: 0;
        padding: 10px 12px;
        border: 1px solid $border-light;
        border-radius: 10px;
        height: auto;
        .material-info {
          .material-name { font-weight: 600; color: $text-primary; margin-bottom: 4px; }
          .material-details { display: flex; gap: 12px; font-size: 12px; color: $text-secondary; }
        }
      }
    }
  }

  .sync-dialog-body {
    .sync-tip { font-size: 13px; color: $text-secondary; margin-bottom: 14px; line-height: 1.6; }
    .sync-plat-group { display: flex; flex-direction: column; gap: 10px; }
    .sync-acc-count { font-size: 12px; color: $text-secondary; }
  }

  .topic-dialog-content {
    .custom-topic-input { display: flex; gap: 10px; margin-bottom: 20px; }
    .recommended-topics {
      h4 { font-size: 14px; font-weight: 600; color: $text-primary; margin: 0 0 12px 0; }
      .topic-grid { display: flex; flex-wrap: wrap; gap: 8px; }
    }
  }

  .publish-progress {
    padding: 8px 0;
    .current-publishing { margin: 12px 0; text-align: center; color: $text-regular; font-size: 13px; }
    .publish-results {
      margin-top: 14px;
      border-top: 1px solid $border-lighter;
      padding-top: 10px;
      max-height: 260px;
      overflow-y: auto;
      .result-item {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 6px 0;
        font-size: 13px;
        &.success { color: $success-color; }
        &.error { color: $danger-color; }
        &.cancelled { color: $text-secondary; }
      }
    }
  }

  .history-drawer-body {
    .history-toolbar {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 16px;
      gap: 10px;
      .history-sub { font-size: 12px; color: $text-secondary; }
    }
    .history-list {
      display: flex;
      flex-direction: column;
      gap: 12px;
      .history-item {
        padding: 14px;
        border-radius: 12px;
        border: 1px solid $border-light;
        background: #f8fafc;
        .history-top {
          display: flex;
          justify-content: space-between;
          align-items: center;
          gap: 8px;
          margin-bottom: 8px;
          .history-badges { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; }
          .history-schedule { font-size: 12px; color: $text-secondary; }
          .history-time { font-size: 11px; color: $text-placeholder; }
        }
        .history-title { font-size: 14px; font-weight: 600; color: $text-primary; margin-bottom: 6px; }
        .history-meta { display: flex; flex-wrap: wrap; gap: 12px; font-size: 12px; color: $text-secondary; margin-bottom: 8px; }
        .history-err { font-size: 12px; color: $danger-color; background: #fef2f2; padding: 6px 10px; border-radius: 8px; margin-bottom: 8px; }
        .history-actions { display: flex; justify-content: space-between; align-items: center; }
      }
    }
  }
}
</style>
