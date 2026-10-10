#This script generates the models used for the investigation of the plugin dependency (for figure 10 and 11)

"""
Parameter Variation Scenario Generator - STRUKTURIERT
======================================

PHASE 1: MODELLE
- Berechne separate Modelle fÃ¼r num_users Ã— plugin_alpha Ã— power Kombinationen
- Mit Basis-Flex-Parametern (duration=15min, act_time=0%)
- Speichere Modelle als .pkl

PHASE 2: FLEX-SZENARIEN
- Nutze das Basis-Modell (num_users=200, plugin_alpha=0.1, power=11)
- Variiere: duration, activation_time
- FÃ¼r beide Locations (Home, Work)
"""

import datetime
import os
import json
from pathlib import Path
import shutil
import sys
import numpy as np
import matplotlib.pyplot as plt

# Stelle sicher, dass wir vom korrekten Verzeichnis aus arbeiten
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
os.chdir(project_root)
sys.path.insert(0, project_root)

from test import start_tool

# ============================================================================
# KONFIGURATION
# ============================================================================

# BASIS-Szenario (Standard-Werte)
BASIS_MODEL_PARAMS = {
    "num_users": 200,
    "plugin_alpha": 5,  # 5
    "power": 11,
    "battery_sizes": 80,

}

# PHASE 1 MODELL-Parameter (nur EINZELNE Variationen, nicht alle Kombinationen)
# Jeweils 5 Modelle pro Parameter, die anderen auf Basis-Wert


MODEL_VARIATIONS = {
    #"num_users": [25,50,100, 200, 400, 800],  # Basis: alpha=0.5, power=11
     "plugin_alpha": [500, 1000, 5000],  # Basis: users=200, power=11
    # "power": [5.5, 11, 22, 44, 88, 176],
    
    # "battery_sizes": [10,20,40,80,160,320], #Basis: users=200, alpha=0.5
}

# PHASE 2 FLEX-Parameter (auf Basis-Modell: users=200, alpha=0.5, power=11)
FLEX_VARIATIONS = {
    "start_time": [1+i*2 for i in range(0,12)],
    # "activation_time": [0, 6.25, 12.5, 25, 50, 100, 200],
}

FLEX_LOCATIONS = ["Home",
                  "Work"]

# Basis-Szenario mit Standard-Flex-Parametern
BASE_SCENARIO = {
    "duration_minutes": 15,
    "activation_time_percent": 0,
    "start_time": 18.5,
}

# Plugin Alpha Simple Konfiguration
COMPUTE_PLUGIN_ALPHA_SIMPLE = True  # Setze auf True um plugin_alpha_simple Modelle zu berechnen

# Verwende absoluten Pfad relativ zu diesem Script
OUTPUT_BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../pl_variations"))
MODELS_DIR = os.path.join(OUTPUT_BASE_DIR, "models")


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def create_model_name(param_type, param_value, location=None):
    # Für alle Parameter: location suffix hinzufügen wenn location vorhanden
    location_suffix = f"_{location.lower()}" if location else ""
    if param_type == "num_users":
        return f"model_users{param_value}{location_suffix}"
    elif param_type == "plugin_alpha":
        return f"model_alpha{str(param_value).replace('.', '_')}{location_suffix}"
    elif param_type == "power":
        return f"model_power{str(param_value).replace('.', '_')}{location_suffix}"
    elif param_type == "battery_sizes":
        return f"model_battery{str(param_value).replace('.', '_')}{location_suffix}"


def create_flex_scenario_name(param_type, param_value, flex_location, model_name):
    """Erstellt einen Namen fÃ¼r ein Flex-Szenario auf Basis-Modell"""
    value_str = str(param_value).replace(".", "_")
    location_str = flex_location.lower()
    return f"flex_{param_type}_{value_str}_{location_str}_on_{model_name}"


def get_flex_time_hours(duration_minutes):
    """Konvertiert Minuten zu Stunden fÃ¼r FLEX_START_TIME"""
    return datetime.timedelta(hours=12)


def get_flex_duration(duration_minutes):
    return duration_minutes


def get_activation_time_hours(activation_time_percent):
    """Konvertiert Aktivierungszeit von Prozent zu Stunden"""
    if activation_time_percent == 0:
        return 0
    else:
        return (activation_time_percent / 100.0) * BASE_SCENARIO['duration_minutes'] / 60


def create_charging_station_csv(power_kw):
    """
    Erstellt eine CSV-Datei fÃ¼r Ladestationen-Spezifikationen
    Format: id;[power, 1, 1, 1, 1]
    Gibt den Pfad zur Datei zurÃ¼ck
    """
    csv_dir = os.path.join(OUTPUT_BASE_DIR, "charging_specs")
    os.makedirs(csv_dir, exist_ok=True)

    power_str = str(power_kw).replace(".", "_")
    csv_file = os.path.join(csv_dir, f"charging_specs_power{power_str}.csv")

    # Wenn Datei bereits existiert, return path
    if os.path.exists(csv_file):
        return csv_file

    # Erstelle CSV mit einer Ladestation mit der gegebenen Power
    with open(csv_file, 'w') as f:
        f.write(f"0;[{power_kw}, 0, 1, 1, 1]")

    return csv_file


