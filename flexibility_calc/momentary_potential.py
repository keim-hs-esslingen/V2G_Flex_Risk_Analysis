from flexibility_calc.AggregatedFlex import  *


class momentaryPotential:
    time: datetime.timedelta = None
    strat_pos: int = None
    profiles: list = None
    total_energy_minus_strat: list = None
    total_power_minus_strat: list = None
    total_power_strat: int = None
    total_energy_strat: int = None
    total_energy: list = None
    total_power: list = None
    boundaries0: list = None
    boundaries1: list = None
    strategy_dependant_computed: bool = None
    strategy_independant_computed: bool = None

    def __init__(self, time, strat_pos, *args, **kwargs):
        super().__init__(**kwargs)
        self.strat_pos = strat_pos
        self.time = time
        self.profiles = list()
        self.boundaries0 = list()
        self.boundaries1 = list()
        self.total_energy_minus_strat = [0, 0]
        self.total_power_minus_strat = [0, 0]
        self.total_power_strat = 0
        self.total_energy_strat = 0
        self.total_power= [0, 0]
        self.total_energy = [0, 0]
        self.strategy_dependant_computed = False
        self.strategy_independant_computed = False

    def compute_momentary_profile_minus_strat(self, bdry):
        charge = True
        discharge = True
        if bdry.t_end - self.time > settingsContainer.getMinDeliveryTime():
            old_bdry = bdry.copy()
            if bdry.vehicle.ID == 13 and self.time == datetime.timedelta(seconds = 54000):
                kl = 0
            flex_profile_c = flex_profile(bdry, "charge", self.strat_pos)
            flex_profile_dc = flex_profile(bdry, "discharge", self.strat_pos)

            flex_profile_c.compute_flex_profile(self.time, bdry.t_max_end)
            flex_profile_dc.compute_flex_profile(self.time, bdry.t_min_end)
            # profile should be basis?!
            if flex_profile_c.available_time != None and flex_profile_c.available_time > settingsContainer.getMinDeliveryTime() and flex_profile_c.profile != None and settingsContainer.getChargingStrategies()[self.strat_pos] != "as soon as posible":

                #flex_profile_c.compute_flex_values() # overwrite
                self.append_profile_flex(flex_profile_c)

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
                #flex_profile_dc.compute_flex_values()
                self.append_profile_flex(flex_profile_dc)

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
        base_profile_c = base_profile(bdry, self.strat_pos, modus_pos)
        base_profile_c.compute_base_profile(self.time, bdry.t_max_end)
        if charge:
            self.append_profile_strat(base_profile_c, append_to_flex=True)


            if (((base_profile_c.energy > flex_profile_c.energy) and (
                    abs(base_profile_c.energy - flex_profile_c.energy) > 1e-8)) or base_profile_c.rate > flex_profile_c.rate):
                if flex_profile_c.energy != flex_profile_c.bdry.e_max:
                    print("Error: base profile shouldn't be larger than flex profile")
                else:
                    if self.strat_pos != 0:
                        print("hiiii")
        # always append base profile to strategy list
        self.append_profile_strat(base_profile_c, append_to_flex=False)

        modus_pos = 1
        # if not charge:
        #    base_profile_dc = base_profile_c#.copy()set_modus_pos(modus_pos)#.copy()
        # else:
        base_profile_dc = base_profile(old_bdry, self.strat_pos, modus_pos)
        base_profile_dc.compute_base_profile(self.time, old_bdry.t_min_end)
        if discharge:
            self.profiles.append(base_profile_dc)
            self.append_profile_strat(base_profile_dc, append_to_flex=True)
            if (flex_profile_dc.charge and (base_profile_dc.energy < flex_profile_dc.energy) and ((
                                                                                                          abs(base_profile_dc.energy - flex_profile_dc.energy) > 1e-8) or base_profile_dc.rate > flex_profile_dc.rate)):
                if flex_profile_dc.energy != flex_profile_dc.bdry.e_max:
                    print("Error: base profile shouldn't be larger than flex profile")
                else:
                    if self.strat_pos != 0:
                        print("hiii")
        self.strategy_dependant_computed = True

    def compute_momentary_profile_independant_of_strategy(self, bdry):
        if bdry.t_max_end - self.time > settingsContainer.getMinDeliveryTime():
            self.total_energy[0] += bdry.e_max
            if bdry.e_max != 0:
                self.total_power[0] += bdry.charging_power
                self.boundaries0.append(bdry)
        if bdry.t_min_end - self.time > settingsContainer.getMinDeliveryTime():
            self.total_energy[1] += bdry.e_min
            if bdry.e_min != 0:
                self.total_power[1] += bdry.discharging_power
                self.boundaries1.append(bdry)
            if bdry.e_min>0:
                print("Error: wrong assumption")
        self.strategy_independant_computed = True

    def getTotalEnergyMinusStrat(self):
        return self.total_energy_minus_strat

    def getTotalPowerMinusStrat(self):
        return self.total_power_minus_strat

    def getTotalEnergy(self):
        return self.total_energy

    def getTotalPower(self):
        return self.total_power

    def append_profile_flex(self, profile):
        if profile.modus == "charge":
            modus_pos = 0
        else:
            modus_pos = 1
        self.profiles.append(profile)
        # Todo vorueichen
        if modus_pos == 1 and not profile.charge:
            # if chraging in discharge mode substract from resulting energy/power
            rate = profile.rate
            energy = -profile.energy
        elif modus_pos == 1 and profile.charge:
            rate = -profile.rate
            energy = -profile.energy
        else:
            rate = profile.rate
            energy = profile.energy
        self.total_energy_minus_strat[modus_pos] += energy
        if energy != 0:
            self.total_power_minus_strat[modus_pos] += rate

    def append_profile_strat(self, profile, append_to_flex = True):

        #if profile.modus == "charge":
        #    modus_pos = 0
        #else:
        #    modus_pos = 1
        self.profiles.append(profile)
        if profile.modus_pos == 1 or not append_to_flex:
            rate = profile.rate
            energy = profile.energy
        else:
            rate = -profile.rate
            energy = -profile.energy

        if append_to_flex:
            self.total_energy_minus_strat[profile.modus_pos] += energy
            if energy != 0:
                self.total_power_minus_strat[profile.modus_pos] += rate
        else:
            self.total_energy_strat += energy
            if energy != 0:
                self.total_power_strat += rate


