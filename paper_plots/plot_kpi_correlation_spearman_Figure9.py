import os
import json
import re
from typing import Tuple

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# optional scipy
try:
    from scipy import stats
    SCIPY_AVAILABLE = True
except Exception:
    SCIPY_AVAILABLE = False

BASE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scenarios_final")
OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "figures", "correlations")
os.makedirs(OUT_DIR, exist_ok=True)

def plot_correlation_summary(df):
    """
    Erstellt:
      - correlation_summary.csv
      - corr_to_avg_energy.png
      - corr_to_variance.png
      - corr_to_avg_energy_bar.png
    """

    groups = {
        "All": df,

        "Home": df[df["place"] == "Home"],
        "Work": df[df["place"] == "Work"],

        "ASAP": df[df["strat_pos"] == 0],
        "ALaAP": df[df["strat_pos"] == 1],
        "ALoAP": df[df["strat_pos"] == 2],

        "NegFlex": df[df["modus_pos"] == 0],
        "PosFlex": df[df["modus_pos"] == 1],
    }

    # --- duration ---
    for d in sorted(df["dur_min"].dropna().unique()):
        if d == 59:  # Skip 59 min duration
            continue
        groups[f"dur_{int(d)}min"] = df[df["dur_min"] == d]

    # --- pl_variants ---
    for v in sorted(df["pl_variant"].dropna().unique()):
        groups[f"pl_{v}"] = df[df["pl_variant"] == v]

    # --- start_times (nur spezifische Zeiten) ---
    _TARGET_TIMES = [
        (1.0,        "t01:00"),
        (8.0,        "t08:00"),
        (11+50/60,   "t11:50"),
        (13+50/60,   "t13:50"),
        (16+50/60,   "t16:50"),
        (18+50/60,   "t18:50"),
        (20.0,       "t20:00"),
        (22.0,       "t22:00"),
    ]
    for t_val, t_label in _TARGET_TIMES:
        groups[t_label] = df[np.abs(df["time"] - t_val) < 1e-3]

    rows = []

    for name, sub in groups.items():

        if len(sub) < 3:
            continue

        r_numveh_en, _ = spearman_r_p(
            sub["mean_energy"],
            sub["k_number_of_vehicles"]
        )

        r_soc_en, _ = spearman_r_p(
            sub["mean_energy"],
            sub["k_avg_soc"]
        )

        r_time_en, _ = spearman_r_p(
            sub["mean_energy"],
            sub["k_avg_time"]
        )

        r_var_en, _ = spearman_r_p(
            sub["mean_energy"],
            sub["k_variance"]
        )

        r_numveh_var, _ = spearman_r_p(
            sub["k_variance"],
            sub["k_number_of_vehicles"]
        )

        r_soc_var, _ = spearman_r_p(
            sub["k_variance"],
            sub["k_avg_soc"]
        )

        r_time_var, _ = spearman_r_p(
            sub["k_variance"],
            sub["k_avg_time"]
        )

        r_energy_var, _ = spearman_r_p(
            sub["k_variance"],
            sub["mean_energy"]
        )

        rows.append({
            "Group": name,
            "n": len(sub),

            "AvgEn_NumVeh": r_numveh_en,
            "AvgEn_AvgSOC": r_soc_en,
            "AvgEn_AvgTime": r_time_en,
            "AvgEn_Variance": r_var_en,

            "Var_NumVeh": r_numveh_var,
            "Var_AvgSOC": r_soc_var,
            "Var_AvgTime": r_time_var,
            "Var_AvgEn": r_energy_var,
        })

    summary = pd.DataFrame(rows)

    csv_path = os.path.join(
        OUT_DIR,
        "correlation_summary.csv"
    )
    summary.to_csv(csv_path, index=False)

    print("Saved:", csv_path)

    # =====================================================
    # DOT PLOT - AVG ENERGY
    # =====================================================

    fig, ax = plt.subplots(figsize=(10, 6))

    x_labels = [
        "NumVeh",
        "AvgSOC",
        "AvgTime",
        "Variance"
    ]

    x = np.arange(len(x_labels))

    offsets = np.linspace(
        -0.30,
        0.30,
        len(summary)
    )

    for offset, (_, row) in zip(offsets, summary.iterrows()):

        y = [
            row["AvgEn_NumVeh"],
            row["AvgEn_AvgSOC"],
            row["AvgEn_AvgTime"],
            row["AvgEn_Variance"]
        ]

        ax.scatter(
            x + offset,
            y,
            s=80,
            label=row["Group"]
        )

    ax.axhline(
        0,
        color="black",
        linewidth=1
    )

    ax.set_xticks(x)
    ax.set_xticklabels(x_labels, fontsize = 18)


    ax.set_ylabel("Spearman rho", fontsize = 20)
    ax.set_ylim(-1, 1)

    ax.tick_params(
        axis='y',
        labelsize=18
    )

    ax.legend(
        bbox_to_anchor=(1.02, 1),
        loc="upper left",
        fontsize = 18
    )

    fig.tight_layout()

    fig.savefig(
        os.path.join(
            OUT_DIR,
            "corr_to_avg_energy_spearman.png"
        ),
        dpi=600
    )

    plt.close(fig)

    # =====================================================
    # DOT PLOT - VARIANCE
    # =====================================================

    fig, ax = plt.subplots(figsize=(10, 6))

    x_labels = [
        "NumVeh",
        "AvgSOC",
        "AvgTime",
        "AvgEn"
    ]

    x = np.arange(len(x_labels))

    for offset, (_, row) in zip(offsets, summary.iterrows()):

        y = [
            row["Var_NumVeh"],
            row["Var_AvgSOC"],
            row["Var_AvgTime"],
            row["Var_AvgEn"]
        ]

        ax.scatter(
            x + offset,
            y,
            s=80,
            label=row["Group"]
        )

    ax.axhline(
        0,
        color="black",
        linewidth=1
    )

    ax.set_xticks(x)
    ax.set_xticklabels(x_labels)

    ax.set_ylabel("Spearman rho")
    ax.set_ylim(-1, 1)

    ax.set_title(
        "Correlation to Variance"
    )

    ax.legend(
        bbox_to_anchor=(1.02, 1),
        loc="upper left"
    )

    fig.tight_layout()

    fig.savefig(
        os.path.join(
            OUT_DIR,
            "corr_to_variance_spearman.png"
        ),
        dpi=200
    )

    plt.close(fig)

    # =====================================================
    # BAR PLOT VARIANCE
    # =====================================================

    fig, ax = plt.subplots(figsize=(12, 6))

    metrics_var_bar = ["Var_NumVeh", "Var_AvgSOC", "Var_AvgTime", "Var_AvgEn"]
    metric_labels_var = ["NumVeh", "AvgSOC", "AvgTime", "AvgEn"]
    x_var = np.arange(len(metric_labels_var))
    width_var = 0.8 / len(summary)

    for i, (_, row) in enumerate(summary.iterrows()):
        y = [row[m] for m in metrics_var_bar]
        ax.bar(x_var + i * width_var, y, width=width_var, label=row["Group"])

    ax.axhline(0, color="black", linewidth=1)
    ax.set_xticks(x_var + width_var * len(summary) / 2)
    ax.set_xticklabels(metric_labels_var, fontsize = 20)
    ax.set_ylim(-1, 1)
    ax.set_ylabel("Spearman correlation", fontsize = 20)
    ax.set_xlabel(
        "Flexibility KPI",
        fontsize=20
    )
    ax.tick_params(
        axis='y',
        labelsize=18
    )

    #ax.set_title("Correlation to Variance")
    ax.legend(bbox_to_anchor=(0, 0), loc="lower left", fontsize = 15, ncol = 4)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT_DIR, "corr_to_variance_bar_spearman.png"), dpi=600)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(12, 6))

    metrics = [
        "AvgEn_NumVeh",
        "AvgEn_AvgSOC",
        "AvgEn_AvgTime",
        "AvgEn_Variance"
    ]

    metric_labels = [
        "NumVeh",
        "AvgSOC",
        "AvgTime",
        "Variance"
    ]

    x = np.arange(len(metric_labels))

    width = 0.8 / len(summary)

    for i, (_, row) in enumerate(summary.iterrows()):

        y = [row[m] for m in metrics]

        ax.bar(
            x + i * width,
            y,
            width=width,
            label=row["Group"]
        )

    ax.axhline(
        0,
        color="black",
        linewidth=1
    )

    ax.set_xticks(
        x + width * len(summary) / 2
    )
    ax.tick_params(
        axis='y',
        labelsize=18
    )

    ax.set_xlabel(
        "Flexibility KPI",
        fontsize=20
    )

    ax.set_xticklabels(metric_labels, fontsize = 18)

    ax.set_ylim(-1, 1)

    ax.set_ylabel("Spearman rho", fontsize = 20)
    #ax.set_title(
    #    "Correlation to Average Energy"
    #)

    ax.legend(
        bbox_to_anchor=(0, 0),
        loc="lower left", ncol = 4, fontsize = 15
    )

    fig.tight_layout()

    fig.savefig(
        os.path.join(
            OUT_DIR,
            "corr_to_avg_energy_bar_spearman.png"
        ),
        dpi=600
    )

    plt.close(fig)

    label_map = {
        "All": "All scenarios",
        "Home": "Home",
        "Work": "Work",
        
        "ASAP": "ASAP",
        "ALaAP": "ALaAP",
        "ALoAP": "ALoAP",
        
        "NegFlex": "Negative",
        "PosFlex": "Positive",
        
        "dur_15min": "Duration: 15 min",
        "dur_60min": "Duration: 60 min",

        "pl_low": "Plugin scenario: plLow",
        "pl_medium": "Plugin scenario: plMedium",
        "pl_normal": "Plugin scenario: plHigh",

        "t01:00": "Start time: 01:00",
        "t08:00": "Start time: 08:00",
        "t11:50": "Start time: 11:30",
        "t13:50": "Start time: 13:30",
        "t16:50": "Start time: 16:30",
        "t18:50": "Start time: 18:30",
        "t20:00": "Start time: 20:00",
        "t22:00": "Start time: 22:00",
    }
    
    # Sortiere summary in gewünschter Reihenfolge für Legende
    # 7 Spalten: 
    # 1) All, Home, Work
    # 2) ASAP, ALaAP, ALoAP
    # 3) NegFlex, PosFlex, dur_15min
    # 4) dur_60min, t01:00, t08:00
    # 5) t11:50, t13:50, t16:50
    # 6) t18:50, t20:00, t22:00
    # 7) pl_low, pl_medium, pl_normal
    desired_order = [
        "All",
        "Home", "Work",
        "ASAP", "ALaAP", "ALoAP",
        "NegFlex", "PosFlex", "dur_15min",
        "dur_60min", "t01:00", "t08:00",
        "t11:50", "t13:50", "t16:50",
        "t18:50", "t20:00", "t22:00",
        "pl_low", "pl_medium", "pl_normal",
    ]
    
    # Nur die Gruppen verwenden, die tatsächlich in summary vorhanden sind
    order_indices = []
    for group in desired_order:
        if group in summary["Group"].values:
            order_indices.append(summary[summary["Group"] == group].index[0])
    
    summary = summary.loc[order_indices].reset_index(drop=True)
    # =====================================================
    # COMBINED BAR PLOTS
    # =====================================================

    fig, (ax2, ax1) = plt.subplots(
        2,
        1,
        figsize=(16, 14)
    )
    fig.subplots_adjust(hspace=0.35, bottom=0.28)

    # Farben basierend auf der Gruppenzugehörigkeit zuordnen
    def get_color_for_group(group_name):
        """Wähle Farbe basierend auf der Gruppe - konsistente Farbfamilien"""
        # Definiere Farbpaletten für jede Kategorie
        color_palettes = {
            # All - Schwarz
            "All": "#000000",
            
            # Place - Blautöne
            "Home": "#1f77b4",      # Dunkelblau
            "Work": "#aec7e8",      # Hellblau
            
            # Charging Strategy - Rottöne
            "ASAP": "#d62728",      # Dunkelrot
            "ALaAP": "#ff7f0e",     # Orange-rot
            "ALoAP": "#ffbb78",     # Helles Orange
            
            # Flexibility - Grüntöne
            "NegFlex": "#2ca02c",   # Dunkelgrün
            "PosFlex": "#98df8a",   # Hellgrün
            
            # Duration - Purpurne/Violett
            "dur_15min": "#9467bd",     # Dunkelviolett
            "dur_60min": "#c5b0d5",     # Hellviolett
            
            # Plugin-activity - Graue Töne (alle aus einer Familie!)
            "pl_low": "#404040",        # Dunkelgrau
            "pl_medium": "#808080",     # Mittelgrau
            "pl_normal": "#c0c0c0",     # Hellgrau
            
            # Start times - Cyan/Türkis Töne (alle aus einer Familie!)
            "t01:00": "#0d82a8",        # Dunkelcyan
            "t08:00": "#1fa9c4",        # Mitteldunkelcyan
            "t11:50": "#40b4d0",        # Mittelhellcyan
            "t13:50": "#6dcce0",        # Hellcyan
            "t16:50": "#9de3eb",        # Sehr hellcyan
            "t18:50": "#b8eef6",        # Sehr hellcyan 2
            "t20:00": "#c9f3f9",        # Sehr hellcyan 3
            "t22:00": "#e0fafe",        # Extrahellcyan
        }
        
        return color_palettes.get(group_name, "#808080")
    
    # Liste der Farben für jede Gruppe in summary
    colors = [get_color_for_group(g) for g in summary["Group"]]

    # =====================================================
    # VARIANCE
    # =====================================================

    metrics_var = [
        "Var_NumVeh",
        "Var_AvgSOC",
        "Var_AvgTime",
        "Var_AvgEn"
    ]

    labels_var = [
        "NumVeh",
        "AvgSOC",
        "AvgTime",
        "AvgEn"
    ]

    x_var = np.arange(len(labels_var))

    width_var = 0.8 / len(summary)

    handles = []

    for i, (_, row) in enumerate(summary.iterrows()):
        color = colors[i]

        bars = ax1.bar(
            x_var + i * width_var,
            [row[m] for m in metrics_var],
            width=width_var,
            color=color,
            edgecolor="black",
            linewidth=0.3,
            label=label_map.get(row["Group"], row["Group"])
        )

        handles.append(bars[0])

    ax1.axhline(
        0,
        color="black",
        linewidth=1
    )

    ax1.set_xticks(
        x_var + width_var * len(summary) / 2
    )

    ax1.set_xticklabels(
        labels_var,
        fontsize=20
    )

    ax1.tick_params(
        axis='y',
        labelsize=18
    )

    ax1.set_ylabel(
        "Spearman correlation",
        fontsize=20
    )

    ax1.set_xlabel(
        "Flexibility KPI",
        fontsize=20
    )

    ax1.set_ylim(-0.3, 1)

    ax1.set_title(
        "Correlation to Variance (Var)",
        fontsize=20
    )

    # =====================================================
    # AVG ENERGY
    # =====================================================

    metrics_en = [
        "AvgEn_NumVeh",
        "AvgEn_AvgSOC",
        "AvgEn_AvgTime",
        "AvgEn_Variance"
    ]

    labels_en = [
        "NumVeh",
        "AvgSOC",
        "AvgTime",
        "Variance"
    ]

    x_en = np.arange(len(labels_en))

    width_en = 0.8 / len(summary)

    for i, (_, row) in enumerate(summary.iterrows()):
        color = colors[i]

        ax2.bar(
            x_en + i * width_en,
            [row[m] for m in metrics_en],
            width=width_en,
            color=color,
            edgecolor="black",
            linewidth=0.3
        )
    ax2.set_ylim(-0.3, 1)
    ax2.axhline(
        0,
        color="black",
        linewidth=1
    )

    ax2.set_xticks(
        x_en + width_en * len(summary) / 2
    )

    ax2.set_xticklabels(
        labels_en,
        fontsize=20
    )

    ax2.tick_params(
        axis='y',
        labelsize=18
    )
    ax2.set_title(
        "Correlation to average Energy (AvgEn)",
        fontsize=20
    )

    ax2.set_ylabel(
        "Spearman correlation",
        fontsize=20
    )

    ax2.set_xlabel(
        "Flexibility KPI",
        fontsize=20
    )





    # =====================================================
    # SHARED LEGEND
    # =====================================================

    legend_labels = [
        label_map.get(g, g)
        for g in summary["Group"]
    ]
    
    # Entferne Präfixe aus den Legendennamen (da die Spaltenüberschriften das bereits sagen)
    cleaned_labels = []
    for label in legend_labels:
        if label.startswith("Duration: "):
            cleaned_labels.append(label.replace("Duration: ", ""))
        elif label.startswith("Start time: "):
            cleaned_labels.append(label.replace("Start time: ", ""))
        elif label.startswith("Plugin scenario: "):
            cleaned_labels.append(label.replace("Plugin scenario: ", ""))
        else:
            cleaned_labels.append(label)
    
    legend_labels = cleaned_labels

    fig.legend(
        handles,
        legend_labels,
        loc="lower center",
        bbox_to_anchor=(0.5, 0.04),
        ncol=7,
        fontsize=17,
        frameon=True
    )

    # Spaltenüberschriften über der Legende
    # Basierend auf der gewünschten Struktur der 7 Spalten
    column_headers = [
        "Charging\nLocation:",
        "Charging\nStrategy:",
        "Flexibility\nDirection /\nFDP Duration:",
        "FDP Duration /\nFDP Start time:",
        "FDP Start time:",
        "",
        "Plugin\nscenario:"
    ]
    
    # Berechne x-Positionen für 7 Spalten - angepasst für unterschiedliche Spaltenbreiten
    ncols = 7
    # Manuelle Positionierung für bessere Alignment
    x_positions = [
        0.15,   # Charging Location (mehr nach rechts)
        0.29,   # Charging Strategy (noch mehr nach rechts)
        0.42,   # Flexibility Direction / Duration (kleines bisschen nach rechts)
        0.54,   # Duration / Start time (kleines bisschen nach rechts)
        0.715,  # Start time (mittig über beiden Start-time-Spalten)
        0.77,   # ungenutzt (Header leer)
        0.88    # Plugin-activity
    ]
    
    for i, (header, x_pos) in enumerate(zip(column_headers, x_positions)):
        if header:  # Nur zeichnen wenn nicht leer
            fig.text(
                x_pos,
                0.21,
                header,
                ha="center",
                va="top",
                fontsize=18
            )

    #fig.tight_layout(
    #    rect=[0, 0.08, 1, 1]
    #)

    fig.savefig(
        os.path.join(
            OUT_DIR,
            "correlation_summary_bars_spearman.png"
        ),
        dpi=300,
        bbox_inches="tight"
    )
    fig.savefig(
        "figures/correlation_summary_bars_spearman_Figure9.png",

        dpi=300,
        bbox_inches="tight"
    )
    print("Saved: correlation_summary_bars_spearman.png")

    plt.close(fig)

    # =====================================================
    # COMBINED: alle group_types in je einem Plot fuer AvgEn und Var
    # =====================================================
    metrics_en   = ["AvgEn_NumVeh", "AvgEn_AvgSOC", "AvgEn_AvgTime", "AvgEn_Variance"]
    metrics_var  = ["Var_NumVeh",   "Var_AvgSOC",   "Var_AvgTime",   "Var_AvgEn"]
    x_labels_en  = ["NumVeh", "AvgSOC", "AvgTime", "Variance"]
    x_labels_var = ["NumVeh", "AvgSOC", "AvgTime", "AvgEn"]
    x = np.arange(4)

    all_gt_rows = []
    for gt in sorted(df["group_type"].dropna().unique()):
        if gt.startswith("work"):
            continue
        sub_gt = df[df["group_type"] == gt]
        for gn in sorted(sub_gt["group_num"].dropna().unique()):
            sub = sub_gt[sub_gt["group_num"] == gn]
            if len(sub) < 3:
                continue
            r_en  = [spearman_r_p(sub["mean_energy"], sub[c])[0]
                     for c in ("k_number_of_vehicles", "k_avg_soc", "k_avg_time", "k_variance")]
            r_var = [spearman_r_p(sub["k_variance"],   sub[c])[0]
                     for c in ("k_number_of_vehicles", "k_avg_soc", "k_avg_time", "mean_energy")]
            all_gt_rows.append({
                "Group": f"{gt}_{int(gn)}",
                "group_type": gt,
                "group_num": int(gn),
                "n": len(sub),
                **dict(zip(metrics_en, r_en)),
                **dict(zip(metrics_var, r_var)),
            })

    if all_gt_rows:
        gt_summary_all = pd.DataFrame(all_gt_rows)
        unique_gts = sorted(gt_summary_all["group_type"].unique())
        cmap_gt = plt.cm.tab20.colors

        for target, mlist, xlbls, fname_suffix in [
            ("AvgEn", metrics_en,  x_labels_en,  "avg_energy"),
            ("Var",   metrics_var, x_labels_var, "variance"),
        ]:
            fig, ax = plt.subplots(figsize=(14, 6))
            offsets_all = np.linspace(-0.35, 0.35, len(gt_summary_all))
            for offset, (_, row) in zip(offsets_all, gt_summary_all.iterrows()):
                color = cmap_gt[unique_gts.index(row["group_type"]) % len(cmap_gt)]
                ax.scatter(x + offset, [row[m] for m in mlist],
                           s=60, color=color, label=row["Group"])
            ax.axhline(0, color="black", linewidth=1)
            ax.set_xticks(x)
            ax.set_xticklabels(xlbls)
            ax.set_ylabel("Spearman rho")
            ax.set_ylim(-1, 1)
            ax.set_title(f"All group types \u2014 Correlation to {target}")
            ax.legend(bbox_to_anchor=(1.02, 1), loc="upper left", fontsize=7, ncol=2)
            fig.tight_layout()
            fig.savefig(os.path.join(OUT_DIR, f"corr_all_groups_{fname_suffix}_spearman.png"), dpi=200)
            plt.close(fig)
            print(f"Saved: corr_all_groups_{fname_suffix}.png")

        # --- Bar plots: 4 subplots (one per metric), groups on x-axis ---
        for target, mlist, xlbls, fname_suffix in [
            ("AvgEn", metrics_en,  x_labels_en,  "avg_energy"),
            ("Var",   metrics_var, x_labels_var, "variance"),
        ]:
            fig, axes = plt.subplots(1, 4, figsize=(22, 5), sharey=True, constrained_layout=True)
            group_names = gt_summary_all["Group"].tolist()
            group_types = gt_summary_all["group_type"].tolist()
            bar_colors = [cmap_gt[unique_gts.index(gt) % len(cmap_gt)] for gt in group_types]
            x_grp = np.arange(len(group_names))

            for ax_i, (metric, xlabel) in enumerate(zip(mlist, xlbls)):
                ax = axes[ax_i]
                vals = gt_summary_all[metric].tolist()
                ax.bar(x_grp, vals, color=bar_colors, width=0.7)
                ax.axhline(0, color="black", linewidth=0.8)
                ax.set_xticks(x_grp)
                ax.set_xticklabels(group_names, rotation=90, fontsize=7)
                ax.set_ylim(-1, 1)
                ax.set_title(xlabel, fontsize=12)
                if ax_i == 0:
                    ax.set_ylabel("Spearman rho")

            # legend für group_type Farben
            from matplotlib.patches import Patch
            legend_handles = [Patch(color=cmap_gt[i % len(cmap_gt)], label=gt)
                              for i, gt in enumerate(unique_gts)]
            fig.legend(handles=legend_handles, loc="lower center",
                       ncol=len(unique_gts), fontsize=8, bbox_to_anchor=(0.5, -0.02))
            fig.suptitle(f"All group types — Correlation to {target}", fontsize=13)
            out_bar = os.path.join(OUT_DIR, f"corr_all_groups_{fname_suffix}_bar_spearman.png")
            fig.savefig(out_bar, dpi=200, bbox_inches="tight")
            plt.close(fig)
            print(f"Saved: corr_all_groups_{fname_suffix}_bar.png")

    return summary

