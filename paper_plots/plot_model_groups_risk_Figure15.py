import os
import json
import re
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

BASE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../scenarios_final")

# ── Fixed scenario selection ─────────────────────────────────────
TARGET_SPONT     = "spontTrue"
TARGET_DUR       = 60
TARGET_STRAT     = 1
TARGET_HEURISTIC = 1
TARGET_MODUS     = 1

# Zeiten als gebrochene Stunden (h + min/60)  →  entsprechen _t1_50, _t8_00 usw.
SELECTED_TIMES = {
    1  + 50/60,   # 01:50
    8.0,          # 08:00
    11 + 50/60,   # 11:50
    13 + 50/60,   # 13:50
    16 + 50/60,   # 16:50
    18 + 50/60,   # 18:50
    20.0,         # 20:00
    22.0,         # 22:00
}


# ── Visualisation mappings ───────────────────────────────────────
GROUP_COLORS = {
    "agegroup":      "#1f77b4",
    "mobilitygroup": "#ff7f0e",
    "econstatus":    "#2ca02c",
    "homogroup":     "#d62728",
    "regiontype":    "#9467bd",
}

GROUP_LABELS = {
    "homogroup": "Homogeneous Group",
    "agegroup": "Age Group",
    "mobilitygroup": "Mobility Group",
    "econstatus": "Economic Status",
    "regiontype": "Region Type",
}

NUMBER_MARKERS = {
    1: "o",
    2: "s",
    3: "^",
    4: "D",
    5: "v",
    6: "P",
    7: "*",
    8: "X",
}


# ── Helpers ──────────────────────────────────────────────────────

def parse_model(model_str):
    match = re.match(r"^([a-zA-Z]+)_(\d+)$", model_str)
    if match:
        return match.group(1), int(match.group(2))
    return None, None


def extract_model(path):
    match = re.search(r"model_pl_normal_([a-zA-Z0-9_]+?)(?:[/\\]|$)", path)
    return match.group(1) if match else None


def extract_time(path):
    match = re.search(r"_t(\d+)_(\d+)", path)
    if match:
        return int(match.group(1)) + int(match.group(2)) / 60.0
    return None


# ── File discovery ───────────────────────────────────────────────

def find_jsons():
    files = []
    for root, _, fs in os.walk(BASE_DIR):
        for f in fs:
            if not f.endswith(".json"):
                continue

            full = os.path.join(root, f)

            if (
                "model_pl_normal_" in full
                and TARGET_SPONT in full
                and f"_dur{TARGET_DUR}_" in full
            ):
                files.append(full)

    return files


# ── Data extraction ──────────────────────────────────────────────

def extract_data(json_path):
    model_str = extract_model(json_path)
    if model_str is None:
        return []

    group_type, group_num = parse_model(model_str)
    if group_type not in GROUP_COLORS:
        return []

    t = extract_time(json_path)
    if t is None:
        return []

    with open(json_path, encoding="utf-8") as fh:
        data = json.load(fh)

    results = []
    for entry in data.get("risk_combinations", []):
        c = entry.get("combination", {})

        if not (
            c.get("strat_pos")     == TARGET_STRAT and
            c.get("heuristic_pos") == TARGET_HEURISTIC and
            c.get("modus_pos")     == TARGET_MODUS
        ):
            continue

        energy = entry.get("quantiles_energy_kwh", {})

        mean = energy.get("mean")
        var  = energy.get("var")

        if mean is None or var is None:
            continue

        results.append({
            "model":      model_str,
            "group_type": group_type,
            "group_num":  group_num,
            "time":       t,
            "mean":       mean,
            "std":        energy.get("std"),
            "var":        var,
        })

    return results


# ── Plot ─────────────────────────────────────────────────────────

def plot(df):

    # ✅ gewünschte Zeiten filtern
    def is_selected(t):
        return any(abs(t - st) < 1e-3 for st in SELECTED_TIMES)

    df = df[df["time"].apply(is_selected)]

    times = sorted(SELECTED_TIMES)

    for t in times:

        fig, ax = plt.subplots(figsize=(7, 5))

        sub = df[df["time"].apply(lambda x: abs(x - t) < 1e-3)]

        if sub.empty:
            print(f"⚠️ keine Daten für Zeit {t}")
            continue

        for _, row in sub.iterrows():

            color  = GROUP_COLORS.get(row["group_type"], "gray")
            marker = NUMBER_MARKERS.get(row["group_num"], "o")

            # ✅ immer sichtbare std-Balken
            min_err = 1e-6
            std_val = row["std"] if row["std"] and row["std"] > 0 else min_err
            yerr = [[std_val], [std_val]]

            ax.errorbar(
                row["var"], row["mean"],
                yerr=yerr,
                fmt=marker,
                color=color,
                markersize=8,
                ecolor=color,
                capsize=4,
                alpha=0.85,
            )

        # ✅ Zeitlabel im ursprünglichen Format
        h = int(t)
        m = int(round((t - h) * 60))
        ax.set_title(f"t{h}_{m:02d}")

        ax.set_xlabel("Variance of Energy [kWh²]")
        ax.set_ylabel("Mean Energy [kWh]")

        ax.grid(alpha=0.3)

        # ── Legende (pro Plot gleich) ─────────────────────
        legend_color_handles = {
            gt: plt.Line2D([], [], color=color, marker="o", linestyle="None", label=gt)
            for gt, color in GROUP_COLORS.items()
        }

        legend_marker_handles = {
            gn: plt.Line2D([], [], color="black",
                           marker=NUMBER_MARKERS.get(gn, "o"),
                           linestyle="None",
                           label=f"Group nr {gn}")
            for gn in sorted(df["group_num"].unique())
        }

        std_handle = plt.Line2D(
            [], [], color="black",
            marker="|",
            linestyle="None",
            markersize=12,
            label="± standard deviation"
        )

        handles = (
            list(legend_color_handles.values()) +
            list(legend_marker_handles.values()) +
            [std_handle]
        )

        ax.legend(handles=handles, fontsize=16, ncol = 2,  loc="best")

        plt.tight_layout()
        plt.show()
