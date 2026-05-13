import io
import logging
from pathlib import Path
from typing import Optional

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import numpy as np

from src.models import TemplateDNA, ThemeColors

logger = logging.getLogger(__name__)

DEFAULT_DPI = 150


class ChartGenerator:
    """通用+科研图表生成，配色适配模板"""

    def __init__(self, template_dna: Optional[TemplateDNA] = None):
        self._template_dna = template_dna or TemplateDNA()
        self._setup_matplotlib()

    def _setup_matplotlib(self):
        theme = self._template_dna.theme
        fonts = self._template_dna.fonts

        plt.rcParams.update({
            "figure.facecolor": theme.background,
            "axes.facecolor": theme.light_bg,
            "axes.edgecolor": theme.subtle,
            "axes.labelcolor": theme.text,
            "xtick.color": theme.text,
            "ytick.color": theme.text,
            "text.color": theme.text,
            "font.family": "sans-serif",
            "font.size": 12,
            "axes.titlesize": 14,
            "axes.labelsize": 12,
            "figure.dpi": DEFAULT_DPI,
        })

        self._color_palette = [
            theme.primary, theme.secondary, theme.accent,
            theme.subtle, "#2ECC71", "#F39C12", "#9B59B6", "#1ABC9C",
        ]

    def generate_comparison_table(self, data: list, headers: list, highlight_best: bool = True, output_path: Optional[str] = None) -> str:
        fig, ax = plt.subplots(figsize=(10, max(2, len(data) * 0.5 + 1)))
        ax.axis("off")

        if highlight_best and data:
            cell_colors = []
            for row in data:
                row_colors = []
                numeric_vals = []
                for val in row[1:]:
                    try:
                        numeric_vals.append(float(str(val).replace("%", "")))
                    except (ValueError, TypeError):
                        numeric_vals.append(None)

                best_idx = None
                if numeric_vals and any(v is not None for v in numeric_vals):
                    valid = [(i, v) for i, v in enumerate(numeric_vals) if v is not None]
                    if valid:
                        best_idx = max(valid, key=lambda x: x[1])[0]

                for j in range(len(row)):
                    if j - 1 == best_idx:
                        row_colors.append(self._hex_to_rgba(self._template_dna.theme.accent, 0.2))
                    else:
                        row_colors.append(self._hex_to_rgba(self._template_dna.theme.light_bg))
                cell_colors.append(row_colors)
        else:
            cell_colors = None

        table = ax.table(
            cellText=data,
            colLabels=headers,
            cellColours=cell_colors,
            loc="center",
            cellLoc="center",
        )
        table.auto_set_font_size(False)
        table.set_fontsize(10)
        table.scale(1, 1.5)

        for key, cell in table.get_celld().items():
            if key[0] == 0:
                cell.set_facecolor(self._template_dna.theme.primary)
                cell.set_text_props(color="white", fontweight="bold")

        return self._save_or_return(fig, output_path)

    def generate_progress_chart(self, milestones: list, output_path: Optional[str] = None) -> str:
        fig, ax = plt.subplots(figsize=(10, 3))

        n = len(milestones)
        y_pos = [0] * n
        colors = [self._color_palette[i % len(self._color_palette)] for i in range(n)]

        ax.scatter(range(n), y_pos, c=colors, s=200, zorder=5)
        ax.plot(range(n), y_pos, color=self._template_dna.theme.subtle, linewidth=2, zorder=3)

        for i, (ms, color) in enumerate(zip(milestones, colors)):
            ax.annotate(ms, (i, 0), textcoords="offset points",
                        xytext=(0, 20), ha="center", fontsize=10, color=color)

        ax.set_ylim(-0.5, 0.5)
        ax.axis("off")

        return self._save_or_return(fig, output_path)

    def generate_metric_dashboard(self, metrics: dict, output_path: Optional[str] = None) -> str:
        n = len(metrics)
        fig, axes = plt.subplots(1, n, figsize=(4 * n, 3))
        if n == 1:
            axes = [axes]

        for ax, (name, value) in zip(axes, metrics.items()):
            ax.text(0.5, 0.6, str(value), transform=ax.transAxes,
                    ha="center", va="center", fontsize=28,
                    fontweight="bold", color=self._template_dna.theme.primary)
            ax.text(0.5, 0.2, name, transform=ax.transAxes,
                    ha="center", va="center", fontsize=12,
                    color=self._template_dna.theme.text)
            ax.axis("off")

        return self._save_or_return(fig, output_path)

    def generate_timeline(self, events: list, output_path: Optional[str] = None) -> str:
        fig, ax = plt.subplots(figsize=(10, 3))

        n = len(events)
        ax.plot(range(n), [0] * n, color=self._template_dna.theme.primary,
                linewidth=3, marker="o", markersize=10,
                markerfacecolor=self._template_dna.theme.accent)

        for i, event in enumerate(events):
            y_offset = 15 if i % 2 == 0 else -25
            ax.annotate(event, (i, 0), textcoords="offset points",
                        xytext=(0, y_offset), ha="center", fontsize=9,
                        color=self._template_dna.theme.text)

        ax.set_ylim(-0.5, 0.5)
        ax.axis("off")

        return self._save_or_return(fig, output_path)

    def generate_sota_comparison(self, data: list, output_path: Optional[str] = None) -> str:
        if not data:
            return ""

        methods = [row[0] for row in data]
        scores = []
        for row in data:
            try:
                scores.append(float(str(row[-1]).replace("%", "")))
            except (ValueError, TypeError):
                scores.append(0)

        fig, ax = plt.subplots(figsize=(8, max(3, len(methods) * 0.5)))

        colors = []
        max_score = max(scores) if scores else 0
        for s in scores:
            if s == max_score:
                colors.append(self._template_dna.theme.accent)
            else:
                colors.append(self._template_dna.theme.secondary)

        bars = ax.barh(methods, scores, color=colors, height=0.6)

        for bar, score in zip(bars, scores):
            ax.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height() / 2,
                    f"{score:.1f}", va="center", fontsize=10,
                    color=self._template_dna.theme.text)

        ax.set_xlabel("Score")
        ax.invert_yaxis()
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

        return self._save_or_return(fig, output_path)

    def generate_ablation_chart(self, data: list, baseline: str = "", output_path: Optional[str] = None) -> str:
        if not data:
            return ""

        components = [row[0] for row in data]
        scores = []
        for row in data:
            try:
                scores.append(float(str(row[-1]).replace("%", "")))
            except (ValueError, TypeError):
                scores.append(0)

        fig, ax = plt.subplots(figsize=(8, max(3, len(components) * 0.5)))

        colors = [self._template_dna.theme.secondary] * len(components)
        if baseline and baseline in components:
            colors[components.index(baseline)] = self._template_dna.theme.primary

        bars = ax.barh(components, scores, color=colors, height=0.6)

        for bar, score in zip(bars, scores):
            ax.text(bar.get_width() + 0.3, bar.get_y() + bar.get_height() / 2,
                    f"{score:.1f}", va="center", fontsize=10,
                    color=self._template_dna.theme.text)

        ax.set_xlabel("Score")
        ax.invert_yaxis()
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

        return self._save_or_return(fig, output_path)

    def generate_training_curves(self, metrics: dict, output_path: Optional[str] = None) -> str:
        fig, ax = plt.subplots(figsize=(8, 5))

        for i, (name, values) in enumerate(metrics.items()):
            color = self._color_palette[i % len(self._color_palette)]
            ax.plot(values, label=name, color=color, linewidth=2)

        ax.set_xlabel("Epoch")
        ax.set_ylabel("Value")
        ax.legend()
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.grid(True, alpha=0.3)

        return self._save_or_return(fig, output_path)

    def generate_bar_chart(self, labels: list, values: list, title: str = "", output_path: Optional[str] = None) -> str:
        fig, ax = plt.subplots(figsize=(8, 5))

        colors = [self._color_palette[i % len(self._color_palette)] for i in range(len(labels))]
        ax.bar(labels, values, color=colors, width=0.6)

        if title:
            ax.set_title(title)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.grid(True, axis="y", alpha=0.3)

        return self._save_or_return(fig, output_path)

    def generate_architecture_diagram(self, components: list, title: str = "", output_path: Optional[str] = None) -> str:
        n = len(components)
        if n == 0:
            return ""

        fig, ax = plt.subplots(figsize=(10, max(3, n * 0.8 + 1)))
        ax.set_xlim(0, 10)
        ax.set_ylim(0, max(n + 1, 3))
        ax.axis("off")

        if title:
            ax.text(5, n + 0.5, title, ha="center", va="center",
                    fontsize=16, fontweight="bold",
                    color=self._template_dna.theme.primary)

        box_w = 3.0
        box_h = 0.6
        x_center = 5.0

        for i, comp in enumerate(components):
            y = n - i - 0.3
            color = self._color_palette[i % len(self._color_palette)]

            rect = plt.Rectangle(
                (x_center - box_w / 2, y - box_h / 2),
                box_w, box_h,
                facecolor=color, edgecolor="white",
                linewidth=1.5, alpha=0.9, zorder=3,
            )
            ax.add_patch(rect)
            ax.text(x_center, y, comp, ha="center", va="center",
                    fontsize=11, color="white", fontweight="bold", zorder=4)

            if i < n - 1:
                ax.annotate(
                    "", xy=(x_center, y - box_h / 2 - 0.05),
                    xytext=(x_center, y - box_h / 2 - 0.35),
                    arrowprops=dict(
                        arrowstyle="->", color=self._template_dna.theme.accent,
                        lw=2,
                    ),
                    zorder=2,
                )

        return self._save_or_return(fig, output_path)

    def _save_or_return(self, fig, output_path: Optional[str]) -> str:
        if output_path:
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            fig.savefig(output_path, bbox_inches="tight", dpi=DEFAULT_DPI, facecolor=fig.get_facecolor())
            plt.close(fig)
            return output_path
        else:
            buf = io.BytesIO()
            fig.savefig(buf, format="png", bbox_inches="tight", dpi=DEFAULT_DPI, facecolor=fig.get_facecolor())
            plt.close(fig)
            buf.seek(0)
            return buf

    def _hex_to_rgba(self, hex_color: str, alpha: float = 1.0) -> tuple:
        hex_color = hex_color.lstrip("#")
        return (
            int(hex_color[0:2], 16) / 255,
            int(hex_color[2:4], 16) / 255,
            int(hex_color[4:6], 16) / 255,
            alpha,
        )
