#!/bin/bash
# ============================================
# Vercel Deployment Script
# ============================================
# Deploys the frontend to Vercel
# Prerequisites: Vercel CLI installed (npm i -g vercel)
#
# Usage: ./deploy-vercel.sh [environment]
#   environment: preview | production (default: preview)

set -euo pipefail

ENV="${1:-preview}"
PROJECT_NAME="text2img-frontend"

echo "╔══════════════════════════════════════╗"
echo "║  Vercel Deploy — ${ENV}               ║"
echo "╚══════════════════════════════════════╝"

# ── Step 1: Verify Vercel CLI ─────────────────
if ! command -v vercel &> /dev/null; then
    echo "Vercel CLI not found. Installing..."
    npm install -g vercel
fi

# ── Step 2: Login ─────────────────────────────
echo "[1/3] Checking Vercel authentication..."
vercel whoami > /dev/null 2>&1 || vercel login

# ── Step 3: Set Environment Variables ─────────
echo "[2/3] Setting environment variables..."
if [ -f .env.production ]; then
    # These should be set via Vercel dashboard or CLI
    echo "  Set these in Vercel Dashboard > Settings > Environment Variables:"
    echo "    NEXT_PUBLIC_API_URL = https://api.yourdomain.com"
    echo "    NEXT_PUBLIC_GOOGLE_CLIENT_ID = your-google-client-id"
fi

# ── Step 4: Deploy ────────────────────────────
echo "[3/3] Deploying to Vercel..."
if [ "${ENV}" = "production" ]; then
    vercel --prod --yes
else
    vercel --yes
fi

echo ""
echo "Deploy complete!"
echo "  Dashboard: https://vercel.com/dashboard"