# helper parsing
def parse_model(model_str: str) -> Tuple[str, int]:
    m = re.match(r"^([a-zA-Z]+)_(\d+)$", model_str)
    if not m:
        return None, None
    return m.group(1), int(m.group(2))


def extract_model(path: str) -> str:
    m = re.search(r"model_pl_(?:normal|low|medium)_([a-zA-Z]+_\d+)", path)
    return m.group(1) if m else None


def extract_pl_variant(path: str) -> str:
    m = re.search(r"model_pl_(normal|low|medium)_", path)
    return m.group(1) if m else None


def extract_time(path: str) -> float:
    m = re.search(r"_t(\d+)_(\d+)", path)
    if not m:
        return None
    return int(m.group(1)) + int(m.group(2)) / 60.0


def extract_dur(path: str) -> int:
    m = re.search(r"_dur(\d+)", path)
    return int(m.group(1)) if m else None


def extract_act(path: str) -> float:
    m = re.search(r"_act(\d+)_(\d+)", path)
    if not m:
        return None
    return int(m.group(1)) + int(m.group(2)) / 100.0


def extract_spont(path: str) -> bool:
    return 'spontTrue' in path


def extract_place(path: str) -> str:
    if 'placeHome' in path:
        return 'Home'
    if 'placeWork' in path:
        return 'Work'
    return None


