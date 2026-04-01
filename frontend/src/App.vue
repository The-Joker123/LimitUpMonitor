<template>
  <div class="dashboard">
    <div class="header">
      <div class="header-content">
        <h1 class="title">
          <svg class="title-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/>
          </svg>
          涨停连板监控
        </h1>
        <p class="subtitle">实时数据 · 东方财富/akshare</p>
      </div>
      <div class="header-actions">
        <el-date-picker
          v-model="selectedDate"
          type="date"
          placeholder="选择日期"
          format="YYYY-MM-DD"
          value-format="YYYYMMDD"
          size="small"
          :clearable="false"
          @change="fetchData"
        />
        <span class="update-time" v-if="currentTime">更新于 {{ currentTime }}</span>
        <el-button type="primary" @click="fetchData" :loading="loading" plain>
          <el-icon><Refresh /></el-icon>
        </el-button>
      </div>
    </div>

    <nav class="main-nav">
      <button
        :class="['nav-tab', { active: currentView === 'limit-up' }]"
        @click="currentView = 'limit-up'"
      >
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/>
        </svg>
        涨停监控
      </button>
      <button
        :class="['nav-tab', { active: currentView === 'twitter' }]"
        @click="currentView = 'twitter'"
      >
        <svg viewBox="0 0 24 24" fill="currentColor">
          <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/>
        </svg>
        X热点
      </button>
    </nav>

    <TwitterTrending v-if="currentView === 'twitter'" />

    <div v-if="currentView === 'limit-up'">
      <div class="summary-cards">
      <div class="summary-card red">
        <div class="card-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"/>
            <path d="M12 6v6l4 2"/>
          </svg>
        </div>
        <div class="card-value" :class="{ loading: loading }">{{ stocks.length }}</div>
        <div class="card-label">涨停总数</div>
      </div>
      <div class="summary-card orange">
        <div class="card-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M23 6l-9.5 9.5-5-5L1 18"/>
            <path d="M17 6h6v6"/>
          </svg>
        </div>
        <div class="card-value" :class="{ loading: loading }">{{ continuousStocks }}</div>
        <div class="card-label">连板股</div>
      </div>
      <div class="summary-card gold">
        <div class="card-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
          </svg>
        </div>
        <div class="card-value" :class="{ loading: loading }">{{ maxContinuous }}<span class="card-unit">板</span></div>
        <div class="card-label">最高连板</div>
      </div>
    </div>

    <div class="board-stats">
      <div class="board-header">
        <span class="board-title">板块统计</span>
        <div class="board-controls">
          <el-switch
            v-model="morningOnly"
            active-text="早盘"
            inactive-text="全部"
            @change="onMorningOnlyChange"
          />
        </div>
        <div class="board-tabs">
          <button
            v-for="tab in boardTabs"
            :key="tab.key"
            :class="['tab-btn', { active: activeTab === tab.key }]"
            @click="activeTab = tab.key"
          >
            {{ tab.label }}
          </button>
        </div>
      </div>
      <div class="board-content">
        <div v-if="currentBoardStats.length === 0" class="empty-state">
          暂无数据
        </div>
        <div v-else class="board-list">
          <div
            v-for="item in currentBoardStats"
            :key="item.industry"
            class="board-item"
            :class="{ active: selectedIndustry === item.industry }"
            @click="toggleIndustry(item.industry)"
          >
            <span class="board-name">{{ item.industry }}</span>
            <span class="board-count">{{ item.count }}</span>
          </div>
        </div>
      </div>
    </div>

    <div class="stock-table">
      <div class="table-header">
        <div class="table-title">
          <span>涨停股明细</span>
          <span v-if="selectedIndustry" class="filter-tag" @click="selectedIndustry = ''">
            {{ selectedIndustry }}
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M18 6L6 18M6 6l12 12"/>
            </svg>
          </span>
        </div>
        <div class="table-actions">
          <input
            v-model="searchQuery"
            type="text"
            class="search-input"
            placeholder="搜索股票代码/名称..."
          />
          <button
            :class="['filter-btn', { active: showCandidatesOnly }]"
            @click="showCandidatesOnly = !showCandidatesOnly"
            :title="showCandidatesOnly ? '显示全部' : '只看首板候选股'"
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
            </svg>
            {{ showCandidatesOnly ? '候选股' : '首板候选' }}
          </button>
          <span class="stock-count">共 {{ filteredStocks.length }} 只</span>
        </div>
      </div>
      <div class="table-wrapper">
        <table v-if="filteredStocks.length > 0">
          <thead>
            <tr>
              <th @click="sortBy('code')" class="sortable">
                代码
                <span class="sort-icon" v-if="sortField === 'code'">{{ sortOrder === 'asc' ? '↑' : '↓' }}</span>
              </th>
              <th @click="sortBy('name')" class="sortable">
                名称
                <span class="sort-icon" v-if="sortField === 'name'">{{ sortOrder === 'asc' ? '↑' : '↓' }}</span>
              </th>
              <th @click="sortBy('pct_chg')" class="sortable text-right">
                涨幅
                <span class="sort-icon" v-if="sortField === 'pct_chg'">{{ sortOrder === 'asc' ? '↑' : '↓' }}</span>
              </th>
              <th @click="sortBy('limit_up_days')" class="sortable text-center">
                连板
                <span class="sort-icon" v-if="sortField === 'limit_up_days'">{{ sortOrder === 'asc' ? '↑' : '↓' }}</span>
              </th>
              <th @click="sortBy('turnover_rate')" class="sortable text-right">
                换手率
                <span class="sort-icon" v-if="sortField === 'turnover_rate'">{{ sortOrder === 'asc' ? '↑' : '↓' }}</span>
              </th>
              <th @click="sortBy('first_seal_time')" class="sortable text-center">
                封板时间
                <span class="sort-icon" v-if="sortField === 'first_seal_time'">{{ sortOrder === 'asc' ? '↑' : '↓' }}</span>
              </th>
              <th @click="sortBy('flow_market_cap')" class="sortable text-right">
                流通市值
                <span class="sort-icon" v-if="sortField === 'flow_market_cap'">{{ sortOrder === 'asc' ? '↑' : '↓' }}</span>
              </th>
              <th @click="sortBy('seal_ratio')" class="sortable text-center">
                封单/成交
                <span class="sort-icon" v-if="sortField === 'seal_ratio'">{{ sortOrder === 'asc' ? '↑' : '↓' }}</span>
              </th>
              <th @click="sortBy('bomb_count')" class="sortable text-center">
                炸板
                <span class="sort-icon" v-if="sortField === 'bomb_count'">{{ sortOrder === 'asc' ? '↑' : '↓' }}</span>
              </th>
              <th>板块</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="stock in filteredStocks" :key="stock.code">
              <td class="code">{{ stock.code }}</td>
              <td class="name clickable" @click="showStockProfile(stock)">
                <span class="candidate-flags">
                  <span :class="stock.first_seal_time <= '1000' ? 'flag-pass' : 'flag-fail'" :title="'早盘封板(10:00前)'">{{ stock.first_seal_time <= '1000' ? '时' : '✕' }}</span>
                  <span :class="stock.turnover_rate >= 5 && stock.turnover_rate <= 15 ? 'flag-pass' : 'flag-fail'" :title="'换手率5-15%'">{{ stock.turnover_rate >= 5 && stock.turnover_rate <= 15 ? '换' : '✕' }}</span>
                  <span :class="stock.flow_market_cap >= 30 && stock.flow_market_cap <= 150 ? 'flag-pass' : 'flag-fail'" :title="'市值30-150亿'">{{ stock.flow_market_cap >= 30 && stock.flow_market_cap <= 150 ? '值' : '✕' }}</span>
                  <span :class="(industryCountMap[stock.industry] || 0) >= 2 ? 'flag-pass' : 'flag-fail'" :title="'板块涨停≥2'">{{ (industryCountMap[stock.industry] || 0) >= 2 ? '板' : '✕' }}</span>
                  <span :class="stock.bomb_count > 0 ? 'flag-bomb-back' : 'flag-pass'" :title="stock.bomb_count > 0 ? '炸板封回，强势' : '未炸板'">{{ stock.bomb_count > 0 ? '回' : '封' }}</span>
                </span>
                {{ stock.name }}
              </td>
              <td class="text-right" :class="getPctClass(stock.pct_chg)">
                +{{ stock.pct_chg.toFixed(2) }}%
              </td>
              <td class="text-center">
                <span v-if="stock.limit_up_days >= 3" class="board-fire">{{ stock.limit_up_days }}</span>
                <span v-else-if="stock.limit_up_days >= 2" class="board-hot">{{ stock.limit_up_days }}</span>
                <span v-else class="board-normal">{{ stock.limit_up_days }}</span>
              </td>
              <td class="text-right turnover-rate">{{ stock.turnover_rate }}%</td>
              <td class="text-center seal-time" :class="getSealTimeClass(stock.first_seal_time)">{{ formatSealTime(stock.first_seal_time) }}</td>
              <td class="text-right market-cap">{{ formatMarketCap(stock.flow_market_cap) }}</td>
              <td class="text-center" :class="getSealRatioClass(stock)" :title="'封板资金: ' + (stock.seal_fund / 1e8).toFixed(2) + '亿\n成交额: ' + (stock.amount / 1e8).toFixed(2) + '亿'">{{ getSealRatio(stock) }}</td>
              <td class="text-center" :class="stock.bomb_count > 0 ? 'bomb-warning' : ''" :title="stock.bomb_count > 0 ? '炸板' + stock.bomb_count + '次' : '未炸板'">{{ stock.bomb_count > 0 ? stock.bomb_count + '次' : '-' }}</td>
              <td class="industry">{{ stock.industry }}</td>
            </tr>
          </tbody>
        </table>
        <div v-else-if="loading" class="loading-state">
          <div class="loading-spinner"></div>
          <span>加载中...</span>
        </div>
        <div v-else class="empty-state">
          {{ searchQuery ? '未找到匹配结果' : '暂无数据' }}
        </div>
      </div>
    </div>

    <LimitUpChart :data="emotionData" :shIndex="shIndexData" />

    <AiChat :stocks="stocks" :boardStats="currentBoardStats" />

    <!-- 公司简介弹窗 -->
    <div v-if="showProfile" class="profile-overlay" @click.self="showProfile = false">
      <div class="profile-modal">
        <div class="profile-header">
          <div class="profile-title">
            <span class="profile-name">{{ stockProfile.name || stockProfile.code }}</span>
            <span v-if="stockProfile.shortName" class="profile-shortname">（{{ stockProfile.shortName }}）</span>
          </div>
          <button class="profile-close" @click="showProfile = false">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M18 6L6 18M6 6l12 12"/>
            </svg>
          </button>
        </div>
        <div class="profile-content">
          <div v-if="profileLoading" class="profile-loading">
            <div class="loading-spinner"></div>
            <span>加载中...</span>
          </div>
          <template v-else-if="stockProfile.error">
            <div class="profile-error">暂无简介信息</div>
          </template>
          <template v-else>
            <div class="profile-section">
              <div class="profile-row">
                <span class="profile-label">所属行业</span>
                <span class="profile-value">{{ stockProfile.industry || '-' }}</span>
              </div>
              <div class="profile-row">
                <span class="profile-label">上市日期</span>
                <span class="profile-value">{{ stockProfile.listingDate || '-' }}</span>
              </div>
              <div class="profile-row">
                <span class="profile-label">注册地址</span>
                <span class="profile-value">{{ stockProfile.registeredAddr || '-' }}</span>
              </div>
              <div class="profile-row">
                <span class="profile-label">办公地址</span>
                <span class="profile-value">{{ stockProfile.officeAddr || '-' }}</span>
              </div>
              <div class="profile-row">
                <span class="profile-label">联系电话</span>
                <span class="profile-value">{{ stockProfile.phone || '-' }}</span>
              </div>
              <div class="profile-row">
                <span class="profile-label">公司官网</span>
                <span class="profile-value">
                  <a v-if="stockProfile.website && stockProfile.website !== 'nan'" :href="stockProfile.website" target="_blank" class="profile-link">{{ stockProfile.website }}</a>
                  <span v-else>-</span>
                </span>
              </div>
            </div>
            <div v-if="stockProfile.mainBusiness" class="profile-section">
              <div class="profile-section-title">主营业务</div>
              <div class="profile-text">{{ stockProfile.mainBusiness }}</div>
            </div>
            <div v-if="stockProfile.businessScope" class="profile-section">
              <div class="profile-section-title">经营范围</div>
              <div class="profile-text">{{ stockProfile.businessScope }}</div>
            </div>
            <div v-if="stockProfile.description" class="profile-section">
              <div class="profile-section-title">公司介绍</div>
              <div class="profile-text">{{ stockProfile.description }}</div>
            </div>
          </template>
        </div>
      </div>
    </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { Refresh } from '@element-plus/icons-vue'
