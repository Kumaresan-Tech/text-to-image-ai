"use client";

import { useState, useEffect, useCallback } from "react";
import { ProtectedRoute } from "@/components/shared/ProtectedRoute";
import { useAuth } from "@/hooks/useAuth";
import { useGenerationStore } from "@/stores/generationStore";
import { imagesApi } from "@/lib/api";
import { UserWelcome } from "@/components/dashboard/UserWelcome";
import { StatsCards } from "@/components/dashboard/StatsCards";
import { RecentGenerations } from "@/components/dashboard/RecentGenerations";
import { QuickGenerate } from "@/components/dashboard/QuickGenerate";
import { QuickEnhance } from "@/components/dashboard/QuickEnhance";
import { QuickActions } from "@/components/dashboard/QuickActions";
import { DailyTip } from "@/components/dashboard/DailyTip";
import { UsageWidget } from "@/components/dashboard/UsageWidget";
import { StaggerContainer, FadeUp } from "@/components/dashboard/MotionWrapper";

function DashboardContent() {
  const { user, token } = useAuth();
  const { images } = useGenerationStore();
  const [stats, setStats] = useState({
    total_images: 0,
    total_favorites: 0,
    total_public: 0,
    total_shares: 0,
  });
  const [recentImages, setRecentImages] = useState<any[]>([]);

  const loadStats = useCallback(async () => {
    if (!token) return;
    try {
      const data = await imagesApi.stats(token);
      setStats(data);
    } catch {}
  }, [token]);

  const loadRecent = useCallback(async () => {
    if (!token) return;
    try {
      const data = await imagesApi.list(1, 8, token);
      setRecentImages(data.images);
    } catch {}
  }, [token]);

  useEffect(() => { loadStats(); }, [loadStats]);
  useEffect(() => { loadRecent(); }, [loadRecent]);

  // Merge generation store images with recent
  const allRecent = [
    ...images.map((img) => ({
      id: img.id,
      prompt: img.prompt,
      image_url: img.image_url,
      model: img.model,
      likes_count: 0,
      created_at: img.created_at,
    })),
    ...recentImages,
  ].slice(0, 8);

  if (!user) return null;

  return (
    <div className="max-w-7xl mx-auto px-4 py-6 space-y-6">
      <UserWelcome
        name={user.name}
        email={user.email}
        credits={user.credits}
        plan={user.plan}
        avatarUrl={user.avatar_url}
        createdAt={user.created_at}
      />

      <StatsCards stats={stats} credits={user.credits} />

      <div className="grid lg:grid-cols-[1fr_340px] gap-6">
        {/* Main content */}
        <StaggerContainer className="space-y-6">
          <FadeUp>
            <RecentGenerations images={allRecent} />
          </FadeUp>
        </StaggerContainer>

        {/* Sidebar */}
        <div className="space-y-4">
          <QuickGenerate />
          <QuickEnhance />
          {token && <UsageWidget token={token} />}
          <QuickActions />
          <DailyTip />
        </div>
      </div>
    </div>
  );
}

export default function DashboardPage() {
  return (
    <ProtectedRoute>
      <DashboardContent />
    </ProtectedRoute>
  );
}