def create_ev_specs_csv(power_kw, battery_size):
    csv_dir = os.path.join(OUTPUT_BASE_DIR, "ev_specs")
    os.makedirs(csv_dir, exist_ok=True)

    power_str = str(power_kw).replace(".", "_")
    batt_str = str(battery_size).replace(".", "_")

    csv_file = os.path.join(csv_dir, f"ev_specs_power{power_str}_battery{batt_str}.csv")

    with open(csv_file, 'w') as f:
        f.write(
            f'1;["VW ID 5", {power_kw}, {power_kw}, {battery_size}, 17.9, 11.6, 23.7, 1, 1, 1, 1, 1, 1]'
        )

    return csv_file


# ============================================================================
# PHASE 1: MODELLE BERECHNEN
# ============================================================================

def compute_models():
    """
    # Berechne Modell-Variationen oder nur Basis-Modell wenn keine Variationen definiert
    """
    print("\n" + "=" * 120)
    print("  PHASE 1: COMPUTING MODELS")
    print("=" * 120)

    os.makedirs(MODELS_DIR, exist_ok=True)
    models_computed = []

    # PrÃ¼fe ob MODEL_VARIATIONS leer ist
    if not any(MODEL_VARIATIONS.values()):
        print(f"\n  No model variations defined. Using BASIS MODEL PARAMS only.")

        # Berechne nur Basis-Modell
        num_users = BASIS_MODEL_PARAMS["num_users"]
        plugin_alpha = BASIS_MODEL_PARAMS["plugin_alpha"]
        power = BASIS_MODEL_PARAMS["power"]

        model_name = f"model_basis_users{num_users}_alpha{str(plugin_alpha).replace('.', '_')}_power{power}"
        model_path = os.path.join(MODELS_DIR, model_name)
        model_file = f"{model_path}.pkl"

        print(f"\n  Model: {model_name}")
        print(f"    Users: {num_users}, Alpha: {plugin_alpha}, Power: {power} kW")

        # PrÃ¼fe ob Modell bereits existiert
        if os.path.exists(model_file):
            print(f"    [OK] Exists, skipping")
            models_computed.append({
                "name": model_name,
                "path": model_path,
                "num_users": num_users,
                "plugin_alpha": plugin_alpha,
                "power": power,
            })
            return models_computed

        try:
            simulation_tool = start_tool()
            csv_path = create_charging_station_csv(power)
            ev_path = create_ev_specs_csv(power)
            print(f"    Computing (users={num_users}, alpha={plugin_alpha}, power={power}kW)...")
            simulation_tool.run_model(
                run_name=model_name,
                number_of_users=num_users,
                number_of_runs=10,
                ch_filepath=csv_path,
                ev_filepath=ev_path,
                plugin_alpha_home=plugin_alpha
            )
            simulation_tool.save_model(filename=model_path)
            models_computed.append({
                "name": model_name,
                "path": model_path,
                "num_users": num_users,
                "plugin_alpha": plugin_alpha,
                "power": power,
            })
            print("    [OK] Saved")
        except Exception as e:
            print(f"    [ERROR] {e}")
            import traceback
            traceback.print_exc()

        return models_computed

    # Berechne Modell-Variationen
    print(f"  Computing model variations...")
    all_variations = []

    for param_type in ["num_users", "plugin_alpha", "power", "battery_sizes"]:
        if param_type in MODEL_VARIATIONS and MODEL_VARIATIONS[param_type]:
            for param_value in MODEL_VARIATIONS[param_type]:
                if param_type == "plugin_alpha":
                    # Zwei Modelle für plugin_alpha - Home und Work
                    all_variations.append((param_type, param_value, "Home"))
                    all_variations.append((param_type, param_value, "Work"))
                else:
                    # Andere Parameter: auch mit Home und Work Locations
                    all_variations.append((param_type, param_value, "Home"))
                    all_variations.append((param_type, param_value, "Work"))

    for param_type, param_value, location in all_variations:

        num_users = BASIS_MODEL_PARAMS["num_users"]
        plugin_alpha = BASIS_MODEL_PARAMS["plugin_alpha"]
        plugin_alpha_home = 2.5  # Standard
        plugin_alpha_work = 2.5  # Standard
        power = BASIS_MODEL_PARAMS["power"]
        battery_size = BASIS_MODEL_PARAMS["battery_sizes"]  # default

        if param_type == "num_users":
            num_users = param_value
        elif param_type == "plugin_alpha":
            plugin_alpha = param_value
            # Setze location-spezifische Werte
            if location == "Work":
                plugin_alpha_work = param_value
                plugin_alpha_home = 0.1
            elif location == "Home":
                plugin_alpha_home = param_value
                plugin_alpha_work = 0.1
        elif param_type == "power":
            power = param_value
        elif param_type == "battery_sizes":
            battery_size = param_value
            power = 11  # Fix fÃ¼r saubere Isolation

        model_name = create_model_name(param_type, param_value, location)
        model_path = os.path.join(MODELS_DIR, model_name)
        model_file = f"{model_path}.pkl"

        print(f"\n  Model: {model_name}")
        print(
            f"    Users: {num_users}, Alpha: {plugin_alpha}, Power: {power}, Battery: {battery_size}, Location: {location}")

        if os.path.exists(model_file):
            print("    [OK] Exists, skipping")
            models_computed.append({
                "name": model_name,
                "path": model_path,
                "num_users": num_users,
                "plugin_alpha": plugin_alpha,
                "power": power,
                "battery_size": battery_size,
                "location": location,
            })
            continue

        try:
            simulation_tool = start_tool()

            csv_path = create_charging_station_csv(power)
            ev_path = create_ev_specs_csv(power, battery_size)

            # Setze plugin_alpha Parameter basierend auf param_type und location
            if param_type == "plugin_alpha" and location == "Work":
                pa_work = plugin_alpha
                pa_home = 0.1
            elif param_type == "plugin_alpha" and location == "Home":
                pa_home = plugin_alpha
                pa_work = 0.1
            elif location == "Work":
                pa_work = 2.5
                pa_home = 0.1
            else:
                pa_home = 2.5
                pa_work = 0.1

            # Nutze location-spezifische plugin_alpha Parameter
            simulation_tool.run_model(
                run_name=model_name,
                number_of_users=num_users,
                number_of_runs=10,
                ch_filepath=csv_path,
                ev_filepath=ev_path,
                plugin_alpha_home=[pa_home],
                plugin_alpha_work=[pa_work]
            )

            simulation_tool.save_model(filename=model_path)

            models_computed.append({
                "name": model_name,
                "path": model_path,
                "num_users": num_users,
                "plugin_alpha": plugin_alpha,
                "power": power,
                "battery_size": battery_size,
                "location": location,
            })

            print("    [OK] Saved")

        except Exception as e:
            print(f"    [ERROR] {e}")
    return models_computed


