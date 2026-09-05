"use client";

import { useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/stores/authStore";
import { authApi } from "@/lib/api";

export function useAuth({ redirectIfUnauthenticated }: { redirectIfUnauthenticated?: boolean } = {}) {
  const { user, token, isLoading, setAuth, setUser, logout } = useAuthStore();
  const router = useRouter();

  useEffect(() => {
    const storedToken = typeof window !== "undefined" ? localStorage.getItem("token") : null;
    if (storedToken && !user) {
      authApi
        .me(storedToken)
        .then((userData) => setAuth(userData, storedToken))
        .catch(() => {
          logout();
          if (redirectIfUnauthenticated) router.push("/auth/login");
        });
    } else if (!storedToken && !user) {
      useAuthStore.setState({ isLoading: false });
      if (redirectIfUnauthenticated) router.push("/auth/login");
    }
  }, []);

  const login = useCallback(
    async (email: string, password: string) => {
      const result = await authApi.login({ email, password });
      setAuth(result.user, result.access_token);
      return result;
    },
    [setAuth]
  );

  const register = useCallback(
    async (email: string, password: string, name?: string) => {
      const result = await authApi.register({ email, password, name });
      setAuth(result.user, result.access_token);
      return result;
    },
    [setAuth]
  );

  const quickLogin = useCallback(
    async (email = "creator@auracraft.ai", name = "Aura Creator") => {
      const result = await authApi.register({ email, password: "demo-password", name });
      setAuth(result.user, result.access_token);
      return result;
    },
    [setAuth]
  );

  const googleLogin = useCallback(
    async (credential: string) => {
      const result = await authApi.googleLogin(credential);
      setAuth(result.user, result.access_token);
      return result;
    },
    [setAuth]
  );

  const forgotPassword = useCallback(async (email: string) => {
    return authApi.forgotPassword(email);
  }, []);

  const resetPassword = useCallback(async (token: string, newPassword: string) => {
    return authApi.resetPassword(token, newPassword);
  }, []);

  const updateProfile = useCallback(
    async (data: { name?: string; avatar_url?: string }) => {
      const storedToken = token || localStorage.getItem("token");
      if (!storedToken) throw new Error("Not authenticated");
      const updated = await authApi.updateProfile(data, storedToken);
      setUser(updated);
      return updated;
    },
    [token, setUser]
  );

  const changePassword = useCallback(
    async (currentPassword: string, newPassword: string) => {
      const storedToken = token || localStorage.getItem("token");
      if (!storedToken) throw new Error("Not authenticated");
      return authApi.changePassword(
        { current_password: currentPassword, new_password: newPassword },
        storedToken
      );
    },
    [token]
  );

  return {
    user,
    token,
    isLoading,
    isAuthenticated: !!user,
    login,
    register,
    quickLogin,
    googleLogin,
    logout,
    forgotPassword,
    resetPassword,
    updateProfile,
    changePassword,
  };
}
