<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, watch, nextTick } from 'vue'
import * as echarts from 'echarts'

const props = defineProps<{
    options: echarts.EChartsOption
    loading: boolean
    modelValue: 'bar' | 'line' | 'pie' | 'doughnut'
}>()

const emit = defineEmits(['update:modelValue'])

const chart = ref<HTMLElement | null>(null)
let myChart: echarts.ECharts | null = null
const chartReady = ref(false)

const initChart = async () => {
    await nextTick()
    if (chart.value) {
        // 检查是否已经存在 ECharts 实例，如果存在则销毁它
        if (myChart) {
            console.log('Disposing existing ECharts instance')
            myChart.dispose();
        }
        console.log('Initializing chart with element:', chart.value)
        myChart = echarts.init(chart.value)
        console.log('ECharts instance created:', myChart)
        updateChartOptions()
        window.addEventListener('resize', resizeChart)
    } else {
        console.log('Chart element is not ready')
    }
}

const resizeChart = () => {
    if (myChart) {
        console.log('Resizing chart')
        myChart.resize()
    }
}

const updateChartOptions = () => {
    if (myChart) {
        console.log('Updating chart options with type:', props.modelValue)
        const updatedOptions = {
            ...props.options,
            series: (props.options.series as echarts.SeriesOption[])?.map((series: any) => ({
                ...series,
                type: props.modelValue === 'doughnut' ? 'pie' : props.modelValue,
                ...(props.modelValue === 'pie' || props.modelValue === 'doughnut' ? {
                    label: {
                        show: true,
                        position: 'outside',
                        formatter: '{b} {d}%', // 显示标签和百分比
                    },
                    labelLine: {
                        show: true
                    },
                    radius: props.modelValue === 'doughnut' ? ['40%', '70%'] : '50%', // 设置饼图和环形图的大小
                } : {}),
            })),
            ...(props.modelValue !== 'pie' && props.modelValue !== 'doughnut' ? {
                dataZoom: [
                    {
                        type: 'slider',
                        show: true,
                        xAxisIndex: [0],
                        start: 0,
                        end: 100,
                    },
                ],
                grid: {
                    left: '10%',
                    right: '10%',
                    bottom: '15%',
                    top: '15%',
                    containLabel: true,
                },
                xAxis: props.options.xAxis,
                yAxis: props.options.yAxis,
            } : {
                xAxis: undefined,
                yAxis: undefined,
                grid: undefined, // 移除 grid 配置
                dataZoom: undefined, // 移除 dataZoom 配置
            }),
        }
        console.log('Setting chart options:', updatedOptions)
        myChart.setOption(updatedOptions)
    } else {
        console.log('ECharts instance is not ready')
    }
}

const setChartType = (type: 'bar' | 'line' | 'pie' | 'doughnut') => {
    emit('update:modelValue', type)
    nextTick(() => {
        updateChartOptions() // 确保每次切换图表类型时都能正确更新图表配置
    })
}

onMounted(() => {
    console.log('Component mounted')
    chartReady.value = true
    initChart()
})

onBeforeUnmount(() => {
    if (myChart) {
        console.log('Disposing chart')
        myChart.dispose()
    }
    window.removeEventListener('resize', resizeChart)
})

watch(
    () => props.options,
    (newOptions) => {
        console.log('Options changed:', newOptions)
        if (myChart) {
            updateChartOptions()
        }
    },
    { deep: true }
)

watch(
    () => props.loading,
    (newLoading) => {
        console.log('Loading state changed:', newLoading)
        if (myChart) {
            if (newLoading) {
                myChart.showLoading()
            } else {
                myChart.hideLoading()
            }
        }
    }
)

watch(
    () => props.modelValue,
    (newType) => {
        console.log('Chart type changed:', newType)
        updateChartOptions()
    }
)
</script>

<template>
    <div class="chart-wrapper">
        <div class="chart-toolbar">
            <v-btn size="small" icon variant="text" @click="setChartType('line')" :class="{'active': props.modelValue === 'line'}">
                <v-icon>mdi-chart-line</v-icon>
            </v-btn>
            <v-btn size="small" icon variant="text" @click="setChartType('bar')" :class="{'active': props.modelValue === 'bar'}">
                <v-icon>mdi-chart-bar</v-icon>
            </v-btn>
            <v-btn size="small" icon variant="text" @click="setChartType('pie')" :class="{'active': props.modelValue === 'pie'}">
                <v-icon>mdi-chart-pie</v-icon>
            </v-btn>
            <v-btn size="small" icon variant="text" @click="setChartType('doughnut')" :class="{'active': props.modelValue === 'doughnut'}">
                <v-icon>mdi-chart-donut</v-icon>
            </v-btn>
        </div>
        <div v-if="chartReady" ref="chart" class="chart-element"></div>
    </div>
</template>

<style scoped>
.chart-wrapper {
    width: 100%;
    min-height: 450px;
    height: 450px;
    position: relative;
    display: flex;
    flex-direction: column;
}

.chart-toolbar {
    display: flex;
    justify-content: flex-end;
    align-items: center;
    gap: 4px;
    padding: 8px 0;
    z-index: 10;
}

.chart-element {
    flex: 1;
    width: 100%;
    min-height: 400px;
}

.v-btn.active {
    background-color: rgb(var(--v-theme-primary));
    color: white;
}
</style>