# ============================================================================
# PHASE 2: FLEX-SZENARIEN AUF BASIS-MODELL
# ============================================================================

def compute_flex_scenarios(base_model_info):
    """
    Berechne Flex-Szenarien mit Variationen von duration, activation_time
    Nutze das Basis-Modell (num_users=200, plugin_alpha=0.1, power=11)
    """
    print("\n" + "=" * 120)
    print("  PHASE 2: COMPUTING FLEX SCENARIOS ON BASE MODEL")
    print(f"  Base model: {base_model_info['name']}")
    print("=" * 120)

    try:
        # Lade Basis-Modell
        base_model_path = base_model_info["path"]
        print(f"  Loading base model...")

        simulation_tool = start_tool()
        simulation_tool.load_model(filename=base_model_path)

        scenarios_computed = 0

        # Variiere FLEX-Parameter
        for param_type, values in FLEX_VARIATIONS.items():
            print(f"\n  {'=' * 116}")
            print(f"  VARYING: {param_type.upper()}")
            print(f"  {'=' * 116}")

            for param_value in values:
                for flex_location in FLEX_LOCATIONS:
                    scenario_name = create_flex_scenario_name(
                        param_type, param_value, flex_location, base_model_info["name"]
                    )
                    output_dir = os.path.join(OUTPUT_BASE_DIR, "flex_scenarios", scenario_name)
                    os.makedirs(output_dir, exist_ok=True)
                    
                    # KPI-Dateien
                    kpi_file = os.path.join(output_dir, f"{scenario_name}_kpis.json")
                    metadata_file = os.path.join(output_dir, f"{scenario_name}_metadata.json")
                    
                    # Prüfe ob Szenario bereits berechnet wurde
                    if os.path.exists(kpi_file) and os.path.exists(metadata_file):
                        print(f"\n    {scenario_name} [OK - already computed]")
                        print(f"      {param_type}: {param_value}, Location: {flex_location}")
                        scenarios_computed += 1
                        continue

                    print(f"\n    {scenario_name}")
                    print(f"      {param_type}: {param_value}, Location: {flex_location}")

                    try:
                        # Build scenario based on parameter type
                        scenario = BASE_SCENARIO.copy()
                        if param_type == "duration":
                            scenario["duration_minutes"] = param_value
                        elif param_type == "activation_time":
                            scenario["activation_time_percent"] = param_value

                        # Flex specifications
                        # flex_start_time = get_flex_time_hours(scenario["duration_minutes"])
                        flex_duration = get_flex_duration(scenario["duration_minutes"])
                        activation_time = get_activation_time_hours(scenario["activation_time_percent"])
                        spontanflex = (scenario["activation_time_percent"] == 0)

                        flex_specs = {
                            "flexibility_specifications": {
                                "SPONTANFLEX": spontanflex,
                                "RISK": True,
                                "FLEX_START_TIME": 11.5 if flex_location == "Work" else 18.5,
                                "FLEX_DURATION": flex_duration,
                                "FLEX_ACTIVATION_TIME": activation_time,
                                "FLEX_PLACE": flex_location,
                                "FLEX_AT_DAYTYPE": -1,
                                "FLEX_AT_NUMBER_OF_DAY": -1,
                            }
                        }

                        # Calculate flexibility
                        simulation_tool.calculate_flexibility(flex_specifications=flex_specs)

                        # Save KPIs
                        simulation_tool.save_flex_kpis_as_json(filename=kpi_file)

                        # Save metadata
                        metadata = {
                            "flex_param_type": param_type,
                            "flex_param_value": param_value,
                            "flex_location": flex_location,
                            "base_model": base_model_info["name"],
                            "base_model_params": {
                                "num_users": base_model_info["num_users"],
                                "plugin_alpha": base_model_info["plugin_alpha"],
                                "power": base_model_info["power"],
                            },
                            "scenario": scenario,
                            "flex_specs": {
                                "spontanflex": spontanflex,
                                "flex_start_time_hours": 11.5 if flex_location == "Work" else 18.5,
                                "flex_duration_minutes": scenario["duration_minutes"],
                                "activation_time_percent": scenario["activation_time_percent"],
                            }
                        }

                        with open(metadata_file, 'w') as f:
                            json.dump(metadata, f, indent=2)

                        print(f"      âœ“ Saved")
                        scenarios_computed += 1

                    except Exception as e:
                        print(f"      âœ— ERROR: {e}")

        return scenarios_computed

    except Exception as e:
        print(f"  âœ— ERROR loading base model: {e}")
        import traceback
        traceback.print_exc()
        return 0


