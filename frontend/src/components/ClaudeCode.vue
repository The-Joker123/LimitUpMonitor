<template>
  <div class="claude-code">
    <div class="toolbar">
      <div class="toolbar-left">
        <span class="claude-badge">Claude Code</span>
        <span class="version-badge">v2.1+</span>
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
      <div class="feed-card official-card">
        <div class="card-header">
          <div class="card-title">
            <span class="feed-icon">📋</span>
            <span class="feed-label">官方更新</span>
          </div>
          <div class="card-controls">
            <el-button @click="translateAllUpdates" :disabled="translatingAll.updates" size="small" title="全部翻译">
              <el-icon v-if="translatingAll.updates" class="is-loading"><Loading /></el-icon>
              <el-icon v-else><Finished /></el-icon>
            </el-button>
            <el-button @click="explainAllUpdates" :disabled="aiExplainingAll.updates" size="small" title="全部AI">
              <el-icon v-if="aiExplainingAll.updates" class="is-loading"><Loading /></el-icon>
              <el-icon v-else><MagicStick /></el-icon>
            </el-button>
            <a href="https://code.claude.com/docs/en/changelog" target="_blank" class="external-link" title="查看完整更新日志">
              <el-icon><Link /></el-icon>
            </a>
            <el-button @click="fetchUpdates" :disabled="loading.updates" circle size="small">
              <el-icon v-if="loading.updates" class="is-loading"><Loading /></el-icon>
              <el-icon v-else><Refresh /></el-icon>
            </el-button>
          </div>
        </div>

        <div v-if="error.updates" class="card-error">{{ error.updates }}</div>
        <div v-else-if="loading.updates" class="card-loading">
          <el-icon class="is-loading"><Loading /></el-icon>
        </div>
        <div v-else class="card-list">
          <div v-for="item in updates" :key="item.version" class="update-item">
            <div class="update-header">
              <span class="update-version">{{ item.version }}</span>
              <span class="update-date">{{ item.date }}</span>
            </div>
            <div class="update-content">
              {{ item.translation || item.highlights }}
            </div>
            <div class="item-actions">
              <button class="meta-btn translate" @click="translateUpdate(item)" :disabled="translating[item.version]" title="翻译">
                <el-icon v-if="translating[item.version]" class="is-loading"><Loading /></el-icon>
                <el-icon v-else><Finished /></el-icon>
              </button>
              <button class="meta-btn ai" @click="explainUpdate(item)" :disabled="aiExplaining[item.version]" title="AI解读">
                <el-icon v-if="aiExplaining[item.version]" class="is-loading"><Loading /></el-icon>
                <el-icon v-else><MagicStick /></el-icon>
              </button>
            </div>
            <div v-if="aiContent[item.version]" class="ai-box">
              {{ aiContent[item.version] }}
            </div>
          </div>
          <div v-if="updates.length === 0" class="empty-state">
            暂无更新数据
          </div>
        </div>
      </div>

      <div class="feed-card hn-card">
        <div class="card-header">
          <div class="card-title">
            <span class="feed-icon">📰</span>
            <span class="feed-label">Hacker News</span>
          </div>
          <div class="card-controls">
            <el-button @click="translateAllHN" :disabled="translatingAll.hn" size="small" title="全部翻译">
              <el-icon v-if="translatingAll.hn" class="is-loading"><Loading /></el-icon>
              <el-icon v-else><Finished /></el-icon>
            </el-button>
            <el-button @click="explainAllHN" :disabled="aiExplainingAll.hn" size="small" title="全部AI">
              <el-icon v-if="aiExplainingAll.hn" class="is-loading"><Loading /></el-icon>
              <el-icon v-else><MagicStick /></el-icon>
            </el-button>
            <a href="https://hn.algolia.com/?q=Claude+Code" target="_blank" class="external-link" title="在 HN 搜索">
              <el-icon><Link /></el-icon>
            </a>
            <el-button @click="fetchHN" :disabled="loading.hn" circle size="small">
              <el-icon v-if="loading.hn" class="is-loading"><Loading /></el-icon>
              <el-icon v-else><Refresh /></el-icon>
            </el-button>
          </div>
        </div>

        <div v-if="error.hn" class="card-error">{{ error.hn }}</div>
        <div v-else-if="loading.hn" class="card-loading">
          <el-icon class="is-loading"><Loading /></el-icon>
        </div>
        <div v-else class="card-list">
          <div v-for="(item, index) in hackerNews" :key="index" class="hn-item">
            <span class="item-rank">{{ index + 1 }}</span>
            <div class="item-content">
              <div class="item-title-row">
                <a :href="item.url" target="_blank" class="item-title">
                  {{ item.translation || item.title }}
                </a>
                <span v-if="item.translation" class="original-title">{{ item.title }}</span>
              </div>
              <div class="item-meta">
                <span class="meta-score">
                  <el-icon><Star /></el-icon>
                  {{ item.score }}
                </span>
                <span class="meta-comments">
                  <el-icon><ChatDotRound /></el-icon>
                  {{ item.comments }}
                </span>
                <span class="meta-author">by {{ item.author }}</span>
                <span class="meta-time">{{ item.time }}</span>
              </div>
              <div class="item-actions">
                <button class="meta-btn translate" @click="translateHN(item)" :disabled="translating[index]" title="翻译">
                  <el-icon v-if="translating[index]" class="is-loading"><Loading /></el-icon>
                  <el-icon v-else><Finished /></el-icon>
                </button>
                <button class="meta-btn ai" @click="explainHN(item)" :disabled="aiExplaining[index]" title="AI解读">
                  <el-icon v-if="aiExplaining[index]" class="is-loading"><Loading /></el-icon>
                  <el-icon v-else><MagicStick /></el-icon>
                </button>
              </div>
              <div v-if="aiContent[index]" class="ai-box">
                {{ aiContent[index] }}
              </div>
            </div>
          </div>
          <div v-if="hackerNews.length === 0" class="empty-state">
            暂无讨论
          </div>
        </div>
      </div>

      <div class="feed-card links-card">
        <div class="card-header">
          <div class="card-title">
            <span class="feed-icon">🔗</span>
            <span class="feed-label">相关链接</span>
          </div>
        </div>
        <div class="card-list links-list">
          <a href="https://claudelog.com/claude-code-changelog" target="_blank" class="link-item">
            <span class="link-icon">📜</span>
            <span class="link-text">
              <span class="link-title">ClaudeLog</span>
              <span class="link-desc">版本历史聚合</span>
            </span>
          </a>
          <a href="https://www.anthropic.com/news" target="_blank" class="link-item">
            <span class="link-icon">🤖</span>
            <span class="link-text">
              <span class="link-title">Anthropic 官方博客</span>
              <span class="link-desc">AI 安全与研究</span>
            </span>
          </a>
          <a href="https://docs.anthropic.com/" target="_blank" class="link-item">
            <span class="link-icon">📚</span>
            <span class="link-text">
              <span class="link-title">API 文档</span>
              <span class="link-desc">开发者文档</span>
            </span>
          </a>
          <a href="https://github.com/anthropics/claude-code" target="_blank" class="link-item">
            <span class="link-icon">💻</span>
            <span class="link-text">
              <span class="link-title">GitHub</span>
              <span class="link-desc">源码与 Issue</span>
            </span>
          </a>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import axios from 'axios'
