import matplotlib.pyplot as plt
import numpy as np

import analysis_methods.plot_Charging
from analysis_methods.load_data import *
from analysis_methods.plot_Charging import *
from simulation_model.Run import *
from SimulationTool.simulation import *

def compare_parking_and_pluginduration():
   parking_duration = open_file('dataCharging/modelData/parking_durations')
   ch_modus = "all"
   modus = "plugin_duration"

   VehicleList = open_file('dataCharging/modelData/VehicleList2')
   all_lists_name = "dataCharging/modelData/allLists" + str(ch_modus)

   allLists = open_file(all_lists_name)
   plug_in_duration = allLists[8]

import os, json, re, hashlib

ID_LEN = 10
MAPPING_FILENAME = "scenario_mapping.json"

def slugify(s: str) -> str:
    s = re.sub(r'[^0-9A-Za-z_\-]+', '_', str(s))
    s = re.sub(r'_+', '_', s).strip('_')
    return s or "x"

def short_id(payload) -> str:
    if isinstance(payload, dict):
        raw = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    else:
        raw = str(payload)
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:ID_LEN]

def ensure_dir(path):
    os.makedirs(path, exist_ok=True)

def update_mapping(save_dir, sid, meta):
    path = os.path.join(save_dir, MAPPING_FILENAME)
    mapping = {}
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                mapping = json.load(f)
        except:
            mapping = {}
    mapping[sid] = meta
    with open(path, "w", encoding="utf-8") as f:
        json.dump(mapping, f, indent=2, ensure_ascii=False)

def plugin_validation(
    ch_modus="lama",
    histogram_comparision=True,
    all_lists_computation=False,
    cluster_model=False,
    cluster_real=False,
    nocs_comparision=False,
    cluster_share=False,
    save_path="plugin/",
    Vehiclelist="dataCharging/modelData/VehicleList2",
    scenario_id=None
):
    import re
    import json

    if scenario_id is None:
        # falls nicht übergeben → immer kurze ID erzeugen
        try:
            plugin_name = settingsContainer.getSettingsAsJson()['plug-in']
        except:
            plugin_name = "plugin"
        scenario_id = short_id(plugin_name)

    stats_filename   = f"stats_{scenario_id}.json"
    hist_filename    = f"hist_{scenario_id}.png"
    cluster_filename = f"clusters_{scenario_id}.png"

    simulation_tool = start_tool()

    if True:
        if Vehiclelist is None:
            simulation_tool = start_tool()
            simulation_tool.run_model()
            simulation_tool.save_model()
            json_settings = settingsContainer.getSettingsAsJson()['plug-in']
            save_list(simulation_tool.model_data.VehicleLists,
                      os.path.join(save_path, f"VehicleList_{scenario_id}"))
            VehicleList = open_file(os.path.join(save_path, f"VehicleList_{scenario_id}"))
        else:
            VehicleList = open_file(Vehiclelist)

        if ch_modus == "home":
            filename_UK = "electric-chargepoint-analysis-2017-raw-domestics-data.csv"
        elif ch_modus == "public":
            filename_UK = "electric-chargepoint-analysis-2017-public-data.csv"
        elif ch_modus == "lama":
            filename_UK = "Ladedaten_Marquardt_Anonymisiert / anonym_data"

        if ch_modus == "_Obelis":
            ch_modus2 = "work"
            file_start = "Obelis_"
        elif ch_modus == "lama":
            ch_modus2 = "work"
            file_start = "lama_"
        else:
            ch_modus2 = ch_modus
            file_start = "UK_Charging_"

        all_lists_name = "dataCharging/modelData/allLists" + str(ch_modus)

        if all_lists_computation:
            allLists = compute_histogram_lists(VehicleList,
                                               start_day=settingsContainer.getStartDay(),
                                               ch_modus=ch_modus2)
            save_list(allLists, all_lists_name)
        else:
            allLists = open_file(all_lists_name)

    if histogram_comparision:
        #plt.plot([1,2,3,4,5,6,7])

        plt.close('all')  # alte Figures schließen
        fig = plt.figure(figsize=(14, 10))

        plot_list = [331,332,333,334,335,336,337,338,339]
        i = 0

        for modus in [
            "start_time","ch_end_time","ch_duration","plugin_end_time",
            "plugin_duration","energy_per_session",
            "ch_durations_per_interval","energies_per_interval"
        ]:
            plug_in_duration = (modus == "plugin_duration")

            plot_histogramm_comparison(
                modus, ch_modus, plot_alone=False,
                plug_in_duration=plug_in_duration, withlabels=True,
                filename_UK=filename_UK, bins=24, interval=0,
                plot1=plt.subplot(plot_list[i]),
                allLists=allLists,
                compute_all_lists=False,
                save_computations=True,
                load_data=False
            )
            i += 1

            if modus == "plugin_duration":
                if ch_modus == "lama":
                    open_filename = f"dataCharging/alreadyLoaded/{file_start}work_{modus}s"
                else:
                    open_filename = f"dataCharging/alreadyLoaded/{file_start}{ch_modus}_{modus}s"

                data = open_file(open_filename)
                real_data = np.array([d.total_seconds() for d in data])
                real_mean = float(real_data.mean())
                real_q = np.quantile(real_data,[0.05,0.25,0.5,0.75,0.95,0.99])

                model_data = allLists[8]
                model_mean = np.mean(model_data)/3600
                model_q = np.quantile(model_data,[0.05,0.25,0.5,0.75,0.95,0.99])

                output = {
                    "real": {
                        "mean": real_mean,
                        "q05": real_q[0], "q25": real_q[1], "q50": real_q[2],
                        "q75": real_q[3], "q95": real_q[4], "q99": real_q[5]
                    },
                    "model": {
                        "mean": model_mean,
                        "q05": model_q[0], "q25": model_q[1], "q50": model_q[2],
                        "q75": model_q[3], "q95": model_q[4], "q99": model_q[5]
                    }
                }

                bundle = {
                    "output": output,
                    "json_settings": json.dumps(output, indent=4, ensure_ascii=False)
                }

                stats_path = os.path.join(save_path, stats_filename)
                with open(stats_path,"w",encoding="utf-8") as f:
                    json.dump(bundle,f,indent=4,ensure_ascii=False)

        plt.savefig(os.path.join(save_path, hist_filename))
        #plt.show()
        plt.close(fig)

