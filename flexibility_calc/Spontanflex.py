from dataclasses import dataclass
from typing import List, Optional, Any, Set

from flexibility_calc.AggregatedFlex import *
from simulation_model.ChargingStrategy import *


class Spontanflex(specific_Flex_object):
    start: datetime.timedelta = None
    end: datetime.timedelta = None
    numberofday: int = None
    spontanflex_list: list = None
    profile_list: list = None
    checked_flex_boundaries: list = None
    checked_flex_boundaries_days: list = None
    checked_flex_boundaries_vehicles: list = None
    total_capacity: float = None
    strategy_capacity: list = None
    aggregated_bdry_and_charging_strategy: list = None
    standard_load_profile: list = None
    standard_load_profile_rate_stat: list = None
    standard_load_profile_energy: list = None
    spontanflex_list_without_standard_profile_simple: list = None
    kpis: List = None

    def __init__(self, start, end, Flex_Place, numberofday,  *args, **kwargs):
        super().__init__(start, datetime.timedelta(0), end - start, True, Flex_Place, **kwargs)
        self.start = start
        self.end = end
        self.profile_list = list()  # [[list()]*2] * len(Charging_strategies)
        self.checked_flex_boundaries = list()
        self.standard_load_profile = list()
        self.standard_load_profile_rate_stat = list()
        self.standard_load_profile_energy = list()
        self.spontanflex_list_without_standard_profile_simple = list()
        self.checked_flex_boundaries_days = list()
        self.checked_flex_boundaries_vehicles = list()
        self.strategy_capacity = list()
        # self.time_list = list()
        #self.total_power_list = list()
        self.spontanflex_list = list()
        self.total_capacity = list()
        self.numberofday = numberofday
        self.aggregated_bdry_and_charging_strategy = list()
        self.kpis = list()
        for i in range(len(settingsContainer.getChargingStrategies())):
            self.standard_load_profile.append(list())
            # initialize per-strategy stats and energy
            self.standard_load_profile_rate_stat.append({'min': None, 'max': None, 'avg': None})
            self.standard_load_profile_energy.append(0.0)
            # per-strategy container for spontanflex_without_standard_profile_simple
            self.spontanflex_list_without_standard_profile_simple.append(list())
            self.checked_flex_boundaries.append(list())
            self.checked_flex_boundaries_days.append(list())
            self.checked_flex_boundaries_vehicles.append(list())
            self.spontanflex_list.append(list())
            self.kpis.append(list())
            self.strategy_capacity.append(list())
            self.total_capacity.append([0, 0])
            self.aggregated_bdry_and_charging_strategy.append(list())
            for j in range(len(settingsContainer.getHeuristics())):
                self.aggregated_bdry_and_charging_strategy[i].append(list())
                self.aggregated_bdry_and_charging_strategy[i][j].append(list())
                self.aggregated_bdry_and_charging_strategy[i][j].append(list())
                self.strategy_capacity[i].append(list())
                self.strategy_capacity[i][j].append([AggregatedFlex(start, start), AggregatedFlex(start, end)])

                #self.strategy_capacity[i][j].append([AggregatedFlex(start, start), AggregatedFlex(start, end)])
                self.spontanflex_list[i].append(list())
                self.kpis[i].append(list())
                self.spontanflex_list[i][j].append([AggregatedFlex(start, start), AggregatedFlex(start, end)])
                self.spontanflex_list[i][j].append([AggregatedFlex(start, start), AggregatedFlex(start, end)])
                self.kpis[i][j].append([KPIs(), KPIs()])
                self.kpis[i][j].append([KPIs(), KPIs()])
                # initialize per-heuristic entry for spontanflex_list_without_standard_profile_simple: two modus entries (0,1)
                self.spontanflex_list_without_standard_profile_simple[i].append([0.0, 0.0])
    def compute_power_profiles_at_start(self, AggregatedFlex, strat_pos):
        charging_strategy = settingsContainer.getChargingStrategies()[strat_pos]
        for pos in range(len(AggregatedFlex.FlexBoundaries)):

            FlexBoundary = AggregatedFlex.FlexBoundaries[pos]

            if AggregatedFlex.days[
                pos] > FlexBoundary.available_period.days and FlexBoundary.t_start < FlexBoundary.t_end:
                print("Error, days")
            if not self.append_to_checked_lists(FlexBoundary, AggregatedFlex.days[pos], strat_pos):
                #if this vehicle already is involved in flexibility_calc computation (activated by other avialable period)
                continue

            #e_curr_new, ch_rate, time_start_charging_for_e_need = compute_new_e_curr(charging_strategy, FlexBoundary, self.start, AggregatedFlex.capacities[pos])
            old_day = AggregatedFlex.days[pos]
            #if pos ==28:
             #   print("hi")
            energy = compute_charged_until_certain_time_according_to_Charging_strategy(FlexBoundary, self.start + datetime.timedelta(days=old_day), charging_strategy)

            new_bdry = FlexBoundary.copy_and_change(self.start, FlexBoundary.e_curr + energy, old_day)
            #new_bdry.compute_boundaries(True) #evtl weg
            new_bdry.compute_simple_times()#
            #new_bdry.set_strategy_info(ch_rate, time_start_charging_for_e_need)

            self.compute_profiles(new_bdry, strat_pos)
        # Test_Spontanflex(self)

    def compute_profiles(self, bdry, strat_pos, next_day=False):
        charge = True
        discharge = True
        old_bdry = bdry.copy()
        if bdry.t_end - self.start > settingsContainer.getMinDeliveryTime():

            flex_profile_c = flex_profile(bdry, "charge", strat_pos)
            flex_profile_dc = flex_profile(bdry, "discharge", strat_pos)
            flex_profile_c.compute_flex_profile(self.start, self.end)
            flex_profile_dc.compute_flex_profile(self.start, self.end)
            if flex_profile_c.available_time != None and flex_profile_c.available_time > settingsContainer.getMinDeliveryTime() and flex_profile_c.profile != None:
                flex_profile_c.compute_flex_values()
                self.append_total_power_entry(flex_profile_c, strat_pos)
                self.profile_list.append(flex_profile_c)
            elif flex_profile_c.available_time == None or flex_profile_c.available_time <= settingsContainer.getMinDeliveryTime():
                charge = False
            else:
                # flx_profile.profile == None
                if flex_profile_c.energy != 0:
                    print("Error: if profile.profile == None, energy should be always zero")
                # in discharge mode, charging described by flx_profile differs to charging strategy
                # --> no charging is more than discharging
                # in charge mode, flx_profile charging differs if ch_strategy equals "as ssoon as possible",
                # as here e_max_alterrnative is larger than e_max in this ch_strategy ev is fully charged,
                # which is different to e_max (MAX_SOC) for charging for flexibility_calc (less)
                # for this special case, however, adapt charging of flx_profile like for the charging strategy,
                # as otherwise flex profile charging lasts less than ch_strategy charging , which makes no sense
                # --> no change between ch_strategy and flx_profile
                charge = False
            if flex_profile_dc.available_time != None and flex_profile_dc.available_time > settingsContainer.getMinDeliveryTime() and flex_profile_dc.profile != None:
                flex_profile_dc.compute_flex_values()
                self.append_total_power_entry(flex_profile_dc, strat_pos)
                self.profile_list.append(flex_profile_dc)
            elif flex_profile_dc.available_time == None or flex_profile_dc.available_time <= settingsContainer.getMinDeliveryTime():
                discharge = False
            else:
                # flx_profile.profile == None
                if flex_profile_dc.energy != 0:
                    print("Error: if profile.profile == None, energy should be always zero")
                # in discharge mode, charging described by flx_profile differs to charging strategy
                # --> no charging is less than charging like maybe in charging strategy
                discharge = True
        else:
            charge = False
            discharge = False


        modus_pos = 0
        base_profile_c = base_profile(bdry, strat_pos, modus_pos)
        base_profile_c.compute_base_profile(self.start, self.end)
        if charge:
                self.append_strategy_entry_to_flex(base_profile_c, modus_pos, append_to_flex=True)
                self.profile_list.append(base_profile_c)

                if (((base_profile_c.energy > flex_profile_c.energy) and (
                        abs(base_profile_c.energy - flex_profile_c.energy) > 1e-8)) or base_profile_c.rate > flex_profile_c.rate):
                    if flex_profile_c.energy != flex_profile_c.bdry.e_max:
                        print("Error: base profile shouldn't be larger than flex profile")
                    else:
                        if strat_pos != 0:
                            print("hiiii")
        # always append base profile to strategy list
        self.append_strategy_entry_to_flex(base_profile_c, modus_pos, append_to_flex=False)

        modus_pos = 1
            #if not charge:
            #    base_profile_dc = base_profile_c#.copy()set_modus_pos(modus_pos)#.copy()
           # else:
        base_profile_dc = base_profile(old_bdry, strat_pos, modus_pos)
        base_profile_dc.compute_base_profile(self.start, self.end)
        if discharge:
            self.profile_list.append(base_profile_dc)
            self.append_strategy_entry_to_flex(base_profile_dc, modus_pos, append_to_flex=True)
            if (flex_profile_dc.charge and (base_profile_dc.energy < flex_profile_dc.energy) and ((
                        abs(base_profile_dc.energy - flex_profile_dc.energy) > 1e-8) or base_profile_dc.rate > flex_profile_dc.rate)):
                if flex_profile_dc.energy != flex_profile_dc.bdry.e_max:
                    print("Error: base profile shouldn't be larger than flex profile")
                else:
                    if strat_pos != 0:
                        print("hiii")

    def append_strategy_entry_to_flex(self, profile, modus_pos, append_to_flex = True):
        modus = "charge"
        if profile.energy > 0:
            if append_to_flex:
                listt = self.spontanflex_list
            else:
                listt = self.strategy_capacity
            for heuristic_pos in range(len(settingsContainer.getHeuristics())):
                if profile.start_time == self.start:
                    idx_start = 0
                else:
                    idx_start = self.find_first_entry_with_larger_time(0, profile.start_time, profile.strat_pos, heuristic_pos,
                                                                       modus_pos, append_to_flex)+1
                    if idx_start == -1:
                        print("hallo")
                    if listt[profile.strat_pos][heuristic_pos][modus_pos][idx_start].start_time!= profile.start_time:
                        print("hi4")
                if profile.end_time == self.end:
                    idx_end = len(listt[profile.strat_pos][heuristic_pos][modus_pos]) - 1
                else:
                    idx_end = self.find_first_entry_with_larger_time(0, profile.end_time, profile.strat_pos, heuristic_pos, modus_pos, append_to_flex)


                if modus_pos == 1 or not append_to_flex:
                    rate = profile.rate
                    energy = profile.energy
                else:
                    rate = -profile.rate
                    energy = -profile.energy
                # going  through all indices and append additional entry to AggregatedFlex
                for idx in range(idx_start, idx_end + 1):
                    if idx == idx_start:
                        modus = "start"
                    elif idx == idx_end:

                        modus = "end"
                    else:
                        modus = "middle"

                    # append entry: compute total capacity of charging rates during this time_sequence
                    # capacities of old entry plus capacity of this profile
                    listt[profile.strat_pos][heuristic_pos][modus_pos][idx].append_entry(profile,
                                                                                                     rate, #substract to compute difference
                                                                                                     modus,
                                                                                                     heuristic_pos)
            # difference from base profiles to flex profiles to compute spontanflex eneergy
            if append_to_flex:
                self.total_capacity[profile.strat_pos][modus_pos] += energy

    def append_total_power_entry(self, profile, strat_pos):
        if profile.modus == "charge":
            modus_pos = 0
        else:  # profile.modus == "discharge":
            modus_pos = 1
        for heuristic_pos in range(len(settingsContainer.getHeuristics())):
            # define idx_start and idx_end
            if profile.whole_time and profile.profile == "basis":
                # if start and end time of spontanflex equals start/end time of profile
                idx_start = 0
                idx_end = len(self.spontanflex_list[strat_pos][heuristic_pos][modus_pos]) - 1
            else:

                # not whole_time, or profile is flex, which means, end or start_time is within interval
                if profile.start_time == self.start:
                    # start_time is the same
                    idx_start = 0
                    # appends new entry to list at entry before time is larger and returns index of this new entry
                    # new entry is copy of entry afterwards, but times of both entries are adapted
                    #  if time already has an entry, only index is returned

                    idx_end = self.find_first_entry_with_larger_time(0, profile.heuristic_dependant[
                        settingsContainer.getHeuristics()[heuristic_pos]].charging_end, strat_pos, heuristic_pos, modus_pos)
                elif profile.heuristic_dependant[
                    settingsContainer.getHeuristics()[heuristic_pos]].charging_end == self.end:
                    # end time is the same
                    idx_start = self.find_first_entry_with_larger_time(0, profile.start_time, strat_pos, heuristic_pos,
                                                                       modus_pos) + 1  # +1, as only entries after this entry have additional (dis)charging capacity
                    idx_end = len(self.spontanflex_list[strat_pos][heuristic_pos][modus_pos]) - 1

                else:
                    idx_start = self.find_first_entry_with_larger_time(0, profile.start_time, strat_pos, heuristic_pos,
                                                                       modus_pos) + 1
                    idx_end = self.find_first_entry_with_larger_time(idx_start , profile.heuristic_dependant[
                        settingsContainer.getHeuristics()[heuristic_pos]].charging_end, strat_pos, heuristic_pos, modus_pos)

            if modus_pos == 1 and not profile.charge:
                # if chraging in discharge mode substract from resulting energy/power
                rate = profile.heuristic_dependant[settingsContainer.getHeuristics()[heuristic_pos]].rate
                energy = -profile.heuristic_dependant[settingsContainer.getHeuristics()[heuristic_pos]].energy
            elif modus_pos == 1 and profile.charge:
                rate = -profile.heuristic_dependant[settingsContainer.getHeuristics()[heuristic_pos]].rate
                energy = -profile.heuristic_dependant[settingsContainer.getHeuristics()[heuristic_pos]].energy
            else:
                rate = profile.heuristic_dependant[settingsContainer.getHeuristics()[heuristic_pos]].rate
                energy = profile.heuristic_dependant[settingsContainer.getHeuristics()[heuristic_pos]].energy


            # going  through all indices and append additional entry to AggregatedFlex
            for idx in range(idx_start, idx_end + 1):
                if idx == idx_start:
                    modus = "start"
                elif idx == idx_end:
                    modus = "end"
                else:
                    modus = "middle"
                # append entry: compute total capacity of charging rates during this time_sequence
                # capacities of old entry plus capacity of this profile
                self.spontanflex_list[strat_pos][heuristic_pos][modus_pos][idx].append_entry(profile,
                                                                                              rate,
                                                                                              modus,
                                                                                              heuristic_pos)  # profile.heuristic_dependant[heuristics[heuristic_pos]].energy
        # energy dependant of heuristic should be the same
        if abs(profile.heuristic_dependant[settingsContainer.getHeuristics()[0]].energy - profile.heuristic_dependant[
            settingsContainer.getHeuristics()[1]].energy) > 1e-8:
            print("Error: computation of heuristic dependant energy")
        self.total_capacity[strat_pos][modus_pos] += energy

    def compute_aggregated_Boundaries_with_charging_strategy_difference(self, strat_pos, heuristic_pos, modus_pos,
                                                                        list_to_append):
        count = 0
        start = self.start
        for entry in list_to_append:
            self.aggregated_bdry_and_charging_strategy[strat_pos][heuristic_pos][modus_pos].append(
                AggregatedFlex(start, entry[0]))
            start = entry[0]
            self.aggregated_bdry_and_charging_strategy[strat_pos][heuristic_pos][modus_pos][count].append_entry(
                None, entry[1], "aggregated", None)
            count += 1
        list1 = self.aggregated_bdry_and_charging_strategy[strat_pos][heuristic_pos][modus_pos]

        for i, entry in enumerate(self.strategy_capacity[strat_pos][heuristic_pos][0]):
            if i == 0:
                continue
            idx_start_strat = self.find_first_entry_with_larger_time(0, entry.start_time, strat_pos, heuristic_pos, modus_pos, append_to_flex=False, search_list = list1)+1
            idx_end_strat = self.find_first_entry_with_larger_time(idx_start_strat, entry.end_time, strat_pos, heuristic_pos, modus_pos, append_to_flex = False, search_list = list1) +1  #+ 1
            if idx_start_strat < idx_end_strat:
                for idx in range(idx_start_strat, idx_end_strat ):
                    if modus_pos == 0:
                        cap_to_append = -entry.total_capacity
                    else:
                        cap_to_append = entry.total_capacity
                    self.aggregated_bdry_and_charging_strategy[strat_pos][heuristic_pos][modus_pos][
                        idx].append_entry(None, cap_to_append, "strategy", None)


    def compute_standard_load_profile(self, strat_pos, list_to_append):
        count = 0
        start = self.start
        for entry in list_to_append:
            self.standard_load_profile[strat_pos].append(
                AggregatedFlex(start, entry[0]))
            start = entry[0]
            self.standard_load_profile[strat_pos][count].append_entry(
                None, 0, "aggregated", None)
            count += 1
        list1 = self.standard_load_profile[strat_pos]

        for i, entry in enumerate(self.strategy_capacity[strat_pos][0][0]):
            if i == 0:
                continue
            idx_start_strat = self.find_first_entry_with_larger_time(0, entry.start_time, strat_pos, 0,0, append_to_flex=False, search_list = self.standard_load_profile[strat_pos])+1
            idx_end_strat = self.find_first_entry_with_larger_time(idx_start_strat, entry.end_time, strat_pos, 0,0, append_to_flex = False, search_list = list1) +1  #+ 1
            if idx_start_strat < idx_end_strat:
                for idx in range(idx_start_strat, idx_end_strat ):
                    #hier stattdesen einfach rate von entry statt capacity?! (ladestrategieverlauf wird schon für base_profeile berechnet

                    self.standard_load_profile[strat_pos][idx].append_entry(None, entry.total_capacity, "strategy", None)
        del self.standard_load_profile[strat_pos][0]
        del self.standard_load_profile[strat_pos][-1]
        self.standard_load_profile_energy[strat_pos] = np.sum([self.standard_load_profile[strat_pos][idx].total_capacity * ((self.standard_load_profile[strat_pos][idx].end_time - self.standard_load_profile[strat_pos][idx].start_time).total_seconds()/3600)  for idx in range(len(self.standard_load_profile[strat_pos]))])
        self.standard_load_profile_rate_stat[strat_pos]['min'] = np.min([self.standard_load_profile[strat_pos][idx].total_capacity for idx in range(len(self.standard_load_profile[strat_pos]))])
        self.standard_load_profile_rate_stat[strat_pos]['max'] = np.max(
            [self.standard_load_profile[strat_pos][idx].total_capacity for idx in
             range(len(self.standard_load_profile[strat_pos]))])
        self.standard_load_profile_rate_stat[strat_pos]['avg'] = np.mean(
            [self.standard_load_profile[strat_pos][idx].total_capacity for idx in
             range(len(self.standard_load_profile[strat_pos]))])

    def compute_flex_without_standard_profile_simple(self, strat_pos):

        for heuristic_pos in range(len(settingsContainer.getHeuristics())):
                for modus_pos in range(2):
                    if modus_pos == 0:
                         min, max, avg = self.compute_statistic_values(strat_pos, heuristic_pos, modus_pos)
                         res = (min  + self.standard_load_profile_rate_stat[strat_pos]['min']) * (self.end - self.start).total_seconds()/3600
                         self.spontanflex_list_without_standard_profile_simple[strat_pos][heuristic_pos][modus_pos] = res
                    else:
                        min, max, avg = self.compute_statistic_values(strat_pos, heuristic_pos, modus_pos)
                        res = (min - self.standard_load_profile_rate_stat[strat_pos]['min']) * (
                                    self.end - self.start).total_seconds() / 3600
                        self.spontanflex_list_without_standard_profile_simple[strat_pos][heuristic_pos][modus_pos] = res

    def find_first_entry_with_larger_time(self, count, reference_time, strat_pos, heuristic_pos, modus_pos, append_to_flex = True, search_list = None):
        if search_list != None:
            list1 = search_list
        else:
            if not append_to_flex:
                list1 = self.strategy_capacity[strat_pos][heuristic_pos][modus_pos]
            else:
                list1 = self.spontanflex_list[strat_pos][heuristic_pos][modus_pos]
        while count < len(list1) and list1[count].end_time < reference_time:
            count += 1

        if list1[count].end_time > reference_time:
            #list[count].copy_and_change_profiles(reference_time)
            # and insert new entry right before this time
            list1.insert(count, list1[count].copy_and_change_profiles(reference_time))
            #list[count].set_end_time(reference_time)
            #list[count + 1].set_start_time(reference_time)
        return count

    def append_to_checked_lists(self, FlexBoundary, day, strat_pos):
        self.checked_flex_boundaries[strat_pos].append(FlexBoundary)
        self.checked_flex_boundaries_days[strat_pos].append(day)
        if not FlexBoundary.vehicle.flex_active:
            self.checked_flex_boundaries_vehicles[strat_pos].append(FlexBoundary.vehicle)
            FlexBoundary.vehicle.set_flex_active(True)
            return True
        else:
            return False

    def append_to_checked_list(self, entry):
        if self.checked_flex_boundaries.count(entry[0]) >= 1:
            print("Error: spontanflex, checked_flex_boundaries")
        self.checked_flex_boundaries.append(entry[0])
        if entry[1] > entry[0].available_period.days and entry[0].t_start < entry[0].t_end:
            print("Error, days")
        self.checked_flex_boundaries_days.append(entry[1])

    def compute_statistic_values(self, strat_pos, heuristic_pos, modus_pos):
        min = self.spontanflex_list[strat_pos][heuristic_pos][modus_pos][0].total_capacity
        max = min
        avg = 0

        for AggFlex in self.spontanflex_list[strat_pos][heuristic_pos][modus_pos]:
            val = AggFlex.total_capacity
            duration = (self.end - self.start).total_seconds()
            avg += val * (((AggFlex.end_time - AggFlex.start_time).total_seconds() / duration))
            if val < min:
                min = val
            if val > max:
                max = val
        avg = avg  # / (len(self.spontan_flex_list[strat_pos][heuristic_pos][modus_pos]))

        return min, max, avg

    def compute_statistic_values_for_heuristics_and_strategies(self, strat_pos_list, heuristic_pos_list,
                                                               modus_pos_list):
        statistic_values = list()
        for strat_pos in strat_pos_list:
            statistic_values.append(list())
            for heuristic_pos in heuristic_pos_list:
                statistic_values[strat_pos].append([list(), list(), list()])
                for modus_pos in modus_pos_list:
                    min, max, avg = self.compute_statistic_values(strat_pos, heuristic_pos, modus_pos)
                    statistic_values[strat_pos][heuristic_pos][0].append(min)
                    statistic_values[strat_pos][heuristic_pos][0].append(max)
                    statistic_values[strat_pos][heuristic_pos][0].append(avg)
        return statistic_values

    def visualize_spontanflex(self, strat_pos, heuristic_pos, modus_pos, withlines = True, with_energy = True, for_risk = False, plt = None):

        min, max, avg = self.compute_statistic_values(strat_pos, heuristic_pos, modus_pos)
        y = list()
        x = list()
        for entry in self.spontanflex_list[strat_pos][heuristic_pos][modus_pos]:
            y.append(entry.total_capacity)
            y.append(entry.total_capacity)
            x.append((entry.start_time.total_seconds() - self.start.total_seconds()) / 60)
            x.append((entry.end_time.total_seconds()-self.start.total_seconds()) / 60)
        if for_risk:
            plt.plot(x, y, label="Ladestrategie: " + str(strat_pos) + ", Heuristik: " + str(heuristic_pos), linewidth = 1, alpha = 0.6)
        else:
            plt.plot(x, y, label="Ladestrategie: " + str(strat_pos) + ", Heuristik: " + str(heuristic_pos), linewidth=3)

        if with_energy:
            text = "Energie:\n " + str(np.round(self.total_capacity[strat_pos][modus_pos]))+ "kwh"
            plt.text(x[0], y[0], text, fontsize=15)

        if withlines:
            plt.axhline(y=max, color="red", linestyle="--", alpha = 0.3)
            plt.axhline(y=min, color="blue", linestyle="--", alpha = 0.3)

            #plt.axhline(y=avg, color="yellow", linestyle="--", alpha = 0.3)

    def visualize_spontanflex_all_heuristics_and_strategies(self):
        for modus_pos in range(2):
            for strat_pos in range(len(settingsContainer.getChargingStrategies())):
                for heuristic_pos in range(len(settingsContainer.getHeuristics())):
                    self.visualize_spontanflex(strat_pos, heuristic_pos, modus_pos)
            plt.legend()
            plt.show()
            plt.figure()

    def visualize_aggregated_potential_wrt_ch_strategy(self, strat_pos, heuristic_pos, modus_pos):
        y = list()
        x = list()
        self.aggregated_bdry_and_charging_strategy[strat_pos][heuristic_pos][modus_pos].pop(-1)
        for entry in self.aggregated_bdry_and_charging_strategy[strat_pos][heuristic_pos][modus_pos]:
            y.append(entry.total_capacity)
            y.append(entry.total_capacity)
            x.append((entry.start_time.total_seconds() - self.start.total_seconds()) / 60)
            x.append((entry.end_time.total_seconds() - self.start.total_seconds()) / 60)
        plt.plot(x, y, label="momentary potential for charging strategy: " + str(1+strat_pos), alpha = 0.6)


    def compute_kpis(self) -> List[List[List[KPIs]]]:
        """
        Berechnet KPIs für alle Kombinationen aus (ChargingStrategy, Heuristic, Modus).
        Erwartet: self.spontanflex_list[strat][heuristic][modus] -> Iterable von 'entry'-Objekten.
          Jedes 'entry' hat z.B.:
            - entry.FlexBoundaries: Iterable mit Boundary-Objekten mit .vehicle.ID (oder ähnlichem)
            - entry.energy_kwh     (oder: entry.total_energy) -> bitte anpassen
            - entry.duration_h     (oder: entry.duration_s/ min) -> bitte anpassen

        Rückgabe:
            3D-Liste kpi_results[strat_idx][heur_idx][modus_idx] -> KPIs
        """
        strategies = settingsContainer.getChargingStrategies()
        heuristics = settingsContainer.getHeuristics()
        num_modus = 2  # 0 = positive, 1 = negative (falls so gedacht)

        # Lege eine 3D-Struktur an: [strategien][heuristiken][modus]
        kpi_results: List[List[List[KPIs]]] = [
            [
                [KPIs(number_of_vehicles=0)
                 for _ in range(num_modus)]
                for _ in range(len(heuristics))
            ]
            for _ in range(len(strategies))
        ]

        for strat_pos in range(len(strategies)):
            for heuristic_pos in range(len(heuristics)):
                for modus_pos in range(num_modus):

                    # Alle Einträge für diese Kombination
                    entries = self.spontanflex_list[strat_pos][heuristic_pos][modus_pos]

                    # 1) Anzahl EINDEUTIGER Fahrzeuge
                    vehicle_ids: Set[Any] = set()

                    start_socs: List[float] = []  # Listen (nicht Sets!) für Durchschnitt
                    available_times: List[float] = []
                    available_ch_energy: List[float] = []
                    available_dch_energy: List[float] = []

                    for entry in entries:
                        # IDs einsammeln
                        # (Falls entry.FlexBoundaries fehlen kann, defensiv prüfen)
                        if getattr(entry, "FlexBoundaries", None) is not None:
                            for bdry in entry.FlexBoundaries:
                                # passt ggf. an: bdry.vehicle.id / bdry.vehicleID
                                vehicle_ids.add(bdry.bdry.vehicle.ID)
                                start_socs.append(bdry.bdry.available_period.start_SOC)
                                available_times.append(bdry.bdry.available_period.available_time.total_seconds())
                                available_ch_energy.append(bdry.bdry.e_max)
                                available_dch_energy.append(bdry.bdry.e_min)




                    number_of_vehicles = len(list(set(vehicle_ids)))

                    avg_soc = float(np.mean(start_socs)) if start_socs else None
                    avg_time = float(np.mean(available_times)) if available_times else None
                    avg_en = float(np.mean(available_ch_energy)) if available_ch_energy else None
                    avg_den = float(np.mean(available_dch_energy)) if available_dch_energy else None

                    # KPIs setzen
                    kpi_results[strat_pos][heuristic_pos][modus_pos] = KPIs(
                        number_of_vehicles=number_of_vehicles, avg_soc = avg_soc, avg_time = avg_time, avg_en = avg_en,
                        avg_den = avg_den
                    )

        self.kpis = kpi_results