import { Refresh, Loading, Clock, Link, Star, ChatDotRound, Finished, MagicStick } from '@element-plus/icons-vue'

const updates = ref([])
const hackerNews = ref([])
const loading = reactive({ updates: false, hn: false })
const error = reactive({ updates: '', hn: '' })
const currentTime = ref('')
const translating = ref({})
const aiExplaining = ref({})
const aiContent = ref({})
const translatingAll = ref({})
const aiExplainingAll = ref({})

const anyLoading = computed(() => loading.updates || loading.hn)

const fetchUpdates = async () => {
  loading.updates = true
  error.updates = ''
  try {
    const res = await axios.get('/api/claude-code/updates')
    updates.value = res.data.data || []
  } catch (e) {
    error.updates = '加载失败'
  } finally {
    loading.updates = false
  }
}

const fetchHN = async () => {
  loading.hn = true
  error.hn = ''
  try {
    const res = await axios.get('/api/claude-code/hacker-news')
    hackerNews.value = res.data.data || []
  } catch (e) {
    error.hn = '加载失败'
  } finally {
    loading.hn = false
  }
}

const fetchAll = async () => {
  await Promise.all([fetchUpdates(), fetchHN()])
}

const translateUpdate = async (item) => {
  if (item.translation) {
    item.translation = null
    return
  }
  translating.value[item.version] = true
  try {
    const res = await axios.get('/api/translate', {
      params: { text: item.highlights, from_lang: 'en', to_lang: 'zh' }
    })
    if (res.data && res.data.translation) {
      item.translation = res.data.translation
    }
  } catch (e) {
    console.error('翻译失败:', e)
  } finally {
    delete translating.value[item.version]
  }
}

