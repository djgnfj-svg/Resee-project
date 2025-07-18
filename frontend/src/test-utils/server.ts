import { rest } from 'msw';
import { setupServer } from 'msw/node';

// Mock API base URL
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

// Mock data
const mockUser = {
  id: 1,
  username: 'testuser',
  email: 'test@example.com',
  first_name: 'Test',
  last_name: 'User',
  timezone: 'Asia/Seoul',
  notification_enabled: true,
};

const mockCategories = [
  { id: 1, name: 'Python', description: 'Python programming', user: 1 },
  { id: 2, name: 'JavaScript', description: 'JavaScript programming', user: 1 },
  { id: 3, name: 'Django', description: 'Django framework', user: 1 },
];

const mockTags = [
  { id: 1, name: 'basics' },
  { id: 2, name: 'advanced' },
  { id: 3, name: 'tutorial' },
];

const mockContents = [
  {
    id: 1,
    title: 'Python Variables',
    content: 'Variables in Python are used to store data values.',
    priority: 'high',
    category: 1,
    tags: [1, 3],
    author: 1,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
  {
    id: 2,
    title: 'JavaScript Functions',
    content: 'Functions are reusable blocks of code.',
    priority: 'medium',
    category: 2,
    tags: [1],
    author: 1,
    created_at: '2024-01-02T00:00:00Z',
    updated_at: '2024-01-02T00:00:00Z',
  },
];

const mockReviewSchedules = [
  {
    id: 1,
    content: 1,
    user: 1,
    next_review_date: new Date().toISOString(),
    interval_index: 0,
    is_active: true,
    initial_review_completed: false,
  },
];

// Request handlers
export const handlers = [
  // Authentication endpoints
  rest.post(`${API_BASE_URL}/auth/token/`, (req, res, ctx) => {
    return res(
      ctx.json({
        access: 'mock-access-token',
        refresh: 'mock-refresh-token',
      })
    );
  }),

  rest.post(`${API_BASE_URL}/auth/token/refresh/`, (req, res, ctx) => {
    return res(
      ctx.json({
        access: 'new-mock-access-token',
      })
    );
  }),

  // User endpoints
  rest.get(`${API_BASE_URL}/accounts/profile/`, (req, res, ctx) => {
    return res(ctx.json(mockUser));
  }),

  rest.put(`${API_BASE_URL}/accounts/profile/`, (req, res, ctx) => {
    return res(ctx.json({ ...mockUser, ...req.body }));
  }),

  rest.post(`${API_BASE_URL}/accounts/users/register/`, (req, res, ctx) => {
    return res(
      ctx.status(201),
      ctx.json({
        id: 2,
        username: 'newuser',
        email: 'new@example.com',
        first_name: 'New',
        last_name: 'User',
      })
    );
  }),

  // Content endpoints
  rest.get(`${API_BASE_URL}/content/contents/`, (req, res, ctx) => {
    const page = req.url.searchParams.get('page') || '1';
    const search = req.url.searchParams.get('search');
    const priority = req.url.searchParams.get('priority');
    
    let filteredContents = [...mockContents];
    
    if (search) {
      filteredContents = filteredContents.filter(content =>
        content.title.toLowerCase().includes(search.toLowerCase()) ||
        content.content.toLowerCase().includes(search.toLowerCase())
      );
    }
    
    if (priority) {
      filteredContents = filteredContents.filter(content => 
        content.priority === priority
      );
    }

    return res(
      ctx.json({
        count: filteredContents.length,
        next: null,
        previous: null,
        results: filteredContents,
      })
    );
  }),

  rest.post(`${API_BASE_URL}/content/contents/`, (req, res, ctx) => {
    const newContent = {
      id: mockContents.length + 1,
      ...req.body,
      author: 1,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };
    return res(ctx.status(201), ctx.json(newContent));
  }),

  rest.get(`${API_BASE_URL}/content/contents/:id/`, (req, res, ctx) => {
    const { id } = req.params;
    const content = mockContents.find(c => c.id === parseInt(id as string));
    
    if (!content) {
      return res(ctx.status(404), ctx.json({ detail: 'Not found.' }));
    }
    
    return res(ctx.json(content));
  }),

  rest.put(`${API_BASE_URL}/content/contents/:id/`, (req, res, ctx) => {
    const { id } = req.params;
    const content = mockContents.find(c => c.id === parseInt(id as string));
    
    if (!content) {
      return res(ctx.status(404), ctx.json({ detail: 'Not found.' }));
    }
    
    const updatedContent = {
      ...content,
      ...req.body,
      updated_at: new Date().toISOString(),
    };
    
    return res(ctx.json(updatedContent));
  }),

  rest.delete(`${API_BASE_URL}/content/contents/:id/`, (req, res, ctx) => {
    return res(ctx.status(204));
  }),

  // Category endpoints
  rest.get(`${API_BASE_URL}/content/categories/`, (req, res, ctx) => {
    return res(
      ctx.json({
        count: mockCategories.length,
        next: null,
        previous: null,
        results: mockCategories,
      })
    );
  }),

  rest.post(`${API_BASE_URL}/content/categories/`, (req, res, ctx) => {
    const newCategory = {
      id: mockCategories.length + 1,
      ...req.body,
      user: 1,
    };
    return res(ctx.status(201), ctx.json(newCategory));
  }),

  // Tag endpoints
  rest.get(`${API_BASE_URL}/content/tags/`, (req, res, ctx) => {
    return res(
      ctx.json({
        count: mockTags.length,
        next: null,
        previous: null,
        results: mockTags,
      })
    );
  }),

  rest.post(`${API_BASE_URL}/content/tags/`, (req, res, ctx) => {
    const newTag = {
      id: mockTags.length + 1,
      ...req.body,
    };
    return res(ctx.status(201), ctx.json(newTag));
  }),

  // Review endpoints
  rest.get(`${API_BASE_URL}/review/today/`, (req, res, ctx) => {
    return res(
      ctx.json({
        count: mockReviewSchedules.length,
        next: null,
        previous: null,
        results: mockReviewSchedules,
      })
    );
  }),

  rest.post(`${API_BASE_URL}/review/complete/`, (req, res, ctx) => {
    return res(
      ctx.json({
        success: true,
        message: 'Review completed successfully',
      })
    );
  }),

  // Analytics endpoints
  rest.get(`${API_BASE_URL}/analytics/dashboard/`, (req, res, ctx) => {
    return res(
      ctx.json({
        total_contents: 10,
        total_reviews: 25,
        categories_count: 5,
        today_reviews: 3,
        week_reviews: 15,
        success_rate: 85.5,
        average_time_spent: 120,
      })
    );
  }),

  rest.get(`${API_BASE_URL}/analytics/review-stats/`, (req, res, ctx) => {
    return res(
      ctx.json({
        total_reviews: 25,
        success_rate: 85.5,
        average_time_spent: 120,
        reviews_by_day: [
          { date: '2024-01-01', count: 5 },
          { date: '2024-01-02', count: 3 },
          { date: '2024-01-03', count: 7 },
        ],
      })
    );
  }),


  // Error scenarios
  rest.get(`${API_BASE_URL}/error-test/`, (req, res, ctx) => {
    return res(ctx.status(500), ctx.json({ error: 'Internal server error' }));
  }),
];

// Setup server
export const server = setupServer(...handlers);