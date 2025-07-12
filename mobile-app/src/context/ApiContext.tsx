import React, { createContext, useContext, useReducer, ReactNode } from 'react';
import axios from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { showMessage } from 'react-native-flash-message';
import { useError } from './ErrorContext';

// Types
export interface Post {
  id: number;
  message_id: string;
  channel_name: string;
  sender_name: string;
  original_text: string;
  translated_text: string;
  media_type?: string;
  media_path?: string;
  classification: string;
  quality_score: number;
  bias_score: number;
  status: string;
  created_at: string;
  processed_at?: string;
  posted_at?: string;
  twitter_url?: string;
  telegram_url?: string;
  priority: number;
}

export interface Analytics {
  posts_by_status: Record<string, number>;
  posts_by_channel: Record<string, number>;
  daily_posts: Record<string, number>;
  user_actions: Record<string, number>;
  quality_metrics: {
    avg_quality: number;
    avg_bias: number;
    total_posts: number;
  };
}

export interface Stats {
  total_posts: number;
  pending_posts: number;
  posted_count: number;
  deleted_count: number;
  archived_count: number;
  post_rate: number;
  delete_rate: number;
}

interface ApiState {
  posts: Post[];
  analytics: Analytics | null;
  stats: Stats | null;
  loading: boolean;
  error: string | null;
  apiUrl: string;
}

type ApiAction =
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'SET_ERROR'; payload: string | null }
  | { type: 'SET_POSTS'; payload: Post[] }
  | { type: 'SET_ANALYTICS'; payload: Analytics }
  | { type: 'SET_STATS'; payload: Stats }
  | { type: 'SET_API_URL'; payload: string }
  | { type: 'UPDATE_POST'; payload: { id: number; updates: Partial<Post> } };

const initialState: ApiState = {
  posts: [],
  analytics: null,
  stats: null,
  loading: false,
  error: null,
  apiUrl: 'https://web-production-a5f83.up.railway.app', // Default API URL
};

const apiReducer = (state: ApiState, action: ApiAction): ApiState => {
  switch (action.type) {
    case 'SET_LOADING':
      return { ...state, loading: action.payload };
    case 'SET_ERROR':
      return { ...state, error: action.payload, loading: false };
    case 'SET_POSTS':
      return { ...state, posts: action.payload, loading: false };
    case 'SET_ANALYTICS':
      return { ...state, analytics: action.payload, loading: false };
    case 'SET_STATS':
      return { ...state, stats: action.payload, loading: false };
    case 'SET_API_URL':
      return { ...state, apiUrl: action.payload };
    case 'UPDATE_POST':
      return {
        ...state,
        posts: state.posts.map(post =>
          post.id === action.payload.id
            ? { ...post, ...action.payload.updates }
            : post
        ),
      };
    default:
      return state;
  }
};

interface ApiContextValue {
  state: ApiState;
  fetchPosts: (status?: string, limit?: number, offset?: number) => Promise<void>;
  performAction: (postId: number, actionType: string, notes?: string, twitterUrl?: string) => Promise<void>;
  batchAction: (postIds: number[], actionType: string, notes?: string) => Promise<void>;
  fetchAnalytics: (days?: number) => Promise<void>;
  fetchStats: () => Promise<void>;
  setApiUrl: (url: string) => Promise<void>;
  refreshData: () => Promise<void>;
}

const ApiContext = createContext<ApiContextValue | undefined>(undefined);

