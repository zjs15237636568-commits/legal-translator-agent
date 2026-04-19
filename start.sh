#!/usr/bin/env bash
# 一键启动脚本：并行跑后端和前端。
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"

cleanup() {
  echo ""
  echo "正在停止服务…"
  jobs -p | xargs -r kill 2>/dev/null || true
  exit 0
}
trap cleanup INT TERM

echo "▶ 启动后端 (http://127.0.0.1:8765) …"
(cd "$ROOT/backend" && ./run.sh) &
BACK_PID=$!

echo "▶ 启动前端 (http://127.0.0.1:5173) …"
(
  cd "$ROOT/frontend"
  if [ ! -d "node_modules" ]; then
    echo "  · 安装前端依赖…"
    npm install --silent
  fi
  npm run dev
) &
FRONT_PID=$!

echo ""
echo "✅ 服务已启动，按 Ctrl+C 退出。"
echo "   - Frontend: http://127.0.0.1:5173"
echo "   - Backend : http://127.0.0.1:8765/docs"
echo ""

wait $BACK_PID $FRONT_PID
