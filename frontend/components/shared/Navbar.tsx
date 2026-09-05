"use client";

import Link from "next/link";
import { useAuth } from "@/hooks/useAuth";
import { useThemeStore } from "@/stores/themeStore";
import { Button } from "@/components/ui/button";
import { Sparkles, LogOut, CreditCard, User, Image as ImageIcon, Sun, Moon, LayoutDashboard, Receipt, Shield } from "lucide-react";
import { motion } from "framer-motion";

export function Navbar() {
  const { user, isLoading, logout } = useAuth();
  const { resolvedTheme, toggleTheme } = useThemeStore();

  return (
    <motion.header
      initial={{ y: -20, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.3, ease: "easeOut" }}
      className="sticky top-0 z-50 w-full border-b border-border/40 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60"
    >
      <div className="max-w-7xl mx-auto flex h-16 items-center justify-between px-4">
        <Link href="/" className="flex items-center gap-2">
          <motion.div whileHover={{ rotate: 15, scale: 1.1 }} transition={{ type: "spring", stiffness: 400 }}>
            <Sparkles className="h-6 w-6 text-primary" />
          </motion.div>
          <span className="text-lg font-bold">Text2Img</span>
        </Link>

        <nav className="flex items-center gap-2 md:gap-4">
          <Link href="/studio" className="flex items-center gap-1.5 text-xs font-semibold px-3 py-1.5 rounded-lg bg-gradient-to-r from-purple-500/20 to-cyan-500/20 border border-purple-500/30 text-purple-300 hover:text-white transition shadow-sm">
            <Sparkles className="h-3.5 w-3.5 text-purple-400" />
            <span>AI Studio</span>
          </Link>

          <Link href="/gallery" className="text-sm text-muted-foreground hover:text-foreground transition-colors hidden sm:inline">
            Gallery
          </Link>
          {user ? (
            <>
              <Link href="/dashboard" className="text-sm text-muted-foreground hover:text-foreground transition-colors hidden md:inline-flex items-center gap-1">
                <LayoutDashboard className="h-3.5 w-3.5" /> Dashboard
              </Link>
              {user.role === "admin" && (
                <Link href="/admin" className="text-sm text-primary hover:text-primary/80 transition-colors hidden md:inline-flex items-center gap-1 font-medium">
                  <Shield className="h-3.5 w-3.5" /> Admin
                </Link>
              )}
              <Link href="/generate">
                <Button size="sm">
                  <Sparkles className="h-3.5 w-3.5 mr-1" /> Create
                </Button>
              </Link>
              <Link href="/images" className="text-sm text-muted-foreground hover:text-foreground transition-colors hidden sm:inline-flex items-center gap-1">
                <ImageIcon className="h-3.5 w-3.5" /> My Images
              </Link>
              <button
                onClick={toggleTheme}
                className="h-8 w-8 rounded-lg bg-secondary/50 flex items-center justify-center hover:bg-secondary transition-colors"
                title={`Switch to ${resolvedTheme === "dark" ? "light" : "dark"} mode`}
              >
                {resolvedTheme === "dark" ? (
                  <Sun className="h-4 w-4 text-muted-foreground" />
                ) : (
                  <Moon className="h-4 w-4 text-muted-foreground" />
                )}
              </button>
              <Link href="/billing" className="flex items-center gap-1.5 text-sm bg-primary/10 rounded-lg px-2.5 py-1 hover:bg-primary/15 transition-colors">
                <CreditCard className="h-3.5 w-3.5 text-primary" />
                <span className="font-semibold text-primary">{user.credits}</span>
              </Link>
              <Link
                href="/profile"
                className="flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors"
              >
                {user.avatar_url ? (
                  <img src={user.avatar_url} alt="" className="h-7 w-7 rounded-full object-cover ring-2 ring-primary/20" />
                ) : (
                  <div className="h-7 w-7 rounded-full bg-primary/10 flex items-center justify-center">
                    <User className="h-3.5 w-3.5 text-primary" />
                  </div>
                )}
              </Link>
              <Button variant="ghost" size="icon" onClick={logout} title="Sign out" className="h-8 w-8">
                <LogOut className="h-4 w-4" />
              </Button>
            </>
          ) : !isLoading ? (
            <div className="flex items-center gap-2">
              <Link href="/studio">
                <Button size="sm" variant="default" className="text-xs">
                  <Sparkles className="h-3.5 w-3.5 mr-1" /> Create
                </Button>
              </Link>
              <Link href="/auth/login">
                <Button size="sm" variant="ghost" className="text-xs">Sign In</Button>
              </Link>
            </div>
          ) : null}
        </nav>
      </div>
    </motion.header>
  );
}
