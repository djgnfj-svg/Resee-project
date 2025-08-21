import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  LineChart, Line, AreaChart, Area, BarChart, Bar,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell
} from 'recharts';
import { 
  TrendingUp, TrendingDown, Users, DollarSign, 
  Target, AlertTriangle, Star, Activity 
} from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { api } from '@/utils/api';

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

interface BusinessMetrics {
  total_users: number;
  active_users_today: number;
  new_users_this_month: number;
  monthly_revenue: number;
  average_session_duration: number;
  daily_active_users_trend: number[];
  user_retention_rate: number;
  total_content_created: number;
  average_reviews_per_user: number;
  content_completion_rate: number;
  conversion_rate: number;
  churn_rate: number;
  average_revenue_per_user: number;
  tier_distribution: Record<string, number>;
  ai_adoption_rate: number;
  ai_cost_efficiency: number;
  ai_questions_per_user: number;
  system_uptime: number;
  average_response_time: number;
  error_rate: number;
}

interface ConversionFunnel {
  funnel_data: {
    total_signups: number;
    users_with_content: number;
    users_with_reviews: number;
    converted_users: number;
  };
  conversion_rates: {
    signup_to_content: number;
    content_to_review: number;
    review_to_subscription: number;
    overall_conversion: number;
  };
  insights: string[];
}

interface ChurnAnalysis {
  total_churned_users: number;
  average_subscription_duration: number;
  average_days_since_last_activity: number;
  high_risk_indicators: string[];
  recommendations: string[];
}

const COLORS = ['#8884d8', '#82ca9d', '#ffc658', '#ff7c7c', '#8dd1e1'];

