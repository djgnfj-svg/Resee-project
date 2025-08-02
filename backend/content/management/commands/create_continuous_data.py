"""
7월부터 현재까지 꾸준한 연속 학습 데이터 생성
연속 학습일 10일+ 달성, 캘린더 히트맵 활성화, 배지 시스템 작동을 위한 데이터
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta, datetime, time, date
import random
import math
import pytz
from content.models import Content, Category
from review.models import ReviewHistory, ReviewSchedule

User = get_user_model()


class Command(BaseCommand):
    help = '7월부터 현재까지 꾸준한 연속 학습 데이터 생성'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            default='test@resee.com',
            help='대상 사용자 이메일 (기본값: test@resee.com)'
        )

    def handle(self, *args, **options):
        email = options['email']
        
        # 사용자 가져오기
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'{email} 사용자가 없습니다.'))
            return

        # 기존 데이터 정리
        self.stdout.write('기존 데이터 정리 중...')
        ReviewHistory.objects.filter(user=user).delete()
        ReviewSchedule.objects.filter(user=user).delete()
        
        self.stdout.write(f'🚀 {email}을 위한 꾸준한 연속 학습 데이터 생성 시작')
        
        # 콘텐츠 가져오기 (이미 생성된 콘텐츠 사용)
        contents = Content.objects.filter(author=user).order_by('id')
        if not contents.exists():
            self.stdout.write(self.style.ERROR('콘텐츠가 없습니다. 먼저 create_realistic_data를 실행하세요.'))
            return
        
        contents_list = list(contents)
        self.stdout.write(f'사용할 콘텐츠: {len(contents_list)}개')
        
        # 연속 학습 데이터 생성 (7월 1일부터 현재까지)
        start_date = date(2024, 7, 1)  # 7월 1일부터 시작
        end_date = timezone.now().date()
        
        self.create_continuous_learning_data(user, contents_list, start_date, end_date)
        
        # 사용자 프로필 업데이트
        user.weekly_goal = 30  # 주 30회 복습 목표로 상향 조정
        user.save()
        
        self.stdout.write(self.style.SUCCESS('\n🎉 연속 학습 데이터 생성 완료!'))
        
        # 통계 출력
        total_reviews = ReviewHistory.objects.filter(user=user).count()
        unique_days = ReviewHistory.objects.filter(user=user).values('review_date__date').distinct().count()
        self.stdout.write(f'총 복습 횟수: {total_reviews}회')
        self.stdout.write(f'활성 학습일: {unique_days}일')

    def create_continuous_learning_data(self, user, contents_list, start_date, end_date):
        """연속 학습 데이터 생성"""
        current_date = start_date
        now = timezone.now()
        
        # 연속 학습을 위한 패턴 설정
        streak_patterns = {
            'high_motivation': 0.95,  # 95% 확률로 학습
            'normal_motivation': 0.85,  # 85% 확률로 학습  
            'low_motivation': 0.7,   # 70% 확률로 학습
            'break_probability': 0.05  # 5% 확률로 하루 쉼
        }
        
        # 시기별 동기 수준
        motivation_periods = [
            (date(2024, 7, 1), date(2024, 7, 20), 'high_motivation'),    # 7월 초 높은 동기
            (date(2024, 7, 21), date(2024, 8, 10), 'normal_motivation'), # 7월 말~8월 초 보통
            (date(2024, 8, 11), date(2024, 8, 25), 'low_motivation'),    # 8월 중순 낮음
            (date(2024, 8, 26), date(2024, 9, 15), 'high_motivation'),   # 8월 말~9월 초 높음
            (date(2024, 9, 16), date(2024, 10, 31), 'normal_motivation'), # 가을 보통
            (date(2024, 11, 1), date(2024, 12, 31), 'high_motivation'),  # 겨울 높음
            (date(2025, 1, 1), date(2025, 3, 31), 'normal_motivation'),  # 신년 보통
            (date(2025, 4, 1), date(2025, 6, 30), 'high_motivation'),    # 봄 높음
            (date(2025, 7, 1), end_date, 'high_motivation'),             # 현재까지 높음
        ]
        
        # 요일별 학습 강도 (월요일=0, 일요일=6)
        weekday_intensity = {
            0: 0.9,   # 월요일 - 높음
            1: 0.85,  # 화요일 - 높음
            2: 0.8,   # 수요일 - 보통
            3: 0.75,  # 목요일 - 보통
            4: 0.7,   # 금요일 - 낮음 (피로)
            5: 0.6,   # 토요일 - 낮음 (주말)
            6: 0.65,  # 일요일 - 보통 (주말 마무리)
        }
        
        # 시간대별 선호도
        preferred_hours = [7, 8, 9, 19, 20, 21, 22]  # 아침, 저녁 시간대
        
        total_reviews = 0
        consecutive_days = 0
        max_streak = 0
        current_streak = 0
        
        while current_date <= end_date:
            # 현재 날짜의 동기 수준 결정
            motivation_level = 'normal_motivation'
            for start, end, level in motivation_periods:
                if start <= current_date <= end:
                    motivation_level = level
                    break
            
            # 요일 강도 적용
            weekday = current_date.weekday()
            weekday_factor = weekday_intensity[weekday]
            
            # 학습 여부 결정
            study_probability = streak_patterns[motivation_level] * weekday_factor
            
            # 연속 학습 보너스 (연속으로 학습할수록 확률 증가)
            if current_streak >= 3:
                study_probability = min(0.98, study_probability + 0.1)
            
            should_study = random.random() < study_probability
            
            if should_study:
                # 하루 학습량 결정 (동기 수준에 따라)
                if motivation_level == 'high_motivation':
                    daily_reviews = random.choices([3, 4, 5, 6, 7, 8], weights=[5, 15, 25, 25, 20, 10])[0]
                elif motivation_level == 'normal_motivation':
                    daily_reviews = random.choices([2, 3, 4, 5, 6], weights=[10, 25, 30, 25, 10])[0]
                else:  # low_motivation
                    daily_reviews = random.choices([1, 2, 3, 4], weights=[20, 40, 30, 10])[0]
                
                # 주말에는 약간 적게
                if weekday >= 5:  # 토, 일
                    daily_reviews = max(1, int(daily_reviews * 0.8))
                
                # 학습 세션 생성
                self.create_daily_sessions(user, contents_list, current_date, daily_reviews, preferred_hours)
                
                total_reviews += daily_reviews
                consecutive_days += 1
                current_streak += 1
                max_streak = max(max_streak, current_streak)
                
                if current_date.day % 5 == 0:  # 매 5일마다 로그
                    self.stdout.write(f'  📅 {current_date.strftime("%m/%d")}: {daily_reviews}회 복습 (연속 {current_streak}일)')
            else:
                # 학습 안 함
                current_streak = 0
                if random.random() < 0.3:  # 30% 확률로 로그
                    self.stdout.write(f'  💤 {current_date.strftime("%m/%d")}: 휴식일')
            
            current_date += timedelta(days=1)
        
        # ReviewSchedule 생성
        self.create_review_schedules(user, contents_list, now)
        
        self.stdout.write(f'\n📊 학습 통계:')
        self.stdout.write(f'  - 총 복습: {total_reviews}회')
        self.stdout.write(f'  - 활성일: {consecutive_days}일')
        self.stdout.write(f'  - 최대 연속: {max_streak}일')

    def create_daily_sessions(self, user, contents_list, study_date, daily_reviews, preferred_hours):
        """하루 동안의 학습 세션 생성"""
        # 세션 수 결정 (1-3개)
        if daily_reviews <= 2:
            session_count = 1
        elif daily_reviews <= 4:
            session_count = random.choices([1, 2], weights=[30, 70])[0]
        else:
            session_count = random.choices([2, 3], weights=[60, 40])[0]
        
        # 세션별 복습 수 분배
        if session_count == 1:
            session_reviews = [daily_reviews]
        elif session_count == 2:
            if daily_reviews == 2:
                session_reviews = [1, 1]
            else:
                first = random.randint(1, daily_reviews - 1)
                session_reviews = [first, daily_reviews - first]
        else:  # 3 sessions
            if daily_reviews <= 3:
                session_reviews = [1] * daily_reviews
            else:
                first = random.randint(1, max(1, daily_reviews - 2))
                second = random.randint(1, max(1, daily_reviews - first - 1))
                third = daily_reviews - first - second
                session_reviews = [first, second, third]
        
        # 각 세션의 시간 결정
        session_times = []
        for i, reviews in enumerate(session_reviews):
            if i == 0:  # 첫 번째 세션
                hour = random.choice([7, 8, 9, 19, 20, 21])
            elif i == 1:  # 두 번째 세션
                hour = random.choice([12, 13, 14, 20, 21, 22])
            else:  # 세 번째 세션
                hour = random.choice([22, 23])
            
            minute = random.randint(0, 59)
            second = random.randint(0, 59)
            
            session_datetime = datetime(
                study_date.year, study_date.month, study_date.day,
                hour, minute, second
            )
            session_time = pytz.UTC.localize(session_datetime)
            session_times.append((session_time, reviews))
        
        # 시간순 정렬
        session_times.sort(key=lambda x: x[0])
        
        # 각 세션에서 복습 생성
        days_since_start = (study_date - date(2024, 7, 1)).days
        base_performance = 0.4 + min(0.4, days_since_start * 0.008)  # 시간이 지날수록 향상
        
        for session_time, reviews in session_times:
            # 세션당 복습할 콘텐츠 선택
            available_contents = contents_list.copy()
            session_contents = random.sample(available_contents, min(reviews, len(available_contents)))
            
            for content in session_contents:
                # 시간대별 성과 조정
                hour = session_time.hour
                if hour in preferred_hours:
                    performance_modifier = 1.2
                elif hour < 7 or hour > 23:
                    performance_modifier = 0.8
                else:
                    performance_modifier = 1.0
                
                # 요일별 성과 조정
                weekday = session_time.weekday()
                if weekday < 5:  # 평일
                    weekday_modifier = 1.0
                else:  # 주말
                    weekday_modifier = 0.9
                
                final_performance = base_performance * performance_modifier * weekday_modifier
                final_performance = min(0.9, final_performance + random.uniform(-0.1, 0.1))
                
                # 성과를 점수로 변환
                score = final_performance * 100
                
                # 결과 결정
                if score >= 75:
                    result = 'remembered'
                elif score >= 50:
                    result = 'partial'
                else:
                    result = 'forgot'
                
                # 학습 시간 계산
                if result == 'remembered':
                    time_spent = random.randint(90, 180)   # 1.5-3분
                elif result == 'partial':
                    time_spent = random.randint(120, 240)  # 2-4분
                else:
                    time_spent = random.randint(180, 360)  # 3-6분
                
                # 복습 이력 생성
                ReviewHistory.objects.create(
                    content=content,
                    user=user,
                    result=result,
                    review_date=session_time,
                    time_spent=time_spent,
                    notes=self.generate_realistic_notes(result, days_since_start)
                )

    def create_review_schedules(self, user, contents_list, now):
        """ReviewSchedule 생성"""
        intervals = [1, 3, 7, 14, 30]  # 에빙하우스 간격
        
        for content in contents_list:
            # 마지막 복습 확인
            last_review = ReviewHistory.objects.filter(
                content=content, user=user
            ).order_by('-review_date').first()
            
            if last_review:
                # 마지막 복습 결과에 따라 간격 결정
                if last_review.result == 'remembered':
                    interval_index = min(4, random.randint(2, 4))
                elif last_review.result == 'partial':
                    interval_index = random.randint(1, 3)
                else:
                    interval_index = random.randint(0, 1)
                
                next_review_date = last_review.review_date.date() + timedelta(days=intervals[interval_index])
                
                # 미래 날짜로 설정
                if next_review_date <= now.date():
                    next_review_date = now.date() + timedelta(days=random.randint(1, 3))
                
            else:
                interval_index = 0
                next_review_date = now.date() + timedelta(days=random.randint(1, 3))
            
            next_review_datetime = pytz.UTC.localize(
                datetime(next_review_date.year, next_review_date.month, next_review_date.day, 9, 0, 0)
            )
            
            schedule, created = ReviewSchedule.objects.get_or_create(
                content=content,
                user=user,
                defaults={
                    'next_review_date': next_review_datetime,
                    'interval_index': interval_index,
                    'initial_review_completed': True
                }
            )

    def generate_realistic_notes(self, result, days_since_start):
        """결과와 학습 경험에 따른 현실적인 노트 생성"""
        if result == 'remembered':
            if days_since_start < 30:
                notes = [
                    "처음엔 어려웠는데 이제 확실히 알겠음",
                    "반복 학습 효과가 나타나고 있음",
                    "개념이 점점 명확해짐",
                    "이해도가 높아졌음"
                ]
            else:
                notes = [
                    "완전히 체화됨. 자신 있음",
                    "응용까지 가능한 수준",
                    "다른 사람에게 설명 가능",
                    "마스터 수준에 도달함",
                    "실무에서도 활용 가능"
                ]
        elif result == 'partial':
            notes = [
                "대부분 기억하지만 세부사항이 애매함",
                "키워드는 알지만 완전하지 않음",
                "조금 더 연습이 필요함",
                "거의 다 맞췄지만 확신 부족",
                "예시를 더 봐야겠음"
            ]
        else:  # forgot
            if days_since_start < 15:
                notes = [
                    "아직 익숙하지 않음. 더 연습 필요",
                    "개념 이해가 부족함",
                    "기본기부터 다시 정리 필요",
                    "처음 배우는 내용이라 어려움"
                ]
            else:
                notes = [
                    "오랜만에 복습해서 까먹었음",
                    "다시 한번 정리가 필요함",
                    "개념은 알지만 적용이 어려움",
                    "더 자주 복습해야겠음"
                ]
        
        return random.choice(notes)