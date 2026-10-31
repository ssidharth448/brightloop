import { useCallback, useEffect, useState } from 'react'

interface FetchState<T> {
  data: T | null
  error: string | null
  loading: boolean
}

/**
 * Loads data and tracks loading / error state.
 * `fetcher` must be a stable reference: use `api.products.list` directly,
 * or wrap parameterised calls in useCallback.
 *
 *   const { data, loading, error, reload } = useFetch(api.products.list)
 */
export function useFetch<T>(fetcher: () => Promise<T>) {
  const [state, setState] = useState<FetchState<T>>({ data: null, error: null, loading: true })
  const [tick, setTick] = useState(0)

  useEffect(() => {
    let cancelled = false
    fetcher()
      .then((data) => {
        if (!cancelled) setState({ data, error: null, loading: false })
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setState({ data: null, error: err instanceof Error ? err.message : 'Something went wrong.', loading: false })
        }
      })
    return () => {
      cancelled = true
    }
  }, [fetcher, tick])

  const reload = useCallback(() => {
    setState((s) => ({ ...s, loading: true, error: null }))
    setTick((t) => t + 1)
  }, [])

  return { ...state, reload }
}
