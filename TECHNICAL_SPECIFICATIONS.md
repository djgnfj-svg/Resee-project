# 🔧 Resee 기술 명세서

> **작성일**: 2025-01-21  
> **버전**: v1.0  
> **대상**: 개발팀, PM

---

## 📋 문서 개요

이 문서는 Resee 프로젝트의 추가 개발이 필요한 기능들에 대한 상세 기술 명세를 제공합니다.

---

## 🖥️ 1. 모니터링 대시보드 프론트엔드

### 1.1 기술 스택
```typescript
// Frontend Stack
- React 18.2.0
- TypeScript 4.9.3
- TailwindCSS 3.2.4
- Recharts 2.15.4 (차트 라이브러리)
- TanStack Query 4.16.1 (서버 상태 관리)
- React Hook Form 7.39.4 (폼 관리)
```

### 1.2 아키텍처 설계
```
frontend/src/
├── pages/
│   └── admin/
│       ├── MonitoringDashboard.tsx      # 메인 대시보드 페이지
│       ├── SystemHealth.tsx             # 시스템 상태 페이지
│       ├── APIMetrics.tsx               # API 성능 페이지
│       ├── UserAnalytics.tsx            # 사용자 분석 페이지
│       └── ErrorLogs.tsx                # 에러 로그 페이지
├── components/
│   └── monitoring/
│       ├── SystemStatusCard.tsx         # 시스템 상태 카드
│       ├── PerformanceChart.tsx         # 성능 차트
│       ├── ErrorLogTable.tsx            # 에러 로그 테이블
│       ├── UserActivityChart.tsx        # 사용자 활동 차트
│       ├── AIUsageChart.tsx             # AI 사용량 차트
│       └── AlertPanel.tsx               # 알림 패널
├── hooks/
│   └── monitoring/
│       ├── useSystemHealth.ts           # 시스템 상태 훅
│       ├── useAPIMetrics.ts             # API 메트릭 훅
│       ├── useErrorLogs.ts              # 에러 로그 훅
│       └── useUserActivity.ts           # 사용자 활동 훅
└── types/
    └── monitoring.ts                    # 모니터링 타입 정의
```

### 1.3 API 연동 명세
```typescript
// 기존 백엔드 API 엔드포인트 활용
interface MonitoringAPIs {
  // 시스템 상태
  '/api/monitoring/dashboard/': {
    method: 'GET';
    response: DashboardOverview;
    auth: 'admin';
  };
  
  // API 성능 메트릭
  '/api/monitoring/api-metrics/': {
    method: 'GET';
    params: { timeframe: '24h' | '7d' | '30d' };
    response: APIMetrics[];
    auth: 'admin';
  };
  
  // 에러 로그
  '/api/monitoring/error-logs/': {
    method: 'GET';
    params: { level: 'ERROR' | 'CRITICAL'; limit: number };
    response: ErrorLog[];
    auth: 'admin';
  };
  
  // 사용자 활동
  '/api/monitoring/user-activity/': {
    method: 'GET';
    params: { period: 'today' | 'week' | 'month' };
    response: UserActivity[];
    auth: 'admin';
  };
}
```

### 1.4 UI 컴포넌트 명세
```typescript
// 시스템 상태 카드
interface SystemStatusCardProps {
  title: string;
  value: number | string;
  unit?: string;
  status: 'healthy' | 'warning' | 'critical';
  trend?: 'up' | 'down' | 'stable';
  onClick?: () => void;
}

// 성능 차트
interface PerformanceChartProps {
  data: MetricDataPoint[];
  type: 'line' | 'area' | 'bar';
  height?: number;
  showLegend?: boolean;
  timeRange: '1h' | '24h' | '7d' | '30d';
}

// 에러 로그 테이블
interface ErrorLogTableProps {
  logs: ErrorLog[];
  onResolve: (id: string) => void;
  onViewDetails: (log: ErrorLog) => void;
  pagination: PaginationProps;
}
```

