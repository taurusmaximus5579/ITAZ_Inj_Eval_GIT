# -*- coding: utf-8 -*-
"""
Scatter-Matrix mit Hexbin für nicht-signifikante Paare
und Scatter+Regression für signifikante Paare.
Alle signifikanten Korrelationen werden im Balkendiagramm geplottet.
"""

def plot_scatter_matrix(df, out_path=None, figsize=(14, 14), alpha=0.25,
                        r_threshold=0.3, p_threshold=0.05, image_cache=None):

    import matplotlib.pyplot as plt
    import numpy as np
    import pandas as pd
    from scipy.stats import pearsonr, norm
    from itertools import combinations

    # ---------------------------------------------------------
    # 0) Alle Korrelationen berechnen (inkl. CI)
    # ---------------------------------------------------------
    corr_results = []

    cols_all = df.columns.tolist()
    for x, y in combinations(cols_all, 2):
        xv = df[x].values
        yv = df[y].values

        r, p = pearsonr(xv, yv)

        # Fisher-Z Transformation
        z = np.arctanh(r)
        se = 1 / np.sqrt(len(xv) - 3)
        z_crit = norm.ppf(0.975)

        z_low = z - z_crit * se
        z_high = z + z_crit * se

        r_low = np.tanh(z_low)
        r_high = np.tanh(z_high)

        corr_results.append({
            "var_x": x,
            "var_y": y,
            "r": r,
            "p": p,
            "r_low": r_low,
            "r_high": r_high,
            "abs_r": abs(r)
        })

    df_corr = pd.DataFrame(corr_results)

    # Nur signifikante Korrelationen behalten
    df_sig = df_corr[
        (df_corr["abs_r"] >= r_threshold) &
        (df_corr["p"] <= p_threshold)
    ]

    if df_sig.empty:
        raise ValueError("Keine signifikanten Korrelationen gefunden.")

    # Sortieren
    df_sig = df_sig.sort_values("abs_r", ascending=False)

    # ---------------------------------------------------------
    # 0b) Balkendiagramm aller signifikanten Korrelationen
    # ---------------------------------------------------------
    df_plot = df_sig.sort_values("abs_r", ascending=True).iloc[::-1]

    labels = [f"{x} vs {y}" for x, y in zip(df_plot["var_x"], df_plot["var_y"])]
    r = df_plot["r"].values
    r_low = df_plot["r_low"].values
    r_high = df_plot["r_high"].values

    err_low = r - r_low
    err_high = r_high - r
    errors = np.vstack([err_low, err_high])

    fig_corr, ax_corr = plt.subplots(figsize=(10, max(6, len(df_plot)*0.4)))
    ax_corr.barh(labels, r, xerr=errors, color="steelblue",
                 alpha=0.8, ecolor="black", capsize=4)

    ax_corr.set_xlabel("Korrelationskoeffizient r")
    ax_corr.set_title("Alle signifikanten Korrelationen (95%-Konfidenzintervalle)")
    ax_corr.grid(axis="x", linestyle="--", alpha=0.5)

    plt.tight_layout()
    if image_cache is not None:
        from image_utils import persist_or_cache_figure
        persist_or_cache_figure(fig_corr, image_cache=image_cache, category="Shot2Shot", name="Correlations", save_to_disk=False)
    elif out_path:
        fig_corr.savefig(out_path + "_significant.png", dpi=150, bbox_inches="tight")
        plt.close(fig_corr)
    else:
        plt.close(fig_corr)

    # ---------------------------------------------------------
    # 1) Relevante Variablen bestimmen
    # ---------------------------------------------------------
    relevant = set()
    for x, y in combinations(cols_all, 2):
        r, p = pearsonr(df[x].values, df[y].values)
        if abs(r) >= r_threshold and p <= p_threshold:
            relevant.add(x)
            relevant.add(y)

    cols = [c for c in cols_all if c in relevant]
    df = df[cols]
    n = len(cols)

    # ---------------------------------------------------------
    # 2) Scatter-Matrix mit Hexbin/Scatter
    # ---------------------------------------------------------
    fig, axes = plt.subplots(n, n, figsize=figsize)
    fig.tight_layout(pad=2.0)

    for i, y_name in enumerate(cols):
        for j, x_name in enumerate(cols):
            ax = axes[i, j]

            if i == j:
                ax.hist(df[x_name].values, bins=15, color="steelblue", alpha=0.8)
                ax.set_xticks([])
                ax.set_yticks([])
                continue

            x = df[x_name].values
            y = df[y_name].values
            r, p = pearsonr(x, y)

            # Untere Dreiecksmatrix: Scatter oder Hexbin
            if i > j:

                if abs(r) >= r_threshold and p <= p_threshold:
                    # Signifikant → Scatter + Regression
                    ax.scatter(x, y, alpha=alpha, s=10, color="tab:blue")

                    m, b = np.polyfit(x, y, 1)
                    x_line = np.linspace(np.min(x), np.max(x), 100)
                    y_line = m * x_line + b
                    ax.plot(x_line, y_line, color="red", linewidth=1.2)

                else:
                    # Nicht signifikant → Hexbin
                    ax.hexbin(x, y, gridsize=25, cmap="Greys", mincnt=1)

                ax.set_xticks([])
                ax.set_yticks([])
                continue

            # Obere Dreiecksmatrix: r & p
            if i < j:
                ax.text(0.5, 0.55, f"r = {r:.3f}",
                        ha="center", va="center", fontsize=12)
                ax.text(0.5, 0.30, f"p = {p:.3e}",
                        ha="center", va="center", fontsize=11)
                ax.set_xticks([])
                ax.set_yticks([])
                continue

    # ---------------------------------------------------------
    # 3) Achsenbeschriftungen außen
    # ---------------------------------------------------------
    for i, name in enumerate(cols):
        axes[-1, i].set_xlabel(name, rotation=45)
        axes[i, 0].set_ylabel(name, rotation=45, labelpad=60)
        axes[i, 0].yaxis.set_label_position("left")

    if image_cache is not None:
        from image_utils import persist_or_cache_figure
        persist_or_cache_figure(fig, image_cache=image_cache, category="Shot2Shot", name="ScatterMatrix", save_to_disk=False)
    elif out_path:
        fig.savefig(out_path, dpi=150, bbox_inches="tight")
        plt.close(fig)
    else:
        plt.close(fig)