# ============================================================================
# PHASE 1.5: FLEXIBILITÃ„TEN AUF ALLE MODELLE (mit BASIS_SCENARIO Parametern)
# ============================================================================

def compute_base_flexibilities(models):
    """
    Berechne FlexibilitÃ¤ten fÃ¼r ALLE Modelle mit BASIS_SCENARIO Parametern
    Dies ermÃ¶glicht den Vergleich: Wie wirken sich Modell-Ã„nderungen auf Flex aus?
    """
    print("\n" + "=" * 120)
    print("  PHASE 1.5: COMPUTING BASE FLEXIBILITIES FOR ALL MODELS")
    print("=" * 120)

    # Wenn keine Modelle vorhanden, Ã¼berspringe Phase 1.5
    if not models:
        print(f"\n  No models to process. Skipping base flexibilities computation.")
        return 0

    flexibilities_computed = 0

    for model in models:
        model_name = model["name"]
        model_path = model["path"]
        model_location = model.get("location", None)  # Home oder Work falls plugin_alpha

        print(f"\n  Model: {model_name}")
        print(f"    Users: {model['num_users']}, Alpha: {model['plugin_alpha']}, Power: {model['power']} kW")

        try:
            # Lade Modell
            simulation_tool = start_tool()
            simulation_tool.load_model(filename=model_path)

            # Erstelle Szenario-Namen fÃ¼r dieses Modell
            scenario_base_name = f"base_flex_on_{model_name}"
            output_dir = os.path.join(OUTPUT_BASE_DIR, "model_flexibilities", scenario_base_name)
            os.makedirs(output_dir, exist_ok=True)

            # FÃ¼r plugin_alpha Modelle: nutze nur die entsprechende Location
            # FÃ¼r andere Modelle: nutze beide Locations
            locations_to_compute = [model_location] if model_location else FLEX_LOCATIONS

            # Für jede Location
            for flex_location in locations_to_compute:
                scenario_name = f"{scenario_base_name}_{flex_location.lower()}"
                
                # KPI-Dateien
                kpi_file = os.path.join(output_dir, f"{scenario_name}_kpis.json")
                metadata_file = os.path.join(output_dir, f"{scenario_name}_metadata.json")
                
                # Prüfe ob Szenario bereits berechnet wurde
                if os.path.exists(kpi_file) and os.path.exists(metadata_file):
                    print(f"\n    {scenario_name} [OK - already computed]")
                    flexibilities_computed += 1
                    continue

                print(f"\n    {scenario_name}")
                print(
                    f"      Duration: {BASE_SCENARIO['duration_minutes']}min, Activation: {BASE_SCENARIO['activation_time_percent']}%, Location: {flex_location}")

                try:
                    # Berechne FlexibilitÃ¤t mit BASE_SCENARIO Parametern
                    # flex_start_time = get_flex_time_hours(BASE_SCENARIO["duration_minutes"])
                    flex_duration = get_flex_duration(BASE_SCENARIO["duration_minutes"])
                    activation_time = get_activation_time_hours(BASE_SCENARIO["activation_time_percent"])
                    spontanflex = (BASE_SCENARIO["activation_time_percent"] == 0)

                    flex_specs = {
                        "flexibility_specifications": {
                            "SPONTANFLEX": spontanflex,
                            "RISK": True,
                            "FLEX_START_TIME": 11.5 if flex_location == "Work" else 18.5,
                            "FLEX_DURATION": flex_duration,
                            "FLEX_ACTIVATION_TIME": activation_time,
                            "FLEX_PLACE": flex_location,
                            "FLEX_AT_DAYTYPE": -1,
                            "FLEX_AT_NUMBER_OF_DAY": -1,
                        }
                    }
                    # Calculate flexibility
                    simulation_tool.calculate_flexibility(flex_specifications=flex_specs)

                    # Save KPIs
                    simulation_tool.save_flex_kpis_as_json(filename=kpi_file)

                    # Save metadata
                    metadata = {
                        "scenario": scenario_name,
                        "model_params": {
                            "name": model_name,
                            "num_users": model["num_users"],
                            "plugin_alpha": model["plugin_alpha"],
                            "power": model["power"],
                        },
                        "flex_params": {
                            "duration_minutes": BASE_SCENARIO["duration_minutes"],
                            "activation_time_percent": BASE_SCENARIO["activation_time_percent"],
                            "flex_location": flex_location,
                            "start_time": 11.5 if flex_location == "Work" else 18.5,
                        },
                        "flex_specs": {
                            "spontanflex": spontanflex,
                            "flex_start_time_hours": 11.5 if flex_location == "Work" else 18.5,
                            "flex_duration_minutes": BASE_SCENARIO["duration_minutes"],
                            "activation_time_percent": BASE_SCENARIO["activation_time_percent"],
                        }
                    }

                    with open(metadata_file, 'w') as f:
                        json.dump(metadata, f, indent=2)

                    print(f"      [OK] Saved")
                    flexibilities_computed += 1

                except Exception as e:
                    print(f"      [ERROR] {e}")
                    import traceback
                    traceback.print_exc()

        except Exception as e:
            print(f"    [ERROR] loading model: {e}")
            import traceback
            traceback.print_exc()

    return flexibilities_computed


