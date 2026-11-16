<template>
  <div class="account-management">
    <div class="studio-page-header">
      <div class="header-titles">
        <h1>账号管理</h1>
        <p>管理抖音、快手、视频号与小红书创作者账号登录态与 Cookie</p>
      </div>
      <div class="header-actions">
        <el-button @click="fetchAccounts" :disabled="appStore.isAccountRefreshing">
          <el-icon :class="{ 'is-loading': appStore.isAccountRefreshing }"><Refresh /></el-icon>
          <span>{{ appStore.isAccountRefreshing ? '验证中...' : '同步验证' }}</span>
        </el-button>
        <el-button type="primary" @click="handleAddAccount">
          <el-icon><Plus /></el-icon>
          <span>添加账号</span>
        </el-button>
      </div>
    </div>

    <el-card class="account-card" shadow="never">
      <div class="toolbar-row">
        <div class="platform-filter-pills">
          <button
            v-for="tab in platformTabs"
            :key="tab.name"
            type="button"
            :class="['filter-pill', { active: activeTab === tab.name }]"
            @click="activeTab = tab.name"
          >
            <span class="pill-name">{{ tab.label }}</span>
            <span class="pill-count">{{ tab.count }}</span>
          </button>
        </div>

        <div class="search-box">
          <el-input
            v-model="searchKeyword"
            placeholder="搜索账号名称..."
            prefix-icon="Search"
            clearable
            @clear="handleSearch"
            @input="handleSearch"
          />
        </div>
      </div>

      <div v-if="displayedAccounts.length > 0" class="account-list">
        <el-table :data="displayedAccounts" style="width: 100%">
          <el-table-column label="账号" min-width="220">
            <template #default="scope">
              <div class="account-cell">
                <div
                  class="avatar-badge"
                  :style="{ background: getAvatarGradient(scope.row.name) }"
                >
                  {{ (scope.row.name || '?').slice(0, 1).toUpperCase() }}
                </div>
                <div class="account-meta">
                  <div class="account-name">{{ scope.row.name }}</div>
                  <div class="account-id">ID: {{ scope.row.id }}</div>
                </div>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="platform" label="平台" width="140">
            <template #default="scope">
              <span :class="['platform-badge', getPlatformClass(scope.row.platform)]">
                <i class="dot"></i>
                {{ scope.row.platform }}
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="status" label="登录状态" width="150">
            <template #default="scope">
              <el-tag
                :type="getStatusTagType(scope.row.status)"
                effect="light"
                :class="{'clickable-status': isStatusClickable(scope.row.status)}"
                @click="handleStatusClick(scope.row)"
              >
                <el-icon :class="scope.row.status === '验证中' ? 'is-loading' : ''" v-if="scope.row.status === '验证中'">
                  <Loading />
                </el-icon>
                {{ scope.row.status }}
                <span v-if="isStatusClickable(scope.row.status)" class="relogin-hint">· 重登</span>
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" min-width="320" align="right">
            <template #default="scope">
              <div class="row-actions">
                <el-button size="small" @click="handleEdit(scope.row)">编辑</el-button>
                <el-button size="small" type="primary" plain :icon="Download" @click="handleDownloadCookie(scope.row)">导出Cookie</el-button>
                <el-button size="small" plain :icon="Upload" @click="handleUploadCookie(scope.row)">导入Cookie</el-button>
                <el-button size="small" type="danger" plain @click="handleDelete(scope.row)">删除</el-button>
              </div>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <div v-else class="empty-data">
        <el-empty :description="emptyDescription" :image-size="96">
          <el-button type="primary" @click="handleAddAccount">
            <el-icon><Plus /></el-icon>
            <span>扫码添加账号</span>
          </el-button>
        </el-empty>
      </div>
    </el-card>

    <!-- 添加/编辑账号对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogType === 'add' ? '添加平台账号' : '编辑 / 重新登录账号'"
      width="480px"
      :close-on-click-modal="false"
      :close-on-press-escape="true"
      :show-close="true"
      @close="handleDialogClose"
    >
      <el-form :model="accountForm" label-position="top" :rules="rules" ref="accountFormRef" class="account-dialog-form">
        <el-form-item label="选择平台" prop="platform">
          <el-select
            v-model="accountForm.platform"
            placeholder="请选择要绑定的视频平台"
            style="width: 100%"
            :disabled="dialogType === 'edit' || sseConnecting"
          >
            <el-option label="快手" value="快手" />
            <el-option label="抖音" value="抖音" />
            <el-option label="视频号" value="视频号" />
            <el-option label="小红书" value="小红书" />
          </el-select>
        </el-form-item>
        <el-form-item label="账号备注名称" prop="name">
          <el-input
            v-model="accountForm.name"
            placeholder="例如：主号-产品科普"
            :disabled="sseConnecting"
          />
        </el-form-item>

        <!-- 二维码显示区域 -->
        <div v-if="sseConnecting" class="qrcode-container">
          <div v-if="qrCodeData && !loginStatus" class="qrcode-wrapper">
            <div class="qrcode-frame">
              <img :src="qrCodeData" alt="登录二维码" class="qrcode-image" />
            </div>
            <p class="qrcode-tip">请打开 <strong>{{ accountForm.platform }}</strong> APP 扫描上方二维码登录</p>
          </div>
          <div v-else-if="!qrCodeData && !loginStatus" class="loading-wrapper">
            <el-icon class="is-loading"><Refresh /></el-icon>
            <span class="state-title">正在生成登录二维码...</span>
            <span class="state-sub">首次拉起浏览器可能需要几秒钟，请勿关闭弹窗</span>
          </div>
          <div v-else-if="loginStatus === '200'" class="success-wrapper">
            <el-icon><CircleCheckFilled /></el-icon>
            <span class="state-title">登录成功</span>
            <span class="state-sub">正在同步账号状态...</span>
          </div>
          <div v-else-if="loginStatus === '500'" class="error-wrapper">
            <el-icon><CircleCloseFilled /></el-icon>
            <span class="state-title">登录失败或已超时</span>
            <span class="state-sub">请检查网络状态后重试</span>
          </div>
        </div>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button
            type="primary"
            @click="submitAccountForm"
            :loading="sseConnecting"
            :disabled="sseConnecting"
          >
            {{ sseConnecting ? '等待扫码中...' : '确认' }}
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onBeforeUnmount } from 'vue'
import { Refresh, CircleCheckFilled, CircleCloseFilled, Download, Upload, Loading, Plus } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { accountApi } from '@/api/account'
import { useAccountStore } from '@/stores/account'
import { useAppStore } from '@/stores/app'
import { http } from '@/utils/request'

