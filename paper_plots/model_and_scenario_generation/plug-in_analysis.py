import os
import json
import numpy as np

from analysis_methods.load_data import *
from analysis_methods.plot_Charging import *
from SimulationTool.simulation import *

# --------------------------------------------------
# EINSTELLUNGEN
# --------------------------------------------------

SAVE_ROOT = "plugin/"
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

# --------------------------------------------------
# HISTOGRAMM FEHLER BERECHNUNG
# --------------------------------------------------

def compute_histogram_error(data_model,
                            data_real,
                            bins=24,
                            plug_in_duration=False,
                            time_adaption=True):

    if time_adaption:
        if plug_in_duration:
            bins_list = [i * 10000 for i in range(0, bins)]
        else:
            bins_list = [(24/(bins-1))*i*3600 for i in range(0, bins)]
    else:
        bins_list = [i * 4 for i in range(0, bins)]

    hist_model, _ = np.histogram(data_model, bins_list)
    hist_real, _ = np.histogram(data_real, bins_list)

    if np.sum(hist_model) == 0 or np.sum(hist_real) == 0:
        return {"L1": None, "RMSE": None, "MAX": None}

    hist_model = hist_model / np.sum(hist_model)
    hist_real = hist_real / np.sum(hist_real)

    diff = hist_model - hist_real

    l1 = np.sum(np.abs(diff))
    rmse = np.sqrt(np.mean(diff**2))
    max_err = np.max(np.abs(diff))

    return {
        "L1": float(l1),
        "RMSE": float(rmse),
        "MAX": float(max_err)
    }


# --------------------------------------------------
# REALE DATEN LADEN
# --------------------------------------------------

def load_real_data(modus, ch_modus):

    if ch_modus == "home":
        file_start = "UK_Charging_"
    elif ch_modus == "work":
        file_start = "lama_"
    else:
        file_start = "UK_Charging_"

    filename = f"dataCharging/alreadyLoaded/{file_start}{ch_modus}_{modus}s"
    data = open_file(filename)

    if modus in ["energy_per_session"]:
        return data
    else:
        return change_to_seconds(data)


# --------------------------------------------------
# MODELL DATEN INDEX
# --------------------------------------------------

def get_position(modus):

    mapping = {
        "start_time": 1,
        "ch_end_time": 3,
        "ch_duration": 5,
        "plugin_end_time": 6,
        "plugin_duration": 8,
        "energy_per_session": 11,
    }

    return mapping[modus]


# --------------------------------------------------
# HAUPTFUNKTION
# --------------------------------------------------

