"use client";

import { useEffect, useState, useCallback } from "react";
import { useAuthStore } from "@/stores/authStore";
import { adminApi } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Users, Image, Activity, AlertTriangle, CheckCircle,
  Shield, Ban, Unlock, Trash2, Eye, Search, ChevronLeft,
  ChevronRight, RefreshCw, Clock, Zap, TrendingUp,
  ArrowUpRight, BarChart3, ScrollText, Server
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

export default function AdminPage() {
  const { token, user } = useAuthStore();
  const [tab, setTab] = useState("stats");
  const [stats, setStats] = useState<any>(null);
  const [health, setHealth] = useState<any>(null);
  const [users, setUsers] = useState<any[]>([]);
  const [usersTotal, setUsersTotal] = useState(0);
  const [usersPage, setUsersPage] = useState(1);
  const [images, setImages] = useState<any[]>([]);
  const [imagesTotal, setImagesTotal] = useState(0);
  const [imagesPage, setImagesPage] = useState(1);
  const [auditLogs, setAuditLogs] = useState<any[]>([]);
  const [auditTotal, setAuditTotal] = useState(0);
  const [auditPage, setAuditPage] = useState(1);
  const [promptAnalytics, setPromptAnalytics] = useState<any>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  const loadStats = useCallback(async () => {
    if (!token) return;
    try {
      const [s, h] = await Promise.all([
        adminApi.stats(token),
        adminApi.health(token),
      ]);
      setStats(s);
      setHealth(h);
    } catch (e) { console.error(e); }
  }, [token]);

  const loadUsers = useCallback(async (page = 1, q?: string) => {
    if (!token) return;
    try {
      const params: Record<string, string> = { page: String(page), per_page: "15" };
      if (q) params.q = q;
      const res = await adminApi.users(token, params);
      setUsers(res.users);
      setUsersTotal(res.total);
      setUsersPage(page);
    } catch (e) { console.error(e); }
  }, [token]);

  const loadImages = useCallback(async (page = 1) => {
    if (!token) return;
    try {
      const res = await adminApi.images(token, { page: String(page), per_page: "12" });
      setImages(res.images);
      setImagesTotal(res.total);
      setImagesPage(page);
    } catch (e) { console.error(e); }
  }, [token]);

  const loadAuditLogs = useCallback(async (page = 1) => {
    if (!token) return;
    try {
      const res = await adminApi.auditLogs(token, { page: String(page), per_page: "20" });
      setAuditLogs(res.logs);
      setAuditTotal(res.total);
      setAuditPage(page);
    } catch (e) { console.error(e); }
  }, [token]);

  const loadPrompts = useCallback(async () => {
    if (!token) return;
    try {
      const res = await adminApi.promptAnalytics(30, token);
      setPromptAnalytics(res);
    } catch (e) { console.error(e); }
  }, [token]);

  useEffect(() => {
    setLoading(true);
    Promise.all([
      loadStats(),
      loadUsers(),
      loadImages(),
      loadAuditLogs(),
      loadPrompts(),
    ]).finally(() => setLoading(false));
  }, [loadStats, loadUsers, loadImages, loadAuditLogs, loadPrompts]);

  const handleBan = async (userId: string) => {
    if (!token || !confirm("Ban this user?")) return;
    setActionLoading(userId);
    try {
      await adminApi.banUser(userId, "Admin action", token);
      await loadUsers(usersPage, searchQuery || undefined);
      await loadStats();
    } catch (e: any) { alert(e.message); }
    setActionLoading(null);
  };

  const handleUnban = async (userId: string) => {
    if (!token) return;
    setActionLoading(userId);
    try {
      await adminApi.unbanUser(userId, token);
      await loadUsers(usersPage, searchQuery || undefined);
      await loadStats();
    } catch (e: any) { alert(e.message); }
    setActionLoading(null);
  };

  const handleSetRole = async (userId: string, role: string) => {
    if (!token || !confirm(`Set role to ${role}?`)) return;
    setActionLoading(userId);
    try {
      await adminApi.setRole(userId, role, token);
      await loadUsers(usersPage, searchQuery || undefined);
    } catch (e: any) { alert(e.message); }
    setActionLoading(null);
  };

  const handleAddCredits = async (userId: string) => {
    if (!token) return;
    const amount = prompt("Credits to add:");
    if (!amount || isNaN(Number(amount))) return;
    setActionLoading(userId);
    try {
      await adminApi.setCredits(userId, Number(amount), token);
      await loadUsers(usersPage, searchQuery || undefined);
      await loadStats();
    } catch (e: any) { alert(e.message); }
    setActionLoading(null);
  };

  const handleSearch = () => {
    loadUsers(1, searchQuery || undefined);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <div className="flex items-center gap-3 mb-8">
        <Shield className="h-8 w-8 text-primary" />
        <div>
          <h1 className="text-3xl font-bold">Admin Panel</h1>
          <p className="text-muted-foreground">Platform management and monitoring</p>
        </div>
      </div>

      <div className="flex items-center gap-2 mb-6 border-b overflow-x-auto pb-px">
        {[
          { id: "stats", label: "Stats", icon: BarChart3 },
          { id: "users", label: "Users", icon: Users },
          { id: "images", label: "Images", icon: Image },
          { id: "prompts", label: "Prompts", icon: Activity },
          { id: "health", label: "Health", icon: Server },
          { id: "audit", label: "Audit Log", icon: ScrollText },
        ].map((t) => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={`flex items-center gap-2 px-4 py-2.5 text-sm font-medium border-b-2 transition-colors whitespace-nowrap ${
              tab === t.id
                ? "border-primary text-primary"
                : "border-transparent text-muted-foreground hover:text-foreground"
            }`}
          >
            <t.icon className="h-4 w-4" />
            {t.label}
          </button>
        ))}
      </div>

      <AnimatePresence mode="wait">
        <motion.div
          key={tab}
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -8 }}
          transition={{ duration: 0.2 }}
        >
          {tab === "stats" && stats && (
            <div className="space-y-6">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {[
                  { label: "Total Users", value: stats.users.total, icon: Users, color: "text-blue-500", sub: `+${stats.users.new_today} today` },
                  { label: "Total Images", value: stats.images.total, icon: Image, color: "text-purple-500", sub: `+${stats.images.today} today` },
                  { label: "Total Jobs", value: stats.jobs.total, icon: Zap, color: "text-amber-500", sub: `${stats.jobs.active} active` },
                  { label: "Credits Used", value: stats.credits.total_used, icon: TrendingUp, color: "text-emerald-500", sub: `${stats.credits.used_today} today` },
                ].map((s, i) => (
                  <Card key={i}>
                    <CardContent className="p-4">
                      <div className="flex items-center justify-between mb-2">
                        <s.icon className={`h-5 w-5 ${s.color}`} />
                        <span className="text-2xl font-bold">{s.value.toLocaleString()}</span>
                      </div>
                      <p className="text-sm text-muted-foreground">{s.label}</p>
                      <p className="text-xs text-muted-foreground mt-1">{s.sub}</p>
                    </CardContent>
                  </Card>
                ))}
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <Card>
                  <CardHeader>
                    <CardTitle className="text-base">Model Usage</CardTitle>
                  </CardHeader>
                  <CardContent>
                    {stats.model_usage.length === 0 ? (
                      <p className="text-sm text-muted-foreground">No data yet</p>
                    ) : (
                      <div className="space-y-3">
                        {stats.model_usage.map((m: any, i: number) => {
                          const max = Math.max(...stats.model_usage.map((x: any) => x.count));
                          const pct = max > 0 ? (m.count / max) * 100 : 0;
                          return (
                            <div key={i}>
                              <div className="flex justify-between text-sm mb-1">
                                <span className="font-medium">{m.model}</span>
                                <span className="text-muted-foreground">{m.count}</span>
                              </div>
                              <div className="h-2 bg-muted rounded-full overflow-hidden">
                                <motion.div
                                  className="h-full bg-primary rounded-full"
                                  initial={{ width: 0 }}
                                  animate={{ width: `${pct}%` }}
                                  transition={{ duration: 0.5, delay: i * 0.1 }}
                                />
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    )}
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="text-base">Daily New Users (7 days)</CardTitle>
                  </CardHeader>
                  <CardContent>
                    {stats.daily_new_users.length === 0 ? (
                      <p className="text-sm text-muted-foreground">No data yet</p>
                    ) : (
                      <div className="space-y-2">
                        {stats.daily_new_users.map((d: any, i: number) => (
                          <div key={i} className="flex items-center gap-3 text-sm">
                            <span className="text-muted-foreground w-24">{d.date}</span>
                            <div className="flex-1 h-5 bg-muted rounded overflow-hidden">
                              <motion.div
                                className="h-full bg-blue-500/70 rounded"
                                initial={{ width: 0 }}
                                animate={{ width: `${(d.count / Math.max(...stats.daily_new_users.map((x: any) => x.count || 1))) * 100}%` }}
                                transition={{ duration: 0.4, delay: i * 0.05 }}
                              />
                            </div>
                            <span className="w-8 text-right">{d.count}</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </CardContent>
                </Card>
              </div>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                <div className="text-center p-3 bg-muted/50 rounded-lg">
                  <p className="text-muted-foreground">Banned Users</p>
                  <p className="text-xl font-bold text-red-500">{stats.users.banned}</p>
                </div>
                <div className="text-center p-3 bg-muted/50 rounded-lg">
                  <p className="text-muted-foreground">Failed Jobs</p>
                  <p className="text-xl font-bold text-red-500">{stats.jobs.failed}</p>
                </div>
                <div className="text-center p-3 bg-muted/50 rounded-lg">
                  <p className="text-muted-foreground">Public Images</p>
                  <p className="text-xl font-bold">{stats.images.public}</p>
                </div>
                <div className="text-center p-3 bg-muted/50 rounded-lg">
                  <p className="text-muted-foreground">This Week</p>
                  <p className="text-xl font-bold">{stats.images.this_week} imgs</p>
                </div>
              </div>
            </div>
          )}

          {tab === "users" && (
            <div className="space-y-4">
              <div className="flex gap-2">
                <div className="relative flex-1">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <Input
                    placeholder="Search by email or name..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && handleSearch()}
                    className="pl-10"
                  />
                </div>
                <Button onClick={handleSearch} variant="secondary">Search</Button>
                <Button onClick={() => loadUsers(1, searchQuery || undefined)} variant="ghost" size="icon">
                  <RefreshCw className="h-4 w-4" />
                </Button>
              </div>

              <div className="rounded-lg border overflow-hidden">
                <table className="w-full text-sm">
                  <thead className="bg-muted/50">
                    <tr>
                      <th className="text-left p-3 font-medium">User</th>
                      <th className="text-left p-3 font-medium">Role</th>
                      <th className="text-left p-3 font-medium">Plan</th>
                      <th className="text-right p-3 font-medium">Credits</th>
                      <th className="text-center p-3 font-medium">Status</th>
                      <th className="text-right p-3 font-medium">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {users.map((u) => (
                      <tr key={u.id} className="border-t hover:bg-muted/30 transition-colors">
                        <td className="p-3">
                          <div>
                            <p className="font-medium">{u.name || "Unnamed"}</p>
                            <p className="text-xs text-muted-foreground">{u.email}</p>
                          </div>
                        </td>
                        <td className="p-3">
                          <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${
                            u.role === "admin" ? "bg-primary/10 text-primary" : "bg-muted text-muted-foreground"
                          }`}>
                            {u.role === "admin" && <Shield className="h-3 w-3" />}
                            {u.role}
                          </span>
                        </td>
                        <td className="p-3">
                          <span className="text-xs font-medium">{u.plan}</span>
                        </td>
                        <td className="p-3 text-right font-mono">{u.credits}</td>
                        <td className="p-3 text-center">
                          {u.is_banned ? (
                            <span className="inline-flex items-center gap-1 text-xs text-red-500">
                              <Ban className="h-3 w-3" /> Banned
                            </span>
                          ) : u.is_active ? (
                            <span className="inline-flex items-center gap-1 text-xs text-emerald-500">
                              <CheckCircle className="h-3 w-3" /> Active
                            </span>
                          ) : (
                            <span className="text-xs text-muted-foreground">Inactive</span>
                          )}
                        </td>
                        <td className="p-3 text-right">
                          <div className="flex items-center justify-end gap-1">
                            {u.is_banned ? (
                              <Button
                                size="sm"
                                variant="ghost"
                                onClick={() => handleUnban(u.id)}
                                disabled={actionLoading === u.id}
                                className="h-7 px-2 text-emerald-500"
                              >
                                <Unlock className="h-3 w-3" />
                              </Button>
                            ) : (
                              <Button
                                size="sm"
                                variant="ghost"
                                onClick={() => handleBan(u.id)}
                                disabled={actionLoading === u.id || u.id === user?.id}
                                className="h-7 px-2 text-red-500"
                              >
                                <Ban className="h-3 w-3" />
                              </Button>
                            )}
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => handleSetRole(u.id, u.role === "admin" ? "user" : "admin")}
                              disabled={actionLoading === u.id || u.id === user?.id}
                              className="h-7 px-2"
                            >
                              <Shield className="h-3 w-3" />
                            </Button>
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => handleAddCredits(u.id)}
                              disabled={actionLoading === u.id}
                              className="h-7 px-2"
                            >
                              + Credits
                            </Button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <div className="flex items-center justify-between text-sm text-muted-foreground">
                <span>Showing {(usersPage - 1) * 15 + 1}–{Math.min(usersPage * 15, usersTotal)} of {usersTotal}</span>
                <div className="flex gap-2">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => loadUsers(usersPage - 1, searchQuery || undefined)}
                    disabled={usersPage <= 1}
                  >
                    <ChevronLeft className="h-4 w-4" />
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => loadUsers(usersPage + 1, searchQuery || undefined)}
                    disabled={usersPage * 15 >= usersTotal}
                  >
                    <ChevronRight className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </div>
          )}

          {tab === "images" && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <p className="text-sm text-muted-foreground">{imagesTotal} images total</p>
                <Button onClick={() => loadImages(imagesPage)} variant="ghost" size="sm">
                  <RefreshCw className="h-4 w-4 mr-1" /> Refresh
                </Button>
              </div>
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                {images.map((img) => (
                  <Card key={img.id} className="overflow-hidden">
                    <div className="aspect-square relative bg-muted">
                      <img src={img.image_url} alt={img.prompt} className="w-full h-full object-cover" />
                      <div className="absolute top-2 right-2 flex gap-1">
                        {img.is_public && (
                          <span className="bg-emerald-500/80 text-white text-xs px-1.5 py-0.5 rounded">Public</span>
                        )}
                      </div>
                    </div>
                    <CardContent className="p-3">
                      <p className="text-xs text-muted-foreground line-clamp-2 mb-1">{img.prompt}</p>
                      <div className="flex items-center justify-between text-xs text-muted-foreground">
                        <span>{img.model}</span>
                        <span>{img.user_name || img.user_email}</span>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
              <div className="flex items-center justify-between text-sm text-muted-foreground">
                <span>Page {imagesPage} of {Math.max(1, Math.ceil(imagesTotal / 12))}</span>
                <div className="flex gap-2">
                  <Button size="sm" variant="outline" onClick={() => loadImages(imagesPage - 1)} disabled={imagesPage <= 1}>
                    <ChevronLeft className="h-4 w-4" />
                  </Button>
                  <Button size="sm" variant="outline" onClick={() => loadImages(imagesPage + 1)} disabled={imagesPage * 12 >= imagesTotal}>
                    <ChevronRight className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </div>
          )}

          {tab === "prompts" && promptAnalytics && (
            <div className="space-y-6">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <Card>
                  <CardContent className="p-4 text-center">
                    <p className="text-2xl font-bold">{promptAnalytics.total_prompts}</p>
                    <p className="text-xs text-muted-foreground">Total Prompts (30d)</p>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="p-4 text-center">
                    <p className="text-2xl font-bold">{promptAnalytics.average_length}</p>
                    <p className="text-xs text-muted-foreground">Avg Length (chars)</p>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="p-4 text-center">
                    <p className="text-2xl font-bold text-amber-500">{promptAnalytics.safety_flagged}</p>
                    <p className="text-xs text-muted-foreground">Safety Flagged</p>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="p-4 text-center">
                    <p className="text-2xl font-bold">{promptAnalytics.action_breakdown.length}</p>
                    <p className="text-xs text-muted-foreground">Action Types</p>
                  </CardContent>
                </Card>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <Card>
                  <CardHeader><CardTitle className="text-base">Action Breakdown</CardTitle></CardHeader>
                  <CardContent className="space-y-3">
                    {promptAnalytics.action_breakdown.map((a: any, i: number) => {
                      const max = Math.max(...promptAnalytics.action_breakdown.map((x: any) => x.count));
                      return (
                        <div key={i}>
                          <div className="flex justify-between text-sm mb-1">
                            <span className="font-medium capitalize">{a.action.replace("_", " ")}</span>
                            <span className="text-muted-foreground">{a.count}</span>
                          </div>
                          <div className="h-2 bg-muted rounded-full overflow-hidden">
                            <motion.div
                              className="h-full bg-primary rounded-full"
                              initial={{ width: 0 }}
                              animate={{ width: `${(a.count / max) * 100}%` }}
                              transition={{ duration: 0.5 }}
                            />
                          </div>
                        </div>
                      );
                    })}
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader><CardTitle className="text-base">Model Targets</CardTitle></CardHeader>
                  <CardContent className="space-y-3">
                    {promptAnalytics.model_targets.length === 0 ? (
                      <p className="text-sm text-muted-foreground">No data</p>
                    ) : promptAnalytics.model_targets.map((m: any, i: number) => {
                      const max = Math.max(...promptAnalytics.model_targets.map((x: any) => x.count));
                      return (
                        <div key={i}>
                          <div className="flex justify-between text-sm mb-1">
                            <span className="font-medium">{m.model}</span>
                            <span className="text-muted-foreground">{m.count}</span>
                          </div>
                          <div className="h-2 bg-muted rounded-full overflow-hidden">
                            <motion.div
                              className="h-full bg-purple-500 rounded-full"
                              initial={{ width: 0 }}
                              animate={{ width: `${(m.count / max) * 100}%` }}
                              transition={{ duration: 0.5 }}
                            />
                          </div>
                        </div>
                      );
                    })}
                  </CardContent>
                </Card>
              </div>

              {promptAnalytics.daily_prompts.length > 0 && (
                <Card>
                  <CardHeader><CardTitle className="text-base">Daily Prompts (30 days)</CardTitle></CardHeader>
                  <CardContent>
                    <div className="flex items-end gap-1 h-32">
                      {promptAnalytics.daily_prompts.slice().reverse().map((d: any, i: number) => {
                        const max = Math.max(...promptAnalytics.daily_prompts.map((x: any) => x.count));
                        const h = max > 0 ? (d.count / max) * 100 : 0;
                        return (
                          <motion.div
                            key={i}
                            className="flex-1 bg-primary/70 rounded-t min-w-[4px]"
                            initial={{ height: 0 }}
                            animate={{ height: `${h}%` }}
                            transition={{ duration: 0.3, delay: i * 0.02 }}
                            title={`${d.date}: ${d.count}`}
                          />
                        );
                      })}
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>
          )}

          {tab === "health" && health && (
            <div className="space-y-6">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <Card>
                  <CardContent className="p-4 text-center">
                    {health.database === "healthy" ? (
                      <CheckCircle className="h-8 w-8 text-emerald-500 mx-auto mb-2" />
                    ) : (
                      <AlertTriangle className="h-8 w-8 text-red-500 mx-auto mb-2" />
                    )}
                    <p className="text-sm font-medium">Database</p>
                    <p className={`text-xs ${health.database === "healthy" ? "text-emerald-500" : "text-red-500"}`}>
                      {health.database}
                    </p>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="p-4 text-center">
                    <p className="text-2xl font-bold">{health.recent_errors_1h}</p>
                    <p className="text-xs text-muted-foreground">Errors (1h)</p>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="p-4 text-center">
                    <p className="text-2xl font-bold">{health.queue.total}</p>
                    <p className="text-xs text-muted-foreground">Queue Size</p>
                    <p className="text-xs text-muted-foreground">
                      {health.queue.processing} processing / {health.queue.pending} pending
                    </p>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="p-4 text-center">
                    <p className="text-2xl font-bold">{health.avg_job_time_seconds}s</p>
                    <p className="text-xs text-muted-foreground">Avg Job Time</p>
                  </CardContent>
                </Card>
              </div>

              <Card>
                <CardHeader><CardTitle className="text-base">System Info</CardTitle></CardHeader>
                <CardContent className="space-y-2 text-sm">
                  <div className="flex justify-between"><span className="text-muted-foreground">Last checked</span><span>{health.timestamp}</span></div>
                  <div className="flex justify-between"><span className="text-muted-foreground">Database status</span><span>{health.database}</span></div>
                  <div className="flex justify-between"><span className="text-muted-foreground">Pending jobs</span><span>{health.queue.pending}</span></div>
                  <div className="flex justify-between"><span className="text-muted-foreground">Processing jobs</span><span>{health.queue.processing}</span></div>
                  <div className="flex justify-between"><span className="text-muted-foreground">Errors (last hour)</span><span>{health.recent_errors_1h}</span></div>
                </CardContent>
              </Card>

              <Button onClick={async () => { setLoading(true); await loadStats(); setLoading(false); }} variant="secondary">
                <RefreshCw className="h-4 w-4 mr-2" /> Refresh All
              </Button>
            </div>
          )}

          {tab === "audit" && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <p className="text-sm text-muted-foreground">{auditTotal} audit entries</p>
                <Button onClick={() => loadAuditLogs(auditPage)} variant="ghost" size="sm">
                  <RefreshCw className="h-4 w-4 mr-1" /> Refresh
                </Button>
              </div>
              <div className="rounded-lg border overflow-hidden">
                <table className="w-full text-sm">
                  <thead className="bg-muted/50">
                    <tr>
                      <th className="text-left p-3 font-medium">Admin</th>
                      <th className="text-left p-3 font-medium">Action</th>
                      <th className="text-left p-3 font-medium">Target</th>
                      <th className="text-left p-3 font-medium">Details</th>
                      <th className="text-right p-3 font-medium">Time</th>
                    </tr>
                  </thead>
                  <tbody>
                    {auditLogs.map((log) => (
                      <tr key={log.id} className="border-t hover:bg-muted/30">
                        <td className="p-3">
                          <p className="font-medium">{log.admin_name || log.admin_email}</p>
                        </td>
                        <td className="p-3">
                          <span className="px-2 py-0.5 rounded-full text-xs bg-muted font-medium">
                            {log.action.replace("_", " ")}
                          </span>
                        </td>
                        <td className="p-3 text-muted-foreground">
                          {log.target_type}{log.target_id ? ` / ${log.target_id.slice(0, 8)}...` : ""}
                        </td>
                        <td className="p-3 text-muted-foreground text-xs">
                          {log.details ? JSON.stringify(log.details) : "—"}
                        </td>
                        <td className="p-3 text-right text-xs text-muted-foreground">
                          {log.created_at ? new Date(log.created_at).toLocaleString() : "—"}
                        </td>
                      </tr>
                    ))}
                    {auditLogs.length === 0 && (
                      <tr><td colSpan={5} className="p-8 text-center text-muted-foreground">No audit logs yet</td></tr>
                    )}
                  </tbody>
                </table>
              </div>
              <div className="flex items-center justify-between text-sm text-muted-foreground">
                <span>Page {auditPage}</span>
                <div className="flex gap-2">
                  <Button size="sm" variant="outline" onClick={() => loadAuditLogs(auditPage - 1)} disabled={auditPage <= 1}>
                    <ChevronLeft className="h-4 w-4" />
                  </Button>
                  <Button size="sm" variant="outline" onClick={() => loadAuditLogs(auditPage + 1)} disabled={auditPage * 20 >= auditTotal}>
                    <ChevronRight className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </div>
          )}
        </motion.div>
      </AnimatePresence>
    </div>
  );
}