import AiChat from './components/AiChat.vue'
import LimitUpChart from './components/LimitUpChart.vue'
import TwitterTrending from './components/TwitterTrending.vue'

const currentView = ref('limit-up')
const stocks = ref([])
const loading = ref(false)
const currentTime = ref('')
const activeTab = ref('all')
const selectedDate = ref(new Date().toISOString().slice(0, 10).replace(/-/g, ''))
const emotionData = ref([])
const shIndexData = ref([])
const searchQuery = ref('')
const selectedIndustry = ref('')
const sortField = ref('pct_chg')
const sortOrder = ref('desc')
const showCandidatesOnly = ref(false)
const morningOnly = ref(false)
let refreshTimer = null

// 板块筛选变化时刷新情绪曲线
watch(selectedIndustry, () => {
  fetchEmotionHistory()
})

// 公司简介相关
const showProfile = ref(false)
const stockProfile = ref({})
const profileLoading = ref(false)

const continuousStocks = computed(() => stocks.value.filter(s => s.limit_up_days >= 2).length)
const maxContinuous = computed(() => Math.max(...stocks.value.map(s => s.limit_up_days), 0))

const boardData = computed(() => {
  const data = { all: {} }
  const maxDays = Math.max(...stocks.value.map(s => s.limit_up_days), 0)
  for (let i = 1; i <= maxDays; i++) {
    data[i] = {}
  }
  stocks.value.forEach(s => {
    const industry = s.industry
    data.all[industry] = (data.all[industry] || 0) + 1
    const days = s.limit_up_days
    if (data[days]) {
      data[days][industry] = (data[days][industry] || 0) + 1
    }
  })

  for (const key in data) {
    const entries = Object.entries(data[key])
      .map(([industry, count]) => ({ industry, count }))
      .sort((a, b) => b.count - a.count)
    data[key] = entries
  }
  return data
})

