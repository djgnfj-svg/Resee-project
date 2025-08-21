// Monitoring and Alert System Types

export interface SystemHealth {
  cpu_usage_percent: number;
  memory_usage_percent: number;
  disk_usage_percent: number;
  db_connection_count: number;
  db_query_avg_time_ms: number;
  cache_hit_rate_percent: number;
  cache_memory_usage_mb: number;
  celery_workers_active: number;
  redis_status: boolean;
  postgres_status: boolean;
  api_requests_per_minute: number;
  api_error_rate_percent: number;
  api_avg_response_time_ms: number;
  timestamp: string;
  date: string;
}

export interface APIMetric {
  id: number;
  endpoint: string;
  method: string;
  response_time_ms: number;
  status_code: number;
  query_count: number;
  timestamp: string;
  user?: string;
}

export interface ErrorLog {
  id: number;
  level: 'ERROR' | 'CRITICAL' | 'WARNING';
  message: string;
  exception_type: string;
  endpoint?: string;
  timestamp: string;
  resolved: boolean;
  occurrences: number;
}

export interface UserActivity {
  user: string;
  date: string;
  api_requests_count: number;
  content_created_count: number;
  reviews_completed_count: number;
  session_duration_minutes: number;
}

export interface AIMetric {
  user: string;
  operation_type: 'question_generation' | 'answer_evaluation' | 'content_analysis' | 'chat';
  tokens_used: number;
  cost_usd: string;
  processing_time_ms: number;
  success: boolean;
  timestamp: string;
}

// Alert System Types
export interface AlertRule {
  id: number;
  name: string;
  description: string;
  alert_type: 'system_error' | 'performance' | 'security' | 'business' | 'database' | 'ai_usage';
  alert_type_display: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  severity_display: string;
  metric_name: string;
  metric_name_display: string;
  condition: 'gt' | 'gte' | 'lt' | 'lte' | 'eq' | 'ne';
  condition_display: string;
  condition_display_verbose: string;
  threshold_value: number;
  time_window_minutes: number;
  slack_enabled: boolean;
  slack_channel: string;
  email_enabled: boolean;
  email_recipients: string[];
  cooldown_minutes: number;
  max_alerts_per_hour: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  created_by?: string;
  is_in_cooldown: boolean;
  recent_alert_count: number;
}

export interface AlertHistory {
  id: number;
  rule: number;
  rule_name: string;
  rule_severity: 'low' | 'medium' | 'high' | 'critical';
  rule_severity_display: string;
  rule_alert_type: string;
  rule_metric_name: string;
  triggered_at: string;
  metric_value: number;
  message: string;
  slack_sent: boolean;
  email_sent: boolean;
  resolved_at?: string;
  resolved_by_email?: string;
  resolution_notes?: string;
  is_resolved: boolean;
  notification_success: boolean;
}

export interface AlertStatistics {
  total_rules: number;
  active_rules: number;
  inactive_rules: number;
  total_alerts_24h: number;
  total_alerts_week: number;
  total_alerts_month: number;
  critical_alerts_24h: number;
  high_alerts_24h: number;
  medium_alerts_24h: number;
  low_alerts_24h: number;
  unresolved_alerts: number;
  resolved_alerts_24h: number;
  notification_success_rate_24h: number;
  most_triggered_rule: string;
  most_triggered_metric: string;
  alerts_by_hour: Array<{
    hour: string;
    count: number;
  }>;
  alerts_by_severity: Record<string, number>;
  alerts_by_type: Record<string, number>;
}

// Dashboard Overview Types
export interface DashboardOverview {
  timeframe: string;
  timestamp: string;
  api_metrics: {
    total_requests: number;
    avg_response_time_ms: number;
    error_rate_percent: number;
    slow_requests: number;
  };
  user_activity: {
    active_users_today: number;
    total_api_requests: number;
    total_content_created: number;
    total_reviews_completed: number;
  };
  ai_usage: {
    total_operations: number;
    total_tokens_used: number;
    total_cost_usd: number;
    success_rate_percent: number;
    avg_processing_time_ms: number;
  };
  errors: {
    total_errors: number;
    critical_errors: number;
    unresolved_errors: number;
    error_rate_percent: number;
  };
  system_health?: SystemHealth;
}

// Chart Data Types
export interface ChartDataPoint {
  timestamp: string;
  value: number;
  label?: string;
}

export interface MetricTrend {
  metric_name: string;
  data_points: ChartDataPoint[];
  current_value: number;
  trend_direction: 'up' | 'down' | 'stable';
  change_percent: number;
}

// Component Props Types
export interface SystemStatusCardProps {
  title: string;
  value: number | string;
  unit?: string;
  status: 'healthy' | 'warning' | 'critical';
  trend?: 'up' | 'down' | 'stable';
  loading?: boolean;
  onClick?: () => void;
}

export interface PerformanceChartProps {
  data: ChartDataPoint[];
  type?: 'line' | 'area' | 'bar';
  height?: number;
  showLegend?: boolean;
  timeRange: '1h' | '24h' | '7d' | '30d';
  title: string;
  loading?: boolean;
}

export interface ErrorLogTableProps {
  logs: ErrorLog[];
  onResolve: (id: number) => void;
  onViewDetails: (log: ErrorLog) => void;
  loading?: boolean;
}

// API Response Types
export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

// Filter and Query Types
export interface MonitoringFilters {
  timeRange: '1h' | '24h' | '7d' | '30d';
  severity?: 'low' | 'medium' | 'high' | 'critical';
  status?: 'resolved' | 'unresolved';
  alertType?: string;
}

// Test and Management Types
export interface TestNotificationRequest {
  notification_type: 'slack' | 'email' | 'both';
  custom_channel?: string;
  custom_recipients?: string[];
}

export interface ManualTriggerRequest {
  rule_ids?: number[];
  force?: boolean;
}