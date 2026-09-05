"use client";

import { motion } from "framer-motion";
import { Image as ImageIcon, Heart, Globe, Share2, CreditCard, Sparkles } from "lucide-react";

interface StatsCardsProps {
  stats: {
    total_images: number;
    total_favorites: number;
    total_public: number;
    total_shares: number;
  };
  credits: number;
}

const cardVariants = {
  hidden: { opacity: 0, y: 20, scale: 0.95 },
  visible: (i: number) => ({
    opacity: 1,
    y: 0,
    scale: 1,
    transition: {
      delay: i * 0.08,
      duration: 0.4,
      ease: [0.25, 0.46, 0.45, 0.94],
    },
  }),
};

const iconPulse = {
  hidden: { scale: 0, rotate: -30 },
  visible: (i: number) => ({
    scale: 1,
    rotate: 0,
    transition: {
      delay: i * 0.08 + 0.2,
      type: "spring",
      stiffness: 300,
      damping: 15,
    },
  }),
};

const cards = (stats: StatsCardsProps["stats"], credits: number) => [
  { label: "Total Images", value: stats.total_images, icon: ImageIcon, color: "text-purple-500", bg: "bg-purple-500/10" },
  { label: "Favorites", value: stats.total_favorites, icon: Heart, color: "text-red-500", bg: "bg-red-500/10" },
  { label: "Public", value: stats.total_public, icon: Globe, color: "text-green-500", bg: "bg-green-500/10" },
  { label: "Shared", value: stats.total_shares, icon: Share2, color: "text-blue-500", bg: "bg-blue-500/10" },
  { label: "Credits Left", value: credits, icon: CreditCard, color: "text-yellow-500", bg: "bg-yellow-500/10" },
  { label: "Generations", value: stats.total_images, icon: Sparkles, color: "text-primary", bg: "bg-primary/10" },
];

export function StatsCards({ stats, credits }: StatsCardsProps) {
  const items = cards(stats, credits);

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
      {items.map((card, i) => (
        <motion.div
          key={card.label}
          custom={i}
          variants={cardVariants}
          initial="hidden"
          animate="visible"
          whileHover={{ y: -2, transition: { duration: 0.2 } }}
          className="glass rounded-xl p-4 cursor-default"
        >
          <div className="flex items-center gap-3 mb-3">
            <motion.div
              custom={i}
              variants={iconPulse}
              initial="hidden"
              animate="visible"
              className={`h-9 w-9 rounded-lg ${card.bg} flex items-center justify-center`}
            >
              <card.icon className={`h-4 w-4 ${card.color}`} />
            </motion.div>
          </div>
          <motion.p
            className="text-2xl font-bold tracking-tight"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: i * 0.08 + 0.3, duration: 0.3 }}
          >
            {card.value.toLocaleString()}
          </motion.p>
          <p className="text-[10px] text-muted-foreground uppercase tracking-wider mt-1">{card.label}</p>
        </motion.div>
      ))}
    </div>
  );
}
