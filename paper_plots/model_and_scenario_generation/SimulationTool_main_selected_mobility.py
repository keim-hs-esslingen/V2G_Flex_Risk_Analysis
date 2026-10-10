import os.path
import multiprocessing
import gc
import time as _time

# Importiere nur die tatsächlich genutzten Symbole aus test, damit keine Namen (z.B. `time`) überschrieben werden
from test import start_tool, compare_fixDate_with_spontanflex

TABLE_DIMS = {
    "regiontype": 8,
    "homogroup": 4,
    "mobilitygroup": 4,
    "agegroup": 4,
    "econstatus": 6,
}

max_variant = {
    "regiontype": "8",
    "homogroup": "4",
    "mobilitygroup": "4",
    "agegroup": "4",
    "econstatus": "6",
}



def cumulative_vector(n_cols, active_idx):
    """
    n_cols: Anzahl Spalten
    active_idx: 1-basierter Index (1..n_cols)
    """
    vec = []
    for i in range(1, n_cols + 1):
        if i < active_idx:
            vec.append(0)
        else:
            vec.append(1)
    return vec

DEFAULT_TABLES = {
    # aus Original-CSV übernehmen!
    "federalstate": cumulative_vector(17, 17),       # letzte Spalte = 1
    "startdestination": cumulative_vector(3, 3),     # letzte Spalte = 1
}

def generate_selected_variants():
    selected = [
        ("homogroup", 2),
        ("mobilitygroup", 3),
        ("mobilitygroup", 4),
        ("agegroup", 1),
        ("agegroup", 3),
        ("agegroup", 4),
    ]

    variants = []

    for dim_name, active_idx in selected:

        tables = {}

        for other_dim, other_cols in TABLE_DIMS.items():
            if other_dim == dim_name:
                tables[other_dim] = cumulative_vector(other_cols, active_idx)
            else:
                tables[other_dim] = cumulative_vector(other_cols, other_cols)

        tables["federalstate"] = DEFAULT_TABLES["federalstate"]
        tables["startdestination"] = DEFAULT_TABLES["startdestination"]

        variant_name = f"{dim_name}_{active_idx}"

        variants.append({
            "name": variant_name,
            "tables": tables
        })

    return variants

def generate_table_variants():
    variants = []

    for dim_name, n_cols in TABLE_DIMS.items():
        for active_idx in range(1, n_cols + 1):

            tables = {}

            for other_dim, other_cols in TABLE_DIMS.items():
                if other_dim == dim_name:
                    tables[other_dim] = cumulative_vector(other_cols, active_idx)
                else:
                    tables[other_dim] = cumulative_vector(other_cols, other_cols)

            # 🔥 FIXE Default-Tabellen ergänzen
            tables["federalstate"] = DEFAULT_TABLES["federalstate"]
            tables["startdestination"] = DEFAULT_TABLES["startdestination"]

            variant_name = f"{dim_name}_{active_idx}"
            variants.append({
                "name": variant_name,
                "tables": tables
            })

    return variants




import numpy as np
if False:
    START_TIMES_BY_PLACE = {
        "Home": [1.5, 8.0, 11.5, 13.5, 16.5, 18.5, 20.0, 22.0],
        "Work": [8.0, 11.0, 12.5, 14.0, 15.5, 17.0],
    }
    # work mit anderen plug-in-parametern
    FLEX_PLACES = ["Home"]
    DURATIONS = [15, 60]

    ACT_TIMES = {
        15: [7.5/60, 15/60],
        60: [30/60, 60/60],
    }

START_TIMES_BY_PLACE = {
    "Home": [1,3,5,7,9,11,13,15,17,19,21,23],#[1, 8, 11.5, 13.5, 16.5, 18.5, 20, 22],
    "Work": [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23]
}
# work mit anderen plug-in-parametern
FLEX_PLACES = ["Home"]
DURATIONS = [60] #15
ACT_TIMES = {
    15: [ 7.5/15,  15 / 15],
    60: [ 15 / 60, 30 / 60, 60 / 60],
}


import os, gc, multiprocessing

import csv