def compute_spontanflex(DayList, start_time, duration, NumberOfDays, start_daytype, Flex_Place = "Home", numberofday=-1, Daytype=0 ):
    if duration > datetime.timedelta(days=1):
        print("Error: spontanflex only computed for durations smaller than 24 hours")
        return
    day_type = int(Daytype)

    if day_type < -1 or day_type > 7:
        print("Error: wrong daytype, insert value between -1,0 = Unknown, 1 = Monday, 2 = Tuesday,7 = Sunday...")

    end_time = start_time + duration

    # list, which days to compute spontanflex of
    if numberofday >= 0 and numberofday < len(DayList):
        Days = [numberofday]
        if day_type <= -1:
            if DayList[numberofday].day_type != day_type:
                print("Error: daytype and number of day do not fit together. Spontanflex computed for inserted number of day")
    elif numberofday < 0:
        Days = compute_day_list(day_type, start_daytype, NumberOfDays)
    else:
        print("Error: number of day not simulated")
        return


    # compute spontanflex

    spontanflex_list = list()
    for day in Days:
        #print(day)
        if Flex_Place == "Home":
            flex = DayList[day].Flexibility_Home
            av_periods = DayList[day].compute_available_periods_at_home()
            if end_time > datetime.timedelta(days=1):
                flex_next_day = DayList[day + 1].Flexibility_Home
                av_periods2 = DayList[day+1].compute_available_periods_at_home()

        else:
            if Flex_Place == "Work":
                flex = DayList[day].Flexibility_Work
                av_periods = DayList[day].compute_available_periods_at_work()
                if end_time > datetime.timedelta(days=1):
                    flex_next_day = DayList[day + 1].Flexibility_Work
                    av_periods2 = DayList[day + 1].compute_available_periods_at_work()
            else:
                flex = DayList[day].Flexibility_All
                av_periods = DayList[day].available_periods
                if end_time > datetime.timedelta(days=1):
                    flex_next_day = DayList[day + 1].Flexibility_All
                    av_periods2 = DayList[day+1].available_periods


        if end_time > datetime.timedelta(days=1):
            # if duration lasts overnight, first compute spontanflex for start day, which works normally


            if not flex.Aggregation_Computed:
                flex.compute_aggregated_Boundaries(av_periods)
            spontan_flex = flex.compute_spontanflex(start_time, duration)
            if day + 1 >= len(DayList):
                print("Computation of flexibility_calc not possible, as day not simulated")
            else:
                # then compute spontanflex of next day by using already computed spontan_flex:
                # special call of compute_spontanflex

                if not flex_next_day.Aggregation_Computed:
                    flex_next_day.compute_aggregated_Boundaries(av_periods2)
                spontan_flex = flex_next_day.compute_spontanflex(datetime.timedelta(0),
                                                                                end_time - datetime.timedelta(days=1),
                                                                                spontan_flex)
        else:
            if not flex.Aggregation_Computed:
                flex.compute_aggregated_Boundaries(av_periods)
            spontan_flex = flex.compute_spontanflex(start_time, duration)
        spontanflex_list.append(spontan_flex)

    return spontanflex_list


