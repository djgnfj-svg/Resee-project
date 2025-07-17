#!/usr/bin/env python
import os
import sys
import django

# Django 설정
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resee.settings')
django.setup()

from django.contrib.auth import get_user_model
from content.models import Category, Tag, Content
from review.models import ReviewSchedule, ReviewHistory
from django.utils import timezone
from datetime import timedelta
import random

User = get_user_model()

def create_test_data():
    print("Creating test user...")
    
    # 기존 사용자가 있으면 삭제
    if User.objects.filter(username='testuser').exists():
        User.objects.filter(username='testuser').delete()
        print("Removed existing test user")
    
    # 테스트 사용자 생성
    user = User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123',
        first_name='Test',
        last_name='User',
        timezone='Asia/Seoul',
        notification_enabled=True
    )
    print(f"Created user: {user.username}")

    # 카테고리 생성
    print("Creating categories...")
    categories = []
    category_names = ['Python', 'Django', 'JavaScript', 'React', 'Database']
    for name in category_names:
        category = Category.objects.create(
            name=name,
            user=user,
            description=f'{name} 관련 학습 자료'
        )
        categories.append(category)
        print(f"Created category: {category.name}")

    # 태그 생성
    print("Creating tags...")
    tags = []
    tag_names = ['기초', '중급', '고급', '프로젝트', '실습', '이론']
    for name in tag_names:
        tag, created = Tag.objects.get_or_create(name=name)
        if created:
            tags.append(tag)
            print(f"Created tag: {tag.name}")
        else:
            tags.append(tag)
            print(f"Using existing tag: {tag.name}")

    # 콘텐츠 생성
    print("Creating contents...")
    contents = []
    content_data = [
        ('Python 기초 - 변수와 데이터 타입', 'Python', '# Python 변수와 데이터 타입\n\n## 변수 선언\n```python\nname = "홍길동"\nage = 25\nis_student = True\n```'),
        ('Django 모델 정의하기', 'Django', '# Django 모델\n\n## 기본 모델 구조\n```python\nclass User(models.Model):\n    name = models.CharField(max_length=100)\n    email = models.EmailField()\n```'),
        ('JavaScript ES6 화살표 함수', 'JavaScript', '# 화살표 함수\n\n## 기본 문법\n```javascript\nconst add = (a, b) => a + b;\nconsole.log(add(1, 2)); // 3\n```'),
        ('React 컴포넌트 생성', 'React', '# React 함수형 컴포넌트\n\n```jsx\nfunction MyComponent() {\n  return <div>Hello World</div>;\n}\n```'),
        ('SQL JOIN 개념', 'Database', '# SQL JOIN\n\n## INNER JOIN\n```sql\nSELECT * FROM users\nINNER JOIN orders ON users.id = orders.user_id;\n```'),
        ('Python 리스트 컴프리헨션', 'Python', '# 리스트 컴프리헨션\n\n```python\nsquares = [x**2 for x in range(10)]\nprint(squares)  # [0, 1, 4, 9, 16, 25, 36, 49, 64, 81]\n```'),
        ('Django REST Framework 시리얼라이저', 'Django', '# DRF 시리얼라이저\n\n```python\nclass UserSerializer(serializers.ModelSerializer):\n    class Meta:\n        model = User\n        fields = "__all__"\n```'),
        ('JavaScript Promise와 async/await', 'JavaScript', '# 비동기 처리\n\n```javascript\nasync function fetchData() {\n  const response = await fetch("/api/data");\n  return response.json();\n}\n```'),
        ('React Hooks - useState', 'React', '# useState Hook\n\n```jsx\nimport { useState } from "react";\n\nfunction Counter() {\n  const [count, setCount] = useState(0);\n  return <button onClick={() => setCount(count + 1)}>{count}</button>;\n}\n```'),
        ('데이터베이스 인덱스 최적화', 'Database', '# 인덱스 최적화\n\n```sql\nCREATE INDEX idx_user_email ON users(email);\nEXPLAIN SELECT * FROM users WHERE email = "test@example.com";\n```')
    ]

    for title, cat_name, content_text in content_data:
        category = Category.objects.get(name=cat_name, user=user)
        content = Content.objects.create(
            title=title,
            content=content_text,
            author=user,
            category=category,
            priority=random.choice(['low', 'medium', 'high'])
        )
        # 랜덤한 태그 추가
        random_tags = random.sample(tags, random.randint(1, 3))
        content.tags.set(random_tags)
        contents.append(content)
        print(f"Created content: {content.title}")

    # 리뷰 스케줄 생성
    print("Creating review schedules...")
    for content in contents:
        # 일부 콘텐츠는 이미 복습이 시작된 상태로 만들기
        if random.choice([True, False]):
            initial_completed = True
            interval_index = random.randint(0, 3)
            next_review_date = timezone.now() + timedelta(days=random.randint(-2, 5))
        else:
            initial_completed = False
            interval_index = 0
            next_review_date = timezone.now()
        
        schedule = ReviewSchedule.objects.create(
            content=content,
            user=user,
            next_review_date=next_review_date,
            interval_index=interval_index,
            initial_review_completed=initial_completed,
            is_active=True
        )
        print(f"Created schedule for: {content.title}")

    # 리뷰 히스토리 생성 (지난 30일간의 복습 기록)
    print("Creating review history...")
    for i in range(50):  # 50개의 복습 기록 생성
        content = random.choice(contents)
        review_date = timezone.now() - timedelta(days=random.randint(0, 30))
        result = random.choices(
            ['remembered', 'partial', 'forgot'], 
            weights=[60, 25, 15]  # 60% 기억함, 25% 애매함, 15% 모름
        )[0]
        time_spent = random.randint(60, 300)  # 1-5분
        
        ReviewHistory.objects.create(
            content=content,
            user=user,
            review_date=review_date,
            result=result,
            time_spent=time_spent,
            notes=f'{result}로 복습 완료'
        )

    print("=" * 50)
    print("테스트 계정 생성 완료!")
    print("=" * 50)
    print(f"사용자명: testuser")
    print(f"비밀번호: testpass123")
    print(f"이메일: test@example.com")
    print(f"생성된 카테고리: {len(categories)}개")
    print(f"생성된 태그: {len(tags)}개")
    print(f"생성된 콘텐츠: {len(contents)}개")
    print(f"생성된 리뷰 스케줄: {ReviewSchedule.objects.count()}개")
    print(f"생성된 리뷰 히스토리: {ReviewHistory.objects.count()}개")
    print("=" * 50)

if __name__ == '__main__':
    create_test_data()