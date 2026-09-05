"use client";

import { motion } from "framer-motion";
import Link from "next/link";
import { Sparkles, Image as ImageIcon, Globe, Heart, CreditCard, Settings } from "lucide-react";

const actions = [
  { label: "Generate", icon: Sparkles, href: "/generate", color: "from-primary to-purple-600" },
  { label: "My Images", icon: ImageIcon, href: "/images", color: "from-blue-500 to-cyan-500" },
  { label: "Gallery", icon: Globe, href: "/gallery", color: "from-green-500 to-emerald-500" },
  { label: "Favorites", icon: Heart, href: "/images?tab=favorites", color: "from-red-500 to-pink-500" },
  { label: "Billing", icon: CreditCard, href: "/profile", color: "from-yellow-500 to-orange-500" },
  { label: "Settings", icon: Settings, href: "/profile", color: "from-gray-500 to-slate-500" },
];

export function QuickActions() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: 0.4 }}
      className="glass rounded-xl p-5 space-y-4"
    >
      <h3 className="text-sm font-semibold">Quick Actions</h3>
      <div className="grid grid-cols-3 gap-2">
        {actions.map((action, i) => (
          <Link key={action.label} href={action.href}>
            <motion.div
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.5 + i * 0.05, type: "spring", stiffness: 300, damping: 20 }}
              whileHover={{ scale: 1.05, y: -2 }}
              whileTap={{ scale: 0.95 }}
              className="flex flex-col items-center gap-2 p-3 rounded-xl bg-secondary/30 hover:bg-secondary/60 transition-colors cursor-pointer"
            >
              <div className={`h-10 w-10 rounded-xl bg-gradient-to-br ${action.color} flex items-center justify-center shadow-lg`}>
                <action.icon className="h-4 w-4 text-white" />
              </div>
              <span className="text-[10px] text-muted-foreground font-medium">{action.label}</span>
            </motion.div>
          </Link>
        ))}
      </div>
    </motion.div>
  );
}