from matplotlib.patches import Ellipse

from matplotlib.patches import Rectangle

from matplotlib.patches import Rectangle

def format_time_label(t):
    h = int(t)
    m = int(round((t - h) * 60))

    # 50 Minuten als 30 Minuten anzeigen
    if m == 50:
        m = 30

    suffix = "a.m." if h < 12 else "p.m."

    h12 = h % 12
    if h12 == 0:
        h12 = 12

    #if m == 0:
    #    return f"{h12} {suffix}"
    #else:
     #   return f"{h12}:{m:02d} {suffix}"
    return f"{h}:{m:02d} "


def plot_subplots(df):
    """Subplot für jede Startzeit"""
    
    target_times = {
        1 ,
        8.0,
        #11 + 50/60,
        13 + 50/60,
        #16 + 50/60,
        18 + 50/60,
        20.0,
        22.0
    }

    def is_selected(t):
        return any(abs(t - tt) < 1e-3 for tt in target_times)

    df = df[df["time"].apply(is_selected)]

    times = sorted(target_times)
    n_times = len(times)
    
    # 2x4 oder 4x2 layout
    n_cols = 3
    n_rows = (n_times + n_cols - 1) // n_cols
    
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(16, 11))
    axes = axes.flatten()  # Flatten für einfache Indexierung

    # Berechne gemeinsame Achsen-Limits
    all_vars = []
    all_means = []
    for t in times:
        sub = df[df["time"].apply(lambda x: abs(x - t) < 1e-3)]
        if not sub.empty:
            all_vars.extend(sub["var"].values)
            all_means.extend(sub["mean"].values)
    
    if all_vars and all_means:
        x_min, x_max = min(all_vars), max(all_vars)
        y_min, y_max = min(all_means), max(all_means)
        # Kleine Puffer
        x_margin = (x_max - x_min) * 0.05
        y_margin = (y_max - y_min) * 0.05
        x_lims = (x_min - x_margin, x_max + x_margin)
        y_lims = (y_min - y_margin, y_max + y_margin)
    else:
        x_lims = (0, 1)
        y_lims = (0, 1)

    for idx, t in enumerate(times):
        ax = axes[idx]
        
        sub = df[df["time"].apply(lambda x: abs(x - t) < 1e-3)]

        if sub.empty:
            ax.text(0.5, 0.5, f"⚠️ keine Daten\nfür Zeit {t}", 
                    ha="center", va="center", transform=ax.transAxes)
            continue

        # Plot Punkte ohne Fehlerbalken
        for _, row in sub.iterrows():
            color  = GROUP_COLORS.get(row["group_type"], "gray")
            marker = NUMBER_MARKERS.get(row["group_num"], "o")

            ax.plot(
                row["var"], row["mean"],
                marker=marker,
                color=color,
                markersize=8,
                linestyle="None",
                alpha=0.85,
            )

        # ✅ Zeitlabel im gewünschten Format
        h = int(t)
        m = int(round((t - h) * 60))
        # 50 Minuten als 30 anzeigen
        if m == 50:
            m = 30
        ax.set_title(f"Start Time: {h:02d}:{m:02d}", fontsize=22)

        # Gemeinsame Achsen-Limits
        ax.set_xlim(x_lims)
        ax.set_ylim(y_lims)
        
        ax.grid(alpha=0.3)
        ax.tick_params(axis='both', labelsize=18)
        
        # Nur links und unten Achsen anzeigen
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        
        # Achsenlabel nur für äußere Subplots
        if idx % n_cols != 0:  # Nicht links
            ax.set_ylabel("")
            ax.set_yticklabels([])
        else:
            ax.set_ylabel("AvgEn [kWh]", fontsize=22)
            
        if idx < n_times - n_cols:  # Nicht unten
            ax.set_xlabel("")
            ax.set_xticklabels([])
        else:
            ax.set_xlabel("Var [kWh²]", fontsize=22)

    # Überschüssige Subplots ausblenden
    for idx in range(n_times, len(axes)):
        axes[idx].axis("off")

    # Gemeinsame Legende
    legend_color_handles = {
        gt: plt.Line2D([], [], color=color, marker="o", linestyle="None", label=GROUP_LABELS.get(gt, gt))
        for gt, color in GROUP_COLORS.items()
    }

    legend_marker_handles = {
        gn: plt.Line2D([], [], color="black",
                       marker=NUMBER_MARKERS.get(gn, "o"),
                       linestyle="None",
                       label=f"Group {gn}")
        for gn in sorted(df["group_num"].unique())
    }

    handles = (
        list(legend_color_handles.values()) +
        list(legend_marker_handles.values())
    )

    fig.legend(handles=handles, fontsize=20, loc="lower center", ncol=5, bbox_to_anchor=(0.5, 0.03))
    plt.tight_layout()
    plt.subplots_adjust(bottom=0.24, left=0.07, hspace=0.15)

    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "figures")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "model_groups_risk_Figure15.png")
    fig.savefig(out_path, dpi=300, bbox_inches="tight")
    print(f"Saved: {out_path}")

    plt.show()


