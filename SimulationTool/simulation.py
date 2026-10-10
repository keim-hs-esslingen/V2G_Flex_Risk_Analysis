from simulation_model.Run import *
from flexibility_calc.flex_object import *
import json
# matplotlib ist hier nicht notwendig, entfernt um Unused-import Warnung zu vermeiden

# settingsContainer hält globale Settings; importieren
from config.settings import settingsContainer

class Simulation:

    def __init__(self):
        self.settingsStructure = {
            "trip-generation": {"MINIMUM_SPEED", "MINIMUM_DISTANCE", "ENERGY_CONSUMPTION"},
            "user": {"USER_CLUSTER1_SHARE", "USER_CLUSTER2_SHARE", "WITH_CLUSTER"},
            "charging": {"CPCV"},
            "plug-in": {"PLUG_IN_ALPHA_PUBLIC", "PLUG_IN_ALPHA_WORK", "PLUG_IN_ALPHA_HOME", "PLUG_IN_SIMPLE", "MIN_SOC_AFTER_LAST_TRIP", "MIN_SOC_AFTER_LAST_TRIP_ACTIVE", "MIN_SOC_PLUG_IN", "WITHOUT_WORKING_STATION_ACCESS", "CHARGING_EVERY_DAY_AFTER_LAST_TRIP"},
            "model_specifications": {"NUMBER_OF_DAYS", "NUMBER_OF_USERS", "NUMBER_OF_RUNS", "START_DAY"},
            "flexibility_calculation": {"MIN_FLEX_TIME", "MIN_SOC", "SOC_TOL", "MAX_SOC", "MIN_CHARGING_RATE", "CHARGING_STRATEGIES", "HEURISTICS", "MIN_DELIEVERY_TIME", "SIMPLE_BOUNDARIES", "V2G_AVAILABILITY"},
            "flexibility_specifications": {"SPONTAN_FLEX", "FLEX_START_TIME", "FLEX_DURATION", "FLEX_ACTIVATION_TIME", "FLEX_PLACE", "RISK", "FLEX_AT_NUMBER_OF_DAY", "FLEX_AT_NUMBER_OF_RUN", "FLEX_AT_DAYTYPE"},
            "viz_flexibility_specifications": {"VIZ_CHARGING_STRATEGIES", "VIZ_HEURISTICS", "VIZ_MODUS", "VIZ_SHOW", "VIZ_SAVE", "VIZ_FILENAME"}
        }

        self.model_data: model_data = None
        self.flexibility_object = None
        self.settings = None
        self.times_momentary_potential = None
        self.capacities_momentary_potential = None
        self.file_name = None

        pass

    def save_model(self, filename = 'model'):
        save_list(self.model_data,filename)
        self.file_name = filename

    def load_model(self, filename = 'model'):
        self.model_data = open_file(filename)
        self.file_name = filename
        self.reset_settings()
        self.updateSettings(self.model_data.model_settings, as_dict = True)
        # model parameters overwritten by parameters of loaded model
        # happens in calculate flexibility_calc anyways


    def run_model(self, number_of_days = None, number_of_users = None, start_day = None, number_of_runs = None,
                  plugin_alpha_public = None, plugin_alpha_work = None, plugin_alpha_home = None, plugin_alpha_simple = None,
                  min_soc_after_last_trip = None, min_soc_after_last_trip_active = None, min_soc_plug_in = None,
                  without_working_station_access = None, charging_every_day_after_last_trip = None, run_name = "",
                  ch_filepath = None, ev_filepath = None):

        # reset parameters
        self.reset_settings()
        # define model specifications according to parameters, if not specified here
        if number_of_days == None:
            number_of_days = settingsContainer.getNumberOfDays()
        if number_of_users == None:
            number_of_users = settingsContainer.getNumberOfUsers()
        if number_of_runs == None:
            number_of_runs = settingsContainer.getNumberOfRuns()
        if start_day == None:
            start_day = settingsContainer.getStartDay()
        if plugin_alpha_public == None:
            plugin_alpha_public = settingsContainer.getPlugInAlphaPublic()
        if plugin_alpha_work == None:
            plugin_alpha_work = settingsContainer.getPlugInAlphaWork()
        if plugin_alpha_home == None:
            plugin_alpha_home = settingsContainer.getPlugInAlphaHome()
        if plugin_alpha_simple == None:
            plugin_alpha_simple = settingsContainer.getPlugInSimple()
        if min_soc_after_last_trip == None:
            min_soc_after_last_trip = settingsContainer.getMinSocAfterLastTrip()
        if min_soc_after_last_trip_active == None:
            min_soc_after_last_trip_active = settingsContainer.getMinSocAfterLastTripActive()
        if min_soc_plug_in == None:
            min_soc_plug_in = settingsContainer.getMinSocPlugIn()
        if without_working_station_access == None:
            without_working_station_access = settingsContainer.getWithoutWorkingStationAccess()
        if charging_every_day_after_last_trip == None:
            charging_every_day_after_last_trip = settingsContainer.getChargingEveryDayAfterLastTrip()
        if ev_filepath == None:
            ev_filepath = "SimulationTool/EVModels.csv"

        # set local model_specifications
        model_specifications = {"model_specifications": {"NUMBER_OF_DAYS": number_of_days,
                                                                  "NUMBER_OF_USERS": number_of_users,
                                                                  "NUMBER_OF_RUNS": number_of_runs,
                                                                  "START_DAY": start_day}}

        plugin_specifications =  {"plug-in" : {
                                                                    "PLUG_IN_ALPHA_PUBLIC": plugin_alpha_public,
                                                                    "PLUG_IN_ALPHA_WORK": plugin_alpha_work,
                                                                    "PLUG_IN_ALPHA_HOME": plugin_alpha_home,
                                                                    "PLUG_IN_SIMPLE": plugin_alpha_simple,
                                                                    "MIN_SOC_AFTER_LAST_TRIP": min_soc_after_last_trip,
                                                                    "MIN_SOC_AFTER_LAST_TRIP_ACTIVE": min_soc_after_last_trip_active,
                                                                    "MIN_SOC_PLUG_IN": min_soc_plug_in,
                                                                    "WITHOUT_WORKING_STATION_ACCESS": without_working_station_access,
                                                                    "CHARGING_EVERY_DAY_AFTER_LAST_TRIP": charging_every_day_after_last_trip
                                                         }}

        settingsContainer.updateSettings(model_specifications, as_dict=True)
        settingsContainer.updateSettings(plugin_specifications, as_dict=True)

        # model_data object
        self.model_data = run(number_of_days, number_of_users, start_day, number_of_runs, run_name, ch_filepath, ev_filepath)


    def calculate_flexibility(self, spontan_flex = None, risk = None, flex_start_time = None, flex_duration = None,
                              flex_activation_time = None, flex_place = None, flex_at_number_of_day=None,
                              flex_at_number_of_run = None, flex_at_daytype=None, flex_specifications = None):
        # reset parameters according to current model data
        self.reset_settings()
        settingsContainer.updateSettings(self.model_data.model_settings, as_dict=True)
        # define flexibility_calc calculation specifications according to parameters, if not specified here

        if flex_specifications is not None:
            flexibility_specifications = flex_specifications
        else:
            # set local flexibility_specifications
            flexibility_specifications = {"flexibility_specifications": {"SPONTANFLEX": spontan_flex,
                                                                         "RISK": risk,
                                                                         "FLEX_START_TIME": flex_start_time,
                                                                         "FLEX_DURATION": flex_duration,
                                                                         "FLEX_ACTIVATION_TIME": flex_activation_time,
                                                                         "FLEX_PLACE": flex_place,
                                                                        "FLEX_AT_NUMBER_OF_DAY": flex_at_number_of_day,
                                                                        "FLEX_AT_NUMBER_OF_RUN": flex_at_number_of_run,
                                                                         "FLEX_AT_DAYTYPE": flex_at_daytype
                                                                         }
                                          }

        settingsContainer.updateSettings(flexibility_specifications, as_dict=True)

        #if spontan_flex == None:
        spontan_flex = settingsContainer.getSpontanflex()
        #if risk == None:
        risk = settingsContainer.getRisk()
        #if flex_start_time == None:
        flex_start_time = settingsContainer.getFlexStartTime()
        #if flex_duration == None:
        flex_duration = settingsContainer.getFlexDuration()
        #if flex_activation_time == None:
        flex_activation_time = settingsContainer.getFlexActivationTime()
        #if flex_place == None:
        flex_place = settingsContainer.getFlexPlace()
        ##if ChargingStrategies != None:
        ##    self.updateSettings({"CHARGING_STRATEGIES": ChargingStrategies}, as_dict=True)
        ##else:
        ##    ChargingStrategies = settingsContainer.getChargingStrategies()
        ##if heuristics != None:
        ##    self.updateSettings({"HEURISTICS": heuristics}, as_dict=True)
        ##else:
        ##    heuristics = settingsContainer.getHeuristics()
        #if flex_at_number_of_day == None:
        flex_at_number_of_day = settingsContainer.getFlexAtNumberOfDay()
        #if flex_at_number_of_run == None:
        flex_at_number_of_run = settingsContainer.getFlexAtNumberOfRun()
        #if flex_at_daytype== None:
        flex_at_daytype = settingsContainer.getFlexAtDaytype()

        if settingsContainer.getNumberOfDays()>10 and risk == True:
            ignore_first_days = 10
        else:
            ignore_first_days = 0
        # intialize flexibility_calc object
        self.flexibility_object = flex_object(spontan_flex, risk, flex_start_time, flex_duration, flex_activation_time,
                                              flex_place, flex_at_number_of_day, flex_at_number_of_run,
                                              flex_at_daytype, ignore_first_days= ignore_first_days)
        self.flexibility_object.compute_flexibility(self.model_data.DayLists, settingsContainer.getNumberOfDays(),
                                        settingsContainer.getStartDay())


    def calculate_dependant_flexibility(self, spontan_flex = None, risk = None, flex_start_time = None, flex_duration = None,
                              flex_activation_time = None, flex_place = None, flex_at_number_of_day=None,
                              flex_at_number_of_run = None, flex_at_daytype=None, flex_start_time2 = None, flex_duration2 = None,
                                         flex_activation_time2 = None, flex_place2 = None, flex_at_number_of_day2 = None,
                                         flex_at_number_of_run2 = None, flex_at_daytype2=None, co2 = True,
                                        concrete_strat = 1, flex_dependant_strat = False) :
        self.reset_settings()
        settingsContainer.updateSettings(self.model_data.model_settings, as_dict=True)
        # define flexibility_calc calculation specifications according to parameters, if not specified here

        if spontan_flex == None:
            spontan_flex = settingsContainer.getSpontanflex()
        if risk == None:
            risk = settingsContainer.getRisk()
        if flex_start_time == None:
            flex_start_time = settingsContainer.getFlexStartTime()
        if flex_duration == None:
            flex_duration = settingsContainer.getFlexDuration()
        if flex_activation_time == None:
            flex_activation_time = settingsContainer.getFlexActivationTime()
        if flex_place == None:
            flex_place = settingsContainer.getFlexPlace()
        # if ChargingStrategies != None:
        #    self.updateSettings({"CHARGING_STRATEGIES": ChargingStrategies}, as_dict=True)
        # else:
        #    ChargingStrategies = settingsContainer.getChargingStrategies()
        # if heuristics != None:
        #    self.updateSettings({"HEURISTICS": heuristics}, as_dict=True)
        # else:
        #    heuristics = settingsContainer.getHeuristics()
        if flex_at_number_of_day == None:
            flex_at_number_of_day = settingsContainer.getFlexAtNumberOfDay()
        if flex_at_number_of_run == None:
            flex_at_number_of_run = settingsContainer.getFlexAtNumberOfRun()
        if flex_at_daytype == None:
            flex_at_daytype = settingsContainer.getFlexAtDaytype()

            # set local flexibility_specifications
        flexibility_specifications = {"flexibility_specifications": {"SPONTANFLEX": spontan_flex,
                                                                     "RISK": risk,
                                                                     "FLEX_START_TIME": flex_start_time,
                                                                     "FLEX_DURATION": flex_duration,
                                                                     "FLEX_ACTIVATION_TIME": flex_activation_time,
                                                                     "FLEX_PLACE": flex_place,
                                                                     "FLEX_AT_NUMBER_OF_DAY": flex_at_number_of_day,
                                                                     "FLEX_AT_NUMBER_OF_RUN": flex_at_number_of_run,
                                                                     "FLEX_AT_DAYTYPE": flex_at_daytype,
                                                                     "FLEX_DEPENDANT": True
                                                                     }
                                      }
        settingsContainer.updateSettings(flexibility_specifications, as_dict=True)
        if settingsContainer.getNumberOfDays() > 10 and risk == True:
            ignore_first_days = 10
        else:
            ignore_first_days = 0
        # intialize flexibility_calc object
        self.flexibility_object = flex_object(spontan_flex, risk, flex_start_time, flex_duration, flex_activation_time,
                                              flex_place, flex_at_number_of_day, flex_at_number_of_run,
                                              flex_at_daytype, ignore_first_days, False)
        self.flexibility_object.compute_flexibility(self.model_data.DayLists, settingsContainer.getNumberOfDays(),
                                                    settingsContainer.getStartDay())
        if flex_dependant_strat == False and concrete_strat == None and co2:
            print("Error: in co2-use case at least flex_dependant_strat should be True")
            flex_dependant_strat = True
        self.flexibility_object2 = flex_object(spontan_flex, risk, flex_start_time2, flex_duration2, flex_activation_time2,
                                              flex_place2, flex_at_number_of_day2, flex_at_number_of_run2,
                                              flex_at_daytype2, ignore_first_days, True, co2 )
        self.flexibility_object2.compute_flexibility(self.model_data.DayLists, settingsContainer.getNumberOfDays(),
                                                    settingsContainer.getStartDay(), self.flexibility_object,
                                                     concrete_strat, flex_dependant_strat)
        self.flexibility_object2.visualize_flexibility([1], 0, 1, False,
                                                       True, "hi", flex_dependant = True,
                                                       strat_pos_dep = 1, modus_pos_dep=1)


    def calculate_momentary_flexibility(self, times=None, daytype=1,
                                        strategy_position=0, energy=True, dependant_of_strat=None, lastday=True):
        self.reset_settings()
        settingsContainer.updateSettings(self.model_data.model_settings, as_dict=True)
        # if not fixednumberofday:

        # Vorsichtiges Handling des Default-Arguments: wenn None, initialisiere mit Standard-Grid
        if times is None:
            times = [datetime.timedelta(hours=i / 2) for i in range(48)]

        start = int(settingsContainer.getStartDay())
        while start != daytype:
            start += 1
        start -= int(settingsContainer.getStartDay())
        while start + 7 < settingsContainer.getNumberOfDays():
            start += 7

        mom_list = compute_mom_potential(self.model_data.DayLists, times, [strategy_position],
                                         settingsContainer.getNumberOfDays(),
                                         1, settingsContainer.getStartDay(),
                                         Flex_place=settingsContainer.getFlexPlace(), numberofday=start, Daytype=daytype,
                                         minus_strat=dependant_of_strat)
        # first zero for strat pos (always zero, as only one strategy is calculated), second zero for run/day (also only one certain day calculated)
        if energy:
            energy_pos = 0
        else:
            energy_pos = 1
        # if modus == "negative":
        #    modus_pos = 0
        # else: #modus == "positive":
        #  modus_pos = 1
        self.times_momentary_potential = times
        self.capacities_momentary_potential = switch_sign(np.array(mom_list[0][0][energy_pos]).transpose(1, 0))

    def get_momentary_potential_data(self):
        return self.times_momentary_potential, self.capacities_momentary_potential

    def visualize_flexibility(self, viz_charging_strategy = None, viz_heuristic = None, viz_modus = None,
                              viz_safe = None, filename = None, viz_show = None, plot_momentary = False,
                              withlines = True, plot_labels = True):
        # no reset of parameters, as this method always works with current flexibility_calc object
        # and is only allowed to call, if flexibility_calc object has been defined
        if self.flexibility_object == None:
            return
        if viz_charging_strategy == None:
            viz_charging_strategy = settingsContainer.getVisChargingStrategies()
        if viz_heuristic == None:
            viz_heuristic = settingsContainer.getVisHeuristics()
        if viz_modus == None:
            viz_modus= settingsContainer.getVisHeuristics()
        if viz_safe == None:
            viz_safe = settingsContainer.getVisSave()
        if viz_show == None:
            viz_show = settingsContainer.getVisShow()
        if filename == None:
            filename = settingsContainer.getVisFilename()
        self.flexibility_object.visualize_flexibility(viz_charging_strategy, viz_heuristic, viz_modus, viz_safe,
                                                      viz_show, filename ,
                                                      plot_momentary_potential = plot_momentary,
                                                      withlines = withlines, plot_labels=plot_labels)

    def reset_settings(self):
        settingsContainer.updateSettings(self.settings, True)

    def set_settings(self, settings_new, as_dict = True):
        self.reset_settings()
        settingsContainer.updateSettings(settings_new, as_dict)
        self.settings = settingsContainer.getSettingsAsJson()

    def mapSettings(self, frontendSettings):
        #mapps the settngs from the Frontend to the Backend Settings defined in self.settingsStructure
        _json = json.loads('{"trip-generation": {}, "plug-in": {}, "model_specifications": {}, "flexibility_calculation": {}, "flexibility_specifications": {}, "viz_flexibility_specifications":{}}')
        print(_json)

        for category in self.settingsStructure:
            for setting in self.settingsStructure[category]:
                for frontendCategory in frontendSettings:
                    for frontendSetting in frontendSettings[frontendCategory]:
                        if frontendSetting == setting:
                            print(category, frontendSetting, setting)
                            data = {setting : frontendSettings[frontendCategory][frontendSetting]}
                            print(data)

                            _json[category].update(data)




                            ##if result[0][category]:
                             ##   result[0][category].append(data)
                              ##  print("hier", result[0])
                            ##else:
                             ##   result[0].append({category:{}})
                              ##  print("hier2", result[0])

                            #result[category].append({setting, frontendSettings[frontendCategory][frontendSetting]})
                            #print(category + " :" + {frontendSetting, frontendSettings[frontendCategory][frontendSetting]})


        print(_json)
        return _json

    def updateSettings(self, _settings, as_dict = False):
        settingsContainer.updateSettings(_settings, as_dict)

    def prepareSettings(self):
        self.settings = settingsContainer.getSettingsAsJson()

    def execute(self):
        self.prepareSettings()
        self.run_model()
        self.calculate_flexibility()
        #self.visualize_flexibility()

    def save_flex_kpis_as_json(self, filename: str = None):
        """
        Speichert `self.model_data.model_settings` inkl. risk_combinations als JSON.
        """
        import json, os, datetime
        from copy import deepcopy  # <<< WICHTIG

        if self.model_data is None:
            print('save_flex_kpis_as_json: kein model_data vorhanden, nichts zu speichern')
            return None

        model_settings = getattr(self.model_data, 'model_settings', None)
        if model_settings is None:
            print('save_flex_kpis_as_json: model_data hat kein Attribut model_settings')
            return None

        if filename is None:
            filename = 'model_settings.json'

        try:
            # ---------------- Basisdaten ----------------
            to_write = json.loads(model_settings) if isinstance(model_settings, str) else model_settings

            def _make_serializable(obj):
                import numpy as _np
                if obj is None:
                    return None
                if isinstance(obj, (str, int, float, bool)):
                    return obj
                if isinstance(obj, datetime.timedelta):
                    return obj.total_seconds()
                if isinstance(obj, datetime.datetime):
                    return obj.isoformat()
                if isinstance(obj, _np.ndarray):
                    return obj.tolist()
                if isinstance(obj, _np.generic):
                    return obj.item()
                if isinstance(obj, dict):
                    return {k: _make_serializable(v) for k, v in obj.items()}
                if isinstance(obj, (list, tuple)):
                    return [_make_serializable(v) for v in obj]
                return str(obj)

            output_data = _make_serializable(to_write) if isinstance(to_write, dict) else {
                "model_settings": _make_serializable(to_write)
            }

            # ---------------- Risk-Auswertung ----------------
            risk_combinations = []
            flex_obj = getattr(self, 'flexibility_object', None)

            # -------- FLEX-PARAMETER speichern --------
            if flex_obj is not None:
                flex_params = {
                    "duration": _make_serializable(getattr(flex_obj, 'duration', None)),
                    "activation_time": _make_serializable(getattr(flex_obj, 'activation_time', None)),
                    "start_time": _make_serializable(getattr(flex_obj, 'start_time', None)),
                    "flex_location": _make_serializable(getattr(flex_obj, 'flex_location', None)),
                    "flex_at_daytype": _make_serializable(getattr(flex_obj, 'flex_at_daytype', None)),
                    "flex_at_number_of_day": _make_serializable(getattr(flex_obj, 'flex_at_number_of_day', None)),
                    "spontanflex": _make_serializable(getattr(flex_obj, 'spontanflex', None)),
                    "risk": _make_serializable(getattr(flex_obj, 'risk', None)),
                }
                output_data["flex_parameters"] = flex_params

            if flex_obj is not None and getattr(flex_obj, 'risk', False):
                ro = flex_obj.risk_object

                if ro is not None and getattr(ro, 'quantiles', None) is not None:

                    dur_h = None
                    if isinstance(flex_obj.duration, datetime.timedelta):
                        dur_h = flex_obj.duration.total_seconds() / 3600.0

                    # ---------- NICHT flex_dependant ----------
                    if not ro.flex_dependant:
                        for i_idx, strat in enumerate(ro.strat_pos_list):
                            for j_idx, heur in enumerate(ro.heuristic_pos_list):
                                for k_idx, modus in enumerate(ro.modus_pos_list):

                                    try:
                                        quant = deepcopy(ro.quantiles[i_idx][j_idx][k_idx])
                                    except Exception:
                                        quant = None

                                    try:
                                        kpi_stat = deepcopy(ro.kpi_statistic[i_idx][j_idx][k_idx])
                                    except Exception:
                                        kpi_stat = None

                                    try:
                                        q_woslp = deepcopy(ro.quantiles_without_slp[i_idx][j_idx][k_idx])
                                    except Exception:
                                        q_woslp = None

                                    data_comb = {
                                        "combination": {
                                            "strat_pos": strat,
                                            "heuristic_pos": heur,
                                            "modus_pos": modus
                                        }
                                    }

                                    if quant is not None:
                                        labels = ['min', 'max', 'mean', 'std', 'var',
                                                  'iqr', 'q05', 'q25', 'q50', 'q75', 'q95']
                                        stats_power = {
                                            lab: _make_serializable(quant[idx])
                                            for idx, lab in enumerate(labels)
                                        }
                                        data_comb["statistics_power"] = stats_power

                                        if dur_h is not None:
                                            data_comb["quantiles_energy_kwh"] = {
                                                k: (v * dur_h if isinstance(v, (int, float)) else None)
                                                for k, v in stats_power.items()
                                            }

                                    if q_woslp is not None:
                                        data_comb["quantiles_without_slp"] = {
                                            "slp_min": _make_serializable(q_woslp[0]),
                                            "spontanflex": _make_serializable(q_woslp[1])
                                        }

                                    if kpi_stat is not None:
                                        data_comb["kpi_statistics"] = _make_serializable(kpi_stat)

                                    risk_combinations.append(data_comb)

                    # ---------- flex_dependant ----------
                    else:
                        for i_idx, strat in enumerate(ro.strat_pos_list):
                            for j_idx, heur in enumerate(ro.heuristic_pos_list):
                                for k_idx, modus in enumerate(ro.modus_pos_list):
                                    for l_idx, strat2 in enumerate(ro.strat_pos_list2):
                                        for m_idx, modus2 in enumerate(ro.modus_pos_list2):

                                            try:
                                                quant = deepcopy(
                                                    ro.quantiles[i_idx][j_idx][k_idx][l_idx][m_idx]
                                                )
                                            except Exception:
                                                quant = None

                                            try:
                                                kpi_stat = deepcopy(
                                                    ro.kpi_statistic[i_idx][j_idx][k_idx][l_idx][m_idx]
                                                )
                                            except Exception:
                                                kpi_stat = None

                                            try:
                                                q_woslp = deepcopy(
                                                    ro.quantiles_without_slp[i_idx][j_idx][k_idx][l_idx][m_idx]
                                                )
                                            except Exception:
                                                q_woslp = None

                                            data_comb = {
                                                "combination": {
                                                    "strat_pos": strat,
                                                    "heuristic_pos": heur,
                                                    "modus_pos": modus,
                                                    "strat_pos_dep": strat2,
                                                    "modus_pos_dep": modus2
                                                }
                                            }

                                            if quant is not None:
                                                labels = ['min', 'max', 'mean', 'std', 'var',
                                                          'iqr', 'q05', 'q25', 'q50', 'q75', 'q95']
                                                data_comb["statistics_power"] = {
                                                    lab: _make_serializable(quant[idx])
                                                    for idx, lab in enumerate(labels)
                                                }

                                            if q_woslp is not None:
                                                data_comb["quantiles_without_slp"] = {
                                                    "slp_min": _make_serializable(q_woslp[0]),
                                                    "spontanflex": _make_serializable(q_woslp[1])
                                                }

                                            if kpi_stat is not None:
                                                data_comb["kpi_statistics"] = _make_serializable(kpi_stat)

                                            risk_combinations.append(data_comb)

            if risk_combinations:
                output_data["risk_combinations"] = risk_combinations

            with open(filename, "w", encoding="utf-8") as fh:
                json.dump(output_data, fh, indent=2, ensure_ascii=False)

            abs_path = os.path.abspath(filename)
            print(f"Model settings gespeichert in: {abs_path}")
            return abs_path

        except Exception as e:
            print("Fehler beim Speichern der model_settings:", e)
            return None



    def save_scenario(self, save_modell = False,  filename: str = None, viz = False, save_flex = False):
        if viz:
            for strat_pos in range(len(settingsContainer.getChargingStrategies())):
                for heuristic_pos in range(len(settingsContainer.getHeuristics())):
                    for modus_pos in range(2):  # assuming modus has two positions: 0 and 1
                        self.visualize_flexibility( viz_charging_strategy = [strat_pos],  viz_heuristic =  heuristic_pos,
                                                    viz_modus =  modus_pos, viz_safe = True, viz_show = False,
                                                   filename = f"{filename}_s{strat_pos}_h{heuristic_pos}_m{modus_pos}",
                                )
        self.save_flex_kpis_as_json(f"{filename}_kpis.json")

        if save_flex:
             save_list(self.flexibility_object, f"{filename}_flex_object")

        if save_modell:
            self.save_model(f"{filename}_model")


def start_tool(settings_file = "SimulationTool/SimulationTool_Settings.json"):
    # method to start the simulation tool
    # to be called before using simulation
    f = open(settings_file)

    data = json.load(f)
    simulation = Simulation()
    simulation.updateSettings(json.dumps(data))
    simulation.prepareSettings()

    return simulation
