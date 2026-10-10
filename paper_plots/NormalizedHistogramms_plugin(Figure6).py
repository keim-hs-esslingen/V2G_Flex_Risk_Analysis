import argparse
import json
import os
from pathlib import Path
import sys

import matplotlib.pyplot as plt
import numpy as np

# Ensure project root is on sys.path so package imports work when running this script
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from analysis_methods.load_data import open_file
from analysis_methods.plot_Charging import compute_histogram_lists
from analysis_methods.Charging_statistic import change_to_seconds
from SimulationTool.simulation import settingsContainer

# Construct correct paths from project root
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
SAVE_ROOT = os.path.join(PROJECT_ROOT, "plugin")
DATA_ROOT = os.path.join(PROJECT_ROOT, "dataCharging", "alreadyLoaded")
CH_MODUS = "home"
BINS = 24

MODI = [
    ("start_time", False),
    ("ch_end_time", False),
    ("ch_duration", False),
    ("plugin_end_time", False),
    ("plugin_duration", True),
    ("energy_per_session", False),
]

POS_MAPPING = {
    "start_time": 1,
    "ch_end_time": 3,
    "ch_duration": 5,
    "plugin_end_time": 6,
    "plugin_duration": 8,
    "energy_per_session": 11,
}

X_LABELS = {
    "start_time": "Hour of day [h]",
    "ch_end_time": "Hour of day [h]",
    "ch_duration": "Duration [h]",
    "plugin_end_time": "Hour of day [h]",
    "plugin_duration": "Duration [h]",
    "energy_per_session": "Energy per session [kWh]",
}

TITLES = {
    "start_time": "Start time",
    "ch_end_time": "Charging end time",
    "ch_duration": "Charging duration",
    "plugin_end_time": "Plugin end time",
    "plugin_duration": "Plugin duration",
    "energy_per_session": "Energy per session",
}


def load_real_data(modus: str, ch_modus: str):
    if ch_modus == "home":
        file_start = "UK_Charging_"
    elif ch_modus == "work":
        file_start = "lama_"
    else:
        file_start = "UK_Charging_"

    filename = os.path.join(DATA_ROOT, f"{file_start}{ch_modus}_{modus}s")
    data = open_file(filename)

    if modus in ["energy_per_session"]:
        return np.asarray(data, dtype=float)

    return np.asarray(change_to_seconds(data), dtype=float)


def get_bins(modus: str, bins: int, plug_in_duration: bool):
    if modus == "energy_per_session":
        return np.asarray([i * 4 for i in range(0, bins)], dtype=float)

    if plug_in_duration:
        return np.asarray([i * 10000 for i in range(0, bins)], dtype=float)

    return np.asarray([(24 / (bins - 1)) * i * 3600 for i in range(0, bins)], dtype=float)


def normalized_hist(data: np.ndarray, bins: np.ndarray):
    hist, edges = np.histogram(data, bins=bins)
    total = np.sum(hist)
    if total == 0:
        return np.zeros_like(hist, dtype=float), edges
    return hist / total, edges


def to_x_hours(edges: np.ndarray):
    return edges[1:] / 3600.0


def to_x_raw(edges: np.ndarray):
    return edges[1:]


