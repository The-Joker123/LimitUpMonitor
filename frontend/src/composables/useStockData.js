import { ref } from 'vue'

export function useStockData() {
  const stocks = ref([])
  const loading = ref(false)
  const currentTime = ref('')
  const emotionData = ref([])
  const shIndexData = ref([])
  const selectedDate = ref(new Date().toISOString().slice(0, 10).replace(/-/g, ''))
  const morningOnly = ref(false)
  let refreshTimer = null

  const fetchData = async () => {
    try {
      loading.value = true
      const url = `/api/limit-up?date=${selectedDate.value}&time_range=${morningOnly.value ? 'morning' : 'all'}`
      const response = await fetch(url)
      const data = await response.json()
      stocks.value = data.stocks
      currentTime.value = new Date().toLocaleTimeString('zh-CN')
    } catch (error) {
      console.error('获取涨停数据失败:', error)
    } finally {
      loading.value = false
    }
  }

  const fetchEmotionHistory = async (selectedIndustry) => {
    try {
      const industryParam = selectedIndustry ? `&industry=${encodeURIComponent(selectedIndustry)}` : ''
      const response = await fetch(`/api/emotion-history?days=20&time_range=${morningOnly.value ? 'morning' : 'all'}${industryParam}`)
      const result = await response.json()
      emotionData.value = result.data || []
    } catch (error) {
      console.error('获取情绪历史数据失败:', error)
    }
  }

  const fetchShIndex = async () => {
    try {
      const response = await fetch('/api/sh-index?days=20')
      const result = await response.json()
      shIndexData.value = result.data || []
    } catch (error) {
      console.error('获取上证指数数据失败:', error)
    }
  }

  const onMorningOnlyChange = () => {
    fetchData()
    fetchEmotionHistory()
  }

  const startAutoRefresh = () => {
    refreshTimer = setInterval(fetchData, 10000)
  }

  const stopAutoRefresh = () => {
    if (refreshTimer) clearInterval(refreshTimer)
  }

  return {
    stocks,
    loading,
    currentTime,
    emotionData,
    shIndexData,
    selectedDate,
    morningOnly,
    fetchData,
    fetchEmotionHistory,
    fetchShIndex,
    onMorningOnlyChange,
    startAutoRefresh,
    stopAutoRefresh,
  }
}