def compute_start_time_sensitivity(models):
    """
    Für jedes plugin_alpha Modell:
    -> alle start_times durchrechnen
    -> getrennt für Home und Work
    """

    print("\n" + "=" * 120)
    print("  PHASE 3: START TIME SENSITIVITY PER PLUGIN ALPHA")
    print("=" * 120)

    scenarios_computed = 0

    start_times = FLEX_VARIATIONS["start_time"]

    for model in models:
        # nur plugin_alpha Modelle
        if "alpha" not in model["name"]:
            continue

        model_name = model["name"]
        model_path = model["path"]
        model_location = model.get("location")

        print(f"\n  Model: {model_name} ({model_location})")

        try:
            simulation_tool = start_tool()
            simulation_tool.load_model(filename=model_path)

            for start_time in start_times:

                scenario_name = f"starttime_{start_time}_{model_location.lower()}_on_{model_name}"
                output_dir = os.path.join(
                    OUTPUT_BASE_DIR,
                    "start_time_sensitivity",
                    model_name,
                    f"{model_location.lower()}_{start_time}"
                )
                os.makedirs(output_dir, exist_ok=True)
                
                # KPI-Dateien
                kpi_file = os.path.join(output_dir, f"{scenario_name}_kpis.json")
                metadata_file = os.path.join(output_dir, f"{scenario_name}_metadata.json")
                
                # Prüfe ob Szenario bereits berechnet wurde
                if os.path.exists(kpi_file) and os.path.exists(metadata_file):
                    print(f"    Start time: {start_time} [OK - already computed]")
                    scenarios_computed += 1
                    continue

                print(f"    Start time: {start_time}")

                try:
                    flex_duration = get_flex_duration(BASE_SCENARIO["duration_minutes"])
                    activation_time = get_activation_time_hours(BASE_SCENARIO["activation_time_percent"])
                    spontanflex = (BASE_SCENARIO["activation_time_percent"] == 0)

                    flex_specs = {
                        "flexibility_specifications": {
                            "SPONTANFLEX": spontanflex,
                            "RISK": True,
                            "FLEX_START_TIME": start_time,
                            "FLEX_DURATION": flex_duration,
                            "FLEX_ACTIVATION_TIME": activation_time,
                            "FLEX_PLACE": model_location,
                            "FLEX_AT_DAYTYPE": -1,
                            "FLEX_AT_NUMBER_OF_DAY": -1,
                        }
                    }

                    simulation_tool.calculate_flexibility(flex_specifications=flex_specs)

                    # KPIs speichern
                    simulation_tool.save_flex_kpis_as_json(filename=kpi_file)

                    # Metadata speichern
                    metadata = {
                        "model": model_name,
                        "plugin_alpha": model["plugin_alpha"],
                        "location": model_location,
                        "start_time": start_time,
                        "base_scenario": BASE_SCENARIO,
                    }

                    with open(metadata_file, "w") as f:
                        json.dump(metadata, f, indent=2)

                    scenarios_computed += 1

                except Exception as e:
                    print(f"      [ERROR] {e}")

        except Exception as e:
            print(f"    [ERROR loading model] {e}")

    print(f"\n  Total start_time scenarios: {scenarios_computed}")
    return scenarios_computed


# ============================================================================
# TRIP UND PLUGIN STATISTIKEN PRO MODELL
# ============================================================================

