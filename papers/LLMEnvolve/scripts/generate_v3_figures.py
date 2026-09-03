#!/usr/bin/env python3
"""Generate the reproducible figures used by the SkyCausal v3 paper."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle


FORMAL_ANALYSIS = (
    "artifacts/skycausal_publication_confirmation_v2_1_09760697/analysis.json"
)
DEVELOPMENT_ANALYSIS = (
    "artifacts/skycausal_execution_value_analysis_dev_v0/analysis.json"
)
ONLINE_META_ANALYSIS = (
    "artifacts/skycausal_online_meta_unified_action_dev_v1/"
    "analysis_30state_calibrated.json"
)

INK = "#172033"
MUTED = "#5E6B7A"
GRID = "#D7DEE8"
BLUE = "#2B6CB0"
BLUE_LIGHT = "#E8F1FB"
TEAL = "#168A83"
TEAL_LIGHT = "#E3F4F1"
ORANGE = "#D97706"
ORANGE_LIGHT = "#FFF2DD"
RED = "#C2414B"
RED_LIGHT = "#FCE8EA"
PURPLE = "#7657A8"
GRAY = "#7B8794"
GRAY_LIGHT = "#F1F3F6"
WHITE = "#FFFFFF"

PROFILE_COLORS = {
    "CP-SAT+EECBS": "#2468A2",
    "CP-SAT+LG-LaCAM": "#159A8C",
    "DE+EECBS": "#E5962D",
    "DE+LG-LaCAM": "#D45D72",
    "PSO+LG-LaCAM": "#8064A2",
    "PSO+MAPF-LNS2": "#658E3F",
}

ACTION_LABELS = {
    "fjsp.cp_sat": "CP-SAT",
    "fjsp.de": "DE",
    "fjsp.pso": "PSO",
    "keep_current": "Keep current",
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _configure_style() -> None:
    mpl.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": [
                "Hiragino Sans GB",
                "Heiti SC",
                "Arial Unicode MS",
                "DejaVu Sans",
            ],
            "font.size": 9.5,
            "axes.titlesize": 10.5,
            "axes.labelsize": 9.5,
            "axes.edgecolor": INK,
            "axes.labelcolor": INK,
            "xtick.color": INK,
            "ytick.color": INK,
            "text.color": INK,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": False,
            "legend.frameon": False,
            "axes.unicode_minus": False,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "savefig.facecolor": WHITE,
        }
    )


def _output_figure(
    fig: plt.Figure,
    *,
    output_dir: Path,
    stem: str,
) -> dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = output_dir / f"{stem}.pdf"
    png_path = output_dir / f"{stem}.png"
    fig.savefig(
        pdf_path,
        bbox_inches="tight",
        metadata={
            "Creator": "generate_v3_figures.py",
            "CreationDate": None,
            "ModDate": None,
        },
    )
    fig.savefig(
        png_path,
        dpi=220,
        bbox_inches="tight",
        metadata={"Software": "generate_v3_figures.py"},
    )
    plt.close(fig)
    return {
        "pdf": str(pdf_path),
        "pdf_sha256": _sha256(pdf_path),
        "png": str(png_path),
        "png_sha256": _sha256(png_path),
    }


def _box(
    ax: plt.Axes,
    x: float,
    y: float,
    width: float,
    height: float,
    title: str,
    detail: str = "",
    *,
    face: str = BLUE_LIGHT,
    edge: str = BLUE,
    linewidth: float = 1.2,
    title_size: float = 9.3,
    detail_size: float = 7.0,
) -> None:
    patch = FancyBboxPatch(
        (x, y),
        width,
        height,
        boxstyle="round,pad=0.008,rounding_size=0.012",
        facecolor=face,
        edgecolor=edge,
        linewidth=linewidth,
    )
    ax.add_patch(patch)
    title_y = y + height * (0.60 if detail else 0.5)
    ax.text(
        x + width / 2,
        title_y,
        title,
        ha="center",
        va="center",
        fontsize=title_size,
        fontweight="semibold",
    )
    if detail:
        ax.text(
            x + width / 2,
            y + height * 0.29,
            detail,
            ha="center",
            va="center",
            fontsize=detail_size,
            color=MUTED,
        )


def _arrow(
    ax: plt.Axes,
    start: tuple[float, float],
    end: tuple[float, float],
    *,
    color: str = MUTED,
    dashed: bool = False,
    connectionstyle: str = "arc3",
    linewidth: float = 1.25,
) -> None:
    arrow = FancyArrowPatch(
        start,
        end,
        arrowstyle="-|>",
        mutation_scale=10,
        linewidth=linewidth,
        color=color,
        linestyle=(0, (3, 2)) if dashed else "solid",
        connectionstyle=connectionstyle,
        shrinkA=2,
        shrinkB=2,
    )
    ax.add_patch(arrow)


def _panel_label(ax: plt.Axes, label: str) -> None:
    ax.text(
        -0.08,
        1.04,
        label,
        transform=ax.transAxes,
        fontsize=11,
        fontweight="bold",
        va="bottom",
    )


def _development_badge(
    fig: plt.Figure,
    *,
    state_count: int = 5,
) -> None:
    fig.text(
        0.985,
        0.012,
        (
            f"开发证据 · n={state_count} · "
            "不支持正式质量结论"
        ),
        ha="right",
        va="bottom",
        fontsize=7.8,
        color=RED,
        bbox={
            "boxstyle": "round,pad=0.28",
            "facecolor": RED_LIGHT,
            "edgecolor": RED,
            "linewidth": 0.7,
        },
    )


def _architecture_figure() -> plt.Figure:
    fig, ax = plt.subplots(figsize=(8.4, 4.5))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    ax.text(
        0.02,
        0.98,
        "SkyCausal：连续物理时钟下的开放式求解器组合元调度",
        fontsize=14,
        fontweight="bold",
        va="top",
    )
    ax.text(
        0.02,
        0.91,
        "上层只在影子环境中探测和分配预算；下层制造系统始终继续执行当前安全计划。",
        fontsize=8.3,
        color=MUTED,
        va="top",
    )

    ax.add_patch(
        FancyBboxPatch(
            (0.02, 0.39),
            0.96,
            0.47,
            boxstyle="round,pad=0.012,rounding_size=0.018",
            facecolor="#F8FAFD",
            edgecolor="#B6C3D3",
            linewidth=1.2,
        )
    )
    ax.text(
        0.035,
        0.825,
        "影子元搜索与安全提交",
        fontsize=10,
        color=BLUE,
        fontweight="bold",
    )

    _box(
        ax,
        0.045,
        0.665,
        0.125,
        0.105,
        "动态事件与状态",
        "订单 · 故障",
    )
    _box(
        ax,
        0.205,
        0.665,
        0.135,
        0.105,
        "Solver Catalog",
        "manifest",
        face=TEAL_LIGHT,
        edge=TEAL,
    )
    _box(
        ax,
        0.375,
        0.665,
        0.145,
        0.105,
        "候选动作生成",
        "solver · config",
        face=ORANGE_LIGHT,
        edge=ORANGE,
    )
    _box(
        ax,
        0.555,
        0.665,
        0.145,
        0.105,
        "短 probe",
        "objective · gap",
        face=ORANGE_LIGHT,
        edge=ORANGE,
    )
    _box(
        ax,
        0.735,
        0.665,
        0.205,
        0.105,
        "Root MCTS / 逐轮淘汰",
        "probe budget",
        face="#F0ECF8",
        edge=PURPLE,
    )
    for left, right in [
        ((0.17, 0.717), (0.205, 0.717)),
        ((0.34, 0.717), (0.375, 0.717)),
        ((0.52, 0.717), (0.555, 0.717)),
        ((0.70, 0.717), (0.735, 0.717)),
    ]:
        _arrow(ax, left, right)

    _box(
        ax,
        0.145,
        0.475,
        0.16,
        0.105,
        "最新状态读取",
        "snapshot · scope",
        face=GRAY_LIGHT,
        edge=GRAY,
    )
    _box(
        ax,
        0.345,
        0.475,
        0.16,
        0.105,
        "freshness / rebase",
        "stale filter",
        face=RED_LIGHT,
        edge=RED,
        linewidth=1.5,
    )
    _box(
        ax,
        0.545,
        0.475,
        0.16,
        0.105,
        "Shadow Q 排序",
        r"$\mu+\beta\sigma$",
        face=TEAL_LIGHT,
        edge=TEAL,
    )
    _box(
        ax,
        0.745,
        0.475,
        0.195,
        0.105,
        "原子激活 / fallback",
        "commit / keep",
        face=BLUE_LIGHT,
        edge=BLUE,
    )
    ax.plot(
        [0.837, 0.837, 0.225],
        [0.665, 0.62, 0.62],
        color=MUTED,
        linewidth=1.25,
    )
    _arrow(ax, (0.225, 0.62), (0.225, 0.58))
    _arrow(ax, (0.305, 0.527), (0.345, 0.527), color=RED)
    _arrow(ax, (0.505, 0.527), (0.545, 0.527), color=TEAL)
    _arrow(ax, (0.705, 0.527), (0.745, 0.527), color=BLUE)

    ax.add_patch(
        FancyBboxPatch(
            (0.02, 0.10),
            0.96,
            0.22,
            boxstyle="round,pad=0.012,rounding_size=0.018",
            facecolor="#F3FAF8",
            edgecolor="#A7CDC5",
            linewidth=1.2,
        )
    )
    ax.text(
        0.035,
        0.285,
        "连续物理执行",
        fontsize=10,
        color=TEAL,
        fontweight="bold",
    )
    _box(
        ax,
        0.075,
        0.155,
        0.18,
        0.08,
        "当前认证计划",
        "安全前缀继续执行",
        face=WHITE,
        edge=TEAL,
    )
    _box(
        ax,
        0.325,
        0.155,
        0.20,
        0.08,
        "机器加工 + AGV 运输",
        "物理时钟不冻结",
        face=WHITE,
        edge=TEAL,
    )
    _box(
        ax,
        0.595,
        0.155,
        0.15,
        0.08,
        "最新物理状态",
        r"$s_{t+\Delta}$",
        face=WHITE,
        edge=TEAL,
    )
    _box(
        ax,
        0.815,
        0.155,
        0.12,
        0.08,
        "继续或切换",
        "原子生效",
        face=WHITE,
        edge=TEAL,
    )
    _arrow(ax, (0.255, 0.195), (0.325, 0.195), color=TEAL, linewidth=1.5)
    _arrow(ax, (0.525, 0.195), (0.595, 0.195), color=TEAL, linewidth=1.5)
    _arrow(ax, (0.745, 0.195), (0.815, 0.195), color=TEAL, linewidth=1.5)
    _arrow(
        ax,
        (0.67, 0.235),
        (0.225, 0.475),
        color=TEAL,
        dashed=True,
        connectionstyle="arc3,rad=0.1",
    )
    _arrow(
        ax,
        (0.842, 0.475),
        (0.875, 0.235),
        color=BLUE,
        dashed=True,
    )
    ax.text(
        0.02,
        0.045,
        "安全优先级：可行性 → 最新状态 freshness/rebase → 价值排序 → 原子激活。学习模型不能绕过确定性安全门。",
        fontsize=7.6,
        color=MUTED,
    )
    return fig


def _timeline_figure() -> plt.Figure:
    fig, ax = plt.subplots(figsize=(9.6, 3.4))
    ax.set_xlim(-1, 101)
    ax.set_ylim(-0.25, 3.9)
    ax.axis("off")

    ax.text(
        0,
        3.72,
        "一次在线决策窗口：probe 与制造执行共享同一段墙钟时间",
        fontsize=12,
        fontweight="bold",
        va="top",
    )

    event_x = 8
    deadline_x = 92
    commit_start = 80
    for x, label, color in [
        (event_x, r"事件触发 $t_0$", BLUE),
        (commit_start, "commit reserve", RED),
        (deadline_x, r"总截止期 $t_D$", RED),
    ]:
        ax.plot([x, x], [0.2, 3.04], color=color, linewidth=1.2, linestyle="--")
        ax.text(x, 3.10, label, ha="center", va="bottom", fontsize=8.5, color=color)

    ax.text(0, 2.58, "影子元搜索", fontweight="bold", color=BLUE, va="center")
    ax.text(0, 1.45, "物理系统", fontweight="bold", color=TEAL, va="center")
    ax.text(0, 0.42, "计划有效性", fontweight="bold", color=MUTED, va="center")

    segments = [
        (event_x, 18, BLUE_LIGHT, BLUE, "候选生成"),
        (18, 32, ORANGE_LIGHT, ORANGE, "probe 第 1 轮"),
        (32, 51, ORANGE_LIGHT, ORANGE, "probe 第 2 轮"),
        (51, 68, "#F0ECF8", PURPLE, "MCTS 追加预算"),
        (68, commit_start, RED_LIGHT, RED, "最新状态重校验"),
        (commit_start, deadline_x, BLUE_LIGHT, BLUE, "原子提交"),
    ]
    for start, end, face, edge, label in segments:
        ax.add_patch(
            FancyBboxPatch(
                (start, 2.30),
                end - start,
                0.52,
                boxstyle="round,pad=0.02,rounding_size=0.08",
                facecolor=face,
                edgecolor=edge,
                linewidth=1.0,
            )
        )
        ax.text((start + end) / 2, 2.56, label, ha="center", va="center", fontsize=8.2)

    ax.add_patch(
        FancyBboxPatch(
            (event_x, 1.18),
            deadline_x - event_x,
            0.52,
            boxstyle="round,pad=0.02,rounding_size=0.08",
            facecolor=TEAL_LIGHT,
            edgecolor=TEAL,
            linewidth=1.2,
        )
    )
    ax.text(
        (event_x + deadline_x) / 2,
        1.44,
        "机器继续加工；AGV 继续移动；维修与订单时钟继续推进",
        ha="center",
        va="center",
        fontsize=9.2,
        fontweight="semibold",
        color=TEAL,
    )

    ax.add_patch(
        FancyBboxPatch(
            (event_x, 0.18),
            commit_start - event_x,
            0.48,
            boxstyle="round,pad=0.02,rounding_size=0.08",
            facecolor=GRAY_LIGHT,
            edgecolor=GRAY,
            linewidth=1.0,
        )
    )
    ax.text(
        (event_x + commit_start) / 2,
        0.42,
        "当前认证计划保持有效",
        ha="center",
        va="center",
        fontsize=8.8,
        color=MUTED,
    )
    ax.add_patch(
        FancyBboxPatch(
            (commit_start, 0.18),
            deadline_x - commit_start,
            0.48,
            boxstyle="round,pad=0.02,rounding_size=0.08",
            facecolor=TEAL_LIGHT,
            edgecolor=TEAL,
            linewidth=1.0,
        )
    )
    ax.text(
        (commit_start + deadline_x) / 2,
        0.42,
        "新计划或 keep",
        ha="center",
        va="center",
        fontsize=8.3,
        color=TEAL,
    )

    ax.annotate(
        r"初始快照 $s_{t_0}$",
        xy=(event_x, 2.28),
        xytext=(13.5, 2.98),
        arrowprops={"arrowstyle": "->", "color": BLUE, "linewidth": 1.0},
        fontsize=8.4,
        color=BLUE,
    )
    ax.annotate(
        r"最新状态 $s_{t_0+\Delta}$",
        xy=(68, 1.68),
        xytext=(61, 1.98),
        arrowprops={"arrowstyle": "->", "color": TEAL, "linewidth": 1.0},
        fontsize=8.4,
        color=TEAL,
    )
    ax.text(
        100,
        -0.03,
        "wall-clock →",
        ha="right",
        va="bottom",
        fontsize=8.5,
        color=MUTED,
    )
    return fig


def _budget_quality_figure(formal: dict[str, Any]) -> plt.Figure:
    rows = formal["budget_curve"]["rows"]
    budgets = np.asarray([row["budget_seconds"] for row in rows], dtype=float)
    improvements = np.asarray(
        [row["mean_improvement_vs_best_fixed"] for row in rows], dtype=float
    )
    ci_low = np.asarray([row["improvement_ci_95"]["low"] for row in rows], dtype=float)
    ci_high = np.asarray([row["improvement_ci_95"]["high"] for row in rows], dtype=float)
    coverage = np.asarray([row["root_coverage_rate"] for row in rows], dtype=float) * 100
    fallbacks = [int(row["fallback_count"]) for row in rows]

    fig, axes = plt.subplots(1, 2, figsize=(8.4, 3.5))
    fig.subplots_adjust(wspace=0.30)

    ax = axes[0]
    yerr = np.vstack([improvements - ci_low, ci_high - improvements])
    ax.axhline(0, color=INK, linewidth=0.9, linestyle="--")
    ax.errorbar(
        budgets,
        improvements,
        yerr=yerr,
        color=BLUE,
        marker="o",
        markersize=5.5,
        linewidth=1.8,
        elinewidth=1.2,
        capsize=3,
    )
    ax.fill_between(budgets, ci_low, ci_high, color=BLUE, alpha=0.10)
    ax.set_xlabel("Planning budget (s)")
    ax.set_ylabel("Paired improvement vs. best fixed (cost)")
    ax.set_xticks(budgets)
    ax.grid(axis="y", color=GRID, linewidth=0.7, alpha=0.8)
    ax.set_title("质量收益随预算增加后趋于饱和")
    _panel_label(ax, "(a)")
    ax.annotate(
        "+23.575",
        xy=(10, improvements[2]),
        xytext=(9.0, 50),
        ha="center",
        fontsize=8.5,
        color=BLUE,
        arrowprops={"arrowstyle": "->", "color": BLUE, "linewidth": 0.9},
    )

    ax = axes[1]
    ax.plot(
        budgets,
        coverage,
        color=TEAL,
        marker="o",
        markersize=5.5,
        linewidth=1.8,
    )
    ax.fill_between(budgets, 0, coverage, color=TEAL, alpha=0.08)
    for index, (x, y, fallback_count) in enumerate(
        zip(budgets, coverage, fallbacks)
    ):
        text_x = x
        horizontal_alignment = "center"
        if index == len(budgets) - 2:
            text_x = x - 0.15
            horizontal_alignment = "right"
        elif index == len(budgets) - 1:
            text_x = x + 0.15
            horizontal_alignment = "left"
        ax.text(
            text_x,
            y + 4.0,
            f"{y:.1f}%\n({fallback_count} fallback)",
            ha=horizontal_alignment,
            va="bottom",
            fontsize=7.8,
            color=TEAL,
        )
    ax.set_ylim(0, 112)
    ax.set_xlabel("Planning budget (s)")
    ax.set_ylabel("Root completion coverage (%)")
    ax.set_xticks(budgets)
    ax.grid(axis="y", color=GRID, linewidth=0.7, alpha=0.8)
    ax.set_title("2 s 预算主要受 coverage 限制")
    _panel_label(ax, "(b)")

    fig.suptitle(
        "独立确认：预算、收益与覆盖率的联合权衡（40 个配对状态）",
        fontsize=12.5,
        fontweight="bold",
        y=1.01,
    )
    return fig


def _state_profile_figure(formal: dict[str, Any]) -> plt.Figure:
    clusters = formal["clusters"]
    profiles = list(formal["profiles"])
    topologies = sorted({cluster["topology"] for cluster in clusters})
    positive_count = sum(
        float(cluster["improvement_vs_best_fixed"]) > 0 for cluster in clusters
    )
    negative_count = sum(
        float(cluster["improvement_vs_best_fixed"]) < 0 for cluster in clusters
    )

    fig, axes = plt.subplots(
        1,
        2,
        figsize=(8.4, 4.0),
        gridspec_kw={"width_ratios": [1.25, 1.0]},
    )
    fig.subplots_adjust(wspace=0.30)

    ax = axes[0]
    profile_handles: dict[str, Any] = {}
    for topology_index, topology in enumerate(topologies):
        topology_clusters = [
            cluster for cluster in clusters if cluster["topology"] == topology
        ]
        for point_index, cluster in enumerate(topology_clusters):
            improvement = float(cluster["improvement_vs_best_fixed"])
            best_fixed = float(cluster["best_fixed_heldout_cost"])
            relative = 100.0 * improvement / best_fixed
            jitter = ((point_index * 37) % 17 - 8) / 90.0
            profile = cluster["selected_profile"]
            marker = "X" if cluster["used_fallback"] else "o"
            scatter = ax.scatter(
                topology_index + jitter,
                relative,
                s=40 if marker == "X" else 31,
                color=PROFILE_COLORS[profile],
                edgecolors=INK if marker == "X" else WHITE,
                linewidths=0.8,
                marker=marker,
                zorder=3,
            )
            profile_handles.setdefault(profile, scatter)
        mean_relative = np.mean(
            [
                100.0
                * float(cluster["improvement_vs_best_fixed"])
                / float(cluster["best_fixed_heldout_cost"])
                for cluster in topology_clusters
            ]
        )
        ax.plot(
            [topology_index - 0.22, topology_index + 0.22],
            [mean_relative, mean_relative],
            color=INK,
            linewidth=2.2,
            zorder=4,
        )
    ax.axhline(0, color=INK, linewidth=0.9, linestyle="--")
    ax.set_xlim(-0.48, len(topologies) - 0.52)
    ax.set_xticks(range(len(topologies)), labels=topologies)
    ax.set_ylabel("State-level relative reduction vs. best fixed (%)")
    ax.set_title(
        f"{positive_count}/{len(clusters)} 状态改善，"
        f"{negative_count}/{len(clusters)} 状态退化"
    )
    ax.grid(axis="y", color=GRID, linewidth=0.7, alpha=0.8)
    _panel_label(ax, "(a)")
    ordered_handles = [profile_handles[p] for p in profiles if p in profile_handles]
    ordered_labels = [p for p in profiles if p in profile_handles]
    ax.legend(
        ordered_handles,
        ordered_labels,
        loc="upper left",
        fontsize=7.2,
        ncol=2,
        handletextpad=0.35,
        columnspacing=0.8,
    )
    ax.text(
        0.99,
        0.02,
        "黑边 X：fallback 状态；短横线：拓扑均值",
        transform=ax.transAxes,
        ha="right",
        va="bottom",
        fontsize=7.2,
        color=MUTED,
    )

    ax = axes[1]
    counts = formal["root"]["selection_counts"]
    y = np.arange(len(profiles))
    values = [counts[profile] for profile in profiles]
    colors = [PROFILE_COLORS[profile] for profile in profiles]
    probabilities = np.asarray(values, dtype=float) / np.sum(values)
    selection_entropy = float(-np.sum(probabilities * np.log2(probabilities)))
    ax.barh(y, values, color=colors, height=0.66)
    ax.set_yticks(y, labels=profiles)
    ax.invert_yaxis()
    ax.set_xlabel("Selection count (out of 40)")
    ax.set_title("六个 profile 均被选择")
    ax.set_xlim(0, max(values) + 3.5)
    ax.grid(axis="x", color=GRID, linewidth=0.7, alpha=0.8)
    ax.set_axisbelow(True)
    for row, value in enumerate(values):
        ax.text(value + 0.35, row, str(value), va="center", fontsize=8.5)
    _panel_label(ax, "(b)")
    ax.text(
        0.99,
        0.02,
        f"selection entropy = {selection_entropy:.2f} bits",
        transform=ax.transAxes,
        ha="right",
        va="bottom",
        fontsize=7.2,
        color=MUTED,
    )

    fig.suptitle(
        "独立确认：状态依赖的 profile 互补性",
        fontsize=12.5,
        fontweight="bold",
        y=1.01,
    )
    return fig


def _action_regret_matrix(
    table: Iterable[dict[str, Any]],
    actions: list[str],
) -> tuple[np.ndarray, list[int]]:
    rows = list(table)
    matrix = np.zeros((len(actions), len(rows)), dtype=float)
    seeds: list[int] = []
    for column, row in enumerate(rows):
        seeds.append(int(row["seed"]))
        oracle = min(
            float(row["actions"][action]["remaining_timeline"]) for action in actions
        )
        for action_index, action in enumerate(actions):
            target = float(row["actions"][action]["remaining_timeline"])
            matrix[action_index, column] = target - oracle
    return matrix, seeds


def _draw_heatmap(
    ax: plt.Axes,
    matrix: np.ndarray,
    *,
    seeds: list[int],
    actions: list[str],
    title: str,
    panel: str,
    vmax: float,
) -> Any:
    image = ax.imshow(
        matrix,
        cmap=mpl.colors.LinearSegmentedColormap.from_list(
            "skycausal_regret", ["#F4FBFA", "#72C3B7", "#F0B44D", "#C94D5D"]
        ),
        vmin=0,
        vmax=vmax,
        aspect="auto",
    )
    ax.set_xticks(range(len(seeds)), labels=seeds)
    ax.set_yticks(range(len(actions)), labels=[ACTION_LABELS[a] for a in actions])
    ax.set_xlabel("State seed")
    ax.set_title(title)
    for row in range(matrix.shape[0]):
        for column in range(matrix.shape[1]):
            value = matrix[row, column]
            color = WHITE if value > vmax * 0.58 else INK
            ax.text(
                column,
                row,
                f"{value:.0f}",
                ha="center",
                va="center",
                fontsize=8.2,
                color=color,
                fontweight="bold" if value == 0 else "normal",
            )
            if value == 0:
                ax.add_patch(
                    Rectangle(
                        (column - 0.46, row - 0.46),
                        0.92,
                        0.92,
                        fill=False,
                        edgecolor=INK,
                        linewidth=1.2,
                    )
                )
    _panel_label(ax, panel)
    return image


def _execution_value_figure(development: dict[str, Any]) -> plt.Figure:
    full_actions = ["fjsp.cp_sat", "fjsp.de", "fjsp.pso"]
    short_actions = ["keep_current", "fjsp.cp_sat", "fjsp.de", "fjsp.pso"]
    full_matrix, full_seeds = _action_regret_matrix(
        development["full_budget"]["table"], full_actions
    )
    short_matrix, short_seeds = _action_regret_matrix(
        development["short_budget"]["table"], short_actions
    )

    fig = plt.figure(figsize=(8.6, 5.4))
    grid = fig.add_gridspec(
        2,
        2,
        height_ratios=[1.05, 0.95],
        hspace=0.58,
        wspace=0.30,
    )
    ax_full = fig.add_subplot(grid[0, 0])
    ax_short = fig.add_subplot(grid[0, 1])
    ax_bar = fig.add_subplot(grid[1, :])

    image = _draw_heatmap(
        ax_full,
        full_matrix,
        seeds=full_seeds,
        actions=full_actions,
        title="全预算：最优 solver 随状态变化",
        panel="(a)",
        vmax=100,
    )
    _draw_heatmap(
        ax_short,
        short_matrix,
        seeds=short_seeds,
        actions=short_actions,
        title="短预算：keep-current 进入最优集合",
        panel="(b)",
        vmax=100,
    )
    colorbar = fig.colorbar(image, ax=[ax_full, ax_short], fraction=0.025, pad=0.025)
    colorbar.set_label("Regret in remaining episode timeline")

    short = development["short_budget"]
    strategies = [
        ("Ridge Q (shadow)", short["ridge_loso"]),
        ("Fixed DE", short["fixed_policies"]["fjsp.de"]),
        ("Pairwise Q (shadow)", short["pairwise_state_solver_interaction_loso"]),
        ("Fixed PSO", short["fixed_policies"]["fjsp.pso"]),
        ("Fixed CP-SAT", short["fixed_policies"]["fjsp.cp_sat"]),
        ("Keep current", short["keep_current"]),
        ("Makespan only", short["makespan_only"]),
    ]
    labels = [item[0] for item in strategies]
    regrets = [float(item[1]["mean_regret"]) for item in strategies]
    colors = [
        TEAL,
        BLUE,
        PURPLE,
        BLUE,
        BLUE,
        GRAY,
        RED,
    ]
    bars = ax_bar.barh(np.arange(len(labels)), regrets, color=colors, height=0.64)
    ax_bar.set_yticks(np.arange(len(labels)), labels=labels)
    ax_bar.invert_yaxis()
    ax_bar.set_xlabel("Mean regret in remaining episode timeline (lower is better)")
    ax_bar.set_title("LOSO 开发结果：makespan-only 无法预测在线终局价值")
    ax_bar.set_xlim(0, max(regrets) + 9)
    ax_bar.grid(axis="x", color=GRID, linewidth=0.7, alpha=0.8)
    ax_bar.set_axisbelow(True)
    for bar, (_, payload), regret in zip(bars, strategies, regrets):
        hit_text = ""
        if "top1_hits" in payload:
            hit_text = f"; hit {payload['top1_hits']}/5"
        ax_bar.text(
            regret + 0.7,
            bar.get_y() + bar.get_height() / 2,
            f"{regret:.1f}{hit_text}",
            va="center",
            fontsize=8.2,
        )
    _panel_label(ax_bar, "(c)")

    fig.suptitle(
        "开发证据：动作互补性、预算效应与状态执行价值",
        fontsize=13,
        fontweight="bold",
        y=0.985,
    )
    _development_badge(fig)
    return fig


def _online_meta_figure(analysis: dict[str, Any]) -> plt.Figure:
    fig, axes = plt.subplots(
        1,
        3,
        figsize=(9.2, 3.8),
        gridspec_kw={"width_ratios": [1.05, 1.25, 0.85]},
    )
    ax_delta, ax_state, ax_choice = axes

    strategies = [
        ("fixed_cp_sat", "固定 CP-SAT", BLUE),
        ("fixed_de", "固定 DE", ORANGE),
        ("fixed_pso", "固定 PSO", PURPLE),
        ("successive_halving", "逐轮淘汰", GRAY),
        ("mcts", "原始 MCTS", TEAL),
        ("mcts_calibrated", "校准 MCTS", RED),
    ]
    means = []
    lower = []
    upper = []
    for strategy, _, _ in strategies:
        paired = analysis["strategy_summaries"][strategy][
            "paired_delta_vs_keep_current"
        ]
        mean = float(paired["mean"])
        ci = [float(item) for item in paired["bootstrap_95_ci"]]
        means.append(mean)
        lower.append(mean - ci[0])
        upper.append(ci[1] - mean)
    y_positions = np.arange(len(strategies))
    ax_delta.errorbar(
        means,
        y_positions,
        xerr=np.array([lower, upper]),
        fmt="none",
        ecolor=MUTED,
        elinewidth=1.1,
        capsize=2.5,
        zorder=1,
    )
    ax_delta.scatter(
        means,
        y_positions,
        s=38,
        color=[item[2] for item in strategies],
        edgecolor=WHITE,
        linewidth=0.7,
        zorder=2,
    )
    ax_delta.axvline(0, color=INK, linewidth=0.9, linestyle="--")
    ax_delta.set_yticks(
        y_positions,
        labels=[item[1] for item in strategies],
    )
    ax_delta.invert_yaxis()
    ax_delta.set_xlabel("相对 keep-current 的终局差值\n（越低越好，95% bootstrap CI）")
    ax_delta.set_title("总体效果")
    ax_delta.grid(axis="x", color=GRID, linewidth=0.7)
    ax_delta.set_axisbelow(True)
    _panel_label(ax_delta, "(a)")

    state_details = analysis["state_details"]
    seeds = [int(item["seed"]) for item in state_details]
    calibrated_delta = [
        float(
            item["terminal_timeline"]["mcts_calibrated"]
            - item["terminal_timeline"]["mcts"]
        )
        for item in state_details
    ]
    colors = [
        TEAL if value < 0 else GRAY if value == 0 else RED
        for value in calibrated_delta
    ]
    ax_state.axhline(0, color=INK, linewidth=0.9, linestyle="--")
    ax_state.vlines(
        range(len(seeds)),
        0,
        calibrated_delta,
        colors=colors,
        linewidth=1.1,
        alpha=0.85,
    )
    ax_state.scatter(
        range(len(seeds)),
        calibrated_delta,
        color=colors,
        s=22,
        zorder=2,
    )
    ax_state.set_xticks(
        [0, 4, 9, 14, 19, 24, 29],
        labels=[
            str(seeds[index])
            for index in [0, 4, 9, 14, 19, 24, 29]
        ],
        rotation=35,
    )
    improved = sum(value < 0 for value in calibrated_delta)
    worse = sum(value > 0 for value in calibrated_delta)
    ax_state.text(
        0.02,
        0.97,
        f"改善 {improved} / 持平 {30 - improved - worse} / 退化 {worse}",
        transform=ax_state.transAxes,
        ha="left",
        va="top",
        fontsize=8.2,
        color=MUTED,
    )
    ax_state.set_xlabel("独立状态 seed")
    ax_state.set_ylabel("校准 MCTS - 原始 MCTS")
    ax_state.set_title("逐状态效果不稳定")
    ax_state.grid(axis="y", color=GRID, linewidth=0.7)
    ax_state.set_axisbelow(True)
    _panel_label(ax_state, "(b)")

    solver_order = ["fjsp.cp_sat", "fjsp.de", "fjsp.pso"]
    method_order = ["mcts", "mcts_calibrated"]
    method_labels = ["原始 MCTS", "校准 MCTS"]
    bottom = np.zeros(len(method_order))
    for solver_id, color in zip(
        solver_order,
        [BLUE, ORANGE, PURPLE],
    ):
        values = [
            analysis["strategy_summaries"][method][
                "selected_solver_counts"
            ].get(solver_id, 0)
            for method in method_order
        ]
        bars = ax_choice.bar(
            method_labels,
            values,
            bottom=bottom,
            color=color,
            width=0.62,
            label=ACTION_LABELS[solver_id],
        )
        for bar, value, base in zip(bars, values, bottom):
            if value:
                ax_choice.text(
                    bar.get_x() + bar.get_width() / 2,
                    base + value / 2,
                    str(value),
                    ha="center",
                    va="center",
                    fontsize=8.2,
                    color=WHITE,
                    fontweight="bold",
                )
        bottom += np.array(values)
    ax_choice.set_ylim(0, 32)
    ax_choice.set_ylabel("最终选择次数")
    ax_choice.set_title("候选覆盖已恢复")
    ax_choice.legend(
        loc="upper center",
        bbox_to_anchor=(0.5, -0.17),
        ncol=3,
        fontsize=7.8,
    )
    _panel_label(ax_choice, "(c)")

    fig.suptitle(
        "30 状态开发实验：可辨识预算修复了覆盖，但没有改善终局质量",
        fontsize=12.5,
        fontweight="bold",
        y=1.02,
    )
    _development_badge(fig, state_count=30)
    fig.subplots_adjust(
        left=0.09,
        right=0.985,
        bottom=0.24,
        top=0.82,
        wspace=0.48,
    )
    return fig


def _validate_inputs(
    formal: dict[str, Any],
    development: dict[str, Any],
    online_meta: dict[str, Any],
) -> None:
    if formal.get("schema_version") != "skycausal.publication-analysis.v1":
        raise ValueError("unexpected publication analysis schema")
    if not formal.get("overall_gate_passed"):
        raise ValueError("publication analysis did not pass its overall gate")
    if not formal.get("search_value_gate_passed"):
        raise ValueError("publication search-value gate did not pass")
    if len(formal.get("clusters", [])) != 40:
        raise ValueError("publication analysis must contain 40 paired clusters")
    if development.get("development_only") is not True:
        raise ValueError("execution-value source must remain development-only")
    if development.get("quality_claim_authorized") is not False:
        raise ValueError("development source unexpectedly authorizes a quality claim")
    if development.get("cohort_audit", {}).get("paired_state_count") != 5:
        raise ValueError("execution-value development source must contain five states")
    if online_meta.get("development_only") is not True:
        raise ValueError("online meta source must remain development-only")
    if online_meta.get("quality_claim_authorized") is not False:
        raise ValueError("online meta source unexpectedly authorizes a quality claim")
    if online_meta.get("state_count") != 30:
        raise ValueError("online meta development source must contain 30 states")
    pairing = online_meta.get("pairing_audit", {})
    if not all(
        pairing.get(key)
        for key in (
            "action_independent_state_match",
            "complete_strategy_matrix",
            "decision_outcome_action_match",
        )
    ):
        raise ValueError("online meta pairing audit did not pass")


def generate(*, workspace_root: Path, output_dir: Path) -> dict[str, Any]:
    formal_path = workspace_root / FORMAL_ANALYSIS
    development_path = workspace_root / DEVELOPMENT_ANALYSIS
    online_meta_path = workspace_root / ONLINE_META_ANALYSIS
    formal = _read_json(formal_path)
    development = _read_json(development_path)
    online_meta = _read_json(online_meta_path)
    _validate_inputs(formal, development, online_meta)
    _configure_style()

    figures = [
        (
            "fig01_system_architecture",
            _architecture_figure(),
            "method",
            "conceptual system architecture; no empirical claim",
            [],
        ),
        (
            "fig02_continuous_clock_timeline",
            _timeline_figure(),
            "method",
            "conceptual online timing contract; no empirical claim",
            [],
        ),
        (
            "fig03_budget_quality_confirmation",
            _budget_quality_figure(formal),
            "confirmed",
            "independent v2.1 confirmation, 40 paired states",
            [str(formal_path)],
        ),
        (
            "fig04_state_profile_confirmation",
            _state_profile_figure(formal),
            "confirmed",
            "independent v2.1 confirmation, 40 paired states",
            [str(formal_path)],
        ),
        (
            "fig05_execution_value_development",
            _execution_value_figure(development),
            "development-only",
            "five paired states; not authorized for an active-policy quality claim",
            [str(development_path)],
        ),
        (
            "fig06_online_meta_30state_development",
            _online_meta_figure(online_meta),
            "development-only",
            (
                "30 paired states; unified action schema and "
                "calibration ablation; not an independent confirmation"
            ),
            [str(online_meta_path)],
        ),
    ]

    entries = []
    for stem, fig, evidence, claim_scope, sources in figures:
        outputs = _output_figure(fig, output_dir=output_dir, stem=stem)
        entries.append(
            {
                "stem": stem,
                "evidence": evidence,
                "claim_scope": claim_scope,
                "sources": sources,
                "outputs": {
                    key: (
                        str(Path(value).relative_to(workspace_root))
                        if key in {"pdf", "png"}
                        else value
                    )
                    for key, value in outputs.items()
                },
            }
        )

    generator_path = Path(__file__).resolve()
    manifest = {
        "schema_version": "skycausal.paper-figure-manifest.v1",
        "generator": {
            "path": str(generator_path.relative_to(workspace_root)),
            "sha256": _sha256(generator_path),
        },
        "source_files": {
            str(formal_path.relative_to(workspace_root)): _sha256(formal_path),
            str(development_path.relative_to(workspace_root)): _sha256(development_path),
            str(online_meta_path.relative_to(workspace_root)): _sha256(
                online_meta_path
            ),
        },
        "figures": entries,
    }
    manifest_path = output_dir / "figure_manifest.json"
    with manifest_path.open("w", encoding="utf-8") as handle:
        json.dump(manifest, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")
    manifest["manifest_path"] = str(manifest_path.relative_to(workspace_root))
    manifest["manifest_sha256"] = _sha256(manifest_path)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    default_root = Path(__file__).resolve().parents[2]
    parser.add_argument(
        "--workspace-root",
        type=Path,
        default=default_root,
        help="SkyCausal paper workspace root",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Figure output directory (default: 论文/figures/v3)",
    )
    args = parser.parse_args()
    workspace_root = args.workspace_root.resolve()
    output_dir = (
        args.output_dir.resolve()
        if args.output_dir is not None
        else workspace_root / "论文" / "figures" / "v3"
    )
    manifest = generate(workspace_root=workspace_root, output_dir=output_dir)
    print(
        json.dumps(
            {
                "manifest_path": manifest["manifest_path"],
                "manifest_sha256": manifest["manifest_sha256"],
                "figure_count": len(manifest["figures"]),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