def plot_selected_times_combined(df):

    target_times = {
        1 + 50/60,
        8.0,
        #11 + 50/60,
        13 + 50/60,
        16 + 50/60,
        18 + 50/60,
        20.0,
        22.0
    }

    def is_selected(t):
        return any(abs(t - tt) < 1e-3 for tt in target_times)

    df = df[df["time"].apply(is_selected)]

    fig, ax = plt.subplots(figsize=(8, 6))

    # 🎨 Farbe je Zeit
    time_values = sorted(target_times)
    time_colors = {
        t: plt.cm.tab10(i % 10)
        for i, t in enumerate(time_values)
    }

    # ---------- RECHTECKE JE ZEIT ----------
    # ---------- RECHTECKE JE ZEIT ----------
    for t in time_values:

        sub = df[df["time"].apply(lambda x: abs(x - t) < 1e-3)]
        if sub.empty:
            continue

        x_min = sub["var"].min()
        x_max = sub["var"].max()

        y_low = sub["mean"].min()
        y_high = sub["mean"].max()

        width = x_max - x_min
        height = y_high - y_low

        rect = Rectangle(
            (x_min, y_low),
            width,
            height,
            facecolor=time_colors[t],
            alpha=0.15,
            edgecolor=None
        )

        ax.add_patch(rect)

        # ✅ ---------- ZEITLABEL (NEU) ----------
        h = int(t)
        m = int(round((t - h) * 60))

        ax.text(
            x_min + width / 2,
            y_low,
            format_time_label(t),
            ha="center",
            va="top",
            fontsize=16,
            color=time_colors[t],
            alpha=0.9,
            weight="bold"
        )

    # ---------- PUNKTE ----------
    jitter_x = 0.01 * df["var"].std()
    jitter_y = 0.01 * df["mean"].std()

    for _, row in df.iterrows():

        color  = GROUP_COLORS.get(row["group_type"], "gray")
        marker = NUMBER_MARKERS.get(row["group_num"], "o")

        x = row["var"] + np.random.uniform(-jitter_x, jitter_x)
        y = row["mean"] + np.random.uniform(-jitter_y, jitter_y)

        ax.plot(
            x, y,
            marker=marker,
            color=color,
            markersize=8,
            linestyle="None",
            alpha=0.9,
        )

    # ---------- AXIS ----------
    ax.set_xlabel("Variance of Energy [kWh²]", fontsize = 16)
    ax.set_ylabel("Mean Energy [kWh]", fontsize =16)
    ax.grid(alpha=0.3)

    # ---------- LEGEND ----------

    legend_color = [
        plt.Line2D(
            [], [],
            color=color,
            marker="o",
            linestyle="None",
            label=GROUP_LABELS.get(gt, gt)
        )
        for gt, color in GROUP_COLORS.items()
    ]

    legend_marker = [
        plt.Line2D([], [], color="black",
                   marker=NUMBER_MARKERS.get(gn, "o"),
                   linestyle="None",
                   label=f"Group {gn}")
        for gn in sorted(df["group_num"].unique())
    ]

    legend_time = [
        plt.Line2D([], [], color=time_colors[t],
                   linewidth=6, alpha=0.3,
                   label=format_time_label(t))
        for t in time_values
    ]

    handles = legend_color + legend_marker + legend_time

    ax.legend(handles=handles, fontsize=14, loc="best", ncol = 2)
    ax.tick_params(axis='both', labelsize=20)
    plt.xlim(1400, 4000)
    plt.tight_layout()
    plt.show()





# ── Main ─────────────────────────────────────────────────────────

def main():

    files = find_jsons()
    print(f"Files found: {len(files)}")

    if not files:
        raise FileNotFoundError("No JSON files found!")

    rows = []
    for f in files:
        rows.extend(extract_data(f))

    df = pd.DataFrame(rows)

    if df.empty:
        raise ValueError("No matching data found!")

    print(df.head())
    plot_subplots(df)  # Subplot-Plot zuerst
    #plot_all_selected_times(df)
    #plot_selected_times_combined(df)
    #plot(df)



if __name__ == "__main__":
    main()