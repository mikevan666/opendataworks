const pendingRouteLoaders = new WeakMap()
let hasScheduledRouteWarmup = false

const getAsyncLoaders = (router, path) => {
  return router.resolve(path).matched.flatMap((record) => {
    const components = record.components ? Object.values(record.components) : [record.component]
    return components.filter((component) => typeof component === 'function')
  })
}

const preloadLoader = async (loader) => {
  if (pendingRouteLoaders.has(loader)) {
    return pendingRouteLoaders.get(loader)
  }

  const pending = Promise.resolve()
    .then(() => loader())
    .catch((error) => {
      pendingRouteLoaders.delete(loader)
      console.warn('[routeWarmup] failed to preload route chunk', error)
      return null
    })

  pendingRouteLoaders.set(loader, pending)
  return pending
}

export const preloadRouteComponents = async (router, path) => {
  const loaders = getAsyncLoaders(router, path)
  await Promise.all(loaders.map((loader) => preloadLoader(loader)))
}

export const scheduleRouteWarmup = (router, paths) => {
  if (hasScheduledRouteWarmup || typeof window === 'undefined') {
    return
  }

  const queue = [...new Set(paths)].filter(Boolean)
  if (!queue.length) {
    return
  }

  hasScheduledRouteWarmup = true

  const run = () => {
    void queue.reduce(
      (chain, path) => chain.then(() => preloadRouteComponents(router, path)),
      Promise.resolve()
    )
  }

  if (typeof window.requestIdleCallback === 'function') {
    window.requestIdleCallback(run, { timeout: 1500 })
    return
  }

  window.setTimeout(run, 300)
}
