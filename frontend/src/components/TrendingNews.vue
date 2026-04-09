<template>
  <div class="trending-news">
    <div class="toolbar">
      <div class="toolbar-left">
        <el-select v-model="currentSource" size="small" style="width: 140px">
          <el-option
            v-for="source in sourceList"
            :key="source.key"
            :label="source.label"
            :value="source.key"
          />
        </el-select>
      </div>
      <div class="toolbar-right">
        <span class="update-time" v-if="currentTime">
          <el-icon class="time-icon"><Clock /></el-icon>
          {{ currentTime }}
        </span>
        <el-button @click="fetchCurrentSource" :disabled="loading" size="small" circle>
          <el-icon v-if="loading" class="is-loading"><Loading /></el-icon>
          <el-icon v-else><Refresh /></el-icon>
        </el-button>
      </div>
    </div>

    <div v-if="error" class="error-box">
      {{ error }}
    </div>

    <div v-else-if="loading && !items.length" class="loading-box">
      <el-icon class="is-loading"><Loading /></el-icon>
      <span>加载中...</span>
    </div>

    <div v-else class="feeds-grid">
      <div v-for="(item, index) in displayItems" :key="item.id" class="feed-item">
        <span class="item-rank">{{ index + 1 }}</span>
        <div class="item-content">
          <div class="item-title-row">
            <a :href="item.url" target="_blank" class="item-title">
              {{ item.translation || item.title }}
            </a>
            <span v-if="item.translation" class="original-title">{{ item.title }}</span>
          </div>
          <div class="item-meta">
            <button class="meta-btn translate" @click="translateTitle(item)" :disabled="translating[item.id]" title="译">
              <el-icon v-if="translating[item.id]" class="is-loading"><Loading /></el-icon>
              <el-icon v-else><Finished /></el-icon>
            </button>
            <button class="meta-btn ai" @click="explainWithAI(item)" :disabled="aiExplaining[item.id]" title="AI">
              <el-icon v-if="aiExplaining[item.id]" class="is-loading"><Loading /></el-icon>
              <el-icon v-else><MagicStick /></el-icon>
            </button>
            <span class="meta-time">{{ formatTime(item.created_at) }}</span>
            <span v-if="item.author" class="meta-author">{{ formatAuthor(item.author) }}</span>
            <span v-if="item.score" class="meta-score">
              <el-icon><Star /></el-icon>
              {{ formatScore(item.score) }}
            </span>
            <span v-if="item.comments" class="meta-comments">
              <el-icon><ChatDotRound /></el-icon>
              {{ item.comments }}
            </span>
          </div>
          <div v-if="aiContent[item.id]" class="ai-box">
            {{ aiContent[item.id] }}
          </div>
          <div v-if="getMetadataField(item, 'description') || getMetadataField(item, 'tagline')" class="item-desc">
            {{ getMetadataField(item, 'description') || getMetadataField(item, 'tagline') }}
          </div>
          <div v-if="getMetadataField(item, 'language')" class="item-lang">
            <span class="lang-dot"></span>
            {{ getMetadataField(item, 'language') }}
          </div>
        </div>
      </div>
    </div>

    <div v-if="hasMore" class="load-more">
      <el-button @click="loadMore" :disabled="loading" size="small">
        加载更多
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted, watch } from 'vue'
import axios from 'axios'
import { Refresh, Loading, Clock, Finished, MagicStick, Star, ChatDotRound } from '@element-plus/icons-vue'

const sourceList = [
  { key: 'github', label: 'GitHub', icon: '💻', prompt: '你是一位技术架构师。请用50字以内简要说明这个开源项目，并解释它为什么值得关注。' },
  { key: 'youtube', label: 'YouTube', icon: '📺', prompt: '你是一位内容创作者。请用50字以内简要说明这个视频内容，并解释它为什么值得关注。' },
  { key: 'google', label: 'Google趋势', icon: '🔍', prompt: '你是一位数据分析师。请用50字以内简要说明这个搜索趋势，并解释它为什么值得关注。' },
  { key: 'xueqiu', label: '雪球', icon: '❄️', prompt: '你是一位金融分析师。请用50字以内简要说明这只股票，并解释它为什么值得关注以及可能的风险。' },
  { key: 'gelonghui', label: '格隆汇', icon: '📈', prompt: '你是一位财经评论员。请用50字以内简要说明这篇文章，并解释它为什么值得关注。' },
  { key: 'producthunt', label: 'Product Hunt', icon: '🎯', prompt: '你是一位产品评论师。请用50字以内简要说明这个产品，并解释它为什么值得关注。' },
]

