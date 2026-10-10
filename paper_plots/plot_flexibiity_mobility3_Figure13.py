import os
import json
import re
import pandas as pd
import matplotlib.pyplot as plt

BASE_DIR = "../scenarios_final"

STRAT_VALUES = [0, 1, 2]
MODUS_VALUES = [0, 1]
HEURISTIC = 1

TARGET_MODELS = [
    "homogroup_2",
    "mobilitygroup_3",
    #"mobilitygroup_4",
    "agegroup_1",
    "agegroup_3",
    "agegroup_4"
]

# spontTrue + placeHome + act0_00 + dur60
SCENARIO_PATTERN = r"spontTrue.*placeHome.*_act0_00.*_t\d+_00_dur60"

VALID_HOURS = {1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23}


# ---------- HELPER ----------

def extract_time(path):
    match = re.search(r"_t(\d+)_(\d+)", path)
    if match:
        h = int(match.group(1))
        m = int(match.group(2))
        return h + m / 60.0
    return None


def extract_model(path):
    match = re.search(r"model_pl_normal_([a-zA-Z0-9_]+)", path)
    if match:
        return match.group(1)
    return None


# ---------- FIND JSON ----------

def find_jsons():
    files = []

    for root, _, fs in os.walk(BASE_DIR):
        for f in fs:
            if not f.endswith(".json"):
                continue

            full = os.path.join(root, f)

            if not re.search(SCENARIO_PATTERN, full):
                continue

            model = extract_model(full)

            if model and model in TARGET_MODELS:
                files.append(full)

    return files


# ---------- EXTRACT ----------

def extract_data(json_path):
    results = []

    model = extract_model(json_path)
    time = extract_time(json_path)

    if model is None or time is None:
        return results

    with open(json_path) as f:
        data = json.load(f)

    for entry in data.get("risk_combinations", []):
        comb = entry.get("combination", {})

        if (
            comb.get("heuristic_pos") == HEURISTIC and
            comb.get("strat_pos") in STRAT_VALUES and
            comb.get("modus_pos") in MODUS_VALUES
        ):
            energy = entry.get("quantiles_energy_kwh", {})

            results.append({
                "model": model,
                "time": time,
                "strat": comb["strat_pos"],
                "modus": comb["modus_pos"],
                "mean": energy.get("mean"),
                "var": energy.get("var"),
                "iqr": energy.get("iqr")
            })

    return results


# ---------- MAIN ----------

