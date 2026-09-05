"use client";

import { useState, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ProtectedRoute } from "@/components/shared/ProtectedRoute";
import { useAuth } from "@/hooks/useAuth";
import { billingApi } from "@/lib/api";
import { ConfirmDialog } from "@/components/shared/ConfirmDialog";
import {
  CreditCard, Check, Crown, Zap, ArrowRight, Loader2, TrendingUp,
  Calendar, ChevronDown, ChevronUp, AlertCircle, Sparkles, History,
  BarChart3, Plus,
} from "lucide-react";

interface Plan {
  id: string;
  name: string;
  credits: number;
  price_monthly: number;
  features: string[];
  stripe_price_id: string | null;
}

interface Subscription {
  id: string;
  plan_id: string;
  plan_name: string;
  status: string;
  current_period_end: string;
  cancel_at_period_end: boolean;
  credits: number;
  credits_used_this_period: number;
}

interface Transaction {
  id: string;
  amount: number;
  balance_after: number;
  type: string;
  description: string;
  created_at: string;
}

interface UsageStats {
  total_generations: number;
  total_credits_used: number;
  generations_today: number;
  credits_used_today: number;
  generations_this_month: number;
  credits_used_this_period: number;
  top_models: { model: string; count: number }[];
  daily_usage: { date: string; generations: number; credits: number }[];
}

