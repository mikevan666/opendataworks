<template>
  <div class="oda-card flex h-full min-h-[280px] flex-col p-6">
    <div class="mb-4 flex items-start justify-between gap-4">
      <div>
        <div class="oda-kicker">{{ eyebrow }}</div>
        <div class="mt-2 text-base font-semibold text-gray-900">{{ title }}</div>
        <p v-if="description" class="mt-2 text-sm leading-relaxed text-gray-600">
          {{ description }}
        </p>
      </div>
      <div v-if="badge" class="oda-chip-neutral">{{ badge }}</div>
    </div>
    <div ref="chartRef" class="min-h-[180px] flex-1" />
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import * as echarts from 'echarts/core'
import { LineChart, BarChart } from 'echarts/charts'
import { GridComponent, TooltipComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'

echarts.use([LineChart, BarChart, GridComponent, TooltipComponent, CanvasRenderer])

const props = defineProps({
  eyebrow: {
    type: String,
    default: 'Operational Trend'
  },
  title: {
    type: String,
    required: true
  },
  description: {
    type: String,
    default: ''
  },
  badge: {
    type: String,
    default: ''
  },
  data: {
    type: Array,
    default: () => []
  },
  xKey: {
    type: String,
    default: 'label'
  },
  yKey: {
    type: String,
    default: 'value'
  },
  type: {
    type: String,
    default: 'line'
  },
  color: {
    type: String,
    default: '#2563eb'
  },
  area: {
    type: Boolean,
    default: true
  },
  valueFormatter: {
    type: Function,
    default: null
  }
})

const chartRef = ref(null)
let chart
let resizeObserver

const normalizedData = computed(() => Array.isArray(props.data) ? props.data : [])

const formatValue = (value) => {
  if (typeof props.valueFormatter === 'function') {
    return props.valueFormatter(value)
  }
  return value
}

const buildOption = () => ({
  animationDuration: 220,
  animationEasing: 'cubicOut',
  grid: {
    left: 8,
    right: 8,
    top: 12,
    bottom: 4,
    containLabel: true
  },
  tooltip: {
    trigger: 'axis',
    borderWidth: 0,
    backgroundColor: '#1d4ed8',
    textStyle: {
      color: '#f9fafb',
      fontSize: 12
    },
    formatter(params) {
      const first = Array.isArray(params) ? params[0] : params
      if (!first) return ''
      return `${first.axisValue}<br/>${formatValue(first.value)}`
    }
  },
  xAxis: {
    type: 'category',
    boundaryGap: props.type === 'bar',
    axisLine: {
      lineStyle: {
        color: '#e5e7eb'
      }
    },
    axisTick: {
      show: false
    },
    axisLabel: {
      color: '#6b7280',
      fontSize: 11
    },
    data: normalizedData.value.map((item) => item?.[props.xKey] ?? '')
  },
  yAxis: {
    type: 'value',
    splitNumber: 4,
    axisLine: {
      show: false
    },
    axisTick: {
      show: false
    },
    axisLabel: {
      color: '#6b7280',
      fontSize: 11,
      formatter: (value) => formatValue(value)
    },
    splitLine: {
      lineStyle: {
        color: '#f3f4f6'
      }
    }
  },
  series: [
    {
      type: props.type,
      smooth: props.type === 'line',
      symbol: props.type === 'line' ? 'circle' : undefined,
      symbolSize: props.type === 'line' ? 6 : undefined,
      itemStyle: {
        color: props.color
      },
      lineStyle: {
        color: props.color,
        width: 2
      },
      areaStyle: props.type === 'line' && props.area
        ? {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: `${props.color}33` },
              { offset: 1, color: `${props.color}08` }
            ])
          }
        : undefined,
      barWidth: props.type === 'bar' ? 18 : undefined,
      data: normalizedData.value.map((item) => item?.[props.yKey] ?? 0)
    }
  ]
})

const renderChart = () => {
  if (!chartRef.value) return
  if (!chart) {
    chart = echarts.init(chartRef.value)
  }
  chart.setOption(buildOption(), true)
  chart.resize()
}

onMounted(() => {
  renderChart()
  if (chartRef.value && typeof ResizeObserver !== 'undefined') {
    resizeObserver = new ResizeObserver(() => {
      chart?.resize()
    })
    resizeObserver.observe(chartRef.value)
  }
})

watch(() => [props.type, props.color, props.xKey, props.yKey, normalizedData.value], () => {
  renderChart()
}, { deep: true })

onBeforeUnmount(() => {
  resizeObserver?.disconnect()
  if (chart) {
    chart.dispose()
    chart = null
  }
})
</script>