const boardTabs = computed(() => {
  const tabs = [{ key: 'all', label: '全部' }]
  const keys = Object.keys(boardData.value).filter(k => k !== 'all').map(Number).sort((a, b) => a - b)
  for (const key of keys) {
    if (boardData.value[key] && boardData.value[key].length > 0) {
      tabs.push({ key: String(key), label: `${key}板` })
    }
  }
  return tabs
})

const currentBoardStats = computed(() => boardData.value[activeTab.value] || [])

const filteredStocks = computed(() => {
  let result = showCandidatesOnly.value ? candidateStocks.value : stocksWithRatio.value
  if (selectedIndustry.value) {
    result = result.filter(s => s.industry === selectedIndustry.value)
  }
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    result = result.filter(s =>
      s.code.toLowerCase().includes(query) ||
      s.name.toLowerCase().includes(query) ||
      s.industry.toLowerCase().includes(query)
    )
  }
  result = [...result].sort((a, b) => {
    const aVal = a[sortField.value]
    const bVal = b[sortField.value]
    if (typeof aVal === 'string') {
      return sortOrder.value === 'asc'
        ? aVal.localeCompare(bVal)
        : bVal.localeCompare(aVal)
    }
    return sortOrder.value === 'asc' ? aVal - bVal : bVal - aVal
  })
  return result
})

