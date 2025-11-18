import React from 'react';

const Footer: React.FC = () => {
  return (
    <footer className="bg-gray-800 text-gray-300 mt-auto">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="text-center space-y-3">
          <div>
            <a href="mailto:reseeall@gmail.com" className="text-sm hover:text-white transition-colors">
              reseeall@gmail.com
            </a>
          </div>
          <div className="text-xs text-gray-400">
            © 2025 Resee. All rights reserved.
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;