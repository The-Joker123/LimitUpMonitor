<template>
  <div class="ai-assistant">
    <div v-if="!isOpen" class="ai-btn" @click="isOpen = true">
      <span class="ai-icon">🤖</span>
      <span class="ai-text">AI助手</span>
    </div>

    <div v-else class="ai-panel">
      <div class="ai-header">
        <div class="ai-title">
          <span class="ai-icon">🤖</span>
          <span>Coding Plan AI</span>
        </div>
        <button class="close-btn" @click="isOpen = false">×</button>
      </div>

      <div class="ai-messages" ref="messagesContainer">
        <div v-if="messages.length === 0" class="welcome-msg">
          <p>👋 你好！我是 AI 助手</p>
          <p class="sub">基于阿里云百炼 Coding Plan，支持 Qwen3.5、GLM-5、MiniMax M2.5、Kimi K2.5</p>
          <div class="quick-prompts">
            <button v-for="prompt in quickPrompts" :key="prompt.text" @click="sendQuickPrompt(prompt.text)">
              {{ prompt.text }}
            </button>
          </div>
        </div>
        <div v-for="(msg, index) in messages" :key="index" :class="['message', msg.role]">
          <div class="message-content">{{ msg.content }}</div>
        </div>
        <div v-if="loading" class="message assistant">
          <div class="message-content loading">
            <span class="dot"></span>
            <span class="dot"></span>
            <span class="dot"></span>
          </div>
        </div>
      </div>

      <div class="ai-input-area">
        <textarea
          v-model="inputText"
          placeholder="输入问题..."
          rows="1"
          @keydown.enter.exact.prevent="sendMessage"
          @input="autoResize"
        ></textarea>
        <button class="send-btn" @click="sendMessage" :disabled="!inputText.trim() || loading">
          发送
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, computed } from 'vue'

const props = defineProps({
  stocks: {
    type: Array,
    default: () => []
  },
  boardStats: {
    type: Array,
    default: () => []
  }
})

const isOpen = ref(false)
const inputText = ref('')
const messages = ref([])
const loading = ref(false)
const messagesContainer = ref(null)

const quickPrompts = computed(() => [
  { text: '分析今日涨停主线', context: '分析当前页面的涨停数据，找出核心主线板块' },
  { text: '连板股有哪些', context: '列出连续涨停的股票及其连板天数' },
  { text: '哪些板块涨停最多', context: '统计各板块涨停数量，按数量排序' }
])

const API_KEY = import.meta.env.VITE_CODING_PLAN_KEY || ''
const BASE_URL = 'https://coding-intl.dashscope.aliyuncs.com/v1'

const formatContextData = () => {
  if (!props.stocks || props.stocks.length === 0) {
    return '暂无涨停数据'
  }

  const totalCount = props.stocks.length
  const continuousStocks = props.stocks.filter(s => s.limit_up_days >= 2)
  const maxContinuous = Math.max(...props.stocks.map(s => s.limit_up_days))

  const industryStats = {}
  props.stocks.forEach(s => {
    industryStats[s.industry] = (industryStats[s.industry] || 0) + 1
  })
  const topIndustries = Object.entries(industryStats)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 10)
    .map(([name, count]) => `${name}: ${count}只`)

  const limitUpStocks = props.stocks
    .sort((a, b) => b.pct_chg - a.pct_chg)
    .slice(0, 20)
    .map(s => `${s.name}(${s.code}) 涨幅${s.pct_chg}% 连板${s.limit_up_days}天 ${s.industry}`)

  return `
【当前页面数据摘要】
- 涨停总数: ${totalCount}只
- 连板股: ${continuousStocks.length}只
- 最高连板: ${maxContinuous}板

【板块统计 TOP10】
${topIndustries.join('\n')}

【涨停股明细(涨幅前20)】
${limitUpStocks.join('\n')}
`.trim()
}

const buildSystemPrompt = () => {
  const contextData = formatContextData()
  return `你是一个专业的金融助手，专门帮助用户分析股票涨停数据。

【重要】用户当前正在查看一个"涨停连板监控"页面，页面上的数据如下：
${contextData}

请基于以上数据回答用户的问题。如果用户问的是分析类问题，请结合数据给出专业的分析意见。
回答要求：
1. 简洁专业，用中文回答
2. 如需引用数据，请从上述数据中提取
3. 如果数据不足或无法回答，请说明情况`.trim()
}

const sendQuickPrompt = (prompt) => {
  inputText.value = prompt
  sendMessage()
}

