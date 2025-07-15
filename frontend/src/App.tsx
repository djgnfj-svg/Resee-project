import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Toaster } from 'react-hot-toast';
import { AuthProvider } from './contexts/AuthContext';
import ErrorBoundary from './components/ErrorBoundary';
import Layout from './components/Layout';
import HomePage from './pages/HomePage';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import DashboardPage from './pages/DashboardPage';
import ContentPage from './pages/ContentPage';
import ReviewPage from './pages/ReviewPage';
import ProtectedRoute from './components/ProtectedRoute';
import './styles/animations.css';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

function App() {
  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          <Router>
            <Layout>
            <Routes>
              <Route path="/" element={<HomePage />} />
              <Route path="/login" element={<LoginPage />} />
              <Route path="/register" element={<RegisterPage />} />
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
                path="/review" 
                element={
                  <ProtectedRoute>
                    <ReviewPage />
                  </ProtectedRoute>
                } 
              />
            </Routes>
          </Layout>
          <Toaster />
        </Router>
      </AuthProvider>
    </QueryClientProvider>
    </ErrorBoundary>
  );
}

export default App;