import os
import json
import re
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

BASE_DIR = str(Path(__file__).parent.parent / "scenarios_final")

# ✅ Kombinationen definieren
STRAT_VALUES = [0, 1, 2]
MODUS_VALUES = [0, 1]
HEURISTIC = 1

# Szenario-Pattern (tolerant of the folder separator between the outer
# "model_pl_normal_<x>" folder and the inner scenario folder/file name)
WORK_PATTERN = r"model_pl_normal_workagegroup_4[/\\].*spontTrue_placeWork_act0_00_t\d+_\d+_dur60"
HOME_PATTERN = r"model_pl_normal_agegroup_4[/\\].*spontTrue_placeHome_act0_00_t\d+_\d+_dur60"


# ---------- Helper ----------

def extract_time(path):
    match = re.search(r"_t(\d+)_(\d+)", path)
    if match:
        h = int(match.group(1))
        m = int(match.group(2))
        return h + m / 100
    return None


def extract_place(path):
    if "pl_normal_work" in path:
        return "work"
    if "placeHome" in path:
        return "home"
    return None


# ---------- JSON finden ----------

def find_jsons():
    files = []

    for root, _, fs in os.walk(BASE_DIR):
        for f in fs:
            if not f.endswith(".json"):
                continue

            full = os.path.join(root, f)

            if re.search(WORK_PATTERN, full) or re.search(HOME_PATTERN, full):
                files.append(full)

    return files


# ---------- Daten extrahieren ----------

def extract_data(json_path):
    place = extract_place(json_path)
    time = extract_time(json_path)

    with open(json_path) as f:
        data = json.load(f)

    results = []

    for entry in data.get("risk_combinations", []):
        comb = entry.get("combination", {})

        # ✅ Filter Kombination
        if (
            comb.get("heuristic_pos") == HEURISTIC
            and comb.get("strat_pos") in STRAT_VALUES
            and comb.get("modus_pos") in MODUS_VALUES
        ):
            energy = entry.get("quantiles_energy_kwh", {})

            results.append({
                "place": place,
                "time": time,
                "strat": comb["strat_pos"],
                "modus": comb["modus_pos"],
                "mean": energy.get("mean"),
                "q25": energy.get("q25"),
                "q75": energy.get("q75")
            })

    return results


# ---------- Daten sammeln ----------

rows = []

for file in find_jsons():
    extracted = extract_data(file)
    rows.extend(extracted)

df = pd.DataFrame(rows)

# Mittelwert falls mehrfach vorhanden
df = df.groupby(
    ["place", "time", "strat", "modus"],
    as_index=False
).mean()


# ---------- Plot ----------

fig, axes = plt.subplots(1, 2, figsize=(12, 5), sharey=True)

plt.rcParams.update({
    'font.size': 20,
    'axes.titlesize': 20,
    'axes.labelsize': 18,
    'xtick.labelsize': 20,
    'ytick.labelsize': 20,
    'legend.fontsize': 20,
    'figure.titlesize': 20,
})

places = ["home", "work"]

# Farbpalette
colors = plt.cm.tab10.colors

for ax, place in zip(axes, places):

    subset_place = df[df["place"] == place]

    for i, (strat, modus) in enumerate(
        [(s, m) for s in STRAT_VALUES for m in MODUS_VALUES]
    ):
        sub = subset_place[
            (subset_place["strat"] == strat) &
            (subset_place["modus"] == modus)
        ].sort_values("time")

        if sub.empty:
            continue

        color = colors[i % len(colors)]

        strat_labels = {
            0: "ASAP",#"As soon as possible",
            1: "ALaAP",#"As late as possible",
            2: "ALoAP"#As long as possible"
        }

        modus_labels = {
            0: "Negative",
            1: "Positive"
        }

        label = f"Charging Strategy: {strat_labels[strat]}\n Flexibility Direction: {modus_labels[modus]}"

        # ✅ Linie
        ax.plot(
            sub["time"],
            sub["mean"],
            color=color,
            linewidth=2,
            label=label
        )

        # ✅ Unsicherheitsbereich
        ax.fill_between(
            sub["time"],
            sub["q25"],
            sub["q75"],
            color=color,
            alpha=0.2
        )

    ax.set_xlim(0, 24)
    ax.set_xticks(range(0, 24, 8))
    ax.grid(alpha=0.3)
    #ax.set_xlabel("Time", fontsize = 20)

    ax.set_title(f"Charging Location: {place.capitalize()}", fontsize = 20)  # falls du GAR KEINEN Titel willst → einfach entfernen

axes[0].set_ylabel("AvgEn (kWh)", fontsize = 20)

# ---------- Zeitformat ----------

def format_time(t):
    h = int(t)
    m = int(round((t - h) * 60))
    return f"{h}:{m:02d}"

all_times = sorted(df["time"].unique())

for ax in axes:
    ax.set_xticks(all_times[::3])
    ax.set_xticklabels(
        [format_time(t) for t in all_times[::3]],
        rotation=45,
        fontsize = 16
    )
    ax.tick_params(axis='y', labelsize=16)
# ---------- Legende ----------

handles, labels = axes[1].get_legend_handles_labels()

fig.legend(
    handles,
    labels,
    loc="lower center",
    ncol=3,
    fontsize = 16,
    bbox_to_anchor=(0.5, -0.2)

)

plt.tight_layout(rect=(0, 0, 1, 0.9))


plt.savefig("figures/mobility_influences_plot_Figure8.png", dpi=600, bbox_inches="tight")

