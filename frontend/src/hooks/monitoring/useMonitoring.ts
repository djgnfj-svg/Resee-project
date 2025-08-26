import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../../utils/api';
import type {
  DashboardOverview,
  SystemHealth,
  APIMetric,
  ErrorLog,
  AlertRule,
  AlertHistory,
  AlertStatistics,
  PaginatedResponse,
  TestNotificationRequest,
  ManualTriggerRequest,
  MonitoringFilters
} from '../../types/monitoring';

// Dashboard Overview
export const useDashboardOverview = () => {
  return useQuery({
    queryKey: ['monitoring', 'dashboard'],
    queryFn: async (): Promise<DashboardOverview> => {
      const { data } = await api.get('/monitoring/dashboard/');
      return data;
    },
    refetchInterval: 30000, // Refetch every 30 seconds
  });
};

// System Health
export const useSystemHealth = () => {
  return useQuery({
    queryKey: ['monitoring', 'system-health'],
    queryFn: async (): Promise<SystemHealth[]> => {
      const { data } = await api.get('/monitoring/system-health/');
      return data.results || data;
    },
    refetchInterval: 30000,
  });
};

// API Metrics
export const useAPIMetrics = (filters?: { timeframe?: string; endpoint?: string }) => {
  return useQuery({
    queryKey: ['monitoring', 'api-metrics', filters],
    queryFn: async (): Promise<PaginatedResponse<APIMetric>> => {
      const params = new URLSearchParams();
      if (filters?.timeframe) params.append('timeframe', filters.timeframe);
      if (filters?.endpoint) params.append('endpoint', filters.endpoint);
      
      const { data } = await api.get(`/monitoring/api-metrics/?${params.toString()}`);
      return data;
    },
    refetchInterval: 60000, // Refetch every minute
  });
};

// Error Logs
export const useErrorLogs = (filters?: { level?: string; hours?: number }) => {
  return useQuery({
    queryKey: ['monitoring', 'error-logs', filters],
    queryFn: async (): Promise<PaginatedResponse<ErrorLog>> => {
      const params = new URLSearchParams();
      if (filters?.level) params.append('level', filters.level);
      if (filters?.hours) params.append('hours', filters.hours.toString());
      
      const { data } = await api.get(`/monitoring/error-logs/?${params.toString()}`);
      return data;
    },
    refetchInterval: 60000,
  });
};

// Alert Rules
export const useAlertRules = (filters?: {
  is_active?: boolean;
  alert_type?: string;
  severity?: string;
  search?: string;
}) => {
  return useQuery({
    queryKey: ['alerts', 'rules', filters],
    queryFn: async (): Promise<PaginatedResponse<AlertRule>> => {
      const params = new URLSearchParams();
      if (filters?.is_active !== undefined) params.append('is_active', filters.is_active.toString());
      if (filters?.alert_type) params.append('alert_type', filters.alert_type);
      if (filters?.severity) params.append('severity', filters.severity);
      if (filters?.search) params.append('search', filters.search);
      
      const { data } = await api.get(`/alerts/rules/?${params.toString()}`);
      return data;
    },
  });
};

// Alert History
export const useAlertHistory = (filters?: {
  rule?: number;
  severity?: string;
  resolved?: boolean;
  hours?: number;
}) => {
  return useQuery({
    queryKey: ['alerts', 'history', filters],
    queryFn: async (): Promise<PaginatedResponse<AlertHistory>> => {
      const params = new URLSearchParams();
      if (filters?.rule) params.append('rule', filters.rule.toString());
      if (filters?.severity) params.append('severity', filters.severity);
      if (filters?.resolved !== undefined) params.append('resolved', filters.resolved.toString());
      if (filters?.hours) params.append('hours', filters.hours.toString());
      
      const { data } = await api.get(`/alerts/history/?${params.toString()}`);
      return data;
    },
    refetchInterval: 60000,
  });
};

// Alert Statistics
export const useAlertStatistics = () => {
  return useQuery({
    queryKey: ['alerts', 'statistics'],
    queryFn: async (): Promise<AlertStatistics> => {
      const { data } = await api.get('/alerts/stats/');
      return data;
    },
    refetchInterval: 300000, // Refetch every 5 minutes
  });
};

// Mutations for Alert Management

// Create Alert Rule
export const useCreateAlertRule = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (ruleData: Partial<AlertRule>) => {
      const { data } = await api.post('/alerts/rules/', ruleData);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alerts', 'rules'] });
      queryClient.invalidateQueries({ queryKey: ['alerts', 'statistics'] });
    },
  });
};

// Update Alert Rule
export const useUpdateAlertRule = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async ({ id, ...ruleData }: Partial<AlertRule> & { id: number }) => {
      const { data } = await api.put(`/alerts/rules/${id}/`, ruleData);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alerts', 'rules'] });
      queryClient.invalidateQueries({ queryKey: ['alerts', 'statistics'] });
    },
  });
};

// Delete Alert Rule
export const useDeleteAlertRule = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (id: number) => {
      await api.delete(`/alerts/rules/${id}/`);
      return id;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alerts', 'rules'] });
      queryClient.invalidateQueries({ queryKey: ['alerts', 'statistics'] });
    },
  });
};

// Resolve Alert
export const useResolveAlert = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async ({ id, resolution_notes }: { id: number; resolution_notes?: string }) => {
      const { data } = await api.post(`/alerts/history/${id}/resolve/`, {
        resolution_notes: resolution_notes || ''
      });
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alerts', 'history'] });
      queryClient.invalidateQueries({ queryKey: ['alerts', 'statistics'] });
    },
  });
};

// Test Notifications
export const useTestSlackNotification = () => {
  return useMutation({
    mutationFn: async (data: TestNotificationRequest) => {
      const { data: response } = await api.post('/alerts/test/slack/', data);
      return response;
    },
  });
};

export const useTestEmailNotification = () => {
  return useMutation({
    mutationFn: async (data: TestNotificationRequest) => {
      const { data: response } = await api.post('/alerts/test/email/', data);
      return response;
    },
  });
};

// Manual Trigger
export const useManualTrigger = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (data: ManualTriggerRequest) => {
      const { data: response } = await api.post('/alerts/trigger/', data);
      return response;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alerts', 'history'] });
      queryClient.invalidateQueries({ queryKey: ['alerts', 'statistics'] });
    },
  });
};

// Real-time data hook with automatic invalidation
export const useRealTimeMonitoring = () => {
  const queryClient = useQueryClient();
  
  // Invalidate queries every 30 seconds for real-time feel
  const invalidateQueries = () => {
    queryClient.invalidateQueries({ queryKey: ['monitoring', 'dashboard'] });
    queryClient.invalidateQueries({ queryKey: ['monitoring', 'system-health'] });
    queryClient.invalidateQueries({ queryKey: ['alerts', 'history'] });
  };
  
  return { invalidateQueries };
};