if __name__ == "__main__":
    import json
    import os
    import itertools
    import re

    SAVE_PATH = "../../plugin/"
    os.makedirs(SAVE_PATH, exist_ok=True)

    with open("../../SimulationTool/SimulationTool_Settings.json", "r", encoding="utf-8") as f:
        base_data = json.load(f)

    def clean(s):
        return re.sub(r"[^0-9A-Za-z_\-]", "_", str(s))

    # -------------------------------------------------
    # FIXE BASISWERTE
    # -------------------------------------------------
    BASE_HOME = 5
    BASE_PUBLIC = 0.1
    BASE_WORK = 0.1
    BASE_SOC_AFTER = 30
    BASE_SOC_PLUG = 40
    BASE_CH = 0

    alpha_home = [ 10]
    alpha_public = [0.2]
    alpha_work = [1.5]

    soc_after_values = [20,30]
    soc_plug_values = [20,30]
    charge_values = [ 1]

    def run_scenario(data, scenario_name):
        scenario_dir = os.path.join(SAVE_PATH, scenario_name)
        os.makedirs(scenario_dir, exist_ok=True)

        settings_path = os.path.join(scenario_dir, f"Settings_{scenario_name}.json")
        with open(settings_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

        simulation_tool = start_tool(settings_file=settings_path)
        simulation_tool.run_model()
        simulation_tool.save_model(
            filename=os.path.join(scenario_dir, f"model_{scenario_name}")
        )

        save_list(
            simulation_tool.model_data.VehicleLists,
            os.path.join(scenario_dir, f"VehicleList_{scenario_name}")
        )

        plugin_validation(
            ch_modus="home",
            all_lists_computation=True,
            save_path=scenario_dir,
            Vehiclelist=os.path.join(scenario_dir, f"VehicleList_{scenario_name}")
        )

    # =============================================================
    # 0) BASELINE: PLUG_IN_SIMPLE = True
    # =============================================================
    data = json.loads(json.dumps(base_data))

    data["plug-in"]["PLUG_IN_SIMPLE"] = True

    scenario_name = "BASE_SIMPLE_TRUE"
    if False:
        run_scenario(data, scenario_name)

    # =============================================================
    # A) ALLE ALPHA-KOMBINATIONEN (3D Kombination)
    # =============================================================
    if False:
        for home_val, pub_val, work_val in itertools.product(
            alpha_home, alpha_public, alpha_work
        ):

            data = json.loads(json.dumps(base_data))
            data["plug-in"]["PLUG_IN_SIMPLE"] = False

            data["plug-in"]["PLUG_IN_ALPHA_HOME"] = [home_val]
            data["plug-in"]["PLUG_IN_ALPHA_PUBLIC"] = [pub_val]
            data["plug-in"]["PLUG_IN_ALPHA_WORK"] = [work_val]

            data["plug-in"]["MIN_SOC_AFTER_LAST_TRIP_ACTIVE"] = False
            data["plug-in"]["MIN_SOC_PLUG_IN"] = BASE_SOC_PLUG
            data["plug-in"]["CHARGING_EVERY_DAY_AFTER_LAST_TRIP"] = BASE_CH

            scenario_name = clean(
                f"A_HOME{home_val}_PUB{pub_val}_WORK{work_val}"
            )
            run_scenario(data, scenario_name)

    # =============================================================
    # B) Nur MIN_SOC_AFTER_LAST_TRIP variieren
    # =============================================================
    if False:
        for soc_after in soc_after_values:
            for soc_plug in soc_plug_values:
                data = json.loads(json.dumps(base_data))
                data["plug-in"]["PLUG_IN_SIMPLE"] = False
    
                data["plug-in"]["PLUG_IN_ALPHA_HOME"] = [BASE_HOME]
                data["plug-in"]["PLUG_IN_ALPHA_PUBLIC"] = [BASE_PUBLIC]
                data["plug-in"]["PLUG_IN_ALPHA_WORK"] = [BASE_WORK]

                data["plug-in"]["MIN_SOC_AFTER_LAST_TRIP_ACTIVE"] = True
                data["plug-in"]["MIN_SOC_AFTER_LAST_TRIP"] = soc_after

                data["plug-in"]["MIN_SOC_PLUG_IN"] = soc_plug
                data["plug-in"]["CHARGING_EVERY_DAY_AFTER_LAST_TRIP"] = BASE_CH

                scenario_name = clean(f"B4_SOC_AFTER{soc_after}_SOC_PLUG{soc_plug}")
                run_scenario(data, scenario_name)
    if False:
    # =============================================================
        # C) Nur MIN_SOC_PLUG_IN variieren
        # =============================================================
        for soc_plug in soc_plug_values:

            data = json.loads(json.dumps(base_data))
            data["plug-in"]["PLUG_IN_SIMPLE"] = False

            data["plug-in"]["PLUG_IN_ALPHA_HOME"] = [BASE_HOME]
            data["plug-in"]["PLUG_IN_ALPHA_PUBLIC"] = [BASE_PUBLIC]
            data["plug-in"]["PLUG_IN_ALPHA_WORK"] = [BASE_WORK]

            data["plug-in"]["MIN_SOC_AFTER_LAST_TRIP_ACTIVE"] = False
            data["plug-in"]["MIN_SOC_AFTER_LAST_TRIP"] = BASE_SOC_AFTER

            data["plug-in"]["MIN_SOC_PLUG_IN"] = soc_plug
            data["plug-in"]["CHARGING_EVERY_DAY_AFTER_LAST_TRIP"] = BASE_CH

            scenario_name = clean(f"C2_SOC_PLUG{soc_plug}")
            run_scenario(data, scenario_name)
    if True:
    # =============================================================
    # D) Nur CHARGING_EVERY_DAY_AFTER_LAST_TRIP variieren
    # =============================================================
        for ch_val in charge_values:

            data = json.loads(json.dumps(base_data))
            data["plug-in"]["PLUG_IN_SIMPLE"] = False

            data["plug-in"]["PLUG_IN_ALPHA_HOME"] = [BASE_HOME]
            data["plug-in"]["PLUG_IN_ALPHA_PUBLIC"] = [BASE_PUBLIC]
            data["plug-in"]["PLUG_IN_ALPHA_WORK"] = [BASE_WORK]

            data["plug-in"]["MIN_SOC_AFTER_LAST_TRIP_ACTIVE"] = False
            data["plug-in"]["MIN_SOC_AFTER_LAST_TRIP"] = BASE_SOC_AFTER

            data["plug-in"]["MIN_SOC_PLUG_IN"] = BASE_SOC_PLUG
            data["plug-in"]["CHARGING_EVERY_DAY_AFTER_LAST_TRIP"] = ch_val

            scenario_name = clean(f"D4_CH{ch_val}")
            run_scenario(data, scenario_name)