const translateAllUpdates = async () => {
  translatingAll.value.updates = true
  try {
    for (const item of updates.value) {
      if (!item.translation) {
        await translateUpdate(item)
      }
    }
  } finally {
    translatingAll.value.updates = false
  }
}

const explainUpdate = async (item) => {
  if (aiContent.value[item.version]) {
    aiContent.value[item.version] = null
    return
  }
  aiExplaining.value[item.version] = true
  try {
    const response = await fetch('/api/ai-chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        messages: [{
          role: 'user',
          content: `你是一位 Claude Code 专家。请用 50 字以内简要说明这个更新的内容，并解释它对开发者的意义和实际价值。

版本信息：
- 版本号：${item.version}
- 发布日期：${item.date}
- 更新内容：${item.highlights}`
        }]
      })
    })
    const data = await response.json()
    if (data.choices && data.choices[0]) {
      aiContent.value[item.version] = data.choices[0].message.content
    } else {
      aiContent.value[item.version] = data.error || '解释生成失败'
    }
  } catch (e) {
    aiContent.value[item.version] = '请求失败'
  } finally {
    delete aiExplaining.value[item.version]
  }
}

const explainAllUpdates = async () => {
  aiExplainingAll.value.updates = true
  try {
    for (const item of updates.value) {
      if (!aiContent.value[item.version]) {
        await explainUpdate(item)
      }
    }
  } finally {
    aiExplainingAll.value.updates = false
  }
}

const translateHN = async (item) => {
  if (item.translation) {
    item.translation = null
    return
  }
  const index = hackerNews.value.indexOf(item)
  translating.value[index] = true
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
    delete translating.value[index]
  }
}

const translateAllHN = async () => {
  translatingAll.value.hn = true
  try {
    for (const item of hackerNews.value) {
      if (!item.translation) {
        await translateHN(item)
      }
    }
  } finally {
    translatingAll.value.hn = false
  }
}

const explainHN = async (item) => {
  const index = hackerNews.value.indexOf(item)
  if (aiContent.value[index]) {
    aiContent.value[index] = null
    return
  }
  aiExplaining.value[index] = true
  try {
    const response = await fetch('/api/ai-chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        messages: [{
          role: 'user',
          content: `你是一位科技评论专家。请用 50 字以内简要说明这篇文章的内容，并解释它为什么值得关注以及可能带来的影响。

文章信息：
- 标题：${item.title}
- 作者：${item.author}
- 评分：${item.score}
- 评论数：${item.comments}
- 链接：${item.url}`
        }]
      })
    })
    const data = await response.json()
    if (data.choices && data.choices[0]) {
      aiContent.value[index] = data.choices[0].message.content
    } else {
      aiContent.value[index] = data.error || '解释生成失败'
    }
  } catch (e) {
    aiContent.value[index] = '请求失败'
  } finally {
    delete aiExplaining.value[index]
  }
}