### 1.5 실시간 업데이트
```typescript
// WebSocket 또는 폴링을 통한 실시간 데이터
const useRealTimeMonitoring = () => {
  const queryClient = useQueryClient();
  
  useEffect(() => {
    const interval = setInterval(() => {
      // 5초마다 중요 메트릭 업데이트
      queryClient.invalidateQueries(['system-health']);
      queryClient.invalidateQueries(['api-metrics']);
    }, 5000);
    
    return () => clearInterval(interval);
  }, [queryClient]);
};
```

---

## 🔔 2. 알림 시스템

### 2.1 기술 스택
```python
# Backend Stack
- Django 4.2 (기존)
- Celery (기존 - 비동기 작업용)
- Redis (기존 - 메시지 브로커)
- python-slack-sdk 3.21.3 (Slack 연동)
- django-ses (이메일 발송)
```

### 2.2 아키텍처 설계
```
backend/
├── alerts/                           # 새로운 Django 앱
│   ├── models.py                     # 알림 규칙, 히스토리 모델
│   ├── services/
│   │   ├── alert_engine.py           # 알림 규칙 엔진
│   │   ├── slack_notifier.py         # Slack 알림 서비스
│   │   ├── email_notifier.py         # 이메일 알림 서비스
│   │   └── notification_manager.py   # 알림 관리자
│   ├── tasks.py                      # Celery 비동기 작업
│   ├── serializers.py                # API 시리얼라이저
│   └── views.py                      # 알림 설정 API
├── monitoring/
│   └── signals.py                    # 모니터링 데이터 기반 알림 트리거
```

### 2.3 알림 규칙 정의
```python
# 알림 모델
class AlertRule(models.Model):
    ALERT_TYPES = [
        ('system_error', 'System Error'),
        ('performance', 'Performance Issue'),
        ('security', 'Security Alert'),
        ('business', 'Business Metric Alert'),
    ]
    
    SEVERITY_LEVELS = [
        ('low', 'Low'),
        ('medium', 'Medium'), 
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    name = models.CharField(max_length=100)
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPES)
    severity = models.CharField(max_length=10, choices=SEVERITY_LEVELS)
    
    # 조건 설정
    metric_name = models.CharField(max_length=50)  # 'cpu_usage', 'error_count', etc.
    condition = models.CharField(max_length=10)    # '>', '<', '==', '!='
    threshold_value = models.FloatField()
    time_window_minutes = models.IntegerField(default=5)
    
    # 알림 설정
    slack_enabled = models.BooleanField(default=True)
    email_enabled = models.BooleanField(default=True)
    slack_channel = models.CharField(max_length=50, default='#alerts')
    email_recipients = models.JSONField(default=list)
    
    # 중복 방지
    cooldown_minutes = models.IntegerField(default=30)
    max_alerts_per_hour = models.IntegerField(default=10)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

# 알림 히스토리
class AlertHistory(models.Model):
    rule = models.ForeignKey(AlertRule, on_delete=models.CASCADE)
    triggered_at = models.DateTimeField(auto_now_add=True)
    metric_value = models.FloatField()
    message = models.TextField()
    
    # 발송 상태
    slack_sent = models.BooleanField(default=False)
    email_sent = models.BooleanField(default=False)
    slack_response = models.JSONField(null=True, blank=True)
    email_response = models.JSONField(null=True, blank=True)
    
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
```

