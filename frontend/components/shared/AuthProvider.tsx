"use client";

import { useEffect } from "react";
import { useAuthStore } from "@/stores/authStore";
import { authApi } from "@/lib/api";

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const { setAuth, logout } = useAuthStore();

  useEffect(() => {
    const storedToken = localStorage.getItem("token");
    if (storedToken) {
      authApi
        .me(storedToken)
        .then((userData) => setAuth(userData, storedToken))
        .catch(() => logout());
    } else {
      useAuthStore.setState({ isLoading: false });
    }
  }, []);

  return <>{children}</>;
}
