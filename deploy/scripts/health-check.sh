#!/bin/bash
# ============================================
# Health Check Script
# ============================================
# Usage: ./health-check.sh
# Checks all services are running and responsive

set -uo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

FAIL=0

check() {
    local name="$1"
    local cmd="$2"
    if eval "${cmd}" > /dev/null 2>&1; then
        echo -e "  ${GREEN}✓${NC} ${name}"
    else
        echo -e "  ${RED}✗${NC} ${name}"
        FAIL=1
    fi
}

echo "╔══════════════════════════════════════╗"
echo "║    Text2Img Health Check             ║"
echo "╚══════════════════════════════════════╝"
echo ""

# ── Docker Containers ──────────────────────────
echo "Docker Containers:"
for svc in t2i_postgres t2i_redis t2i_backend t2i_worker t2i_frontend t2i_nginx; do
    check "${svc}" "docker inspect --format='{{.State.Running}}' ${svc} 2>/dev/null | grep -q true"
done
echo ""

# ── Service Endpoints ─────────────────────────
echo "Service Endpoints:"
check "Backend health"  "curl -sf http://localhost:8000/api/health"
check "Frontend"        "curl -sf http://localhost:3000/ > /dev/null"
check "Nginx proxy"     "curl -sf http://localhost/health"
check "API docs"        "curl -sf http://localhost:8000/api/docs > /dev/null"
echo ""

# ── Database ──────────────────────────────────
echo "Database:"
check "PostgreSQL ping" "docker exec t2i_postgres pg_isready -U text2img"
check "PostgreSQL query" "docker exec t2i_postgres psql -U text2img -d text2img -c 'SELECT 1' > /dev/null"
echo ""

# ── Redis ─────────────────────────────────────
echo "Redis:"
check "Redis ping"      "docker exec t2i_redis redis-cli ping"
echo ""

# ── Disk Space ────────────────────────────────
echo "Disk Space:"
DISK_USAGE=$(df -h / | tail -1 | awk '{print $5}' | tr -d '%')
if [ "${DISK_USAGE}" -gt 90 ]; then
    echo -e "  ${RED}!${NC} Disk usage: ${DISK_USAGE}% (critical)"
    FAIL=1
elif [ "${DISK_USAGE}" -gt 80 ]; then
    echo -e "  ${YELLOW}!${NC} Disk usage: ${DISK_USAGE}% (warning)"
else
    echo -e "  ${GREEN}✓${NC} Disk usage: ${DISK_USAGE}%"
fi
echo ""

# ── Summary ───────────────────────────────────
if [ "${FAIL}" -eq 0 ]; then
    echo -e "${GREEN}All checks passed!${NC}"
    exit 0
else
    echo -e "${RED}Some checks failed!${NC}"
    exit 1
fi
