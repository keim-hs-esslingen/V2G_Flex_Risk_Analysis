#für figure 16 und 17 werden hier die MOdelle generiert

"""
This has been used in particular for the model generation for figure 16 and 17 in the paper
Parameter Variation Scenario Generator - STRUKTURIERT
======================================

PHASE 1: MODELLE
- Berechne separate Modelle für num_users Ã— plugin_alpha Ã— power Kombinationen
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
from test import start_tool
import shutil

# ============================================================================
# KONFIGURATION
# ============================================================================

# BASIS-Szenario (Standard-Werte)
BASIS_MODEL_PARAMS = {
    "num_users": 100,
    "plugin_alpha": 2.5, #5
    "power": 11,
    "battery_sizes": 80,

}

# PHASE 1 MODELL-Parameter (nur EINZELNE Variationen, nicht alle Kombinationen)
# Jeweils 5 Modelle pro Parameter, die anderen auf Basis-Wert


MODEL_VARIATIONS = {
    "num_users": [25,50,100, 200, 300, 400],          # Basis: alpha=0.5, power=11
    "plugin_alpha": [0.15625, 0.3125, 0.625, 1.25, 2.5, 5, 7.5, 10],  # Basis: users=200, power=11
    "power": [5.5, 11, 22, 44, 88, 132, 176],
    "battery_sizes": [ 20, 40, 80, 160, 240, 320], #Basis: users=200, alpha=0.5
    "battery_sizes_simple": [20, 40, 80, 160, 240, 320], # same as battery_sizes but with plugin_alpha_simple=True
}

# PHASE 2 FLEX-Parameter (auf Basis-Modell: users=200, alpha=0.5, power=11)
FLEX_VARIATIONS = {
   "duration": [3.75, 7.5, 15, 30, 60, 90, 120],
    "activation_time": [0, 6.25, 12.5, 25, 50, 100, 200],
}

FLEX_LOCATIONS = ["Home", "Work"]

# Basis-Szenario mit Standard-Flex-Parametern
BASE_SCENARIO = {
    "duration_minutes": 30,
    "activation_time_percent": 0,
    "start_time": 18.5,
}

OUTPUT_BASE_DIR = "../../parameter_variations2"
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
    elif param_type == "battery_sizes_simple":
        return f"model_battery{str(param_value).replace('.', '_')}_simple{location_suffix}"

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
        return (activation_time_percent / 100.0) * BASE_SCENARIO['duration_minutes']/60


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
            f'1;["VW ID 5", {battery_size}, {power_kw}, {power_kw}, 17.9, 11.6, 23.7, 1, 1, 1, 1, 1, 1]'
        )

    return csv_file

# ============================================================================
# PHASE 1: MODELLE BERECHNEN
# ============================================================================

def compute_models():
    """
    # Berechne Modell-Variationen oder nur Basis-Modell wenn keine Variationen definiert
    """
    print("\n" + "="*120)
    print("  PHASE 1: COMPUTING MODELS")
    print("="*120)
    
    os.makedirs(MODELS_DIR, exist_ok=True)
    models_computed = []
    
    # Prüfe ob MODEL_VARIATIONS leer ist
    if not any(MODEL_VARIATIONS.values()):
        print(f"\n  No model variations defined. Creating two BASIS MODELS (Home and Work focused).")
        
        # Erstelle zwei Basis-Modelle: eine mit Home-Focus, eine mit Work-Focus
        for location in ["Home", "Work"]:
            num_users = BASIS_MODEL_PARAMS["num_users"]
            power = BASIS_MODEL_PARAMS["power"]
            battery_size = BASIS_MODEL_PARAMS["battery_sizes"]
            
            # Setze plugin_alpha basierend auf Location - nutze BASIS_MODEL_PARAMS
            base_alpha = BASIS_MODEL_PARAMS["plugin_alpha"]
            alpha_str = str(base_alpha).replace(".", "_")
            if location == "Home":
                pa_home = base_alpha
                pa_work = 0.1
                model_name = f"model_basis_home_users{num_users}_alpha{alpha_str}_power{power}"
            else:  # Work
                pa_home = 0.1
                pa_work = base_alpha
                model_name = f"model_basis_work_users{num_users}_alpha{alpha_str}_power{power}"
            
            model_path = os.path.join(MODELS_DIR, model_name)
            model_file = f"{model_path}.pkl"
            
            print(f"\n  Model: {model_name}")
            print(f"    Users: {num_users}, Alpha Home: {pa_home}, Alpha Work: {pa_work}, Power: {power} kW")
            
            # Prüfe ob Modell bereits existiert
            if os.path.exists(model_file):
                print(f"    [OK] Exists, skipping")
                models_computed.append({
                    "name": model_name,
                    "path": model_path,
                    "num_users": num_users,
                    "plugin_alpha_home": pa_home,
                    "plugin_alpha_work": pa_work,
                    "power": power,
                    "location": location,
                })
                continue
            
            try:
                simulation_tool = start_tool()
                csv_path = create_charging_station_csv(power)
                ev_path = create_ev_specs_csv(power, battery_size)
                print(f"    Computing (users={num_users}, alpha_home={pa_home}, alpha_work={pa_work}, power={power}kW)...")
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
                    "plugin_alpha_home": pa_home,
                    "plugin_alpha_work": pa_work,
                    "power": power,
                    "location": location,
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
    
    for param_type in ["num_users", "plugin_alpha", "power", "battery_sizes", "battery_sizes_simple"]:
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
        elif param_type == "battery_sizes_simple":
            battery_size = param_value


        model_name = create_model_name(param_type, param_value, location)
        model_path = os.path.join(MODELS_DIR, model_name)
        model_file = f"{model_path}.pkl"

        print(f"\n  Model: {model_name}")
        print(f"    Users: {num_users}, Alpha: {plugin_alpha}, Power: {power}, Battery: {battery_size}, Location: {location}")

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
            run_model_kwargs = dict(
                run_name=model_name,
                number_of_users=num_users,
                number_of_runs=10,
                ch_filepath=csv_path,
                ev_filepath=ev_path,
                plugin_alpha_home=[pa_home],
                plugin_alpha_work=[pa_work],
            )
            if param_type == "battery_sizes_simple":
                run_model_kwargs["plugin_alpha_simple"] = True
            simulation_tool.run_model(**run_model_kwargs)

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
    print("\n" + "="*120)
    print("  PHASE 2: COMPUTING FLEX SCENARIOS ON BASE MODEL")
    print(f"  Base model: {base_model_info['name']}")
    print("="*120)
    
    try:
        # Lade Basis-Modell
        base_model_path = base_model_info["path"]
        print(f"  Loading base model...")
        
        simulation_tool = start_tool()
        simulation_tool.load_model(filename=base_model_path)
        
        scenarios_computed = 0
        
        # Nutze nur die Location, für die das Modell optimiert wurde
        model_location = base_model_info.get("location", "Home")
        locations_to_compute = [model_location]
        
        # Variiere FLEX-Parameter
        for param_type, values in FLEX_VARIATIONS.items():
            print(f"\n  {'='*116}")
            print(f"  VARYING: {param_type.upper()}")
            print(f"  {'='*116}")
            
            for param_value in values:
                for flex_location in locations_to_compute:
                    scenario_name = create_flex_scenario_name(
                        param_type, param_value, flex_location, base_model_info["name"]
                    )
                    output_dir = os.path.join(OUTPUT_BASE_DIR, "flex_scenarios", scenario_name)
                    os.makedirs(output_dir, exist_ok=True)
                    
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
                        #flex_start_time = get_flex_time_hours(scenario["duration_minutes"])
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
                        
                        # Save KPIs (folder name already encodes the scenario, no need to repeat it in the file name)
                        kpi_file = os.path.join(output_dir, "kpis.json")
                        simulation_tool.save_flex_kpis_as_json(filename=kpi_file)
                        
                        # Save metadata
                        metadata_file = os.path.join(output_dir, "metadata.json")
                        
                        # Build base_model_params based on model structure
                        base_model_params = {
                            "num_users": base_model_info["num_users"],
                            "power": base_model_info["power"],
                        }
                        if "plugin_alpha" in base_model_info:
                            base_model_params["plugin_alpha"] = base_model_info["plugin_alpha"]
                        else:
                            base_model_params["plugin_alpha_home"] = base_model_info.get("plugin_alpha_home", "N/A")
                            base_model_params["plugin_alpha_work"] = base_model_info.get("plugin_alpha_work", "N/A")
                        
                        metadata = {
                            "flex_param_type": param_type,
                            "flex_param_value": param_value,
                            "flex_location": flex_location,
                            "base_model": base_model_info["name"],
                            "base_model_params": base_model_params,
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
    print("\n" + "="*120)
    print("  PHASE 1.5: COMPUTING BASE FLEXIBILITIES FOR ALL MODELS")
    print("="*120)
    
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
        # Handle beide alte und neue Modell-Struktur
        if "plugin_alpha" in model:
            plugin_alpha_info = f"Alpha: {model['plugin_alpha']}"
        else:
            plugin_alpha_info = f"Alpha Home: {model.get('plugin_alpha_home', 'N/A')}, Alpha Work: {model.get('plugin_alpha_work', 'N/A')}"
        print(f"    Users: {model['num_users']}, {plugin_alpha_info}, Power: {model['power']} kW")
        
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
            
            # FÃ¼r jede Location
            for flex_location in locations_to_compute:
                scenario_name = f"{scenario_base_name}_{flex_location.lower()}"
                
                print(f"\n    {scenario_name}")
                print(f"      Duration: {BASE_SCENARIO['duration_minutes']}min, Activation: {BASE_SCENARIO['activation_time_percent']}%, Location: {flex_location}")
                
                try:
                    # Berechne FlexibilitÃ¤t mit BASE_SCENARIO Parametern
                    #flex_start_time = get_flex_time_hours(BASE_SCENARIO["duration_minutes"])
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
                    
                    # Save KPIs (folder name already encodes the scenario, no need to repeat it in the file name)
                    kpi_file = os.path.join(output_dir, "kpis.json")
                    simulation_tool.save_flex_kpis_as_json(filename=kpi_file)
                    
                    # Save metadata
                    metadata_file = os.path.join(output_dir, "metadata.json")
                    
                    # Build model_params based on model structure
                    model_params = {
                        "name": model_name,
                        "num_users": model["num_users"],
                        "power": model["power"],
                    }
                    if "plugin_alpha" in model:
                        model_params["plugin_alpha"] = model["plugin_alpha"]
                    else:
                        model_params["plugin_alpha_home"] = model.get("plugin_alpha_home", "N/A")
                        model_params["plugin_alpha_work"] = model.get("plugin_alpha_work", "N/A")
                    
                    metadata = {
                        "scenario": scenario_name,
                        "model_params": model_params,
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

# ============================================================================
# HAUPTPROGRAMM
# ============================================================================

def main():
    print("\n" + "="*120)
    print("  PARAMETER VARIATION SCENARIO GENERATOR - STRUCTURED")
    print("="*120)
    
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
    
    print(f"\n{'='*120}")
    print(f"  Models computed: {len(models)}")
    print(f"{'='*120}")
    
    # PHASE 1.5: Compute base flexibilities for all models
    base_flexibilities = compute_base_flexibilities(models)
    
    print(f"\n{'='*120}")
    print(f"  Base flexibilities computed: {base_flexibilities}")
    print(f"{'='*120}")
    
    # PHASE 2: Compute flex scenarios ONLY on basis models (wenn MODEL_VARIATIONS leer ist)
    # Nur wenn keine Variationen definiert sind, berechne Flex-Szenarien auf den Basis-Modellen
    total_flex_scenarios = 0
    
    if not any(MODEL_VARIATIONS.values()):
        # Find base models only when using base scenario
        base_models = [model for model in models if "basis" in model["name"]]
        
        if base_models:
            print(f"\n  Berechne Flex-Szenarien für Basis-Modelle...")
            for base_model in base_models:
                # Überprüfe dass die Basis-Parameter im Modellnamen enthalten sind
                users_str = str(BASIS_MODEL_PARAMS["num_users"])
                alpha_str = str(BASIS_MODEL_PARAMS["plugin_alpha"]).replace(".", "_")
                power_str = str(BASIS_MODEL_PARAMS["power"])
                
                expected_params = f"users{users_str}_alpha{alpha_str}_power{power_str}"
                
                if expected_params in base_model["name"]:
                    print(f"\n  Base model found: {base_model['name']}")
                    print(f"    Parameters OK: {expected_params}")
                    flex_scenarios = compute_flex_scenarios(base_model)
                    total_flex_scenarios += flex_scenarios
                else:
                    print(f"\n  WARNING: Base model name mismatch!")
                    print(f"    Expected: {expected_params}")
                    print(f"    Found in name: {base_model['name']}")
            
            print(f"\n{'='*120}")
            print(f"SUMMARY")
            print(f"{'='*120}")
            print(f"Models computed: {len(models)}")
            print(f"Base models: {len(base_models)} (Home and Work focused)")
            print(f"Base flexibilities computed (for all models): {base_flexibilities}")
            print(f"Flex scenarios computed (on basis models): {total_flex_scenarios}")
            print(f"Output directory: {OUTPUT_BASE_DIR}")
            print(f"{'='*120}")
        else:
            print(f"\n  ERROR: Base models not found!")
    else:
        print(f"\n  Model variations defined - skipping flex scenarios on basis models")
        print(f"  (Flex scenarios nur für basis models wenn MODEL_VARIATIONS leer ist)")
        print(f"{'='*120}")
        print(f"SUMMARY")
        print(f"{'='*120}")
        print(f"Models computed: {len(models)}")
        print(f"Base flexibilities computed (for all models): {base_flexibilities}")
        print(f"Output directory: {OUTPUT_BASE_DIR}")
        print(f"{'='*120}")



if __name__ == "__main__":
    main()

