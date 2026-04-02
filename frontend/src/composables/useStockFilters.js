import { ref, computed } from 'vue'

export function useStockFilters(stocksRef) {
  const selectedIndustry = ref('')
  const sortField = ref('pct_chg')
  const sortOrder = ref('desc')
  const showCandidatesOnly = ref(false)

  const boardData = computed(() => {
    const stocks = stocksRef.value
    const data = { all: {} }
    const maxDays = Math.max(...stocks.map(s => s.limit_up_days), 0)
    for (let i = 1; i <= maxDays; i++) {
      data[i] = {}
    }
    stocks.forEach(s => {
      const industry = s.industry
      data.all[industry] = (data.all[industry] || 0) + 1
      const days = s.limit_up_days
      if (data[days]) {
        data[days][industry] = (data[days][industry] || 0) + 1
      }
    })

    for (const key in data) {
      const entries = Object.entries(data[key])
        .map(([industry, count]) => ({ industry, count }))
        .sort((a, b) => b.count - a.count)
      data[key] = entries
    }
    return data
  })

  const boardTabs = computed(() => {
    const tabs = [{ key: 'all', label: '全部' }]
    const keys = Object.keys(boardData.value).filter(k => k !== 'all').map(Number).sort((a, b) => a - b)
    for (const key of keys) {
      if (boardData.value[key] && boardData.value[key].length > 0) {
        tabs.push({ key: String(key), label: `${key}板` })
      }
    }
    return tabs
  })

  const industryCountMap = computed(() => {
    const map = {}
    boardData.value.all?.forEach(item => {
      map[item.industry] = item.count
    })
    return map
  })

  // 计算封单/成交比率
  const stocksWithRatio = computed(() => {
    return stocksRef.value.map(s => ({
      ...s,
      seal_ratio: s.amount && s.seal_fund ? s.seal_fund / s.amount : 0
    }))
  })

  // 首板候选股筛选
  const candidateStocks = computed(() => {
    return stocksWithRatio.value.filter(stock => {
      if (stock.limit_up_days !== 1) return false
      if (!stock.first_seal_time || stock.first_seal_time > '1000') return false
      if (stock.turnover_rate < 5 || stock.turnover_rate > 15) return false
      if (stock.flow_market_cap < 30 || stock.flow_market_cap > 150) return false
      const industryCount = industryCountMap.value[stock.industry] || 0
      if (industryCount < 2) return false
      return true
    })
  })

  const filteredStocks = computed(() => {
    let result = showCandidatesOnly.value ? candidateStocks.value : stocksWithRatio.value
    if (selectedIndustry.value) {
      result = result.filter(s => s.industry === selectedIndustry.value)
    }
    result = [...result].sort((a, b) => {
      const aVal = a[sortField.value]
      const bVal = b[sortField.value]
      if (typeof aVal === 'string') {
        return sortOrder.value === 'asc'
          ? aVal.localeCompare(bVal)
          : bVal.localeCompare(aVal)
      }
      return sortOrder.value === 'asc' ? aVal - bVal : bVal - aVal
    })
    return result
  })

  const sortBy = (field) => {
    if (sortField.value === field) {
      sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc'
    } else {
      sortField.value = field
      sortOrder.value = 'desc'
    }
  }

  const toggleIndustry = (industry) => {
    if (selectedIndustry.value === industry) {
      selectedIndustry.value = ''
    } else {
      selectedIndustry.value = industry
    }
  }

  return {
    selectedIndustry,
    sortField,
    sortOrder,
    showCandidatesOnly,
    boardData,
    boardTabs,
    industryCountMap,
    stocksWithRatio,
    candidateStocks,
    filteredStocks,
    sortBy,
    toggleIndustry,
  }
}