// 获取账号状态管理
const accountStore = useAccountStore()
// 获取应用状态管理
const appStore = useAppStore()

// 当前激活的标签页
const activeTab = ref('all')

// 搜索关键词
const searchKeyword = ref('')

// 获取账号数据（快速，不验证）
const fetchAccountsQuick = async () => {
  try {
    const res = await accountApi.getAccounts()
    if (res.code === 200 && res.data) {
      // 将所有账号的状态暂时设为"验证中"
      const accountsWithPendingStatus = res.data.map(account => {
        const updatedAccount = [...account];
        updatedAccount[4] = -1; // -1 表示验证中的临时状态
        return updatedAccount;
      });
      accountStore.setAccounts(accountsWithPendingStatus);
    }
  } catch (error) {
    console.error('快速获取账号数据失败:', error)
  }
}

// 获取账号数据（带验证）
const fetchAccounts = async () => {
  if (appStore.isAccountRefreshing) return

  appStore.setAccountRefreshing(true)

  try {
    const res = await accountApi.getValidAccounts()
    if (res.code === 200 && res.data) {
      accountStore.setAccounts(res.data)
      ElMessage.success('账号数据获取成功')
      // 标记为已访问
      if (appStore.isFirstTimeAccountManagement) {
        appStore.setAccountManagementVisited()
      }
    } else {
      ElMessage.error('获取账号数据失败')
    }
  } catch (error) {
    console.error('获取账号数据失败:', error)
    ElMessage.error('获取账号数据失败')
  } finally {
    appStore.setAccountRefreshing(false)
  }
}

