#!/usr/bin/env bash
# 一键重建 flex_manufacture 工作区（文档 + 4 个代码仓库 + 引擎修复分支 worktree）
# 用法: bash bootstrap.sh [目标根目录]   默认 ./flex_manufacture
set -euo pipefail

GH="https://github.com/skyrimforest"
ROOT="${1:-$(pwd)/flex_manufacture}"
PREP="$ROOT/260601天工论文准备"

mkdir -p "$PREP/codebase"

# 1. 文档仓库（本仓库）
if [ ! -d "$PREP/.git" ]; then
  git clone "$GH/Graduation.git" "$PREP"
else
  echo "[skip] Graduation 已存在"
fi

clone_branch() {  # clone_branch <repo> <dir> <branch>
  local repo="$1" dir="$2" branch="$3"
  if [ ! -d "$PREP/codebase/$dir/.git" ]; then
    git clone "$GH/$repo.git" "$PREP/codebase/$dir"
  fi
  git -C "$PREP/codebase/$dir" fetch origin "$branch" || true
  git -C "$PREP/codebase/$dir" checkout "$branch"
  echo "[ok] $dir @ $branch"
}

# 2. 四个代码仓库
clone_branch SkyEngine                SkyEngine        trae/skycausal-research
clone_branch SkyEngine-FJSP           SkyEngine-FJSP   trae/skycausal-evolution
clone_branch SkyEngine-MAPF           SkyEngine-MAPF   trae/skycausal-evolution
clone_branch SkyEngine-research       sky_research     0901icaps1
git -C "$PREP/codebase/sky_research" fetch origin 0901llmdiag || true   # 方向7 LLM诊断

# 3. 引擎修复分支（论文三层屏障修复所在）+ 确认实验 worktree
git -C "$PREP/codebase/SkyEngine" fetch origin 0902dedupe 0901softcommit || true
if [ ! -e "$PREP/codebase/SkyEngine-confirmation-v2-1" ]; then
  git -C "$PREP/codebase/SkyEngine" worktree add ../SkyEngine-confirmation-v2-1 0902dedupe || true
fi

echo
echo "完成。下一步:"
echo "  1) cp $PREP/codebase/SkyEngine/.env.example $PREP/codebase/SkyEngine/.env  # 填写密钥"
echo "  2) 按 $PREP/codebase/SkyEngine/SETUP_GUIDE.md 构建并启动实验栈"
echo "  3) 论文编译: sh $PREP/scripts/latex-build.sh <tex文件>"