# Systematic parameter grid actually used for the paper (table "Simulation model and
# flexibility specifications for correlation analysis"). Any file whose extracted
# time/dur/act/spont combination does not match this grid is a leftover/exploratory
# run (e.g. extra full-hour spontTrue scans, extra act fractions) and gets excluded.
_CANONICAL_TIMES_HOME = {1.0, 8.0, 11 + 50/60, 13 + 50/60, 16 + 50/60, 18 + 50/60, 20.0, 22.0}
_CANONICAL_TIMES_WORK = {8.0, 11.0, 12 + 50/60, 14.0, 15 + 50/60, 17.0}


def is_canonical_time(place: str, time: float) -> bool:
    if time is None:
        return False
    times = _CANONICAL_TIMES_WORK if place == 'Work' else _CANONICAL_TIMES_HOME
    return any(abs(time - t) < 1e-3 for t in times)


def is_canonical_combo(dur, act, spont: bool) -> bool:
    if dur not in (15, 60):
        return False
    if act is None:
        return False
    if spont:
        return abs(act) < 1e-9
    if abs(act - 0.25) < 1e-9 or abs(act - 0.75) < 1e-9:
        return dur == 60
    if abs(act - 0.5) < 1e-9 or abs(act - 1.0) < 1e-9:
        return True
    return False


