"""
AI-powered content validation module.
Validates learning content for factual accuracy, logical consistency, and title relevance.
"""

import os
import json
import logging
from anthropic import Anthropic

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
    client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

    prompt = f"""당신은 학습 자료 검증 전문가입니다. 다음 학습 콘텐츠를 엄격하게 검토해주세요.

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
{{
  "is_valid": true/false (모든 점수가 70점 이상이면 true),
  "factual_accuracy": {{
    "score": 0-100,
    "issues": ["문제점1", "문제점2", ...] (없으면 빈 배열)
  }},
  "logical_consistency": {{
    "score": 0-100,
    "issues": ["문제점1", "문제점2", ...] (없으면 빈 배열)
  }},
  "title_relevance": {{
    "score": 0-100,
    "issues": ["문제점1", "문제점2", ...] (없으면 빈 배열)
  }},
  "overall_feedback": "전체 평가 요약 (2-3문장)"
}}

**평가 기준:**
- 90-100점: 매우 우수, 문제 없음
- 70-89점: 양호, 사소한 개선 필요
- 50-69점: 보통, 중요한 개선 필요
- 0-49점: 부족, 전면 수정 필요

JSON만 반환하세요."""

    try:
        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=2000,
            temperature=0.3,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        response_text = message.content[0].text.strip()
        logger.info(f"AI validation response: {response_text}")

        # Parse JSON response
        result = _parse_validation_response(response_text)
        return result

    except Exception as e:
        logger.error(f"AI validation failed: {str(e)}")
        return {
            "is_valid": False,
            "factual_accuracy": {"score": 0, "issues": ["AI 검증 실패"]},
            "logical_consistency": {"score": 0, "issues": ["AI 검증 실패"]},
            "title_relevance": {"score": 0, "issues": ["AI 검증 실패"]},
            "overall_feedback": f"AI 검증 중 오류가 발생했습니다: {str(e)}"
        }


def _parse_validation_response(response_text: str) -> dict:
    """Parse AI validation response."""
    try:
        # Try to find JSON in response
        if '```json' in response_text:
            start = response_text.find('```json') + 7
            end = response_text.find('```', start)
            response_text = response_text[start:end].strip()
        elif '```' in response_text:
            start = response_text.find('```') + 3
            end = response_text.find('```', start)
            response_text = response_text[start:end].strip()

        result = json.loads(response_text)

        # Validate structure
        required_keys = ['is_valid', 'factual_accuracy', 'logical_consistency', 'title_relevance', 'overall_feedback']
        if not all(key in result for key in required_keys):
            raise ValueError("Missing required keys in response")

        return result

    except Exception as e:
        logger.error(f"Failed to parse validation response: {str(e)}")
        raise ValueError(f"AI 응답 파싱 실패: {str(e)}")
