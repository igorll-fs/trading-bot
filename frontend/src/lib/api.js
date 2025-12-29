import axios from 'axios';

const sanitizeUrl = (url) => (typeof url === 'string' ? url.trim().replace(/\/+$/, '') : '');

const envBackendUrl = sanitizeUrl(
  typeof process !== 'undefined' ? process.env?.REACT_APP_BACKEND_URL : ''
);

// Função que retorna a URL do backend dinamicamente
const getBackendUrl = () => {
  if (typeof window === 'undefined') {
    return envBackendUrl || 'http://127.0.0.1:8000';
  }

  try {
    const { protocol, hostname, port } = window.location;
    
    // Se estamos em botrading.uk (domínio personalizado)
    if (hostname === 'botrading.uk' || hostname.endsWith('.botrading.uk')) {
      return 'https://api.botrading.uk';
    }
    
    // Se estamos em trycloudflare.com (túnel remoto temporário)
    if (hostname.includes('trycloudflare.com')) {
      // Tentar buscar URL do backend do localStorage
      const storedBackendUrl = localStorage.getItem('remote_backend_url');
      if (storedBackendUrl) {
        return sanitizeUrl(storedBackendUrl);
      }
      
      // Se não tem no localStorage, retornar null para indicar que precisa configurar
      return null;
    }
    
    // Se tem URL de ambiente, usar ela
    if (envBackendUrl) {
      return envBackendUrl;
    }
    
    // Acesso local - inferir porta
    if (!port) {
      return sanitizeUrl(`${protocol}//${hostname}:8000`);
    }

    if (['3000', '3001', '3300', '5173', '8080'].includes(port)) {
      return sanitizeUrl(`${protocol}//${hostname}:8000`);
    }

    return sanitizeUrl(`${protocol}//${hostname}:${port}`);
  } catch (error) {
    console.warn('[api] Failed to infer backend URL:', error);
    return 'http://127.0.0.1:8000';
  }
};

// Função exportada para obter a URL (reavalia a cada chamada)
export const getBackendBaseUrl = () => getBackendUrl() || '';

// Criar cliente axios com interceptor para URL dinâmica
export const apiClient = axios.create({
  timeout: 15000,
  headers: {
    Accept: 'application/json',
  },
});

// Interceptor para definir baseURL dinamicamente em cada request
apiClient.interceptors.request.use((config) => {
  const baseUrl = getBackendUrl();
  if (baseUrl) {
    config.baseURL = `${baseUrl}/api`;
  } else {
    // Se não tem URL configurada, usar localhost como fallback
    config.baseURL = 'http://127.0.0.1:8000/api';
  }
  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (!error.response) {
      error.isNetworkError = true;
    }
    return Promise.reject(error);
  }
);
