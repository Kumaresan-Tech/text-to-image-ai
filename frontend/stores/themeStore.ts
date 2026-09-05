"use client";

import { create } from "zustand";

type Theme = "dark" | "light" | "system";

interface ThemeState {
  theme: Theme;
  resolvedTheme: "dark" | "light";
  setTheme: (theme: Theme) => void;
  toggleTheme: () => void;
}

function getSystemTheme(): "dark" | "light" {
  if (typeof window === "undefined") return "dark";
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

function applyTheme(resolved: "dark" | "light") {
  const root = document.documentElement;
  root.classList.remove("dark", "light");
  root.classList.add(resolved);
}

function resolveTheme(theme: Theme): "dark" | "light" {
  return theme === "system" ? getSystemTheme() : theme;
}

export const useThemeStore = create<ThemeState>((set, get) => ({
  theme: (typeof window !== "undefined" ? (localStorage.getItem("theme") as Theme) : null) || "dark",
  resolvedTheme: "dark",

  setTheme: (theme) => {
    const resolved = resolveTheme(theme);
    localStorage.setItem("theme", theme);
    applyTheme(resolved);
    set({ theme, resolvedTheme: resolved });
  },

  toggleTheme: () => {
    const current = get().resolvedTheme;
    const next: Theme = current === "dark" ? "light" : "dark";
    const resolved = resolveTheme(next);
    localStorage.setItem("theme", next);
    applyTheme(resolved);
    set({ theme: next, resolvedTheme: resolved });
  },
}));