def write_populate_users_csv(path, tables_dict):
    """
    Schreibe PopulateUsers CSV mit der richtigen Reihenfolge und Längen
    Basierend auf: models/model_pl_medium_agegroup_1/PopulateUsers.csv
    """
    # Reihenfolge MUSS genau so sein wie in den bestehenden Modellen!
    order = [
        "regiontype",        # Row 1: 8 Elemente
        "federalstate",      # Row 2: 17 Elemente
        "homogroup",         # Row 3: 4 Elemente
        "mobilitygroup",     # Row 4: 4 Elemente
        "agegroup",          # Row 5: 3 Elemente
        "startdestination",  # Row 6: 3 Elemente
        "econstatus",        # Row 7: 6 Elemente
    ]

    with open(path, "w", newline="") as f:
        writer = csv.writer(f, delimiter=";")
        for i, key in enumerate(order, start=1):
            vec = tables_dict[key]
            # Formatiere die Liste als String: [0, 0, 1, ...]
            vec_str = str(vec)
            writer.writerow([i, vec_str])

from config.settings import set_populate_users_csv_path

PL_VARIANTS = ["pl_normal_"]#, "pl_low_", "pl_medium_"]

#Todo: andere pl_low, pl_medium und pl_normal_work (mit work anderen plugin und dann location flex_places auf work
# bei work-graphiken auch schauen, das nur diese verwendet werden

def run_all_scenarios(simulation_tool,
                      pl_variant="pl_normal_",
                      base_dir="scenarios_final/",
                      batch_size=16,
                      batch_timeout_s=60*30):

    table_variants = generate_selected_variants()

    for table_variant in table_variants:

        # --------------------------------------------------
        # 1) Eindeutiger Modellname
        # --------------------------------------------------
        model_name = f"model_{pl_variant}{table_variant['name']}"
        model_path = os.path.join("../../models_final", model_name)

        print(f"\n=== MODEL: {model_name} ===")

        os.makedirs("../../models", exist_ok=True)

        # --------------------------------------------------
        # 2) PopulateUsers-CSV für dieses Modell erzeugen
        # --------------------------------------------------
        model_dir = os.path.join("../../models", model_name)
        os.makedirs(model_dir, exist_ok=True)

        populate_csv_path = os.path.join(model_dir, "PopulateUsers.csv")

        write_populate_users_csv(
            populate_csv_path,
            table_variant["tables"]
        )

        # 🔑 globalen Pfad setzen (entscheidend!)
        set_populate_users_csv_path(populate_csv_path)

        # --------------------------------------------------
        # 3) Modell laden oder neu rechnen
        # --------------------------------------------------
        if os.path.exists(f"{model_path}.pkl"):
            print("Modell vorhanden – lade.")
            simulation_tool.load_model(filename=model_path)
        else:
            print("Berechne neues Modell.")
            simulation_tool.run_model(run_name=model_name)
            simulation_tool.save_model(filename=model_path)

        scenarios_root = os.path.join(base_dir, model_name)
        os.makedirs(scenarios_root, exist_ok=True)

        current_batch = []
        if True:
            test = False
            # --------------------------------------------------
            # 3) Flex-Szenarien
            # --------------------------------------------------
            if test == False:
                for spontanflex in [True]:
                    for flex_place in FLEX_PLACES:
                        start_times = START_TIMES_BY_PLACE[flex_place]

                        for duration in DURATIONS:
                            for start_time in start_times:

                                if spontanflex:
                                    act_times = [0]
                                else:
                                    act_times = ACT_TIMES[duration]

                                for act_time in act_times:

                                    flex_spec = {
                                        "flexibility_specifications": {
                                            "SPONTANFLEX": spontanflex,
                                            "RISK": 1,
                                            "FLEX_PLACE": flex_place,
                                            "FLEX_DURATION": duration,
                                            "FLEX_START_TIME": round(start_time, 2),
                                            "FLEX_ACTIVATION_TIME": act_time,
                                            "FLEX_AT_NUMBER_OF_DAY": -1,
                                            "FLEX_AT_NUMBER_OF_RUN": -1,
                                            "FLEX_AT_DAYTYPE": -1,
                                        }
                                    }

                                    scenario_name = (
                                        f"spont{spontanflex}"
                                        f"_place{flex_place}"
                                        f"_act{act_time:.2f}"
                                        f"_t{start_time:.2f}"
                                        f"_dur60"#{duration}
                                    ).replace(".", "_")

                                    current_batch.append((scenario_name, flex_spec))

                                    if len(current_batch) >= batch_size:
                                        _run_batch(
                                            current_batch,
                                            model_name,
                                            scenarios_root,
                                            batch_timeout_s
                                        )
                                        current_batch = []
            else:
                flex_spec = {
                    "flexibility_specifications": {
                        "SPONTANFLEX": True,
                        "RISK": 1,
                        "FLEX_PLACE": "Home",
                        "FLEX_DURATION": 15,
                        "FLEX_START_TIME": round(18.0, 2),
                        "FLEX_ACTIVATION_TIME": 0.0,
                        "FLEX_AT_NUMBER_OF_DAY": -1,
                        "FLEX_AT_NUMBER_OF_RUN": -1,
                        "FLEX_AT_DAYTYPE": -1,
                    }
                }
                scenario_name = (
                    f"{pl_variant}{table_variant['name']}"
                ).replace(".", "_")

                current_batch.append((scenario_name, flex_spec))

                if len(current_batch) >= batch_size:
                    _run_batch(
                        current_batch,
                        model_name,
                        scenarios_root,
                        batch_timeout_s
                    )
                    current_batch = []
            # --------------------------------------------------
            # 4) Restlicher Batch
            # --------------------------------------------------
            if current_batch:
                _run_batch(
                    current_batch,
                    model_name,
                    scenarios_root,
                    batch_timeout_s
                )

            simulation_tool.save_model(filename=model_path)


