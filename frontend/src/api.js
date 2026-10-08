let csrfToken = '';
export async function api(path, options = {}) {
  const method = options.method || 'GET';
  const isForm = options.body instanceof FormData;
  if (!['GET', 'HEAD'].includes(method) && !csrfToken) {
    const response = await fetch('/api/auth/csrf', { credentials: 'include' });
    const data = await response.json();
    csrfToken = data.csrfToken;
  }
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 180000);
  try {
    const response = await fetch('/api' + path, {
      ...options, method, credentials: 'include', signal: options.signal || controller.signal,
      headers: { ...(!isForm && options.body ? { 'Content-Type': 'application/json' } : {}),
        ...(!['GET', 'HEAD'].includes(method) ? { 'X-CSRFToken': csrfToken } : {}), ...options.headers },
      body: isForm ? options.body : options.body ? JSON.stringify(options.body) : undefined,
    });
    if (options.blob && response.ok) return response.blob();
    const data = await response.json().catch(() => ({ error: 'The server returned an unexpected response. Please try again.' }));
    if (!response.ok) {
      const error = new Error(data.details?.length ? `${data.error} ${data.details.join(' ')}` : data.error || 'Request failed.');
      error.status = response.status;
      if (response.status === 403) csrfToken = '';
      throw error;
    }
    if (data.csrfToken) csrfToken = data.csrfToken;
    return data;
  } catch (error) {
    if (error.name === 'AbortError') throw new Error('The request took too long. Refresh to check whether it completed.');
    if (error instanceof TypeError) throw new Error('Cannot reach the server. Check your connection and try again.');
    throw error;
  } finally { clearTimeout(timeout); }
}

export function download(blob, name) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url; a.download = name; a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
