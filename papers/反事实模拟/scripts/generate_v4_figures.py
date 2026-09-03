#!/usr/bin/env python3
"""Generate the v4 figures for the counterfactual simulation paper.

fig07: budgeted racing round-by-round elimination (data-driven, from the
       frozen racing_result.json of the compose-smoke run).
fig08: racing search structure — candidates, rounds, and the maintained
       top-K branch scenes (schematic, labeled with real actions).

All numbers in fig07 come from the JSON artifact; nothing is hand-edited.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

REPO = Path(__file__).resolve().parents[2]
RACING_JSON = (
    REPO
    / "codebase/SkyEngine/racing_results/compose-smoke/racing_result.json"
)
OUT = Path(__file__).resolve().parents[1] / "figures" / "v4"

INK = "#172033"
MUTED = "#5E6B7A"
GRID = "#D7DEE8"
BLUE = "#2B6CB0"
TEAL = "#168A83"
ORANGE = "#D97706"
RED = "#C2414B"
GRAY = "#7B8794"
SURVIVOR_COLORS = [BLUE, TEAL, ORANGE]

mpl.rcParams.update(
    {
        "font.size": 8.5,
        "axes.edgecolor": MUTED,
        "axes.labelcolor": INK,
        "text.color": INK,
        "xtick.color": MUTED,
        "ytick.color": MUTED,
        "axes.grid": True,
        "grid.color": GRID,
        "grid.linewidth": 0.6,
        "axes.axisbelow": True,
        "font.family": "sans-serif",
        "axes.spines.top": False,
        "axes.spines.right": False,
    }
)

CJK = {"font.sans-serif": ["PingFang SC", "Hiragino Sans GB", "Noto Sans CJK SC", "Arial Unicode MS"]}
mpl.rcParams.update(CJK)


def _short(action_id: str) -> str:
    if action_id == "keep-current":
        return "keep-current"
    return action_id.replace("recipe.greedy_", "").replace("_resastar", "")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fig07_racing_elimination(payload: dict) -> None:
    rounds = payload["rounds"]
    horizons = [round_["horizon"] for round_ in rounds]
    eliminated_at = {
        row["action_id"]: row["eliminated_at"] for row in payload["ranking"]
    }
    mean_by_action: dict[str, list[tuple[int, float]]] = {}
    for round_ in rounds:
        for candidate in round_["candidates"]:
            mean_by_action.setdefault(candidate["action_id"], []).append(
                (round_["horizon"], candidate["mean_cost"])
            )

    survivors = [
        action_id
        for action_id, at in eliminated_at.items()
        if at is None
    ]
    color_map = {
        action_id: SURVIVOR_COLORS[index % len(SURVIVOR_COLORS)]
        for index, action_id in enumerate(sorted(survivors))
    }

    fig, (ax_left, ax_right) = plt.subplots(
        1, 2, figsize=(7.0, 2.7), gridspec_kw={"width_ratios": [2.1, 1.0]}
    )

    for action_id, points in sorted(mean_by_action.items()):
        xs = [point[0] for point in points]
        ys = [point[1] for point in points]
        at = eliminated_at.get(action_id)
        if at is None:
            ax_left.plot(
                xs, ys, marker="o", markersize=3.5, linewidth=1.6,
                color=color_map[action_id], label=_short(action_id),
            )
        else:
            color = GRAY
            ax_left.plot(
                xs, ys, marker="x", markersize=4.5, linewidth=1.1,
                linestyle="--", color=color, alpha=0.85,
            )
            ax_left.annotate(
                _short(action_id),
                (xs[-1], ys[-1]),
                textcoords="offset points",
                xytext=(4, -1),
                fontsize=6.2, color=MUTED,
            )

    ax_left.set_xlabel("统一累计 horizon $H_r$（步）")
    ax_left.set_ylabel("删失口径平均代价 $\\hat{J}$")
    ax_left.set_xticks(horizons)
    ax_left.set_yscale("log")
    ax_left.legend(frameon=False, fontsize=6.8, loc="center left")
    ax_left.set_title("(a) 逐轮淘汰：存活者与被淘汰候选", fontsize=8.5)

    scenes = payload["top_branches"]
    labels = [f"{_short(scene['action_id'])}\n{scene['tape_id']}" for scene in scenes]
    costs = [scene["cost"] for scene in scenes]
    bars = ax_right.bar(
        range(len(scenes)), costs,
        color=[SURVIVOR_COLORS[i % 3] for i in range(len(scenes))],
        width=0.62,
    )
    ax_right.set_xticks(range(len(scenes)))
    ax_right.set_xticklabels(labels, fontsize=6.0)
    ax_right.set_ylabel("分支终局代价")
    ax_right.set_ylim(60, 80)
    for bar, cost in zip(bars, costs):
        ax_right.annotate(
            f"{cost:.0f}", (bar.get_x() + bar.get_width() / 2, cost),
            textcoords="offset points", xytext=(0, 2),
            ha="center", fontsize=7,
        )
    ax_right.set_title("(b) 维护的 top-K 分支场面", fontsize=8.5)

    fig.tight_layout()
    for suffix in ("pdf", "png"):
        fig.savefig(OUT / f"fig07_racing_elimination.{suffix}", dpi=300)
    plt.close(fig)


def fig08_racing_structure(payload: dict) -> None:
    fig, ax = plt.subplots(figsize=(7.0, 2.9))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 4.6)
    ax.axis("off")

    def box(x, y, w, h, text, *, face, edge, fontsize=6.8, style="round,pad=0.06"):
        ax.add_patch(
            FancyBboxPatch(
                (x, y), w, h, boxstyle=style,
                linewidth=1.0, facecolor=face, edgecolor=edge,
            )
        )
        ax.text(
            x + w / 2, y + h / 2, text, ha="center", va="center",
            fontsize=fontsize, color=INK,
        )

    def arrow(x0, y0, x1, y1, *, color=MUTED, style="-|>"):
        ax.add_patch(
            FancyArrowPatch(
                (x0, y0), (x1, y1), arrowstyle=style,
                mutation_scale=9, linewidth=0.9, color=color,
            )
        )

    box(0.15, 2.1, 1.5, 0.85, "决策根 $\\tilde{s}$\n(工厂+求解器\n上下文快照)", face="#E8F1FB", edge=BLUE)
    actions = payload["actions"]
    n = len(actions)
    lanes = [round(4.3 - index * (4.0 / max(n - 1, 1)), 2) for index in range(n)]
    eliminated_at = {
        row["action_id"]: row["eliminated_at"] for row in payload["ranking"]
    }
    for action_id, lane in zip(actions, lanes):
        at = eliminated_at.get(action_id)
        eliminated = at is not None
        arrow(1.68, 2.52, 2.45, lane + 0.16)
        box(
            2.45, lane, 2.5, 0.42,
            _short(action_id),
            face="#F1F3F6" if eliminated else "#E3F4F1",
            edge=GRAY if eliminated else TEAL,
            fontsize=6.0,
        )
        if eliminated:
            ax.text(
                5.02, lane + 0.2, f"$\\times$ R{at}",
                fontsize=6.0, color=RED, va="center",
            )
        else:
            arrow(4.98, lane + 0.21, 5.75, 2.52, color=TEAL)

    box(5.75, 2.35, 1.75, 0.55, "统一 $H_r$ 竞赛\n+ 温续跑 $\\Delta H$", face="#FFF2DD", edge=ORANGE, fontsize=6.4)
    arrow(7.52, 2.62, 8.05, 2.62, color=ORANGE)
    scenes = payload["top_branches"]
    for index, scene in enumerate(scenes):
        y = 3.55 - index * 1.05
        box(
            8.05, y, 1.8, 0.62,
            f"分支场面 #{index + 1}\n{_short(scene['action_id'])} · "
            f"{scene['tape_id']}\n$J$={scene['terminal_makespan'] if scene['terminal_makespan'] is not None else scene['cost']:.0f}",
            face="#E3F4F1", edge=TEAL, fontsize=5.6,
        )
        if index == 0:
            arrow(8.0, 2.62, 8.9, y + 0.65, color=ORANGE)

    ax.text(
        4.9, 0.28,
        "每轮：所有存活候选 × 同一 tape 集 × 同一累计 horizon；"
        "预算（墙钟/转移数/步数）耗尽或全部终局即停",
        ha="center", fontsize=6.2, color=MUTED,
    )

    fig.tight_layout()
    for suffix in ("pdf", "png"):
        fig.savefig(OUT / f"fig08_racing_structure.{suffix}", dpi=300)
    plt.close(fig)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    payload = json.loads(RACING_JSON.read_text(encoding="utf-8"))
    fig07_racing_elimination(payload)
    fig08_racing_structure(payload)
    manifest = {
        "schema_version": "skycausal.paper-figures.v4",
        "source": {
            "racing_result": str(RACING_JSON.relative_to(REPO)),
            "racing_result_sha256": _sha256(RACING_JSON),
            "racing_semantic_hash": payload["semantic_hash"],
        },
        "figures": {
            name: {
                "pdf_sha256": _sha256(OUT / f"{name}.pdf"),
                "png_sha256": _sha256(OUT / f"{name}.png"),
            }
            for name in (
                "fig07_racing_elimination",
                "fig08_racing_structure",
            )
        },
    }
    (OUT / "figure_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(manifest, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