def _run_batch(batch, model_name, scenarios_root, timeout):
    p = multiprocessing.Process(
        target=_batch_worker_run_scenarios,
        args=(
            batch.copy(),
            os.path.join("../../models_final", model_name),
            scenarios_root,
            model_name,
        )
    )
    p.start()
    p.join(timeout=timeout)

    if p.is_alive():
        print("Batch hängt – terminate.")
        p.terminate()
        p.join()

    try:
        p.close()
    except Exception:
        pass

    gc.collect()

## running one scenario
def run_scenario(scenario_name, model_name, flex_spec, simulation_tool, base_dir = "scenarios_final/", load_model = False):
    scenario_dir = os.path.join(base_dir, scenario_name)
    model_path = os.path.join("../../models_final/", model_name)

    # Skip wenn KPI-Datei bereits existiert
    kpi_file = os.path.join(scenario_dir, f"{scenario_name}_kpis.json")
    if os.path.exists(kpi_file):
        print(f"[Skip] Szenario bereits vorhanden: {scenario_name}")
        return

    if os.path.exists(f"{model_path}.pkl"):
        print(f"Gefundenes Modell: {model_path}.pkl")
        if load_model:
            print(f"Lade Modell '{model_name}' aus '{model_path}.pkl'...")
            simulation_tool.load_model(filename=model_path)
            print("Modell geladen.")
        else:
            print(f"Modell '{model_name}' ist vorhanden, lade es nicht (load_model=False).")
    else:
        print(f"Modell nicht gefunden: {model_path}.pkl -> Berechne Modell '{model_name}'...")
        simulation_tool.run_model(run_name = model_name)
        print("Modellberechnung abgeschlossen. Speichere Modell...")
        simulation_tool.save_model(filename=model_path)
        print(f"Modell berechnet und gespeichert: {model_path}.pkl")

    print(f"Starte Flexibilitätsberechnung für Szenario '{scenario_name}'...")
    print(f"Flex-Spezifikationen: {flex_spec}")
    simulation_tool.calculate_flexibility(flex_specifications=flex_spec)
    print(f"Flexibilitätsberechnung für Szenario '{scenario_name}' abgeschlossen.")

    # NOTE: Quantiles und KPIs werden bereits in calculate_flexibility() berechnet
    # (in flex_object.compute_flexibility() → compute_min_quarter_quantiles_from_flex_list())
    # Redundante Aufrufe hier waren BUGGY und führten zur Verdoppelung der Statistiken!

    os.makedirs(scenario_dir, exist_ok=True)

    # Speichern
    print(f"Speichere Szenario '{scenario_name}' in '{scenario_dir}'...")
    simulation_tool.save_scenario(filename=f"{scenario_dir}/{scenario_name}")
    print(f"Szenario '{scenario_name}' gespeichert in '{scenario_dir}'")
    #model_data.name wird gesetzt bei run_model
    #save_model wird unter filename abgepeichert und filename auch in kpis_json abgepeichert zusammen mit model_data.name

    #--> d.h. über laod_model/run_model kann gleiches modell geladen werden mit filename und model_name sollte filename ohne dir sein

#running several scenarios automatically with different specifications
import numpy as np
import os

