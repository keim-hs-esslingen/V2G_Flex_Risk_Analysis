from flexibility_calc.flexibility import *
from config.settings import settingsContainer
import numpy as np
import datetime

class Risk_statistic:

    # compute_min_quarter_quantiles calls other methods, and everyting is calculated newly
    # by using single_flex_objects
    # if time before thesis

    strat_pos_list: list = None
    heuristic_pos_list: list = None
    modus_pos_list: list = None
    statistics: list = None
    statistics_without_slp: list = None
    quantiles: list = None
    quantiles_without_slp: list = None
    statistics_np: np.array = None
    flex_list: list = None
    all_flexes: list = None
    power: bool = None
    spontanflex: bool = None
    duration: datetime.timedelta = None
    start_time: datetime.timedelta = None
    flex_dependant: bool = None
    strat_pos_list2: list = None
    modus_pos_list2: list = None

    def __init__(self, spontanflex = True, strat_pos = -1, heuristic_pos = -1, modus_pos = -1, power = True, flex_dependant = False, strat_pos2 = -1, modus_pos2 = -1, *args, **kwargs):
        super().__init__(**kwargs)
        self.power = power
        self.flex_dependant = flex_dependant
        self.spontanflex = spontanflex
        # initialize strat_pos list
        if strat_pos.__class__ != list:
            if strat_pos.__class__ == int:
                if strat_pos >= 0 and strat_pos < len(settingsContainer.getChargingStrategies()):
                    self.strat_pos_list = [strat_pos]
                else:
                    if strat_pos == -1:
                        self.strat_pos_list = [i for i in range(len(settingsContainer.getChargingStrategies()))]
                    else:
                        print("Error: Please insert value between 0 and \f for strat_pos parameter",
                              len(settingsContainer.getChargingStrategies()) - 1)
            else:
                print("Error: Please insert nothing (default), list of ints or int as parameter for strat_pos")
        else:
            if max(strat_pos) >= len(settingsContainer.getChargingStrategies()) or min(strat_pos) < 0:
                print("Error: Please insert values between 0 and \f for strat_pos parameter",
                      len(settingsContainer.getChargingStrategies()) - 1)
            else:
                self.strat_pos_list = strat_pos
        # initialize heuristic_pos list
        if heuristic_pos.__class__ != list:
            if heuristic_pos.__class__ == int:
                if heuristic_pos >= 0 and heuristic_pos < len(settingsContainer.getHeuristics()):
                    self.heuristic_pos_list = [heuristic_pos]
                else:
                    if heuristic_pos == -1:
                        self.heuristic_pos_list = [i for i in range(len(settingsContainer.getHeuristics()))]
                    else:
                        print("Error: Please insert value between 0 and \f for heuristic parameter",
                              len(settingsContainer.getHeuristics()) - 1)
            else:
                print("Error: Please insert nothing (default), list of ints or int as parameter for heuristic_pos")
        else:
            if max(heuristic_pos) >= len(settingsContainer.getHeuristics()) or min(heuristic_pos) < 0:
                print("Error: Please insert values between 0 and \f for heuristic parameter", len(settingsContainer.getHeuristics()) - 1)
            else:
                self.heuristic_pos_list = heuristic_pos
        # initialize modus_pos list
        if modus_pos.__class__ != list:
            if modus_pos.__class__ == int:
                if modus_pos == 0 or modus_pos == 1:
                    self.modus_pos_list = [modus_pos]
                else:
                    if modus_pos == -1:
                        self.modus_pos_list = [0, 1]
                    else:
                        print("Error: Please insert value between 0 and 1 for modus_pos parameter", len(settingsContainer.getHeuristics()) - 1)
            else:
                print("Error: Please insert nothing (default), list of ints or int as parameter for modus_pos")
        else:
            if max(modus_pos) >= 2 or min(modus_pos) < 0:
                print("Error: Please insert values between 0 and 1 for modus_pos parameter", len(settingsContainer.getHeuristics()) - 1)
            else:
                self.modus_pos_list = modus_pos

        if flex_dependant:
            if strat_pos2.__class__ != list:
                if strat_pos2.__class__ == int:
                    if strat_pos2 >= 0 and strat_pos2 < len(settingsContainer.getChargingStrategies()):
                        self.strat_pos_list2 = [strat_pos2]
                    else:
                        if strat_pos2 == -1:
                            self.strat_pos_list2 = [i for i in range(len(settingsContainer.getChargingStrategies()))]
                        else:
                            print("Error: Please insert value between 0 and \f for strat_pos parameter",
                                  len(settingsContainer.getChargingStrategies()) - 1)
                else:
                    print("Error: Please insert nothing (default), list of ints or int as parameter for strat_pos")
            else:
                if max(strat_pos2) >= len(settingsContainer.getChargingStrategies()) or min(strat_pos2) < 0:
                    print("Error: Please insert values between 0 and \f for strat_pos parameter",
                          len(settingsContainer.getChargingStrategies()) - 1)
                else:
                    self.strat_pos_list2 = strat_pos2

            if modus_pos2.__class__ != list:
                if modus_pos2.__class__ == int:
                    if modus_pos2 == 0 or modus_pos2 == 1:
                        self.modus_pos_list2 = [modus_pos2]
                    else:
                        if modus_pos2 == -1:
                            self.modus_pos_list2 = [0, 1]
                        else:
                            print("Error: Please insert value between 0 and 1 for modus_pos parameter",
                                  len(settingsContainer.getHeuristics()) - 1)
                else:
                    print("Error: Please insert nothing (default), list of ints or int as parameter for modus_pos")
            else:
                if max(modus_pos2) >= 2 or min(modus_pos2) < 0:
                    print("Error: Please insert values between 0 and 1 for modus_pos parameter",
                          len(settingsContainer.getHeuristics()) - 1)
                else:
                    self.modus_pos_list2 = modus_pos2



        # initizalize statisitics list
        self.statistics = list()
        self.statistics_without_slp = list()
        self.quantiles = list()
        self.quantiles_without_slp = list()
        self.flex_list = list()
        self.all_flexes = list()
        self.kpis = list()
        self.kpi_statistic = list()

        for i in range(len(self.strat_pos_list)):
            self.statistics.append(list())
            self.statistics_without_slp.append(list())
            self.quantiles_without_slp.append(list())
            self.kpis.append(list())
            self.kpi_statistic.append(list())
            self.quantiles.append(list())
            for j in range(len(self.heuristic_pos_list)):
                self.statistics[i].append(list())
                self.statistics_without_slp[i].append(list())
                self.quantiles_without_slp[i].append(list())
                self.kpis[i].append(list())
                self.kpi_statistic[i].append(list())

                self.quantiles[i].append(list())
                for modus_pos in range(len(self.modus_pos_list)):
                    # self.statistics[strat_pos2][heuristic_pos2].append(list())
                    # self.quantiles[strat_pos2][heuristic_pos2].append(list())

                    if flex_dependant:
                        self.statistics[i][j].append(list())
                        self.statistics_without_slp[i][j].append(list())
                        self.quantiles_without_slp[i][j].append(list())
                        self.kpis[i][j].append(list())
                        self.kpi_statistic[i][j].append(list())
                        self.quantiles[i][j].append(list())
                        for l in range(len(self.strat_pos_list2)):
                            self.statistics[i][j][modus_pos].append(list())
                            self.statistics_without_slp[i][j][modus_pos].append(list())
                            self.quantiles_without_slp[i][j][modus_pos].append(list())
                            self.kpis[i][j][modus_pos].append(list())
                            self.kpi_statistic[i][j][modus_pos].append(list())
                            self.quantiles[i][j][modus_pos].append(list())
                            for modus_pos2 in range(len(self.modus_pos_list2)):

                                    # self.statistics[strat_pos2][heuristic_pos2].append(list())
                                    # self.quantiles[strat_pos2][heuristic_pos2].append(list())
                                    self.statistics[i][j][modus_pos][l].append([list(), list(), list()])
                                    # for dependent-case: store two parallel lists: slp_min list and spontanflex_without_slp list
                                    self.statistics_without_slp[i][j][modus_pos][l].append([list(), list()])
                                    # initialize corresponding quantiles structures (two entries: slp_min and spont)
                                    self.quantiles_without_slp[i][j][modus_pos][l].append([None, None])
                                    self.quantiles[i][j][modus_pos][l].append(list())
                                    self.kpis[i][j][modus_pos][l].append([list(), list(), list()])

                    else:
                        #self.statistics[strat_pos2][heuristic_pos2].append(list())
                        #self.quantiles[strat_pos2][heuristic_pos2].append(list())
                        self.statistics[i][j].append([list(), list(), list()])
                        self.statistics_without_slp[i][j].append([list(), list()])
                        # for non-flex-dependant case initialize quantiles_without_slp entry with two None placeholders
                        self.quantiles_without_slp[i][j].append([None, None])
                        self.quantiles[i][j].append(list())
                        self.kpis[i][j].append([list(), list(), list(), list(), list()])
                        self.kpi_statistic[i][j].append([None, None, None, None, None])

    def compute_all_flexes(self, all_DaysList, start_time, duration, NumberOfDays, start_daytype, act_time, Flex_place, numberofday, Daytype, already_computed = False):
        self.duration = duration
        self.start_time = start_time
        if already_computed:
            if self.all_flexes == None:

                for DayList in all_DaysList:
                    flex_day_list = list()
                    for day in DayList:
                        if Flex_place == "Home":
                            if self.spontanflex:
                                flex_day_list.append(day.Flexibility_Home.spontanflexes_on_this_day[-1])
                            else:
                                flex_day_list.append(day.Flexibility_Home.fixDateflexes_on_this_day[-1])
                        elif Flex_place == "Work":
                            if self.spontanflex:
                                flex_day_list.append(day.Flexibility_Work.spontanflexes_on_this_day[-1])
                            else:
                                flex_day_list.append(day.Flexibility_Work.fixDateflexes_on_this_day[-1])
                        else:
                            if self.spontanflex:
                                flex_day_list.append(day.Flexibility_All.spontanflexes_on_this_day[-1])
                            else:
                                flex_day_list.append(day.Flexibility_All.fixDateflexes_on_this_day[-1])
                    self.all_flexes.append(flex_day_list)
            #else: no new computation necessary
        else:
            flex_list = compute_flexibility(self.spontanflex, True, all_DaysList, start_time, duration, NumberOfDays, start_daytype, act_time, home, numberofday, Daytype)
            self.all_flexes = flex_list

    def compute_flexes_of_days(self, all_DaysList, start_time, duration, NumberOfDays, start_daytype, act_time, Flex_place, numberofday, Daytype, already_computed = False):

        if already_computed:
            self.flex_list = list()
            # no computation necessary
            Days = compute_day_list(Daytype, start_daytype, NumberOfDays)


            for DayList in all_DaysList:
                flex_day_list = list()
                for day_number in Days:
                    day = DayList[day_number]
                    if Flex_place == "Home":
                        if self.spontanflex:
                            flex_day_list.append(day.Flexibility_Home.spontanflexes_on_this_day[-1])
                        else:
                            flex_day_list.append(day.Flexibility_Home.fixDateflexes_on_this_day[-1])
                    elif Flex_place == "Work":
                        if self.spontanflex:
                            flex_day_list.append(day.Flexibility_Work.spontanflexes_on_this_day[-1])
                        else:
                            flex_day_list.append(day.Flexibility_Work.fixDateflexes_on_this_day[-1])
                    else:
                        if self.spontanflex:
                            flex_day_list.append(day.Flexibility_All.spontanflexes_on_this_day[-1])
                        else:
                            flex_day_list.append(day.Flexibility_All.fixDateflexes_on_this_day[-1])
                self.flex_list.append(flex_day_list)
        else:
            flex_list = compute_flexibility(self.spontanflex, True, all_DaysList, start_time, duration, NumberOfDays,
                                            start_daytype, act_time, Flex_place, numberofday, Daytype)
            self.flex_list = flex_list

    def compute_statistics_of_flexes(self):
        count = 0
        for flex_day_list in self.flex_list:
            for flex in flex_day_list:
                # statistics = list()
                for i in range(len(self.strat_pos_list)):
                    strat_pos = self.strat_pos_list[i]
                    # statistics.append(list())
                    for j in range(len(self.heuristic_pos_list)):
                        heuristic_pos = self.heuristic_pos_list[j]
                        # statistics[strat_pos].append([list(), list(), list()])
                        for k in range(len(self.modus_pos_list)):
                            modus_pos = self.modus_pos_list[k]
                            if self.power:
                                # power changes during period
                                if self.flex_dependant:
                                    for l in range(len(self.strat_pos_list2)):
                                        # use the l index to select the dependent strategy
                                        strat_pos2 = self.strat_pos_list2[l]
                                        for m in range(len(self.modus_pos_list2)):
                                            modus_pos2 = self.modus_pos_list2[m]
                                            #min, max, avg = flex.compute_statistic_values(strat_pos, heuristic_pos, modus_pos)
                                            min, max, avg = compute_statistic_values(flex, strat_pos, heuristic_pos,
                                                                                     modus_pos, strat_pos2, modus_pos2)
                                            if self.flex_dependant:
                                                # append statistics into the per-(l,m) containers
                                                self.statistics[i][j][k][l][m][0].append(min)
                                                self.statistics[i][j][k][l][m][1].append(max)
                                                self.statistics[i][j][k][l][m][2].append(avg)
                                                # kpis for the dependent case are stored at [i][j][k][l][m]
                                                try:
                                                    self.kpis[i][j][k][l][m][0].append(flex.kpis[i][j][k][0].number_of_vehicles)
                                                    self.kpis[i][j][k][l][m][1].append(flex.kpis[i][j][k][1].avg_soc)
                                                except Exception:
                                                    # fallback: try reading flat attributes if structure differs
                                                    try:
                                                        self.kpis[i][j][k][l][m][0].append(flex.kpis[i][j][k].number_of_vehicles)
                                                    except Exception:
                                                        pass
                                                try:
                                                    self.kpis[i][j][k][l][m][2].append(flex.kpis[i][j][k][2].avg_en)
                                                    self.kpis[i][j][k][l][m][3].append(flex.kpis[i][j][k][3].avg_den)
                                                    self.kpis[i][j][k][l][m][4].append(flex.kpis[i][j][k][4].avg_time)
                                                except Exception:
                                                    # best-effort: append if alternative structure present
                                                    try:
                                                        self.kpis[i][j][k][l][m][1].append(flex.kpis[i][j][k].avg_soc)
                                                        self.kpis[i][j][k][l][m][2].append(flex.kpis[i][j][k].avg_en)
                                                    except Exception:
                                                        pass
                                                 # collect SLP-min and spontanflex_without_standard_profile_simple for dependent case
                                                try:
                                                     slp_min_val = flex.standard_load_profile_rate_stat[strat_pos]['min']
                                                except Exception:
                                                     slp_min_val = None
                                                try:
                                                     spont_val = flex.spontanflex_list_without_standard_profile_simple[strat_pos][heuristic_pos][modus_pos]
                                                except Exception:
                                                     spont_val = None
                                                 # append to the parallel lists created in __init__
                                                try:
                                                    self.statistics_without_slp[i][j][k][l][m][0].append(slp_min_val)
                                                    self.statistics_without_slp[i][j][k][l][m][1].append(spont_val)
                                                except Exception:
                                                     # structure not present or indexing mismatch -> ignore
                                                     pass
                                else:
                                                 min, max, avg = flex.compute_statistic_values(strat_pos, heuristic_pos, modus_pos)
                                                 self.statistics[i][j][k][0].append(min)
                                                 self.statistics[i][j][k][1].append(max)
                                                 self.statistics[i][j][k][2].append(avg)
                                                 try:
                                                     self.statistics_without_slp[i][j][k][0].append(flex.standard_load_profile_rate_stat[strat_pos]['min'])
                                                 except Exception:
                                                     pass
                                                 try:
                                                     self.statistics_without_slp[i][j][k][1].append(
                                                         flex.spontanflex_list_without_standard_profile_simple[strat_pos][heuristic_pos][modus_pos])
                                                 except Exception:
                                                     pass
                                                 # collect SLP-min and spontanflex_without_standard_profile_simple for non-dependent case
                                                 try:
                                                     slp_min_val = flex.standard_load_profile_rate_stat[strat_pos]['min']
                                                 except Exception:
                                                     slp_min_val = None
                                                 try:
                                                     spont_val = flex.spontanflex_list_without_standard_profile_simple[strat_pos][heuristic_pos][modus_pos]
                                                 except Exception:
                                                     spont_val = None
                                                 # append into the two parallel lists at indices [0] (slp_min) and [1] (spont)
                                                 try:
                                                     self.statistics_without_slp[i][j][k][0].append(slp_min_val)
                                                     self.statistics_without_slp[i][j][k][1].append(spont_val)
                                                 except Exception:
                                                     pass
                                                 self.kpis[i][j][k][0].append(flex.kpis[i][j][k].number_of_vehicles)
                                                 self.kpis[i][j][k][1].append(flex.kpis[i][j][k].avg_soc)
                                                 self.kpis[i][j][k][2].append(flex.kpis[i][j][k].avg_en)
                                                 self.kpis[i][j][k][3].append(flex.kpis[i][j][k].avg_den)
                                                 self.kpis[i][j][k][4].append(flex.kpis[i][j][k].avg_time)
                            else:
                                             # total energy capacity charged/discharged
                                             if self.flex_dependant:
                                                 print("hi3")
                                             else:

                                                 min, max, avg = [flex.total_capacity[strat_pos][modus_pos], flex.total_capacity[strat_pos][modus_pos], flex.total_capacity[strat_pos][modus_pos]]




        self.statistics_np = np.array(self.statistics)
        self.compute_kpis_statistics()

    def compute_kpis_statistics(self):
        # Handle both non-dependent (3D kpis[i][j][k]) and flex-dependent (5D kpis[i][j][k][l][m]) structures
        for i in range(len(self.strat_pos_list)):
            for j in range(len(self.heuristic_pos_list)):
                for k in range(len(self.modus_pos_list)):
                    # detect if this entry is flex-dependent (deep nested lists)
                    try:
                        # if first element is a list with further nesting, treat as dependent
                        first = self.kpis[i][j][k][0]
                        is_dependent = any(isinstance(x, list) for x in first)
                    except Exception:
                        is_dependent = False

                    if not self.flex_dependant or not is_dependent:
                        # Non-dependent: kpis[i][j][k] is a list of lists per KPI attribute
                        for att in range(len(self.kpis[i][j][k])):
                            arr = np.array(self.kpis[i][j][k][att], dtype=float)
                            arr = arr[~np.isnan(arr)]
                            if len(arr) == 0:
                                continue
                            min1 = float(np.min(arr))
                            max1 = float(np.max(arr))
                            avg = float(np.mean(arr))
                            std = float(np.std(arr, ddof=1))
                            var = float(np.var(arr, ddof=1))
                            iqr = float(np.quantile(arr, 0.75) - np.quantile(arr, 0.25))
                            q01 = float(np.quantile(arr, 0.05))
                            q02 = float(np.quantile(arr, 0.25))
                            q03 = float(np.quantile(arr, 0.5))
                            q04 = float(np.quantile(arr, 0.75))
                            q05 = float(np.quantile(arr, 0.95))

                            self.kpi_statistic[i][j][k][att] = {'min': min1, 'max': max1, 'avg': avg, 'std': std, 'var': var, 'iqr': iqr, 'q05': q01, 'q25': q02, 'q50': q03, 'q75': q04, 'q95': q05}
                    #else:
                        # Dependent: iterate l and m dims
                      #  for l in range(len(self.kpis[i][j][k])):
                        #    for m in range(len(self.kpis[i][j][k][l])):
                                # ensure kpi_statistic structure exists at this index
        #self.kpi_statistic

    def compute_quantile(self, stat_modus, strat_pos, heuristic_pos, modus_pos, strat_pos_dep = None, modus_pos_dep = None):
        def compute_stats(arr):
            if len(arr) == 0:
                return None

            arr = np.array(arr, dtype=float)
            arr = arr[~np.isnan(arr)]
            if arr.size == 0:
                return None

            q05 = np.quantile(arr, 0.05)
            q25 = np.quantile(arr, 0.25)
            q50 = np.quantile(arr, 0.5)
            q75 = np.quantile(arr, 0.75)
            q95 = np.quantile(arr, 0.95)

            return [
                float(np.min(arr)),
                float(np.max(arr)),
                float(np.mean(arr)),
                float(np.std(arr, ddof=1)),  # std
                float(np.var(arr, ddof=1)),  # var
                float(q75 - q25),  # iqr
                float(q05),
                float(q25),
                float(q50),
                float(q75),
                float(q95),
            ]
        if stat_modus == "max":
            stat_value = 1
        elif stat_modus == "min":
            stat_value = 0
        elif stat_modus == "average":
            stat_value = 2
        strat_pos2 = self.strat_pos_list.index(strat_pos)
        heuristic_pos2 = self.heuristic_pos_list.index(heuristic_pos)
        modus_pos2 = self.modus_pos_list.index(modus_pos)
        if self.flex_dependant:
            strat_pos22 = self.strat_pos_list2.index(strat_pos_dep)
            modus_pos22 = self.modus_pos_list2.index(modus_pos_dep)

            arr = self.statistics_np[strat_pos2][heuristic_pos2][modus_pos2][strat_pos22][modus_pos22][stat_value]
            stats = compute_stats(arr)
            if stats is None:
                return

            self.quantiles[strat_pos2][heuristic_pos2][modus_pos2][strat_pos22][modus_pos_dep] = stats

        else:
            arr = self.statistics_np[strat_pos2][heuristic_pos2][modus_pos2][stat_value]
            stats = compute_stats(arr)
            if stats is None:
                return

            self.quantiles[strat_pos2][heuristic_pos2][modus_pos2] = stats

        return

    def compute_quantile_without_slp(self, strat_pos, heuristic_pos, modus_pos, strat_pos_dep=None, modus_pos_dep=None):
        """Berechnet die Quantile für die zwei Listen in statistics_without_slp (SLP-min und spontan)
        für die übergebenen Indizes und speichert das Ergebnis in quantiles_without_slp.
        Die Rückgabe ist ein Tuple bzw. Liste [q_slp, q_spont] wobei jedes q_* entweder ein Dict
        mit 'min','max','avg','q05','q25','q50','q75','q95' oder None ist.
        """

        def make_qdict(lst):
            if lst is None:
                return None
            arr = np.array(lst, dtype=float)
            arr = arr[~np.isnan(arr)]
            if arr.size == 0:
                return None

            q25 = np.quantile(arr, 0.25)
            q75 = np.quantile(arr, 0.75)

            return {
                'min': float(np.min(arr)),
                'max': float(np.max(arr)),
                'avg': float(np.mean(arr)),
                'std': float(np.std(arr, ddof = 1)),  # Standardabweichung
                'var': float(np.var(arr, ddof = 1)),  # Varianz
                'iqr': float(q75 - q25),  # Interquartilsabstand
                'q05': float(np.quantile(arr, 0.05)),
                'q25': float(q25),
                'q50': float(np.quantile(arr, 0.5)),
                'q75': float(q75),
                'q95': float(np.quantile(arr, 0.95)),
            }

        strat_pos2 = self.strat_pos_list.index(strat_pos)
        heuristic_pos2 = self.heuristic_pos_list.index(heuristic_pos)
        modus_pos2 = self.modus_pos_list.index(modus_pos)

        if self.flex_dependant:
            if strat_pos_dep is None or modus_pos_dep is None:
                return None
            strat_pos22 = self.strat_pos_list2.index(strat_pos_dep)
            modus_pos22 = self.modus_pos_list2.index(modus_pos_dep)
            # try to read the two parallel lists
            try:
                lists = self.statistics_without_slp[strat_pos2][heuristic_pos2][modus_pos2][strat_pos22][modus_pos22]
            except Exception:
                lists = None
            if not lists:
                # write None if structure present
                try:
                    self.quantiles_without_slp[strat_pos2][heuristic_pos2][modus_pos2][strat_pos22][modus_pos22] = [None, None]
                except Exception:
                    pass
                return None
            q_slp = make_qdict(lists[0]) if len(lists) > 0 else None
            q_spont = make_qdict(lists[1]) if len(lists) > 1 else None
            try:
                self.quantiles_without_slp[strat_pos2][heuristic_pos2][modus_pos2][strat_pos22][modus_pos22] = [q_slp, q_spont]
            except Exception:
                # try to ensure container then assign
                try:
                    while len(self.quantiles_without_slp[strat_pos2][heuristic_pos2][modus_pos2]) <= strat_pos22:
                        self.quantiles_without_slp[strat_pos2][heuristic_pos2][modus_pos2].append([None, None])
                    self.quantiles_without_slp[strat_pos2][heuristic_pos2][modus_pos2][strat_pos22][modus_pos22] = [q_slp, q_spont]
                except Exception:
                    pass
            return [q_slp, q_spont]
        else:
            try:
                lists = self.statistics_without_slp[strat_pos2][heuristic_pos2][modus_pos2]
            except Exception:
                lists = None
            if not lists:
                try:
                    self.quantiles_without_slp[strat_pos2][heuristic_pos2][modus_pos2] = [None, None]
                except Exception:
                    pass
                return None
            q_slp = make_qdict(lists[0]) if len(lists) > 0 else None
            q_spont = make_qdict(lists[1]) if len(lists) > 1 else None
            try:
                self.quantiles_without_slp[strat_pos2][heuristic_pos2][modus_pos2] = [q_slp, q_spont]
            except Exception:
                try:
                    while len(self.quantiles_without_slp[strat_pos2][heuristic_pos2]) <= modus_pos2:
                        self.quantiles_without_slp[strat_pos2][heuristic_pos2].append([None, None])
                    self.quantiles_without_slp[strat_pos2][heuristic_pos2][modus_pos2] = [q_slp, q_spont]
                except Exception:
                    pass
            return [q_slp, q_spont]

    def compute_min_quarter_quantiles_new(self, all_DaysList, start_time, duration, NumberOfDays, start_daytype, act_time, numberofday, Daytype, Flex_place = "Home"):
        # self.compute_all_flexes(all_DaysList, start_time, duration, act_time, Flex_place, numberofday, Daytype)
        self.compute_flexes_of_days(all_DaysList, start_time, duration, NumberOfDays, start_daytype, act_time, Flex_place,
                                        numberofday, Daytype)

        self.compute_statistics_of_flexes()
        for strat_pos2 in self.strat_pos_list:
            for heuristic_pos2 in self.heuristic_pos_list:
                for modus_pos2 in self.modus_pos_list:
                    self.compute_quantile("min", strat_pos2, heuristic_pos2, modus_pos2)
                    self.compute_quantile_without_slp(strat_pos2, heuristic_pos2, modus_pos2)
    def compute_min_quarter_quantiles_from_flex_list(self, flex_list):
        self.flex_list = flex_list
        self.compute_statistics_of_flexes()
        for strat_pos2 in self.strat_pos_list:
            for heuristic_pos2 in self.heuristic_pos_list:
                for modus_pos2 in self.modus_pos_list:
                    if self.flex_dependant:
                        for strat_pos22 in self.strat_pos_list2:
                            for modus_pos22 in self.modus_pos_list2:
                                self.compute_quantile("min", strat_pos2, heuristic_pos2, modus_pos2, strat_pos22, modus_pos22)
                                self.compute_quantile_without_slp(strat_pos2, heuristic_pos2, modus_pos2, strat_pos22, modus_pos22)
                    else:
                        self.compute_quantile("min", strat_pos2, heuristic_pos2, modus_pos2)
                        self.compute_quantile_without_slp(strat_pos2, heuristic_pos2, modus_pos2)


    def visualize_quantiles(self, strat_pos, heuristic_pos, modus_pos, with_energy = False, strat_pos_dep=None, modus_pos_dep=None):
        strat_pos2 = self.strat_pos_list.index(strat_pos)
        heuristic_pos2 = self.heuristic_pos_list.index(heuristic_pos)
        modus_pos2 = self.modus_pos_list.index(modus_pos)
        if self.flex_dependant:
            strat_pos_dep2 = self.strat_pos_list2.index(strat_pos_dep)

            modus_pos_dep2 = self.modus_pos_list2.index(modus_pos_dep)

            quantiles = self.quantiles[strat_pos2][heuristic_pos2][modus_pos2][strat_pos_dep2][modus_pos_dep].copy()
        else:
            quantiles = self.quantiles[strat_pos2][heuristic_pos2][modus_pos2].copy()
        del quantiles[3]  # delete std
        del quantiles[3] #delete var
        del quantiles[3]# delete iqr
        labels = ["min", "max", "average", "0.05", "0.25", "0.5", "0.75", "0.95" ]
        colors = ['blue','red', 'orange', 'purple', 'cyan', 'green', 'pink', 'magenta']

        for i in range(len(quantiles)):
            plt.axhline(y=quantiles[i], color = colors[i],  linestyle="--", label = labels[i])

            if with_energy:
                text = "Energie:\n " + str(int(quantiles[i]*self.duration.total_seconds()/3600)) + " kwh"
                plt.text((self.start_time + self.duration)/60, quantiles[i], text, fontsize=14)
        #print(quantiles)




def compute_statistic_values(flex, strat_pos, heuristic_pos, modus_pos, strat_pos2, modus_pos2):
    min = flex[strat_pos2][modus_pos2].spontanflex_list[strat_pos][heuristic_pos][modus_pos][0].total_capacity
    max = min
    avg = 0

    for AggFlex in flex[strat_pos2][modus_pos2].spontanflex_list[strat_pos][heuristic_pos][modus_pos]:
        val = AggFlex.total_capacity
        duration = (flex[strat_pos2][modus_pos2].end - flex[strat_pos2][modus_pos2].start).total_seconds()
        avg += val * (((AggFlex.end_time - AggFlex.start_time).total_seconds() / duration))
        if val < min:
            min = val
        if val > max:
            max = val
    avg = avg  # / (len(self.spontan_flex_list[strat_pos][heuristic_pos][modus_pos]))


    return min, max, avg