def find_jsons():
    files = []
    for root, _, fs in os.walk(BASE_DIR):
        for f in fs:
            if not f.endswith('.json'):
                continue
            full = os.path.join(root, f)
            #if 'agegroup_4' in full:
            #    continue
            files.append(full)
    return files


def extract_kpis(entry: dict):
    kpis = entry.get('kpi_statistics')
    energy = entry.get("quantiles_energy_kwh")
    if isinstance(kpis, list) and len(kpis) >= 5:
        try:
            return (
                kpis[0].get('avg'),
                kpis[1].get('avg'),

                kpis[4].get('avg'),
                energy.get('var'),
            )
        except Exception:
            pass


    fallback = []
    for key in ('number_of_vehicles', 'avg_soc', 'avg_time'):
        fallback.append(entry.get(key))
    fallback.append(entry.get('quantiles_energy_kwh', {}).get('var'))
    return tuple(fallback)


def spearman_r_p(x, y):
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    mask = ~np.isnan(x) & ~np.isnan(y)
    if mask.sum() < 3:
        return np.nan, np.nan
    if SCIPY_AVAILABLE:
        try:
            r, p = stats.spearmanr(x[mask], y[mask])
        except Exception:
            r = np.nan
            p = np.nan
    else:
        r = np.nan
        p = np.nan
    return r, p