def _batch_worker_run_scenarios(batch_scenarios, model_path, scenarios_root, model_name):
    """
    Worker-Funktion, läuft in eigenem Prozess. Lädt/erstellt ein neues simulation_tool
    und führt `run_scenario` für alle Einträge in `batch_scenarios` aus.

    batch_scenarios: Liste von (scenario_name, flex_spec)
    model_path: Pfad ohne '.pkl', z.B. 'models/model_5'
    scenarios_root: Zielordner für Szenarien
    model_name: Name des Modells (z.B. 'model_5')
    """
    try:
        from test import start_tool
    except Exception as e:
        print("Worker: Fehler beim Import von start_tool:", e)
        return

    sim = None
    try:
        sim = start_tool()
        pkl_path = f"{model_path}.pkl"
        if os.path.exists(pkl_path):
            try:
                sim.load_model(filename=model_path)
            except Exception as e:
                print(f"Worker: Fehler beim Laden des Modells '{pkl_path}':", e)
                try:
                    sim.run_model(run_name=model_name)
                    sim.save_model(filename=model_path)
                except Exception as e2:
                    print("Worker: Fehler beim Neuberechnen des Modells:", e2)
                    return
        else:
            try:
                sim.run_model(run_name=model_name)
                sim.save_model(filename=model_path)
            except Exception as e:
                print("Worker: Fehler beim Erstellen/Speichern des Modells:", e)
                return

        for scenario_name, flex_spec in batch_scenarios:
            try:
                print(f"[Worker] Starte Szenario: {scenario_name}")
                run_scenario(scenario_name=scenario_name,
                             model_name=model_name,
                             flex_spec=flex_spec,
                             simulation_tool=sim,
                             base_dir=scenarios_root,
                             load_model=False)
                print(f"[Worker] Szenario abgeschlossen: {scenario_name}")
            except Exception as e:
                print(f"[Worker] Fehler bei Szenario '{scenario_name}':", e)
    finally:
        # Aufräumen im Worker
        try:
            sim = None
            gc.collect()
        except Exception:
            pass

def SimulationTool():
    # Do not delete this line
    simulation_tool = start_tool()


    # in SimulationTool_Settings.json, one can adapt global parameters for computation.
    # To adapt specifications during main method, one can also overwrite the global parameters
    # by setting parameters within call of the methods (see example methods above)
    # --> specification names are the same like the global parameter names, but in lower case letters

    # Here work with tool methods and specifications or set parameters simply in SimulationTool_Settings.json:
    # load_model()/ save_model(), run_model(), calculate_flexibility(), visualize_flexibility()

    # first: run_model or if a model is already saved: load_model()
    simulation_tool.run_model()
    simulation_tool.save_model()
    #simulation_tool.load_model()

    # second: calculate flexibility_calc, so it can be visualized
    simulation_tool.calculate_flexibility()

    # third: user defined methods, save_model(), calculate_flexibility() or visualize_flexibility
    simulation_tool.visualize_flexibility()

    # repeat step 2 to 4 for different flexibilities and visualizations
    # main also can be started with different configuration
    # see above methods for examples

    # if you use specifications:
    # model specifications do overwrite the corresponding global parameters as long as another model within
    # SimulationTool() is computed.
    # Flexibility calculation/ visualization therefore knows about model parameters of the current model

    # flexibility_specifications do overwrite the corresponding global parameters as long as calculate_flexibility()
    # is called again. Then specifications are set to new specifications (if given) or to global parameters
    # time specifications are declared with datetime.timedelta(). Within the brackets, one can define the time according
    # to hours, minutes, seconds and microseconds.
    # To declare the start time of the flexibility_calc delievery, one defines within the method:
    # flexibility_calculations(flex_start_time = datetime.timedelta(hours = 13, minutes = 20, seconds = 40)
    # to start the flex time at 13:20:40. The global parameter in SimulationTool_Settings is given in hours:
    # FLEX_START_TIME: 13.34444444,

    # Visualization specifications are only overwritten during call of the method



if __name__ == "__main__":
    simulation_tool = start_tool()
    for pl_variant in PL_VARIANTS:
        run_all_scenarios(simulation_tool=simulation_tool, pl_variant=pl_variant)
    #testing()
    #load_model_and_calculate_several_flexibilities_with_user_defined_analysis()


# parameter units in SimulationTool_settings.json:
#duration, min_flex_time, min_delievery_time,: minutes
#flex_activation_time, flex_start time: hours