"use client";

import { motion } from "framer-motion";
import { CreditCard, ArrowRight } from "lucide-react";
import Link from "next/link";

interface UserWelcomeProps {
  name: string | null;
  email: string;
  credits: number;
  plan: string;
  avatarUrl: string | null;
  createdAt: string;
}

export function UserWelcome({ name, email, credits, plan, avatarUrl, createdAt }: UserWelcomeProps) {
  const displayName = name || email.split("@")[0];
  const memberSince = new Date(createdAt).toLocaleDateString("en-US", {
    month: "long",
    year: "numeric",
  });

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, ease: [0.25, 0.46, 0.45, 0.94] }}
      className="relative overflow-hidden glass rounded-2xl p-6 md:p-8"
    >
      {/* Background decoration */}
      <div className="absolute top-0 right-0 w-64 h-64 bg-primary/5 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2" />
      <div className="absolute bottom-0 left-0 w-48 h-48 bg-purple-500/5 rounded-full blur-3xl translate-y-1/2 -translate-x-1/2" />

      <div className="relative flex items-center gap-5">
        {/* Avatar */}
        <motion.div
          initial={{ scale: 0, rotate: -180 }}
          animate={{ scale: 1, rotate: 0 }}
          transition={{ type: "spring", stiffness: 200, damping: 15, delay: 0.2 }}
        >
          {avatarUrl ? (
            <img
              src={avatarUrl}
              alt={displayName}
              className="h-16 w-16 rounded-2xl object-cover ring-2 ring-primary/30 shadow-lg shadow-primary/20"
            />
          ) : (
            <div className="h-16 w-16 rounded-2xl bg-gradient-to-br from-primary to-purple-600 flex items-center justify-center shadow-lg shadow-primary/20">
              <span className="text-2xl font-bold text-white">{displayName[0].toUpperCase()}</span>
            </div>
          )}
        </motion.div>

        {/* Info */}
        <div className="flex-1 min-w-0">
          <motion.h1
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.3, duration: 0.3 }}
            className="text-xl md:text-2xl font-bold"
          >
            Welcome back, {displayName}
          </motion.h1>
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.4, duration: 0.3 }}
            className="text-sm text-muted-foreground mt-1"
          >
            Member since {memberSince}
          </motion.p>

          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5, duration: 0.3 }}
            className="flex items-center gap-3 mt-3"
          >
            <div className="flex items-center gap-1.5 bg-primary/10 rounded-lg px-3 py-1.5">
              <CreditCard className="h-3.5 w-3.5 text-primary" />
              <span className="text-sm font-semibold text-primary">{credits}</span>
              <span className="text-xs text-muted-foreground">credits</span>
            </div>
            <span className="text-xs bg-secondary/50 rounded-md px-2 py-1 text-muted-foreground font-medium">{plan}</span>
          </motion.div>
        </div>

        {/* CTA */}
        <Link href="/generate" className="hidden md:flex items-center gap-1.5 text-sm text-primary hover:underline font-medium flex-shrink-0">
          Start creating <ArrowRight className="h-3.5 w-3.5" />
        </Link>
      </div>
    </motion.div>
  );
}