// 后台验证所有账号（优化版本，使用setTimeout避免阻塞UI）
const validateAllAccountsInBackground = async () => {
  // 使用setTimeout将验证过程放在下一个事件循环，避免阻塞UI
  setTimeout(async () => {
    try {
      const res = await accountApi.getValidAccounts()
      if (res.code === 200 && res.data) {
        accountStore.setAccounts(res.data)
      }
    } catch (error) {
      console.error('后台验证账号失败:', error)
    }
  }, 0)
}

// 页面加载时获取账号数据
onMounted(() => {
  // 快速获取账号列表（不验证），立即显示
  fetchAccountsQuick()

  // 在后台验证所有账号
  setTimeout(() => {
    validateAllAccountsInBackground()
  }, 100) // 稍微延迟一下，让用户看到快速加载的效果
})

// 获取平台标签类型
const getPlatformTagType = (platform) => {
  const typeMap = {
    '快手': 'success',
    '抖音': 'danger',
    '视频号': 'warning',
    '小红书': 'info'
  }
  return typeMap[platform] || 'info'
}

// 判断状态是否可点击（异常状态可点击）
const isStatusClickable = (status) => {
  return status === '异常'; // 只有异常状态可点击，验证中不可点击
}

// 获取状态标签类型
const getStatusTagType = (status) => {
  if (status === '验证中') {
    return 'info'; // 验证中使用灰色
  } else if (status === '正常') {
    return 'success'; // 正常使用绿色
  } else {
    return 'danger'; // 无效使用红色
  }
}

// 处理状态点击事件
const handleStatusClick = (row) => {
  if (isStatusClickable(row.status)) {
    // 触发重新登录流程
    handleReLogin(row)
  }
}

// 过滤后的账号列表
const filteredAccounts = computed(() => {
  if (!searchKeyword.value) return accountStore.accounts
  return accountStore.accounts.filter(account =>
    account.name.includes(searchKeyword.value)
  )
})

// 按平台过滤的账号列表
const filteredKuaishouAccounts = computed(() => {
  return filteredAccounts.value.filter(account => account.platform === '快手')
})

const filteredDouyinAccounts = computed(() => {
  return filteredAccounts.value.filter(account => account.platform === '抖音')
})

const filteredChannelsAccounts = computed(() => {
  return filteredAccounts.value.filter(account => account.platform === '视频号')
})

const filteredXiaohongshuAccounts = computed(() => {
  return filteredAccounts.value.filter(account => account.platform === '小红书')
})

const platformTabs = computed(() => [
  { name: 'all', label: '全部平台', count: filteredAccounts.value.length },
  { name: 'kuaishou', label: '快手', count: filteredKuaishouAccounts.value.length },
  { name: 'douyin', label: '抖音', count: filteredDouyinAccounts.value.length },
  { name: 'channels', label: '视频号', count: filteredChannelsAccounts.value.length },
  { name: 'xiaohongshu', label: '小红书', count: filteredXiaohongshuAccounts.value.length }
])

const displayedAccounts = computed(() => {
  const map = {
    all: filteredAccounts.value,
    kuaishou: filteredKuaishouAccounts.value,
    douyin: filteredDouyinAccounts.value,
    channels: filteredChannelsAccounts.value,
    xiaohongshu: filteredXiaohongshuAccounts.value
  }
  return map[activeTab.value] || filteredAccounts.value
})

const emptyDescription = computed(() => {
  const labelMap = {
    all: '暂无平台账号，点击下方按钮扫码绑定',
    kuaishou: '暂无快手账号',
    douyin: '暂无抖音账号',
    channels: '暂无视频号账号',
    xiaohongshu: '暂无小红书账号'
  }
  return labelMap[activeTab.value] || '暂无账号数据'
})

