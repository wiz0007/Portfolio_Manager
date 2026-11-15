export class ApiClientError extends Error {
  status: number;
  data: any;

  constructor(message: string, status: number, data?: any) {
    super(message);
    this.name = 'ApiClientError';
    this.status = status;
    this.data = data;
  }
}

function getCookie(name: string): string | null {
  const match = document.cookie.match(new RegExp('(^|;\\s*)(' + name + ')=([^;]*)'));
  return match ? decodeURIComponent(match[3]) : null;
}

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

async function ensureCsrfToken(): Promise<string | null> {
  let token = getCookie('csrftoken');
  if (!token) {
    try {
      const res = await fetch(`${BASE_URL}/auth/csrf/`, {
        credentials: 'include',
      });
      if (res.ok) {
        const json = await res.json();
        token = json.csrfToken || getCookie('csrftoken');
      }
    } catch {
      // Ignore network errors here; fallback to empty token
    }
  }
  return token;
}

async function request<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${BASE_URL}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;

  const headers = new Headers(options.headers || {});
  if (!headers.has('Content-Type') && !(options.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json');
  }

  const method = (options.method || 'GET').toUpperCase();
  if (['POST', 'PUT', 'PATCH', 'DELETE'].includes(method)) {
    const csrfToken = await ensureCsrfToken();
    if (csrfToken) {
      headers.set('X-CSRFToken', csrfToken);
    }
  }

  const response = await fetch(url, {
    ...options,
    headers,
    credentials: 'include',
  });

  const contentType = response.headers.get('content-type') || '';
  const isJson = contentType.includes('application/json');
  const data = isJson ? await response.json() : await response.text();

  if (!response.ok) {
    let errorMessage = `Server error (${response.status})`;
    if (data && typeof data === 'object') {
      if (data.detail) {
        errorMessage = Array.isArray(data.detail) ? data.detail.join(' ') : String(data.detail);
      } else if (data.message) {
        errorMessage = String(data.message);
      } else if (data.error) {
        errorMessage = String(data.error);
      } else {
        const entries = Object.entries(data);
        if (entries.length > 0) {
          const [key, val] = entries[0];
          if (Array.isArray(val)) {
            errorMessage = `${key}: ${val.join(', ')}`;
          } else if (typeof val === 'object' && val !== null) {
            const subEntries = Object.entries(val);
            if (subEntries.length > 0) {
              const [subKey, subVal] = subEntries[0];
              errorMessage = `${key}.${subKey}: ${Array.isArray(subVal) ? subVal.join(', ') : subVal}`;
            } else {
              errorMessage = `${key}: Invalid value`;
            }
          } else {
            errorMessage = `${key}: ${val}`;
          }
        }
      }
    } else if (typeof data === 'string' && data.trim()) {
      if (data.includes('<html') || data.includes('<!DOCTYPE')) {
        errorMessage = `Internal Server Error (${response.status}). Check backend server logs.`;
      } else {
        errorMessage = data.slice(0, 300);
      }
    }
    throw new ApiClientError(errorMessage, response.status, data);
  }

  return data as T;
}

export const apiClient = {
  get: <T>(endpoint: string, options?: RequestInit) =>
    request<T>(endpoint, { ...options, method: 'GET' }),
  post: <T>(endpoint: string, body?: unknown, options?: RequestInit) =>
    request<T>(endpoint, {
      ...options,
      method: 'POST',
      body: body ? JSON.stringify(body) : undefined,
    }),
  put: <T>(endpoint: string, body?: unknown, options?: RequestInit) =>
    request<T>(endpoint, {
      ...options,
      method: 'PUT',
      body: body ? JSON.stringify(body) : undefined,
    }),
  patch: <T>(endpoint: string, body?: unknown, options?: RequestInit) =>
    request<T>(endpoint, {
      ...options,
      method: 'PATCH',
      body: body ? JSON.stringify(body) : undefined,
    }),
  delete: <T>(endpoint: string, options?: RequestInit) =>
    request<T>(endpoint, { ...options, method: 'DELETE' }),
};

