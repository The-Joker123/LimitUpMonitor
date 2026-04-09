<template>
  <div class="hacker-news">
    <div class="toolbar">
      <div class="toolbar-right">
        <span class="update-time" v-if="currentTime">
          <el-icon class="time-icon"><Clock /></el-icon>
          {{ currentTime }}
        </span>
        <span class="update-time eastern" v-if="easternTime">
          <span class="et-label">ET</span>
          {{ easternTime }}
        </span>
        <span class="update-time pacific" v-if="pacificTime">
          <span class="et-label">PT</span>
          {{ pacificTime }}
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
            <el-select v-model="feedSortMap[feed.key]" size="small" style="width: 80px" @change="sortFeed(feed.key)">
              <el-option label="默认" value="default" />
              <el-option label="分数" value="score" />
              <el-option label="评论" value="comments" />
            </el-select>
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

        <div v-else-if="feedData[feed.key].loading" class="card-loading">
          <el-icon class="is-loading"><Loading /></el-icon>
        </div>

        <div v-else class="card-list">
          <div
            v-for="(item, index) in getDisplayStories(feed.key)"
            :key="item.id"
            class="feed-item"
          >
            <span class="item-rank">{{ index + 1 }}</span>
            <div class="item-content">
              <div class="item-title-row">
                <a
                  :href="getItemUrl(item, feed.key)"
                  target="_blank"
                  class="item-title"
                >
                  {{ item.translation || item.title }}
                </a>
                <span v-if="item.translation" class="original-title">{{ item.title }}</span>
              </div>
              <div class="item-meta">
                <button class="meta-btn translate" @click="translateTitle(item)" :disabled="translating[item.id]" :title="item.translation ? '原文' : '译'">
                  <el-icon v-if="translating[item.id]" class="is-loading"><Loading /></el-icon>
                  <el-icon v-else><Finished /></el-icon>
                </button>
                <button class="meta-btn ai" @click="explainWithAI(item)" :disabled="aiExplaining[item.id]" title="AI">
                  <el-icon v-if="aiExplaining[item.id]" class="is-loading"><Loading /></el-icon>
                  <el-icon v-else><MagicStick /></el-icon>
                </button>
                <span class="meta-score">
                  <el-icon><ArrowUp /></el-icon>{{ item.score }}
                </span>
                <span v-if="feed.key !== 'jobs'" class="meta-comments">
                  <el-icon><ChatLineSquare /></el-icon>{{ item.descendants || 0 }}
                </span>
                <span class="meta-time">{{ formatTime(item.time) }}</span>
                <span class="meta-author">by {{ item.by }}</span>
                <span v-if="item.domain" class="meta-domain">{{ item.domain }}</span>
              </div>
              <div v-if="aiContent[item.id]" class="ai-box">
                {{ aiContent[item.id] }}
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
import { Refresh, Loading, ArrowUp, ChatLineSquare, Clock, Finished, MagicStick } from '@element-plus/icons-vue'

const feedList = [
  { key: 'top',  label: '热门', icon: '🔥', endpoint: 'topstories' },
  { key: 'new',  label: '最新', icon: '✨', endpoint: 'newstories' },
  { key: 'best', label: '最佳', icon: '⭐', endpoint: 'beststories' },
  { key: 'ask',  label: 'Ask',  icon: '❓', endpoint: 'askstories' },
  { key: 'show', label: 'Show', icon: '💡', endpoint: 'showstories' },
  { key: 'jobs', label: 'Jobs', icon: '💼', endpoint: 'jobstories' }
]

const feedData = reactive({})
const feedSortMap = reactive({})
const translating = ref({})
const aiExplaining = ref({})
const aiContent = ref({})
const translatingAll = ref({})
const aiExplainingAll = ref({})
const currentTime = ref('')
const easternTime = ref('')
const pacificTime = ref('')

feedList.forEach(feed => {
  feedData[feed.key] = { stories: [], loading: false, error: '' }
  feedSortMap[feed.key] = 'default'
})

const anyLoading = computed(() => feedList.some(f => feedData[f.key].loading))

const getDisplayStories = (feedKey) => {
  const stories = feedData[feedKey].stories || []
  const sort = feedSortMap[feedKey] || 'default'
  const display = stories.slice(0, 15)
  if (sort === 'score') return [...display].sort((a, b) => b.score - a.score)
  if (sort === 'comments') return [...display].sort((a, b) => (b.descendants || 0) - (a.descendants || 0))
  return display
}

const sortFeed = (feedKey) => {
  // Trigger reactivity by reassigning
  const map = { ...feedSortMap }
  feedSortMap[feedKey] = map[feedKey]
}

const getItemUrl = (item, feedKey) => {
  if (feedKey === 'jobs') return `https://news.ycombinator.com/item?id=${item.id}`
  return item.url || `https://news.ycombinator.com/item?id=${item.id}`
}

