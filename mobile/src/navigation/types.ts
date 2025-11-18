import { NavigatorScreenParams } from '@react-navigation/native';
import { NativeStackScreenProps } from '@react-navigation/native-stack';
import { BottomTabScreenProps } from '@react-navigation/bottom-tabs';

// Root Stack Navigator
export type RootStackParamList = {
  Auth: NavigatorScreenParams<AuthStackParamList>;
  Main: NavigatorScreenParams<MainTabParamList>;
};

// Auth Stack Navigator
export type AuthStackParamList = {
  Login: undefined;
  Register: undefined;
  EmailVerification: { email: string; token?: string };
  VerificationPending: { email: string };
};

// Main Tab Navigator
export type MainTabParamList = {
  DashboardTab: undefined;
  ContentTab: NavigatorScreenParams<ContentStackParamList>;
  ReviewTab: undefined;
  ExamsTab: NavigatorScreenParams<ExamsStackParamList>;
  ProfileTab: undefined;
};

// Content Stack Navigator
export type ContentStackParamList = {
  ContentList: undefined;
  ContentDetail: { id: number };
  ContentCreate: undefined;
  ContentEdit: { id: number };
};

// Exams Stack Navigator
export type ExamsStackParamList = {
  ExamList: undefined;
  ExamDetail: { id: number };
  ExamCreate: undefined;
  ExamResult: { id: number };
};

// Screen Props Types
export type RootStackScreenProps<T extends keyof RootStackParamList> =
  NativeStackScreenProps<RootStackParamList, T>;

export type AuthStackScreenProps<T extends keyof AuthStackParamList> =
  NativeStackScreenProps<AuthStackParamList, T>;

export type MainTabScreenProps<T extends keyof MainTabParamList> =
  BottomTabScreenProps<MainTabParamList, T>;

export type ContentStackScreenProps<T extends keyof ContentStackParamList> =
  NativeStackScreenProps<ContentStackParamList, T>;

export type ExamsStackScreenProps<T extends keyof ExamsStackParamList> =
  NativeStackScreenProps<ExamsStackParamList, T>;