def compute_trip_plugin_statistics(models):
    """
    Berechne für jedes Modell:
    - Anzahl Trips pro Tag: len(simulation_tool.model_data.VehicleLists[i][j].total_trip_chain_list[k])
    - Anzahl Plugins pro Tag: len(simulation_tool.model_data.VehicleLists[i][j].total_plugin_list[k])
    - Verhältnis Plugins/Trips (NUR für Tage mit mindestens 1 Trip)
    
    Speichere Statistiken und erstelle Plots
    """
    print("\n" + "=" * 120)
    print("  COMPUTING TRIP AND PLUGIN STATISTICS")
    print("=" * 120)

    for model in models:
        model_name = model["name"]
        model_path = model["path"]
        
        print(f"\n  Model: {model_name}")
        
        # Erstelle Output-Verzeichnis
        stats_dir = os.path.join(OUTPUT_BASE_DIR, "trip_plugin_statistics")
        os.makedirs(stats_dir, exist_ok=True)
        
        # Prüfe ob Statistiken bereits berechnet wurden
        json_file = os.path.join(stats_dir, f"{model_name}_statistics.json")
        plot_file = os.path.join(stats_dir, f"{model_name}_statistics.png")
        
        if os.path.exists(json_file) and os.path.exists(plot_file):
            print(f"    [OK] Statistics already computed, skipping")
            continue
        
        try:
            # Lade Modell
            simulation_tool = start_tool()
            simulation_tool.load_model(filename=model_path)
            
            # Sammle Statistiken
            all_trips_per_day = []
            all_charging_per_day = []
            charging_home_per_day = []
            charging_work_per_day = []
            charging_public_per_day = []
            ratios_per_day = []  # Gesamt Ladevorgänge / Trips
            ratios_home_per_day = []  # Home Ladevorgänge / Trips
            ratios_work_per_day = []  # Work Ladevorgänge / Trips
            ratios_public_per_day = []  # Public Ladevorgänge / Trips
            
            vehicle_lists = simulation_tool.model_data.VehicleLists
            num_runs = len(vehicle_lists)
            
            print(f"    Processing {num_runs} runs...")
            
            # Iteriere durch alle Runs (i), EVs (j), Tage (k)
            for i in range(num_runs):
                vehicles_in_run = vehicle_lists[i]
                num_vehicles = len(vehicles_in_run)
                
                for j in range(num_vehicles):
                    vehicle = vehicles_in_run[j]
                    trip_chains = vehicle.total_trip_chain_list
                    charging_list = vehicle.total_Charging_list  # NEUER: total_Charging_list
                    
                    # Nutze die tatsächliche Länge der Listen
                    num_days = len(trip_chains)
                    
                    for k in range(num_days):
                        if k < len(charging_list):
                            # Anzahl Trips an Tag k
                            trips_count = trip_chains[k].length if hasattr(trip_chains[k], 'length') else 0
                            
                            # Anzahl Ladevorgänge an Tag k - OHNE die, die um 0:00 anfangen
                            # Gruppiert nach Ort (home, work, public)
                            charging_at_day = charging_list[k]
                            
                            charging_count = 0
                            charging_home = 0
                            charging_work = 0
                            charging_public = 0
                            
                            for charging in charging_at_day:
                                # Prüfe ob Ladevorgang NICHT um nptime(0,0) anfängt
                                if hasattr(charging, 'start') and charging.start != 0:
                                    charging_count += 1
                                    
                                    # Bestimme Ort des Ladevorgangs
                                    if hasattr(charging, 'station') and hasattr(charging.station, 'Place'):
                                        place = charging.station.Place
                                        if place.lower() == 'home':
                                            charging_home += 1
                                        elif place.lower() == 'work':
                                            charging_work += 1
                                        elif place.lower() == 'public':
                                            charging_public += 1
                                elif not hasattr(charging, 'start'):
                                    # Falls kein start Attribut, zähle es
                                    charging_count += 1
                            
                            all_trips_per_day.append(trips_count)
                            all_charging_per_day.append(charging_count)
                            charging_home_per_day.append(charging_home)
                            charging_work_per_day.append(charging_work)
                            charging_public_per_day.append(charging_public)
                            
                            # Verhältnisse nur bei Tagen mit mindestens 1 Trip
                            if trips_count > 0:
                                ratio = charging_count / trips_count
                                ratios_per_day.append(ratio)
                                
                                ratio_home = charging_home / trips_count
                                ratios_home_per_day.append(ratio_home)
                                
                                ratio_work = charging_work / trips_count
                                ratios_work_per_day.append(ratio_work)
                                
                                ratio_public = charging_public / trips_count
                                ratios_public_per_day.append(ratio_public)
            
            # Berechne Statistiken
            stats = {
                "model_name": model_name,
                "model_params": {
                    "num_users": model.get("num_users"),
                    "plugin_alpha": model.get("plugin_alpha"),
                    "power": model.get("power"),
                    "location": model.get("location"),
                },
                "statistics": {
                    "total_records": len(all_trips_per_day),
                    "total_trips": sum(all_trips_per_day),
                    "total_charging": sum(all_charging_per_day),
                    "total_charging_home": sum(charging_home_per_day),
                    "total_charging_work": sum(charging_work_per_day),
                    "total_charging_public": sum(charging_public_per_day),
                    "days_with_trips": len(ratios_per_day),
                    "days_without_trips": len(all_trips_per_day) - len(ratios_per_day),
                    "avg_trips_per_day": float(np.mean(all_trips_per_day)),
                    "avg_charging_per_day": float(np.mean(all_charging_per_day)),
                    "avg_charging_home_per_day": float(np.mean(charging_home_per_day)),
                    "avg_charging_work_per_day": float(np.mean(charging_work_per_day)),
                    "avg_charging_public_per_day": float(np.mean(charging_public_per_day)),
                    "avg_ratio_charging_to_trips": float(np.mean(ratios_per_day)) if ratios_per_day else 0,
                    "avg_ratio_home_charging_to_trips": float(np.mean(ratios_home_per_day)) if ratios_home_per_day else 0,
                    "avg_ratio_work_charging_to_trips": float(np.mean(ratios_work_per_day)) if ratios_work_per_day else 0,
                    "avg_ratio_public_charging_to_trips": float(np.mean(ratios_public_per_day)) if ratios_public_per_day else 0,
                    "median_ratio_charging_to_trips": float(np.median(ratios_per_day)) if ratios_per_day else 0,
                    "std_ratio_charging_to_trips": float(np.std(ratios_per_day)) if ratios_per_day else 0,
                    "min_ratio": float(np.min(ratios_per_day)) if ratios_per_day else 0,
                    "max_ratio": float(np.max(ratios_per_day)) if ratios_per_day else 0,
                }
            }
            
            # Speichere JSON
            with open(json_file, 'w') as f:
                json.dump(stats, f, indent=2)
            
            print(f"    Total days: {len(all_trips_per_day)}")
            print(f"    Days with trips: {len(ratios_per_day)}")
            print(f"    Avg Trips/Day: {stats['statistics']['avg_trips_per_day']:.2f}")
            print(f"    Avg Charging/Day: {stats['statistics']['avg_charging_per_day']:.2f}")
            print(f"      - Home: {stats['statistics']['avg_charging_home_per_day']:.2f}")
            print(f"      - Work: {stats['statistics']['avg_charging_work_per_day']:.2f}")
            print(f"      - Public: {stats['statistics']['avg_charging_public_per_day']:.2f}")
            print(f"    Ratio Charging/Trips: {stats['statistics']['avg_ratio_charging_to_trips']:.4f}")
            print(f"      - Home: {stats['statistics']['avg_ratio_home_charging_to_trips']:.4f}")
            print(f"      - Work: {stats['statistics']['avg_ratio_work_charging_to_trips']:.4f}")
            print(f"      - Public: {stats['statistics']['avg_ratio_public_charging_to_trips']:.4f}")
            print(f"    [OK] Statistics saved to {json_file}")
            
            # Erstelle Plot
            fig, axes = plt.subplots(2, 3, figsize=(16, 10))
            fig.suptitle(f"Charging and Trip Statistics - {model_name}", fontsize=14, fontweight='bold')
            
            # Plot 1: Trips pro Tag
            axes[0, 0].hist(all_trips_per_day, bins=30, alpha=0.7, color='blue', edgecolor='black')
            axes[0, 0].set_xlabel("Trips per Day")
            axes[0, 0].set_ylabel("Frequency")
            axes[0, 0].set_title("Distribution of Trips per Day")
            axes[0, 0].axvline(np.mean(all_trips_per_day), color='red', linestyle='--', linewidth=2, label=f"Mean: {np.mean(all_trips_per_day):.2f}")
            axes[0, 0].legend()
            
            # Plot 2: Charging pro Tag (gesamt)
            axes[0, 1].hist(all_charging_per_day, bins=30, alpha=0.7, color='green', edgecolor='black')
            axes[0, 1].set_xlabel("Charging per Day")
            axes[0, 1].set_ylabel("Frequency")
            axes[0, 1].set_title("Distribution of Charging per Day")
            axes[0, 1].axvline(np.mean(all_charging_per_day), color='red', linestyle='--', linewidth=2, label=f"Mean: {np.mean(all_charging_per_day):.2f}")
            axes[0, 1].legend()
            
            # Plot 3: Charging pro Tag nach Ort (Home, Work, Public)
            x_pos = np.arange(3)
            charging_by_place = [
                np.mean(charging_home_per_day),
                np.mean(charging_work_per_day),
                np.mean(charging_public_per_day)
            ]
            axes[0, 2].bar(x_pos, charging_by_place, alpha=0.7, color=['orange', 'purple', 'red'], edgecolor='black')
            axes[0, 2].set_xlabel("Place")
            axes[0, 2].set_ylabel("Avg Charging Events")
            axes[0, 2].set_title("Average Charging Events by Place")
            axes[0, 2].set_xticks(x_pos)
            axes[0, 2].set_xticklabels(['Home', 'Work', 'Public'])
            
            # Plot 4: Verhältnis Charging/Trips (gesamt)
            if ratios_per_day:
                axes[1, 0].hist(ratios_per_day, bins=30, alpha=0.7, color='cyan', edgecolor='black')
                axes[1, 0].set_xlabel("Ratio (Charging/Trips)")
                axes[1, 0].set_ylabel("Frequency")
                axes[1, 0].set_title("Distribution of Charging/Trips Ratio (only days with trips)")
                axes[1, 0].axvline(np.mean(ratios_per_day), color='red', linestyle='--', linewidth=2, label=f"Mean: {np.mean(ratios_per_day):.4f}")
                axes[1, 0].legend()
            else:
                axes[1, 0].text(0.5, 0.5, "No days with trips", ha='center', va='center', fontsize=12)
                axes[1, 0].set_title("Distribution of Charging/Trips Ratio")
            
            # Plot 5: Verhältnis nach Ort (Home, Work, Public)
            ratios_by_place = [
                np.mean(ratios_home_per_day) if ratios_home_per_day else 0,
                np.mean(ratios_work_per_day) if ratios_work_per_day else 0,
                np.mean(ratios_public_per_day) if ratios_public_per_day else 0
            ]
            axes[1, 1].bar(x_pos, ratios_by_place, alpha=0.7, color=['orange', 'purple', 'red'], edgecolor='black')
            axes[1, 1].set_xlabel("Place")
            axes[1, 1].set_ylabel("Avg Charging/Trips Ratio")
            axes[1, 1].set_title("Average Charging/Trips Ratio by Place")
            axes[1, 1].set_xticks(x_pos)
            axes[1, 1].set_xticklabels(['Home', 'Work', 'Public'])
            
            # Plot 6: Scatter - Trips vs Charging (nur Tage mit Trips)
            if ratios_per_day:
                trips_with_ratio = [all_trips_per_day[i] for i in range(len(all_trips_per_day)) if all_trips_per_day[i] > 0]
                charging_with_ratio = [all_charging_per_day[i] for i in range(len(all_trips_per_day)) if all_trips_per_day[i] > 0]
                axes[1, 2].scatter(trips_with_ratio, charging_with_ratio, alpha=0.5, s=10)
            axes[1, 2].set_xlabel("Trips per Day")
            axes[1, 2].set_ylabel("Charging per Day")
            axes[1, 2].set_title("Correlation: Trips vs Charging (only days with trips)")
            
            plt.tight_layout()
            
            # Speichere Plot
            plot_file = os.path.join(stats_dir, f"{model_name}_statistics.png")
            plt.savefig(plot_file, dpi=150, bbox_inches='tight')
            plt.close()
            
            print(f"    [OK] Plot saved to {plot_file}")
            
        except Exception as e:
            print(f"    [ERROR] {e}")
            import traceback
            traceback.print_exc()