export const ApiProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [state, dispatch] = useReducer(apiReducer, initialState);

  // Load API URL from storage on mount
  React.useEffect(() => {
    loadApiUrl();
  }, []);

  const loadApiUrl = async () => {
    try {
      const savedUrl = await AsyncStorage.getItem('apiUrl');
      if (savedUrl) {
        dispatch({ type: 'SET_API_URL', payload: savedUrl });
      }
    } catch (error) {
      console.error('Failed to load API URL:', error);
    }
  };

  const setApiUrl = async (url: string) => {
    try {
      await AsyncStorage.setItem('apiUrl', url);
      dispatch({ type: 'SET_API_URL', payload: url });
      showMessage({
        message: 'API URL updated successfully',
        type: 'success',
      });
    } catch (error) {
      console.error('Failed to save API URL:', error);
      showMessage({
        message: 'Failed to save API URL',
        type: 'danger',
      });
    }
  };

  const handleApiError = (error: any, defaultMessage: string) => {
    let message = defaultMessage;
    let title = 'Error';
    
    if (error.response) {
      // Server responded with error status
      const status = error.response.status;
      message = error.response.data?.error || error.response.data?.message || defaultMessage;
      
      if (status === 404) {
        title = 'Not Found';
        message = 'The requested resource was not found. Please check your API URL.';
      } else if (status === 500) {
        title = 'Server Error';
        message = 'Internal server error. Please try again later.';
      } else if (status === 401) {
        title = 'Unauthorized';
        message = 'Authentication failed. Please check your credentials.';
      } else if (status === 403) {
        title = 'Forbidden';
        message = 'You do not have permission to perform this action.';
      }
    } else if (error.request) {
      // Network error
      title = 'Network Error';
      message = 'Unable to connect to the server. Please check your internet connection and API URL.';
    } else {
      // Other error
      message = error.message || defaultMessage;
    }
    
    dispatch({ type: 'SET_ERROR', payload: message });
    showMessage({
      message,
      type: 'danger',
    });
    
    console.error('API Error:', {
      title,
      message,
      error: error.response?.data || error.message,
      status: error.response?.status,
    });
  };

  const fetchPosts = async (status?: string, limit = 50, offset = 0, retryCount = 0) => {
    dispatch({ type: 'SET_LOADING', payload: true });
    try {
      const params = new URLSearchParams();
      if (status) params.append('status', status);
      params.append('limit', limit.toString());
      params.append('offset', offset.toString());

      const token = await AsyncStorage.getItem('access_token');

      const response = await axios.get(`${state.apiUrl}/api/posts?${params}`, {
        timeout: 10000, // 10 second timeout
        headers: { Authorization: `Bearer ${token}` },
      });
      dispatch({ type: 'SET_POSTS', payload: response.data.posts });
      dispatch({ type: 'SET_ERROR', payload: null }); // Clear any previous errors
    } catch (error) {
      if (retryCount < 2 && (error.code === 'ECONNABORTED' || error.code === 'NETWORK_ERROR')) {
        // Retry on timeout or network error
        console.log(`Retrying fetchPosts... attempt ${retryCount + 1}`);
        setTimeout(() => fetchPosts(status, limit, offset, retryCount + 1), 1000 * (retryCount + 1));
      } else {
        handleApiError(error, 'Failed to fetch posts');
      }
    }
  };

  const performAction = async (postId: number, actionType: string, notes?: string, twitterUrl?: string) => {
    try {
      const payload: any = { action_type: actionType };
      if (notes) payload.notes = notes;
      if (twitterUrl) payload.twitter_url = twitterUrl;

      const token = await AsyncStorage.getItem('access_token');

      const response = await axios.post(`${state.apiUrl}/api/posts/${postId}/action`, payload, {
        headers: { Authorization: `Bearer ${token}` },
      });
      
      // Update post in local state
      dispatch({
        type: 'UPDATE_POST',
        payload: {
          id: postId,
          updates: { status: response.data.new_status },
        },
      });

      showMessage({
        message: response.data.message,
        type: 'success',
      });
    } catch (error) {
      handleApiError(error, 'Failed to perform action');
    }
  };

  const batchAction = async (postIds: number[], actionType: string, notes?: string) => {
    try {
      const payload = {
        post_ids: postIds,
        action_type: actionType,
        notes: notes || '',
      };

      const token = await AsyncStorage.getItem('access_token');

      const response = await axios.post(`${state.apiUrl}/api/posts/batch-action`, payload, {
        headers: { Authorization: `Bearer ${token}` },
      });
      
      // Update posts in local state
      postIds.forEach(postId => {
        dispatch({
          type: 'UPDATE_POST',
          payload: {
            id: postId,
            updates: { status: actionType === 'delete' ? 'deleted' : 'processed' },
          },
        });
      });

      showMessage({
        message: response.data.message,
        type: 'success',
      });
    } catch (error) {
      handleApiError(error, 'Failed to perform batch action');
    }
  };

  const fetchAnalytics = async (days = 7) => {
    dispatch({ type: 'SET_LOADING', payload: true });
    try {
      const token = await AsyncStorage.getItem('access_token');

      const response = await axios.get(`${state.apiUrl}/api/analytics?days=${days}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      dispatch({ type: 'SET_ANALYTICS', payload: response.data.analytics });
    } catch (error) {
      handleApiError(error, 'Failed to fetch analytics');
    }
  };

  const fetchStats = async () => {
    try {
      const token = await AsyncStorage.getItem('access_token');

      const response = await axios.get(`${state.apiUrl}/api/stats`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      dispatch({ type: 'SET_STATS', payload: response.data.stats });
    } catch (error) {
      handleApiError(error, 'Failed to fetch stats');
    }
  };

  const refreshData = async () => {
    await Promise.all([
      fetchPosts(),
      fetchStats(),
      fetchAnalytics(),
    ]);
  };

  const value: ApiContextValue = {
    state,
    fetchPosts,
    performAction,
    batchAction,
    fetchAnalytics,
    fetchStats,
    setApiUrl,
    refreshData,
  };

  return (
    <ApiContext.Provider value={value}>
      {children}
    </ApiContext.Provider>
  );
};

export const useApi = (): ApiContextValue => {
  const context = useContext(ApiContext);
  if (!context) {
    throw new Error('useApi must be used within an ApiProvider');
  }
  return context;
}; 