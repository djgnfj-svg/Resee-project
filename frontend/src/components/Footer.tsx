import React from 'react';

const Footer: React.FC = () => {
  return (
    <footer className="bg-gray-800 text-gray-300 mt-auto">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div>
            <h3 className="text-white font-semibold mb-3">Resee</h3>
          </div>
          
          <div>
            <h3 className="text-white font-semibold mb-3">고객 지원</h3>
            <ul className="space-y-2 text-sm">
              <li>
                <a href="mailto:reseeall@gmail.com" className="hover:text-white transition-colors">
                  이메일: reseeall@gmail.com
                </a>
              </li>
              <li>운영시간: 평일 09:00 - 18:00</li>
            </ul>
          </div>
          
          <div>
            <h3 className="text-white font-semibold mb-3">법적 정보</h3>
            <ul className="space-y-2 text-sm">
              <li>
                <a href="/terms" className="hover:text-white transition-colors">
                  이용약관
                </a>
              </li>
              <li>
                <a href="/privacy" className="hover:text-white transition-colors">
                  개인정보처리방침
                </a>
              </li>
            </ul>
          </div>
        </div>
        
        <div className="border-t border-gray-700 mt-8 pt-8 text-center text-sm">
          <p>© 2025 Resee. All rights reserved.</p>
        </div>
      </div>
    </footer>
  );
};

export default Footer;