const sendMessage = async () => {
  if (!inputText.value.trim() || loading.value) return

  const userMsg = { role: 'user', content: inputText.value.trim() }
  messages.value.push(userMsg)
  inputText.value = ''
  loading.value = true
  scrollToBottom()

  try {
    const response = await fetch(`${BASE_URL}/chat/completions`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${API_KEY}`
      },
      body: JSON.stringify({
        model: 'MiniMax',
        messages: [
          { role: 'system', content: buildSystemPrompt() },
          ...messages.value.map(m => ({ role: m.role, content: m.content }))
        ],
        stream: false
      })
    })

    if (!response.ok) {
      throw new Error(`API error: ${response.status}`)
    }

    const data = await response.json()
    const assistantMsg = { role: 'assistant', content: data.choices[0].message.content }
    messages.value.push(assistantMsg)
  } catch (error) {
    messages.value.push({ 
      role: 'assistant', 
      content: `请求失败: ${error.message}。请检查 API Key 是否配置正确。` 
    })
  } finally {
    loading.value = false
    scrollToBottom()
  }
}

const scrollToBottom = () => {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}

const autoResize = (e) => {
  e.target.style.height = 'auto'
  e.target.style.height = Math.min(e.target.scrollHeight, 120) + 'px'
}
</script>

<style scoped>
.ai-assistant {
  position: fixed;
  bottom: 24px;
  right: 24px;
  z-index: 9999;
  font-family: 'PingFang SC', -apple-system, BlinkMacSystemFont, sans-serif;
}

.ai-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 14px 20px;
  background: linear-gradient(135deg, #667eea, #764ba2);
  border-radius: 28px;
  color: #fff;
  cursor: pointer;
  box-shadow: 0 4px 20px rgba(102, 126, 234, 0.4);
  transition: all 0.3s;
}

.ai-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 24px rgba(102, 126, 234, 0.5);
}

.ai-icon {
  font-size: 20px;
}

.ai-text {
  font-size: 14px;
  font-weight: 600;
}

.ai-panel {
  width: 380px;
  height: 520px;
  background: #1a1a2e;
  border-radius: 16px;
  border: 1px solid rgba(255,255,255,0.1);
  display: flex;
  flex-direction: column;
  box-shadow: 0 8px 40px rgba(0,0,0,0.4);
  overflow: hidden;
}

.ai-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background: rgba(255,255,255,0.03);
  border-bottom: 1px solid rgba(255,255,255,0.06);
}

.ai-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 15px;
  font-weight: 600;
  color: #fff;
}

.close-btn {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  border: none;
  background: rgba(255,255,255,0.1);
  color: #fff;
  font-size: 18px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

.close-btn:hover {
  background: rgba(255,255,255,0.2);
}

.ai-messages {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

.welcome-msg {
  text-align: center;
  padding: 24px 16px;
  color: rgba(255,255,255,0.7);
}

.welcome-msg p {
  margin-bottom: 8px;
}

.welcome-msg .sub {
  font-size: 12px;
  color: rgba(255,255,255,0.4);
  margin-bottom: 16px;
}

.quick-prompts {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: center;
}

.quick-prompts button {
  padding: 8px 14px;
  border-radius: 16px;
  border: 1px solid rgba(102,126,234,0.5);
  background: rgba(102,126,234,0.1);
  color: #667eea;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.quick-prompts button:hover {
  background: rgba(102,126,234,0.2);
  border-color: #667eea;
}

.message {
  margin-bottom: 12px;
  display: flex;
}

.message.user {
  justify-content: flex-end;
}

.message.assistant {
  justify-content: flex-start;
}

.message-content {
  max-width: 85%;
  padding: 10px 14px;
  border-radius: 12px;
  font-size: 14px;
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-word;
}

.message.user .message-content {
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: #fff;
  border-bottom-right-radius: 4px;
}

.message.assistant .message-content {
  background: rgba(255,255,255,0.08);
  color: rgba(255,255,255,0.85);
  border-bottom-left-radius: 4px;
}

.loading {
  display: flex;
  gap: 4px;
  padding: 12px 16px;
}

.loading .dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: rgba(255,255,255,0.5);
  animation: bounce 1.4s infinite ease-in-out;
}

.loading .dot:nth-child(1) { animation-delay: 0s; }
.loading .dot:nth-child(2) { animation-delay: 0.2s; }
.loading .dot:nth-child(3) { animation-delay: 0.4s; }

@keyframes bounce {
  0%, 80%, 100% { transform: scale(0.6); opacity: 0.5; }
  40% { transform: scale(1); opacity: 1; }
}

.ai-input-area {
  display: flex;
  gap: 10px;
  padding: 12px 16px;
  border-top: 1px solid rgba(255,255,255,0.06);
  background: rgba(255,255,255,0.02);
}

.ai-input-area textarea {
  flex: 1;
  padding: 10px 14px;
  border-radius: 12px;
  border: 1px solid rgba(255,255,255,0.1);
  background: rgba(255,255,255,0.05);
  color: #fff;
  font-size: 14px;
  resize: none;
  outline: none;
  font-family: inherit;
}

.ai-input-area textarea::placeholder {
  color: rgba(255,255,255,0.3);
}

.ai-input-area textarea:focus {
  border-color: rgba(102,126,234,0.5);
}

.send-btn {
  padding: 10px 18px;
  border-radius: 12px;
  border: none;
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: #fff;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.send-btn:hover:not(:disabled) {
  opacity: 0.9;
}

.send-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
