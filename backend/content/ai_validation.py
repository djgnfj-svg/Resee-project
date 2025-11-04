"""
AI-powered content validation module.
Validates learning content for factual accuracy, logical consistency, and title relevance.

LangChain 기반으로 구현됨
"""

import json
import logging
from typing import Optional, Dict
from django.conf import settings
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate

logger = logging.getLogger(__name__)


def validate_content(title: str, content: str) -> dict:
    """
    Validate learning content using AI.

    Args:
        title: Content title
        content: Content body (markdown)

    Returns:
        dict: Validation results with scores and feedback
    """
    api_key = getattr(settings, 'ANTHROPIC_API_KEY', None)

    if not api_key:
        logger.error("ANTHROPIC_API_KEY not configured")
        return _get_error_response("API 키가 설정되지 않았습니다")

    try:
        llm = ChatAnthropic(
            model="claude-3-7-sonnet-20250219",
            temperature=0.3,
            max_tokens=2000,
            api_key=api_key
        )

        prompt = ChatPromptTemplate.from_template("""당신은 학습 자료 검증 전문가입니다. 다음 학습 콘텐츠를 엄격하게 검토해주세요.

제목: {title}
내용:
{content}

다음 3가지를 평가해주세요:

1. **사실적 정확성** (Factual Accuracy):
   - 내용이 객관적으로 정확한가?
   - 잘못된 정보나 오해의 소지가 있는가?
   - 점수: 0-100 (100점 만점)

2. **논리적 일관성** (Logical Consistency):
   - 설명의 논리가 타당한가?
   - 모순되는 내용이 있는가?
   - 점수: 0-100 (100점 만점)

3. **제목-내용 적합성** (Title Relevance):
   - 제목과 내용이 일치하는가?
   - 제목에서 기대되는 내용을 다루고 있는가?
   - 점수: 0-100 (100점 만점)

**응답 형식 (JSON만 반환, 다른 텍스트 없이):**
{{{{
  "is_valid": true/false (모든 점수가 70점 이상이면 true),
  "factual_accuracy": {{{{
    "score": 0-100,
    "issues": ["문제점1", "문제점2", ...] (없으면 빈 배열)
  }}}},
  "logical_consistency": {{{{
    "score": 0-100,
    "issues": ["문제점1", "문제점2", ...] (없으면 빈 배열)
  }}}},
  "title_relevance": {{{{
    "score": 0-100,
    "issues": ["문제점1", "문제점2", ...] (없으면 빈 배열)
  }}}},
  "overall_feedback": "전체 평가 요약 (2-3문장)"
}}}}

**평가 기준:**
- 90-100점: 매우 우수, 문제 없음
- 70-89점: 양호, 사소한 개선 필요
- 50-69점: 보통, 중요한 개선 필요
- 0-49점: 부족, 전면 수정 필요

JSON만 반환하세요.""")

        response = llm.invoke(prompt.format(title=title, content=content))
        response_text = response.content.strip()

        logger.info(f"AI validation response received for '{title[:50]}...'")

        # Parse JSON response
        result = _parse_validation_response(response_text)
        return result

    except Exception as e:
        logger.error(f"AI validation failed for title '{title[:50]}...': {str(e)}", exc_info=True)
        return _get_error_response(f"AI 검증 중 오류가 발생했습니다: {str(e)}")


def _get_error_response(error_message: str) -> dict:
    """에러 발생 시 반환할 기본 응답"""
    return {
        "is_valid": False,
        "factual_accuracy": {"score": 0, "issues": ["AI 검증 실패"]},
        "logical_consistency": {"score": 0, "issues": ["AI 검증 실패"]},
        "title_relevance": {"score": 0, "issues": ["AI 검증 실패"]},
        "overall_feedback": error_message
    }


def _parse_validation_response(response_text: str) -> dict:
    """
    Parse AI validation response with improved JSON extraction.

    중괄호 카운팅 방식으로 정확한 JSON 객체 추출
    """
    try:
        text = response_text.strip()

        # 코드 블록 제거
        if text.startswith('```json'):
            text = text[7:].strip()
            if '```' in text:
                text = text[:text.index('```')].strip()
        elif text.startswith('```'):
            text = text[3:].strip()
            if '```' in text:
                text = text[:text.index('```')].strip()

        # JSON 객체 경계 찾기 (중괄호 카운팅)
        if text.startswith('{'):
            brace_count = 0
            for i, char in enumerate(text):
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        text = text[:i+1]
                        break

        result = json.loads(text)

        # Validate structure
        required_keys = [
            'is_valid',
            'factual_accuracy',
            'logical_consistency',
            'title_relevance',
            'overall_feedback'
        ]

        if not all(key in result for key in required_keys):
            logger.warning(f"Missing required keys. Got: {list(result.keys())}")
            raise ValueError("Missing required keys in response")

        return result

    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing failed: {e}")
        logger.debug(f"Raw response text: {response_text[:500]}...")
        raise ValueError(f"AI 응답 JSON 파싱 실패: {str(e)}")
    except Exception as e:
        logger.error(f"Failed to parse validation response: {str(e)}", exc_info=True)
        logger.debug(f"Raw response text: {response_text[:500]}...")
        raise ValueError(f"AI 응답 파싱 실패: {str(e)}")
