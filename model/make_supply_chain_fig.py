"""
Render the NI minerals supply-chain structure + key players as a figure.

Reads data/company_register.csv and groups the named firms into the five
supply-chain stages the model uses, drawing the circular value chain
(imports -> primary/processing -> manufacturing -> use -> end-of-life ->
collection -> recovery) and highlighting the binding midstream bottleneck
(a single processing asset). Writes outputs/figures/fig0_supply_chain.png.

Run:  python make_supply_chain_fig.py
"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import pandas as pd

HERE = os.path.dirname(__file__)
FIGDIR = os.path.join(HERE, "outputs", "figures")
os.makedirs(FIGDIR, exist_ok=True)

# --- stage definitions (firm short-names grouped by the model's chain stages) ---
STAGES = {
    "primary": dict(
        title="PRIMARY  &  QUARRY", subtitle="8 firms · 2,840 jobs",
        firms=["Dalradian (Au/Sb/Cu — contested)", "Mannok · Irish Salt · Kilwaughter",
               "Breedon · FP McCann · Galantas · Conroy"],
        colour="#c9a66b"),
    "processing": dict(
        title="PROCESSING  &  RECOVERY", subtitle="1 firm · 70 jobs  —  BINDING GAP",
        firms=["Ionic Technologies", "(Belfast · 400 tpa REE oxide target)",
               "no Li / Co / Ni recovery capacity"],
        colour="#d98880"),
    "manufacturing": dict(
        title="MANUFACTURING  (downstream)", subtitle="5 firms · 8,470 jobs",
        firms=["Wrightbus · Seagate · Spirit", "Encirc · Harland & Wolff / Navantia",
               "demand-rich: EV, magnets, aerospace"],
        colour="#7fb3d5"),
    "collection": dict(
        title="COLLECTION  &  FEEDSTOCK", subtitle="5 firms · 824 jobs",
        firms=["Re-Gen · RiverRidge · Bryson", "Envirogreen · Plaswire (turbine blades)",
               "routes exist; critical-metal capture low"],
        colour="#7dcea0"),
    "enabling": dict(
        title="EQUIPMENT  &  ENABLING", subtitle="2 firms · 1,500 jobs  +  QUB / QUILL",
        firms=["CDE Group · Terex / Powerscreen / Finlay", "processing & recycling equipment",
               "skills, R&D and cluster anchor"],
        colour="#bfbfbf"),
}


def box(ax, x, y, w, h, stage, highlight=False):
    s = STAGES[stage]
    lw = 2.6 if highlight else 1.2
    edge = "#b03a2e" if highlight else "#555555"
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.06",
                                linewidth=lw, edgecolor=edge, facecolor=s["colour"], alpha=0.85, zorder=2))
    ax.text(x + w / 2, y + h - 0.18, s["title"], ha="center", va="top",
            fontsize=10.5, fontweight="bold", zorder=3)
    ax.text(x + w / 2, y + h - 0.42, s["subtitle"], ha="center", va="top",
            fontsize=8.4, fontstyle="italic",
            color=("#7b241c" if highlight else "#222222"), zorder=3)
    for k, f in enumerate(s["firms"]):
        ax.text(x + w / 2, y + h - 0.66 - k * 0.235, f, ha="center", va="top",
                fontsize=7.6, zorder=3)


def arrow(ax, p0, p1, colour="#34495e", style="-|>", lw=2.0, ls="-", rad=0.0):
    ax.add_patch(FancyArrowPatch(p0, p1, arrowstyle=style, mutation_scale=16,
                                 linewidth=lw, color=colour, linestyle=ls,
                                 connectionstyle=f"arc3,rad={rad}", zorder=1))


def main():
    fig, ax = plt.subplots(figsize=(14.4, 7.4))
    ax.set_xlim(0, 14.4); ax.set_ylim(0, 7.4); ax.axis("off")

    fig.suptitle("Northern Ireland minerals supply chain — structure and key players",
                 fontsize=14, fontweight="bold", y=0.985)
    ax.text(6.7, 6.78, "Linear chain (top, left→right) with the circular return loop (bottom). "
            "Stage jobs from the 21-firm register.", ha="center", fontsize=9, color="#444")

    W, H = 3.05, 1.55
    # top linear chain
    yT = 4.55
    xP, xR, xM = 0.30, 5.05, 9.55
    box(ax, xP, yT, W, H, "primary")
    box(ax, xR, yT, W, H, "processing", highlight=True)
    box(ax, xM, yT, W, H, "manufacturing")
    # bottom circular return
    yB = 1.55
    box(ax, xR, yB, W, H, "collection")
    box(ax, xP, yB, W, H, "enabling")

    # imports (closes the balance) node, under manufacturing
    ax.add_patch(FancyBboxPatch((xM, yB + 0.25), W, 1.05, boxstyle="round,pad=0.02,rounding_size=0.05",
                                linewidth=1.0, edgecolor="#555", facecolor="#f4d35e", alpha=0.7, zorder=2))
    ax.text(xM + W / 2, yB + 1.08, "IMPORTS  close the balance", ha="center", va="top",
            fontsize=8.8, fontweight="bold", zorder=3)
    ax.text(xM + W / 2, yB + 0.80, "~65% of critical-mineral supply", ha="center", va="top",
            fontsize=7.8, zorder=3)
    ax.text(xM + W / 2, yB + 0.58, "single-country 70–74% (REE/Co)", ha="center", va="top",
            fontsize=7.6, color="#7b241c", zorder=3)

    # --- flows ---
    # primary -> processing -> manufacturing (top)
    arrow(ax, (xP + W, yT + H / 2), (xR, yT + H / 2), lw=2.4)
    arrow(ax, (xR + W, yT + H / 2), (xM, yT + H / 2), lw=2.4)
    ax.text((xP + W + xR) / 2, yT + H / 2 + 0.16, "ore / concentrate", ha="center", fontsize=7, color="#34495e")
    ax.text((xR + W + xM) / 2, yT + H / 2 + 0.20, "refined /\nsecondary material", ha="center", fontsize=7, color="#34495e")

    # imports -> manufacturing (up)
    arrow(ax, (xM + W / 2, yB + 1.30), (xM + W / 2, yT), colour="#b9770e", lw=2.2)
    # manufacturing -> end-of-life -> collection (the return loop)
    arrow(ax, (xM + W / 2 - 0.7, yT), (xR + W, yB + H / 2 + 0.2), colour="#1e8449", lw=2.2, rad=-0.18)
    ax.text(8.05, yB + H + 0.30, "end-of-life arisings  (WEEE · ELV · turbines)",
            ha="center", fontsize=7.4, color="#1e8449")
    # collection -> processing (feedstock feeds recovery, the loop closes)
    arrow(ax, (xR + W / 2, yB + H), (xR + W / 2, yT), colour="#1e8449", lw=2.6)
    ax.text(xR + W / 2 + 0.12, (yB + H + yT) / 2, "feedstock", ha="left", va="center",
            fontsize=7.6, color="#1e8449", rotation=90)

    # enabling -> primary & processing (support, dashed)
    arrow(ax, (xP + W / 2, yB + H), (xP + W / 2, yT), colour="#566573", lw=1.6, ls="--")
    arrow(ax, (xP + W, yB + H - 0.2), (xR, yT + 0.15), colour="#566573", lw=1.4, ls="--", rad=0.12)
    ax.text(xP + W / 2 + 0.10, (yB + H + yT) / 2, "equipment · skills", ha="left", va="center",
            fontsize=7.4, color="#566573", rotation=90)

    # exports note off manufacturing (to the right, with room)
    arrow(ax, (xM + W, yT + H / 2), (xM + W + 1.05, yT + H / 2), colour="#7d3c98", lw=1.8)
    ax.text(xM + W + 0.55, yT + H / 2 + 0.62, "exports\n~80% of UK\nmetals sent\nout to process",
            ha="center", va="center", fontsize=6.9, color="#7d3c98")

    # legend
    ax.text(0.30, 0.55, "Flow legend:", fontsize=8, fontweight="bold")
    ax.plot([1.7, 2.3], [0.6, 0.6], color="#34495e", lw=2.4)
    ax.text(2.4, 0.6, "primary material", va="center", fontsize=7.6)
    ax.plot([4.3, 4.9], [0.6, 0.6], color="#1e8449", lw=2.4)
    ax.text(5.0, 0.6, "circular return", va="center", fontsize=7.6)
    ax.plot([6.7, 7.3], [0.6, 0.6], color="#b9770e", lw=2.2)
    ax.text(7.4, 0.6, "imports", va="center", fontsize=7.6)
    ax.plot([8.5, 9.1], [0.6, 0.6], color="#566573", lw=1.6, ls="--")
    ax.text(9.2, 0.6, "enabling support", va="center", fontsize=7.6)

    out = os.path.join(FIGDIR, "fig0_supply_chain.png")
    fig.savefig(out, dpi=160, bbox_inches="tight")
    print(f"wrote {os.path.relpath(out, HERE)}")


if __name__ == "__main__":
    main()