### 2.4 알림 엔진 구현
```python
# alerts/services/alert_engine.py
class AlertEngine:
    def __init__(self):
        self.slack_notifier = SlackNotifier()
        self.email_notifier = EmailNotifier()
    
    def check_alert_conditions(self):
        """모든 활성 알림 규칙을 확인하고 조건에 맞으면 알림 발송"""
        active_rules = AlertRule.objects.filter(is_active=True)
        
        for rule in active_rules:
            if self._should_check_rule(rule):
                metric_value = self._get_metric_value(rule)
                
                if self._condition_met(rule, metric_value):
                    if not self._in_cooldown(rule):
                        self._send_alert(rule, metric_value)
    
    def _get_metric_value(self, rule: AlertRule) -> float:
        """현재 메트릭 값을 가져옴"""
        now = timezone.now()
        time_window = now - timedelta(minutes=rule.time_window_minutes)
        
        if rule.metric_name == 'cpu_usage':
            return SystemHealth.objects.filter(
                timestamp__gte=time_window
            ).aggregate(avg_cpu=Avg('cpu_usage_percent'))['avg_cpu'] or 0
            
        elif rule.metric_name == 'error_count':
            return ErrorLog.objects.filter(
                timestamp__gte=time_window,
                level__in=['ERROR', 'CRITICAL']
            ).count()
            
        elif rule.metric_name == 'api_response_time':
            return APIMetrics.objects.filter(
                timestamp__gte=time_window
            ).aggregate(avg_time=Avg('response_time_ms'))['avg_time'] or 0
        
        # 추가 메트릭들...
        
    def _send_alert(self, rule: AlertRule, metric_value: float):
        """알림 발송"""
        message = self._build_message(rule, metric_value)
        
        # 알림 히스토리 생성
        alert_history = AlertHistory.objects.create(
            rule=rule,
            metric_value=metric_value,
            message=message
        )
        
        # Slack 알림
        if rule.slack_enabled:
            slack_result = self.slack_notifier.send_alert(
                channel=rule.slack_channel,
                message=message,
                severity=rule.severity
            )
            alert_history.slack_sent = slack_result.get('success', False)
            alert_history.slack_response = slack_result
        
        # 이메일 알림  
        if rule.email_enabled and rule.email_recipients:
            email_result = self.email_notifier.send_alert(
                recipients=rule.email_recipients,
                subject=f"[{rule.severity.upper()}] {rule.name}",
                message=message
            )
            alert_history.email_sent = email_result.get('success', False)
            alert_history.email_response = email_result
            
        alert_history.save()
```

### 2.5 Celery 작업 정의
```python
# alerts/tasks.py
from celery import shared_task
from .services.alert_engine import AlertEngine

@shared_task
def check_system_alerts():
    """시스템 알림 규칙 확인 (매 1분마다 실행)"""
    engine = AlertEngine()
    engine.check_alert_conditions()

@shared_task  
def send_daily_report():
    """일일 시스템 상태 리포트 발송"""
    # 일일 요약 리포트 생성 및 발송
    pass

@shared_task
def cleanup_old_alerts():
    """오래된 알림 히스토리 정리 (매일 실행)"""
    cutoff_date = timezone.now() - timedelta(days=30)
    AlertHistory.objects.filter(triggered_at__lt=cutoff_date).delete()

# Celery Beat 스케줄 (settings.py)
CELERY_BEAT_SCHEDULE = {
    'check-system-alerts': {
        'task': 'alerts.tasks.check_system_alerts',
        'schedule': crontab(minute='*'),  # 매분 실행
    },
    'send-daily-report': {
        'task': 'alerts.tasks.send_daily_report', 
        'schedule': crontab(hour=9, minute=0),  # 매일 오전 9시
    },
    'cleanup-old-alerts': {
        'task': 'alerts.tasks.cleanup_old_alerts',
        'schedule': crontab(hour=2, minute=0),  # 매일 오전 2시
    },
}
```

---

## ⚡ 3. 성능 최적화

### 3.1 데이터베이스 최적화
```sql
-- 추가할 인덱스들
-- 복습 시스템 최적화
CREATE INDEX CONCURRENTLY idx_review_schedule_user_date 
ON review_reviewschedule(user_id, next_review_date) 
WHERE next_review_date <= CURRENT_DATE;

-- API 메트릭 최적화
CREATE INDEX CONCURRENTLY idx_api_metrics_endpoint_date_time
ON monitoring_api_metrics(endpoint, date, response_time_ms);

-- AI 메트릭 최적화  
CREATE INDEX CONCURRENTLY idx_ai_metrics_user_date_cost
ON monitoring_ai_metrics(user_id, date, cost_usd);

-- 사용자 활동 최적화
CREATE INDEX CONCURRENTLY idx_user_activity_compound
ON monitoring_user_activity(date, api_requests_count, reviews_completed_count);
```