const explainAllHN = async () => {
  aiExplainingAll.value.hn = true
  try {
    for (const item of hackerNews.value) {
      const index = hackerNews.value.indexOf(item)
      if (!aiContent.value[index]) {
        await explainHN(item)
      }
    }
  } finally {
    aiExplainingAll.value.hn = false
  }
}

const updateTime = () => {
  const now = new Date()
  currentTime.value = now.toLocaleTimeString('zh-CN', {
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
.claude-code {
  padding: 0 20px 20px;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: nowrap;
  padding: 8px 12px;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 10px;
  border: 1px solid rgba(255, 255, 255, 0.05);
  margin-bottom: 16px;
  height: 44px;
  box-sizing: border-box;
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.toolbar-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.claude-badge {
  background: linear-gradient(135deg, #ff6b6b, #ee5a24);
  color: #fff;
  padding: 4px 12px;
  border-radius: 16px;
  font-size: 12px;
  font-weight: 600;
}

.version-badge {
  background: rgba(255, 107, 107, 0.2);
  color: #ff6b6b;
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 11px;
  font-weight: 500;
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

.official-card .card-header {
  border-bottom: 1px solid rgba(255, 107, 107, 0.15);
}

.official-card .item-rank {
  background: rgba(255, 107, 107, 0.2);
  color: #ff6b6b;
}

.hn-card .item-rank {
  background: rgba(255, 69, 0, 0.2);
  color: #ff4500;
}

.links-card {
  background: rgba(255, 107, 107, 0.03);
}

.links-card .card-header {
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: rgba(255, 255, 255, 0.03);
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
  gap: 6px;
  align-items: center;
}

.external-link {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: rgba(255, 255, 255, 0.6);
  text-decoration: none;
  transition: all 0.2s;
}

.external-link:hover {
  background: rgba(255, 255, 255, 0.1);
  border-color: rgba(255, 255, 255, 0.2);
  color: #fff;
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

.empty-state {
  padding: 30px;
  text-align: center;
  color: rgba(255, 255, 255, 0.3);
  font-size: 13px;
}

.card-list {
  padding: 8px;
  max-height: 500px;
  overflow-y: auto;
}

.card-list::-webkit-scrollbar { width: 4px; }
.card-list::-webkit-scrollbar-track { background: transparent; }
.card-list::-webkit-scrollbar-thumb { background: rgba(255, 255, 255, 0.1); border-radius: 2px; }

.update-item {
  padding: 12px 8px;
  border-radius: 8px;
  transition: background 0.2s;
}

.update-item:hover {
  background: rgba(255, 255, 255, 0.04);
}

.update-item:not(:last-child) {
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.update-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.update-version {
  background: rgba(255, 107, 107, 0.15);
  color: #ff6b6b;
  padding: 2px 8px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 600;
  font-family: 'JetBrains Mono', monospace;
}

.update-date {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.4);
}

.update-content {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.7);
  line-height: 1.5;
  margin-bottom: 6px;
}

.item-actions {
  display: flex;
  gap: 4px;
  margin-bottom: 4px;
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

.hn-item {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 10px 8px;
  border-radius: 8px;
  transition: background 0.2s;
}

.hn-item:hover {
  background: rgba(255, 255, 255, 0.04);
}

.item-rank {
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
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
  color: #ff6b6b;
}

.original-title {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.35);
  text-decoration: line-through;
}

.item-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 6px;
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

.links-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.link-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border-radius: 8px;
  text-decoration: none;
  transition: background 0.2s;
}

.link-item:hover {
  background: rgba(255, 255, 255, 0.05);
}

.link-icon {
  font-size: 20px;
}

.link-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.link-title {
  font-size: 13px;
  color: #fff;
  font-weight: 500;
}

.link-desc {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.4);
}
</style>
