import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  LineChart, Line, AreaChart, Area
} from 'recharts';
import { Target, TrendingUp, Brain, Calendar, Clock, CheckCircle } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { api } from '@/utils/api';

interface UserAnalyticsProps {
  userId?: number;
}

interface LearningInsights {
  total_learning_days: number;
  current_streak: number;
  longest_streak: number;
  average_daily_reviews: number;
  average_success_rate: number;
  most_productive_hour: number;
  total_study_hours: number;
  learning_consistency_score: number;
}

interface ConversionProbability {
  user_id: number;
  conversion_probability: number;
  score_breakdown: Record<string, number>;
  user_features: {
    total_contents: number;
    total_reviews: number;
    avg_success_rate: number;
    longest_streak: number;
    days_since_last_activity: number;
    days_since_signup: number;
    reviews_per_day: number;
  };
  recommendations: string[];
  risk_level: 'high' | 'medium' | 'low';
}

interface ContentAnalytics {
  total_content: number;
  mastered_content: number;
  struggling_content: number;
  abandoned_content: number;
  average_mastery_time_days: number;
  most_effective_content_type: string;
  least_effective_content_type: string;
  category_performance: Record<string, {
    total: number;
    success_rate: number;
    reviews: number;
  }>;
}

interface PerformanceTrend {
  date: string;
  success_rate: number;
  reviews_completed: number;
  study_time_minutes: number;
  difficulty_trend: number;
  engagement_score: number;
}