# ============================================================================
# PLUGIN ALPHA SIMPLE MODELLE
# ============================================================================

def compute_plugin_alpha_simple_models():
    """
    Berechne Modelle mit plugin_alpha_simple=True
    Erstelle separate Modelle für Home und Work Locations
    """
    print("\n" + "=" * 120)
    print("  PHASE: COMPUTING PLUGIN ALPHA SIMPLE MODELS")
    print("=" * 120)

    os.makedirs(MODELS_DIR, exist_ok=True)
    models_computed = []

    # Basis-Parameter
    num_users = BASIS_MODEL_PARAMS["num_users"]
    power = BASIS_MODEL_PARAMS["power"]
    battery_size = BASIS_MODEL_PARAMS["battery_sizes"]

    # Erstelle zwei Modelle - für Home und Work
    for location in ["Home", "Work"]:
        model_name = f"model_plugin_alpha_simple_{location.lower()}"
        model_path = os.path.join(MODELS_DIR, model_name)
        model_file = f"{model_path}.pkl"
        
        # Konvertiere zu absolutem Pfad für zuverlässige Existenz-Prüfung
        model_file_abs = os.path.abspath(model_file)

        print(f"\n  Model: {model_name}")
        print(f"    Users: {num_users}, Plugin Alpha Simple: True, Power: {power} kW, Location: {location}")
        print(f"    Path: {model_file_abs}")

        # Prüfe ob Modell bereits existiert
        if os.path.exists(model_file_abs):
            print(f"    [OK] Exists, skipping")
            models_computed.append({
                "name": model_name,
                "path": model_path,
                "num_users": num_users,
                "plugin_alpha": "simple",
                "power": power,
                "battery_size": battery_size,
                "location": location,
                "plugin_alpha_simple": True,
            })
            continue

        try:
            simulation_tool = start_tool()
            csv_path = create_charging_station_csv(power)
            ev_path = create_ev_specs_csv(power, battery_size)

            print(f"    Computing (users={num_users}, plugin_alpha_simple=True, power={power}kW, location={location})...")
            
            # Run model with plugin_alpha_simple=True
            simulation_tool.run_model(
                run_name=model_name,
                number_of_users=num_users,
                number_of_runs=10,
                ch_filepath=csv_path,
                ev_filepath=ev_path,
                plugin_alpha_simple=True
            )
            
            simulation_tool.save_model(filename=model_path)
            
            models_computed.append({
                "name": model_name,
                "path": model_path,
                "num_users": num_users,
                "plugin_alpha": "simple",
                "power": power,
                "battery_size": battery_size,
                "location": location,
                "plugin_alpha_simple": True,
            })
            print("    [OK] Saved")

        except Exception as e:
            print(f"    [ERROR] {e}")
            import traceback
            traceback.print_exc()

    return models_computed

