"use client";

import { Shield, ShieldAlert, ShieldCheck, Loader2 } from "lucide-react";

interface SafetyBadgeProps {
  isSafe: boolean | null;
  flags?: string[];
  isLoading?: boolean;
  className?: string;
}

export function SafetyBadge({ isSafe, flags = [], isLoading, className = "" }: SafetyBadgeProps) {
  if (isLoading) {
    return (
      <div className={`inline-flex items-center gap-1.5 text-xs text-muted-foreground ${className}`}>
        <Loader2 className="h-3 w-3 animate-spin" />
        Checking...
      </div>
    );
  }

  if (isSafe === null) return null;

  if (isSafe) {
    return (
      <div className={`inline-flex items-center gap-1.5 text-xs text-green-500 ${className}`}>
        <ShieldCheck className="h-3 w-3" />
        Safe
      </div>
    );
  }

  return (
    <div className={`group relative inline-flex items-center gap-1.5 text-xs text-amber-500 ${className}`}>
      <ShieldAlert className="h-3 w-3" />
      Flagged
      {flags.length > 0 && (
        <div className="hidden group-hover:block absolute bottom-full left-0 mb-1 w-56 p-2 rounded-lg bg-popover border border-border shadow-lg z-10">
          <p className="text-[10px] font-medium text-foreground mb-1">Content flags:</p>
          {flags.map((f, i) => (
            <p key={i} className="text-[10px] text-muted-foreground">- {f}</p>
          ))}
        </div>
      )}
    </div>
  );
}
