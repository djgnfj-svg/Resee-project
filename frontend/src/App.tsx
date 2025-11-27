import React, { lazy, Suspense } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Toaster } from 'react-hot-toast';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { ThemeProvider } from './contexts/ThemeContext';
import ErrorBoundary from './components/common/ErrorBoundary';
import Layout from './components/layout/Layout';
import LoadingFallback from './components/common/LoadingFallback';
import ProtectedRoute from './components/auth/ProtectedRoute';
import './styles/design-system.css';
import './styles/animations.css';

// Lazy load all page components for code splitting
const HomePage = lazy(() => import('./pages/HomePage'));
const LoginPage = lazy(() => import('./pages/LoginPage'));
const RegisterPage = lazy(() => import('./pages/RegisterPage'));
const EmailVerificationPage = lazy(() => import('./pages/EmailVerificationPage'));
const VerificationPendingPage = lazy(() => import('./pages/VerificationPendingPage'));
const DashboardPage = lazy(() => import('./pages/DashboardPage'));
const ContentPage = lazy(() => import('./pages/ContentPage'));
const CreateContentPage = lazy(() => import('./pages/CreateContentPage'));
const EditContentPage = lazy(() => import('./pages/EditContentPage'));
const ReviewPage = lazy(() => import('./pages/ReviewPage'));
const ExamsPage = lazy(() => import('./pages/ExamsPage'));
const ProfilePage = lazy(() => import('./pages/ProfilePage'));
const SettingsPage = lazy(() => import('./pages/SettingsPage'));
const SubscriptionPage = lazy(() => import('./pages/SubscriptionPage'));
const NotFoundPage = lazy(() => import('./pages/NotFoundPage'));

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      // 재시도 전략
      retry: 1,
      retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),

      // 캐시 전략
      staleTime: 5 * 60 * 1000, // 5분 - 이 시간 동안은 데이터가 "fresh"로 간주됨
      cacheTime: 10 * 60 * 1000, // 10분 - 사용하지 않는 데이터를 메모리에 보관할 시간

      // 리페칭 동작
      refetchOnWindowFocus: false,
      refetchOnReconnect: true, // 네트워크 재연결 시 자동 리페치
      refetchOnMount: true, // 컴포넌트 마운트 시 stale 데이터는 리페치

      // 에러 처리
      useErrorBoundary: false, // 각 컴포넌트에서 에러 처리
    },
    mutations: {
      // 뮤테이션 재시도 (일반적으로 재시도 안 함)
      retry: 0,
    },
  },
});

// AppContent component that uses Auth context
const AppContent: React.FC = () => {
  const { isLoading } = useAuth();

  // Show loading spinner during initial auth check
  if (isLoading) {
    return <LoadingFallback />;
  }

  return (
    <Router future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
      <Layout>
        <Suspense fallback={<LoadingFallback />}>
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
            <Route path="/verify-email" element={<EmailVerificationPage />} />
            <Route path="/verification-pending" element={<VerificationPendingPage />} />
            <Route
              path="/dashboard"
              element={
                <ProtectedRoute>
                  <DashboardPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/content"
              element={
                <ProtectedRoute>
                  <ContentPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/content/new"
              element={
                <ProtectedRoute>
                  <CreateContentPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/content/:id/edit"
              element={
                <ProtectedRoute>
                  <EditContentPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/review"
              element={
                <ProtectedRoute>
                  <ReviewPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/exams"
              element={
                <ProtectedRoute>
                  <ExamsPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/exams/:id"
              element={
                <ProtectedRoute>
                  <ExamsPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/profile"
              element={
                <ProtectedRoute>
                  <ProfilePage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/settings"
              element={
                <ProtectedRoute>
                  <SettingsPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/subscription"
              element={
                <ProtectedRoute>
                  <SubscriptionPage />
                </ProtectedRoute>
              }
            />
            {/* 404 페이지 - 모든 라우트의 맨 마지막에 위치 */}
            <Route path="*" element={<NotFoundPage />} />
          </Routes>
        </Suspense>
      </Layout>
    </Router>
  );
};

function App() {
  return (
    <ErrorBoundary>
      <ThemeProvider>
        <QueryClientProvider client={queryClient}>
          <AuthProvider>
            <AppContent />
            <Toaster
              position="top-right"
              toastOptions={{
                duration: 4000,
                style: {
                  background: 'var(--toast-bg, #fff)',
                  color: 'var(--toast-text, #333)',
                },
                success: {
                  iconTheme: {
                    primary: '#10b981',
                    secondary: '#fff',
                  },
                },
                error: {
                  iconTheme: {
                    primary: '#ef4444',
                    secondary: '#fff',
                  },
                },
              }}
            />
          </AuthProvider>
        </QueryClientProvider>
      </ThemeProvider>
    </ErrorBoundary>
  );
}

export default App;