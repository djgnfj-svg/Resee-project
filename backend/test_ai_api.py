#!/usr/bin/env python
"""
Test AI API endpoints with mock responses
"""
import os
import sys
import django
import requests
import json

# Setup Django
sys.path.append('/mnt/c/mypojects/Resee/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resee.settings.development')
django.setup()

from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from content.models import Content

# Get test user and token
User = get_user_model()
user = User.objects.filter(is_superuser=True).first()
if not user:
    print("❌ No test user found")
    sys.exit(1)

# Generate JWT token
refresh = RefreshToken.for_user(user)
access_token = str(refresh.access_token)

# API base URL
BASE_URL = "http://localhost:8000/api"
headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json"
}

print("🧪 Testing AI API Endpoints with Mock Responses\n")
print(f"User: {user.email}")
print(f"Mock Mode: {os.environ.get('AI_USE_MOCK_RESPONSES', 'True')}\n")

# Get or create test content
content = Content.objects.filter(author=user).first()
if not content:
    from content.models import Category
    category, _ = Category.objects.get_or_create(
        name="Programming",
        user=user
    )
    content = Content.objects.create(
        author=user,
        title="Test Content for AI",
        content="This is test content for AI functionality testing.",
        category=category
    )
    print(f"✅ Created test content: {content.title}")
else:
    print(f"✅ Using existing content: {content.title}")

print(f"Content ID: {content.id}\n")

# Test 1: AI Health Check
print("1. Testing AI Health Check:")
try:
    response = requests.get(f"{BASE_URL}/ai-review/health/", headers=headers)
    if response.status_code == 200:
        print(f"   ✅ Health check passed: {response.json()}")
    else:
        print(f"   ❌ Health check failed: {response.status_code}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 2: Generate Questions
print("\n2. Testing Question Generation:")
try:
    data = {
        "content_id": content.id,
        "question_types": ["multiple_choice"],
        "difficulty": 3,
        "count": 2
    }
    response = requests.post(f"{BASE_URL}/ai-review/generate-questions/", 
                            json=data, headers=headers)
    if response.status_code in [200, 201]:
        result = response.json()
        print(f"   ✅ Generated {len(result)} questions")
        if result:
            print(f"   📝 First question: {result[0].get('question_text', 'N/A')[:50]}...")
    else:
        print(f"   ❌ Failed: {response.status_code} - {response.text[:200]}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 3: AI Chat
print("\n3. Testing AI Chat:")
try:
    data = {
        "content_id": content.id,
        "message": "이 콘텐츠의 핵심 개념은 무엇인가요?"
    }
    response = requests.post(f"{BASE_URL}/ai-review/chat/", 
                            json=data, headers=headers)
    if response.status_code == 200:
        result = response.json()
        print(f"   ✅ Chat response received")
        print(f"   💬 Response: {result.get('response', 'N/A')[:100]}...")
        print(f"   🎯 Confidence: {result.get('confidence_score', 'N/A')}")
    else:
        print(f"   ❌ Failed: {response.status_code} - {response.text[:200]}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 4: AI Analytics
print("\n4. Testing AI Analytics:")
try:
    data = {
        "period_type": "weekly"
    }
    response = requests.post(f"{BASE_URL}/ai-review/analytics/", 
                            json=data, headers=headers)
    if response.status_code == 200:
        result = response.json()
        print(f"   ✅ Analytics generated")
        metrics = result.get('metrics', {})
        print(f"   📊 Success rate: {metrics.get('success_rate', 'N/A')}%")
        print(f"   📈 Total reviews: {metrics.get('total_reviews', 'N/A')}")
    else:
        print(f"   ❌ Failed: {response.status_code} - {response.text[:200]}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 5: Weekly Test
print("\n5. Testing Weekly Test Creation:")
try:
    # First check if test exists
    response = requests.get(f"{BASE_URL}/ai-review/weekly-test/", headers=headers)
    if response.status_code == 200:
        result = response.json()
        if result.get('exists'):
            print(f"   ℹ️  Test already exists for this week")
        else:
            # Create new test
            data = {
                "total_questions": 10
            }
            response = requests.post(f"{BASE_URL}/ai-review/weekly-test/", 
                                    json=data, headers=headers)
            if response.status_code in [200, 201]:
                result = response.json()
                print(f"   ✅ Weekly test created")
                print(f"   📝 Test ID: {result.get('test_id', 'N/A')}")
            else:
                print(f"   ⚠️  Cannot create test: {response.json().get('message', 'Unknown error')}")
    else:
        print(f"   ❌ Failed to check test: {response.status_code}")
except Exception as e:
    print(f"   ❌ Error: {e}")

print("\n✨ AI API Testing Complete!")
print(f"ℹ️  Mock mode is {'ENABLED' if os.environ.get('AI_USE_MOCK_RESPONSES', 'True') == 'True' else 'DISABLED'}")
print("💡 To switch between mock and real AI, set AI_USE_MOCK_RESPONSES environment variable")