def compute_new_e_curr(charging_strategy, FlexBoundary, time):

    if charging_strategy == "as soon as possible":
        #e_max, t_max_end = FlexBoundary.compute_alternative_t_max_end()
        #charged_capacity = min(e_max, FlexBoundary.vehicle.charge(
        #            time - FlexBoundary.t_start, FlexBoundary.charging_power))
        #e_curr_new = FlexBoundary.e_curr + charged_capacity  # energy charged until current time
        # if no charging was possible, as e_curr == e_max --> E_curr = E_Max --> remaining_energy = 0
        e_max, t_max_end = FlexBoundary.compute_alternative_t_max_end()

        if t_max_end < time:
            # enough time to fully charge
            e_curr_new = e_max + FlexBoundary.e_curr
        else:
            e_curr_new = FlexBoundary.e_curr + FlexBoundary.vehicle.charge(time - FlexBoundary.t_start,
                                                                           FlexBoundary.charging_power)  # energy charged until current time

        ch_rate = None
        time_start_charging_for_e_need = None
    elif charging_strategy == "as late as possible":
        if FlexBoundary.e_min > 0:
            print("Error: e_min always smaller or equal than zero!")
            # charging until e_min in beginning with full_power
            if FlexBoundary.t_min_end > time:
                e_curr_new = FlexBoundary.e_curr + FlexBoundary.vehicle.charge(
                    time - FlexBoundary.t_start, FlexBoundary.charging_power)
            else:
                # if start_time is later than t_min_end, e_min is already charged
                e_curr_new = FlexBoundary.e_curr + FlexBoundary.e_min
                if time > FlexBoundary.t_min_start2 - datetime.timedelta(seconds=1):
                    # in this case, charging for e_need has been started as well
                    # compute charged energy
                    e_curr_new += FlexBoundary.vehicle.charge(
                        time - FlexBoundary.t_min_start2 + datetime.timedelta(seconds=1),
                        FlexBoundary.charging_power)
        else:
            if FlexBoundary.e_need > 0:
                # compute latest point to start charging, which is different from t_min_start2, as this is the point
                # to start charging, if discharged until e_min; but in this strategy no discharge until e_min
                time_start_charging_for_e_need = FlexBoundary.t_end - FlexBoundary.vehicle.time_to_charge(
                    FlexBoundary.e_need, FlexBoundary.charging_power) - datetime.timedelta(seconds=1)
                if time <= time_start_charging_for_e_need:
                    # charging not started
                    e_curr_new = FlexBoundary.e_curr
                else:
                    # charging started, so compute energy charged until start_time
                    diff = time - time_start_charging_for_e_need
                    e_curr_new = FlexBoundary.e_curr + FlexBoundary.vehicle.charge(diff,
                                                                                   FlexBoundary.charging_power)
            else:
                e_curr_new = FlexBoundary.e_curr
                time_start_charging_for_e_need = FlexBoundary.t_end
        ch_rate = None
    elif charging_strategy == "as long as possible with minimum rate":

        # compute minimum charging_rate to charge energy in available time
        ch_rate = compute_min_charging_rate(FlexBoundary.available_period.available_time, FlexBoundary.e_max,
                                            FlexBoundary.charging_power)
        energy_charged = min(FlexBoundary.vehicle.charge(time - FlexBoundary.t_start, ch_rate),
                             FlexBoundary.e_max)
        e_curr_new = FlexBoundary.e_curr + energy_charged
        time_start_charging_for_e_need = None
    return e_curr_new, ch_rate, time_start_charging_for_e_need
