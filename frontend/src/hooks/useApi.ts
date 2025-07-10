import axios, { AxiosRequestConfig } from 'axios';
import { useCallback } from 'react';

const BASE_URL = "http://localhost:8000";

export const useApi = () => {
  const getToken = () => localStorage.getItem('token');

  const request = useCallback(async (config: AxiosRequestConfig) => {
    try {
      const response = await axios({
        ...config,
        baseURL: BASE_URL,
        headers: {
          Authorization: `Bearer ${getToken()}`,
          'Content-Type': 'application/json',
          ...config.headers,
        }
      });
      return response.data;
    } catch (error: any) {
      if (error.response) {
        throw new Error(error.response.data.detail || 'Request error');
      } else {
        throw new Error('Network error');
      }
    }
  }, []);

  return {
    get: (endpoint: string) => request({ method: 'GET', url: endpoint }),
    post: (endpoint: string, data: any) => request({ method: 'POST', url: endpoint, data }),
    put: (endpoint: string, data: any) => request({ method: 'PUT', url: endpoint, data }),
    delete: (endpoint: string) => request({ method: 'DELETE', url: endpoint })
  };
};