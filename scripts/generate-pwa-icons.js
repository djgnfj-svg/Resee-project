#!/usr/bin/env node

/**
 * PWA 아이콘 생성 스크립트
 * 
 * 사용법:
 * node scripts/generate-pwa-icons.js
 * 
 * 요구사항:
 * - 1024x1024 크기의 마스터 아이콘이 public/icon-master.png에 있어야 함
 * - sharp 패키지가 설치되어 있어야 함: npm install sharp
 * 
 * 또는 온라인 도구 사용:
 * - https://www.pwabuilder.com/imageGenerator
 * - https://realfavicongenerator.net/
 */

const fs = require('fs');
const path = require('path');

// 필요한 아이콘 크기들
const iconSizes = [
  { size: 72, name: 'icon-72x72.png' },
  { size: 96, name: 'icon-96x96.png' },
  { size: 128, name: 'icon-128x128.png' },
  { size: 144, name: 'icon-144x144.png' },
  { size: 152, name: 'icon-152x152.png' },
  { size: 192, name: 'icon-192x192.png' },
  { size: 384, name: 'icon-384x384.png' },
  { size: 512, name: 'icon-512x512.png' }
];

// 단축키 아이콘들
const shortcutIcons = [
  { name: 'shortcut-new.png', color: '#10b981' }, // green
  { name: 'shortcut-review.png', color: '#3b82f6' }, // blue  
  { name: 'shortcut-stats.png', color: '#8b5cf6' }  // purple
];

const iconsDir = path.join(__dirname, '../frontend/public/icons');
const masterIconPath = path.join(__dirname, '../frontend/public/icon-master.png');

// 디렉토리 생성
if (!fs.existsSync(iconsDir)) {
  fs.mkdirSync(iconsDir, { recursive: true });
}

console.log('🎨 PWA 아이콘 생성 도구');
console.log('====================');

// sharp 설치 확인
try {
  require.resolve('sharp');
  generateIconsWithSharp();
} catch (error) {
  console.log('⚠️  Sharp 패키지가 설치되지 않았습니다.');
  console.log('');
  console.log('방법 1: Sharp를 설치하여 자동 생성');
  console.log('  npm install sharp');
  console.log('  node scripts/generate-pwa-icons.js');
  console.log('');
  console.log('방법 2: 온라인 도구 사용');
  console.log('  1. https://www.pwabuilder.com/imageGenerator 방문');
  console.log('  2. 1024x1024 마스터 아이콘 업로드');
  console.log('  3. 생성된 아이콘들을 frontend/public/icons/ 폴더에 저장');
  console.log('');
  console.log('방법 3: 수동 생성');
  console.log('  다음 크기의 PNG 파일들을 frontend/public/icons/에 생성하세요:');
  iconSizes.forEach(icon => {
    console.log(`  - ${icon.name} (${icon.size}x${icon.size})`);
  });
  
  // 기본 플레이스홀더 아이콘들 생성
  generatePlaceholderIcons();
}

function generateIconsWithSharp() {
  const sharp = require('sharp');
  
  if (!fs.existsSync(masterIconPath)) {
    console.error(`❌ 마스터 아이콘을 찾을 수 없습니다: ${masterIconPath}`);
    console.log('1024x1024 크기의 마스터 아이콘을 public/icon-master.png로 저장하세요.');
    return;
  }
  
  console.log('✅ Sharp를 사용하여 아이콘 생성 중...');
  
  Promise.all(
    iconSizes.map(async ({ size, name }) => {
      try {
        await sharp(masterIconPath)
          .resize(size, size)
          .png()
          .toFile(path.join(iconsDir, name));
        console.log(`✅ ${name} 생성 완료`);
      } catch (error) {
        console.error(`❌ ${name} 생성 실패:`, error.message);
      }
    })
  ).then(() => {
    console.log('🎉 모든 PWA 아이콘이 성공적으로 생성되었습니다!');
    generateAdditionalAssets();
  });
}

