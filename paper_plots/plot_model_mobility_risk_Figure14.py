import os
import json
import re
import pandas as pd
import matplotlib.pyplot as plt

BASE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../scenarios_final")

TARGET_MODEL = "agegroup_4"
TARGET_TIME = 18 + 50 / 60.0
TIME_TOL = 1e-3

STRAT_VALUES = [0, 1, 2]
MODUS_VALUES = [0, 1]


# ---------- HELPER ----------

def extract_time(path):
    match = re.search(r"_t(\d+)_(\d+)", path)
    if match:
        h, m = int(match.group(1)), int(match.group(2))
        return h + m / 60.0
    return None


def extract_model(path):
    match = re.search(r"model_pl_normal_([a-zA-Z0-9_]+?)(?:[/\\]|$)", path)
    if match:
        return match.group(1)
    return None


def extract_act(path):
    match = re.search(r"_act(\d+)_(\d+)", path)
    if match:
        return int(match.group(1)) + int(match.group(2)) / 100

    # ✅ spontTrue → act = 0
    if "spontTrue" in path:
        return 0.0

    return None


def extract_dur(path):
    match = re.search(r"_dur(\d+)[_/\\]", path)
    if match:
        return int(match.group(1))
    return None


# ---------- FIND JSON ----------

def find_jsons():
    needle = f"model_pl_normal_{TARGET_MODEL}"
    files = []

    for root, _, fs in os.walk(BASE_DIR):
        for f in fs:
            if not f.endswith(".json"):
                continue

            full = os.path.join(root, f)

            if needle in full and ("spontFalse" in full or "spontTrue" in full):
                files.append(full)

    return files


# ---------- EXTRACT ----------

def extract_data(json_path):
    model = extract_model(json_path)
    time = extract_time(json_path)
    act = extract_act(json_path)
    dur = extract_dur(json_path)

    if model != TARGET_MODEL:
        return []

    if time is None or abs(time - TARGET_TIME) > TIME_TOL:
        return []

    results = []

    with open(json_path, encoding="utf-8") as fh:
        data = json.load(fh)

    for entry in data.get("risk_combinations", []):
        comb = entry.get("combination", {})

        if not (
            comb.get("strat_pos") in STRAT_VALUES
            and comb.get("modus_pos") in MODUS_VALUES
            and comb.get("heuristic_pos") == 1
        ):
            continue

        energy = entry.get("quantiles_energy_kwh", {})

        mean = energy.get("mean")
        var = energy.get("var")

        if mean is None or var is None:
            continue

        results.append({
            "strat": comb["strat_pos"],
            "modus": comb["modus_pos"],
            "act": act,
            "dur": dur,
            "mean": mean,
            "std": energy.get("std"),
            "var": var,
            "iqr": energy.get("iqr"),
            "spont": "True" if "spontTrue" in json_path else "False"
        })

    return results


# ---------- PLOT ----------

