import React from 'react';
import { Link } from 'react-router-dom';

const PrivacyPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-4xl mx-auto bg-white dark:bg-gray-800 rounded-lg shadow-lg p-8">
          <div className="mb-8">
            <Link to="/" className="text-indigo-600 hover:text-indigo-700 dark:text-indigo-400 dark:hover:text-indigo-300 text-sm font-medium">
              ← 홈으로 돌아가기
            </Link>
          </div>
          
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-8">개인정보처리방침</h1>
          
          <div className="prose prose-gray dark:prose-invert max-w-none">
            <section className="mb-8">
              <h2 className="text-xl font-semibold text-gray-800 dark:text-gray-200 mb-4">제 1 조 (개인정보의 처리목적)</h2>
              <p className="text-gray-600 dark:text-gray-400 mb-4">
                Resee(이하 "회사")는 다음의 목적을 위하여 개인정보를 처리합니다. 처리하고 있는 개인정보는 다음의 목적 이외의 용도로는 이용되지 않으며, 이용 목적이 변경되는 경우에는 개인정보보호법 제18조에 따라 별도의 동의를 받는 등 필요한 조치를 이행할 예정입니다.
              </p>
              <div className="space-y-2 text-gray-600 dark:text-gray-400">
                <p>1. 회원가입 및 관리: 회원 식별, 서비스 이용에 따른 본인확인, 연령확인, 불만처리 등</p>
                <p>2. 서비스 제공: 학습 콘텐츠 관리, 복습 스케줄 생성, 학습 분석 및 통계</p>
                <p>3. 마케팅 및 광고에의 활용: 신규 서비스 개발 및 맞춤 서비스 제공, 이벤트 및 광고성 정보 제공</p>
              </div>
            </section>

            <section className="mb-8">
              <h2 className="text-xl font-semibold text-gray-800 dark:text-gray-200 mb-4">제 2 조 (처리하는 개인정보의 항목)</h2>
              <div className="space-y-4 text-gray-600 dark:text-gray-400">
                <div>
                  <h3 className="font-semibold text-gray-700 dark:text-gray-300 mb-2">필수항목:</h3>
                  <ul className="list-disc pl-6 space-y-1">
                    <li>이메일 주소</li>
                    <li>비밀번호 (암호화 저장)</li>
                    <li>서비스 이용 기록</li>
                    <li>접속 로그, IP주소, 쿠키, 접속 일시</li>
                  </ul>
                </div>
                <div>
                  <h3 className="font-semibold text-gray-700 dark:text-gray-300 mb-2">선택항목:</h3>
                  <ul className="list-disc pl-6 space-y-1">
                    <li>이름 (구글 로그인 시)</li>
                    <li>프로필 사진 (구글 로그인 시)</li>
                    <li>학습 선호도 및 목표 설정</li>
                  </ul>
                </div>
              </div>
            </section>

            <section className="mb-8">
              <h2 className="text-xl font-semibold text-gray-800 dark:text-gray-200 mb-4">제 3 조 (개인정보의 처리 및 보유기간)</h2>
              <div className="space-y-2 text-gray-600 dark:text-gray-400">
                <p>회사는 법령에 따른 개인정보 보유·이용기간 또는 정보주체로부터 개인정보를 수집 시에 동의 받은 개인정보 보유·이용기간 내에서 개인정보를 처리·보유합니다.</p>
                <p><strong>회원정보:</strong> 회원 탈퇴 시까지 (탈퇴 후 즉시 삭제)</p>
                <p><strong>학습 데이터:</strong> 회원 탈퇴 후 3년간 보관 (단, 사용자가 삭제를 요청할 경우 즉시 삭제)</p>
                <p><strong>서비스 이용 기록:</strong> 3년간 보관</p>
              </div>
            </section>

            <section className="mb-8">
              <h2 className="text-xl font-semibold text-gray-800 dark:text-gray-200 mb-4">제 4 조 (개인정보의 제3자 제공)</h2>
              <div className="space-y-2 text-gray-600 dark:text-gray-400">
                <p>회사는 원칙적으로 정보주체의 개인정보를 제3자에게 제공하지 않습니다. 다만, 다음의 경우에는 예외로 합니다:</p>
                <ul className="list-disc pl-6 space-y-1">
                  <li>정보주체로부터 별도의 동의를 받은 경우</li>
                  <li>법률에 특별한 규정이 있거나 법령상 의무를 준수하기 위하여 불가피한 경우</li>
                  <li>정보주체 또는 그 법정대리인이 의사표시를 할 수 없는 상태에 있거나 주소불명 등으로 사전 동의를 받을 수 없는 경우로서 명백히 정보주체 또는 제3자의 급박한 생명, 신체, 재산의 이익을 위하여 필요하다고 인정되는 경우</li>
                </ul>
              </div>
            </section>

            <section className="mb-8">
              <h2 className="text-xl font-semibold text-gray-800 dark:text-gray-200 mb-4">제 5 조 (개인정보의 파기)</h2>
              <div className="space-y-2 text-gray-600 dark:text-gray-400">
                <p>회사는 개인정보 보유기간의 경과, 처리목적 달성 등 개인정보가 불필요하게 되었을 때에는 지체없이 해당 개인정보를 파기합니다.</p>
                <p><strong>파기절차:</strong> 불필요한 개인정보 및 개인정보파일은 개인정보보호책임자의 승인을 받아 파기합니다.</p>
                <p><strong>파기방법:</strong> 전자적 파일 형태는 기록을 재생할 수 없는 기술적 방법을 사용하여 삭제하며, 종이에 출력된 개인정보는 분쇄기로 분쇄하거나 소각합니다.</p>
              </div>
            </section>

            <section className="mb-8">
              <h2 className="text-xl font-semibold text-gray-800 dark:text-gray-200 mb-4">제 6 조 (정보주체의 권리·의무 및 행사방법)</h2>
              <div className="space-y-2 text-gray-600 dark:text-gray-400">
                <p>정보주체는 회사에 대해 언제든지 다음 각 호의 개인정보 보호 관련 권리를 행사할 수 있습니다:</p>
                <ul className="list-disc pl-6 space-y-1">
                  <li>개인정보 처리현황 통지요구</li>
                  <li>개인정보 열람요구</li>
                  <li>개인정보 정정·삭제요구</li>
                  <li>개인정보 처리정지요구</li>
                </ul>
                <p className="mt-4">위의 권리 행사는 개인정보보호법 시행규칙 별지 제8호 서식에 따라 작성하여 서면, 전자우편, 모사전송(FAX) 등을 통하여 하실 수 있으며 회사는 이에 대해 지체없이 조치하겠습니다.</p>
              </div>
            </section>

            <section className="mb-8">
              <h2 className="text-xl font-semibold text-gray-800 dark:text-gray-200 mb-4">제 7 조 (개인정보보호책임자)</h2>
              <div className="space-y-2 text-gray-600 dark:text-gray-400">
                <p>회사는 개인정보 처리에 관한 업무를 총괄해서 책임지고, 개인정보 처리와 관련한 정보주체의 불만처리 및 피해구제를 처리하기 위하여 아래와 같이 개인정보보호책임자를 지정하고 있습니다.</p>
                <div className="mt-4 p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                  <p><strong>개인정보보호책임자</strong></p>
                  <p>이메일: reseeall@gmail.com</p>
                  <p>처리시간: 평일 09:00 - 18:00</p>
                </div>
              </div>
            </section>

            <section className="mb-8">
              <h2 className="text-xl font-semibold text-gray-800 dark:text-gray-200 mb-4">제 8 조 (개인정보의 안전성 확보조치)</h2>
              <div className="space-y-2 text-gray-600 dark:text-gray-400">
                <p>회사는 개인정보의 안전성 확보를 위해 다음과 같은 조치를 취하고 있습니다:</p>
                <ul className="list-disc pl-6 space-y-1">
                  <li>관리적 조치: 내부관리계획 수립·시행, 정기적 직원 교육 등</li>
                  <li>기술적 조치: 개인정보처리시스템 등의 접근권한 관리, 접근통제시스템 설치, 고유식별정보 등의 암호화, 보안프로그램 설치</li>
                  <li>물리적 조치: 전산실, 자료보관실 등의 접근통제</li>
                </ul>
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

export default PrivacyPage;