def build_dataframe(files):
    rows = []
    for p in files:
        model = extract_model(p)
        if model is None:
            continue
        group_type, group_num = parse_model(model)
        time = extract_time(p)
        dur = extract_dur(p)
        act = extract_act(p)
        spont = extract_spont(p)
        place = extract_place(p)

        # Skip leftover/exploratory files that are not part of the systematic
        # parameter grid (see table in the paper) so they don't skew the correlations.
        if not is_canonical_time(place, time) or not is_canonical_combo(dur, act, spont):
            continue

        with open(p, encoding='utf-8') as fh:
            try:
                data = json.load(fh)
            except Exception:
                continue
        for entry in data.get('risk_combinations', []):
            c = entry.get('combination', {})
            strat = c.get('strat_pos')
            heuristic = c.get('heuristic_pos')
            modus = c.get('modus_pos')
            energy = entry.get('quantiles_energy_kwh', {})
            mean_e = energy.get('mean')
            if mean_e is None:
                continue
            k0, k1, k4, k5 = extract_kpis(entry)
            rows.append({
                'model': model,
                'group_type': group_type,
                'group_num': group_num,
                'pl_variant': extract_pl_variant(p),
                'place': place,
                'time': time,
                'dur_min': dur,
                'dur_h': (dur/60.0) if dur is not None else None,
                'act_h': act,
                'spont': spont,
                'strat_pos': strat,
                'heuristic_pos': heuristic,
                'modus_pos': modus,
                'mean_energy': mean_e,
                'k_number_of_vehicles': k0,
                'k_avg_soc': k1,

                'k_avg_time': k4,
                'k_variance': k5
            })
    return pd.DataFrame(rows)


