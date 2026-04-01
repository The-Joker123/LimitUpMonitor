<template>
  <div class="twitter-trending">
    <div class="page-header">
      <h2>X (Twitter) 热点话题</h2>
      <div class="header-controls">
        <el-select v-model="selectedLocation" placeholder="选择地区" size="default" @change="fetchTrends">
          <el-option label="全球" value="" />
          <el-option label="美国" value="united-states" />
          <el-option label="英国" value="united-kingdom" />
          <el-option label="日本" value="japan" />
        </el-select>
        <el-button @click="fetchTrends" :loading="loading">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>
    </div>

    <div v-if="error" class="error-message">
      <p>{{ error }}</p>
      <p class="hint">请确保已安装 Playwright 并配置代理</p>
    </div>

    <div v-else-if="loading" class="loading-state">
      <el-icon class="is-loading"><Loading /></el-icon>
      <span>加载中（可能需要几秒）...</span>
    </div>

    <div v-else class="trends-container">
      <div class="location-tag">
        <el-icon><Location /></el-icon>
        {{ location }}
      </div>
      <div class="trends-list">
        <div v-for="(trend, index) in trends" :key="index" class="trend-item">
          <div class="trend-rank">{{ index + 1 }}</div>
          <div class="trend-content">
            <a :href="'https://x.com/search?q=' + encodeURIComponent(trend.name)" target="_blank" class="trend-name">{{ trend.name }}</a>
            <div v-if="trend.tweet_volume" class="trend-volume">
              {{ formatVolume(trend.tweet_volume) }} 推文
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { Refresh, Loading, Location } from '@element-plus/icons-vue'

const trends = ref([])
const location = ref('')
const loading = ref(false)
const error = ref('')
const selectedLocation = ref('')

const fetchTrends = async () => {
  loading.value = true
  error.value = ''
  try {
    const response = await axios.get('/api/x-trending', {
      params: { location: selectedLocation.value }
    })
    if (response.data.error) {
      error.value = response.data.error
    } else {
      trends.value = response.data.trends || []
      location.value = response.data.location || '全球'
    }
  } catch (e) {
    error.value = '获取失败: ' + (e.message || '未知错误')
  } finally {
    loading.value = false
  }
}

const formatVolume = (volume) => {
  if (!volume) return '-'
  if (volume >= 1000000) return (volume / 1000000).toFixed(1) + 'M'
  if (volume >= 1000) return (volume / 1000).toFixed(1) + 'K'
  return volume
}

onMounted(() => {
  fetchTrends()
})
</script>

<style scoped>
.twitter-trending {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.page-header h2 {
  margin: 0;
  font-size: 24px;
  color: #303133;
}

.header-controls {
  display: flex;
  gap: 12px;
  align-items: center;
}

.error-message {
  background: #fef0f0;
  border: 1px solid #fde2e2;
  border-radius: 8px;
  padding: 24px;
  text-align: center;
  color: #f56c6c;
}

.error-message .hint {
  margin-top: 8px;
  font-size: 12px;
  color: #909399;
}

.loading-state {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 12px;
  padding: 60px;
  color: #909399;
}

.trends-container {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

.location-tag {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background: #409eff;
  color: #fff;
  border-radius: 16px;
  font-size: 14px;
  margin-bottom: 20px;
}

.trends-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.trend-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  background: #f5f7fa;
  border-radius: 8px;
  transition: background 0.2s;
}

.trend-item:hover {
  background: #ecf5ff;
}

.trend-rank {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #409eff;
  color: #fff;
  border-radius: 50%;
  font-weight: bold;
  font-size: 14px;
}

.trend-content {
  flex: 1;
}

.trend-name {
  font-size: 16px;
  font-weight: 500;
  color: #303133;
  text-decoration: none;
}

.trend-name:hover {
  color: #409eff;
}

.trend-volume {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}
</style>
