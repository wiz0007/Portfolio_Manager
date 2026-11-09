import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { authService } from '../services/authService';
import { LoginRequest, RegisterRequest, User } from '../types/auth';
import { ApiClientError } from '@/services/api/client';

export const AUTH_USER_QUERY_KEY = ['currentUser'];

export function useCurrentUser() {
  return useQuery<User | null, ApiClientError>({
    queryKey: AUTH_USER_QUERY_KEY,
    queryFn: async () => {
      try {
        return await authService.getCurrentUser();
      } catch (err: any) {
        if (err instanceof ApiClientError && (err.status === 401 || err.status === 403)) {
          return null;
        }
        throw err;
      }
    },
    retry: false,
    staleTime: 5 * 60 * 1000,
  });
}

export function useLogin() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (credentials: LoginRequest) => authService.login(credentials),
    onSuccess: (data) => {
      queryClient.setQueryData(AUTH_USER_QUERY_KEY, data.user);
    },
  });
}

export function useRegister() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: RegisterRequest) => authService.register(payload),
    onSuccess: (data) => {
      queryClient.setQueryData(AUTH_USER_QUERY_KEY, data.user);
    },
  });
}

export function useLogout() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () => authService.logout(),
    onSuccess: () => {
      queryClient.setQueryData(AUTH_USER_QUERY_KEY, null);
      queryClient.invalidateQueries({ queryKey: AUTH_USER_QUERY_KEY });
    },
  });
}
