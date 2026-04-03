<template>
  <div v-if="visible" class="settings-overlay" @click.self="close">
    <div class="settings-modal">
      <div class="modal-header">
        <h3>设置</h3>
        <button class="close-btn" @click="close">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M18 6L6 18M6 6l12 12"/>
          </svg>
        </button>
      </div>

      <div class="modal-body">
        <div class="section-title">AI 模型配置</div>

        <div class="form-group">
          <label>Provider</label>
          <el-select v-model="form.provider" style="width: 100%">
            <el-option label="MiniMax" value="minimax" />
            <el-option label="阿里百炼 (DashScope)" value="dashscope" />
            <el-option label="OpenAI" value="openai" />
            <el-option label="Anthropic" value="anthropic" />
          </el-select>
        </div>

        <div class="form-group">
          <label>API Key</label>
          <el-input
            v-model="form.apiKey"
            type="password"
            placeholder="输入 API Key"
            show-password
          />
        </div>

        <div class="form-group">
          <label>Base URL</label>
          <el-input v-model="form.baseUrl" placeholder="API 端点地址" />
        </div>

        <div class="form-group">
          <label>Model</label>
          <el-input v-model="form.model" placeholder="模型名称" />
        </div>

        <div v-if="error" class="error-msg">{{ error }}</div>
        <div v-if="success" class="success-msg">{{ success }}</div>
      </div>

      <div class="modal-footer">
        <el-button @click="close">取消</el-button>
        <el-button type="primary" @click="save" :loading="saving">保存</el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import axios from 'axios'

const props = defineProps({ visible: Boolean })
const emit = defineEmits(['close', 'saved'])

const providers = {
  minimax: {
    baseUrl: 'https://api.minimaxi.com/anthropic',
    model: 'MiniMax-M2.7'
  },
  dashscope: {
    baseUrl: 'https://dashscope.aliyuncs.com/compatible-mode/v1',
    model: 'qwen-plus'
  },
  openai: {
    baseUrl: 'https://api.openai.com/v1',
    model: 'gpt-4o'
  },
  anthropic: {
    baseUrl: 'https://api.anthropic.com',
    model: 'claude-3-5-sonnet-20241022'
  }
}

const form = ref({
  provider: 'minimax',
  apiKey: '',
  baseUrl: 'https://api.minimaxi.com/anthropic',
  model: 'MiniMax-M2.7'
})

const saving = ref(false)
const error = ref('')
const success = ref('')

watch(() => form.value.provider, (val) => {
  const p = providers[val]
  if (p) {
    form.value.baseUrl = p.baseUrl
    form.value.model = p.model
  }
})

watch(() => props.visible, async (val) => {
  if (val) {
    error.value = ''
    success.value = ''
    await loadConfig()
  }
})

const loadConfig = async () => {
  try {
    const res = await axios.get('/api/config')
    const ai = res.data.ai || {}
    form.value.provider = ai.provider || 'minimax'
    form.value.baseUrl = ai.baseUrl || providers[form.value.provider].baseUrl
    form.value.model = ai.model || providers[form.value.provider].model
    form.value.apiKey = '' // 不回填 key
  } catch (e) {
    error.value = '加载配置失败'
  }
}

const save = async () => {
  if (!form.value.apiKey) {
    error.value = '请输入 API Key'
    return
  }
  saving.value = true
  error.value = ''
  success.value = ''
  try {
    await axios.post('/api/config/ai', null, {
      params: {
        provider: form.value.provider,
        api_key: form.value.apiKey,
        base_url: form.value.baseUrl,
        model: form.value.model
      }
    })
    success.value = '保存成功'
    emit('saved')
    setTimeout(() => close(), 1000)
  } catch (e) {
    error.value = '保存失败: ' + (e.message || e)
  } finally {
    saving.value = false
  }
}

const close = () => {
  emit('close')
}
</script>

<style scoped>
.settings-overlay {
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

.settings-modal {
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
  border-radius: 16px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  width: 90%;
  max-width: 480px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.modal-header h3 {
  margin: 0;
  font-size: 18px;
  color: #fff;
}

.close-btn {
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

.close-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
}

.close-btn svg {
  width: 18px;
  height: 18px;
}

.modal-body {
  padding: 24px;
}

.section-title {
  font-size: 12px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.4);
  text-transform: uppercase;
  letter-spacing: 1px;
  margin-bottom: 16px;
}

.form-group {
  margin-bottom: 16px;
}

.form-group label {
  display: block;
  font-size: 13px;
  color: rgba(255, 255, 255, 0.6);
  margin-bottom: 6px;
}

:deep(.el-input__wrapper),
:deep(.el-select .el-input__wrapper) {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 8px;
  box-shadow: none;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

:deep(.el-input__inner) {
  color: #fff;
}

:deep(.el-select-dropdown) {
  background: #1a1a2e;
  border-color: rgba(255, 255, 255, 0.1);
}

:deep(.el-select-dropdown__item) {
  color: rgba(255, 255, 255, 0.8);
}

:deep(.el-select-dropdown__item.selected) {
  color: #ff6600;
}

.error-msg {
  padding: 10px;
  background: rgba(255, 71, 87, 0.1);
  border: 1px solid rgba(255, 71, 87, 0.3);
  border-radius: 8px;
  color: #ff4757;
  font-size: 13px;
  margin-top: 12px;
}

.success-msg {
  padding: 10px;
  background: rgba(0, 255, 136, 0.1);
  border: 1px solid rgba(0, 255, 136, 0.3);
  border-radius: 8px;
  color: #00ff88;
  font-size: 13px;
  margin-top: 12px;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 24px;
  border-top: 1px solid rgba(255, 255, 255, 0.05);
}

:deep(.el-button) {
  border-radius: 8px;
}

:deep(.el-button--primary) {
  background: linear-gradient(135deg, #ff4757, #ff6b81);
  border: none;
}
</style>
