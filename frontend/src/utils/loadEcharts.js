let echartsPromise = null

export const loadEcharts = async () => {
  if (!echartsPromise) {
    echartsPromise = import('./echartsBundle').then((module) => module.echarts)
  }
  return echartsPromise
}