# ============================================================================
# HAUPTPROGRAMM
# ============================================================================

def main():
    print("\n" + "=" * 120)
    print("  PARAMETER VARIATION SCENARIO GENERATOR - STRUCTURED")
    print("=" * 120)

    print(f"\nBase Scenario:")
    for key, value in BASE_SCENARIO.items():
        print(f"  {key}: {value}")

    print(f"\nModel Parameters (each combination = new model):")
    for key, values in MODEL_VARIATIONS.items():
        print(f"  {key}: {values}")

    print(f"\nFlex Parameters (on base model only):")
    for key, values in FLEX_VARIATIONS.items():
        print(f"  {key}: {values}")

    os.makedirs(OUTPUT_BASE_DIR, exist_ok=True)

    # PHASE 1: Compute models
    models = compute_models()
    
    # PHASE: Compute plugin_alpha_simple models
    if COMPUTE_PLUGIN_ALPHA_SIMPLE:
        simple_models = compute_plugin_alpha_simple_models()
        models.extend(simple_models)

    print(f"\n{'=' * 120}")
    print(f"  Models computed: {len(models)}")
    print(f"{'=' * 120}")

    # PHASE 1.5: Compute trip and plugin statistics for all models
    print("\n  Computing trip and plugin statistics for all models...")
    compute_trip_plugin_statistics(models)

    print(f"\n{'=' * 120}")
    print(f"  Trip/Plugin statistics computed")
    print(f"{'=' * 120}")

    # PHASE 1.5: Compute base flexibilities for all models
    #base_flexibilities = compute_base_flexibilities(models)

    #print(f"\n{'=' * 120}")
    #print(f"  Base flexibilities computed: {base_flexibilities}")
    #print(f"{'=' * 120}")

    # PHASE 2: Compute flex scenarios on base model
    # Find base model (num_users=200, plugin_alpha=0.5, power=11)
    if False:
        base_model = None
        for model in models:
            if (model["num_users"] == 100 and
                    model["plugin_alpha"] == 2.5 and
                    model["power"] == 11):
                base_model = model
                break

        if base_model:
            print(f"\n  Base model found: {base_model['name']}")
            flex_scenarios = compute_flex_scenarios(base_model)

            print(f"\n{'=' * 120}")
            print(f"SUMMARY")
            print(f"{'=' * 120}")
            print(f"Models computed: {len(models)}")
            print(f"Base flexibilities computed (for all models): {base_flexibilities}")
            print(f"Flex scenarios computed (on base model): {flex_scenarios}")
            print(f"Output directory: {OUTPUT_BASE_DIR}")
            print(f"{'=' * 120}")
        else:
            print(f"\n  ✗ ERROR: Base model not found!")
            print(f"  Available models:")
            for model in models[:10]:
                print(f"    {model['name']}")

    # PHASE 3: Startzeit Sensitivity für plugin_alpha
    start_time_runs = compute_start_time_sensitivity(models)

    print(f"\nStart-time sensitivity scenarios computed: {start_time_runs}")


if __name__ == "__main__":
    main()

