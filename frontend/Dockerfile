FROM node:18-alpine

# 보안 및 성능 최적화
RUN apk add --no-cache \
    curl \
    && addgroup -g 1001 -S nodejs \
    && adduser -S reactapp -u 1001

WORKDIR /app

# package.json 및 package-lock.json 복사 (캐싱 최적화)
COPY package*.json ./
RUN npm ci --silent

# 소스 코드 복사
COPY . .

# 소유권 변경
RUN chown -R reactapp:nodejs /app
USER reactapp

# 헬스체크 추가
HEALTHCHECK --interval=60s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:3000/ || exit 1

# 포트 노출
EXPOSE 3000

# 애플리케이션 시작
CMD ["npm", "start"]