class momentary_potentials:
    times: list = None
    entries: list = None

    def __init__(self, *args, **kwargs):
        super().__init__(**kwargs)
        self.entries = list()
        self.times = list()

        for strat_pos in range(len(settingsContainer.getChargingStrategies())):
            self.entries.append([momentaryPotential(datetime.timedelta(0), strat_pos), momentaryPotential(datetime.timedelta(0), strat_pos)])
            self.times.append([datetime.timedelta(0), datetime.timedelta(hours = 24)])

    def CheckIfPotentialAlreadyComputed(self, time, strat_pos, minus_strat):
        idx = None
        if self.times[strat_pos].count(time) > 0:
            idx = self.times[strat_pos].index(time)

            if minus_strat:
                if self.entries[strat_pos][idx].strategy_dependant_computed:
                    return [True, idx]
                else:
                    return [False, idx]
            else:
                if self.entries[strat_pos][idx].strategy_independant_computed:
                    return [True, idx]
                else:
                    return [False, idx]
        else:
            return [False, idx]

    def append_entry(self, time, strat_pos, mom_pot, count):
        new_count = find_first_entry_with_larger_time_and_insert(self.times[strat_pos], count, time)
        #if self.times[strat_pos][new_count]!= time:
            # no inseertion already computed --> should be updated by copy by referenc #todo check this

        self.entries[strat_pos].insert(new_count, mom_pot)
        #elif time == datetime.timedelta(0):
        #    self.entries[strat_pos].__delitem__(0)
        #    self.entries[strat_pos].insert(0, mom_pot)
        #elif time == datetime.timedelta(hours = 24):
        #    self.entries[strat_pos].__delitem__(-1)
       #     self.entries[strat_pos].insert(-1, mom_pot)

    def getAndComputeMomentaryPotentialAt(self, time, strat_pos, count, AggFlex, minus_strat = True):

        alreadyComputed, idx = self.CheckIfPotentialAlreadyComputed(time, strat_pos, minus_strat)
        if not alreadyComputed:
            charging_strategy = settingsContainer.getChargingStrategies()[strat_pos]
            if idx == None:

                momentary_potential = momentaryPotential(time, strat_pos)
                append = True
            else:
                momentary_potential = self.entries[strat_pos][idx]
                append = False
            for pos in range(len(AggFlex.FlexBoundaries)):
                # if pos == 68:
                # print("hi")
                FlexBoundary = AggFlex.FlexBoundaries[pos]

                if AggFlex.days[
                    pos] > FlexBoundary.available_period.days and FlexBoundary.t_start < FlexBoundary.t_end:
                    print("Error, days")


                # e_curr_new, ch_rate, time_start_charging_for_e_need = compute_new_e_curr(charging_strategy, FlexBoundary, self.start, AggregatedFlex.capacities[pos])
                old_day = AggFlex.days[pos]
                # if pos ==28:
                #   print("hi")
                energy = compute_charged_until_certain_time_according_to_Charging_strategy(FlexBoundary,
                                                                                           time + datetime.timedelta(
                                                                                               days=old_day),
                                                                                           charging_strategy)

                new_bdry = FlexBoundary.copy_and_change(time, FlexBoundary.e_curr + energy, old_day)
                # new_bdry.compute_boundaries(True) #evtl weg
                new_bdry.compute_simple_times()  #
                if minus_strat:
                    momentary_potential.compute_momentary_profile_minus_strat(new_bdry)
                else:
                    momentary_potential.compute_momentary_profile_independant_of_strategy(new_bdry)
                #if idx == None or len(self.times[strat_pos]==2):
            if append:
                self.append_entry(time, strat_pos, momentary_potential, count)
        else:
            #index = idx #self.times[strat_pos].index(time)
            momentary_potential = self.entries[strat_pos][idx]
        if minus_strat:
            energy = momentary_potential.getTotalEnergyMinusStrat()
            power = momentary_potential.getTotalPowerMinusStrat()
        else:
            energy = momentary_potential.getTotalEnergy()
            power = momentary_potential.getTotalPower()
        return energy, power


