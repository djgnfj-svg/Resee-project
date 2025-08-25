#!/bin/bash

# Resee 빠른 배포 스크립트 (테스트 스킵)
# 개발 중 빠른 배포용

echo "🚀 빠른 배포를 실행합니다..."

# 테스트 스킵하고 배포 실행
SKIP_TESTS=true ./deploy-beta.sh

echo "✅ 빠른 배포 완료!"