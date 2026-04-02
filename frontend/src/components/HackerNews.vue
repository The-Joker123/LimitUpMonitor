<template>
  <div class="hacker-news">
    <div class="page-header">
      <h2>Hacker News 热门话题</h2>
      <div class="header-controls">
        <el-select v-model="selectedFeed" placeholder="选择类型" size="default" @change="fetchNews">
          <el-option label="热门" value="top" />
          <el-option label="最新" value="new" />
          <el-option label="最佳" value="best" />
        </el-select>
        <el-button @click="fetchNews" :loading="loading">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>
    </div>

    <div v-if="error" class="error-message">
      <p>{{ error }}</p>
    </div>

    <div v-else-if="loading" class="loading-state">
      <el-icon class="is-loading"><Loading /></el-icon>
      <span>加载中...</span>
    </div>

    <div v-else class="news-container">
      <div class="news-list">
        <div v-for="(item, index) in stories" :key="item.id" class="news-item">
          <div class="news-rank" :class="getRankClass(index + 1)">{{ index + 1 }}</div>
          <div class="news-content">
            <div class="news-title-container">
              <a :href="item.url || `https://news.ycombinator.com/item?id=${item.id}`" target="_blank" class="news-title">
                {{ item.translation || item.title }}
              </a>
              <span v-if="item.translation" class="original-title">{{ item.title }}</span>
              <button 
                class="translate-btn" 
                @click="translateTitle(item)"
                :disabled="translating[item.id]"
                :title="item.translation ? '显示原文' : '翻译'"
              >
                <el-icon v-if="translating[item.id]" class="is-loading"><Loading /></el-icon>
                <el-icon v-else><Finished /></el-icon>
              </button>
              <button 
                class="ai-btn" 
                @click="explainWithAI(item)"
                :disabled="aiExplaining[item.id]"
                title="AI讲解"
              >
                <el-icon v-if="aiExplaining[item.id]" class="is-loading"><Loading /></el-icon>
                <el-icon v-else><MagicStick /></el-icon>
              </button>
            </div>
            <div v-if="aiContent[item.id]" class="ai-explain">
              <div class="ai-content">{{ aiContent[item.id] }}</div>
            </div>
            <div class="news-meta">
              <span class="meta-item">
                <el-icon><ArrowUp /></el-icon>
                {{ item.score }}
              </span>
              <span class="meta-item">
                <el-icon><ChatLineSquare /></el-icon>
                {{ item.descendants || 0 }}
              </span>
              <span class="meta-item time">
                <el-icon><Clock /></el-icon>
                {{ formatTime(item.time) }}
              </span>
              <span class="meta-item author">
                by {{ item.by }}
              </span>
            </div>
            <div v-if="item.domain" class="news-domain">{{ item.domain }}</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { Refresh, Loading, ArrowUp, ChatLineSquare, Clock, Finished, MagicStick } from '@element-plus/icons-vue'

const stories = ref([])
const loading = ref(false)
const error = ref('')
const selectedFeed = ref('top')
const translating = ref({})
const aiExplaining = ref({})
const aiContent = ref({})

const feedMap = {
  'top': 'topstories',
  'new': 'newstories',
  'best': 'beststories'
}