def find_first_entry_with_larger_time_and_insert(flex_list, count, reference_time):
    while count < len(flex_list)-1 and flex_list[count] < reference_time:
        count += 1
    #if count > len(flex_list)-1:
        #print("hi")
    if flex_list[count] > reference_time:
        # and insert new entry right before this time
        flex_list.insert(count, reference_time)
    return count

def compute_mom_potential(DayList, times, strategies, NumberOfDays, NumberOfRuns, start_daytype, Flex_place = "Home", numberofday=-1, Daytype=0, minus_strat = True ):
    day_type = int(Daytype)

    if day_type < -1 or day_type > 7:
        print("Error: wrong daytype, insert value between -1,0 = Unknown, 1 = Monday, 2 = Tuesday,7 = Sunday...")

    # list, which days to compute spontanflex of
    if numberofday >= 0 and numberofday < len(DayList[0]):
        Days = [numberofday]
        if day_type <= -1:
            if DayList[0][numberofday].day_type != day_type:
                print("Error: daytype and number of day do not fit together. Spontanflex computed for inserted number of day")
    elif numberofday < 0:
        Days = compute_day_list(day_type, start_daytype, NumberOfDays)
    else:
        print("Error: number of day not simulated")
        return

    momentary_potential_list = [list() for strat in strategies]
    for run in range(NumberOfRuns):
        for day in Days:

            if Flex_place == "Home":
                flex = DayList[run][day].Flexibility_Home
                av_periods = DayList[run][day].compute_available_periods_at_home()
            elif Flex_place == "Work":
                flex = DayList[run][day].Flexibility_Work
                av_periods = DayList[run][day].compute_available_periods_at_work()
            else:
                flex = DayList[run][day].Flexibility_All
                av_periods = DayList[run][day].available_periods

            if not flex.Aggregation_Computed:
                flex.compute_aggregated_Boundaries(av_periods)
            strat_num = 0
            for strat_pos in strategies:
                energies, powers = flex.compute_momentary_potential(times, strat_pos, minus_strat)
                momentary_potential_list[strat_num].append([energies, powers])
                strat_num += 1

    return momentary_potential_list