<template>
    <div ref="chart" class="chart-container"></div>
  </template>
  
  <script setup lang="ts">
  import { ref, onMounted, nextTick } from 'vue'
  import * as echarts from 'echarts'
  
  const chart = ref<HTMLElement | null>(null)
  let myChart: echarts.ECharts | null = null
  
  onMounted(async () => {
    await nextTick() // 确保 DOM 已经更新
  
    if (chart.value) {
      myChart = echarts.init(chart.value)
      // 使用 mock 数据初始化图表
      const mockData = {
        x_axis: 'category',
        y_axes: ['value1', 'value2'],
        data: [
          { category: 'A', value1: 120, value2: 200 },
          { category: 'B', value1: 150, value2: 180 },
          { category: 'C', value1: 170, value2: 250 },
          { category: 'D', value1: 210, value2: 300 },
          { category: 'E', value1: 240, value2: 350 }
        ]
      }
  
      const xAxisData = mockData.data.map((item: Record<string, any>) => item[mockData.x_axis])
      const seriesData = mockData.y_axes.map(yAxis => {
        return {
          name: yAxis,
          type: 'bar',
          stack: 'Total',
          data: mockData.data.map((item: Record<string, any>) => item[yAxis])
        }
      })
  
      myChart.setOption({
        xAxis: {
          type: 'category',
          data: xAxisData,
        },
        yAxis: {
          type: 'value',
        },
        series: seriesData,
        legend: {
          data: mockData.y_axes
        },
        tooltip: {
          trigger: 'axis'
        }
      })
  
      window.addEventListener('resize', () => {
        if (myChart) {
          myChart.resize()
        }
      })
    }
  })
  </script>
  
  <style scoped>
  .chart-container {
    width: 100%;
    height: 400px;
  }
  </style>