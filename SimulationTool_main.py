import os.path

from test import *

def run_model_and_visualize_flex():
    # settings adapted in SimulationTool_Settings.json
    simulation_tool = start_tool()
    simulation_tool.run_model()
    # as alternative for running model:
    # simulation_tool load_model()
    simulation_tool.calculate_flexibility()
    simulation_tool.visualize_flexibility()


def run_model_and_visualize_several_times():
    # settings adapted in SimulationTool_Settings.json
    # this method only works if all charging strategies are computed
    # --> parameter CHARGING_STRATEGIES includes all 3 charging strategies
    # --> parameter Heuristic includes 2 parameters
    simulation_tool = start_tool()
    simulation_tool.run_model()

    # as alternative for running model:
    # simulation_tool load_model()
    simulation_tool.calculate_flexibility()
    # model is saved
    simulation_tool.save_model()
    for strat_pos in [0,1,2]:
        for modus_pos in [0,1]:
            simulation_tool.visualize_flexibility(viz_charging_strategy=[strat_pos],  viz_heuristic= 1, viz_modus=modus_pos)


def load_model_and_calculate_several_flexibilities_with_user_defined_analysis():
    simulation_tool = start_tool()
    simulation_tool.load_model()
    # as alternative for loading model:
    # simulation_tool.run_model()
    simulation_tool.calculate_flexibility(spontan_flex=True)

    #--------------------------------------------------
    # user_defined section
    spontanflex = simulation_tool.flexibility_object.flex_list[0][0]
    #--------------------------------------------------

    simulation_tool.calculate_flexibility(spontan_flex=False, flex_activation_time = datetime.timedelta(0))

    # --------------------------------------------------
    # user_defined section
    fixdateflex = simulation_tool.flexibility_object.flex_list[0][0]
    #---------------------------------------------------

    # user defined section for checking if  flexibility_calc with activation time = 0 return the same like spontanous flexibility_calc
    # method is written in test file
    compare_fixDate_with_spontanflex(fixdateflex, spontanflex)


def run_model_and_calculate_several_different_flexibilities():
    # settings adapted in SimulationTool_Settings.json
    # Presumption: Charging strategies has to include at least two charging strategies to compute

    simulation_tool = start_tool()
    simulation_tool.run_model()
    # as alternative for running model:
    # simulation_tool load_model()

    # example for defining flexibility_calc specifications within method
    # spontanous flexibility_calc (with risk)  at 13:20 for a duration of 15 minutes on Tuesdays
    # considering only charging sessions at home.
    simulation_tool.calculate_flexibility(risk = True, spontan_flex = True,
                                          flex_start_time = datetime.timedelta(hours = 13, minutes = 20),
                                          flex_duration = datetime.timedelta(minutes = 15), flex_place = "Home",
                                          flex_at_number_of_day=-1, flex_at_daytype = 2)
    # visualize for charging strategy one and two
    simulation_tool.visualize_flexibility(viz_charging_strategy=[0])
    simulation_tool.visualize_flexibility(viz_charging_strategy=[1])
    simulation_tool.calculate_flexibility(risk = True, spontan_flex = False,
                                          flex_start_time = datetime.timedelta(hours = 13, minutes = 20),
                                          flex_duration = datetime.timedelta(minutes = 15), flex_place = "Home",
                                          flex_at_number_of_day=-1, flex_at_daytype = 2)
    simulation_tool.visualize_flexibility(viz_charging_strategy=[0])
    simulation_tool.visualize_flexibility(viz_charging_strategy=[1])

def testing():
    # settings adapted in SimulationTool_Settings.json
    # Presumption: Charging strategies has to include at least two charging strategies to compute

    simulation_tool = start_tool()
    #simulation_tool.run_model()
    #simulation_tool.save_model()
    # as alternative for running model:
    simulation_tool.load_model()

    # example for defining flexibility_calc specifications within method
    # spontanous flexibility_calc (with risk)  at 13:20 for a duration of 15 minutes on Tuesdays
    # considering only charging sessions at home.
    simulation_tool.calculate_flexibility(risk = True, spontan_flex = True,
                                          flex_start_time = datetime.timedelta(hours = 20, minutes = 20),
                                          flex_duration = datetime.timedelta(minutes = 15), flex_place = "Home",
                                          flex_at_number_of_day=-1, flex_at_daytype = 2)
    #simulation_tool.flexibility_object.flex_list[3][3].compute_kpis()

    # visualize for charging strategy one and two
    simulation_tool.visualize_flexibility(viz_charging_strategy=[0])

    simulation_tool.save_flex_kpis_as_json(filename = "hi")


## running one scenario
def run_scenario(scenario_name, model_name, flex_spec, simulation_tool, base_dir = "scenarios/", load_model = False):
    scenario_dir = os.path.join(base_dir, scenario_name)
    model_path = os.path.join( "models/", model_name)

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

# python
def run_all_scenarios(simulation_tool, model_name, base_dir="scenarios/"):

    # Modell nur einmal laden 🚀
    model_path = os.path.join("models/", model_name)

    if os.path.exists(f"{model_path}.pkl"):
        print(f"Modell geladen: {model_path}.pkl")
        simulation_tool.load_model(filename=model_path)
    else:
        print(f"Modell nicht gefunden, berechne Modell: {model_name}")
        simulation_tool.run_model(run_name=model_name)
        simulation_tool.save_model(filename=model_path)
        print(f"Modell berechnet und gespeichert: {model_path}.pkl")

        # Sicherstellen, dass das Szenario-Verzeichnis für dieses Modell existiert
    scenarios_root = os.path.join(base_dir, model_name)
    os.makedirs(scenarios_root, exist_ok=True)

    # Parameterbereiche
    spontanflex_values = [False]
    start_times = np.arange(15.0, 23, 20)
    duration_times = [15]
    act_times = [0, 23, 1, 3, 6, 12]
    # Batch initialisieren
    current_batch = []

    for spontanflex in spontanflex_values:
        for duration in duration_times:
            for start_time in start_times:
                for act_time in act_times:
                    flex_spec = {
                        "flexibility_specifications": {
                            "SPONTANFLEX": spontanflex,
                            "RISK": 1,
                            "FLEX_START_TIME": round(start_time, 2),
                            "FLEX_DURATION": duration,
                            "FLEX_ACTIVATION_TIME": act_time,
                            "FLEX_PLACE": "Home",
                            "FLEX_AT_NUMBER_OF_DAY": -1,
                            "FLEX_AT_NUMBER_OF_RUN": -1,
                            "FLEX_AT_DAYTYPE": -1,
                        }
                    }

                    scenario_name = f"act{act_time}_t{start_time:.2f}".replace('.', '_')
                    print(f"Starte Szenario: {scenario_name} duration={duration}, START_TIME={start_time:.2f})")

                    run_scenario(
                            scenario_name=scenario_name,
                            model_name=model_name,
                            flex_spec=flex_spec,
                            simulation_tool=simulation_tool,
                            base_dir=scenarios_root,
                            load_model=False,
                        )

                    print(f"Szenario abgeschlossen und gespeichert: {os.path.join(base_dir, scenario_name)}\n")



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
    run_all_scenarios(simulation_tool = simulation_tool, model_name = "model_56")
    #testing()
    #load_model_and_calculate_several_flexibilities_with_user_defined_analysis()


# parameter units in SimulationTool_settings.json:
#duration, min_flex_time, min_delievery_time,: minutes
#flex_activation_time, flex_start time: hours