const UserAnalytics: React.FC<UserAnalyticsProps> = ({ userId }) => {
  const [selectedPeriod, setSelectedPeriod] = useState(30);

  const { data: userInsights, isLoading } = useQuery({
    queryKey: ['user-analytics', userId, selectedPeriod],
    queryFn: () => api.get(`/api/bi/learning-insights/?days=${selectedPeriod}`).then(res => res.data),
    enabled: !!userId
  });

  const { data: conversionProb } = useQuery({
    queryKey: ['conversion-probability', userId],
    queryFn: () => api.get(`/api/bi/subscription-analysis/conversion-probability/?user_id=${userId}`).then(res => res.data),
    enabled: !!userId
  });

  const { data: contentAnalytics } = useQuery({
    queryKey: ['content-analytics', userId],
    queryFn: () => api.get(`/api/bi/content-analytics/`).then(res => res.data),
    enabled: !!userId
  });

  const { data: performanceTrends } = useQuery({
    queryKey: ['performance-trends', userId, selectedPeriod],
    queryFn: () => api.get(`/api/bi/performance-trends/?days=${selectedPeriod}`).then(res => res.data),
    enabled: !!userId
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
        <span className="ml-2">Loading user analytics...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">Learning Analytics</h2>
        <select
          value={selectedPeriod}
          onChange={(e) => setSelectedPeriod(Number(e.target.value))}
          className="px-3 py-2 border rounded-md"
        >
          <option value={7}>Last 7 days</option>
          <option value={30}>Last 30 days</option>
          <option value={90}>Last 90 days</option>
        </select>
      </div>

      {/* Performance Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-3">
              <Brain className="w-8 h-8 text-blue-500" />
              <div>
                <p className="text-sm text-muted-foreground">Learning Days</p>
                <p className="text-2xl font-bold">{userInsights?.total_learning_days || 0}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-3">
              <Target className="w-8 h-8 text-green-500" />
              <div>
                <p className="text-sm text-muted-foreground">Success Rate</p>
                <p className="text-2xl font-bold">{userInsights?.average_success_rate || 0}%</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-3">
              <Calendar className="w-8 h-8 text-orange-500" />
              <div>
                <p className="text-sm text-muted-foreground">Current Streak</p>
                <p className="text-2xl font-bold">{userInsights?.current_streak || 0} days</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-3">
              <Clock className="w-8 h-8 text-purple-500" />
              <div>
                <p className="text-sm text-muted-foreground">Study Hours</p>
                <p className="text-2xl font-bold">{userInsights?.total_study_hours || 0}h</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Learning Insights Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Learning Consistency</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span>Consistency Score</span>
                <div className="flex items-center space-x-2">
                  <Progress value={userInsights?.learning_consistency_score || 0} className="w-20" />
                  <span className="font-bold">{userInsights?.learning_consistency_score || 0}%</span>
                </div>
              </div>
              <div className="flex justify-between">
                <span>Average Daily Reviews</span>
                <span className="font-bold">{userInsights?.average_daily_reviews || 0}</span>
              </div>
              <div className="flex justify-between">
                <span>Most Productive Hour</span>
                <span className="font-bold">{userInsights?.most_productive_hour || 12}:00</span>
              </div>
              <div className="flex justify-between">
                <span>Longest Streak</span>
                <Badge variant="secondary">{userInsights?.longest_streak || 0} days</Badge>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Content Progress</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {contentAnalytics && (
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span>Total Content</span>
                  <span className="font-bold">{contentAnalytics.total_content}</span>
                </div>
                <div className="flex justify-between">
                  <span>Mastered</span>
                  <div className="flex items-center space-x-2">
                    <CheckCircle className="w-4 h-4 text-green-500" />
                    <span className="font-bold text-green-600">{contentAnalytics.mastered_content}</span>
                  </div>
                </div>
                <div className="flex justify-between">
                  <span>Struggling</span>
                  <span className="font-bold text-yellow-600">{contentAnalytics.struggling_content}</span>
                </div>
                <div className="flex justify-between">
                  <span>Abandoned</span>
                  <span className="font-bold text-red-600">{contentAnalytics.abandoned_content}</span>
                </div>
                <div className="flex justify-between">
                  <span>Avg Mastery Time</span>
                  <span className="font-bold">{contentAnalytics.average_mastery_time_days} days</span>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Performance Trends Chart */}
      {performanceTrends && performanceTrends.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Performance Trends</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={400}>
              <LineChart data={performanceTrends}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis 
                  dataKey="date" 
                  tickFormatter={(value) => new Date(value).toLocaleDateString()}
                />
                <YAxis yAxisId="left" />
                <YAxis yAxisId="right" orientation="right" />
                <Tooltip 
                  labelFormatter={(value) => new Date(value).toLocaleDateString()}
                />
                <Line 
                  yAxisId="left"
                  type="monotone" 
                  dataKey="success_rate" 
                  stroke="#8884d8" 
                  name="Success Rate (%)"
                  strokeWidth={2}
                />
                <Line 
                  yAxisId="right"
                  type="monotone" 
                  dataKey="reviews_completed" 
                  stroke="#82ca9d" 
                  name="Reviews Completed"
                  strokeWidth={2}
                />
                <Line 
                  yAxisId="left"
                  type="monotone" 
                  dataKey="engagement_score" 
                  stroke="#ffc658" 
                  name="Engagement Score"
                  strokeWidth={2}
                />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      )}

      {/* Conversion Probability */}
      {conversionProb && !conversionProb.message && (
        <Card>
          <CardHeader>
            <CardTitle>Subscription Conversion Analysis</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <span>Conversion Probability</span>
              <div className="flex items-center space-x-2">
                <Progress value={conversionProb.conversion_probability} className="w-32" />
                <span className="font-bold">{conversionProb.conversion_probability}%</span>
                <Badge variant={
                  conversionProb.risk_level === 'high' ? 'default' :
                  conversionProb.risk_level === 'medium' ? 'secondary' : 'outline'
                }>
                  {conversionProb.risk_level}
                </Badge>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h4 className="font-medium mb-3">Score Breakdown</h4>
                <div className="space-y-2 text-sm">
                  {Object.entries(conversionProb.score_breakdown || {}).map(([key, value]) => (
                    <div key={key} className="flex justify-between">
                      <span className="capitalize">{key.replace('_', ' ')}:</span>
                      <Progress value={Number(value)} className="w-16 h-2" />
                      <span className="text-xs w-8">{value}</span>
                    </div>
                  ))}
                </div>
              </div>
              
              <div>
                <h4 className="font-medium mb-3">User Features</h4>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span>Total Contents:</span>
                    <span>{conversionProb.user_features?.total_contents}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Total Reviews:</span>
                    <span>{conversionProb.user_features?.total_reviews}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Reviews per Day:</span>
                    <span>{conversionProb.user_features?.reviews_per_day}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Days Since Signup:</span>
                    <span>{conversionProb.user_features?.days_since_signup}</span>
                  </div>
                </div>
              </div>
            </div>

            {conversionProb.recommendations && conversionProb.recommendations.length > 0 && (
              <div>
                <h4 className="font-medium mb-3">Personalized Recommendations</h4>
                <div className="space-y-2">
                  {conversionProb.recommendations.map((rec: string, index: number) => (
                    <div key={index} className="flex items-start space-x-2">
                      <TrendingUp className="w-4 h-4 text-blue-500 mt-0.5 flex-shrink-0" />
                      <p className="text-sm text-muted-foreground">{rec}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Content Type Effectiveness */}
      {contentAnalytics && Object.keys(contentAnalytics.category_performance || {}).length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Category Performance</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={Object.entries(contentAnalytics.category_performance).map(([category, data]) => ({
                category,
                success_rate: data.success_rate,
                total_reviews: data.reviews,
                total_content: data.total
              }))}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="category" />
                <YAxis yAxisId="left" />
                <YAxis yAxisId="right" orientation="right" />
                <Tooltip />
                <Bar yAxisId="left" dataKey="success_rate" fill="#8884d8" name="Success Rate (%)" />
                <Bar yAxisId="right" dataKey="total_reviews" fill="#82ca9d" name="Total Reviews" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      )}

      {/* Study Time Analysis */}
      {performanceTrends && performanceTrends.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Study Time Pattern</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={performanceTrends}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis 
                  dataKey="date" 
                  tickFormatter={(value) => new Date(value).toLocaleDateString()}
                />
                <YAxis />
                <Tooltip 
                  labelFormatter={(value) => new Date(value).toLocaleDateString()}
                />
                <Area 
                  type="monotone" 
                  dataKey="study_time_minutes" 
                  stroke="#8884d8" 
                  fill="#8884d8"
                  name="Study Time (minutes)"
                />
              </AreaChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default UserAnalytics;