const sortBy = (field) => {
  if (sortField.value === field) {
    sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortField.value = field
    sortOrder.value = 'desc'
  }
}

// 首板候选股筛选：早封板 + 高换手 + 板块强势 + 流通市值适中
const candidateStocks = computed(() => {
  return stocksWithRatio.value.filter(stock => {
    // 只看首板
    if (stock.limit_up_days !== 1) return false

    // 早盘封板（10:00前）
    if (!stock.first_seal_time || stock.first_seal_time > '1000') return false

    // 换手率 5-15%
    if (stock.turnover_rate < 5 || stock.turnover_rate > 15) return false

    // 流通市值 30-150亿
    if (stock.flow_market_cap < 30 || stock.flow_market_cap > 150) return false

    // 板块内涨停 >= 2
    const industryCount = industryCountMap[stock.industry] || 0
    if (industryCount < 2) return false

    return true
  })
})

const isCandidate = (stock) => {
  return candidateStocks.value.some(c => c.code === stock.code)
}

const getCandidateReason = (stock) => {
  const reasons = []
  if (stock.first_seal_time && stock.first_seal_time <= '1000') reasons.push('早盘封板')
  if (stock.turnover_rate >= 5 && stock.turnover_rate <= 15) reasons.push('换手率适中')
  if (stock.flow_market_cap >= 30 && stock.flow_market_cap <= 150) reasons.push('市值适中')
  const industryCount = industryCountMap[stock.industry] || 0
  if (industryCount >= 2) reasons.push(`板块涨停${industryCount}只`)
  if (stock.bomb_count > 0) reasons.push('炸板封回')
  return '候选原因：' + reasons.join(' + ')
}

const getSealTimeClass = (time) => {
  if (!time) return ''
  if (time <= '0930') return 'seal-early'  // 早板
  if (time <= '1000') return 'seal-good'   // 午前板
  if (time <= '1030') return 'seal-ok'     // 勉强
  return 'seal-late'                        // 午后板
}

const getSealRatio = (stock) => {
  if (!stock.amount || !stock.seal_fund) return '-'
  const ratio = stock.seal_fund / stock.amount
  const sealText = stock.seal_fund >= 1e8
    ? (stock.seal_fund / 1e8).toFixed(1) + '亿'
    : (stock.seal_fund / 1e4).toFixed(0) + '万'
  const amountText = stock.amount >= 1e8
    ? (stock.amount / 1e8).toFixed(1) + '亿'
    : (stock.amount / 1e4).toFixed(0) + '万'
  return `${sealText}/${amountText}=${(ratio * 100).toFixed(0)}%`
}