const fetchFeed = async (feedKey) => {
  const feed = feedList.find(f => f.key === feedKey)
  if (!feed) return

  feedData[feedKey].loading = true
  feedData[feedKey].error = ''
  try {
    const idsResponse = await axios.get(`https://hacker-news.firebaseio.com/v0/${feed.endpoint}.json`)
    const ids = (idsResponse.data || []).slice(0, 20)

    const storiesData = await Promise.all(
      ids.map(async (id) => {
        try {
          const res = await axios.get(`https://hacker-news.firebaseio.com/v0/item/${id}.json`)
          const item = res.data
          if (!item || item.type === 'job') return null
          let domain = ''
          if (item.url) {
            try { domain = new URL(item.url).hostname.replace('www.', '') } catch (e) {}
          }
          return { ...item, domain }
        } catch (e) { return null }
      })
    )

    feedData[feedKey].stories = storiesData.filter(s => s !== null)
  } catch (e) {
    feedData[feedKey].error = '加载失败'
  } finally {
    feedData[feedKey].loading = false
  }
}

const fetchAll = async () => {
  await Promise.all(feedList.map(f => fetchFeed(f.key)))
}

const translateTitle = async (item) => {
  if (item.translation) {
    item.translation = null
    return
  }
  translating.value[item.id] = true
  try {
    const response = await axios.get('/api/translate', {
      params: { text: item.title, from_lang: 'en', to_lang: 'zh' }
    })
    if (response.data && response.data.translation) {
      item.translation = response.data.translation
    }
  } catch (e) {
    console.error('翻译失败:', e)
  } finally {
    delete translating.value[item.id]
  }
}

const translateAll = async (feedKey) => {
  const stories = feedData[feedKey].stories || []
  translatingAll.value[feedKey] = true
  try {
    for (const item of stories) {
      if (!item.translation) {
        await translateTitle(item)
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
          content: `你是一位科技资讯评论员。请用50字以内简要说明这篇文章的内容，并解释它为什么值得关注。

文章信息：
- 标题：${item.title}
- 作者：${item.by}
- 得分：${item.score}分
- 链接：${item.url || '无'}`
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
  const stories = feedData[feedKey].stories || []
  aiExplainingAll.value[feedKey] = true
  try {
    for (const item of stories) {
      if (!aiContent.value[item.id]) {
        await explainWithAI(item)
      }
    }
  } finally {
    aiExplainingAll.value[feedKey] = false
  }
}

const formatTime = (timestamp) => {
  const now = Math.floor(Date.now() / 1000)
  const diff = now - timestamp
  if (diff < 60) return `${diff}s`
  if (diff < 3600) return `${Math.floor(diff / 60)}m`
  if (diff < 86400) return `${Math.floor(diff / 3600)}h`
  return `${Math.floor(diff / 86400)}d`
}

const updateTime = () => {
  const now = new Date()
  currentTime.value = now.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false })
  easternTime.value = now.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: false, timeZone: 'America/New_York' })
  pacificTime.value = now.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: false, timeZone: 'America/Los_Angeles' })
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
.hacker-news {
  padding: 0 20px 20px;
}

.toolbar {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  flex-wrap: nowrap;
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
  flex-shrink: 0;
}

.refresh-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
}

.refresh-btn .el-icon {
  font-size: 14px;
}

.refresh-btn .is-loading {
  animation: rotating 1s linear infinite;
}

@keyframes rotating {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
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

.eastern,
.pacific {
  color: rgba(255, 255, 255, 0.5);
  padding-left: 8px;
  border-left: 1px solid rgba(255, 255, 255, 0.1);
  margin-left: 4px;
}

.et-label {
  font-size: 10px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.3);
  margin-right: 4px;
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

:deep(.el-select) {
  --el-fill-color-blank: rgba(255, 255, 255, 0.05);
  --el-text-color-regular: rgba(255, 255, 255, 0.8);
  --el-border-color: rgba(255, 255, 255, 0.1);
}

:deep(.el-input__wrapper) {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 6px;
  box-shadow: none;
}

:deep(.el-input__inner) {
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
  color: #ff6600;
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
  background: rgba(255, 102, 0, 0.2);
  color: #ff6600;
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
  color: #ff6600;
}

.original-title {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.35);
  text-decoration: line-through;
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
.meta-domain {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  font-size: 11px;
  color: rgba(255, 255, 255, 0.4);
}

.meta-score .el-icon,
.meta-comments .el-icon {
  font-size: 12px;
  color: #ff6600;
}

.meta-domain {
  padding: 1px 6px;
  background: rgba(255, 102, 0, 0.1);
  border-radius: 4px;
  color: #ff8533;
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
</style>
