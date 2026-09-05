"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import Link from "next/link";
import { BarChart3, ArrowRight, Zap } from "lucide-react";
import { billingApi } from "@/lib/api";

interface UsageWidgetProps {
  token: string;
}

export function UsageWidget({ token }: UsageWidgetProps) {
  const [usage, setUsage] = useState<{
    generations_today: number;
    generations_this_month: number;
    credits_used_today: number;
  } | null>(null);

  useEffect(() => {
    billingApi.usage(token).then(setUsage).catch(() => {});
  }, [token]);

  if (!usage) return null;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: 0.6 }}
      className="glass rounded-xl p-5 space-y-3"
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="h-7 w-7 rounded-lg bg-blue-500/10 flex items-center justify-center">
            <BarChart3 className="h-3.5 w-3.5 text-blue-500" />
          </div>
          <span className="text-xs font-semibold">Usage</span>
        </div>
        <Link href="/billing" className="text-[10px] text-muted-foreground hover:text-foreground flex items-center gap-0.5 transition-colors">
          Details <ArrowRight className="h-2.5 w-2.5" />
        </Link>
      </div>

      <div className="grid grid-cols-2 gap-2">
        <div className="bg-secondary/30 rounded-lg p-2.5">
          <div className="flex items-center gap-1">
            <Zap className="h-2.5 w-2.5 text-primary" />
            <span className="text-lg font-bold">{usage.generations_today}</span>
          </div>
          <p className="text-[9px] text-muted-foreground uppercase">Today</p>
        </div>
        <div className="bg-secondary/30 rounded-lg p-2.5">
          <div className="flex items-center gap-1">
            <BarChart3 className="h-2.5 w-2.5 text-blue-500" />
            <span className="text-lg font-bold">{usage.generations_this_month}</span>
          </div>
          <p className="text-[9px] text-muted-foreground uppercase">This month</p>
        </div>
      </div>
    </motion.div>
  );
}