const getSealRatioClass = (stock) => {
  if (!stock.amount || !stock.seal_fund) return ''
  const ratio = stock.seal_fund / stock.amount
  if (ratio >= 0.3) return 'ratio-strong'
  if (ratio >= 0.15) return 'ratio-medium'
  return 'ratio-weak'
}

const formatMarketCap = (cap) => {
  if (!cap) return '-'
  return cap.toFixed(0) + '亿'
}

const formatSealTime = (time) => {
  if (!time || time.length !== 6) return time || '-'
  return time.slice(0, 2) + ':' + time.slice(2, 4) + ':' + time.slice(4, 6)
}

// 计算封单/成交比率（用于排序）
const stocksWithRatio = computed(() => {
  return stocks.value.map(s => ({
    ...s,
    seal_ratio: s.amount && s.seal_fund ? s.seal_fund / s.amount : 0
  }))
})

// 板块涨停数量映射
const industryCountMap = computed(() => {
  const map = {}
  boardData.value.all?.forEach(item => {
    map[item.industry] = item.count
  })
  return map
})

const getPctClass = (pct) => {
  if (pct >= 10) return 'pct-gold'
  if (pct >= 9.8) return 'pct-red'
  if (pct >= 5) return 'pct-orange'
  return 'pct-yellow'
}

const toggleIndustry = (industry) => {
  if (selectedIndustry.value === industry) {
    selectedIndustry.value = ''
  } else {
    selectedIndustry.value = industry
  }
}

const showStockProfile = async (stock) => {
  showProfile.value = true
  stockProfile.value = {}
  profileLoading.value = true
  try {
    const response = await fetch(`/api/stock/profile?code=${stock.code}`)
    stockProfile.value = await response.json()
  } catch (error) {
    stockProfile.value = { error: '获取失败' }
  } finally {
    profileLoading.value = false
  }
}

const fetchData = async () => {
  try {
    loading.value = true
    const url = `/api/limit-up?date=${selectedDate.value}&time_range=${morningOnly.value ? 'morning' : 'all'}`
    const response = await fetch(url)
    const data = await response.json()
    stocks.value = data.stocks
    currentTime.value = new Date().toLocaleTimeString('zh-CN')
  } catch (error) {
    // silently fail, UI will show empty state
  } finally {
    loading.value = false
  }
}

const onMorningOnlyChange = () => {
  fetchData()
  fetchEmotionHistory()
}

const fetchEmotionHistory = async () => {
  try {
    const industryParam = selectedIndustry.value ? `&industry=${encodeURIComponent(selectedIndustry.value)}` : ''
    const response = await fetch(`/api/emotion-history?days=20&time_range=${morningOnly.value ? 'morning' : 'all'}${industryParam}`)
    const result = await response.json()
    emotionData.value = result.data || []
  } catch (error) {
    // silently fail, chart will show empty state
  }
}

const fetchShIndex = async () => {
  try {
    const response = await fetch('/api/sh-index?days=20')
    const result = await response.json()
    shIndexData.value = result.data || []
  } catch (error) {
    // silently fail, chart will show empty state
  }
}

onMounted(() => {
  fetchData()
  fetchEmotionHistory()
  fetchShIndex()
  refreshTimer = setInterval(fetchData, 10000)
})

onUnmounted(() => {
  if (refreshTimer) clearInterval(refreshTimer)
})
</script>

<style scoped>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

