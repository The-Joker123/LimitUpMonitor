<template>
  <div class="chart-section">
    <div class="chart-header">
      <span>📈 情绪指数</span>
    </div>
    <div ref="chartRef" class="chart-container"></div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  data: {
    type: Array,
    default: () => []
  }
})

const chartRef = ref(null)
let chartInstance = null

const initChart = () => {
  if (!chartRef.value) return
  
  chartInstance = echarts.init(chartRef.value)
  updateChart()
}

const updateChart = () => {
  if (!chartInstance || !props.data.length) return

  const dates = props.data.map(d => d.date)
  const lbCount = props.data.map(d => d.lbCount)
  const highCount = props.data.map(d => d.highCount)
  const maxBoard = props.data.map(d => d.maxBoard)
  const emotionScore = props.data.map(d => d.emotionScore)
  const ztCount = props.data.map(d => d.ztCount || 0)

  const option = {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(20, 20, 40, 0.95)',
      borderColor: 'rgba(255, 255, 255, 0.1)',
      textStyle: { color: '#e0e0e0' },
      formatter: (params) => {
        let result = `<div style="font-weight:bold;margin-bottom:8px;">${params[0].axisValue}</div>`
        params.forEach(p => {
          const colors = {
            '连板数': '#ff6b6b',
            '高标数': '#ffd93d',
            '最高板': '#6bcb77',
            '情绪指数': '#4ecdc4'
          }
          result += `<div style="display:flex;align-items:center;gap:8px;margin:4px 0;">
            <span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:${colors[p.seriesName] || '#fff'};"></span>
            <span>${p.seriesName}: <strong>${p.value}</strong></span>
          </div>`
        })
        return result
      }
    },
    legend: {
      data: ['连板数', '高标数', '最高板', '情绪指数', '涨停总数'],
      textStyle: { color: 'rgba(255,255,255,0.7)' },
      top: 10,
      itemGap: 20
    },
    grid: {
      left: 50,
      right: 30,
      top: 50,
      bottom: 80
    },
    xAxis: {
      type: 'category',
      data: dates,
      axisLine: { lineStyle: { color: 'rgba(255,255,255,0.1)' } },
      axisLabel: { color: 'rgba(255,255,255,0.5)' }
    },
    yAxis: [
      {
        type: 'value',
        name: '数量',
        axisLine: { show: false },
        axisLabel: { color: 'rgba(255,255,255,0.5)' },
        splitLine: { lineStyle: { color: 'rgba(255,255,255,0.05)' } }
      },
      {
        type: 'value',
        name: '指数',
        axisLine: { show: false },
        axisLabel: { color: 'rgba(255,255,255,0.5)' },
        splitLine: { show: false }
      }
    ],
    dataZoom: [
      { type: 'inside', start: 0, end: 100 },
      {
        type: 'slider',
        start: 0,
        end: 100,
        height: 25,
        bottom: 10,
        backgroundColor: 'rgba(255,255,255,0.05)',
        borderColor: 'rgba(255,255,255,0.1)',
        fillerColor: 'rgba(255,255,255,0.1)',
        handleStyle: { color: '#4ecdc4' },
        textStyle: { color: 'rgba(255,255,255,0.5)' }
      }
    ],
    series: [
      {
        name: '连板数',
        type: 'line',
        data: lbCount,
        smooth: true,
        lineStyle: { color: '#ff6b6b', width: 2 },
        itemStyle: { color: '#ff6b6b' },
        emphasis: { focus: 'series' }
      },
      {
        name: '高标数',
        type: 'line',
        data: highCount,
        smooth: true,
        lineStyle: { color: '#ffd93d', width: 2 },
        itemStyle: { color: '#ffd93d' },
        emphasis: { focus: 'series' }
      },
      {
        name: '最高板',
        type: 'line',
        data: maxBoard,
        smooth: true,
        lineStyle: { color: '#6bcb77', width: 2 },
        itemStyle: { color: '#6bcb77' },
        emphasis: { focus: 'series' }
      },
      {
        name: '情绪指数',
        type: 'line',
        yAxisIndex: 1,
        data: emotionScore,
        smooth: true,
        lineStyle: { color: '#4ecdc4', width: 3 },
        itemStyle: { color: '#4ecdc4' },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(78, 205, 196, 0.3)' },
            { offset: 1, color: 'rgba(78, 205, 196, 0.05)' }
          ])
        },
        emphasis: { focus: 'series' }
      },
      {
        name: '涨停总数',
        type: 'line',
        data: ztCount,
        smooth: true,
        lineStyle: { color: '#a855f7', width: 2 },
        itemStyle: { color: '#a855f7' },
        emphasis: { focus: 'series' }
      }
    ]
  }

  chartInstance.setOption(option)
}

const handleResize = () => {
  chartInstance?.resize()
}

watch(() => props.data, updateChart, { deep: true })

onMounted(() => {
  initChart()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  chartInstance?.dispose()
})
</script>

<style scoped>
.chart-section {
  background: rgba(255, 255, 255, 0.03);
  border-radius: 16px;
  border: 1px solid rgba(255, 255, 255, 0.06);
  padding: 16px;
  margin-top: 20px;
}

.chart-header {
  font-size: 16px;
  font-weight: 600;
  color: #fff;
  margin-bottom: 16px;
}

.chart-container {
  width: 100%;
  height: 350px;
}
</style>