const getPlatformClass = (platform) => {
  const map = {
    '快手': 'kuaishou',
    '抖音': 'douyin',
    '视频号': 'channels',
    '小红书': 'xiaohongshu'
  }
  return map[platform] || 'default'
}

const getAvatarGradient = (name) => {
  const palettes = [
    'linear-gradient(135deg, #4f46e5, #818cf8)',
    'linear-gradient(135deg, #0ea5e9, #38bdf8)',
    'linear-gradient(135deg, #10b981, #34d399)',
    'linear-gradient(135deg, #f59e0b, #fbbf24)',
    'linear-gradient(135deg, #ec4899, #f472b6)'
  ]
  const text = String(name || 'A')
  let hash = 0
  for (let i = 0; i < text.length; i++) {
    hash = text.charCodeAt(i) + ((hash << 5) - hash)
  }
  return palettes[Math.abs(hash) % palettes.length]
}

// 搜索处理
const handleSearch = () => {
  // 搜索逻辑已通过计算属性实现
}

// 对话框相关
const dialogVisible = ref(false)
const dialogType = ref('add') // 'add' 或 'edit'
const accountFormRef = ref(null)

// 账号表单
const accountForm = reactive({
  id: null,
  name: '',
  platform: '',
  status: '正常'
})

// 表单验证规则
const rules = {
  platform: [{ required: true, message: '请选择平台', trigger: 'change' }],
  name: [{ required: true, message: '请输入账号名称', trigger: 'blur' }]
}

// SSE连接状态
const sseConnecting = ref(false)
const qrCodeData = ref('')
const loginStatus = ref('')

// 添加账号
const handleAddAccount = () => {
  const tabPlatformMap = {
    kuaishou: '快手',
    douyin: '抖音',
    channels: '视频号',
    xiaohongshu: '小红书'
  }
  dialogType.value = 'add'
  Object.assign(accountForm, {
    id: null,
    name: '',
    platform: tabPlatformMap[activeTab.value] || '',
    status: '正常'
  })
  // 重置SSE状态
  sseConnecting.value = false
  qrCodeData.value = ''
  loginStatus.value = ''
  dialogVisible.value = true
}

// 编辑账号
const handleEdit = (row) => {
  dialogType.value = 'edit'
  Object.assign(accountForm, {
    id: row.id,
    name: row.name,
    platform: row.platform,
    status: row.status
  })
  dialogVisible.value = true
}

// 删除账号
const handleDelete = (row) => {
  ElMessageBox.confirm(
    `确定要删除账号 ${row.name} 吗？`,
    '警告',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    }
  )
    .then(async () => {
      try {
        // 调用API删除账号
        const response = await accountApi.deleteAccount(row.id)

        if (response.code === 200) {
          // 从状态管理中删除账号
          accountStore.deleteAccount(row.id)
          ElMessage({
            type: 'success',
            message: '删除成功',
          })
        } else {
          ElMessage.error(response.msg || '删除失败')
        }
      } catch (error) {
        console.error('删除账号失败:', error)
        ElMessage.error('删除账号失败')
      }
    })
    .catch(() => {
      // 取消删除
    })
}

// 下载Cookie文件
const handleDownloadCookie = (row) => {
  // 从后端获取Cookie文件
  const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5409'
  const downloadUrl = `${baseUrl}/downloadCookie?filePath=${encodeURIComponent(row.filePath)}`

  // 创建一个隐藏的链接来触发下载
  const link = document.createElement('a')
  link.href = downloadUrl
  link.download = `${row.name}_cookie.json`
  link.target = '_blank'
  link.style.display = 'none'
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}

