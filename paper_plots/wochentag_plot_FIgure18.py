import json
import os
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np

# Change to parent directory (project root) so that paths work correctly
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Basisordner deiner Szenarien
BASE_DIR = Path("scenarios_final/pl_model_daytime_daytype_analysis")

# Alle Modellgruppen
MODEL_GROUPS = [
    "agegroup_4",
    "agegroup_1",
    "econstatus_1",
    "econstatus_5",
    "regiontype_5",
    "mobilitygroup_3",
    "mobilitygroup_1",
    "homogroup_2",
    "homogroup_1",
    "agegroup_3",

]


GROUP_LABELS = {
    "agegroup_4": "All Attributes Unknown",
    "agegroup_1": "Age Group Under40",
    "econstatus_1": "Economic Status VeryLow",
    "econstatus_5": "Economic Status VeryHigh",
    "regiontype_5": "Region Type RuralCentralCity",
    "mobilitygroup_3": "Mobility Group NonCarUser",
    "mobilitygroup_1": "Mobility Group CarUser",
    "homogroup_2": "Homogeneous Group NotWorking",
    "homogroup_1": "Homogeneous Group Working",
    "agegroup_3": "Age Group Over65",
}



# Farben für verschiedene Modellgruppen
COLORS = [
    '#1f77b4',  # blau
    '#ff7f0e',  # orange
    '#2ca02c',  # grün
    '#d62728',  # rot
    '#9467bd',  # lila
    '#8c564b',  # braun
    '#e377c2',  # pink
    '#7f7f7f',  # grau
    '#bcbd22',  # oliv
    '#17becf',  # türkis
    '#00cc96'   # zusätzliches türkis-grün
]
START_TIMES = [1,4,7,10,13,16,19,22]
DAYTYPES = [1, 2, 3, 4, 5, 6, 7]


# Labels schöner machen
def format_time(t):
    h = int(t)
    m = int((t - h) * 60)
    return f"{h:02d}:{m:02d}"


def daytype_name(d):
    names = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    return names[d - 1]


# Daten sammeln für jede Modellgruppe
fig, ax = plt.subplots(figsize=(16, 9))

x_labels = []
time_labels = []

# Nur einmal die x-labels generieren
for day in DAYTYPES:
    for t in START_TIMES:
        label = f"{daytype_name(day)}\n{format_time(t)}"
        x_labels.append(label)
        time_labels.append(format_time(t))

x = list(range(len(x_labels)))

# Plot für jede Modellgruppe
for group_idx, model_group in enumerate(MODEL_GROUPS):
    y_values = []
    
    print(f"\nProcessing {model_group}...")
    print(f"  BASE_DIR: {BASE_DIR}")
    print(f"  BASE_DIR exists: {BASE_DIR.exists()}")
    
    for day_idx, day in enumerate(DAYTYPES):
        for time_idx, t in enumerate(START_TIMES):
            scenario_name = f"pl_{model_group}_daytype{day}_{daytype_name(day).lower()}_starttime{t:.1f}h".replace(".", "_")

            json_path = BASE_DIR / scenario_name / f"{scenario_name}_kpis"
            
            # Debug: Nur beim ersten Versuch ausgeben
            if day_idx == 0 and time_idx == 0:
                print(f"  First scenario path: {json_path}")
            
            # Versuche mit und ohne .json Erweiterung
            json_file = None
            if json_path.with_suffix('.json').exists():
                json_file = json_path.with_suffix('.json')
            elif json_path.exists():
                # Versuche ohne Erweiterung
                json_file = json_path
            
            if json_file is None:
                print(f"Missing: {json_path}")
                y_values.append(None)
                continue

            try:
                with open(json_file) as f:
                    data = json.load(f)

                # richtige Kombination suchen
                found = False
                for comb in data["risk_combinations"]:
                    c = comb["combination"]
                    if c["strat_pos"] == 1 and c["heuristic_pos"] == 1 and c["modus_pos"] == 1:
                        mean_energy = comb["quantiles_energy_kwh"]["mean"]
                        y_values.append(mean_energy)
                        found = True
                        break

                if not found:
                    print(f"No matching combination in {json_file}")
                    y_values.append(None)
                    
            except Exception as e:
                print(f"Error reading {json_file}: {e}")
                y_values.append(None)
    
    # Plot für diese Modellgruppe
    print(f"  y_values: {len([y for y in y_values if y is not None])} / {len(y_values)} values found")
    ax.plot(x, y_values, marker="o", linewidth=2, label=model_group, color=COLORS[group_idx], alpha=0.7)

# X-Ticks = nur Uhrzeiten (nur jeden zweiten Tick beschriften)
ax.set_xticks(x)
sparse_labels = [label if i % 2 == 0 else "" for i, label in enumerate(time_labels)]
ax.set_xticklabels(sparse_labels, rotation=45)

n_times = len(START_TIMES)

# Wochentage als Gruppenbeschriftung
for i, day in enumerate(DAYTYPES):
    start = i * n_times
    end = start + n_times - 1
    center = (start + end) / 2

    # Hintergrund leicht einfärben (abwechselnd)
    if i % 2 == 0:
        ax.axvspan(start - 0.5, end + 0.5, alpha=0.06, color="gray")

    # vertikale Linie zur Trennung
    ax.axvline(start - 0.5, color="black", linewidth=0.5, alpha=0.3)

    # Wochentag
    ax.text(
        center,
        ax.get_ylim()[1] * 1.03,
        daytype_name(day).capitalize(),
        ha="center",
        va="top",
        fontsize=22,
        #fontweight="bold",
        transform=ax.transData
    )

# letzte Trennlinie rechts
ax.axvline(len(x) - 0.5, color="black", linewidth=0.5, alpha=0.3)

ax.set_ylabel("AvgEn in kWh", fontsize = 22)
ax.set_xlabel("Time", fontsize = 22)
#ax.set_yticks([-100, -50, 0, 50, 100])
#ax.set_title("Flexibility Mean Energy over Week (Home) - All Model Groups")
ax.grid(alpha=0.3)
handles, labels = ax.get_legend_handles_labels()

new_labels = [GROUP_LABELS.get(label, label) for label in labels]


ax.legend(
    handles,
    new_labels,
    loc="upper center",
    bbox_to_anchor=(0.5, -0.2),
    ncol=3,
    fontsize=18,
    frameon = True)

ax.tick_params(axis='x', labelsize=18)
ax.tick_params(axis='y', labelsize=18)



plt.tight_layout()
plt.savefig("paper_plots/figures/weekday_plot_Figure18.png", dpi=300, bbox_inches="tight")