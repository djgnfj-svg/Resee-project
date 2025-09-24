// Re-export all API modules for backward compatibility
export { authAPI } from './api/auth';
export { contentAPI } from './api/content';
export { reviewAPI } from './api/review';
export { subscriptionAPI } from './api/subscription';
export { analyticsAPI } from './api/analytics';

// Re-export individual functions for backward compatibility
export const verifyEmail = (token: string, email: string) => {
  return import('./api/auth').then(({ authAPI }) => authAPI.verifyEmail(token, email));
};
export const resendVerificationEmail = (email: string) => {
  return import('./api/auth').then(({ authAPI }) => authAPI.resendVerificationEmail(email));
};

// Export the main api client
export { default, apiClient } from './api/index';