import axios from 'axios';
import { API_BASE_URL } from '@/config';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const getTrades = () => apiClient.get('/api/trades/');
export const getPerformanceSummary = (startDate?: string, endDate?: string) => 
  apiClient.get('/api/performance/summary', { params: { start_date: startDate, end_date: endDate } });
export const getSettings = () => apiClient.get('/api/settings/');
export const updateSetting = (key: string, value: string) => 
  apiClient.post('/api/settings/update', { key, value });

export const getSystemStatus = () => apiClient.get('/api/system/status');

export default apiClient;
