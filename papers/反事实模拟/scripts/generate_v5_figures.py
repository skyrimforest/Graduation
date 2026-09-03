"""Generate the v5 result figures from frozen experiment manifests.

Sources (all frozen, hash-chained artifacts — figures must be rebuilt
through this script, never hand-edited):

  E1   results/e1_hero_v0_20260827/manifest.json      (closed-loop matrix)
  E2a  results/e2a_full_20260827/e2a_report.json      (paired counterfactuals)
  GOLD results/golden_trace_r1_20260826/manifest.json (reference values)

Outputs to 论文_反事实模拟/figures/v5/ :
  fig11_e1_main paired diff vs fixed_never by workload family (F1)
  fig12_e1_pareto quality vs search compute (F2)
  fig13_e2a_paired_delta delta distribution + by phase (F3a)
  fig14_golden_gap per-spec gap to golden reference (F4)
  fig15_hero_case one hero episode decision timeline (F6)
  fig16_switch_composition hero switch-target distribution (F7)

Missing inputs are skipped with a printed note (E3 sensitivity figure
comes later with the lambda/tau grid).
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
PAPER = HERE.parent
REPO = PAPER.parent / "codebase" / "SkyEngine" / "experiment" / "skycausal" / "results"
E1_MANIFEST = REPO / "e1_merged_20260827" / "manifest.json"
E2A_REPORT = REPO / "e2a_full_20260827" / "e2a_report.json"
GOLD_MANIFEST = (
    REPO / "golden_trace_r1_20260826" / "manifest.json"
)
E1_EPISODES = REPO / "e1_hero_v0b_20260827" / "episodes"
OUT = PAPER / "figures" / "v5"
OUT.mkdir(parents=True, exist_ok=True)

plt.rcParams.update(
    {
        "figure.dpi": 150,
        "font.size": 9,
        "axes.grid": True,
        "grid.alpha": 0.25,
    }
)
METHOD_LABELS = {
    "fixed_never": "fixed (never)",
    "static_map": "static map",
    "oneshot_uniform": "one-shot uniform",
    "hero_v0": "hero V0 (trigger-only)",
    "hero_v0b": "hero V0b (ours)",
}


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def fig_e1_main() -> bool:
    if not E1_MANIFEST.exists():
        print("skip fig11: E1 manifest missing")
        return False
    manifest = _load(E1_MANIFEST)
    methods = [
        m for m in manifest["methods"] if m != "fixed_never"
    ]
    families = sorted(
        {row["workload_family"] for row in manifest["rows"]}
    )
    fig, axes = plt.subplots(
        len(families),
        1,
        figsize=(7, 1.5 * len(families) + 1),
        sharex=True,
    )
    if len(families) == 1:
        axes = [axes]
    for axis, family in zip(axes, families):
        rows = [
            row
            for row in manifest["rows"]
            if row["workload_family"] == family
            and "fixed_never" in row["methods"]
        ]
        data, labels = [], []
        for method in methods:
            diffs = [
                row["methods"][method]["evaluation_makespan"]
                - row["methods"]["fixed_never"]["evaluation_makespan"]
                for row in rows
                if method in row["methods"]
            ]
            data.append(diffs)
            labels.append(METHOD_LABELS.get(method, method))
        axis.boxplot(data, labels=labels, showmeans=True)
        axis.axhline(0, color="k", linewidth=0.8)
        axis.set_ylabel(family.replace("_", "\n"), fontsize=7)
    axes[-1].set_xlabel(
        "paired makespan difference vs fixed (negative = better)"
    )
    fig.suptitle("E1 closed-loop comparison (72 specs, paired)", y=0.995)
    fig.tight_layout()
    fig.savefig(OUT / "fig11_e1_main.pdf", bbox_inches="tight")
    plt.close(fig)
    return True


def fig_e1_pareto() -> bool:
    if not E1_MANIFEST.exists():
        print("skip fig12: E1 manifest missing")
        return False
    manifest = _load(E1_MANIFEST)
    fig, axis = plt.subplots(figsize=(6, 4))
    for method in manifest["methods"]:
        rows = [
            row
            for row in manifest["rows"]
            if method in row["methods"]
        ]
        if not rows:
            continue
        quality = sum(
            row["methods"][method]["evaluation_makespan"]
            for row in rows
        ) / len(rows)
        compute = sum(
            row["methods"][method]["search_runtime_ms"]
            for row in rows
        ) / len(rows) / 1000.0
        axis.scatter(
            compute,
            quality,
            s=70,
            label=METHOD_LABELS.get(method, method),
        )
        axis.annotate(
            METHOD_LABELS.get(method, method),
            (compute, quality),
            textcoords="offset points",
            xytext=(6, 4),
            fontsize=7,
        )
    axis.set_xlabel("mean search wall-clock per episode (s)")
    axis.set_ylabel("mean evaluation makespan")
    axis.set_title("quality vs compute (dual-ledger, not merged)")
    fig.tight_layout()
    fig.savefig(OUT / "fig12_e1_pareto.pdf", bbox_inches="tight")
    plt.close(fig)
    return True


def fig_e2a_delta() -> bool:
    if not E2A_REPORT.exists():
        print("skip fig13: E2a report missing")
        return False
    report = _load(E2A_REPORT)
    pairs = report["pairs"]
    deltas = [
        value
        for record in pairs
        for value in record["deltas"].values()
        if value is not None
    ]
    fig, axes = plt.subplots(1, 2, figsize=(8, 3.2))
    axes[0].hist(deltas, bins=30, color="#4477aa")
    axes[0].axvline(0, color="k", linewidth=1)
    axes[0].set_xlabel(
        "paired Delta = J(keep) - J(switch-then-keep)"
    )
    axes[0].set_title(f"individual-level Delta (n={len(deltas)})")
    by_phase = {"early": [], "mid": [], "late": []}
    for record in pairs:
        position = record["pair_row_index"] / max(
            record["rows_len"], 1
        )
        phase = (
            "early"
            if position < 1 / 3
            else "mid" if position < 2 / 3 else "late"
        )
        for value in record["deltas"].values():
            if value is not None:
                by_phase[phase].append(value)
    axes[1].boxplot(
        [by_phase[p] for p in ("early", "mid", "late")],
        labels=["early", "mid", "late"],
        showmeans=True,
    )
    axes[1].axhline(0, color="k", linewidth=1)
    axes[1].set_xlabel("decision-point phase within episode")
    axes[1].set_title("Delta by phase (CATE stratification)")
    fig.tight_layout()
    fig.savefig(OUT / "fig13_e2a_paired_delta.pdf", bbox_inches="tight")
    plt.close(fig)
    return True


def fig_golden_gap() -> bool:
    if not E1_MANIFEST.exists():
        print("skip fig14: E1 manifest missing")
        return False
    manifest = _load(E1_MANIFEST)
    fig, axis = plt.subplots(figsize=(6, 4))
    for method in manifest["methods"]:
        rows = [
            row
            for row in manifest["rows"]
            if method in row["methods"]
            and row.get("golden_reference")
        ]
        gaps = [
            row["methods"][method]["evaluation_makespan"]
            - row["golden_reference"]
            for row in rows
        ]
        if not gaps:
            continue
        sizes = [4 for _ in gaps]
        axis.scatter(
            range(len(gaps)),
            sorted(gaps),
            s=sizes,
            label=METHOD_LABELS.get(method, method),
            alpha=0.7,
        )
    axis.axhline(0, color="k", linewidth=1)
    axis.set_xlabel("episode spec (sorted)")
    axis.set_ylabel("makespan gap to golden reference")
    axis.set_title("gap to best-of-K reference (reference, not baseline)")
    axis.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(OUT / "fig14_golden_gap.pdf", bbox_inches="tight")
    plt.close(fig)
    return True


def _hero_case_episode() -> Path | None:
    if not E1_EPISODES.exists():
        return None
    candidates = sorted(E1_EPISODES.iterdir())
    for episode_dir in candidates:
        hero = episode_dir / "hero_v0b"
        log = hero / "decision_log.json"
        if not log.exists():
            continue
        rows = _load(log)["rows"]
        switches = [
            row
            for row in rows
            if row["selected_first_action"]["action_type"] == "SWITCH"
        ]
        if 1 <= len(switches) <= 6 and len(rows) >= 5:
            return log
    return None


def fig_hero_case() -> bool:
    log = _hero_case_episode()
    if log is None:
        print("skip fig15: no suitable hero episode yet")
        return False
    rows = _load(log)["rows"]
    episode_id = log.parents[1].name
    fig, axis = plt.subplots(figsize=(8, 3))
    steps = [row["physical_step"] for row in rows]
    kinds = [
        1 if row["selected_first_action"]["action_type"] == "SWITCH" else 0
        for row in rows
    ]
    axis.step(
        steps,
        kinds,
        where="post",
        linewidth=1.4,
    )
    axis.set_yticks([0, 1])
    axis.set_yticklabels(["KEEP", "SWITCH"])
    for row in rows:
        if row["selected_first_action"]["action_type"] == "SWITCH":
            target = (
                row["selected_first_action"]
                .get("target_recipe", {})
                .get("recipe_id", "")
            )
            axis.annotate(
                target.replace("recipe.greedy_", "").replace(
                    "_resastar", ""
                ),
                (row["physical_step"], 1),
                textcoords="offset points",
                xytext=(4, -12),
                fontsize=6,
                rotation=30,
            )
    axis.set_xlabel("physical step (decision points every 10)")
    axis.set_title(f"hero V0 decision timeline — {episode_id[:48]}")
    fig.tight_layout()
    fig.savefig(OUT / "fig15_hero_case.pdf", bbox_inches="tight")
    plt.close(fig)
    return True


def fig_switch_composition() -> bool:
    if not E1_EPISODES.exists():
        print("skip fig16: E1 episodes missing")
        return False
    counter: Counter[str] = Counter()
    for episode_dir in E1_EPISODES.iterdir():
        log = episode_dir / "hero_v0" / "decision_log.json"
        if not log.exists():
            continue
        for row in _load(log)["rows"]:
            if (
                row["selected_first_action"]["action_type"]
                == "SWITCH"
            ):
                target = (
                    row["selected_first_action"]
                    .get("target_recipe", {})
                    .get("recipe_id", "?")
                )
                counter[target] += 1
    if not counter:
        print("skip fig16: no hero switches recorded yet")
        return False
    fig, axis = plt.subplots(figsize=(6, 3.2))
    items = counter.most_common()
    axis.barh(
        [name.replace("recipe.greedy_", "") for name, _ in items],
        [count for _, count in items],
        color="#66ccee",
    )
    axis.set_xlabel("committed switch count (E1 hero_v0)")
    axis.set_title("switch-target composition (V0 frozen pool)")
    fig.tight_layout()
    fig.savefig(OUT / "fig16_switch_composition.pdf", bbox_inches="tight")
    plt.close(fig)
    return True


def main() -> None:
    produced = [
        fig_e1_main(),
        fig_e1_pareto(),
        fig_e2a_delta(),
        fig_golden_gap(),
        fig_hero_case(),
        fig_switch_composition(),
    ]
    print(
        f"v5 figures written to {OUT}: "
        f"{sum(1 for p in produced if p)}/{len(produced)}"
    )


if __name__ == "__main__":
    main()