def save_heatmap(corr, cols, path, title=''):
    fig, ax = plt.subplots(figsize=(6, 5))
    cax = ax.imshow(corr, cmap='coolwarm', vmin=-1, vmax=1)
    ax.set_xticks(range(len(cols)))
    ax.set_xticklabels(cols, rotation=45, ha='right')
    ax.set_yticks(range(len(cols)))
    ax.set_yticklabels(cols)
    fig.colorbar(cax, ax=ax)
    ax.set_title(title)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def compute_and_save(df, group_name, sub, out_prefix):
    cols = ['mean_energy', 'k_number_of_vehicles', 'k_avg_soc', 'k_avg_time', 'k_variance']
    if len(sub) < 3:
        return None
    corr = sub[cols].corr()
    out_png = os.path.join(OUT_DIR, f"{out_prefix}.png")
    save_heatmap(corr.values, cols, out_png, title=f'corr {group_name} (n={len(sub)})')
    # compute r and p for each KPI
    results = {}
    for k in cols[1:]:
        r, p = spearman_r_p(sub['mean_energy'], sub[k])
        results[k] = {'r': r, 'p': p}
    return results


def run_all(df):
    rows = []
    # overall
    res = compute_and_save(df, 'overall', df, 'overall')
    rows.append(("overall", res))

    # spont True/False — but for spont True require act_h == dur_h
    df_spont = df.copy()
    mask_spont_true = (df_spont['spont'] == True) & (~df_spont['act_h'].isna()) & (~df_spont['dur_h'].isna())
    df_spont_true = df_spont[mask_spont_true & (df_spont['act_h'].round(3) == df_spont['dur_h'].round(3))]
    df_spont_false = df[df['spont'] == False]
    compute_and_save(df_spont_true, 'spontTrue_act==dur', df_spont_true, 'spontTrue_act_eq_dur')
    compute_and_save(df_spont_false, 'spontFalse', df_spont_false, 'spontFalse')

    # by duration
    for d in sorted(df['dur_min'].dropna().unique()):
        if d == 59:  # Skip 59 min duration
            continue
        sub = df[df['dur_min'] == d]
        res = compute_and_save(sub, f'dur{int(d)}', sub, f'dur_{int(d)}')
        rows.append((f'dur_{int(d)}', res))

    # by group_type and group_num
    for gt in sorted(df['group_type'].dropna().unique()):
        sub_gt = df[df['group_type'] == gt]
        compute_and_save(sub_gt, f'{gt}_overall', sub_gt, f'{gt}_overall')
        for gn in sorted(sub_gt['group_num'].dropna().unique()):
            sub = sub_gt[sub_gt['group_num'] == gn]
            compute_and_save(sub, f'{gt}_{int(gn)}', sub, f'{gt}_{int(gn)}')

    # strat_pos, modus_pos combinations
    for strat in sorted(df['strat_pos'].dropna().unique()):
        sub = df[df['strat_pos'] == strat]
        compute_and_save(sub, f'strat_{int(strat)}', sub, f'strat_{int(strat)}')
    for modus in sorted(df['modus_pos'].dropna().unique()):
        sub = df[df['modus_pos'] == modus]
        compute_and_save(sub, f'modus_{int(modus)}', sub, f'modus_{int(modus)}')

    # combinations (no group types for combos): duration + strat_pos, duration + modus_pos, strat+modus
    combos = []
    for d in sorted(df['dur_min'].dropna().unique()):
        if d == 59:  # Skip 59 min duration
            continue
        for strat in sorted(df['strat_pos'].dropna().unique()):
            sub = df[(df['dur_min'] == d) & (df['strat_pos'] == strat)]
            compute_and_save(sub, f'd{int(d)}_s{int(strat)}', sub, f'combo_d{int(d)}_s{int(strat)}')
            combos.append((f'd{int(d)}_s{int(strat)}', len(sub)))
        for modus in sorted(df['modus_pos'].dropna().unique()):
            sub = df[(df['dur_min'] == d) & (df['modus_pos'] == modus)]
            compute_and_save(sub, f'd{int(d)}_m{int(modus)}', sub, f'combo_d{int(d)}_m{int(modus)}')
            combos.append((f'd{int(d)}_m{int(modus)}', len(sub)))
    for strat in sorted(df['strat_pos'].dropna().unique()):
        for modus in sorted(df['modus_pos'].dropna().unique()):
            sub = df[(df['strat_pos'] == strat) & (df['modus_pos'] == modus)]
            compute_and_save(sub, f's{int(strat)}_m{int(modus)}', sub, f'combo_s{int(strat)}_m{int(modus)}')
            combos.append((f's{int(strat)}_m{int(modus)}', len(sub)))

    # times of interest
    times = [1 + 50/60, 8.0, 11 + 50/60, 13 + 50/60, 16 + 50/60, 18 + 50/60, 20.0, 22.0]
    for t in times:
        sub = df[np.abs(df['time'] - t) < 1e-3]
        compute_and_save(sub, f't{int(t)}_{int(round((t-int(t))*60))}', sub, f't_{int(t)}_{int(round((t-int(t))*60))}')

    # save summary CSV of combos sizes
    combos_df = pd.DataFrame(combos, columns=['combo', 'n'])
    combos_df.to_csv(os.path.join(OUT_DIR, 'combo_sizes.csv'), index=False)