// 上传Cookie文件
const handleUploadCookie = (row) => {
  // 创建一个隐藏的文件输入框
  const input = document.createElement('input')
  input.type = 'file'
  input.accept = '.json'
  input.style.display = 'none'
  document.body.appendChild(input)

  input.onchange = async (event) => {
    const file = event.target.files[0]
    if (!file) return

    // 检查文件类型
    if (!file.name.endsWith('.json')) {
      ElMessage.error('请选择JSON格式的Cookie文件')
      document.body.removeChild(input)
      return
    }

    try {
      // 创建FormData对象
      const formData = new FormData()
      formData.append('file', file)
      formData.append('id', row.id)
      formData.append('platform', row.platform)

      // 使用统一的http封装发送上传请求
      const result = await http.upload('/uploadCookie', formData)

      ElMessage.success('Cookie文件上传成功')
      // 刷新账号列表以显示更新
      fetchAccounts()
    } catch (error) {
      ElMessage.error('Cookie文件上传失败')
    } finally {
      document.body.removeChild(input)
    }
  }

  input.click()
}

// 重新登录账号
const handleReLogin = (row) => {
  // 设置表单信息
  dialogType.value = 'edit'
  Object.assign(accountForm, {
    id: row.id,
    name: row.name,
    platform: row.platform,
    status: row.status
  })

  // 重置SSE状态
  sseConnecting.value = false
  qrCodeData.value = ''
  loginStatus.value = ''

  // 显示对话框
  dialogVisible.value = true

  // 立即开始登录流程
  setTimeout(() => {
    connectSSE(row.platform, row.name)
  }, 300)
}

// SSE事件源对象
let eventSource = null
let qrTimeoutTimer = null
let totalTimeoutTimer = null

const clearSSETimers = () => {
  if (qrTimeoutTimer) {
    clearTimeout(qrTimeoutTimer)
    qrTimeoutTimer = null
  }
  if (totalTimeoutTimer) {
    clearTimeout(totalTimeoutTimer)
    totalTimeoutTimer = null
  }
}

// 关闭SSE连接
const closeSSEConnection = () => {
  clearSSETimers()
  if (eventSource) {
    eventSource.close()
    eventSource = null
  }
}

const handleDialogClose = () => {
  closeSSEConnection()
  sseConnecting.value = false
  qrCodeData.value = ''
  loginStatus.value = ''
}

// 建立SSE连接
const connectSSE = (platform, name) => {
  // 关闭可能存在的连接
  closeSSEConnection()

  // 设置连接状态
  sseConnecting.value = true
  qrCodeData.value = ''
  loginStatus.value = ''

  // 获取平台类型编号
  const platformTypeMap = {
    '小红书': '1',
    '视频号': '2',
    '抖音': '3',
    '快手': '4'
  }

  const type = platformTypeMap[platform] || '1'

  // 创建SSE连接
  const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5409'
  const url = `${baseUrl}/login?type=${type}&id=${encodeURIComponent(name)}`

  eventSource = new EventSource(url)

  // 超时兜底：45秒未收到二维码或240秒未完成登录，自动中断避免无限“请求中...”
  qrTimeoutTimer = setTimeout(() => {
    if (sseConnecting.value && !qrCodeData.value && !loginStatus.value) {
      closeSSEConnection()
      sseConnecting.value = false
      ElMessage.error('获取登录二维码超时，请关闭弹窗重试一次')
    }
  }, 45000)

  totalTimeoutTimer = setTimeout(() => {
    if (sseConnecting.value && !loginStatus.value) {
      closeSSEConnection()
      loginStatus.value = '500'
      ElMessage.error('扫码登录超时，请重试')
      setTimeout(() => {
        sseConnecting.value = false
        qrCodeData.value = ''
        loginStatus.value = ''
      }, 1500)
    }
  }, 240000)

  // 监听消息
  eventSource.onmessage = (event) => {
    const data = (event.data || '').trim()
    if (!data) return

    if (data.startsWith('ERROR:')) {
      ElMessage.error(data.slice(6) || '登录失败，请稍后重试')
      return
    }

    // 如果还没有二维码数据，且数据长度较长，认为是二维码
    if (data !== '200' && data !== '500' && (data.startsWith('data:image') || data.startsWith('http://') || data.startsWith('https://') || data.length > 100)) {
      try {
        if (qrTimeoutTimer) {
          clearTimeout(qrTimeoutTimer)
          qrTimeoutTimer = null
        }
        if (data.startsWith('data:image') || data.startsWith('http://') || data.startsWith('https://')) {
          qrCodeData.value = data
        } else {
          qrCodeData.value = `data:image/png;base64,${data}`
        }
      } catch (error) {
        // 处理二维码数据出错
      }
    }
    // 如果收到状态码
    else if (data === '200' || data === '500') {
      loginStatus.value = data

      // 如果登录成功
      if (data === '200') {
        closeSSEConnection()
        setTimeout(() => {
          // 1秒后关闭对话框并开始刷新
          setTimeout(() => {
            dialogVisible.value = false
            sseConnecting.value = false

            // 根据是否是重新登录显示不同提示
            ElMessage.success(dialogType.value === 'edit' ? '重新登录成功' : '账号添加成功')

            // 显示更新账号信息提示
            ElMessage({
              type: 'info',
              message: '正在同步账号信息...',
              duration: 0
            })

            // 触发刷新操作
            fetchAccounts().then(() => {
              // 刷新完成后关闭提示
              ElMessage.closeAll()
              ElMessage.success('账号信息已更新')
            })
          }, 1000)
        }, 1000)
      } else {
        // 登录失败，关闭连接
        closeSSEConnection()

        // 2秒后重置状态，允许重试
        setTimeout(() => {
          sseConnecting.value = false
          qrCodeData.value = ''
          loginStatus.value = ''
        }, 2000)
      }
    }
  }

  // 监听错误
  eventSource.onerror = (error) => {
    console.error('SSE连接错误:', error)
    ElMessage.error('连接服务器失败，请稍后再试')
    closeSSEConnection()
    sseConnecting.value = false
  }
}