def collect_scenario_errors(save_root: str):
    all_errors = {}

    for scenario in os.listdir(save_root):
        scenario_dir = os.path.join(save_root, scenario)
        if not os.path.isdir(scenario_dir):
            continue

        error_file = os.path.join(scenario_dir, "histogram_errors.json")
        if not os.path.exists(error_file):
            continue

        with open(error_file, "r", encoding="utf-8") as f:
            all_errors[scenario] = json.load(f)

    if all_errors:
        return all_errors

    aggregate_file = os.path.join(save_root, "histogram_errors.json")
    if os.path.exists(aggregate_file):
        with open(aggregate_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            for scenario, scenario_errors in data.items():
                if isinstance(scenario_errors, dict):
                    all_errors[scenario] = scenario_errors

    return all_errors


def compute_avg_rmse(scenario_errors: dict):
    values = []
    for value in scenario_errors.values():
        rmse = value.get("RMSE") if isinstance(value, dict) else None
        if rmse is not None:
            values.append(float(rmse))
    if not values:
        return None
    return float(np.mean(values))


def pick_best_scenario(save_root: str):
    all_errors = collect_scenario_errors(save_root)
    if not all_errors:
        raise FileNotFoundError(
            "Keine histogram_errors.json gefunden. Bitte zuerst plug-in_analysis.py laufen lassen."
        )

    scored = []
    for scenario, errors in all_errors.items():
        avg_rmse = compute_avg_rmse(errors)
        if avg_rmse is not None:
            scored.append((scenario, avg_rmse))

    if not scored:
        raise RuntimeError("Es konnten keine gueltigen RMSE-Werte fuer Szenarien gefunden werden.")

    scored.sort(key=lambda x: x[1])
    return scored[0][0], scored[0][1]


def create_hist_plot_for_scenario(scenario: str, save_root: str, ch_modus: str, bins: int):
    scenario_dir = os.path.join(save_root, scenario)
    if not os.path.isdir(scenario_dir):
        raise FileNotFoundError(f"Szenario-Ordner nicht gefunden: {scenario_dir}")

    vehicle_file = os.path.join(scenario_dir, f"VehicleList_{scenario}")
    if not os.path.exists(f"{vehicle_file}.pkl"):
        raise FileNotFoundError(f"VehicleList-Datei fehlt: {vehicle_file}.pkl")

    vehicle_list = open_file(vehicle_file)

    all_lists = compute_histogram_lists(
        vehicle_list,
        start_day=settingsContainer.getStartDay(),
        ch_modus=ch_modus,
    )

    fig, axes = plt.subplots(2, 3, figsize=(17, 9))
    axes = axes.flatten()
    
    # Add vertical space between plot rows
    fig.subplots_adjust(hspace=0.6)

    for idx, (modus, plug_flag) in enumerate(MODI):
        ax = axes[idx]

        pos = POS_MAPPING[modus]
        data_model = np.asarray(all_lists[pos], dtype=float)
        data_real = load_real_data(modus, ch_modus)

        bin_edges = get_bins(modus, bins=bins, plug_in_duration=plug_flag)

        model_hist, edges = normalized_hist(data_model, bin_edges)
        real_hist, _ = normalized_hist(data_real, bin_edges)

        if modus in ["energy_per_session"]:
            x_values = to_x_raw(edges)
        else:
            x_values = to_x_hours(edges)

        ax.plot(x_values, model_hist, linewidth=2.0, label="Model")
        ax.plot(x_values, real_hist, linewidth=2.0, label="Real")

        ax.set_title(TITLES[modus], fontsize = 32)
        ax.set_xlabel(X_LABELS[modus], fontsize = 28)
        ax.grid(alpha=0.25)

        # Tick-Größen
        ax.tick_params(axis='x', labelsize=26)
        ax.tick_params(axis='y', labelsize=26)

    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(
        handles,
        labels,
        loc="lower center",
        bbox_to_anchor=(0.5, -0.13),
        ncol=2,
        frameon=False,
        fontsize = 32
    )
    # Use subplots_adjust for full control instead of tight_layout
    fig.subplots_adjust(left=0.06, right=0.95, top=0.90, bottom=0.08, hspace=0.65, wspace=0.3)
    fig.supylabel("Share on total sessions", x=-0.03, fontsize = 32)

    out_file = os.path.join(scenario_dir, f"hist_{scenario}_comparison.png")
    fig.savefig(out_file, dpi=300, bbox_inches="tight")
    fig.savefig(f"figures/hist_{scenario}_comparison_Figure6.png", dpi=300, bbox_inches="tight")
    plt.close(fig)

    return out_file


def parse_args():
    parser = argparse.ArgumentParser(
        description="Plotte Histogrammvergleich fuer ein Szenario (default: bestes Szenario nach Avg RMSE)."
    )
    parser.add_argument(
        "--scenario",
        default=None,
        help="Szenarioname. Wenn nicht gesetzt, wird das beste Szenario automatisch gewaehlt.",
    )
    parser.add_argument("--save-root", default=SAVE_ROOT, help="Root-Ordner mit Szenario-Unterordnern")
    parser.add_argument("--ch-modus", default=CH_MODUS, help="Lademodus fuer den Vergleich, z.B. home/work")
    parser.add_argument("--bins", type=int, default=BINS, help="Anzahl Bins wie in plug-in_analysis")
    return parser.parse_args()


def main():
    args = parse_args()

    scenario = args.scenario
    if scenario is None:
        scenario, avg_rmse = pick_best_scenario(args.save_root)
        print(f"Bestes Szenario (Avg RMSE): {scenario} ({avg_rmse:.6f})")

    out_file = create_hist_plot_for_scenario(
        scenario=scenario,
        save_root=args.save_root,
        ch_modus=args.ch_modus,
        bins=args.bins,
    )

    print(f"Histogrammvergleich gespeichert: {out_file}")


if __name__ == "__main__":
    main()