function generatePlaceholderIcons() {
  console.log('📝 플레이스홀더 아이콘 생성 중...');
  
  // SVG 기반 플레이스홀더 생성
  iconSizes.forEach(({ size, name }) => {
    const svg = createPlaceholderSVG(size);
    const svgPath = path.join(iconsDir, name.replace('.png', '.svg'));
    fs.writeFileSync(svgPath, svg);
    console.log(`📄 ${name.replace('.png', '.svg')} 플레이스홀더 생성`);
  });
  
  console.log('');
  console.log('📝 플레이스홀더 아이콘이 생성되었습니다.');
  console.log('실제 PNG 아이콘을 사용하려면 위의 방법 1 또는 2를 사용하세요.');
}

function createPlaceholderSVG(size) {
  return `<?xml version="1.0" encoding="UTF-8"?>
<svg width="${size}" height="${size}" viewBox="0 0 ${size} ${size}" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="gradient" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#667eea"/>
      <stop offset="100%" style="stop-color:#764ba2"/>
    </linearGradient>
  </defs>
  <rect width="${size}" height="${size}" rx="${size * 0.125}" fill="url(#gradient)"/>
  <text x="50%" y="50%" text-anchor="middle" dy="0.35em" fill="white" font-family="Arial, sans-serif" font-size="${size * 0.4}" font-weight="bold">R</text>
</svg>`;
}

function generateAdditionalAssets() {
  console.log('🎯 추가 에셋 생성 중...');
  
  // 스크린샷 플레이스홀더
  const screenshotsDir = path.join(__dirname, '../frontend/public/screenshots');
  if (!fs.existsSync(screenshotsDir)) {
    fs.mkdirSync(screenshotsDir, { recursive: true });
  }
  
  // 데스크톱 스크린샷 플레이스홀더
  const desktopScreenshot = createScreenshotSVG(1280, 720, 'desktop');
  fs.writeFileSync(path.join(screenshotsDir, 'desktop.svg'), desktopScreenshot);
  
  // 모바일 스크린샷 플레이스홀더  
  const mobileScreenshot = createScreenshotSVG(390, 844, 'mobile');
  fs.writeFileSync(path.join(screenshotsDir, 'mobile.svg'), mobileScreenshot);
  
  console.log('📱 스크린샷 플레이스홀더 생성 완료');
  console.log('');
  console.log('🎉 PWA 설정이 완료되었습니다!');
  console.log('');
  console.log('다음 단계:');
  console.log('1. 실제 아이콘 이미지로 교체 (선택사항)');
  console.log('2. 실제 스크린샷으로 교체 (앱 스토어용)');
  console.log('3. manifest.json에서 앱 정보 커스터마이징');
}

function createScreenshotSVG(width, height, type) {
  const title = type === 'desktop' ? 'Resee - 과학적 복습 플랫폼' : 'Resee';
  return `<?xml version="1.0" encoding="UTF-8"?>
<svg width="${width}" height="${height}" viewBox="0 0 ${width} ${height}" xmlns="http://www.w3.org/2000/svg">
  <rect width="${width}" height="${height}" fill="#f8fafc"/>
  <rect x="0" y="0" width="${width}" height="64" fill="linear-gradient(135deg, #667eea 0%, #764ba2 100%)"/>
  <text x="${width/2}" y="40" text-anchor="middle" fill="white" font-family="Arial, sans-serif" font-size="20" font-weight="600">${title}</text>
  <rect x="20" y="80" width="${width-40}" height="60" rx="8" fill="#e2e8f0"/>
  <text x="${width/2}" y="115" text-anchor="middle" fill="#64748b" font-family="Arial, sans-serif" font-size="16">📚 오늘의 복습 콘텐츠</text>
  <rect x="20" y="160" width="${(width-60)/3}" height="120" rx="8" fill="white"/>
  <rect x="${20 + (width-60)/3 + 20}" y="160" width="${(width-60)/3}" height="120" rx="8" fill="white"/>
  <rect x="${20 + 2*(width-60)/3 + 40}" y="160" width="${(width-60)/3}" height="120" rx="8" fill="white"/>
</svg>`;
}

// 스크립트 실행
if (require.main === module) {
  // 직접 실행된 경우에만 실행
}`;

<style>
.code-block {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 16px;
  margin: 16px 0;
  overflow-x: auto;
}
</style>