const fetchNews = async () => {
  loading.value = true
  error.value = ''
  try {
    const idsUrl = `https://hacker-news.firebaseio.com/v0/${feedMap[selectedFeed.value]}.json`
    const idsResponse = await axios.get(idsUrl)
    const ids = idsResponse.data.slice(0, 30)
    
    const storiesData = await Promise.all(
      ids.map(async (id) => {
        try {
          const response = await axios.get(`https://hacker-news.firebaseio.com/v0/item/${id}.json`)
          const item = response.data
          if (item && item.type === 'story') {
            let domain = ''
            if (item.url) {
              try {
                domain = new URL(item.url).hostname.replace('www.', '')
              } catch (e) {}
            }
            return { ...item, domain }
          }
          return null
        } catch (e) {
          return null
        }
      })
    )
    
    stories.value = storiesData.filter(s => s !== null)
  } catch (e) {
    error.value = '获取失败: ' + (e.message || '未知错误')
  } finally {
    loading.value = false
  }
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
          content: `你是一位科技资讯评论员。请用50字以内简要说明这篇文章的内容，并解释它为什么值得关注（上榜）。

文章信息：
- 标题：${item.title}
- 作者：${item.by}
- 得分：${item.score}分
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
    aiContent.value[item.id] = '请求失败: ' + e.message
  } finally {
    delete aiExplaining.value[item.id]
  }
}

const formatTime = (timestamp) => {
  const now = Math.floor(Date.now() / 1000)
  const diff = now - timestamp
  
  if (diff < 60) return `${diff}秒前`
  if (diff < 3600) return `${Math.floor(diff / 60)}分钟前`
  if (diff < 86400) return `${Math.floor(diff / 3600)}小时前`
  return `${Math.floor(diff / 86400)}天前`
}

const getRankClass = (rank) => {
  if (rank <= 3) return `rank-top${rank}`
  return ''
}

onMounted(() => {
  fetchNews()
})
</script>

<style scoped>
.hacker-news {
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
  color: #fff;
}

.header-controls {
  display: flex;
  gap: 12px;
  align-items: center;
}

.error-message {
  background: rgba(255, 71, 87, 0.1);
  border: 1px solid rgba(255, 71, 87, 0.3);
  border-radius: 8px;
  padding: 24px;
  text-align: center;
  color: #ff4757;
}

.loading-state {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 12px;
  padding: 60px;
  color: rgba(255, 255, 255, 0.5);
}

.news-container {
  background: rgba(255, 255, 255, 0.02);
  border-radius: 16px;
  border: 1px solid rgba(255, 255, 255, 0.05);
  padding: 20px;
}

.news-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.news-item {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  padding: 16px;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.05);
  transition: all 0.2s;
}

.news-item:hover {
  background: rgba(255, 255, 255, 0.06);
  border-color: rgba(255, 255, 255, 0.1);
  transform: translateY(-2px);
}

.news-rank {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #ff6600, #ff8533);
  color: #fff;
  border-radius: 50%;
  font-weight: bold;
  font-size: 14px;
  flex-shrink: 0;
}

.rank-top1 {
  background: linear-gradient(135deg, #ffd700, #ffb700);
  font-size: 16px;
}

.rank-top2 {
  background: linear-gradient(135deg, #c0c0c0, #a8a8a8);
  font-size: 15px;
}

.rank-top3 {
  background: linear-gradient(135deg, #cd7f32, #b87333);
  font-size: 14px;
}

.news-content {
  flex: 1;
  min-width: 0;
}

.news-title {
  font-size: 16px;
  font-weight: 500;
  color: #fff;
  text-decoration: none;
  display: block;
  line-height: 1.4;
  margin-bottom: 8px;
}

.news-title:hover {
  color: #ff6600;
}

.news-title-container {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.original-title {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.4);
  text-decoration: line-through;
}

.translate-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border-radius: 4px;
  border: 1px solid rgba(255, 102, 0, 0.3);
  background: rgba(255, 102, 0, 0.1);
  color: #ff6600;
  cursor: pointer;
  transition: all 0.2s;
  flex-shrink: 0;
}

.translate-btn:hover {
  background: rgba(255, 102, 0, 0.2);
  border-color: #ff6600;
}

.translate-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.translate-btn .el-icon {
  font-size: 14px;
}

.ai-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border-radius: 4px;
  border: 1px solid rgba(78, 205, 196, 0.3);
  background: rgba(78, 205, 196, 0.1);
  color: #4ecdc4;
  cursor: pointer;
  transition: all 0.2s;
  flex-shrink: 0;
}

.ai-btn:hover {
  background: rgba(78, 205, 196, 0.2);
  border-color: #4ecdc4;
}

.ai-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.ai-btn .el-icon {
  font-size: 14px;
}

.ai-explain {
  margin-top: 12px;
  padding: 12px;
  background: rgba(78, 205, 196, 0.05);
  border: 1px solid rgba(78, 205, 196, 0.2);
  border-radius: 8px;
}

.ai-content {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.85);
  line-height: 1.6;
  white-space: pre-wrap;
}

.news-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.meta-item {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.5);
}

.meta-item .el-icon {
  font-size: 14px;
  color: #ff6600;
}

.meta-item.time {
  color: rgba(255, 255, 255, 0.4);
}

.meta-item.author {
  color: rgba(255, 255, 255, 0.4);
}

.news-domain {
  display: inline-block;
  margin-top: 8px;
  font-size: 11px;
  padding: 2px 8px;
  background: rgba(255, 102, 0, 0.15);
  color: #ff8533;
  border-radius: 8px;
}
</style>
