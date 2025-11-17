"""
Google OAuth 인증 처리
"""
import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from google.auth.transport import requests
from google.oauth2 import id_token
from rest_framework import serializers

User = get_user_model()
logger = logging.getLogger(__name__)


class GoogleOAuthError(Exception):
    """Google OAuth 관련 에러"""


class GoogleAuthService:
    """Google OAuth 인증 서비스"""

    @staticmethod
    def verify_google_token(token: str) -> dict:
        """
        Google ID 토큰을 검증하고 사용자 정보를 반환

        Args:
            token: Google ID 토큰

        Returns:
            dict: 검증된 사용자 정보

        Raises:
            GoogleOAuthError: 토큰 검증 실패시
        """
        try:
            # Google 클라이언트 ID
            client_id = settings.SOCIALACCOUNT_PROVIDERS['google']['APP']['client_id']

            if not client_id:
                raise GoogleOAuthError("Google OAuth client ID가 설정되지 않았습니다.")

            # 토큰 검증
            idinfo = id_token.verify_oauth2_token(
                token,
                requests.Request(),
                client_id
            )

            # 발급자 확인
            if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
                raise GoogleOAuthError("잘못된 토큰 발급자입니다.")

            logger.info(f"Google OAuth 검증 성공: {idinfo.get('email')}")
            return idinfo

        except ValueError as e:
            logger.error(f"Google OAuth 토큰 검증 실패: {str(e)}")
            raise GoogleOAuthError(f"토큰 검증 실패: {str(e)}")
        except Exception as e:
            logger.error(f"Google OAuth 오류: {str(e)}")
            raise GoogleOAuthError(f"인증 처리 중 오류: {str(e)}")

    @staticmethod
    def get_or_create_user(google_user_info: dict) -> tuple[User, bool]:
        """
        Google 사용자 정보로 사용자를 찾거나 생성

        Args:
            google_user_info: Google에서 받은 사용자 정보

        Returns:
            tuple: (User 객체, 생성 여부)
        """
        email = google_user_info.get('email')
        if not email:
            raise GoogleOAuthError("Google 계정에서 이메일을 가져올 수 없습니다.")

        try:
            # 기존 사용자 찾기
            user = User.objects.get(email=email)
            logger.info(f"기존 사용자 로그인: {email}")

            # Google OAuth로 로그인하는 사용자는 이미 이메일이 인증됨
            if not user.is_email_verified:
                user.is_email_verified = True
                user.save()
                logger.info(f"Google OAuth 사용자 이메일 인증 완료: {email}")

            return user, False

        except User.DoesNotExist:
            # 새 사용자 생성
            first_name = google_user_info.get('given_name', '')
            last_name = google_user_info.get('family_name', '')
            name = google_user_info.get('name', '')

            # 이름이 없으면 name에서 추출 시도
            if not first_name and not last_name and name:
                name_parts = name.split(' ', 1)
                first_name = name_parts[0]
                if len(name_parts) > 1:
                    last_name = name_parts[1]

            user = User.objects.create_user(
                email=email,
                first_name=first_name,
                last_name=last_name,
                is_email_verified=True,  # Google 계정은 이미 인증됨
            )

            logger.info(f"Google OAuth 신규 사용자 생성: {email}")
            return user, True


class GoogleAuthSerializer(serializers.Serializer):
    """Google OAuth 인증 시리얼라이저"""
    token = serializers.CharField(required=True, help_text="Google ID 토큰")

    def validate_token(self, value):
        """토큰 검증"""
        if not value:
            raise serializers.ValidationError("Google 토큰이 필요합니다.")

        try:
            # Google 토큰 검증
            google_user_info = GoogleAuthService.verify_google_token(value)

            # 사용자 찾거나 생성
            user, created = GoogleAuthService.get_or_create_user(google_user_info)

            # 검증된 데이터에 사용자 정보 추가
            self._user = user
            self._created = created
            self._google_user_info = google_user_info

            return value

        except GoogleOAuthError as e:
            raise serializers.ValidationError(str(e))
        except Exception as e:
            logger.error(f"Google OAuth 처리 오류: {str(e)}")
            raise serializers.ValidationError("Google 인증 처리 중 오류가 발생했습니다.")

    def get_user(self):
        """인증된 사용자 반환"""
        return getattr(self, '_user', None)

    def is_new_user(self):
        """신규 사용자 여부"""
        return getattr(self, '_created', False)

    def get_google_user_info(self):
        """Google 사용자 정보 반환"""
        return getattr(self, '_google_user_info', {})