const currentSource = ref('github')
const items = ref([])
const loading = ref(false)
const error = ref('')
const currentTime = ref('')
const translating = ref({})
const aiExplaining = ref({})
const aiContent = ref({})
const displayCount = ref(15)

const displayItems = computed(() => items.value.slice(0, displayCount.value))
const hasMore = computed(() => items.value.length > displayCount.value)

const fetchCurrentSource = async () => {
  loading.value = true
  error.value = ''
  displayCount.value = 15

  try {
    const source = sourceList.find(s => s.key === currentSource.value)
    const res = await axios.get(`/api/trending/${currentSource.value}`)

    if (res.data && res.data.error) {
      error.value = res.data.error
      items.value = []
    } else {
      items.value = res.data.items || []
    }
  } catch (e) {
    error.value = '加载失败，请稍后重试'
    items.value = []
  } finally {
    loading.value = false
  }
}

const loadMore = () => {
  displayCount.value += 15
}

const translateTitle = async (item) => {
  if (item.translation) {
    item.translation = null
    return
  }
  translating.value[item.id] = true
  try {
    const res = await axios.get('/api/translate', {
      params: { text: item.title, from_lang: 'en', to_lang: 'zh' }
    })
    if (res.data && res.data.translation) {
      item.translation = res.data.translation
    }
  } catch (e) {
    console.error('翻译失败:', e)
  } finally {
    delete translating.value[item.id]
  }
}

const explainWithAI = async (item) => {
  if (aiContent.value[item.id]) {
    aiContent.value[item.id] = null
    return
  }
  const source = sourceList.find(s => s.key === currentSource.value)
  const expertPrompt = source?.prompt || '请用50字以内简要说明这个内容，并解释它为什么值得关注。'

  aiExplaining.value[item.id] = true
  try {
    const response = await fetch('/api/ai-chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        messages: [{
          role: 'user',
          content: `${expertPrompt}

内容信息：
- 标题：${item.title}
- 作者：${item.author || '未知'}
- 热度：${item.score}
- 链接：${item.url}`
        }]
      })
    })
    const data = await response.json()
    if (data.choices && data.choices[0]) {
      aiContent.value[item.id] = data.choices[0].message.content
    } else {
      aiContent.value[item.id] = data.error || '解释生成失败'
    }
  } catch (e) {
    aiContent.value[item.id] = '请求失败'
  } finally {
    delete aiExplaining.value[item.id]
  }
}

const formatTime = (timestamp) => {
  if (!timestamp) return '-'
  const now = Math.floor(Date.now() / 1000)
  const diff = now - timestamp
  if (diff < 3600) return `${Math.floor(diff / 60)}m`
  if (diff < 86400) return `${Math.floor(diff / 3600)}h`
  return `${Math.floor(diff / 86400)}d`
}

const formatAuthor = (author) => {
  if (!author) return ''
  if (author.length > 15) return author.slice(0, 15) + '...'
  return author
}

const formatScore = (score) => {
  if (score >= 1000000) return (score / 1000000).toFixed(1) + 'M'
  if (score >= 1000) return (score / 1000).toFixed(1) + 'k'
  return score
}

const getMetadataField = (item, field) => {
  return item.metadata?.[field] || ''
}

const updateTime = () => {
  currentTime.value = new Date().toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false
  })
}

let timeTimer = null

watch(currentSource, () => {
  fetchCurrentSource()
})

onMounted(() => {
  fetchCurrentSource()
  updateTime()
  timeTimer = setInterval(updateTime, 1000)
})

onUnmounted(() => {
  if (timeTimer) clearInterval(timeTimer)
})
</script>

<style scoped>
.trending-news {
  padding: 0 20px 20px;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 10px;
  border: 1px solid rgba(255, 255, 255, 0.05);
  margin-bottom: 16px;
  height: 36px;
  box-sizing: border-box;
}