def plot(df):
    strat_names = {
        0: "ASAP",
        1: "ALaAP",
        2: "ALoAP"
    }
    import numpy as np
    import matplotlib.pyplot as plt

    # Filter: nur 0%, 50%, 100% Aktivierungszeiten
    df["act_percent"] = df["act"].apply(lambda x: int(round(x * 100)))
    df = df[df["act_percent"].isin([0, 50, 100])]

    fig, ax = plt.subplots(figsize=(10, 7))

    # ---------- COLORS: act_time ----------
    unique_acts = sorted(df["act"].dropna().unique())
    cmap = plt.cm.viridis

    act_colors = {
        act: cmap(i / max(len(unique_acts) - 1, 1))
        for i, act in enumerate(unique_acts)
    }

    # ---------- MARKERS ----------
    COMBO_MARKERS = {
        (0, 0): "o",
        (0, 1): "s",
        (1, 0): "D",
        (1, 1): "^",
        (2, 0): "v",
        (2, 1): "P",
    }

    legend_strategy = {}
    legend_duration = {}
    legend_act = {}

    # ---------- JITTER ----------
    jitter_x = 0.02 * df["var"].std()
    jitter_y = 0.02 * df["mean"].std()

    # ---------- PLOT ----------
    for _, row in df.iterrows():

        strat = int(row["strat"])
        modus = int(row["modus"])
        combo = (strat, modus)

        marker = COMBO_MARKERS.get(combo, "x")
        color = act_colors[row["act"]]

        # jitter gegen Überlagerung
        x = row["var"] + np.random.uniform(-jitter_x, jitter_x)
        y = row["mean"] + np.random.uniform(-jitter_y, jitter_y)

        # ✅ nur vertikale Fehlerbalken (std)
        yerr = [[row["std"]], [row["std"]]] if row["std"] else [[0], [0]]

        # ✅ duration → Rahmen
        if row["dur"] == 60:
            edgecolor = "black"
            linewidth_edge = 1.5
        else:
            edgecolor = "none"
            linewidth_edge = 0

        ax.errorbar(
            x, y,
            yerr=yerr,
            fmt=marker,
            markerfacecolor=color,
            markeredgecolor=edgecolor,
            markeredgewidth=linewidth_edge,
            color=color,
            markersize=9,
            ecolor=color,
            elinewidth=1,
            capsize=4,   # ✅ immer sichtbar
            alpha=0.85,
        )

        # ---------- Legend: Strategy ----------
        direction = "Positive" if modus == 1 else "Negative"

        strat_label = strat_names.get(strat, strat)

        strat_key = (
            f"Ch.: {strat_label}, "
            f"Flex. Direction: {direction}"
        )
        if strat_key not in legend_strategy:
            legend_strategy[strat_key] = plt.Line2D(
                [], [], color="black",
                marker=marker,
                linestyle="None",
                markersize=8,
                label=strat_key
            )
        # ---------- LEGEND: std Erklärung ----------
        std_handle = plt.Line2D(
                [], [],
                color="black",
                marker="|",
                linestyle="None",
                markersize=12,
                label="Vertical bars: ± standard deviation"
            )

        # ---------- Legend: Duration ----------
        dur_key = f"Duration: {int(row['dur'])} min"

        if dur_key not in legend_duration:
            if row["dur"] == 60:
                legend_duration[dur_key] = plt.Line2D(
                    [], [], color="black",
                    marker="o",
                    markerfacecolor="white",
                    markeredgecolor="black",
                    markeredgewidth=1.5,
                    linestyle="None",
                    markersize=8,

                    label=dur_key
                )
            else:
                legend_duration[dur_key] = plt.Line2D(
                    [], [], color="black",
                    marker="o",
                    markerfacecolor="black",
                    linestyle="None",
                    markersize=8,
                    label=dur_key
                )

        # ---------- Legend: Activation Time ----------
        act_percent = row["act_percent"]
        
        if act_percent in [0, 50, 100]:
            act_key = f"Activation Time/ Flex. Duration: {act_percent} %"

            if act_key not in legend_act:
                legend_act[act_key] = plt.Line2D(
                    [], [], color=act_colors[row["act"]],
                    marker="o",
                    linestyle="None",
                    markersize=8,
                    label=act_key
                )

    # ---------- ORIGIN ----------
    ax.axhline(0, color="black", linewidth=1)
    ax.axvline(0, color="black", linewidth=1)

    # ---------- REFERENCE LINE ----------
    if len(df) > 1:
        slope = df["mean"].mean() / (df["var"].mean() + 1e-9)
        x_vals = sorted(df["var"])
        y_vals = [slope * x for x in x_vals]

        ax.plot(x_vals, y_vals, "--", color="gray", linewidth=1.5)

    # ---------- AXES ----------
    ax.set_xlabel("Variance of Energy (Var) [kWh²]", fontsize = 20)
    ax.set_ylabel("Average Energy (AvgEn) [kWh]", fontsize = 20)
    ax.grid(alpha=0.3)
    ax.tick_params(axis='both', labelsize=18)


    handles = (
        list(legend_strategy.values()) + [std_handle] +
        list(legend_duration.values()) +
        list(legend_act.values())

    )

    ax.legend(
        handles=handles,
        fontsize=14,
        loc="upper center",
        bbox_to_anchor=(0.455, -0.15),
        ncol=2
    )

    plt.tight_layout()
    plt.savefig("figures/risk_vs_energy_Figure14.png", dpi=300, bbox_inches="tight")
    plt.show()


