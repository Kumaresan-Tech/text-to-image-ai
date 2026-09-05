"use client";

import { motion, type Variants } from "framer-motion";
import { type ReactNode } from "react";

const stagger: Variants = {
  hidden: {},
  visible: { transition: { staggerChildren: 0.06 } },
};

const fadeUp: Variants = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.4, ease: [0.25, 0.46, 0.45, 0.94] } },
};

const scaleIn: Variants = {
  hidden: { opacity: 0, scale: 0.95 },
  visible: { opacity: 1, scale: 1, transition: { duration: 0.3, ease: "easeOut" } },
};

const slideRight: Variants = {
  hidden: { opacity: 0, x: -20 },
  visible: { opacity: 1, x: 0, transition: { duration: 0.35, ease: "easeOut" } },
};

interface MotionProps {
  children: ReactNode;
  className?: string;
  delay?: number;
}

export function StaggerContainer({ children, className }: MotionProps) {
  return (
    <motion.div variants={stagger} initial="hidden" animate="visible" className={className}>
      {children}
    </motion.div>
  );
}

export function FadeUp({ children, className, delay }: MotionProps) {
  return (
    <motion.div variants={fadeUp} custom={delay} className={className}>
      {children}
    </motion.div>
  );
}

export function ScaleIn({ children, className, delay }: MotionProps) {
  return (
    <motion.div variants={scaleIn} custom={delay} className={className}>
      {children}
    </motion.div>
  );
}

export function SlideRight({ children, className, delay }: MotionProps) {
  return (
    <motion.div variants={slideRight} custom={delay} className={className}>
      {children}
    </motion.div>
  );
}

export function HoverScale({ children, className }: MotionProps) {
  return (
    <motion.div whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }} transition={{ type: "spring", stiffness: 400, damping: 17 }} className={className}>
      {children}
    </motion.div>
  );
}
