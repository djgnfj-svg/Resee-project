#!/usr/bin/env python
"""
Test script for AI mock responses
"""
import os
import sys
import django

# Add the backend directory to Python path
sys.path.append('/mnt/c/mypojects/Resee/backend')

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resee.settings.development')
django.setup()

from ai_review.mock_responses import AIMockResponses
from ai_review.services import QuestionGeneratorService, AnswerEvaluatorService, AIChatService


def test_mock_responses():
    """Test all mock response functions"""
    
    print("🤖 Testing AI Mock Response System\n")
    
    # Test question generation mock
    print("1. Testing Question Generation Mock:")
    mock_questions = AIMockResponses.get_question_generation_response(
        content_text="Python 프로그래밍의 기초",
        question_type="multiple_choice",
        difficulty=3,
        count=2
    )
    print(f"   ✅ Generated {len(mock_questions['questions'])} questions")
    print(f"   📝 Sample question: {mock_questions['questions'][0]['question'][:50]}...")
    
    # Test answer evaluation mock
    print("\n2. Testing Answer Evaluation Mock:")
    mock_evaluation = AIMockResponses.get_answer_evaluation_response(
        question_text="Python에서 리스트의 특징은?",
        correct_answer="순서가 있고 변경 가능한 데이터 구조",
        user_answer="순서가 있고 값을 바꿀 수 있는 자료구조",
        question_type="multiple_choice"
    )
    print(f"   ✅ Evaluation score: {mock_evaluation['score']}")
    print(f"   💬 Feedback: {mock_evaluation['feedback'][:50]}...")
    
    # Test chat mock
    print("\n3. Testing AI Chat Mock:")
    mock_chat = AIMockResponses.get_chat_response(
        content_text="파이썬 변수와 데이터 타입",
        content_title="Python 기초",
        user_message="변수란 무엇인가요?"
    )
    print(f"   ✅ Chat response: {mock_chat['response'][:50]}...")
    print(f"   🎯 Confidence: {mock_chat['confidence_score']}")
    
    # Test weekly test mock
    print("\n4. Testing Weekly Test Mock:")
    mock_test = AIMockResponses.get_weekly_test_response()
    print(f"   ✅ Test generated with {mock_test['total_questions']} questions")
    print(f"   🎯 Difficulty distribution: {mock_test['difficulty_distribution']}")
    
    print("\n🎉 All AI Mock Response tests completed successfully!")


def test_ai_services():
    """Test AI services with mock responses"""
    
    print("\n🔧 Testing AI Services with Mock Integration\n")
    
    # Test QuestionGeneratorService
    print("1. Testing QuestionGeneratorService:")
    question_service = QuestionGeneratorService()
    print(f"   ✅ Mock mode: {question_service.use_mock_responses}")
    
    # Test AnswerEvaluatorService
    print("\n2. Testing AnswerEvaluatorService:")
    evaluator_service = AnswerEvaluatorService()
    print(f"   ✅ Mock mode: {evaluator_service.use_mock_responses}")
    
    # Test AIChatService
    print("\n3. Testing AIChatService:")
    chat_service = AIChatService()
    print(f"   ✅ Mock mode: {chat_service.use_mock_responses}")
    
    print("\n🎉 All AI Services initialization tests completed!")


if __name__ == "__main__":
    try:
        test_mock_responses()
        test_ai_services()
    except Exception as e:
        print(f"\n❌ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()