if False:
    def plot(df):
        import numpy as np
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(figsize=(10, 7))

        # ---------- GROUP SPLIT ----------
        def split_group(model_name):
            parts = model_name.split("_")
            return "_".join(parts[:-1]), int(parts[-1])

        df["group_type"], df["group_id"] = zip(*df["model"].apply(split_group))

        # ---------- COLOR: group type ----------
        unique_groups = sorted(df["group_type"].unique())
        cmap = plt.cm.tab10

        group_colors = {
            g: cmap(i / max(len(unique_groups) - 1, 1))
            for i, g in enumerate(unique_groups)
        }

        # ---------- MARKERS: group id ----------
        MARKERS = ["o", "s", "D", "^", "v", "P", "X"]

        group_markers = {
            i + 1: MARKERS[i % len(MARKERS)]
            for i in sorted(df["group_id"].unique())
        }

        legend_groups = {}
        legend_ids = {}

        # ---------- JITTER ----------
        jitter_x = 0.02 * df["var"].std()
        jitter_y = 0.02 * df["mean"].std()

        # ---------- PLOT ----------
        for _, row in df.iterrows():

            group_type = row["group_type"]
            group_id = row["group_id"]

            color = group_colors[group_type]
            marker = group_markers[group_id]

            # jitter
            x = row["var"] + np.random.uniform(-jitter_x, jitter_x)
            y = row["mean"] + np.random.uniform(-jitter_y, jitter_y)

            # std → Fehlerbalken
            min_err = 1e-6
            std_val = row["std"] if row["std"] and row["std"] > 0 else min_err

            yerr = [[std_val], [std_val]]

            ax.errorbar(
                x, y,
                yerr=yerr,
                fmt=marker,
                markerfacecolor=color,
                markeredgecolor="black",
                markeredgewidth=1,
                color=color,
                markersize=9,
                ecolor=color,
                capsize=4,
                alpha=0.85,
            )

            # ---------- Legend: group type ----------
            if group_type not in legend_groups:
                legend_groups[group_type] = plt.Line2D(
                    [], [], color=group_colors[group_type],
                    marker="o",
                    linestyle="None",
                    markersize=8,
                    label=group_type
                )

            # ---------- Legend: group id ----------
            id_key = f"id {group_id}"
            if id_key not in legend_ids:
                legend_ids[id_key] = plt.Line2D(
                    [], [], color="black",
                    marker=group_markers[group_id],
                    linestyle="None",
                    markersize=8,
                    label=id_key
                )

        # ---------- ORIGIN ----------
        ax.axhline(0, color="black", linewidth=1)
        ax.axvline(0, color="black", linewidth=1)

        # ---------- REFERENCE LINE ----------
        if len(df) > 1:
            slope = df["mean"].mean() / (df["var"].mean() + 1e-9)
            x_vals = sorted(df["var"])
            y_vals = [slope * x for x in x_vals]
            ax.plot(x_vals, y_vals, "--", color="gray", linewidth=1.5)

        # ---------- AXES ----------
        ax.set_xlabel("Variance of Energy [kWh²]")
        ax.set_ylabel("Mean Energy [kWh]")
        ax.grid(alpha=0.3)

        # ---------- LEGEND ----------
        std_handle = plt.Line2D(
            [], [], color="black", marker="|",
            linestyle="None", markersize=12,
            label="vertical bars: ± std"
        )

        handles = (
            list(legend_groups.values()) +
            list(legend_ids.values()) +
            [std_handle]
        )

        ax.legend(handles=handles, fontsize=8, loc="best")

        plt.tight_layout()
        plt.show()



# ---------- MAIN ----------

def main():
    files = find_jsons()
    print(f"Files found: {len(files)}")

    if not files:
        raise FileNotFoundError("❌ No matching JSON files found")

    rows = []
    for f in files:
        rows.extend(extract_data(f))

    df = pd.DataFrame(rows)

    if df.empty:
        raise ValueError("❌ No matching data for selected time")

    print(df.to_string(index=False))
    plot(df)


if __name__ == "__main__":
    main()