// 提交账号表单
const submitAccountForm = () => {
  accountFormRef.value.validate(async (valid) => {
    if (valid) {
      if (dialogType.value === 'add') {
        // 建立SSE连接
        connectSSE(accountForm.platform, accountForm.name)
      } else {
        // 编辑账号逻辑
        try {
          // 将平台名称转换为类型数字
          const platformTypeMap = {
            '小红书': 1,
            '视频号': 2,
            '抖音': 3,
            '快手': 4
          };
          const type = platformTypeMap[accountForm.platform] || 1;

          const res = await accountApi.updateAccount({
            id: accountForm.id,
            type: type,
            userName: accountForm.name
          })
          if (res.code === 200) {
            // 更新状态管理中的账号
            const updatedAccount = {
              id: accountForm.id,
              name: accountForm.name,
              platform: accountForm.platform,
              status: accountForm.status // Keep the existing status
            };
            accountStore.updateAccount(accountForm.id, updatedAccount)
            ElMessage.success('更新成功')
            dialogVisible.value = false
            // 刷新账号列表
            fetchAccounts()
          } else {
            ElMessage.error(res.msg || '更新账号失败')
          }
        } catch (error) {
          console.error('更新账号失败:', error)
          ElMessage.error('更新账号失败')
        }
      }
    } else {
      return false
    }
  })
}

// 组件卸载前关闭SSE连接
onBeforeUnmount(() => {
  closeSSEConnection()
})
</script>

<style lang="scss" scoped>
@use '@/styles/variables.scss' as *;