```python
# ORM 쿼리 최적화 예시
# Before (N+1 문제)
def get_user_reviews_slow():
    schedules = ReviewSchedule.objects.filter(
        next_review_date__lte=timezone.now().date()
    )
    for schedule in schedules:
        content_title = schedule.content.title  # N+1 쿼리 발생
        user_email = schedule.user.email        # N+1 쿼리 발생

# After (최적화된 쿼리)
def get_user_reviews_optimized():
    schedules = ReviewSchedule.objects.filter(
        next_review_date__lte=timezone.now().date()
    ).select_related('content', 'user')  # JOIN으로 한 번에 가져옴
    
    for schedule in schedules:
        content_title = schedule.content.title  # 추가 쿼리 없음
        user_email = schedule.user.email        # 추가 쿼리 없음
```

### 3.2 캐싱 전략
```python
# Redis 캐시 설정 강화
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://redis:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'SERIALIZER': 'django_redis.serializers.json.JSONSerializer',
        },
        'KEY_PREFIX': 'resee',
        'VERSION': 1,
    },
    # 세션별 캐시 분리
    'sessions': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://redis:6379/2',
        'TIMEOUT': 86400,  # 24시간
    },
    # API 응답 캐시
    'api_responses': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://redis:6379/3', 
        'TIMEOUT': 300,    # 5분
    }
}

# 캐시 데코레이터 활용
from django.views.decorators.cache import cache_page
from django.core.cache import cache

@cache_page(60 * 5, cache='api_responses')  # 5분 캐싱
def api_statistics_view(request):
    # 통계 데이터 API
    pass

# 복잡한 쿼리 결과 캐싱
def get_user_learning_stats(user_id, cache_timeout=300):
    cache_key = f'learning_stats_{user_id}'
    stats = cache.get(cache_key)
    
    if stats is None:
        stats = {
            'total_reviews': ReviewHistory.objects.filter(user_id=user_id).count(),
            'success_rate': ReviewHistory.objects.filter(
                user_id=user_id, result='remembered'
            ).count() / max(1, ReviewHistory.objects.filter(user_id=user_id).count()),
            # 기타 통계 계산...
        }
        cache.set(cache_key, stats, cache_timeout)
    
    return stats
```

---

## 📊 4. 비즈니스 인텔리전스 대시보드

### 4.1 데이터 모델 확장
```python
# analytics/models.py
class LearningPattern(models.Model):
    """사용자 학습 패턴 분석"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField()
    
    # 학습 시간 패턴
    morning_activity_score = models.FloatField(default=0)    # 0-100
    afternoon_activity_score = models.FloatField(default=0)
    evening_activity_score = models.FloatField(default=0)
    
    # 복습 패턴
    avg_review_interval_days = models.FloatField(default=0)
    preferred_review_count_per_session = models.IntegerField(default=0)
    success_rate_trend = models.FloatField(default=0)       # -1 to 1
    
    # 콘텐츠 선호도
    preferred_content_length = models.CharField(max_length=20, default='medium')  # short/medium/long
    most_active_category = models.CharField(max_length=100, blank=True)
    
    # AI 사용 패턴
    ai_dependency_score = models.FloatField(default=0)      # 0-100
    question_type_preference = models.JSONField(default=dict)
    
    class Meta:
        unique_together = ['user', 'date']

class ConversionFunnel(models.Model):
    """구독 전환 퍼널 분석"""
    date = models.DateField()
    
    # 퍼널 단계별 사용자 수
    visitors = models.IntegerField(default=0)
    signups = models.IntegerField(default=0)
    email_verified = models.IntegerField(default=0)
    first_content_created = models.IntegerField(default=0)
    first_review_completed = models.IntegerField(default=0)
    upgraded_to_basic = models.IntegerField(default=0)
    upgraded_to_pro = models.IntegerField(default=0)
    
    # 전환율 (자동 계산)
    signup_rate = models.FloatField(default=0)
    verification_rate = models.FloatField(default=0)
    activation_rate = models.FloatField(default=0)
    basic_conversion_rate = models.FloatField(default=0)
    pro_conversion_rate = models.FloatField(default=0)
    
    class Meta:
        unique_together = ['date']
```

