<template>
  <div class="github-news">
    <div class="toolbar">
      <div class="toolbar-left">
        <el-select v-model="language" size="small" style="width: 120px" @change="fetchAll">
          <el-option label="全部" value="" />
          <el-option label="Python" value="python" />
          <el-option label="JavaScript" value="javascript" />
          <el-option label="TypeScript" value="typescript" />
          <el-option label="Go" value="go" />
          <el-option label="Rust" value="rust" />
          <el-option label="Java" value="java" />
          <el-option label="C++" value="cpp" />
        </el-select>
      </div>
      <div class="toolbar-right">
        <span class="update-time" v-if="currentTime">
          <el-icon class="time-icon"><Clock /></el-icon>
          {{ currentTime }}
        </span>
        <el-button @click="fetchAll" :disabled="anyLoading" size="small" circle>
          <el-icon v-if="anyLoading" class="is-loading"><Loading /></el-icon>
          <el-icon v-else><Refresh /></el-icon>
        </el-button>
      </div>
    </div>

    <div class="feeds-grid">
      <div v-for="feed in feedList" :key="feed.key" class="feed-card">
        <div class="card-header">
          <div class="card-title">
            <span class="feed-icon">{{ feed.icon }}</span>
            <span class="feed-label">{{ feed.label }}</span>
          </div>
          <div class="card-controls">
            <el-button @click="translateAll(feed.key)" :disabled="translatingAll[feed.key]" size="small" title="全部翻译">
              <el-icon v-if="translatingAll[feed.key]" class="is-loading"><Loading /></el-icon>
              <el-icon v-else><Finished /></el-icon>
            </el-button>
            <el-button @click="explainAll(feed.key)" :disabled="aiExplainingAll[feed.key]" size="small" title="全部AI">
              <el-icon v-if="aiExplainingAll[feed.key]" class="is-loading"><Loading /></el-icon>
              <el-icon v-else><MagicStick /></el-icon>
            </el-button>
            <el-button @click="fetchFeed(feed.key)" :disabled="feedData[feed.key].loading" circle size="small">
              <el-icon v-if="feedData[feed.key].loading" class="is-loading"><Loading /></el-icon>
              <el-icon v-else><Refresh /></el-icon>
            </el-button>
          </div>
        </div>

        <div v-if="feedData[feed.key].error" class="card-error">
          {{ feedData[feed.key].error }}
        </div>

        <div v-else-if="feedData[feed.key].loading && !feedData[feed.key].items.length" class="card-loading">
          <el-icon class="is-loading"><Loading /></el-icon>
        </div>

        <div v-else class="card-list">
          <div v-for="(item, index) in feedData[feed.key].items.slice(0, 15)" :key="item.id" class="feed-item">
            <span class="item-rank">{{ index + 1 }}</span>
            <div class="item-content">
              <div class="item-title-row">
                <a :href="item.url" target="_blank" class="item-title">
                  {{ item.translation || item.title }}
                </a>
                <span v-if="item.translation" class="original-title">{{ item.title }}</span>
              </div>
              <div class="item-meta">
                <button class="meta-btn translate" @click="translateRepo(item)" :disabled="translating[item.id]" :title="item.translation ? '原文' : '译'">
                  <el-icon v-if="translating[item.id]" class="is-loading"><Loading /></el-icon>
                  <el-icon v-else><Finished /></el-icon>
                </button>
                <button class="meta-btn ai" @click="explainWithAI(item)" :disabled="aiExplaining[item.id]" title="AI">
                  <el-icon v-if="aiExplaining[item.id]" class="is-loading"><Loading /></el-icon>
                  <el-icon v-else><MagicStick /></el-icon>
                </button>
                <span v-if="item.author" class="meta-author">{{ item.author }}</span>
                <span v-if="item.score" class="meta-score">
                  <el-icon><Star /></el-icon>{{ formatScore(item.score) }}
                </span>
                <span v-if="item.comments" class="meta-comments">
                  <el-icon><Share /></el-icon>{{ formatScore(item.comments) }}
                </span>
                <span v-if="item.metadata?.new_stars_today" class="meta-new">
                  +{{ item.metadata.new_stars_today }} today
                </span>
              </div>
              <div v-if="aiContent[item.id]" class="ai-box">
                {{ aiContent[item.id] }}
              </div>
              <div v-if="item.metadata?.description" class="item-desc">
                {{ item.metadata.description }}
              </div>
              <div v-if="item.metadata?.language" class="item-lang">
                <span class="lang-dot"></span>
                {{ item.metadata.language }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import axios from 'axios'
import { Refresh, Loading, Clock, Finished, MagicStick, Star, Share } from '@element-plus/icons-vue'

const feedList = [
  { key: 'daily', label: '今日', icon: '📅', period: 'daily' },
  { key: 'weekly', label: '本周', icon: '📆', period: 'weekly' },
  { key: 'monthly', label: '本月', icon: '🗓️', period: 'monthly' }
]

const language = ref('')
const feedData = reactive({})
const translating = ref({})
const aiExplaining = ref({})
const aiContent = ref({})
const translatingAll = ref({})
const aiExplainingAll = ref({})
const currentTime = ref('')

feedList.forEach(feed => {
  feedData[feed.key] = { items: [], loading: false, error: '' }
})

const anyLoading = computed(() => feedList.some(f => feedData[f.key].loading))

const fetchFeed = async (feedKey) => {
  const feed = feedList.find(f => f.key === feedKey)
  if (!feed) return

  feedData[feedKey].loading = true
  feedData[feedKey].error = ''

  try {
    const res = await axios.get('/api/trending/github', {
      params: { language: language.value, period: feed.period }
    })

    if (res.data && res.data.error) {
      feedData[feedKey].error = res.data.error
      feedData[feedKey].items = []
    } else {
      feedData[feedKey].items = res.data.items || []
    }
  } catch (e) {
    feedData[feedKey].error = '加载失败'
    feedData[feedKey].items = []
  } finally {
    feedData[feedKey].loading = false
  }
}

const fetchAll = async () => {
  await Promise.all(feedList.map(f => fetchFeed(f.key)))
}

const translateRepo = async (item) => {
  if (item.translation) {
    item.translation = null
    return
  }
  translating.value[item.id] = true
  try {
    const desc = item.metadata?.description || item.title
    const res = await axios.get('/api/translate', {
      params: { text: desc, from_lang: 'en', to_lang: 'zh' }
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

const translateAll = async (feedKey) => {
  const items = feedData[feedKey].items || []
  translatingAll.value[feedKey] = true
  try {
    for (const item of items) {
      if (!item.translation) {
        await translateRepo(item)
      }
    }
  } finally {
    translatingAll.value[feedKey] = false
  }
}

const explainWithAI = async (item) => {
  if (aiContent.value[item.id]) {
    aiContent.value[item.id] = null
    return
  }
  aiExplaining.value[item.id] = true
  try {
    const response = await fetch('/api/ai-chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        messages: [{
          role: 'user',
          content: `你是一位技术架构师。请用50字以内简要说明这个开源项目，并解释它为什么值得关注。

项目信息：
- 名称：${item.title}
- 作者：${item.author}
- Stars：${item.score}
- 描述：${item.metadata?.description || '无'}
- 编程语言：${item.metadata?.language || '未知'}
- 今日新增：${item.metadata?.new_stars_today || 0} stars`
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

const explainAll = async (feedKey) => {
  const items = feedData[feedKey].items || []
  aiExplainingAll.value[feedKey] = true
  try {
    for (const item of items) {
      if (!aiContent.value[item.id]) {
        await explainWithAI(item)
      }
    }
  } finally {
    aiExplainingAll.value[feedKey] = false
  }
}

const formatScore = (score) => {
  if (score >= 1000) return (score / 1000).toFixed(1) + 'k'
  return score
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

onMounted(() => {
  fetchAll()
  updateTime()
  timeTimer = setInterval(updateTime, 1000)
})

onUnmounted(() => {
  if (timeTimer) clearInterval(timeTimer)
})
</script>

<style scoped>
.github-news {
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

.feeds-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

@media (max-width: 1200px) {
  .feeds-grid { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 768px) {
  .feeds-grid { grid-template-columns: 1fr; }
}

.feed-card {
  background: rgba(255, 255, 255, 0.02);
  border-radius: 16px;
  border: 1px solid rgba(255, 255, 255, 0.05);
  overflow: hidden;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: rgba(255, 255, 255, 0.03);
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.card-title {
  display: flex;
  align-items: center;
  gap: 8px;
}

.feed-icon {
  font-size: 18px;
}

.feed-label {
  font-size: 14px;
  font-weight: 600;
  color: #fff;
}

.card-controls {
  display: flex;
  gap: 8px;
  align-items: center;
}

.card-controls .el-button {
  background: rgba(255, 255, 255, 0.05);
  border-color: rgba(255, 255, 255, 0.1);
  color: rgba(255, 255, 255, 0.8);
}

.card-controls .el-button:hover {
  background: rgba(255, 255, 255, 0.1);
  border-color: rgba(255, 255, 255, 0.2);
  color: #fff;
}

.card-controls .el-button:disabled {
  background: rgba(255, 255, 255, 0.03);
  border-color: rgba(255, 255, 255, 0.05);
  color: rgba(255, 255, 255, 0.3);
}

.card-loading {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 40px;
  color: rgba(255, 255, 255, 0.4);
}

.card-error {
  padding: 20px;
  text-align: center;
  color: #ff4757;
  font-size: 13px;
}

.card-list {
  padding: 8px;
  max-height: 480px;
  overflow-y: auto;
}

.card-list::-webkit-scrollbar {
  width: 4px;
}
.card-list::-webkit-scrollbar-track {
  background: transparent;
}
.card-list::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 2px;
}

.feed-item {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 10px 8px;
  border-radius: 8px;
  transition: background 0.2s;
}

.feed-item:hover {
  background: rgba(255, 255, 255, 0.04);
}

.item-rank {
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(110, 84, 148, 0.3);
  color: #a48fff;
  border-radius: 4px;
  font-size: 11px;
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
  gap: 2px;
  margin-bottom: 6px;
}

.item-title {
  font-size: 13px;
  color: #fff;
  text-decoration: none;
  line-height: 1.4;
  display: block;
}

.item-title:hover {
  color: #6e5494;
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
  background: #6e5494;
  border-radius: 50%;
}

.item-meta {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}

.meta-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
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
.meta-author,
.meta-new {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  font-size: 11px;
  color: rgba(255, 255, 255, 0.4);
}

.meta-score .el-icon,
.meta-comments .el-icon {
  font-size: 12px;
  color: #6e5494;
}

.meta-new {
  color: #00ff88;
  font-weight: 600;
}

.ai-box {
  margin-top: 8px;
  padding: 8px;
  background: rgba(78, 205, 196, 0.05);
  border: 1px solid rgba(78, 205, 196, 0.15);
  border-radius: 6px;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.8);
  line-height: 1.5;
  white-space: pre-wrap;
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
  color: #6e5494;
}

.is-loading {
  animation: rotating 1s linear infinite;
}

@keyframes rotating {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>