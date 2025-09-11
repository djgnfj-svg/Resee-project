import React from 'react';
import { Link } from 'react-router-dom';

const TermsPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-4xl mx-auto bg-white dark:bg-gray-800 rounded-lg shadow-lg p-8">
          <div className="mb-8">
            <Link to="/" className="text-indigo-600 hover:text-indigo-700 dark:text-indigo-400 dark:hover:text-indigo-300 text-sm font-medium">
              ← 홈으로 돌아가기
            </Link>
          </div>
          
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-8">이용약관</h1>
          
          <div className="prose prose-gray dark:prose-invert max-w-none">
            <section className="mb-8">
              <h2 className="text-xl font-semibold text-gray-800 dark:text-gray-200 mb-4">제 1 조 (목적)</h2>
              <p className="text-gray-600 dark:text-gray-400 mb-4">
                본 약관은 Resee(이하 "회사")가 제공하는 스마트 복습 플랫폼 서비스(이하 "서비스")의 이용과 관련하여 회사와 이용자 간의 권리, 의무 및 책임사항을 규정함을 목적으로 합니다.
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-xl font-semibold text-gray-800 dark:text-gray-200 mb-4">제 2 조 (정의)</h2>
              <div className="space-y-2 text-gray-600 dark:text-gray-400">
                <p>1. "서비스"란 회사가 제공하는 에빙하우스 망각곡선 기반의 스마트 복습 시스템을 의미합니다.</p>
                <p>2. "이용자"란 본 약관에 따라 회사가 제공하는 서비스를 받는 회원 및 비회원을 의미합니다.</p>
                <p>3. "회원"이란 회사에 개인정보를 제공하여 회원등록을 한 자로서, 회사의 서비스를 지속적으로 이용할 수 있는 자를 의미합니다.</p>
              </div>
            </section>

            <section className="mb-8">
              <h2 className="text-xl font-semibold text-gray-800 dark:text-gray-200 mb-4">제 3 조 (약관의 효력 및 변경)</h2>
              <div className="space-y-2 text-gray-600 dark:text-gray-400">
                <p>1. 본 약관은 서비스 화면에 게시하거나 기타의 방법으로 이용자에게 공지함으로써 효력을 발생합니다.</p>
                <p>2. 회사는 필요한 경우 관련 법령을 위반하지 않는 범위에서 본 약관을 변경할 수 있습니다.</p>
                <p>3. 약관이 변경되는 경우 회사는 변경사항을 시행일자 7일 이전부터 서비스 내 공지사항을 통해 공지합니다.</p>
              </div>
            </section>

            <section className="mb-8">
              <h2 className="text-xl font-semibold text-gray-800 dark:text-gray-200 mb-4">제 4 조 (서비스의 제공)</h2>
              <div className="space-y-2 text-gray-600 dark:text-gray-400">
                <p>1. 회사는 다음과 같은 서비스를 제공합니다:</p>
                <ul className="list-disc pl-6 space-y-1">
                  <li>에빙하우스 망각곡선 기반 복습 스케줄링</li>
                  <li>학습 콘텐츠 관리 및 분류</li>
                  <li>학습 진도 추적 및 분석</li>
                  <li>AI 기반 학습 지원 기능</li>
                  <li>기타 회사가 정하는 서비스</li>
                </ul>
              </div>
            </section>

            <section className="mb-8">
              <h2 className="text-xl font-semibold text-gray-800 dark:text-gray-200 mb-4">제 5 조 (이용자의 의무)</h2>
              <div className="space-y-2 text-gray-600 dark:text-gray-400">
                <p>1. 이용자는 본 약관 및 관련 법령을 준수하여야 합니다.</p>
                <p>2. 이용자는 다음 각 호의 행위를 하여서는 아니 됩니다:</p>
                <ul className="list-disc pl-6 space-y-1">
                  <li>타인의 정보 도용</li>
                  <li>회사의 서비스 정보를 무단으로 변경하는 행위</li>
                  <li>회사의 저작권, 제3자의 저작권 등 기타 권리를 침해하는 행위</li>
                  <li>공공질서 및 미풍양속에 위반되는 행위</li>
                </ul>
              </div>
            </section>

            <section className="mb-8">
              <h2 className="text-xl font-semibold text-gray-800 dark:text-gray-200 mb-4">제 6 조 (개인정보보호)</h2>
              <p className="text-gray-600 dark:text-gray-400 mb-4">
                회사는 이용자의 개인정보를 보호하기 위해 개인정보처리방침을 별도로 정하여 운영합니다. 자세한 내용은 개인정보처리방침을 참조하시기 바랍니다.
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-xl font-semibold text-gray-800 dark:text-gray-200 mb-4">제 7 조 (면책조항)</h2>
              <div className="space-y-2 text-gray-600 dark:text-gray-400">
                <p>1. 회사는 천재지변, 전쟁, 기간통신 사업자의 서비스 중지 등 불가항력으로 인하여 서비스를 제공할 수 없는 경우에는 서비스 제공에 대한 책임이 면제됩니다.</p>
                <p>2. 회사는 이용자의 귀책사유로 인한 서비스 이용의 장애에 대하여는 책임지지 않습니다.</p>
              </div>
            </section>
          </div>
          
          <div className="mt-12 pt-8 border-t border-gray-200 dark:border-gray-700">
            <p className="text-sm text-gray-500 dark:text-gray-400">
              최종 수정일: 2025년 01월 01일<br />
              시행일: 2025년 01월 01일
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TermsPage;