#!/usr/bin/env python
"""
Django script to create test accounts for the Resee application.
Run with: python manage.py shell < create_test_accounts.py
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resee.settings')
django.setup()

from django.contrib.auth import get_user_model
from content.models import Category, Content
from review.models import ReviewSchedule
import logging

User = get_user_model()
logger = logging.getLogger(__name__)

def create_test_accounts():
    """Create test accounts with sample data"""
    
    print("🚀 테스트 계정 생성을 시작합니다...")
    
    test_accounts = [
        {
            'email': 'admin@resee.com',
            'password': 'admin123!',
            'first_name': '관리자',
            'last_name': '시스템',
            'is_superuser': True,
            'is_staff': True
        },
        {
            'email': 'test@resee.com',
            'password': 'test123!',
            'first_name': '테스트',
            'last_name': '사용자',
            'is_superuser': False,
            'is_staff': False
        },
        {
            'email': 'demo@resee.com',
            'password': 'demo123!',
            'first_name': '데모',
            'last_name': '계정',
            'is_superuser': False,
            'is_staff': False
        }
    ]
    
    created_users = []
    
    for account_data in test_accounts:
        email = account_data['email']
        
        # Check if user already exists
        if User.objects.filter(email=email).exists():
            print(f"⚠️  사용자 '{email}'이 이미 존재합니다. 건너뜁니다.")
            user = User.objects.get(email=email)
            created_users.append(user)
            continue
        
        try:
            # Create user
            user_data = account_data.copy()
            password = user_data.pop('password')
            
            if user_data.get('is_superuser'):
                user = User.objects.create_superuser(
                    email=user_data['email'],
                    password=password,
                    first_name=user_data.get('first_name', ''),
                    last_name=user_data.get('last_name', '')
                )
            else:
                user = User.objects.create_user(
                    email=user_data['email'],
                    password=password,
                    first_name=user_data.get('first_name', ''),
                    last_name=user_data.get('last_name', ''),
                    is_staff=user_data.get('is_staff', False)
                )
            
            created_users.append(user)
            print(f"✅ 사용자 '{email}' 생성 완료")
            
        except Exception as e:
            print(f"❌ 사용자 '{email}' 생성 실패: {str(e)}")
    
    return created_users

def create_sample_content():
    """Create sample content for test users"""
    
    print("\n📚 샘플 콘텐츠 생성을 시작합니다...")
    
    # Get test users (exclude admin)
    test_users = User.objects.filter(email__in=['test@resee.com', 'demo@resee.com'])
    
    if not test_users.exists():
        print("⚠️  테스트 사용자가 없습니다. 샘플 콘텐츠를 생성하지 않습니다.")
        return
    
    # Create global categories if they don't exist (user=None for global categories)
    categories_data = [
        {'name': '프로그래밍', 'description': '프로그래밍 관련 학습 자료'},
        {'name': '과학', 'description': '과학 지식 및 이론'},
        {'name': '언어학습', 'description': '외국어 학습 자료'},
        {'name': '일반상식', 'description': '일반적인 상식과 정보'}
    ]
    
    created_categories = []
    for cat_data in categories_data:
        category, created = Category.objects.get_or_create(
            name=cat_data['name'],
            user=None,  # Global category
            defaults={
                'description': cat_data['description']
            }
        )
        created_categories.append(category)
        if created:
            print(f"✅ 카테고리 '{category.name}' 생성 완료")
    
    # Skip tag creation as Tag model is not used in current schema
    print("⚠️  Tag 모델이 현재 스키마에 없으므로 태그 생성을 건너뜁니다.")
    
    # Create sample content for each test user
    sample_contents = [
        {
            'title': 'Python 기초 문법',
            'content': '''# Python 기초 문법

## 변수와 데이터 타입
- 문자열: `str`
- 정수: `int`
- 실수: `float`
- 불린: `bool`

## 제어 구조
```python
if condition:
    print("조건이 참입니다")
elif other_condition:
    print("다른 조건이 참입니다")
else:
    print("모든 조건이 거짓입니다")
```

## 반복문
```python
for i in range(5):
    print(f"숫자: {i}")

while condition:
    # 조건이 참인 동안 실행
    pass
```''',
            'category_name': '프로그래밍',
            'tags': ['기초', '중요'],
            'priority': 'high'
        },
        {
            'title': '메모리 관리와 가비지 컬렉션',
            'content': '''# 메모리 관리와 가비지 컬렉션

## 스택 메모리
- 지역 변수와 함수 호출 정보 저장
- LIFO (Last In, First Out) 구조
- 자동으로 해제됨

## 힙 메모리
- 동적으로 할당되는 메모리
- 객체와 배열이 저장됨
- 가비지 컬렉션이 필요

## 가비지 컬렉션 알고리즘
1. **Mark and Sweep**: 참조되지 않는 객체를 표시하고 제거
2. **Reference Counting**: 참조 횟수를 세어 0이 되면 제거
3. **Generational GC**: 세대별로 나누어 관리''',
            'category_name': '프로그래밍',
            'tags': ['심화', '중요'],
            'priority': 'medium'
        },
        {
            'title': '영어 불규칙 동사',
            'content': '''# 영어 불규칙 동사

## A-A-A 패턴 (원형-과거-과거분사가 모두 같음)
- **cut** - cut - cut (자르다)
- **put** - put - put (놓다)
- **hit** - hit - hit (치다)
- **cost** - cost - cost (비용이 들다)

## A-B-A 패턴 (원형과 과거분사가 같음)
- **come** - came - come (오다)
- **run** - ran - run (달리다)
- **become** - became - become (되다)

## A-B-B 패턴 (과거와 과거분사가 같음)
- **make** - made - made (만들다)
- **have** - had - had (가지다)
- **say** - said - said (말하다)''',
            'category_name': '언어학습',
            'tags': ['기초', '복습필요'],
            'priority': 'high'
        },
        {
            'title': '뉴턴의 운동 법칙',
            'content': '''# 뉴턴의 운동 법칙

## 제1법칙: 관성의 법칙
정지해 있는 물체는 외력이 작용하지 않는 한 계속 정지해 있고, 운동하는 물체는 외력이 작용하지 않는 한 등속직선운동을 계속한다.

**공식**: v = 일정 (F = 0일 때)

## 제2법칙: 가속도의 법칙
물체의 가속도는 작용하는 힘에 비례하고, 질량에 반비례한다.

**공식**: F = ma
- F: 힘 (뉴턴, N)
- m: 질량 (킬로그램, kg)
- a: 가속도 (m/s²)

## 제3법칙: 작용-반작용의 법칙
물체 A가 물체 B에 힘을 가하면, 물체 B도 물체 A에 크기가 같고 방향이 반대인 힘을 가한다.

**공식**: F₁ = -F₂''',
            'category_name': '과학',
            'tags': ['기초', '중요'],
            'priority': 'high'
        },
        {
            'title': '세계 주요 국가 수도',
            'content': '''# 세계 주요 국가 수도

## 아시아
- **대한민국**: 서울
- **일본**: 도쿄
- **중국**: 베이징
- **인도**: 뉴델리
- **태국**: 방콕

## 유럽
- **영국**: 런던
- **프랑스**: 파리
- **독일**: 베를린
- **이탈리아**: 로마
- **스페인**: 마드리드

## 아메리카
- **미국**: 워싱턴 D.C.
- **캐나다**: 오타와
- **브라질**: 브라질리아
- **아르헨티나**: 부에노스아이레스

## 기타
- **호주**: 캔버라
- **이집트**: 카이로
- **남아프리카공화국**: 케이프타운, 프리토리아, 블룸폰테인''',
            'category_name': '일반상식',
            'tags': ['기초'],
            'priority': 'low'
        }
    ]
    
    for user in test_users:
        print(f"\n👤 사용자 '{user.email}'의 샘플 콘텐츠 생성 중...")
        
        for content_data in sample_contents:
            # Get category
            try:
                category = Category.objects.get(name=content_data['category_name'])
            except Category.DoesNotExist:
                print(f"⚠️  카테고리 '{content_data['category_name']}'를 찾을 수 없습니다.")
                continue
            
            # Check if content already exists for this user
            if Content.objects.filter(
                author=user, 
                title=content_data['title']
            ).exists():
                print(f"⚠️  콘텐츠 '{content_data['title']}'이 이미 존재합니다. 건너뜁니다.")
                continue
            
            try:
                # Create content
                content = Content.objects.create(
                    author=user,  # Use 'author' field instead of 'user'
                    title=content_data['title'],
                    content=content_data['content'],
                    category=category,
                    priority=content_data['priority']
                )
                
                # Skip tag assignment as Tag model is not used
                # for tag_name in content_data['tags']:
                #     try:
                #         tag = Tag.objects.get(name=tag_name)
                #         content.tags.add(tag)
                #     except Tag.DoesNotExist:
                #         print(f"⚠️  태그 '{tag_name}'을 찾을 수 없습니다.")
                
                print(f"✅ 콘텐츠 '{content.title}' 생성 완료")
                
            except Exception as e:
                print(f"❌ 콘텐츠 '{content_data['title']}' 생성 실패: {str(e)}")

def main():
    """Main function to create test accounts and sample data"""
    
    print("="*60)
    print("🧪 RESEE 테스트 환경 설정")
    print("="*60)
    
    try:
        # Create test accounts
        created_users = create_test_accounts()
        
        # Create sample content
        create_sample_content()
        
        print("\n" + "="*60)
        print("✅ 테스트 환경 설정 완료!")
        print("="*60)
        
        print("\n📋 생성된 테스트 계정:")
        print("-" * 40)
        print("관리자 계정:")
        print("  이메일: admin@resee.com")
        print("  비밀번호: admin123!")
        print()
        print("일반 사용자 계정:")
        print("  이메일: test@resee.com")
        print("  비밀번호: test123!")
        print()
        print("데모 계정:")
        print("  이메일: demo@resee.com")
        print("  비밀번호: demo123!")
        print()
        print("🌐 로그인 페이지: http://localhost:3000/login")
        print("🔧 관리자 페이지: http://localhost:8000/admin")
        
    except Exception as e:
        print(f"\n❌ 테스트 환경 설정 중 오류 발생: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()