<template>
  <div class="dashboard">
    <div class="header">
      <div class="header-content">
        <h1 class="title">
          <span class="fire-icon">🔥</span>
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
        <span class="update-time">{{ currentTime }}</span>
        <el-button type="primary" @click="fetchData" :loading="loading" plain>
          <el-icon><Refresh /></el-icon>
        </el-button>
      </div>
    </div>

    <div class="summary-cards">
      <div class="summary-card red">
        <div class="card-value">{{ stocks.length }}</div>
        <div class="card-label">涨停总数</div>
      </div>
      <div class="summary-card orange">
        <div class="card-value">{{ continuousStocks }}</div>
        <div class="card-label">连板股</div>
      </div>
      <div class="summary-card gold">
        <div class="card-value">{{ maxContinuous }}板</div>
        <div class="card-label">最高连板</div>
      </div>
    </div>

    <div class="board-stats">
      <div class="board-header">
        <span class="board-title">📊 板块统计</span>
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
        <div class="board-list">
          <div 
            v-for="item in currentBoardStats" 
            :key="item.industry" 
            class="board-item"
          >
            <span class="board-name">{{ item.industry }}</span>
            <span class="board-count">{{ item.count }}</span>
          </div>
        </div>
      </div>
    </div>

    <div class="stock-table">
      <div class="table-header">
        <span>📋 涨停股明细</span>
        <span class="stock-count">共 {{ stocks.length }} 只</span>
      </div>
      <div class="table-wrapper">
        <table>
          <thead>
            <tr>
              <th>代码</th>
              <th>名称</th>
              <th class="text-right">涨幅</th>
              <th class="text-center">连板</th>
              <th>板块</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="stock in stocks" :key="stock.code">
              <td class="code">{{ stock.code }}</td>
              <td class="name">{{ stock.name }}</td>
              <td class="text-right" :class="stock.pct_chg >= 9.8 ? 'pct-red' : 'pct-orange'">
                +{{ stock.pct_chg.toFixed(2) }}%
              </td>
              <td class="text-center">
                <span v-if="stock.limit_up_days >= 3" class="board-fire">🔥{{ stock.limit_up_days }}</span>
                <span v-else-if="stock.limit_up_days >= 2" class="board-hot">🔥2</span>
                <span v-else class="board-normal">{{ stock.limit_up_days }}</span>
              </td>
              <td class="industry">{{ stock.industry }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <LimitUpChart :data="emotionData" />

    <AiChat :stocks="stocks" :boardStats="currentBoardStats" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { Refresh } from '@element-plus/icons-vue'
import AiChat from './components/AiChat.vue'
import LimitUpChart from './components/LimitUpChart.vue'

const stocks = ref([])
const loading = ref(false)
const currentTime = ref('')
const activeTab = ref('all')
const selectedDate = ref(new Date().toLocaleDateString('zh-CN').replace(/\//g, '-').replace(/-/g, ''))
const emotionData = ref([])
let refreshTimer = null

const continuousStocks = computed(() => stocks.value.filter(s => s.limit_up_days >= 2).length)
const maxContinuous = computed(() => Math.max(...stocks.value.map(s => s.limit_up_days), 0))

const boardData = computed(() => {
  const data = { all: [], 1: [], 2: [], 3: [], 4: [], 5: [], 6: [], 7: [] }
  stocks.value.forEach(s => {
    const industry = s.industry
    data.all.push({ industry, count: (data.all.find(x => x.industry === industry)?.count || 0) + 1 })
    const days = s.limit_up_days
    const boardKey = days >= 7 ? 7 : days
    if (data[boardKey]) {
      data[boardKey].push({ industry, count: (data[boardKey].find(x => x.industry === industry)?.count || 0) + 1 })
    }
  })

  for (const key in data) {
    const seen = new Set()
    data[key] = data[key].filter(x => {
      if (seen.has(x.industry)) return false
      seen.add(x.industry)
      return true
    }).sort((a, b) => b.count - a.count)
  }
  return data
})

const boardTabs = computed(() => {
  const tabs = [{ key: 'all', label: '全部' }]
  for (let i = 1; i <= 7; i++) {
    if (boardData.value[i].length > 0) {
      tabs.push({ key: String(i), label: `${i}板` })
    }
  }
  return tabs
})

const currentBoardStats = computed(() => boardData.value[activeTab.value] || [])

const fetchData = async () => {
  try {
    loading.value = true
    const url = `/api/limit-up?date=${selectedDate.value}`
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

const fetchEmotionHistory = async () => {
  try {
    const response = await fetch('/api/emotion-history?days=20')
    const result = await response.json()
    emotionData.value = result.data || []
  } catch (error) {
    // silently fail, chart will show empty state
  }
}

onMounted(() => {
  fetchData()
  fetchEmotionHistory()
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

body {
  font-family: 'PingFang SC', -apple-system, BlinkMacSystemFont, sans-serif;
  background: #0f0f23;
  color: #e0e0e0;
}

.dashboard {
  min-height: 100vh;
  background: linear-gradient(180deg, #0f0f23 0%, #1a1a2e 100%);
  padding: 20px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  background: rgba(255,255,255,0.03);
  border-radius: 16px;
  border: 1px solid rgba(255,255,255,0.06);
  margin-bottom: 20px;
}

.header-content {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.title {
  font-size: 24px;
  font-weight: 700;
  color: #fff;
  display: flex;
  align-items: center;
  gap: 8px;
}

.fire-icon {
  font-size: 28px;
}

.subtitle {
  font-size: 13px;
  color: rgba(255,255,255,0.4);
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 16px;
}

.update-time {
  font-size: 12px;
  color: rgba(255,255,255,0.5);
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
  padding: 20px;
  border-radius: 12px;
  text-align: center;
  border: 1px solid rgba(255,255,255,0.1);
}

.summary-card.red {
  background: linear-gradient(135deg, rgba(255,71,87,0.2), rgba(255,71,87,0.05));
}

.summary-card.orange {
  background: linear-gradient(135deg, rgba(255,127,80,0.2), rgba(255,127,80,0.05));
}

.summary-card.gold {
  background: linear-gradient(135deg, rgba(255,215,0,0.2), rgba(255,215,0,0.05));
}

.card-value {
  font-size: 36px;
  font-weight: 800;
}

.summary-card.red .card-value { color: #ff4757; }
.summary-card.orange .card-value { color: #ff7f50; }
.summary-card.gold .card-value { color: #ffd700; }

.card-label {
  font-size: 13px;
  color: rgba(255,255,255,0.5);
  margin-top: 4px;
}

.board-stats {
  background: rgba(255,255,255,0.03);
  border-radius: 16px;
  border: 1px solid rgba(255,255,255,0.06);
  padding: 16px;
  margin-bottom: 20px;
}

.board-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.board-title {
  font-size: 16px;
  font-weight: 600;
  color: #fff;
}

.board-tabs {
  display: flex;
  gap: 8px;
}

.tab-btn {
  padding: 6px 14px;
  border-radius: 20px;
  border: 1px solid rgba(255,255,255,0.1);
  background: transparent;
  color: rgba(255,255,255,0.5);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}

.tab-btn.active {
  background: linear-gradient(135deg, #ff4757, #ff7f50);
  color: #fff;
  border-color: transparent;
}

.board-list {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.board-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 16px;
  background: rgba(255,255,255,0.05);
  border-radius: 8px;
  border: 1px solid rgba(255,255,255,0.08);
}

.board-name {
  font-size: 14px;
  color: #ccc;
}

.board-count {
  font-size: 18px;
  font-weight: 700;
  color: #ff7f50;
  background: rgba(255,127,80,0.15);
  padding: 2px 10px;
  border-radius: 12px;
}

.stock-table {
  background: rgba(255,255,255,0.03);
  border-radius: 16px;
  border: 1px solid rgba(255,255,255,0.06);
  overflow: hidden;
}

.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid rgba(255,255,255,0.06);
  font-size: 15px;
  font-weight: 600;
  color: #fff;
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
  font-size: 12px;
  font-weight: 600;
  color: rgba(255,255,255,0.4);
  text-transform: uppercase;
  letter-spacing: 1px;
  background: rgba(255,255,255,0.02);
  border-bottom: 1px solid rgba(255,255,255,0.06);
}

td {
  padding: 14px 16px;
  font-size: 14px;
  border-bottom: 1px solid rgba(255,255,255,0.04);
}

tr:hover td {
  background: rgba(255,255,255,0.02);
}

.text-right {
  text-align: right;
}

.text-center {
  text-align: center;
}

.code {
  color: rgba(255,255,255,0.5);
  font-family: monospace;
}

.name {
  font-weight: 600;
  color: #fff;
}

.pct-red {
  color: #ff4757;
  font-weight: 700;
}

.pct-orange {
  color: #ff7f50;
  font-weight: 600;
}

.board-fire {
  display: inline-block;
  padding: 4px 10px;
  background: linear-gradient(135deg, #ff4757, #ff7f50);
  border-radius: 6px;
  font-weight: 700;
  font-size: 14px;
  color: #fff;
}

.board-hot {
  display: inline-block;
  padding: 4px 10px;
  background: rgba(255,127,80,0.3);
  border-radius: 6px;
  font-weight: 700;
  font-size: 14px;
  color: #ff7f50;
}

.board-normal {
  padding: 4px 10px;
  background: rgba(255,255,255,0.1);
  border-radius: 6px;
  font-size: 14px;
  color: rgba(255,255,255,0.6);
}

.industry {
  color: rgba(255,255,255,0.5);
  font-size: 13px;
}

:deep(.el-button) {
  font-weight: 500;
}
</style>