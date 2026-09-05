"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Sparkles, Zap, Shield, Image as ImageIcon, ArrowRight, LayoutDashboard } from "lucide-react";
import { useAuth } from "@/hooks/useAuth";

const features = [
  {
    icon: Zap,
    title: "Lightning Fast",
    desc: "Generate images in under 10 seconds with our optimized GPU pipeline.",
    href: "/studio",
    cta: "Generate now",
  },
  {
    icon: ImageIcon,
    title: "HD Quality",
    desc: "Up to 2048x2048 resolution with fine-tuned parameters control.",
    href: "/studio",
    cta: "Try high quality",
  },
  {
    icon: Shield,
    title: "Private by Default",
    desc: "Your generations are private. Share publicly only when you choose.",
    href: "/studio",
    cta: "Open Studio",
  },
];

export default function HomePage() {
  const { user } = useAuth();

  return (
    <div className="flex flex-col items-center">
      {/* Hero */}
      <section className="relative w-full max-w-6xl mx-auto px-4 pt-24 pb-32 text-center">
        <div className="absolute inset-0 -z-10 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-purple-900/20 via-transparent to-transparent" />

        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, ease: [0.25, 0.46, 0.45, 0.94] }}
        >
          <h1 className="text-5xl md:text-7xl font-bold tracking-tight">
            <span className="gradient-text">Text to Image</span>
            <br />
            <span className="text-foreground/90">AI Generator</span>
          </h1>
        </motion.div>

        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.15, duration: 0.5 }}
          className="mt-6 text-lg text-muted-foreground max-w-2xl mx-auto"
        >
          Transform your ideas into stunning visuals. Powered by Stable Diffusion XL, our AI generates
          high-quality images in seconds.
        </motion.p>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3, duration: 0.5 }}
          className="mt-10 flex gap-4 justify-center flex-wrap"
        >
          {user ? (
            <>
              <Link href="/dashboard">
                <Button size="lg" className="text-base px-8">
                  <LayoutDashboard className="mr-2 h-5 w-5" /> Dashboard
                </Button>
              </Link>
              <Link href="/generate">
                <Button size="lg" variant="outline" className="text-base px-8">
                  <Sparkles className="mr-2 h-5 w-5" /> Generate
                </Button>
              </Link>
            </>
          ) : (
            <>
              <Link href="/studio">
                <Button size="lg" className="text-base px-8 bg-gradient-to-r from-purple-600 to-cyan-600 hover:from-purple-500 hover:to-cyan-500 text-white shadow-lg shadow-purple-500/20">
                  <Sparkles className="mr-2 h-5 w-5" /> Launch AI Studio (Instant)
                </Button>
              </Link>
              <Link href="/gallery">
                <Button size="lg" variant="outline" className="text-base px-8">
                  Browse Gallery <ArrowRight className="ml-2 h-4 w-4" />
                </Button>
              </Link>
            </>
          )}
        </motion.div>
      </section>

      {/* Features */}
      <section className="w-full max-w-6xl mx-auto px-4 pb-24">
        <div className="grid md:grid-cols-3 gap-8">
          {features.map(({ icon: Icon, title, desc, href, cta }, i) => (
            <Link key={title} href={href}>
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.4 + i * 0.1, duration: 0.4 }}
                whileHover={{ y: -4, transition: { duration: 0.2 } }}
                className="glass rounded-xl p-6 text-center cursor-pointer transition-shadow hover:shadow-lg group"
              >
                <div className="mx-auto w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center mb-4">
                  <Icon className="h-6 w-6 text-primary" />
                </div>
                <h3 className="text-lg font-semibold mb-2">{title}</h3>
                <p className="text-sm text-muted-foreground mb-4">{desc}</p>
                <span className="inline-flex items-center gap-1 text-sm font-medium text-primary group-hover:gap-2 transition-all">
                  {cta} <ArrowRight className="h-4 w-4" />
                </span>
              </motion.div>
            </Link>
          ))}
        </div>
      </section>
    </div>
  );
}