function BillingContent() {
  const { user, token } = useAuth();
  const [plans, setPlans] = useState<Plan[]>([]);
  const [subscription, setSubscription] = useState<Subscription | null>(null);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [usage, setUsage] = useState<UsageStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [checkoutLoading, setCheckoutLoading] = useState<string | null>(null);
  const [txPage, setTxPage] = useState(1);
  const [txHasNext, setTxHasNext] = useState(false);
  const [showCancelConfirm, setShowCancelConfirm] = useState(false);
  const [activeTab, setActiveTab] = useState<"plans" | "usage" | "history">("plans");

  const loadBilling = useCallback(async () => {
    if (!token) return;
    setLoading(true);
    try {
      const [plansData, subData, usageData, txData] = await Promise.all([
        billingApi.plans(),
        billingApi.subscription(token),
        billingApi.usage(token),
        billingApi.transactions(1, 10, undefined, token),
      ]);
      setPlans(plansData);
      setSubscription(subData);
      setUsage(usageData);
      setTransactions(txData.transactions);
      setTxHasNext(txData.has_next);
    } catch {
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => { loadBilling(); }, [loadBilling]);

  async function loadMoreTx() {
    if (!token) return;
    const nextPage = txPage + 1;
    const data = await billingApi.transactions(nextPage, 10, undefined, token);
    setTransactions((prev) => [...prev, ...data.transactions]);
    setTxPage(nextPage);
    setTxHasNext(data.has_next);
  }

  async function handleCheckout(planId: string) {
    if (!token) return;
    setCheckoutLoading(planId);
    try {
      const result = await billingApi.checkout(
        {
          plan_id: planId,
          success_url: `${window.location.origin}/billing?success=true`,
          cancel_url: `${window.location.origin}/billing?canceled=true`,
        },
        token
      );
      if (result.checkout_url) {
        window.location.href = result.checkout_url;
      }
    } catch {
    } finally {
      setCheckoutLoading(null);
    }
  }

  async function handleCancelSubscription() {
    if (!token) return;
    try {
      await billingApi.cancelSubscription(token);
      await loadBilling();
      setShowCancelConfirm(false);
    } catch {
    }
  }

  async function handleAddCredits(amount: number) {
    if (!token) return;
    try {
      await billingApi.addCredits(amount, `Added ${amount} credits`, token);
      await loadBilling();
    } catch {
    }
  }

  function getPlanIcon(planId: string) {
    switch (planId) {
      case "FREE": return Zap;
      case "STARTER": return Sparkles;
      case "PRO": return Crown;
      case "ENTERPRISE": return Crown;
      default: return CreditCard;
    }
  }

  function getPlanColor(planId: string) {
    switch (planId) {
      case "FREE": return "from-gray-500 to-slate-500";
      case "STARTER": return "from-blue-500 to-cyan-500";
      case "PRO": return "from-purple-500 to-pink-500";
      case "ENTERPRISE": return "from-yellow-500 to-orange-500";
      default: return "from-gray-500 to-slate-500";
    }
  }

  const creditPacks = [
    { amount: 100, price: 4.99 },
    { amount: 500, price: 19.99 },
    { amount: 1000, price: 34.99 },
  ];

  return (
    <div className="max-w-6xl mx-auto px-4 py-8 space-y-6">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: 15 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
      >
        <h1 className="text-2xl font-bold">Billing & Usage</h1>
        <p className="text-sm text-muted-foreground mt-1">Manage your subscription and track usage</p>
      </motion.div>

      {/* Current Status */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1, duration: 0.4 }}
        className="grid md:grid-cols-3 gap-4"
      >
        <div className="glass rounded-xl p-5">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center">
              <CreditCard className="h-5 w-5 text-primary" />
            </div>
            <div>
              <p className="text-2xl font-bold">{user?.credits ?? 0}</p>
              <p className="text-xs text-muted-foreground">Credits remaining</p>
            </div>
          </div>
        </div>
        <div className="glass rounded-xl p-5">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-lg bg-green-500/10 flex items-center justify-center">
              <TrendingUp className="h-5 w-5 text-green-500" />
            </div>
            <div>
              <p className="text-2xl font-bold">{usage?.generations_today ?? 0}</p>
              <p className="text-xs text-muted-foreground">Generated today</p>
            </div>
          </div>
        </div>
        <div className="glass rounded-xl p-5">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-lg bg-blue-500/10 flex items-center justify-center">
              <BarChart3 className="h-5 w-5 text-blue-500" />
            </div>
            <div>
              <p className="text-2xl font-bold">{usage?.generations_this_month ?? 0}</p>
              <p className="text-xs text-muted-foreground">This month</p>
            </div>
          </div>
        </div>
      </motion.div>

      {/* Tabs */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.2 }}
        className="flex gap-1 border-b border-border"
      >
        {([
          { id: "plans" as const, label: "Plans", icon: Crown },
          { id: "usage" as const, label: "Usage", icon: BarChart3 },
          { id: "history" as const, label: "History", icon: History },
        ]).map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            onClick={() => setActiveTab(id)}
            className={`flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
              activeTab === id
                ? "border-primary text-foreground"
                : "border-transparent text-muted-foreground hover:text-foreground"
            }`}
          >
            <Icon className="h-4 w-4" />
            {label}
          </button>
        ))}
      </motion.div>

      {/* Plans Tab */}
      {activeTab === "plans" && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
          className="space-y-6"
        >
          {/* Subscription Status */}
          {subscription && (
            <div className="glass rounded-xl p-5 space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className={`h-10 w-10 rounded-lg bg-gradient-to-br ${getPlanColor(subscription.plan_id)} flex items-center justify-center`}>
                    <Crown className="h-5 w-5 text-white" />
                  </div>
                  <div>
                    <p className="font-semibold">{subscription.plan_name}</p>
                    <p className="text-xs text-muted-foreground capitalize">{subscription.status}</p>
                  </div>
                </div>
                {subscription.plan_id !== "FREE" && !subscription.cancel_at_period_end && (
                  <button
                    onClick={() => setShowCancelConfirm(true)}
                    className="text-xs text-destructive hover:underline"
                  >
                    Cancel subscription
                  </button>
                )}
              </div>
              {subscription.current_period_end && (
                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                  <Calendar className="h-3 w-3" />
                  {subscription.cancel_at_period_end
                    ? `Cancels on ${new Date(subscription.current_period_end).toLocaleDateString()}`
                    : `Renews on ${new Date(subscription.current_period_end).toLocaleDateString()}`
                  }
                </div>
              )}
              {subscription.plan_id !== "FREE" && (
                <div className="w-full h-2 bg-secondary rounded-full overflow-hidden">
                  <div
                    className="h-full bg-primary rounded-full transition-all"
                    style={{
                      width: `${Math.min(100, (subscription.credits_used_this_period / Math.max(1, subscription.credits + subscription.credits_used_this_period)) * 100)}%`
                    }}
                  />
                </div>
              )}
              {subscription.plan_id !== "FREE" && (
                <p className="text-[10px] text-muted-foreground">
                  {subscription.credits_used_this_period} credits used this period
                </p>
              )}
            </div>
          )}

          {/* Plan Cards */}
          <div className="grid md:grid-cols-4 gap-4">
            {plans.map((plan, i) => {
              const Icon = getPlanIcon(plan.id);
              const isCurrent = user?.plan === plan.id;
              const isFree = plan.price_monthly === 0;

              return (
                <motion.div
                  key={plan.id}
                  initial={{ opacity: 0, y: 15 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.1 + i * 0.08, duration: 0.4 }}
                  whileHover={{ y: -3, transition: { duration: 0.2 } }}
                  className={`glass rounded-xl p-5 space-y-4 relative ${
                    isCurrent ? "ring-2 ring-primary" : ""
                  }`}
                >
                  {isCurrent && (
                    <div className="absolute -top-2.5 left-1/2 -translate-x-1/2 bg-primary text-primary-foreground text-[10px] font-semibold px-2 py-0.5 rounded-full">
                      Current
                    </div>
                  )}

                  <div className={`h-12 w-12 rounded-xl bg-gradient-to-br ${getPlanColor(plan.id)} flex items-center justify-center`}>
                    <Icon className="h-6 w-6 text-white" />
                  </div>

                  <div>
                    <h3 className="font-semibold">{plan.name}</h3>
                    <div className="flex items-baseline gap-1 mt-1">
                      <span className="text-2xl font-bold">${isFree ? "0" : plan.price_monthly}</span>
                      {!isFree && <span className="text-xs text-muted-foreground">/mo</span>}
                    </div>
                    <p className="text-xs text-primary mt-1">{plan.credits.toLocaleString()} credits/mo</p>
                  </div>

                  <ul className="space-y-1.5">
                    {plan.features.map((feature) => (
                      <li key={feature} className="flex items-start gap-1.5 text-xs text-muted-foreground">
                        <Check className="h-3 w-3 text-green-500 shrink-0 mt-0.5" />
                        {feature}
                      </li>
                    ))}
                  </ul>

                  {isCurrent ? (
                    <div className="h-9 rounded-lg bg-secondary/50 flex items-center justify-center text-xs text-muted-foreground">
                      Current Plan
                    </div>
                  ) : isFree ? (
                    <div className="h-9 rounded-lg bg-secondary/50 flex items-center justify-center text-xs text-muted-foreground">
                      Free forever
                    </div>
                  ) : (
                    <button
                      onClick={() => handleCheckout(plan.id)}
                      disabled={checkoutLoading === plan.id}
                      className="w-full h-9 rounded-lg bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 transition-colors flex items-center justify-center gap-1.5 disabled:opacity-50"
                    >
                      {checkoutLoading === plan.id ? (
                        <Loader2 className="h-3.5 w-3.5 animate-spin" />
                      ) : (
                        <>Upgrade <ArrowRight className="h-3.5 w-3.5" /></>
                      )}
                    </button>
                  )}
                </motion.div>
              );
            })}
          </div>

          {/* Credit Packs */}
          <div className="space-y-3">
            <h3 className="text-sm font-semibold">Credit Packs</h3>
            <div className="grid md:grid-cols-3 gap-3">
              {creditPacks.map((pack) => (
                <motion.button
                  key={pack.amount}
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={() => handleAddCredits(pack.amount)}
                  className="glass rounded-xl p-4 text-left hover:bg-white/5 transition-colors"
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-lg font-bold">{pack.amount.toLocaleString()}</p>
                      <p className="text-xs text-muted-foreground">credits</p>
                    </div>
                    <div className="text-right">
                      <p className="font-semibold">${pack.price}</p>
                      <p className="text-[10px] text-green-500">${(pack.price / pack.amount * 100).toFixed(1)}c each</p>
                    </div>
                  </div>
                </motion.button>
              ))}
            </div>
          </div>
        </motion.div>
      )}

      {/* Usage Tab */}
      {activeTab === "usage" && usage && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
          className="space-y-6"
        >
          <div className="grid md:grid-cols-2 gap-4">
            <div className="glass rounded-xl p-5 space-y-3">
              <h3 className="text-sm font-semibold">Usage Summary</h3>
              <div className="grid grid-cols-2 gap-3">
                {[
                  { label: "Total generations", value: usage.total_generations },
                  { label: "Total credits used", value: usage.total_credits_used },
                  { label: "Today", value: usage.generations_today },
                  { label: "Credits today", value: usage.credits_used_today },
                ].map((stat) => (
                  <div key={stat.label} className="bg-secondary/30 rounded-lg p-3">
                    <p className="text-lg font-bold">{stat.value.toLocaleString()}</p>
                    <p className="text-[10px] text-muted-foreground uppercase">{stat.label}</p>
                  </div>
                ))}
              </div>
            </div>

            <div className="glass rounded-xl p-5 space-y-3">
              <h3 className="text-sm font-semibold">Top Models</h3>
              {usage.top_models.length === 0 ? (
                <p className="text-xs text-muted-foreground">No usage data yet</p>
              ) : (
                <div className="space-y-2">
                  {usage.top_models.map((m, i) => (
                    <div key={m.model} className="flex items-center gap-2">
                      <span className="text-xs text-muted-foreground w-4">{i + 1}.</span>
                      <span className="text-xs font-mono flex-1 truncate">{m.model}</span>
                      <span className="text-xs text-primary">{m.count}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Usage Chart */}
          {usage.daily_usage.length > 0 && (
            <div className="glass rounded-xl p-5 space-y-3">
              <h3 className="text-sm font-semibold">Daily Usage (This Month)</h3>
              <div className="flex items-end gap-1 h-32">
                {usage.daily_usage.reverse().map((day) => {
                  const maxGen = Math.max(...usage.daily_usage.map((d) => d.generations), 1);
                  const height = (day.generations / maxGen) * 100;
                  return (
                    <div
                      key={day.date}
                      className="flex-1 flex flex-col items-center gap-1"
                      title={`${day.date}: ${day.generations} generations, ${day.credits} credits`}
                    >
                      <div
                        className="w-full bg-primary/60 rounded-t-sm min-h-[2px] transition-all"
                        style={{ height: `${Math.max(2, height)}%` }}
                      />
                      <span className="text-[8px] text-muted-foreground">
                        {new Date(day.date).getDate()}
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </motion.div>
      )}

      {/* History Tab */}
      {activeTab === "history" && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
          className="space-y-4"
        >
          {transactions.length === 0 ? (
            <div className="glass rounded-xl p-8 text-center">
              <History className="h-8 w-8 text-muted-foreground/30 mx-auto mb-2" />
              <p className="text-sm text-muted-foreground">No transactions yet</p>
            </div>
          ) : (
            <div className="glass rounded-xl divide-y divide-border overflow-hidden">
              {transactions.map((tx) => (
                <div key={tx.id} className="px-4 py-3 flex items-center gap-3">
                  <div className={`h-8 w-8 rounded-lg flex items-center justify-center ${
                    tx.amount > 0 ? "bg-green-500/10" : "bg-red-500/10"
                  }`}>
                    {tx.amount > 0 ? (
                      <Plus className="h-4 w-4 text-green-500" />
                    ) : (
                      <ArrowRight className="h-4 w-4 text-red-500 rotate-45" />
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-medium truncate">{tx.description}</p>
                    <p className="text-[10px] text-muted-foreground">
                      {new Date(tx.created_at).toLocaleString()}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className={`text-sm font-semibold ${tx.amount > 0 ? "text-green-500" : "text-red-500"}`}>
                      {tx.amount > 0 ? "+" : ""}{tx.amount}
                    </p>
                    <p className="text-[10px] text-muted-foreground">
                      Balance: {tx.balance_after}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          )}

          {txHasNext && (
            <button
              onClick={loadMoreTx}
              className="w-full h-9 rounded-lg border border-input bg-background text-sm font-medium hover:bg-accent transition-colors"
            >
              Load more
            </button>
          )}
        </motion.div>
      )}

      <ConfirmDialog
        open={showCancelConfirm}
        title="Cancel Subscription"
        message="Your subscription will remain active until the end of the current billing period. After that, you'll be downgraded to the Free plan."
        confirmLabel="Cancel Subscription"
        variant="danger"
        onConfirm={handleCancelSubscription}
        onCancel={() => setShowCancelConfirm(false)}
      />
    </div>
  );
}

export default function BillingPage() {
  return (
    <ProtectedRoute>
      <BillingContent />
    </ProtectedRoute>
  );
}
