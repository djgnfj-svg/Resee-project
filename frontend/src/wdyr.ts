import React from 'react';

if (process.env.NODE_ENV === 'development') {
  // eslint-disable-next-line @typescript-eslint/no-var-requires
  const whyDidYouRender = require('@welldone-software/why-did-you-render');

  whyDidYouRender(React, {
    trackAllPureComponents: false,
    trackHooks: true,
    trackExtraHooks: [[require('@tanstack/react-query'), 'useQuery']],
    logOnDifferentValues: true,
    collapseGroups: true,
    include: [
      // 모니터링할 컴포넌트 정규식 패턴
      /^ContentCard$/,
      /^TestListItem$/,
      /^ReviewCard$/,
      /^Layout$/,
      /^AuthContext$/,
      /^ThemeContext$/,
    ],
    exclude: [
      /^Route$/,
      /^Link$/,
      /^Navigate$/,
    ],
  });
}