def main():
    strat_names = {
        0: "ASAP",
        1: "ALaAP",
        2: "ALoAP"
    }

    modus_names = {
        0: "Negative Flexibility",
        1: "Positive Flexibility"
    }

    files = find_jsons()
    print(f"JSONs: {len(files)}")

    if not files:
        raise ValueError("❌ Keine Szenarien gefunden – Pattern prüfen!")

    rows = []

    for f in files:
        rows.extend(extract_data(f))

    df = pd.DataFrame(rows)

    if df.empty:
        raise ValueError("❌ Keine Daten gefunden")

    # keep only the defined valid hours
    df = df[df["time"].apply(lambda t: int(t) in VALID_HOURS)]

    if df.empty:
        raise ValueError("❌ Keine Daten nach valid_hours-Filter")

    df = df.groupby(["model", "time", "strat", "modus"], as_index=False).mean()
    df = df.sort_values("time")

    # ---------- GLOBALE SKALEN ----------

    def add_margin(min_val, max_val, factor=0.1):
        span = max_val - min_val
        return min_val - factor * span, max_val + factor * span

    mean_min, mean_max = add_margin(df["mean"].min(), df["mean"].max())
    var_min, var_max = add_margin(df["var"].min(), df["var"].max())
    iqr_min, iqr_max = add_margin(df["iqr"].min(), df["iqr"].max())

    # ---------- SUBPLOTS ----------
    fig, axes = plt.subplots(3, 2, figsize=(15, 18), sharex=True)

    fig.subplots_adjust(
        top=0.93,
        bottom=0.14,
        left=0.16,
        right=0.83,
        wspace=0.1,
        hspace=0.1
    )

    colors = plt.cm.tab10.colors

    for i, strat in enumerate(STRAT_VALUES):
        for j, modus in enumerate(MODUS_VALUES):

            ax1 = axes[i][j]
            ax2 = ax1.twinx()
            ax3 = ax1.twinx()

            ax3.spines["right"].set_position(("outward", 70))

            subset = df[
                (df["strat"] == strat) &
                (df["modus"] == modus)
                ]

            for k, (model, group) in enumerate(subset.groupby("model")):
                group = group.sort_values("time")

                color = colors[k % len(colors)]
                label = model.replace("_", " ")

                ax1.plot(
                    group["time"],
                    group["mean"],
                    color=color,
                    linewidth=2,
                    marker="o",
                    label=label
                )

                ax2.plot(
                    group["time"],
                    group["var"],
                    linestyle="--",
                    color=color
                )

                ax3.plot(
                    group["time"],
                    group["iqr"],
                    linestyle=":",
                    color=color
                )

            # ---------------- Y-Limits ----------------

            if  modus == 0:
                ax1.set_ylim(-10, 200)
                ax2.set_ylim(0, 2000)
                ax3.set_ylim(20, 100)
            else:
                ax1.set_ylim(100, 450)
                ax2.set_ylim(1000, 5000)
                ax3.set_ylim(0,70)






            # ---------------- Titel nur oben ----------------

            if i == 0:
                ax1.set_title(
                    modus_names[modus],
                    fontsize=24,
                    pad=20
                )

            # ---------------- Flexibility direction links ----------------

            if j == 0:
                ax1.text(
                    -0.25,
                    0.5,
                    f"Charging Strategy {strat_names[strat]}",
                    transform=ax1.transAxes,
                    rotation=90,
                    va="center",
                    ha="center",
                    fontsize=24

                )

            # ---------------- Tick-Größen ----------------

            ax1.tick_params(axis="y", labelsize=16)
            ax2.tick_params(axis="y", labelsize=16)
            ax3.tick_params(axis="y", labelsize=16)

            ax1.tick_params(axis="x", labelsize=16)

            # ---------------- AvgEn nur links außen ----------------

            if j == 0:
                ax1.set_ylabel("Average Energy (AvgEn)", fontsize=20)
            else:
                ax1.set_ylabel("")
                ax1.tick_params(labelleft=False)

            # ---------------- Var nur rechts außen ----------------

            if j == 1:
                ax2.set_ylabel("Var", fontsize=20)
            else:
                ax2.set_ylabel("")
                ax2.tick_params(labelright=False)
                ax2.spines["right"].set_visible(False)
                ax2.yaxis.set_visible(False)

            # ---------------- IQR nur rechts außen ----------------

            if j == 1:
                ax3.set_ylabel("IQR", fontsize=20)
            else:
                ax3.set_ylabel("")
                ax3.tick_params(labelright=False)
                ax3.spines["right"].set_visible(False)
                ax3.yaxis.set_visible(False)

            # ---------------- X-Achse nur unten ----------------

            if i < len(STRAT_VALUES) - 1:
                ax1.tick_params(labelbottom=False)

            ax1.grid(alpha=0.3)

    # ---------- Zeitformat ----------

    def format_time(t):
        h = int(t)
        m = int(round((t - h) * 60))
        return f"{h}:{m:02d}"

    times = sorted(df["time"].unique())

    for i, ax_row in enumerate(axes):
        for ax in ax_row:

            ax.set_xticks(times)

            if i == len(STRAT_VALUES) - 1:
                ax.set_xticklabels(
                    [format_time(t) for t in times],
                    rotation=45
                )
            else:
                ax.set_xticklabels([])

    # ---------- Legende ----------

    from matplotlib.lines import Line2D

    model_handles, model_labels = axes[0][0].get_legend_handles_labels()

    name_map = {
        "agegroup 1": "Age Group under40",
        "agegroup 3": "Age Group Over65",
        "homogroup 2": "Homogenous Group NotWorking",
        "mobilitygroup 3": "Mobility Group NonCarUsers",
        "agegroup 4": "All Attributes Unknown"
    }

    model_labels = [name_map.get(label, label) for label in model_labels]

    metric_handles = [
            Line2D([0], [0], color="black", lw=2,
                   linestyle="-", label="AvgEn"),
            Line2D([0], [0], color="black", lw=2,
                   linestyle="--", label="Var"),
            Line2D([0], [0], color="black", lw=2,
                   linestyle=":", label="IQR"),
        ]

    all_handles = model_handles + metric_handles

    all_labels = model_labels + ["AvgEn", "Var", "IQR"]

    fig.legend(
        all_handles,
        all_labels,
        loc="lower center",
        bbox_to_anchor=(0.5, 0.045),
        ncol=4,
        fontsize=15,
        frameon=True
    )

    fig.supxlabel(
        "Time",
        fontsize=16,
        y=0.10
    )

    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "figures")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "flexibility_mobility3_Figure13.png")
    fig.savefig(out_path, dpi=300, bbox_inches="tight")
    print(f"Saved: {out_path}")

    plt.show()


# ---------- RUN ----------
if __name__ == "__main__":
    main()