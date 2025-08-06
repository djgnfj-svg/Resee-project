#!/usr/bin/env python
print('=== Claude API 연결 테스트 ===')
try:
    from ai_review.services import ClaudeService
    service = ClaudeService()
    
    # API 키 상태 확인
    api_key = service.client.api_key
    has_api_key = api_key and api_key != 'test-key'
    print('API Key 설정: ', 'Yes' if has_api_key else 'No')
    
    if has_api_key:
        # 간단한 테스트 메시지
        messages = [{'role': 'user', 'content': '테스트 메시지입니다. 짧게 대답해주세요.'}]
        
        # 실제 API 호출 테스트
        response, time_ms = service._make_api_call(messages, temperature=0.3, max_tokens=50)
        print('API 호출 성공!')
        print('응답:', response[:200])
        print('응답 시간:', time_ms, 'ms')
    else:
        print('API 키가 설정되지 않았습니다.')
        
except Exception as e:
    print('Claude API 테스트 실패:', str(e))