def evaluate_all_scenarios():

    results = {}

    for scenario in os.listdir(SAVE_ROOT):

        if not scenario.startswith("D4"):# and not scenario.startswith("B4_SOC_AFTER30_SOC_PLUG20") and not scenario.startswith("B4_SOC_AFTER30_SOC_PLUG30"):
           continue

        scenario_dir = os.path.join(SAVE_ROOT, scenario)

        if not os.path.isdir(scenario_dir):
            continue

        vehicle_file = os.path.join(
            scenario_dir,
            f"VehicleList_{scenario}",

        )

        if not os.path.exists(f"{vehicle_file}.pkl"):
            continue

        print(f"Evaluating scenario: {scenario}")

        VehicleList = open_file(vehicle_file)

        allLists = compute_histogram_lists(
            VehicleList,
            start_day=settingsContainer.getStartDay(),
            ch_modus=CH_MODUS
        )

        scenario_errors = {}

        for modus, plug_flag in MODI:

            print(f"   -> {modus}")

            pos = get_position(modus)

            data_model = allLists[pos]
            data_real = load_real_data(modus, CH_MODUS)

            if modus not in ["energy_per_session"]:
                data_model = np.array(data_model)

            error = compute_histogram_error(
                data_model,
                data_real,
                bins=BINS,
                plug_in_duration=plug_flag
            )

            scenario_errors[modus] = error

        results[scenario] = scenario_errors

        # Speichern im jeweiligen Szenario-Ordner
        output_file = os.path.join(scenario_dir, "histogram_errors.json")

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(scenario_errors, f, indent=4)

        print(f"   Fehler gespeichert unter: {output_file}")

    # Speichern
    output_file = os.path.join(SAVE_ROOT, "histogram_errors.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4)

    print("\nAlle Fehler gespeichert unter:")
    print(output_file)

    # Ranking nach plugin_duration RMSE
    ranking = sorted(
        results.items(),
        key=lambda x: x[1]["plugin_duration"]["RMSE"]
            if x[1]["plugin_duration"]["RMSE"] is not None
            else 999
    )

    print("\nRanking nach plugin_duration RMSE:\n")
    for i, (scenario, values) in enumerate(ranking):
        rmse = values["plugin_duration"]["RMSE"]
        print(f"{i+1}. {scenario} -> RMSE = {rmse}")


def compute_average_ranking_from_files(save_root):

    ranking_l1 = []
    ranking_rmse = []

    for scenario in os.listdir(save_root):

        scenario_dir = os.path.join(save_root, scenario)

        if not os.path.isdir(scenario_dir):
            continue

        error_file = os.path.join(scenario_dir, "histogram_errors.json")

        if not os.path.exists(error_file):
            continue

        with open(error_file, "r", encoding="utf-8") as f:
            errors = json.load(f)

        l1_values = []
        rmse_values = []

        for modus in errors.values():

            if modus["L1"] is not None:
                l1_values.append(modus["L1"])

            if modus["RMSE"] is not None:
                rmse_values.append(modus["RMSE"])

        avg_l1 = np.mean(l1_values) if len(l1_values) > 0 else None
        avg_rmse = np.mean(rmse_values) if len(rmse_values) > 0 else None

        ranking_l1.append((scenario, avg_l1))
        ranking_rmse.append((scenario, avg_rmse))

    # Sortieren (kleiner Fehler = besser)
    ranking_l1 = sorted(
        ranking_l1,
        key=lambda x: x[1] if x[1] is not None else 999
    )

    ranking_rmse = sorted(
        ranking_rmse,
        key=lambda x: x[1] if x[1] is not None else 999
    )

    print("\n====================================")
    print("Ranking nach durchschnittlichem L1")
    print("====================================\n")

    for i, (scenario, value) in enumerate(ranking_l1):
        print(f"{i+1}. {scenario} -> Avg L1 = {value}")

    print("\n====================================")
    print("Ranking nach durchschnittlichem RMSE")
    print("====================================\n")

    for i, (scenario, value) in enumerate(ranking_rmse):
        print(f"{i+1}. {scenario} -> Avg RMSE = {value}")


def analyze_A_scenarios_top5(save_root):

    ranking_l1 = []
    ranking_rmse = []
    ranking_max = []

    scenario_errors = {}

    for scenario in os.listdir(save_root):

        #if scenario.startswith("A") or scenario.startswith("B") or scenario.startswith("C"):
         #   continue

        scenario_dir = os.path.join(save_root, scenario)

        if not os.path.isdir(scenario_dir):
            continue

        error_file = os.path.join(scenario_dir, "histogram_errors.json")

        if not os.path.exists(error_file):
            continue

        with open(error_file, "r", encoding="utf-8") as f:
            errors = json.load(f)

        l1_vals = []
        rmse_vals = []
        max_vals = []

        for modus in errors.values():

            if modus["L1"] is not None:
                l1_vals.append(modus["L1"])

            if modus["RMSE"] is not None:
                rmse_vals.append(modus["RMSE"])

            if modus["MAX"] is not None:
                max_vals.append(modus["MAX"])

        if len(l1_vals) == 0:
            continue

        avg_l1 = np.mean(l1_vals)
        avg_rmse = np.mean(rmse_vals)
        avg_max = np.mean(max_vals)

        ranking_l1.append((scenario, avg_l1))
        ranking_rmse.append((scenario, avg_rmse))
        ranking_max.append((scenario, avg_max))

        scenario_errors[scenario] = {
            "L1": avg_l1,
            "RMSE": avg_rmse,
            "MAX": avg_max
        }

    # Sortieren (kleiner Fehler = besser)
    ranking_l1.sort(key=lambda x: x[1])
    ranking_rmse.sort(key=lambda x: x[1])
    ranking_max.sort(key=lambda x: x[1])

    top5_l1 = set([x[0] for x in ranking_l1[:5]])
    top5_rmse = set([x[0] for x in ranking_rmse[:5]])
    top5_max = set([x[0] for x in ranking_max[:5]])

    intersection = top5_l1 & top5_rmse & top5_max

    print("\n====================================")
    print("Szenarien in ALLEN drei Top-5:")
    print("====================================\n")

    if len(intersection) == 0:
        print("Keine Ueberschneidung.")
        return

    # Ausgabe inkl. Fehlerwerte
    sorted_intersection = sorted(
        list(intersection),
        key=lambda s: scenario_errors[s]["RMSE"]
    )

    for s in sorted_intersection:
        print(f"{s}")
        print(f"   Avg L1   = {scenario_errors[s]['L1']}")
        print(f"   Avg RMSE = {scenario_errors[s]['RMSE']}")
        print(f"   Avg MAX  = {scenario_errors[s]['MAX']}")
        print("")
# --------------------------------------------------

if __name__ == "__main__":
   # evaluate_all_scenarios()

    compute_average_ranking_from_files(SAVE_ROOT)
    analyze_A_scenarios_top5(SAVE_ROOT)