.dashboard {
  min-height: 100vh;
  background: linear-gradient(135deg, #0a0a1a 0%, #0f1029 50%, #0a0a1a 100%);
  padding: 20px;
  font-family: 'PingFang SC', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24px 28px;
  background: rgba(255,255,255,0.02);
  border-radius: 16px;
  border: 1px solid rgba(255,255,255,0.05);
  margin-bottom: 20px;
  backdrop-filter: blur(10px);
}

.title {
  font-size: 24px;
  font-weight: 700;
  color: #fff;
  display: flex;
  align-items: center;
  gap: 12px;
}

.title-icon {
  width: 26px;
  height: 26px;
  color: #ffd700;
  filter: drop-shadow(0 0 6px rgba(255, 215, 0, 0.4));
}

.subtitle {
  font-size: 13px;
  color: rgba(255,255,255,0.4);
  margin-top: 4px;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 16px;
}

.update-time {
  font-size: 12px;
  color: rgba(255,255,255,0.4);
  padding: 6px 12px;
  background: rgba(255,255,255,0.03);
  border-radius: 20px;
}

:deep(.el-date-picker) {
  background: rgba(255,255,255,0.05);
  border-color: rgba(255,255,255,0.1);
}

:deep(.el-input__wrapper) {
  background: rgba(255,255,255,0.05);
  border-color: rgba(255,255,255,0.1);
  box-shadow: none;
}

:deep(.el-input__inner) {
  color: #fff;
}

:deep(.el-input__prefix) {
  color: rgba(255,255,255,0.5);
}

.summary-cards {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-bottom: 20px;
}

.summary-card {
  padding: 24px 20px;
  border-radius: 16px;
  text-align: center;
  border: 1px solid rgba(255,255,255,0.05);
  position: relative;
  overflow: hidden;
  transition: all 0.3s;
}

.summary-card:hover {
  transform: translateY(-2px);
  border-color: rgba(255,255,255,0.1);
}

.summary-card.red {
  background: linear-gradient(135deg, rgba(255,71,87,0.12), rgba(255,71,87,0.02));
  box-shadow: 0 4px 20px rgba(255,71,87,0.1);
}

.summary-card.red:hover {
  box-shadow: 0 8px 30px rgba(255,71,87,0.2);
}

.summary-card.orange {
  background: linear-gradient(135deg, rgba(255,127,80,0.12), rgba(255,127,80,0.02));
  box-shadow: 0 4px 20px rgba(255,127,80,0.1);
}

.summary-card.orange:hover {
  box-shadow: 0 8px 30px rgba(255,127,80,0.2);
}

.summary-card.gold {
  background: linear-gradient(135deg, rgba(255,215,0,0.12), rgba(255,215,0,0.02));
  box-shadow: 0 4px 20px rgba(255,215,0,0.1);
}

.summary-card.gold:hover {
  box-shadow: 0 8px 30px rgba(255,215,0,0.2);
}

.card-icon {
  position: absolute;
  top: 16px;
  right: 16px;
  width: 24px;
  height: 24px;
  opacity: 0.25;
}

.summary-card.red .card-icon { color: #ff4757; }
.summary-card.orange .card-icon { color: #ff7f50; }
.summary-card.gold .card-icon { color: #ffd700; }

.card-value {
  font-size: 42px;
  font-weight: 800;
  transition: opacity 0.3s;
}

.summary-card.red .card-value { color: #ff4757; }
.summary-card.orange .card-value { color: #ff7f50; }
.summary-card.gold .card-value { color: #ffd700; }

.card-value.loading {
  opacity: 0.5;
}

.card-unit {
  font-size: 18px;
  font-weight: 400;
  margin-left: 4px;
}

.card-label {
  font-size: 13px;
  color: rgba(255,255,255,0.5);
  margin-top: 8px;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.board-stats {
  background: rgba(255,255,255,0.02);
  border-radius: 16px;
  border: 1px solid rgba(255,255,255,0.05);
  padding: 20px;
  margin-bottom: 20px;
}

.board-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.board-title {
  font-size: 16px;
  font-weight: 600;
  color: #fff;
}

.board-controls {
  display: flex;
  align-items: center;
  gap: 12px;
}

.board-tabs {
  display: flex;
  gap: 8px;
}

.tab-btn {
  padding: 8px 16px;
  border-radius: 20px;
  border: 1px solid rgba(255,255,255,0.08);
  background: rgba(255,255,255,0.03);
  color: rgba(255,255,255,0.5);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.3s;
}

.tab-btn:hover {
  background: rgba(255,255,255,0.06);
  color: rgba(255,255,255,0.8);
  border-color: rgba(255,255,255,0.12);
}

.tab-btn.active {
  background: linear-gradient(135deg, #ff4757, #ff7f50);
  color: #fff;
  border-color: transparent;
  box-shadow: 0 4px 16px rgba(255,71,87,0.3);
}

.board-list {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.board-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 16px;
  background: rgba(255,255,255,0.03);
  border-radius: 10px;
  border: 1px solid rgba(255,255,255,0.05);
  transition: all 0.2s;
  cursor: pointer;
}

.board-item:hover {
  background: rgba(255,255,255,0.06);
  border-color: rgba(255,255,255,0.08);
  transform: translateY(-1px);
}

.board-item.active {
  background: rgba(255,127,80,0.15);
  border-color: rgba(255,127,80,0.4);
}

.board-item.active .board-name {
  color: #ff7f50;
}

.board-name {
  font-size: 13px;
  color: rgba(255,255,255,0.7);
}

.board-count {
  font-size: 15px;
  font-weight: 700;
  color: #ff7f50;
  background: rgba(255,127,80,0.12);
  padding: 2px 10px;
  border-radius: 10px;
}

.stock-table {
  background: rgba(255,255,255,0.02);
  border-radius: 16px;
  border: 1px solid rgba(255,255,255,0.05);
  overflow: hidden;
  margin-bottom: 20px;
}

.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid rgba(255,255,255,0.05);
  font-size: 14px;
  font-weight: 600;
  color: #fff;
}

.table-title {
  display: flex;
  align-items: center;
  gap: 12px;
}

.filter-tag {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 12px;
  background: rgba(255,127,80,0.15);
  border: 1px solid rgba(255,127,80,0.3);
  border-radius: 16px;
  font-size: 12px;
  color: #ff7f50;
  cursor: pointer;
  transition: all 0.2s;
}

.filter-tag:hover {
  background: rgba(255,127,80,0.25);
}

.filter-tag svg {
  width: 12px;
  height: 12px;
}

.table-actions {
  display: flex;
  align-items: center;
  gap: 16px;
}

.search-input {
  padding: 8px 16px;
  border-radius: 8px;
  border: 1px solid rgba(255,255,255,0.1);
  background: rgba(255,255,255,0.05);
  color: #fff;
  font-size: 13px;
  outline: none;
  transition: border-color 0.3s;
  width: 180px;
}

.search-input::placeholder {
  color: rgba(255,255,255,0.3);
}

.search-input:focus {
  border-color: rgba(255,127,80,0.5);
}

.filter-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border-radius: 8px;
  border: 1px solid rgba(255,215,0,0.3);
  background: rgba(255,215,0,0.08);
  color: rgba(255,215,0,0.8);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.3s;
}

.filter-btn svg {
  width: 14px;
  height: 14px;
}

.filter-btn:hover {
  background: rgba(255,215,0,0.15);
  border-color: rgba(255,215,0,0.5);
}

.filter-btn.active {
  background: linear-gradient(135deg, #ff4757, #ff7f50);
  color: #fff;
  border-color: transparent;
}

.stock-count {
  font-size: 13px;
  color: rgba(255,255,255,0.4);
  font-weight: 400;
}

.table-wrapper {
  overflow-x: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
}

th {
  padding: 14px 16px;
  text-align: left;
  font-size: 11px;
  font-weight: 600;
  color: rgba(255,255,255,0.4);
  text-transform: uppercase;
  letter-spacing: 1px;
  background: rgba(255,255,255,0.01);
  border-bottom: 1px solid rgba(255,255,255,0.05);
  white-space: nowrap;
}

th.sortable {
  cursor: pointer;
  user-select: none;
  transition: color 0.2s;
}

th.sortable:hover {
  color: rgba(255,255,255,0.8);
}

.sort-icon {
  margin-left: 4px;
  color: #ff7f50;
}

.text-right {
  text-align: right;
}

.text-center {
  text-align: center;
}

td {
  padding: 14px 16px;
  font-size: 15px;
  border-bottom: 1px solid rgba(255,255,255,0.03);
}

tr:nth-child(even) td {
  background: rgba(255,255,255,0.01);
}

tr:hover td {
  background: rgba(255,255,255,0.03);
}

tr:hover td:first-child {
  border-radius: 8px 0 0 8px;
}

tr:hover td:last-child {
  border-radius: 0 8px 8px 0;
}

.code {
  color: rgba(255,255,255,0.5);
  font-family: 'SF Mono', 'Fira Code', monospace;
}

.name {
  font-weight: 600;
  color: #fff;
}

.pct-gold {
  color: #ffd700;
  font-weight: 700;
}

.pct-red {
  color: #ff4757;
  font-weight: 700;
}

.pct-orange {
  color: #ff7f50;
  font-weight: 600;
}

.pct-yellow {
  color: #ffc107;
  font-weight: 600;
}

.board-fire {
  display: inline-block;
  padding: 4px 10px;
  background: linear-gradient(135deg, #ff4757, #ff7f50);
  border-radius: 6px;
  font-weight: 700;
  font-size: 13px;
  color: #fff;
}

.board-hot {
  display: inline-block;
  padding: 4px 10px;
  background: rgba(255,127,80,0.3);
  border-radius: 6px;
  font-weight: 700;
  font-size: 13px;
  color: #ff7f50;
}

.board-normal {
  padding: 4px 10px;
  background: rgba(255,255,255,0.08);
  border-radius: 6px;
  font-size: 13px;
  color: rgba(255,255,255,0.6);
}

.industry {
  color: rgba(255,255,255,0.5);
  font-size: 13px;
}

.seal-time {
  font-family: 'SF Mono', 'Fira Code', monospace;
  font-size: 13px;
  font-weight: 600;
}

.seal-early {
  color: #00ff88;
  font-weight: 700;
  text-shadow: 0 0 8px rgba(0, 255, 136, 0.5);
}

.seal-good {
  color: #00ff88;
}

.seal-ok {
  color: #ffd700;
  font-weight: 600;
}

.seal-late {
  color: rgba(255,255,255,0.5);
}

.ratio-strong {
  color: #00ff88;
  font-weight: 700;
}

.ratio-medium {
  color: #ffd700;
  font-weight: 600;
}

.ratio-weak {
  color: rgba(255,255,255,0.5);
}

.bomb-warning {
  color: #ff4757;
  font-weight: 700;
}

.turnover-rate {
  color: #00ff88;
  font-weight: 600;
}

.market-cap {
  color: #00ff88;
  font-weight: 600;
}

.loading-state,
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 48px;
  color: rgba(255,255,255,0.4);
  gap: 12px;
}

.loading-spinner {
  width: 32px;
  height: 32px;
  border: 3px solid rgba(255,255,255,0.1);
  border-top-color: #ff7f50;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* 公司简介弹窗样式 */
.profile-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  backdrop-filter: blur(4px);
}

.profile-modal {
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
  border-radius: 16px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  width: 90%;
  max-width: 600px;
  max-height: 80vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
}

.profile-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  background: rgba(255, 255, 255, 0.02);
}

.profile-title {
  display: flex;
  align-items: center;
  gap: 8px;
}

.profile-name {
  font-size: 18px;
  font-weight: 700;
  color: #fff;
}

.profile-shortname {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.5);
}

.profile-close {
  background: rgba(255, 255, 255, 0.05);
  border: none;
  border-radius: 8px;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: rgba(255, 255, 255, 0.5);
  transition: all 0.2s;
}

.profile-close:hover {
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
}

.profile-close svg {
  width: 18px;
  height: 18px;
}

.profile-content {
  padding: 20px 24px;
  overflow-y: auto;
  flex: 1;
}

.profile-loading,
.profile-error {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px;
  color: rgba(255, 255, 255, 0.5);
  gap: 12px;
}

.profile-section {
  margin-bottom: 20px;
}

.profile-section:last-child {
  margin-bottom: 0;
}

.profile-section-title {
  font-size: 13px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.5);
  text-transform: uppercase;
  letter-spacing: 1px;
  margin-bottom: 10px;
}

.profile-row {
  display: flex;
  padding: 8px 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.profile-row:last-child {
  border-bottom: none;
}

.profile-label {
  width: 90px;
  flex-shrink: 0;
  font-size: 13px;
  color: rgba(255, 255, 255, 0.4);
}

.profile-value {
  flex: 1;
  font-size: 13px;
  color: rgba(255, 255, 255, 0.8);
  word-break: break-all;
}

.profile-link {
  color: #4ecdc4;
  text-decoration: none;
}

.profile-link:hover {
  text-decoration: underline;
}

.profile-text {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.7);
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-all;
}

.name.clickable {
  cursor: pointer;
  color: #4ecdc4;
  transition: color 0.2s;
}

.name.clickable:hover {
  color: #fff;
  text-decoration: underline;
}

.candidate-star {
  margin-right: 4px;
  cursor: help;
}

.candidate-flags {
  display: inline-flex;
  gap: 2px;
  margin-right: 6px;
}

.candidate-flags span {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 700;
}

.flag-pass {
  background: rgba(0, 255, 136, 0.2);
  color: #00ff88;
  border: 1px solid rgba(0, 255, 136, 0.4);
}

.flag-bomb-back {
  background: rgba(255, 215, 0, 0.2);
  color: #ffd700;
  border: 1px solid rgba(255, 215, 0, 0.4);
}

.flag-fail {
  background: rgba(255, 71, 87, 0.15);
  color: #ff4757;
  border: 1px solid rgba(255, 71, 87, 0.3);
}

:deep(.el-button) {
  font-weight: 500;
}

.main-nav {
  display: flex;
  gap: 8px;
  padding: 0 20px;
  margin-bottom: 20px;
  border-bottom: 1px solid #ebeef5;
}

.nav-tab {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 20px;
  background: none;
  border: none;
  border-bottom: 2px solid transparent;
  color: #606266;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
}

.nav-tab svg {
  width: 18px;
  height: 18px;
}

.nav-tab:hover {
  color: #409eff;
}

.nav-tab.active {
  color: #409eff;
  border-bottom-color: #409eff;
}

@media (max-width: 768px) {
  .header {
    flex-direction: column;
    gap: 16px;
  }

  .summary-cards {
    grid-template-columns: 1fr;
  }

  .table-header {
    flex-direction: column;
    gap: 12px;
  }

  .table-actions {
    width: 100%;
    flex-direction: column;
  }

  .search-input {
    width: 100%;
  }
}
</style>