.toolbar-left,
.toolbar-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.update-time {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  color: rgba(255, 255, 255, 0.6);
  padding: 5px 12px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 16px;
  font-family: 'JetBrains Mono', 'SF Mono', 'Fira Code', monospace;
  line-height: 1;
  height: 24px;
  box-sizing: border-box;
}

.time-icon {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.4);
}

.loading-box,
.error-box {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 60px 20px;
  color: rgba(255, 255, 255, 0.5);
  font-size: 14px;
}

.error-box {
  color: #ff4757;
}

.feeds-grid {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.feed-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 14px 16px;
  background: rgba(255, 255, 255, 0.02);
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.05);
  transition: all 0.2s;
}

.feed-item:hover {
  background: rgba(255, 255, 255, 0.04);
  border-color: rgba(255, 255, 255, 0.1);
}

.item-rank {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 69, 0, 0.2);
  color: #ff4500;
  border-radius: 6px;
  font-size: 12px;
  font-weight: bold;
  flex-shrink: 0;
  margin-top: 2px;
}

.item-content {
  flex: 1;
  min-width: 0;
}

.item-title-row {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-bottom: 8px;
}

.item-title {
  font-size: 14px;
  color: #fff;
  text-decoration: none;
  line-height: 1.4;
  display: block;
}

.item-title:hover {
  color: #ff4500;
}

.original-title {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.35);
  text-decoration: line-through;
}

.item-desc {
  margin-top: 6px;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.5);
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.item-lang {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  margin-top: 6px;
  font-size: 11px;
  color: rgba(255, 255, 255, 0.4);
}

.lang-dot {
  width: 6px;
  height: 6px;
  background: #4ecdc4;
  border-radius: 50%;
}

.item-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.meta-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 22px;
  height: 22px;
  border-radius: 4px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  background: transparent;
  color: rgba(255, 255, 255, 0.4);
  cursor: pointer;
  transition: all 0.2s;
  padding: 0;
}

.meta-btn .el-icon {
  font-size: 12px;
}

.meta-btn.translate:hover {
  border-color: rgba(255, 102, 0, 0.5);
  color: #ff6600;
  background: rgba(255, 102, 0, 0.1);
}

.meta-btn.ai:hover {
  border-color: rgba(78, 205, 196, 0.5);
  color: #4ecdc4;
  background: rgba(78, 205, 196, 0.1);
}

.meta-score,
.meta-comments,
.meta-time,
.meta-author {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  font-size: 11px;
  color: rgba(255, 255, 255, 0.4);
}

.meta-score .el-icon,
.meta-comments .el-icon {
  font-size: 12px;
  color: #ff4500;
}

.ai-box {
  margin-top: 10px;
  padding: 10px 12px;
  background: rgba(78, 205, 196, 0.05);
  border: 1px solid rgba(78, 205, 196, 0.15);
  border-radius: 8px;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.8);
  line-height: 1.5;
  white-space: pre-wrap;
}

.load-more {
  display: flex;
  justify-content: center;
  margin-top: 16px;
}

.load-more .el-button {
  background: rgba(255, 255, 255, 0.05);
  border-color: rgba(255, 255, 255, 0.1);
  color: rgba(255, 255, 255, 0.7);
}

.load-more .el-button:hover {
  background: rgba(255, 255, 255, 0.1);
  border-color: rgba(255, 255, 255, 0.2);
  color: #fff;
}

:deep(.el-select) {
  --el-fill-color-blank: rgba(255, 255, 255, 0.05);
  --el-text-color-regular: rgba(255, 255, 255, 0.8);
  --el-border-color: rgba(255, 255, 255, 0.1);
}

:deep(.el-select .el-input__wrapper) {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 6px;
  box-shadow: none;
}

:deep(.el-select .el-input__inner) {
  color: rgba(255, 255, 255, 0.8);
  font-size: 12px;
}

:deep(.el-select-dropdown) {
  background: #1a1a2e;
  border-color: rgba(255, 255, 255, 0.1);
}

:deep(.el-select-dropdown__item) {
  color: rgba(255, 255, 255, 0.8);
  font-size: 12px;
}

:deep(.el-select-dropdown__item.selected) {
  color: #ff4500;
}

.is-loading {
  animation: rotating 1s linear infinite;
}

@keyframes rotating {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>
