#!/usr/bin/env python3
"""
부족한 기능들 상세 분석 스크립트
현재 구현된 기능과 누락된 기능들을 체계적으로 분석
"""

import os
import json
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class FeatureAnalysis:
    category: str
    feature_name: str
    current_status: str  # implemented, partial, missing, planned
    priority: str  # critical, high, medium, low
    complexity: str  # simple, medium, complex
    description: str
    current_implementation: Optional[str] = None
    missing_components: List[str] = None
    recommended_approach: Optional[str] = None
    estimated_effort: Optional[str] = None
    dependencies: List[str] = None
    user_impact: str = "medium"
    business_value: str = "medium"

    def __post_init__(self):
        if self.missing_components is None:
            self.missing_components = []
        if self.dependencies is None:
            self.dependencies = []


class MissingFeaturesAnalyzer:
    """부족한 기능 분석기"""
    
    def __init__(self, project_root: str):
        self.project_root = project_root
        self.features: List[FeatureAnalysis] = []
        self.analysis_time = datetime.now()
        
    def analyze_authentication_features(self):
        """인증 관련 기능 분석"""
        print("🔐 인증 및 보안 기능 분석")
        
        features = [
            FeatureAnalysis(
                category="Authentication",
                feature_name="이메일 인증",
                current_status="missing",
                priority="high",
                complexity="medium",
                description="사용자 등록 시 이메일 인증을 통한 계정 활성화",
                missing_components=[
                    "이메일 인증 토큰 생성",
                    "이메일 발송 시스템",
                    "인증 완료 페이지",
                    "재발송 기능"
                ],
                recommended_approach="Django의 이메일 백엔드와 Celery를 활용한 비동기 이메일 발송",
                estimated_effort="3-5일",
                dependencies=["SMTP 설정", "Celery 작업"],
                user_impact="high",
                business_value="high"
            ),
            FeatureAnalysis(
                category="Authentication",
                feature_name="비밀번호 재설정",
                current_status="missing",
                priority="high",
                complexity="medium",
                description="이메일을 통한 비밀번호 재설정 기능",
                missing_components=[
                    "비밀번호 재설정 토큰",
                    "재설정 이메일 템플릿",
                    "새 비밀번호 설정 페이지",
                    "보안 검증"
                ],
                recommended_approach="Django의 기본 패스워드 리셋 기능 확장",
                estimated_effort="2-3일",
                user_impact="high",
                business_value="high"
            ),
            FeatureAnalysis(
                category="Authentication",
                feature_name="소셜 로그인",
                current_status="missing",
                priority="medium",
                complexity="complex",
                description="Google, GitHub 등 소셜 계정을 통한 로그인",
                missing_components=[
                    "OAuth 통합",
                    "소셜 계정 연결 관리",
                    "기존 계정 병합",
                    "소셜 로그인 UI"
                ],
                recommended_approach="django-allauth 라이브러리 활용",
                estimated_effort="5-7일",
                dependencies=["OAuth 앱 등록", "SSL 인증서"],
                user_impact="medium",
                business_value="medium"
            ),
            FeatureAnalysis(
                category="Authentication",
                feature_name="2단계 인증 (2FA)",
                current_status="missing",
                priority="medium",
                complexity="complex",
                description="TOTP 또는 SMS를 통한 2단계 인증",
                missing_components=[
                    "TOTP 생성/검증",
                    "QR 코드 생성",
                    "백업 코드",
                    "SMS 인증 (선택)"
                ],
                recommended_approach="django-otp 라이브러리 활용",
                estimated_effort="4-6일",
                user_impact="low",
                business_value="medium"
            )
        ]
        
        self.features.extend(features)
        print(f"   ✅ {len(features)}개 인증 기능 분석 완료")
    
    def analyze_content_features(self):
        """콘텐츠 관련 기능 분석"""
        print("📝 콘텐츠 관리 기능 분석")
        
        features = [
            FeatureAnalysis(
                category="Content Management",
                feature_name="콘텐츠 태그 시스템",
                current_status="missing",
                priority="high",
                complexity="medium",
                description="콘텐츠에 태그를 추가하여 분류 및 검색 개선",
                missing_components=[
                    "Tag 모델",
                    "태그 자동완성",
                    "태그별 필터링",
                    "태그 클라우드",
                    "인기 태그 표시"
                ],
                recommended_approach="Many-to-Many 관계로 Tag 모델 구현",
                estimated_effort="3-4일",
                user_impact="high",
                business_value="high"
            ),
            FeatureAnalysis(
                category="Content Management",
                feature_name="파일 첨부 시스템",
                current_status="missing",
                priority="medium",
                complexity="complex",
                description="이미지, PDF, 문서 등 파일을 콘텐츠에 첨부",
                missing_components=[
                    "파일 업로드 API",
                    "파일 타입 검증",
                    "이미지 리사이징",
                    "파일 저장소 관리",
                    "첨부파일 뷰어"
                ],
                recommended_approach="Django FileField와 클라우드 스토리지 연동",
                estimated_effort="5-7일",
                dependencies=["AWS S3 또는 클라우드 스토리지"],
                user_impact="medium",
                business_value="medium"
            ),
            FeatureAnalysis(
                category="Content Management",
                feature_name="콘텐츠 버전 관리",
                current_status="missing",
                priority="medium",
                complexity="complex",
                description="콘텐츠 수정 이력 추적 및 이전 버전 복원",
                missing_components=[
                    "버전 히스토리 모델",
                    "변경사항 diff 뷰",
                    "버전 복원 기능",
                    "변경 알림"
                ],
                recommended_approach="django-reversion 라이브러리 활용",
                estimated_effort="4-5일",
                user_impact="medium",
                business_value="low"
            ),
            FeatureAnalysis(
                category="Content Management",
                feature_name="콘텐츠 공유 기능",
                current_status="missing",
                priority="medium",
                complexity="medium",
                description="다른 사용자와 콘텐츠 공유 및 협업",
                missing_components=[
                    "공유 권한 관리",
                    "공유 링크 생성",
                    "댓글 시스템",
                    "공동 편집"
                ],
                recommended_approach="권한 기반 공유 시스템 구현",
                estimated_effort="6-8일",
                user_impact="medium",
                business_value="high"
            ),
            FeatureAnalysis(
                category="Content Management",
                feature_name="고급 검색 기능",
                current_status="partial",
                priority="high",
                complexity="complex",
                description="전문 검색, 필터링, 정렬 기능",
                current_implementation="기본적인 제목/내용 검색만 구현됨",
                missing_components=[
                    "전문 검색 (Full-text search)",
                    "고급 필터 (날짜, 태그, 카테고리 조합)",
                    "검색 결과 하이라이팅",
                    "검색 자동완성",
                    "저장된 검색",
                    "검색 통계"
                ],
                recommended_approach="PostgreSQL의 Full-text search 또는 Elasticsearch 도입",
                estimated_effort="5-8일",
                dependencies=["검색 엔진 설정"],
                user_impact="high",
                business_value="high"
            ),
            FeatureAnalysis(
                category="Content Management",
                feature_name="콘텐츠 템플릿",
                current_status="missing",
                priority="low",
                complexity="medium",
                description="자주 사용하는 콘텐츠 형식을 템플릿으로 저장",
                missing_components=[
                    "템플릿 모델",
                    "템플릿 선택 UI",
                    "템플릿 편집기",
                    "공유 템플릿"
                ],
                recommended_approach="Template 모델과 변수 치환 시스템",
                estimated_effort="3-4일",
                user_impact="low",
                business_value="low"
            )
        ]
        
        self.features.extend(features)
        print(f"   ✅ {len(features)}개 콘텐츠 기능 분석 완료")
    
    def analyze_review_features(self):
        """복습 시스템 기능 분석"""
        print("🧠 복습 시스템 기능 분석")
        
        features = [
            FeatureAnalysis(
                category="Review System",
                feature_name="적응형 복습 알고리즘",
                current_status="partial",
                priority="high",
                complexity="complex",
                description="사용자 학습 패턴에 따른 개인화된 복습 간격",
                current_implementation="고정된 간격 기반 spaced repetition",
                missing_components=[
                    "사용자별 학습 성과 분석",
                    "동적 난이도 조정",
                    "개인화된 간격 계산",
                    "학습 효율성 최적화"
                ],
                recommended_approach="ML 기반 개인화 알고리즘 또는 SuperMemo SM-2+ 알고리즘",
                estimated_effort="8-12일",
                dependencies=["학습 데이터 수집", "ML 라이브러리"],
                user_impact="high",
                business_value="high"
            ),
            FeatureAnalysis(
                category="Review System",
                feature_name="복습 모드 다양화",
                current_status="partial",
                priority="medium",
                complexity="medium",
                description="플래시카드, 퀴즈, 빈칸 채우기 등 다양한 복습 방식",
                current_implementation="기본적인 Q&A 방식만 지원",
                missing_components=[
                    "플래시카드 모드",
                    "객관식 퀴즈",
                    "빈칸 채우기",
                    "매칭 게임",
                    "타이핑 연습"
                ],
                recommended_approach="복습 모드별 컴포넌트 개발",
                estimated_effort="6-8일",
                user_impact="high",
                business_value="medium"
            ),
            FeatureAnalysis(
                category="Review System",
                feature_name="복습 성과 예측",
                current_status="missing",
                priority="medium",
                complexity="complex",
                description="학습 진도와 성과를 예측하여 학습 계획 제안",
                missing_components=[
                    "학습 성과 모델링",
                    "진도 예측 알고리즘",
                    "목표 달성 예상 시간",
                    "학습 계획 추천"
                ],
                recommended_approach="통계 모델 기반 예측 시스템",
                estimated_effort="10-14일",
                dependencies=["충분한 학습 데이터"],
                user_impact="medium",
                business_value="medium"
            ),
            FeatureAnalysis(
                category="Review System",
                feature_name="복습 알림 시스템",
                current_status="partial",
                priority="medium",
                complexity="medium",
                description="다양한 채널을 통한 복습 알림",
                current_implementation="기본적인 일일 알림만 구현",
                missing_components=[
                    "푸시 알림 (웹, 모바일)",
                    "이메일 알림 커스터마이징",
                    "SMS 알림",
                    "Slack/Discord 연동",
                    "알림 스케줄링"
                ],
                recommended_approach="다중 채널 알림 시스템 구축",
                estimated_effort="4-6일",
                dependencies=["푸시 알림 서비스", "외부 API"],
                user_impact="medium",
                business_value="medium"
            ),
            FeatureAnalysis(
                category="Review System",
                feature_name="그룹 학습 기능",
                current_status="missing",
                priority="low",
                complexity="complex",
                description="그룹으로 함께 학습하고 경쟁하는 기능",
                missing_components=[
                    "학습 그룹 생성/관리",
                    "그룹 진도 비교",
                    "그룹 챌린지",
                    "리더보드",
                    "그룹 채팅"
                ],
                recommended_approach="소셜 학습 플랫폼 구조",
                estimated_effort="12-16일",
                user_impact="low",
                business_value="medium"
            )
        ]
        
        self.features.extend(features)
        print(f"   ✅ {len(features)}개 복습 기능 분석 완료")
    
    def analyze_analytics_features(self):
        """분석 및 대시보드 기능 분석"""
        print("📊 분석 및 대시보드 기능 분석")
        
        features = [
            FeatureAnalysis(
                category="Analytics",
                feature_name="고급 학습 분석",
                current_status="partial",
                priority="high",
                complexity="medium",
                description="상세한 학습 패턴 분석 및 인사이트 제공",
                current_implementation="기본적인 성공률과 복습 횟수만 표시",
                missing_components=[
                    "학습 시간 패턴 분석",
                    "어려운 콘텐츠 식별",
                    "학습 효율성 메트릭",
                    "개인화된 인사이트",
                    "학습 목표 대비 진도"
                ],
                recommended_approach="데이터 분석 기반 인사이트 엔진",
                estimated_effort="6-8일",
                user_impact="high",
                business_value="high"
            ),
            FeatureAnalysis(
                category="Analytics",
                feature_name="학습 캘린더 히트맵",
                current_status="missing",
                priority="medium",
                complexity="medium",
                description="GitHub 스타일의 학습 활동 히트맵",
                missing_components=[
                    "일별 학습 활동 데이터",
                    "히트맵 시각화",
                    "연속 학습 스트릭",
                    "월별/연별 뷰",
                    "목표 달성률 표시"
                ],
                recommended_approach="D3.js 또는 Chart.js 기반 히트맵",
                estimated_effort="3-4일",
                user_impact="medium",
                business_value="medium"
            ),
            FeatureAnalysis(
                category="Analytics",
                feature_name="학습 리포트 생성",
                current_status="missing",
                priority="medium",
                complexity="medium",
                description="주간/월간 학습 리포트 자동 생성 및 공유",
                missing_components=[
                    "리포트 템플릿",
                    "자동 리포트 생성",
                    "PDF 내보내기",
                    "이메일 발송",
                    "리포트 커스터마이징"
                ],
                recommended_approach="리포트 생성기와 PDF 라이브러리 연동",
                estimated_effort="5-6일",
                dependencies=["PDF 생성 라이브러리"],
                user_impact="medium",
                business_value="low"
            ),
            FeatureAnalysis(
                category="Analytics",
                feature_name="비교 분석 기능",
                current_status="missing",
                priority="low",
                complexity="medium",
                description="다른 사용자나 기간과의 학습 성과 비교",
                missing_components=[
                    "익명화된 사용자 비교",
                    "기간별 성과 비교",
                    "벤치마크 데이터",
                    "개선 제안"
                ],
                recommended_approach="통계 기반 비교 분석 시스템",
                estimated_effort="4-5일",
                user_impact="low",
                business_value="low"
            )
        ]
        
        self.features.extend(features)
        print(f"   ✅ {len(features)}개 분석 기능 분석 완료")
    
    def analyze_user_experience_features(self):
        """사용자 경험 기능 분석"""
        print("🎨 사용자 경험 기능 분석")
        
        features = [
            FeatureAnalysis(
                category="User Experience",
                feature_name="다크 모드",
                current_status="missing",
                priority="medium",
                complexity="simple",
                description="다크 테마 지원으로 야간 학습 환경 개선",
                missing_components=[
                    "다크 테마 CSS",
                    "테마 토글 버튼",
                    "테마 설정 저장",
                    "시스템 설정 연동"
                ],
                recommended_approach="CSS 변수와 테마 컨텍스트 활용",
                estimated_effort="2-3일",
                user_impact="medium",
                business_value="low"
            ),
            FeatureAnalysis(
                category="User Experience",
                feature_name="키보드 단축키",
                current_status="partial",
                priority="medium",
                complexity="medium",
                description="복습 진행과 탐색을 위한 키보드 단축키",
                current_implementation="복습 화면에서 기본적인 단축키만 지원",
                missing_components=[
                    "전역 단축키",
                    "커스터마이징 가능한 키 바인딩",
                    "단축키 도움말",
                    "vim 스타일 네비게이션"
                ],
                recommended_approach="키보드 이벤트 핸들러와 설정 시스템",
                estimated_effort="3-4일",
                user_impact="medium",
                business_value="low"
            ),
            FeatureAnalysis(
                category="User Experience",
                feature_name="오프라인 지원",
                current_status="missing",
                priority="medium",
                complexity="complex",
                description="오프라인 상태에서도 학습 가능한 PWA 기능",
                missing_components=[
                    "서비스 워커",
                    "오프라인 데이터 캐싱",
                    "오프라인 표시기",
                    "데이터 동기화",
                    "PWA 매니페스트"
                ],
                recommended_approach="Progressive Web App (PWA) 구현",
                estimated_effort="8-10일",
                dependencies=["HTTPS 설정"],
                user_impact="high",
                business_value="medium"
            ),
            FeatureAnalysis(
                category="User Experience",
                feature_name="모바일 앱",
                current_status="missing",
                priority="medium",
                complexity="complex",
                description="네이티브 모바일 앱 또는 하이브리드 앱",
                missing_components=[
                    "모바일 앱 개발",
                    "푸시 알림",
                    "오프라인 동기화",
                    "모바일 최적화 UI",
                    "앱스토어 배포"
                ],
                recommended_approach="React Native 또는 Flutter 활용",
                estimated_effort="20-30일",
                dependencies=["모바일 개발 환경"],
                user_impact="high",
                business_value="high"
            ),
            FeatureAnalysis(
                category="User Experience",
                feature_name="접근성 개선",
                current_status="partial",
                priority="medium",
                complexity="medium",
                description="시각, 청각, 운동 장애인을 위한 접근성 기능",
                current_implementation="기본적인 semantic HTML과 ARIA만 적용",
                missing_components=[
                    "스크린 리더 최적화",
                    "고대비 모드",
                    "큰 글씨 모드",
                    "키보드 전용 네비게이션",
                    "음성 명령 지원"
                ],
                recommended_approach="WCAG 2.1 가이드라인 준수",
                estimated_effort="5-7일",
                user_impact="medium",
                business_value="medium"
            ),
            FeatureAnalysis(
                category="User Experience",
                feature_name="국제화 (i18n)",
                current_status="missing",
                priority="low",
                complexity="medium",
                description="다국어 지원으로 글로벌 사용자 확대",
                missing_components=[
                    "다국어 리소스 관리",
                    "언어 감지 및 설정",
                    "RTL 언어 지원",
                    "날짜/시간 현지화",
                    "숫자 형식 현지화"
                ],
                recommended_approach="React i18next와 Django i18n 활용",
                estimated_effort="6-8일",
                user_impact="low",
                business_value="medium"
            )
        ]
        
        self.features.extend(features)
        print(f"   ✅ {len(features)}개 UX 기능 분석 완료")
    
    def analyze_technical_features(self):
        """기술적 기능 분석"""
        print("⚙️ 기술적 기능 분석")
        
        features = [
            FeatureAnalysis(
                category="Technical",
                feature_name="실시간 알림",
                current_status="missing",
                priority="medium",
                complexity="complex",
                description="WebSocket을 통한 실시간 알림 및 업데이트",
                missing_components=[
                    "WebSocket 서버",
                    "실시간 알림 시스템",
                    "연결 관리",
                    "알림 큐",
                    "클라이언트 재연결 로직"
                ],
                recommended_approach="Django Channels와 Redis 활용",
                estimated_effort="6-8일",
                dependencies=["WebSocket 지원", "Redis 설정"],
                user_impact="medium",
                business_value="medium"
            ),
            FeatureAnalysis(
                category="Technical",
                feature_name="API 버전 관리",
                current_status="missing",
                priority="low",
                complexity="medium",
                description="API 하위 호환성과 점진적 업그레이드 지원",
                missing_components=[
                    "API 버전 라우팅",
                    "하위 호환성 유지",
                    "버전별 문서화",
                    "deprecation 경고"
                ],
                recommended_approach="URL path 기반 버전 관리",
                estimated_effort="3-4일",
                user_impact="low",
                business_value="low"
            ),
            FeatureAnalysis(
                category="Technical",
                feature_name="API 속도 제한 고도화",
                current_status="partial",
                priority="medium",
                complexity="medium",
                description="정교한 rate limiting과 사용량 모니터링",
                current_implementation="기본적인 rate limiting만 구현",
                missing_components=[
                    "사용자별 할당량",
                    "동적 속도 제한",
                    "API 사용량 대시보드",
                    "abuse 감지"
                ],
                recommended_approach="Redis 기반 고급 rate limiting",
                estimated_effort="4-5일",
                user_impact="low",
                business_value="medium"
            ),
            FeatureAnalysis(
                category="Technical",
                feature_name="데이터 백업 및 복원",
                current_status="missing",
                priority="high",
                complexity="medium",
                description="자동화된 데이터 백업과 재해 복구 시스템",
                missing_components=[
                    "자동 백업 스케줄링",
                    "증분 백업",
                    "백업 검증",
                    "복원 프로세스",
                    "오프사이트 백업"
                ],
                recommended_approach="PostgreSQL 백업과 클라우드 스토리지 연동",
                estimated_effort="4-6일",
                dependencies=["클라우드 스토리지", "백업 도구"],
                user_impact="low",
                business_value="high"
            ),
            FeatureAnalysis(
                category="Technical",
                feature_name="성능 모니터링",
                current_status="missing",
                priority="medium",
                complexity="medium",
                description="애플리케이션 성능 모니터링 및 알림",
                missing_components=[
                    "성능 메트릭 수집",
                    "알림 시스템",
                    "성능 대시보드",
                    "병목 지점 식별",
                    "자동 스케일링 연동"
                ],
                recommended_approach="APM 도구 연동 (Sentry, DataDog 등)",
                estimated_effort="3-5일",
                dependencies=["모니터링 서비스"],
                user_impact="low",
                business_value="medium"
            ),
            FeatureAnalysis(
                category="Technical",
                feature_name="검색 엔진 최적화",
                current_status="missing",
                priority="low",
                complexity="medium",
                description="공개 콘텐츠의 SEO 최적화",
                missing_components=[
                    "메타 태그 최적화",
                    "sitemap 생성",
                    "structured data",
                    "Open Graph 태그",
                    "robots.txt"
                ],
                recommended_approach="SEO 최적화 미들웨어와 템플릿",
                estimated_effort="3-4일",
                user_impact="low",
                business_value="low"
            )
        ]
        
        self.features.extend(features)
        print(f"   ✅ {len(features)}개 기술 기능 분석 완료")
    
    def analyze_ai_features(self):
        """AI 및 자동화 기능 분석"""
        print("🤖 AI 및 자동화 기능 분석")
        
        features = [
            FeatureAnalysis(
                category="AI & Automation",
                feature_name="콘텐츠 자동 요약",
                current_status="missing",
                priority="medium",
                complexity="complex",
                description="긴 콘텐츠의 핵심 내용을 자동으로 요약",
                missing_components=[
                    "텍스트 요약 AI 모델",
                    "요약 품질 평가",
                    "사용자 피드백 학습",
                    "다국어 요약 지원"
                ],
                recommended_approach="Transformer 기반 요약 모델 또는 OpenAI API",
                estimated_effort="8-12일",
                dependencies=["AI 모델 또는 API", "GPU 리소스"],
                user_impact="medium",
                business_value="medium"
            ),
            FeatureAnalysis(
                category="AI & Automation",
                feature_name="스마트 복습 추천",
                current_status="missing",
                priority="high",
                complexity="complex",
                description="AI 기반 개인화된 복습 콘텐츠 추천",
                missing_components=[
                    "추천 알고리즘",
                    "학습 패턴 분석",
                    "콘텐츠 유사도 계산",
                    "실시간 추천 업데이트"
                ],
                recommended_approach="협업 필터링과 콘텐츠 기반 추천 하이브리드",
                estimated_effort="10-14일",
                dependencies=["충분한 사용자 데이터"],
                user_impact="high",
                business_value="high"
            ),
            FeatureAnalysis(
                category="AI & Automation",
                feature_name="자동 퀴즈 생성",
                current_status="missing",
                priority="medium",
                complexity="complex",
                description="콘텐츠를 기반으로 자동으로 퀴즈 문제 생성",
                missing_components=[
                    "질문 생성 AI",
                    "정답/오답 생성",
                    "난이도 조절",
                    "문제 품질 검증"
                ],
                recommended_approach="GPT 기반 질문 생성 또는 전용 모델",
                estimated_effort="12-16일",
                dependencies=["대용량 언어 모델"],
                user_impact="high",
                business_value="medium"
            ),
            FeatureAnalysis(
                category="AI & Automation",
                feature_name="학습 패턴 분석",
                current_status="missing",
                priority="medium",
                complexity="complex",
                description="사용자 행동 분석을 통한 학습 최적화 제안",
                missing_components=[
                    "행동 패턴 추적",
                    "이상 패턴 감지",
                    "개선 제안 생성",
                    "예측 모델링"
                ],
                recommended_approach="시계열 분석과 머신러닝 모델",
                estimated_effort="8-10일",
                user_impact="medium",
                business_value="medium"
            ),
            FeatureAnalysis(
                category="AI & Automation",
                feature_name="음성 인식 복습",
                current_status="missing",
                priority="low",
                complexity="complex",
                description="음성으로 답변하고 발음을 평가하는 기능",
                missing_components=[
                    "음성 인식 엔진",
                    "발음 평가",
                    "음성 데이터 처리",
                    "실시간 피드백"
                ],
                recommended_approach="Web Speech API 또는 Google Speech-to-Text",
                estimated_effort="10-12일",
                dependencies=["음성 인식 서비스"],
                user_impact="low",
                business_value="low"
            )
        ]
        
        self.features.extend(features)
        print(f"   ✅ {len(features)}개 AI 기능 분석 완료")
    
    def generate_priority_matrix(self) -> Dict:
        """우선순위 매트릭스 생성"""
        matrix = {
            "critical": {"high": [], "medium": [], "low": []},
            "high": {"high": [], "medium": [], "low": []},
            "medium": {"high": [], "medium": [], "low": []},
            "low": {"high": [], "medium": [], "low": []}
        }
        
        for feature in self.features:
            matrix[feature.priority][feature.user_impact].append(feature)
        
        return matrix
    
    def generate_roadmap(self) -> Dict:
        """개발 로드맵 생성"""
        roadmap = {
            "Phase 1 (즉시 구현 - 1-2주)": [],
            "Phase 2 (단기 - 1개월)": [],
            "Phase 3 (중기 - 3개월)": [],
            "Phase 4 (장기 - 6개월+)": []
        }
        
        # 우선순위와 복잡도를 기반으로 페이즈 분류
        for feature in self.features:
            if feature.priority == "critical" or (feature.priority == "high" and feature.complexity == "simple"):
                roadmap["Phase 1 (즉시 구현 - 1-2주)"].append(feature)
            elif feature.priority == "high" and feature.complexity in ["medium", "complex"]:
                roadmap["Phase 2 (단기 - 1개월)"].append(feature)
            elif feature.priority == "medium":
                roadmap["Phase 3 (중기 - 3개월)"].append(feature)
            else:
                roadmap["Phase 4 (장기 - 6개월+)"].append(feature)
        
        return roadmap
    
    def generate_effort_estimation(self) -> Dict:
        """개발 공수 추정"""
        effort_by_category = {}
        total_effort = {"simple": 0, "medium": 0, "complex": 0}
        
        for feature in self.features:
            category = feature.category
            if category not in effort_by_category:
                effort_by_category[category] = {"simple": 0, "medium": 0, "complex": 0}
            
            effort_by_category[category][feature.complexity] += 1
            total_effort[feature.complexity] += 1
        
        return {
            "by_category": effort_by_category,
            "total": total_effort,
            "estimated_days": {
                "simple": total_effort["simple"] * 2,  # 평균 2일
                "medium": total_effort["medium"] * 5,  # 평균 5일
                "complex": total_effort["complex"] * 10  # 평균 10일
            }
        }
    
    def generate_report(self) -> Dict:
        """종합 리포트 생성"""
        print("\n📋 분석 리포트 생성 중...")
        
        # 통계 계산
        total_features = len(self.features)
        status_counts = {}
        priority_counts = {}
        complexity_counts = {}
        category_counts = {}
        
        for feature in self.features:
            # 상태별 집계
            status = feature.current_status
            status_counts[status] = status_counts.get(status, 0) + 1
            
            # 우선순위별 집계
            priority = feature.priority
            priority_counts[priority] = priority_counts.get(priority, 0) + 1
            
            # 복잡도별 집계
            complexity = feature.complexity
            complexity_counts[complexity] = complexity_counts.get(complexity, 0) + 1
            
            # 카테고리별 집계
            category = feature.category
            category_counts[category] = category_counts.get(category, 0) + 1
        
        priority_matrix = self.generate_priority_matrix()
        roadmap = self.generate_roadmap()
        effort_estimation = self.generate_effort_estimation()
        
        report = {
            "analysis_info": {
                "timestamp": self.analysis_time.isoformat(),
                "total_features_analyzed": total_features,
                "analyzer_version": "1.0"
            },
            "summary": {
                "status_distribution": status_counts,
                "priority_distribution": priority_counts,
                "complexity_distribution": complexity_counts,
                "category_distribution": category_counts
            },
            "features": [asdict(feature) for feature in self.features],
            "priority_matrix": {
                priority: {
                    impact: [asdict(f) for f in features]
                    for impact, features in impacts.items()
                }
                for priority, impacts in priority_matrix.items()
            },
            "development_roadmap": {
                phase: [asdict(f) for f in features]
                for phase, features in roadmap.items()
            },
            "effort_estimation": effort_estimation,
            "recommendations": {
                "immediate_actions": [
                    "이메일 인증 시스템 구현 (보안 향상)",
                    "콘텐츠 태그 시스템 구현 (사용성 향상)",
                    "고급 검색 기능 구현 (사용자 경험 향상)",
                    "적응형 복습 알고리즘 연구 시작 (핵심 차별화 요소)"
                ],
                "quick_wins": [
                    "다크 모드 구현 (2-3일, 사용자 만족도 향상)",
                    "키보드 단축키 확장 (3-4일, 파워 유저 만족도)",
                    "학습 캘린더 히트맵 (3-4일, 동기부여 향상)"
                ],
                "strategic_investments": [
                    "PWA 오프라인 지원 (모바일 사용성)",
                    "AI 기반 콘텐츠 추천 (개인화)",
                    "모바일 앱 개발 (사용자 확대)"
                ]
            }
        }
        
        return report
    
    def run_analysis(self):
        """전체 분석 실행"""
        print("🔍 부족한 기능들 상세 분석 시작")
        print("=" * 60)
        
        # 각 카테고리별 분석 실행
        self.analyze_authentication_features()
        self.analyze_content_features()
        self.analyze_review_features()
        self.analyze_analytics_features()
        self.analyze_user_experience_features()
        self.analyze_technical_features()
        self.analyze_ai_features()
        
        # 리포트 생성
        report = self.generate_report()
        
        # 파일로 저장
        output_file = os.path.join(self.project_root, 'missing_features_analysis.json')
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 상세 분석 리포트가 '{output_file}'에 저장되었습니다.")
        
        # 요약 출력
        self.print_summary(report)
        
        return report
    
    def print_summary(self, report: Dict):
        """분석 요약 출력"""
        print("\n" + "=" * 60)
        print("📋 분석 결과 요약:")
        print(f"   📊 총 분석된 기능: {report['analysis_info']['total_features_analyzed']}개")
        
        print(f"\n📈 상태별 분포:")
        for status, count in report['summary']['status_distribution'].items():
            print(f"   - {status}: {count}개")
        
        print(f"\n🎯 우선순위별 분포:")
        for priority, count in report['summary']['priority_distribution'].items():
            print(f"   - {priority}: {count}개")
        
        print(f"\n⚙️ 복잡도별 분포:")
        for complexity, count in report['summary']['complexity_distribution'].items():
            print(f"   - {complexity}: {count}개")
        
        print(f"\n📂 카테고리별 분포:")
        for category, count in report['summary']['category_distribution'].items():
            print(f"   - {category}: {count}개")
        
        print(f"\n⏱️ 예상 개발 기간:")
        estimated_days = report['effort_estimation']['estimated_days']
        total_days = sum(estimated_days.values())
        print(f"   - 간단한 기능: {estimated_days['simple']}일")
        print(f"   - 중간 기능: {estimated_days['medium']}일")
        print(f"   - 복잡한 기능: {estimated_days['complex']}일")
        print(f"   - 총 예상 기간: {total_days}일 ({total_days//20:.1f}개월)")
        
        print(f"\n🚀 즉시 실행 권장사항:")
        for action in report['recommendations']['immediate_actions']:
            print(f"   • {action}")


def main():
    """메인 함수"""
    print("🔍 Resee 프로젝트 부족한 기능 분석")
    print("현재 구현된 기능과 누락된 기능들을 체계적으로 분석합니다.")
    
    project_root = "/mnt/c/mypojects/Resee"
    analyzer = MissingFeaturesAnalyzer(project_root)
    
    try:
        report = analyzer.run_analysis()
        
        print("\n✅ 분석이 완료되었습니다!")
        print("📋 상세한 내용은 'missing_features_analysis.json' 파일을 확인하세요.")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ 분석 중 오류가 발생했습니다: {str(e)}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)