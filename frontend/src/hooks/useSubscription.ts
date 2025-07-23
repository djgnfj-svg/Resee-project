import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { subscriptionAPI } from '../utils/api';
import { Subscription, SubscriptionUpgradeData } from '../types';

export const useSubscription = () => {
  const queryClient = useQueryClient();

  const subscriptionQuery = useQuery({
    queryKey: ['subscription'],
    queryFn: subscriptionAPI.getSubscription,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  const subscriptionTiersQuery = useQuery({
    queryKey: ['subscription-tiers'],
    queryFn: subscriptionAPI.getSubscriptionTiers,
    staleTime: 30 * 60 * 1000, // 30 minutes
  });

  const upgradeMutation = useMutation({
    mutationFn: (data: SubscriptionUpgradeData) => subscriptionAPI.upgradeSubscription(data),
    onSuccess: (updatedSubscription: Subscription) => {
      // Update subscription cache
      queryClient.setQueryData(['subscription'], updatedSubscription);
      
      // Invalidate related queries to refresh data
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
      queryClient.invalidateQueries({ queryKey: ['review-schedules'] });
    },
  });

  return {
    subscription: subscriptionQuery.data,
    subscriptionTiers: subscriptionTiersQuery.data,
    isLoadingSubscription: subscriptionQuery.isLoading,
    isLoadingTiers: subscriptionTiersQuery.isLoading,
    subscriptionError: subscriptionQuery.error,
    tiersError: subscriptionTiersQuery.error,
    upgradeSubscription: upgradeMutation.mutate,
    isUpgrading: upgradeMutation.isPending,
    upgradeError: upgradeMutation.error,
    upgradeSuccess: upgradeMutation.isSuccess,
  };
};