### 4.2 분석 서비스
```python
# analytics/services/bi_analyzer.py
class BIAnalyzer:
    def generate_learning_insights(self, user_id: int, days: int = 30):
        """사용자별 학습 인사이트 생성"""
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)
        
        # 복습 성공률 트렌드
        success_trend = self._calculate_success_trend(user_id, start_date, end_date)
        
        # 최적 학습 시간대 분석
        optimal_time = self._find_optimal_learning_time(user_id, start_date, end_date)
        
        # 콘텐츠 추천
        content_recommendations = self._generate_content_recommendations(user_id)
        
        return {
            'success_trend': success_trend,
            'optimal_learning_time': optimal_time,
            'recommendations': content_recommendations,
            'insights': self._generate_textual_insights(user_id, days)
        }
    
    def analyze_cohort_retention(self, cohort_month: str):
        """코호트 분석 - 월별 사용자 리텐션"""
        cohort_users = User.objects.filter(
            date_joined__year=int(cohort_month.split('-')[0]),
            date_joined__month=int(cohort_month.split('-')[1])
        )
        
        retention_data = {}
        for weeks in range(1, 13):  # 12주간 추적
            week_start = timezone.now().date() - timedelta(weeks=weeks)
            week_end = week_start + timedelta(days=7)
            
            active_users = UserActivity.objects.filter(
                user__in=cohort_users,
                date__range=[week_start, week_end]
            ).values('user').distinct().count()
            
            retention_rate = active_users / cohort_users.count() * 100
            retention_data[f'week_{weeks}'] = retention_rate
            
        return retention_data
```

---

## 🧪 5. A/B 테스트 프레임워크

### 5.1 실험 관리 모델
```python
# experiments/models.py
class Experiment(models.Model):
    EXPERIMENT_STATUS = [
        ('draft', 'Draft'),
        ('running', 'Running'), 
        ('paused', 'Paused'),
        ('completed', 'Completed'),
    ]
    
    name = models.CharField(max_length=100)
    description = models.TextField()
    hypothesis = models.TextField()
    
    # 실험 설정
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    status = models.CharField(max_length=10, choices=EXPERIMENT_STATUS, default='draft')
    
    # 대상 사용자 설정
    target_user_percentage = models.FloatField(default=50.0)  # 0-100%
    user_filter_criteria = models.JSONField(default=dict)     # 필터 조건
    
    # 성공 지표
    primary_metric = models.CharField(max_length=50)
    secondary_metrics = models.JSONField(default=list)
    minimum_sample_size = models.IntegerField(default=1000)
    
    # 실험 결과
    statistical_significance = models.FloatField(null=True, blank=True)
    winner_variant = models.CharField(max_length=50, blank=True)
    
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)

class ExperimentVariant(models.Model):
    experiment = models.ForeignKey(Experiment, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)  # 'control', 'variant_a', etc.
    description = models.TextField()
    traffic_percentage = models.FloatField(default=50.0)
    
    # 변경사항 정의
    feature_flags = models.JSONField(default=dict)
    config_overrides = models.JSONField(default=dict)

class ExperimentAssignment(models.Model):
    """사용자별 실험 배정"""
    experiment = models.ForeignKey(Experiment, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    variant = models.ForeignKey(ExperimentVariant, on_delete=models.CASCADE)
    assigned_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['experiment', 'user']

class ExperimentEvent(models.Model):
    """실험 이벤트 추적"""
    assignment = models.ForeignKey(ExperimentAssignment, on_delete=models.CASCADE)
    event_name = models.CharField(max_length=100)  # 'page_view', 'signup', 'purchase', etc.
    event_data = models.JSONField(default=dict)
    timestamp = models.DateTimeField(auto_now_add=True)
```

