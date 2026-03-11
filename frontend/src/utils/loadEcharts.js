let echartsPromise = null

export const loadEcharts = async () => {
  if (!echartsPromise) {
    echartsPromise = import('echarts')
  }
  return echartsPromise
}
