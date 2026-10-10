from dataclasses import dataclass
from typing import List, Any, Set
import datetime
import numpy as np
from flexibility_calc.AggregatedFlex import *

class fixDateflex(specific_Flex_object):
    start: datetime.timedelta = None
    end: datetime.timedelta = None
    numberofday: int = None
    activation_start: datetime.timedelta = None
    fixDate_flex_list: list = None
    profile_list: list = None
    checked_flex_boundaries: list = None
    checked_flex_boundaries_days: list = None
    checked_flex_boundaries_vehicles: list = None
    total_capacity: list = None
    time_before_delievery: datetime.timedelta = None
    relevant_FlexBoundaries: list = None
    standard_load_profile: list = None
    standard_load_profile_rate_stat: list = None
    standard_load_profile_energy: list = None
    fixDateflex_list_without_standard_profile_simple: list = None
    kpis: List = None

    strategy_capacity: list = None
    aggregated_bdry_and_charging_strategy: list = None

    def __init__(self, start, end, activation_time,  Flex_place, numberofday, *args, **kwargs):
        super().__init__(start, activation_time, end-start, False, Flex_place, **kwargs)
        self.start = start
        self.activation_start = start-activation_time
        self.end = end
        self.profile_list = list()  # [[list()]*2] * len(Charging_strategies)
        self.checked_flex_boundaries = list()
        self.standard_load_profile = list()
        self.standard_load_profile_rate_stat = list()
        self.standard_load_profile_energy = list()
        self.fixDateflex_list_without_standard_profile_simple = list()
        self.checked_flex_boundaries_days = list()
        self.checked_flex_boundaries_vehicles = list()
        # self.time_list = list()
        self.fixDate_flex_list = list()
        self.total_capacity = list()
        self.numberofday = numberofday

        self.relevant_FlexBoundaries = list()
        self.strategy_capacity = list()
        self.aggregated_bdry_and_charging_strategy = list()
        self.kpis = list()

        for i in range(len(settingsContainer.getChargingStrategies())):
            self.standard_load_profile.append(list())
            # initialize per-strategy stats and energy
            self.standard_load_profile_rate_stat.append({'min': None, 'max': None, 'avg': None})
            self.standard_load_profile_energy.append(0.0)
            # per-strategy container for spontanflex_without_standard_profile_simple
            self.fixDateflex_list_without_standard_profile_simple.append(list())
            self.fixDate_flex_list.append(list())
            self.strategy_capacity.append(list())
            self.total_capacity.append([0, 0])
            self.aggregated_bdry_and_charging_strategy.append(list())
            self.checked_flex_boundaries.append(list())
            self.checked_flex_boundaries_days.append(list())
            self.checked_flex_boundaries_vehicles.append(list())
            self.kpis.append(list())
            for j in range(len(settingsContainer.getHeuristics())):
                self.aggregated_bdry_and_charging_strategy[i].append(list())
                self.aggregated_bdry_and_charging_strategy[i][j].append(list())
                self.aggregated_bdry_and_charging_strategy[i][j].append(list())
                self.strategy_capacity[i].append(list())
                self.strategy_capacity[i][j].append([AggregatedFlex(start, start), AggregatedFlex(start, end)])
                self.fixDateflex_list_without_standard_profile_simple[i].append([0.0, 0.0])
                self.kpis[i].append(list())
                self.fixDate_flex_list[i].append(list())
                self.fixDate_flex_list[i][j].append([AggregatedFlex(start, start), AggregatedFlex(start, end)])
                self.fixDate_flex_list[i][j].append([AggregatedFlex(start, start), AggregatedFlex(start, end)])
                self.kpis[i][j].append([KPIs(), KPIs()])
                self.kpis[i][j].append([KPIs(), KPIs()])
    #def vehicles_to_manipulate(self):
    def determine_SOCAdaption_startpoint(self, FlexBoundary, current_day_in_FlexBoundary):
        # start_point of vehicle of this FlexBoundary, when SOC adaption for maximum fixDate flex can start
        # vehicle.activation_start_time  >= start_time-activation_time = general activation_start_time
        # several variants possible, but here, we only look at the current FlexBoundary
        # assuming aggregator informs user about possible fixdateflex delievery at activation start point and
        # user then informs aggregator after last drive before flex.start_time that delievery is possibly
        # other variants would be that user informs aggregator earlier, but then information about
        # driving distances/ energy consumption of upcoming drives before dleieevery start are necessary as well,
        # which in chosen variant is not ( --> more realicitic application)

        # at least start_time -activation time and not less then FlexBoundary.t_start (when flexible period begins)
        if self.activation_start > FlexBoundary.t_start - datetime.timedelta(days = current_day_in_FlexBoundary):
            whole_period = False
            SOCAdaption_start = self.activation_start
        else:
            whole_period = True
            SOCAdaption_start = FlexBoundary.t_start - datetime.timedelta(days = current_day_in_FlexBoundary)
        # SOCAdaption_start = max(self.start-self.activation_time, FlexBoundary.t_start - datetime.timedelta(days = current_day_in_FlexBoundary))

        # in more complex cases, appension of several Flexboundaries possible
        self.relevant_FlexBoundaries.append([FlexBoundary, SOCAdaption_start, whole_period, current_day_in_FlexBoundary])

    def determine_relevant_boundaries(self, AggregatedFlex):
        for pos in range(len(AggregatedFlex.FlexBoundaries)):
            FlexBoundary = AggregatedFlex.FlexBoundaries[pos]

            if AggregatedFlex.days[
                pos] > FlexBoundary.available_period.days and FlexBoundary.t_start < FlexBoundary.t_end:
                print("Error, days")
            if FlexBoundary.t_end-datetime.timedelta(days =AggregatedFlex.days[pos])-self.start > settingsContainer.getMinDeliveryTime():
                self.determine_SOCAdaption_startpoint(FlexBoundary, AggregatedFlex.days[pos])


    def compute_fixDateflex_profiles_at_start(self, strat_pos):
        charging_strategy = settingsContainer.getChargingStrategies()[strat_pos]
        # going through relevant boundaries, which are available at start_time and maybe earlier
        for entry in self.relevant_FlexBoundaries:

            # here, in variant with only one FlexBoundary per entry
            # check relevant boundaries, if whole_period is after self.activation start or period starts earlier
            FlexBoundary = entry[0]
            whole_period = entry[2]
            days = datetime.timedelta(days=entry[3])

            if not self.append_to_checked_lists(FlexBoundary, entry[3], strat_pos):
                # if this vehicle already is involved in flexibility_calc computation (activated by other avialable period)
                continue

            # activation_start_time_in_relation_to_boundary_times
            activation_start_time_irtobdr = self.activation_start + days
            if whole_period:
                new_bdry = FlexBoundary.copy()
            else:
                # if period of FlexBoundary starts earlier than self.activation_start,
                # adaption of e_curr according to charging_strategies are made
                times = [FlexBoundary.t_start, FlexBoundary.t_max_end, FlexBoundary.t_min_end,
                         FlexBoundary.t_min_start2, FlexBoundary.t_end]

                time_to_charge = activation_start_time_irtobdr - times[0]
                if time_to_charge < datetime.timedelta(0):
                    print("Error: computation profiles_at start: SOC adaption")
                e_curr_new = FlexBoundary.e_curr + compute_charged_until_certain_time_according_to_Charging_strategy(
                    FlexBoundary, activation_start_time_irtobdr, charging_strategy)

                if self.activation_start < datetime.timedelta(0):
                    # as activation_start is negative, time of activation start is day earlier
                    old_day = entry[3]+self.activation_start.days  # activation_start.days negative
                    activation_start_time_irtobdr += datetime.timedelta(days = self.activation_start.days)
                    # add day to activation start, so that time is positive
                    # by setting old_day to zero, no adaption of available_time days variable of available period
                    # --> adaption is done later, when new_bdry is copied again, but with keep_days = False and old_day variable
                    new_bdry = FlexBoundary.copy_and_change(self.activation_start + days, e_curr_new, old_day = 0, strategy_reset=False)
                    old_day -= self.activation_start.days
                else:
                    old_day = entry[3]
                    new_bdry = FlexBoundary.copy_and_change(self.activation_start + days, e_curr_new, old_day = 0, strategy_reset=False)
                new_bdry.compute_simple_times()
                #old_day = -self.activation_start.days
            # Now for all FlexBoundaries available at the start of the fixDate_flex time the new (or old) FlexBoundaries
            # after charging according to charging_strategy are computed. With this information, the (dis)charge
            # boundaries are calculated: how much energy can be adapted until fixDate_flex_start_time
            # calculation of SOC adaption:
            if new_bdry.e_min>0:
                print("Error: fdf")
            start_irtobdr = self.start + days
            if new_bdry.t_min_end <= start_irtobdr:
                # e_min can be reached before start of fixdate_flex period
                e_curr_new_min = new_bdry.e_curr + new_bdry.e_min #MIN_SOC*new_bdry.vehicle.battery_size/100
                if new_bdry.t_min_start2 <= start_irtobdr:
                    # charging to e_need already started
                    e_curr_new_min += new_bdry.vehicle.charge(start_irtobdr-new_bdry.t_min_start2, new_bdry.charging_power)
            else:
                time_to_charge = start_irtobdr - new_bdry.t_start
                if time_to_charge < datetime.timedelta(0):
                    print("Error: calculation SOC adaption")
                # determine how much energy can be discharged
                if new_bdry.e_min > 0:
                    print("Error: fdF: e_min always larger or equal than zero")
                    #e_curr_new_min = FlexBoundary.e_curr + FlexBoundary.vehicle.charge(time_to_charge, FlexBoundary.charging_power)
                else:
                    e_curr_new_min = new_bdry.e_curr - new_bdry.vehicle.discharge(time_to_charge, new_bdry.discharging_power)
            # max charged energy is not complex
            if new_bdry.t_max_end <= start_irtobdr:
                e_curr_new_max = new_bdry.e_curr+ new_bdry.e_max
            else:
                e_curr_new_max = new_bdry.e_curr + new_bdry.vehicle.charge(start_irtobdr-new_bdry.t_start, new_bdry.charging_power)

            #if whole_period:
             #   old_day = entry[3]
            new_bdry2 = new_bdry.copy_and_change(self.start, e_curr_new_max, entry[3], strategy_reset = False)
            new_bdry3 = new_bdry.copy_and_change(self.start, e_curr_new_min, entry[3], strategy_reset = True)
            new_bdry2.compute_simple_times()
            new_bdry3.compute_simple_times()
            if new_bdry2.e_min>0:
                print("Error: fdf")
            if new_bdry3.e_min>0:
                print("Error: fdf")
            energy = compute_charged_until_certain_time_according_to_Charging_strategy(FlexBoundary,
                                                                                       self.start + days,
                                                                                       charging_strategy)

            old_bdry = FlexBoundary.copy_and_change(self.start, FlexBoundary.e_curr + energy, entry[3])
            # new_bdry.compute_boundaries(True) #evtl weg
            old_bdry.compute_simple_times()  #
            self.compute_profiles(new_bdry2,  strat_pos, "discharge", old_bdry)
            self.compute_profiles(new_bdry3, strat_pos, "charge", old_bdry)
            # with calculated new e_curr, now calculate heurisitic dependant and strategy dependant capacities:
            # new bdry (nötig?) --> sollte einfacher sein, dann kann es wie bei Spontanflex gemacht werden (mit flex/base profile)!
            # compute_profiles



            #self.compute_profiles(new_bdry, strat_pos)  --> adapt to optionaly take two bdry arguments
        # Test_Spontanflex(self)

    def compute_profiles(self, bdry, strat_pos, modus, old_bdry):
        active = True

        if bdry.t_end - self.start > settingsContainer.getMinDeliveryTime():
            flx_profile = flex_profile(bdry, modus, strat_pos, spontanflex=False)
            flx_profile.compute_flex_profile(self.start, self.end)
            if flx_profile.available_time != None and flx_profile.available_time > settingsContainer.getMinDeliveryTime() and flx_profile.profile != None:
                flx_profile.compute_flex_values()
                self.append_total_power_entry(flx_profile, strat_pos)
                self.profile_list.append(flx_profile)
            elif flx_profile.available_time == None or flx_profile.available_time <= settingsContainer.getMinDeliveryTime():
                active = False
            else:
                # flx_profile.profile == None
                if flx_profile.energy!= 0:
                    print("Error: if profile.profile == None, energy should be always zero")
                # in discharge mode, charging described by flx_profile differs to charging strategy
                # --> no charging is more than discharging
                # in charge mode, flx_profile charging differs if ch_strategy equals "as ssoon as possible",
                # as here e_max_alterrnative is larger than e_max in this ch_strategy ev is fully charged,
                # which is different to e_max (MAX_SOC) for charging for flexibility_calc (less)
                # for this special case, however, adapt charging of flx_profile like for the charging strategy,
                # as otherwise flex profile charging lasts less than ch_strategy charging , which makes no sense
                # --> no change between ch_strategy and flx_profile
                if modus == "charge":
                    active = False
                else:
                    active=True
        else:
            active = False

        if modus == "charge":
            modus_pos = 0
        else:  # modus == "discharge"
            modus_pos = 1

        base_profile_c = base_profile(old_bdry, strat_pos, modus_pos)
        base_profile_c.compute_base_profile(self.start, self.end)

        if active:
            self.append_strategy_entry(base_profile_c, modus_pos, append_to_flex=True)
            self.profile_list.append(base_profile_c)
            if (modus == "charge" and ((base_profile_c.energy -flx_profile.energy) >1e-8 or base_profile_c.rate > flx_profile.rate)) or (modus == "discharge" and ((flx_profile.energy - base_profile_c.energy) > 1e-8)):
                if flx_profile.energy != flx_profile.bdry.e_max:
                    print("Error: base profile shouldn't be larger than flex profile")
                else:
                    if strat_pos != 0:
                        print("hiiii")

        if modus == "charge":
            # always append base profile to strategy list
            self.append_strategy_entry(base_profile_c, modus_pos, append_to_flex=False)

    def append_strategy_entry(self, profile, modus_pos, append_to_flex = True):
        modus = "charge"

        if profile.energy > 0:
            if append_to_flex:
                listt = self.fixDate_flex_list
            else:
                listt = self.strategy_capacity

            for heuristic_pos in range(len(settingsContainer.getHeuristics())):
                if profile.start_time == self.start:
                    idx_start = 0
                else:
                    idx_start = self.find_first_entry_with_larger_time(0, profile.start_time, profile.strat_pos,
                                                                       heuristic_pos,
                                                                       modus_pos, append_to_flex) +1
                    if idx_start == -1:
                        print("hallo")
                if profile.end_time == self.end:
                    idx_end = len(listt[profile.strat_pos][heuristic_pos][modus_pos]) - 1
                else:
                    idx_end = self.find_first_entry_with_larger_time(0, profile.end_time, profile.strat_pos,
                                                                     heuristic_pos, modus_pos, append_to_flex)

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
                                                                                                         rate,
                                                                                                         # substract to compute difference
                                                                                                         modus,
                                                                                                         heuristic_pos)

            if append_to_flex:
                # difference from base profiles to flex profiles to compute spontanflex eneergy
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
                idx_end = len(self.fixDate_flex_list[strat_pos][heuristic_pos][modus_pos]) - 1
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
                                                                       modus_pos)   + 1  # +1, as only entries after this entry have additional (dis)charging capacity
                    idx_end = len(self.fixDate_flex_list[strat_pos][heuristic_pos][modus_pos]) - 1

                else:
                    idx_start = self.find_first_entry_with_larger_time(0, profile.start_time, strat_pos, heuristic_pos,
                                                                       modus_pos)   + 1
                    idx_end = self.find_first_entry_with_larger_time(idx_start, profile.heuristic_dependant[
                        settingsContainer.getHeuristics()[heuristic_pos]].charging_end, strat_pos, heuristic_pos, modus_pos)
            if modus_pos == 1 and not profile.charge:
                # if chraging in discharge mode substract from resulting energy/power
                rate = profile.heuristic_dependant[settingsContainer.getHeuristics()[heuristic_pos]].rate
                energy =  -profile.heuristic_dependant[settingsContainer.getHeuristics()[heuristic_pos]].energy
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
                self.fixDate_flex_list[strat_pos][heuristic_pos][modus_pos][idx].append_entry(profile,
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
            if i ==0:
                continue
            idx_start_strat = self.find_first_entry_with_larger_time(0, entry.start_time, strat_pos, heuristic_pos, modus_pos, append_to_flex=False, search_list = list1)+1
            idx_end_strat = self.find_first_entry_with_larger_time(idx_start_strat, entry.end_time, strat_pos, heuristic_pos, modus_pos, append_to_flex = False, search_list = list1)+1
            if idx_start_strat < idx_end_strat:
                for idx in range(idx_start_strat, idx_end_strat):
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
            # initial aggregated entry with 0 capacity (will be updated by strategy entries)
            self.standard_load_profile[strat_pos][count].append_entry(
                None, 0, "aggregated", None)
            count += 1
        list1 = self.standard_load_profile[strat_pos]

        # Merge strategy capacities into the standard profile where applicable
        for i, entry in enumerate(self.strategy_capacity[strat_pos][0][0]):
            if i == 0:
                continue
            idx_start_strat = self.find_first_entry_with_larger_time(0, entry.start_time, strat_pos, 0, 0, append_to_flex=False, search_list=self.standard_load_profile[strat_pos]) + 1
            idx_end_strat = self.find_first_entry_with_larger_time(idx_start_strat, entry.end_time, strat_pos, 0, 0, append_to_flex=False, search_list=list1) + 1
            if idx_start_strat < idx_end_strat:
                for idx in range(idx_start_strat, idx_end_strat):
                    self.standard_load_profile[strat_pos][idx].append_entry(None, entry.total_capacity, "strategy", None)

        # remove artificial first and last entries (boundaries)
        if len(self.standard_load_profile[strat_pos]) >= 2:
            del self.standard_load_profile[strat_pos][0]
            del self.standard_load_profile[strat_pos][-1]

        # compute energy (kWh) and rate statistics robustly using index iteration
        if len(self.standard_load_profile[strat_pos]) > 0:
            self.standard_load_profile_energy[strat_pos] = np.sum([
                self.standard_load_profile[strat_pos][idx].total_capacity * ((self.standard_load_profile[strat_pos][idx].end_time - self.standard_load_profile[strat_pos][idx].start_time).total_seconds() / 3600)
                for idx in range(len(self.standard_load_profile[strat_pos]))
            ])
            capacities = [self.standard_load_profile[strat_pos][idx].total_capacity for idx in range(len(self.standard_load_profile[strat_pos]))]
            self.standard_load_profile_rate_stat[strat_pos]['min'] = np.min(capacities) if capacities else 0.0
            self.standard_load_profile_rate_stat[strat_pos]['max'] = np.max(capacities) if capacities else 0.0
            self.standard_load_profile_rate_stat[strat_pos]['avg'] = np.mean(capacities) if capacities else 0.0
        else:
            self.standard_load_profile_energy[strat_pos] = 0.0
            self.standard_load_profile_rate_stat[strat_pos]['min'] = 0.0
            self.standard_load_profile_rate_stat[strat_pos]['max'] = 0.0
            self.standard_load_profile_rate_stat[strat_pos]['avg'] = 0.0

    def compute_flex_without_standard_profile_simple(self, strat_pos):

        for heuristic_pos in range(len(settingsContainer.getHeuristics())):
            for modus_pos in range(2):
                if modus_pos == 0:
                    min, max, avg = self.compute_statistic_values(strat_pos, heuristic_pos, modus_pos)
                    res = (min + self.standard_load_profile_rate_stat[strat_pos]['min']) * (
                                self.end - self.start).total_seconds() / 3600
                    self.fixDateflex_list_without_standard_profile_simple[strat_pos][heuristic_pos][modus_pos] = res
                else:
                    min, max, avg = self.compute_statistic_values(strat_pos, heuristic_pos, modus_pos)
                    res = (min - self.standard_load_profile_rate_stat[strat_pos]['min']) * (
                            self.end - self.start).total_seconds() / 3600
                    self.fixDateflex_list_without_standard_profile_simple[strat_pos][heuristic_pos][modus_pos] = res

    def find_first_entry_with_larger_time(self, count, reference_time, strat_pos, heuristic_pos, modus_pos, append_to_flex = True, search_list = None):
        if search_list != None:
            list1 = search_list
        else:
            if not append_to_flex:
                list1 = self.strategy_capacity[strat_pos][heuristic_pos][modus_pos]
            else:
                list1 = self.fixDate_flex_list[strat_pos][heuristic_pos][modus_pos]
        while count < len(list1) and list1[count].end_time < reference_time:
            count += 1

        if list1[count].end_time > reference_time:
            #list[count].copy_and_change_profiles(reference_time)
            # and insert new entry right before this time
            list1.insert(count, list1[count].copy_and_change_profiles(reference_time))
            #list[count].set_end_time(reference_time)
            #list[count + 1].set_start_time(reference_time)
        return count

    def append_to_checked_list(self, entry):
        if self.checked_flex_boundaries.count(entry[0]) >= 1:
            print("Error: spontanflex, checked_flex_boundaries")
        self.checked_flex_boundaries.append(entry[0])

        if entry[1] > entry[0].available_period.days and entry[0].t_start < entry[0].t_end:
            print("Error, days")
        self.checked_flex_boundaries_days.append(entry[1])

    def append_to_checked_lists(self, FlexBoundary, day, strat_pos):
        self.checked_flex_boundaries[strat_pos].append(FlexBoundary)
        self.checked_flex_boundaries_days[strat_pos].append(day)
        if not FlexBoundary.vehicle.flex_active:
            self.checked_flex_boundaries_vehicles[strat_pos].append(FlexBoundary.vehicle)
            FlexBoundary.vehicle.set_flex_active(True)
            return True
        else:
            return False

    def compute_statistic_values(self, strat_pos, heuristic_pos, modus_pos):
        min_val = self.fixDate_flex_list[strat_pos][heuristic_pos][modus_pos][0].total_capacity
        max_val = min_val
        avg = 0

        for AggFlex in self.fixDate_flex_list[strat_pos][heuristic_pos][modus_pos]:
            val = AggFlex.total_capacity
            duration = (self.end - self.start).total_seconds()
            avg += val * (((AggFlex.end_time - AggFlex.start_time).total_seconds() / duration))
            if val < min_val:
                min_val = val
            if val > max_val:
                max_val = val
        avg = avg  # / (len(self.spontan_flex_list[strat_pos][heuristic_pos][modus_pos]))

        return min_val, max_val, avg

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

    def visualize_fixDate_flex(self, strat_pos, heuristic_pos, modus_pos, withlines = True, with_energy= False, for_risk = False, plt = None):
        min, max, avg = self.compute_statistic_values(strat_pos, heuristic_pos, modus_pos)
        y = list()
        x = list()
        for entry in self.fixDate_flex_list[strat_pos][heuristic_pos][modus_pos]:
            y.append(entry.total_capacity)
            y.append(entry.total_capacity)
            x.append((entry.start_time.total_seconds()-self.start.total_seconds()) / 60)
            x.append((entry.end_time.total_seconds()-self.start.total_seconds())/60)
        if for_risk:
            plt.plot(x, y, label="Ladestrategie: " + str(strat_pos) + ", heuristic: " + str(heuristic_pos), linewidth=1, alpha = 0.6)
        else:
            plt.plot(x, y, label="Ladestrategie: " + str(strat_pos) + ", heuristic: " + str(heuristic_pos), linewidth = 3)
        if withlines:
            plt.axhline(y=max, color="red", linestyle="--", alpha = 0.3)
            plt.axhline(y=min, color="blue", linestyle="--", alpha = 0.3)
        if with_energy:
            text = "Energie:\n" + str(int(np.round(self.total_capacity[strat_pos][modus_pos],0)))+ " kwh"
            plt.text(x[-1], y[-1], text, fontsize=14)
            #plt.axhline(y=avg, color="yellow", linestyle="--", alpha = 0.3)

    def visualize_fixDate_flex_all_heuristics_and_strategies(self):
        for modus_pos in range(2):
            for strat_pos in range(len(settingsContainer.getChargingStrategies())):
                for heuristic_pos in range(len(settingsContainer.getHeuristics())):
                    self.visualize_fixDate_flex(strat_pos, heuristic_pos, modus_pos)
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
        plt.plot(x, y, label="Momentanpotential bei Ladestrategie: " + str(strat_pos +1), alpha = 0.3)

    def compute_kpis(self) -> List[List[List[KPIs]]]:

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
                    entries = self.fixDate_flex_list[strat_pos][heuristic_pos][modus_pos]

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


def compute_fixDate_flex(DayList, start_time, duration, NumberOfDays, start_daytype, activation_time, Flex_place = "Home", numberofday=-1, Daytype=8):
    if duration > datetime.timedelta(days=1):
        print("Error: fixDate_flex only computed for durations smaller than 24 hours")
        return
    day_type = int(Daytype)
    if day_type < 1 and day_type > 7:
        print("Error: wrong daytype, insert value between 1 = Monday, 2 = Tuesday,..., 8 = Unknown")

    end_time = start_time + duration

    # list, which days to compute fixDate_flex of
    if numberofday >= 0 and numberofday < len(DayList):
        Days = [numberofday]
        if day_type <= -1:
            if DayList[numberofday].day_type != day_type:
                print("Error: daytype and number of day do not fit together. fixDate_flex computed for number of day")
    elif numberofday < 0:
        Days = compute_day_list(day_type, start_daytype, NumberOfDays)
    else:
        print("Error: number of day not simulated")
        return

    # compute fixDate_flex

    fixDate_flex_list = list()
    for day in Days:

        print(day)
        if Flex_place == "Home":
            flex = DayList[day].Flexibility_Home
            av_periods = DayList[day].compute_available_periods_at_home()
            if end_time > datetime.timedelta(days=1):
                flex_next_day = DayList[day + 1].Flexibility_Home
                av_periods2 = DayList[day + 1].compute_available_periods_at_home()

        elif Flex_place == "Work":
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
                av_periods2 = DayList[day + 1].available_periods
        if end_time > datetime.timedelta(days=1):
            # if duration lasts overnight, first compute fixDate_flex for start day, which works normally
            if not flex.Aggregation_Computed:
                flex.compute_aggregated_Boundaries(DayList[day].available_periods)
            fixDate_flex = flex.compute_fixDateflex(start_time, duration, activation_time)
            if day + 1 >= len(DayList):
                print("Computation of flexibility_calc not possible, as day not simulated")
            else:
                # then compute fixDate_flex of next day by using already computed fixDate_flex:
                # special call of compute_fixDate_flex
                if not flex_next_day.Aggregation_Computed:
                    flex_next_day.compute_aggregated_Boundaries(av_periods2)
                fixDate_flex = flex_next_day.compute_fixDateflex(datetime.timedelta(0),
                                                                                end_time - datetime.timedelta(days=1), datetime.timedelta(0),
                                                                                fixDate_flex)
        else:
            if not flex.Aggregation_Computed:
                flex.compute_aggregated_Boundaries(av_periods)
            fixDate_flex = flex.compute_fixDateflex(start_time, duration, activation_time)
        fixDate_flex_list.append(fixDate_flex)

    return fixDate_flex_list

