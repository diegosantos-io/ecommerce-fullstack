const API_URL = 'http://127.0.0.1:8000'

export async function apiRequest(endpoint, options = {}) {
  const token = sessionStorage.getItem('access_token')

  const response = await fetch(`${API_URL}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers,
    },
  })

  if (response.status === 204) {
    if (!response.ok) {
      throw new Error('Não foi possível concluir a solicitação.')
    }
    return null
  }

  const data = await response.json().catch(() => null)

  if (!response.ok) {
    const detail = data?.detail
    const message = Array.isArray(detail)
      ? detail.map((item) => item.msg).join(', ')
      : detail || 'Não foi possível concluir a solicitação.'

    throw new Error(message)
  }

  return data
}