@keyframes rotate {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.account-management {
  .header-actions {
    display: flex;
    gap: 10px;

    .el-icon {
      margin-right: 4px;

      &.is-loading {
        animation: rotate 1s linear infinite;
      }
    }
  }

  .account-card {
    :deep(.el-card__body) {
      padding: 20px 22px;
    }
  }

  .toolbar-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 14px;
    margin-bottom: 20px;
    flex-wrap: wrap;

    .platform-filter-pills {
      display: flex;
      align-items: center;
      gap: 6px;
      flex-wrap: wrap;
      background: #f1f5f9;
      padding: 4px;
      border-radius: 10px;

      .filter-pill {
        border: none;
        background: transparent;
        padding: 7px 13px;
        border-radius: 8px;
        font-size: 13px;
        font-weight: 500;
        color: $text-secondary;
        cursor: pointer;
        display: inline-flex;
        align-items: center;
        gap: 6px;
        transition: all 0.18s ease;

        .pill-count {
          font-size: 11px;
          padding: 1px 6px;
          border-radius: 999px;
          background: rgba(15, 23, 42, 0.06);
          color: $text-secondary;
          font-variant-numeric: tabular-nums;
        }

        &:hover {
          color: $text-primary;
        }

        &.active {
          background: #ffffff;
          color: $primary-color;
          box-shadow: 0 1px 3px rgba(15, 23, 42, 0.08);

          .pill-count {
            background: $primary-light;
            color: $primary-color;
          }
        }
      }
    }

    .search-box {
      width: 260px;
      max-width: 100%;
    }
  }

  .account-cell {
    display: flex;
    align-items: center;
    gap: 12px;

    .avatar-badge {
      width: 38px;
      height: 38px;
      border-radius: 11px;
      display: flex;
      align-items: center;
      justify-content: center;
      color: #fff;
      font-weight: 700;
      font-size: 15px;
      flex-shrink: 0;
      box-shadow: 0 3px 8px rgba(15, 23, 42, 0.1);
    }

    .account-meta {
      min-width: 0;

      .account-name {
        font-weight: 600;
        color: $text-primary;
        font-size: 14px;
      }

      .account-id {
        font-size: 12px;
        color: $text-secondary;
      }
    }
  }

  .platform-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 4px 10px;
    border-radius: 999px;
    font-size: 12px;
    font-weight: 600;

    .dot {
      width: 6px;
      height: 6px;
      border-radius: 50%;
    }

    &.kuaishou {
      background: #fff7ed;
      color: #c2410c;
      .dot { background: #f97316; }
    }

    &.douyin {
      background: #fff1f2;
      color: #be123c;
      .dot { background: #f43f5e; }
    }

    &.channels {
      background: #fffbeb;
      color: #b45309;
      .dot { background: #f59e0b; }
    }

    &.xiaohongshu {
      background: #fdf2f8;
      color: #db2777;
      .dot { background: #ec4899; }
    }
  }

  .row-actions {
    display: flex;
    justify-content: flex-end;
    flex-wrap: wrap;
    gap: 6px;
  }

  .empty-data {
    padding: 48px 0;

    .el-icon {
      margin-right: 4px;
    }
  }
  
  // 二维码容器样式
  .clickable-status {
    cursor: pointer;
    transition: all 0.2s;

    &:hover {
      transform: translateY(-1px);
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.12);
    }

    .relogin-hint {
      margin-left: 2px;
      font-weight: 600;
    }
  }

  .qrcode-container {
    margin-top: 16px;
    padding: 24px 18px;
    border-radius: 14px;
    background: #f8fafc;
    border: 1px solid $border-light;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: 240px;
    
    .qrcode-wrapper {
      text-align: center;

      .qrcode-frame {
        display: inline-block;
        padding: 12px;
        background: #ffffff;
        border-radius: 14px;
        border: 1px solid $border-light;
        box-shadow: $box-shadow-base;
        margin-bottom: 14px;
      }
      
      .qrcode-tip {
        margin: 0;
        font-size: 13px;
        color: $text-regular;
      }
      
      .qrcode-image {
        width: 188px;
        height: 188px;
        object-fit: contain;
        display: block;
      }
    }
    
    .loading-wrapper, .success-wrapper, .error-wrapper {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      gap: 8px;
      text-align: center;
      
      .el-icon {
        font-size: 44px;
        margin-bottom: 4px;
        
        &.is-loading {
          animation: rotate 1s linear infinite;
          color: $primary-color;
        }
      }
      
      .state-title {
        font-size: 15px;
        font-weight: 600;
        color: $text-primary;
      }

      .state-sub {
        font-size: 12px;
        color: $text-secondary;
      }
    }
    
    .success-wrapper .el-icon {
      color: $success-color;
    }
    
    .error-wrapper .el-icon {
      color: $danger-color;
    }
  }
}
</style>