def plot_selected_subplots(df):
    cols = [
        'mean_energy',
        'k_number_of_vehicles',
        'k_avg_soc',
        'k_avg_time',
        'k_variance'
    ]

    # ✅ neue Display-Namen für Achsen
    col_labels = ['AvgEn', 'NumVeh', 'AvgSOC', 'AvgTime', 'Var']

    subsets = {
        "All": df,

        "Negative flexibility": df[df['modus_pos'] == 0],
        "Positive flexibility": df[df['modus_pos'] == 1],

        "Start time: 6:30 pm": df[np.abs(df['time'] - (18 + 50/60)) < 1e-3],

        "Duration: 15 min,\n ch. strategy: ALaAP":
            df[(df['dur_min'] == 15) & (df['strat_pos'] == 1)],

        "Ch. strategy: ASAP": df[df['strat_pos'] == 0],
        "Ch. strategy: ALaAP": df[df['strat_pos'] == 1],
        "Ch. strategy: ALoAP": df[df['strat_pos'] == 2],
    }

    n_plots = len(subsets)
    ncols = 2
    nrows = int(np.ceil(n_plots / ncols))

    fig, axes = plt.subplots(
        nrows,
        ncols,
        figsize=(5*ncols, 4*nrows),
        constrained_layout=True
    )

    axes = axes.flatten()
    im = None

    for i, (name, sub) in enumerate(subsets.items()):
        ax = axes[i]

        if len(sub) < 3:
            ax.set_title(f"{name}\n(n<{3})")
            ax.axis("off")
            continue

        corr = sub[cols].corr()
        im = ax.imshow(corr.values, cmap='coolwarm', vmin=-1, vmax=1)

        # ✅ X-Achse
        if i // ncols == nrows - 1:
            ax.set_xticks(range(len(cols)))
            ax.set_xticklabels(col_labels, rotation=45, ha='right', fontsize=20)
        else:
            ax.set_xticks([])

        # ✅ Y-Achse
        if i % ncols == 0:
            ax.set_yticks(range(len(cols)))
            ax.set_yticklabels(col_labels, fontsize=20)
        else:
            ax.set_yticks([])

        ax.set_title(f"{name}\n(n={len(sub)})", fontsize = 20)
        ax.set_aspect('equal')

    # restliche axes ausblenden
    for j in range(i + 1, len(axes)):
        axes[j].axis("off")

    # ✅ gemeinsame Colorbar
    cbar = fig.colorbar(
        im,
        ax=axes,
        location='right',
        shrink=0.85,
        pad=0.02
    )
    cbar.set_label("Correlation")

    out_path = os.path.join(OUT_DIR, "selected_subplots.png")
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def plot_place_and_variant(df):
    """Korrelations-Heatmaps je Place (Home/Work) und pl_variant (normal/low/medium)."""
    cols = ['mean_energy', 'k_number_of_vehicles', 'k_avg_soc', 'k_avg_time', 'k_variance']
    col_labels = ['AvgEn', 'NumVeh', 'AvgSOC', 'AvgTime', 'Var']

    places = sorted(df['place'].dropna().unique())
    variants = sorted(df['pl_variant'].dropna().unique())

    # --- Plot 1: Home vs Work ---
    subsets_place = [("All", df)] + [(p, df[df['place'] == p]) for p in places]
    _save_corr_grid(subsets_place, cols, col_labels, "place_comparison.png", "Place comparison")

    # --- Plot 2: pl_variant ---
    subsets_variant = [("All", df)] + [(v, df[df['pl_variant'] == v]) for v in variants]
    _save_corr_grid(subsets_variant, cols, col_labels, "variant_comparison.png", "PL variant comparison")

    # --- Plot 3: place × variant grid ---
    subsets_combined = []
    for p in places:
        for v in variants:
            sub = df[(df['place'] == p) & (df['pl_variant'] == v)]
            subsets_combined.append((f"{p}\n{v}", sub))
    _save_corr_grid(subsets_combined, cols, col_labels, "place_x_variant.png", "Place × Variant",
                    ncols=len(variants), nrows=len(places))