### 5.2 실험 엔진
```python
# experiments/services/experiment_engine.py
class ExperimentEngine:
    def assign_user_to_experiment(self, user: User, experiment_name: str):
        """사용자를 실험에 배정"""
        try:
            experiment = Experiment.objects.get(
                name=experiment_name, 
                status='running',
                start_date__lte=timezone.now(),
                end_date__gte=timezone.now()
            )
        except Experiment.DoesNotExist:
            return None
            
        # 이미 배정된 사용자인지 확인
        existing_assignment = ExperimentAssignment.objects.filter(
            experiment=experiment,
            user=user
        ).first()
        
        if existing_assignment:
            return existing_assignment.variant
            
        # 사용자가 실험 대상인지 확인
        if not self._is_eligible_user(user, experiment):
            return None
            
        # 배정 로직 (해시 기반으로 일관된 배정)
        user_hash = hash(f"{experiment.id}_{user.id}") % 100
        
        cumulative_percentage = 0
        for variant in experiment.experimentvariant_set.all():
            cumulative_percentage += variant.traffic_percentage
            if user_hash < cumulative_percentage:
                # 사용자 배정 생성
                assignment = ExperimentAssignment.objects.create(
                    experiment=experiment,
                    user=user,
                    variant=variant
                )
                return variant
        
        return None  # 실험에 배정되지 않음
    
    def track_event(self, user: User, event_name: str, event_data: dict = None):
        """실험 관련 이벤트 추적"""
        # 사용자의 활성 실험 배정 찾기
        active_assignments = ExperimentAssignment.objects.filter(
            user=user,
            experiment__status='running',
            experiment__start_date__lte=timezone.now(),
            experiment__end_date__gte=timezone.now()
        )
        
        for assignment in active_assignments:
            ExperimentEvent.objects.create(
                assignment=assignment,
                event_name=event_name,
                event_data=event_data or {}
            )
    
    def get_experiment_results(self, experiment_id: int):
        """실험 결과 분석"""
        experiment = Experiment.objects.get(id=experiment_id)
        variants = experiment.experimentvariant_set.all()
        
        results = {}
        for variant in variants:
            # 변형별 사용자 수
            total_users = ExperimentAssignment.objects.filter(
                experiment=experiment,
                variant=variant
            ).count()
            
            # 주요 지표별 전환율 계산
            primary_conversions = ExperimentEvent.objects.filter(
                assignment__experiment=experiment,
                assignment__variant=variant,
                event_name=experiment.primary_metric
            ).values('assignment__user').distinct().count()
            
            conversion_rate = primary_conversions / max(1, total_users) * 100
            
            results[variant.name] = {
                'total_users': total_users,
                'conversions': primary_conversions,
                'conversion_rate': conversion_rate
            }
        
        # 통계적 유의성 검정
        significance = self._calculate_statistical_significance(results)
        
        return {
            'results': results,
            'statistical_significance': significance,
            'recommended_winner': self._determine_winner(results, significance)
        }
```

---

## 🔧 6. 구현 가이드라인

### 6.1 코드 품질 기준
```python
# 모든 새로운 코드는 다음 기준을 준수해야 함:
1. 테스트 커버리지 > 80%
2. Type hints 100% 적용 (Python)
3. ESLint/TypeScript strict mode (Frontend)
4. 문서화 (docstring) 필수
5. 보안 검토 통과
```

### 6.2 성능 기준
```yaml
# 성능 요구사항
API Response Time: < 200ms (95 percentile)
Database Query Time: < 50ms (average)
Frontend Bundle Size: < 1MB (gzipped)
Memory Usage: < 512MB per service
```

### 6.3 모니터링 기준
```python
# 각 기능은 다음 메트릭을 제공해야 함:
1. 성능 메트릭 (응답시간, 처리량)
2. 에러 메트릭 (에러율, 에러 타입)
3. 비즈니스 메트릭 (사용률, 전환율)
4. 리소스 사용량 (CPU, 메모리, DB)
```

---

## 📋 체크리스트 템플릿

각 기능 개발 시 사용할 체크리스트:

### 개발 전 체크리스트
- [ ] 요구사항 명확화 완료
- [ ] 기술 스택 확정
- [ ] 아키텍처 설계 검토
- [ ] API 명세서 작성
- [ ] 테스트 계획 수립

### 개발 중 체크리스트  
- [ ] 코드 리뷰 수행
- [ ] 단위 테스트 작성
- [ ] 통합 테스트 작성
- [ ] 성능 테스트 수행
- [ ] 보안 검토 수행

### 배포 전 체크리스트
- [ ] 프로덕션 환경 테스트
- [ ] 롤백 계획 수립
- [ ] 모니터링 설정 완료
- [ ] 문서 업데이트 완료
- [ ] 팀 공유 완료

---

*이 기술 명세서는 개발 진행에 따라 지속적으로 업데이트됩니다.*