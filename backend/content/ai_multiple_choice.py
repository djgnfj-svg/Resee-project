"""
AI-powered multiple choice generation module.
Generates 4-choice quiz options based on content.
"""

import os
import json
import logging
from anthropic import Anthropic

logger = logging.getLogger(__name__)


def generate_multiple_choice_options(title: str, content: str) -> dict:
    """
    Generate multiple choice options based on content.
    User will see the content and choose the correct title from 4 options.

    Args:
        title: Correct title (answer)
        content: Content body (markdown)

    Returns:
        dict: {
            "choices": ["제목1", "제목2", "제목3", "제목4"],
            "correct_answer": "제목1"  # Same as title parameter
        }
    """
    client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

    prompt = f"""당신은 학습 콘텐츠 기반 객관식 문제 생성 전문가입니다.

다음 학습 콘텐츠의 **내용**을 읽고, 가장 적합한 **제목**을 맞추는 4지선다 문제를 만들어주세요.

**정답 제목**: {title}

**콘텐츠 내용**:
{content[:1500]}{"..." if len(content) > 1500 else ""}

**요구사항**:
1. 정답 제목({title})을 포함하여 총 4개의 보기 생성
2. 오답 3개는 다음 조건을 만족해야 함:
   - 내용과 어느 정도 관련이 있어 보이지만 정답은 아닌 제목
   - 너무 쉽게 구분되지 않도록 (하지만 명확히 틀린 것)
   - 길이와 형식이 정답과 유사
3. 4개 보기의 순서는 랜덤하게 배치 (정답이 항상 첫 번째가 아니도록)

**응답 형식 (JSON만 반환, 다른 텍스트 없이)**:
{{
  "choices": ["제목1", "제목2", "제목3", "제목4"],
  "correct_answer": "{title}"
}}

**예시**:
정답: "파이썬 리스트 기초"
오답: ["파이썬 딕셔너리 활용", "파이썬 문자열 처리", "파이썬 반복문 이해"]

JSON만 반환하세요."""

    try:
        message = client.messages.create(
            model="claude-3-haiku-20240307",  # Fast and cost-efficient
            max_tokens=500,
            temperature=0.7,  # Higher for creative wrong options
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        response_text = message.content[0].text.strip()
        logger.info(f"AI MC generation response: {response_text[:200]}")

        # Parse JSON response
        result = _parse_mc_response(response_text, title)
        return result

    except Exception as e:
        logger.error(f"AI MC generation failed for title '{title[:50]}...': {str(e)}", exc_info=True)
        # Return None on failure - will be handled by caller
        return None


def _parse_mc_response(response_text: str, expected_title: str) -> dict:
    """Parse AI multiple choice response."""
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
        if 'choices' not in result or 'correct_answer' not in result:
            raise ValueError("Missing required keys: choices or correct_answer")

        if not isinstance(result['choices'], list):
            raise ValueError("choices must be a list")

        if len(result['choices']) != 4:
            raise ValueError(f"Must have exactly 4 choices, got {len(result['choices'])}")

        # Verify correct answer is in choices
        if result['correct_answer'] not in result['choices']:
            raise ValueError("correct_answer must be one of the choices")

        # Ensure correct answer matches expected title
        if result['correct_answer'] != expected_title:
            logger.warning(f"AI returned different correct_answer: {result['correct_answer']} vs {expected_title}")
            result['correct_answer'] = expected_title
            # Replace one of the choices with the expected title if not present
            if expected_title not in result['choices']:
                result['choices'][0] = expected_title

        logger.info(f"Successfully generated MC options for: {expected_title}")
        return result

    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing failed: {str(e)}", exc_info=True)
        logger.debug(f"Raw response text: {response_text[:500]}...")
        raise ValueError(f"AI 응답 파싱 실패: {str(e)}")
    except Exception as e:
        logger.error(f"MC response validation failed: {str(e)}")
        raise ValueError(f"객관식 보기 검증 실패: {str(e)}")