def _save_corr_grid(subsets, cols, col_labels, filename, title, ncols=None, nrows=1):
    if ncols is None:
        ncols = len(subsets)
        nrows = 1
    fig, axes = plt.subplots(nrows, ncols, figsize=(5 * ncols, 5 * nrows), constrained_layout=True,
                             squeeze=False)
    axes_flat = axes.flatten()
    im = None
    for i, (name, sub) in enumerate(subsets):
        ax = axes_flat[i]
        if len(sub) < 3:
            ax.axis('off')
            ax.set_title(f"{name}\n(n<3)", fontsize=13)
            continue
        corr = sub[cols].corr()
        im = ax.imshow(corr.values, cmap='coolwarm', vmin=-1, vmax=1)
        ax.set_xticks(range(len(cols)))
        ax.set_xticklabels(col_labels, rotation=45, ha='right', fontsize=12)
        row_i, col_i = divmod(i, ncols)
        if col_i == 0:
            ax.set_yticks(range(len(cols)))
            ax.set_yticklabels(col_labels, fontsize=12)
        else:
            ax.set_yticks([])
        ax.set_title(f"{name}\n(n={len(sub)})", fontsize=13)
        ax.set_aspect('equal')
    for j in range(len(subsets), len(axes_flat)):
        axes_flat[j].axis('off')
    if im is not None:
        fig.colorbar(im, ax=axes_flat, location='right', shrink=0.8, pad=0.02)
    fig.suptitle(title, fontsize=14)
    out_path = os.path.join(OUT_DIR, filename)
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    print(f"Saved: {filename}")


def plot_groups_comparison(df):
    """Für jeden group_type ein Subplot-Grid mit allen group_nums."""
    cols = ['mean_energy', 'k_number_of_vehicles', 'k_avg_soc', 'k_avg_time', 'k_variance']
    col_labels = ['AvgEn', 'NumVeh', 'AvgSOC', 'AvgTime', 'Var']

    group_types = sorted(df['group_type'].dropna().unique())

    for gt in group_types:
        sub_gt = df[df['group_type'] == gt]
        group_nums = sorted(sub_gt['group_num'].dropna().unique())

        subsets = [(f"{gt} (all)", sub_gt)] + [
            (f"{gt}_{int(gn)}", sub_gt[sub_gt['group_num'] == gn])
            for gn in group_nums
        ]

        ncols = len(subsets)
        fig, axes = plt.subplots(1, ncols, figsize=(5 * ncols, 5), constrained_layout=True)
        if ncols == 1:
            axes = [axes]

        im = None
        for i, (name, sub) in enumerate(subsets):
            ax = axes[i]
            if len(sub) < 3:
                ax.axis('off')
                ax.set_title(f"{name}\n(n<3)", fontsize=13)
                continue
            corr = sub[cols].corr()
            im = ax.imshow(corr.values, cmap='coolwarm', vmin=-1, vmax=1)
            ax.set_xticks(range(len(cols)))
            ax.set_xticklabels(col_labels, rotation=45, ha='right', fontsize=12)
            if i == 0:
                ax.set_yticks(range(len(cols)))
                ax.set_yticklabels(col_labels, fontsize=12)
            else:
                ax.set_yticks([])
            ax.set_title(f"{name}\n(n={len(sub)})", fontsize=13)
            ax.set_aspect('equal')

        if im is not None:
            fig.colorbar(im, ax=axes, location='right', shrink=0.8, pad=0.02)

        out_path = os.path.join(OUT_DIR, f"groups_{gt}.png")
        fig.savefig(out_path, dpi=150)
        plt.close(fig)
        print(f"Saved: groups_{gt}.png")


def plot_work_breakdown(df):
    """Work-Szenarien nach modus_pos und strat_pos aufgeschlüsselt."""
    df_work = df[df['place'] == 'Work']

    # modus_pos
    modus_vals = sorted(df_work['modus_pos'].dropna().unique())
    subsets_modus = [('Work (all)', df_work)] + [
        (f'Work modus_{int(m)}', df_work[df_work['modus_pos'] == m])
        for m in modus_vals
    ]
    _save_corr_grid(subsets_modus, 
                    ['mean_energy', 'k_number_of_vehicles', 'k_avg_soc', 'k_avg_time', 'k_variance'],
                    ['AvgEn', 'NumVeh', 'AvgSOC', 'AvgTime', 'Var'],
                    'work_modus.png', 'Work — by modus_pos')

    # strat_pos
    strat_vals = sorted(df_work['strat_pos'].dropna().unique())
    subsets_strat = [('Work (all)', df_work)] + [
        (f'Work strat_{int(s)}', df_work[df_work['strat_pos'] == s])
        for s in strat_vals
    ]
    _save_corr_grid(subsets_strat,
                    ['mean_energy', 'k_number_of_vehicles', 'k_avg_soc', 'k_avg_time', 'k_variance'],
                    ['AvgEn', 'NumVeh', 'AvgSOC', 'AvgTime', 'Var'],
                    'work_strat.png', 'Work — by strat_pos')

    # strat × modus grid
    subsets_combined = []
    for s in strat_vals:
        for m in modus_vals:
            sub = df_work[(df_work['strat_pos'] == s) & (df_work['modus_pos'] == m)]
            subsets_combined.append((f'strat_{int(s)}\nmodus_{int(m)}', sub))
    _save_corr_grid(subsets_combined,
                    ['mean_energy', 'k_number_of_vehicles', 'k_avg_soc', 'k_avg_time', 'k_variance'],
                    ['AvgEn', 'NumVeh', 'AvgSOC', 'AvgTime', 'Var'],
                    'work_strat_x_modus.png', 'Work — strat × modus',
                    ncols=len(modus_vals), nrows=len(strat_vals))


def main():
    files = find_jsons()
    print('Files found:', len(files))
    df = build_dataframe(files)
    if df.empty:
        raise ValueError('no data')
    # apply spont True filter: keep spont False rows as is; for spont True only keep rows where act_h == dur_h
    # (we will perform analyses using subsets inside run_all)
    df.to_csv(os.path.join(OUT_DIR, 'raw_dataframe.csv'), index=False)
    run_all(df)
    plot_correlation_summary(df)
    plot_selected_subplots(df)
    plot_place_and_variant(df)
    plot_groups_comparison(df)
    plot_work_breakdown(df)

if __name__ == '__main__':
    main()