const BIDashboard: React.FC = () => {
  const [selectedPeriod, setSelectedPeriod] = useState(30);

  // API Queries
  const { data: learningInsights, isLoading: learningLoading } = useQuery({
    queryKey: ['learning-insights', selectedPeriod],
    queryFn: () => api.get(`/api/bi/learning-insights/?days=${selectedPeriod}`).then(res => res.data)
  });

  const { data: businessMetrics, isLoading: businessLoading } = useQuery({
    queryKey: ['business-dashboard'],
    queryFn: () => api.get('/api/bi/business-dashboard/').then(res => res.data)
  });

  const { data: conversionFunnel, isLoading: conversionLoading } = useQuery({
    queryKey: ['conversion-funnel', selectedPeriod],
    queryFn: () => api.get(`/api/bi/subscription-analysis/conversion-funnel/?days=${selectedPeriod}`).then(res => res.data)
  });

  const { data: churnAnalysis, isLoading: churnLoading } = useQuery({
    queryKey: ['churn-analysis', selectedPeriod],
    queryFn: () => api.get(`/api/bi/subscription-analysis/churn-patterns/?days=${selectedPeriod * 3}`).then(res => res.data)
  });

  const { data: recommendations } = useQuery({
    queryKey: ['bi-recommendations'],
    queryFn: () => api.get('/api/bi/recommendations/').then(res => res.data)
  });

  const MetricCard: React.FC<{
    title: string;
    value: string | number;
    change?: number;
    icon: React.ReactNode;
    prefix?: string;
    suffix?: string;
  }> = ({ title, value, change, icon, prefix = '', suffix = '' }) => (
    <Card>
      <CardContent className="p-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-muted-foreground">{title}</p>
            <p className="text-2xl font-bold">{prefix}{value}{suffix}</p>
            {change !== undefined && (
              <p className={`text-xs ${change > 0 ? 'text-green-600' : 'text-red-600'} flex items-center`}>
                {change > 0 ? <TrendingUp className="w-3 h-3 mr-1" /> : <TrendingDown className="w-3 h-3 mr-1" />}
                {Math.abs(change)}% from last period
              </p>
            )}
          </div>
          <div className="text-muted-foreground">{icon}</div>
        </div>
      </CardContent>
    </Card>
  );

  const FunnelChart: React.FC<{ data: ConversionFunnel }> = ({ data }) => {
    const funnelData = [
      { name: 'Signups', value: data.funnel_data.total_signups, fill: '#8884d8' },
      { name: 'Created Content', value: data.funnel_data.users_with_content, fill: '#82ca9d' },
      { name: 'Started Reviews', value: data.funnel_data.users_with_reviews, fill: '#ffc658' },
      { name: 'Subscribed', value: data.funnel_data.converted_users, fill: '#ff7c7c' }
    ];

    return (
      <div className="space-y-4">
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={funnelData} layout="horizontal">
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis type="number" />
            <YAxis dataKey="name" type="category" width={100} />
            <Tooltip />
            <Bar dataKey="value" fill="#8884d8" />
          </BarChart>
        </ResponsiveContainer>
        
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <h4 className="font-semibold">Conversion Rates</h4>
            <div className="space-y-1 text-sm">
              <div className="flex justify-between">
                <span>Signup → Content:</span>
                <Badge variant="secondary">{data.conversion_rates.signup_to_content}%</Badge>
              </div>
              <div className="flex justify-between">
                <span>Content → Review:</span>
                <Badge variant="secondary">{data.conversion_rates.content_to_review}%</Badge>
              </div>
              <div className="flex justify-between">
                <span>Review → Subscribe:</span>
                <Badge variant="secondary">{data.conversion_rates.review_to_subscription}%</Badge>
              </div>
              <div className="flex justify-between font-medium">
                <span>Overall:</span>
                <Badge>{data.conversion_rates.overall_conversion}%</Badge>
              </div>
            </div>
          </div>
          
          <div className="space-y-2">
            <h4 className="font-semibold">Insights</h4>
            <div className="space-y-1">
              {data.insights.map((insight, index) => (
                <Alert key={index} className="p-2">
                  <AlertTriangle className="h-3 w-3" />
                  <AlertDescription className="text-xs">{insight}</AlertDescription>
                </Alert>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  };

  const TierDistributionChart: React.FC<{ data: Record<string, number> }> = ({ data }) => {
    const pieData = Object.entries(data).map(([tier, count]) => ({
      name: tier,
      value: count,
      fill: COLORS[Object.keys(data).indexOf(tier) % COLORS.length]
    }));

    return (
      <ResponsiveContainer width="100%" height={300}>
        <PieChart>
          <Pie
            data={pieData}
            cx="50%"
            cy="50%"
            labelLine={false}
            label={({ name, value }) => `${name}: ${value}`}
            outerRadius={80}
            fill="#8884d8"
            dataKey="value"
          >
            {pieData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.fill} />
            ))}
          </Pie>
          <Tooltip />
        </PieChart>
      </ResponsiveContainer>
    );
  };

  const RecommendationsList: React.FC<{ recommendations: any[] }> = ({ recommendations }) => (
    <div className="space-y-3">
      {recommendations?.slice(0, 5).map((rec, index) => (
        <Alert key={index} className={`border-l-4 ${
          rec.priority === 'high' ? 'border-l-red-500' : 
          rec.priority === 'medium' ? 'border-l-yellow-500' : 'border-l-green-500'
        }`}>
          <div className="flex items-start space-x-3">
            <Star className="h-4 w-4 mt-0.5" />
            <div className="flex-1">
              <div className="flex items-center justify-between">
                <h4 className="font-medium">{rec.title}</h4>
                <Badge variant={rec.priority === 'high' ? 'destructive' : 'secondary'}>
                  {rec.priority}
                </Badge>
              </div>
              <p className="text-sm text-muted-foreground mt-1">{rec.description}</p>
              <div className="flex items-center space-x-2 mt-2">
                <span className="text-xs">Confidence:</span>
                <Progress value={rec.confidence_score * 100} className="w-20 h-2" />
                <span className="text-xs">{Math.round(rec.confidence_score * 100)}%</span>
              </div>
            </div>
          </div>
        </Alert>
      ))}
    </div>
  );

  if (learningLoading || businessLoading || conversionLoading || churnLoading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
        <span className="ml-2">Loading BI Dashboard...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">Business Intelligence Dashboard</h1>
        <div className="flex items-center space-x-2">
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
      </div>

      {/* Key Metrics Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Total Users"
          value={businessMetrics?.total_users || 0}
          icon={<Users className="w-8 h-8" />}
        />
        <MetricCard
          title="Active Today"
          value={businessMetrics?.active_users_today || 0}
          icon={<Activity className="w-8 h-8" />}
        />
        <MetricCard
          title="Monthly Revenue"
          value={businessMetrics?.monthly_revenue || 0}
          prefix="₩"
          icon={<DollarSign className="w-8 h-8" />}
        />
        <MetricCard
          title="Conversion Rate"
          value={businessMetrics?.conversion_rate || 0}
          suffix="%"
          icon={<Target className="w-8 h-8" />}
        />
      </div>

      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="users">Users & Engagement</TabsTrigger>
          <TabsTrigger value="conversion">Conversion Analysis</TabsTrigger>
          <TabsTrigger value="revenue">Revenue & Subscriptions</TabsTrigger>
          <TabsTrigger value="recommendations">AI Recommendations</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>User Activity Trends</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <AreaChart data={businessMetrics?.daily_active_users_trend?.map((value, index) => ({
                    day: index + 1,
                    users: value
                  })) || []}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="day" />
                    <YAxis />
                    <Tooltip />
                    <Area type="monotone" dataKey="users" stroke="#8884d8" fill="#8884d8" />
                  </AreaChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Key Performance Indicators</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm text-muted-foreground">Retention Rate</p>
                    <p className="text-2xl font-bold">{businessMetrics?.user_retention_rate || 0}%</p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Churn Rate</p>
                    <p className="text-2xl font-bold">{businessMetrics?.churn_rate || 0}%</p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">ARPU</p>
                    <p className="text-2xl font-bold">₩{businessMetrics?.average_revenue_per_user || 0}</p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">System Uptime</p>
                    <p className="text-2xl font-bold">{businessMetrics?.system_uptime || 0}%</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="users" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>User Engagement Metrics</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span>Average Session Duration</span>
                    <span className="font-bold">{businessMetrics?.average_session_duration || 0} min</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Content Completion Rate</span>
                    <span className="font-bold">{businessMetrics?.content_completion_rate || 0}%</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Average Reviews per User</span>
                    <span className="font-bold">{businessMetrics?.average_reviews_per_user || 0}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>AI Adoption Rate</span>
                    <span className="font-bold">{businessMetrics?.ai_adoption_rate || 0}%</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Subscription Tier Distribution</CardTitle>
              </CardHeader>
              <CardContent>
                {businessMetrics?.tier_distribution && (
                  <TierDistributionChart data={businessMetrics.tier_distribution} />
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="conversion" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Conversion Funnel Analysis</CardTitle>
            </CardHeader>
            <CardContent>
              {conversionFunnel && <FunnelChart data={conversionFunnel} />}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="revenue" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Revenue Metrics</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span>Monthly Revenue</span>
                    <span className="font-bold">₩{businessMetrics?.monthly_revenue || 0}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Average Revenue per User</span>
                    <span className="font-bold">₩{businessMetrics?.average_revenue_per_user || 0}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Conversion Rate</span>
                    <span className="font-bold">{businessMetrics?.conversion_rate || 0}%</span>
                  </div>
                  <div className="flex justify-between">
                    <span>AI Cost Efficiency</span>
                    <span className="font-bold">${businessMetrics?.ai_cost_efficiency || 0}</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Churn Analysis</CardTitle>
              </CardHeader>
              <CardContent>
                {churnAnalysis && (
                  <div className="space-y-3">
                    <div className="flex justify-between">
                      <span>Churned Users:</span>
                      <span className="font-bold text-red-600">{churnAnalysis.total_churned_users}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Avg Subscription Duration:</span>
                      <span>{churnAnalysis.average_subscription_duration} days</span>
                    </div>
                    <div className="space-y-2">
                      <h4 className="font-medium">Risk Indicators:</h4>
                      {churnAnalysis.high_risk_indicators.map((indicator, index) => (
                        <Badge key={index} variant="destructive" className="block mb-1">
                          {indicator}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="recommendations" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>AI-Powered Business Recommendations</CardTitle>
            </CardHeader>
            <CardContent>
              <RecommendationsList recommendations={recommendations} />
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default BIDashboard;