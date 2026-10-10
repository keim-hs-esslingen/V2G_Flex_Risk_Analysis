import helper_files.variables

from flexibility_calc.Spontanflex import *
from flexibility_calc.fixdateflex import *
from flexibility_calc.Risk import *
from flexibility_calc.momentary_potential import *
from flexibility_calc.flex_dependancy import  *

class flex_on_day():
    flex_times_c: list = None
    flex_times_dc: list = None
    flex_capacities_c: list = None
    flex_capacities_dc: list = None
    power_times_ch: list = None
    power_times_dc: list = None
    Flex_list: list = None
    fixCharging_periods: list = list()
    power_cap_ch: list = None
    power_cap_dc: list = None
    flex_cap_c2: list = None
    Aggregation_Computed: bool = None
    spontanflexes_on_this_day: list = None
    fixDateflexes_on_this_day: list = None
    momentary_potentials: momentary_potentials = None


    def __init__(self, number_of_day, **kwargs):
        super().__init__(**kwargs)
        self.flex_times_dc = list()
        self.flex_times_c = list()
        self.flex_capacities_c = list()
        self.flex_capacities_dc = list()
        self.power_times_ch = list()
        self.power_times_dc = list()
        self.Flex_list = list()

        self.power_cap_ch = list()
        self.power_cap_dc = list()
        self.Aggregation_Computed = False
        self.spontanflexes_on_this_day = list()
        self.fixDateflexes_on_this_day = list()
        self.number_of_day = number_of_day
        self.momentary_potentials = momentary_potentials()

    def copy(self):
        new_flex_on_day = flex_on_day(self.number_of_day)
        new_flex_on_day.flex_times_dc = self.flex_times_dc
        new_flex_on_day.flex_times_c = self.flex_times_c
        new_flex_on_day.flex_capacities_c= self.flex_capacities_c
        new_flex_on_day.flex_capacities_dc = self.flex_capacities_dc
        new_flex_on_day.power_times_ch= self.power_times_ch
        new_flex_on_day.power_times_dc = self.power_times_dc
        new_flex_on_day.Flex_list = self.Flex_list
        new_flex_on_day.fixCharging_periods = self.fixCharging_periods
        new_flex_on_day.power_cap_ch= self.power_cap_ch
        new_flex_on_day.power_cap_dc = self.power_cap_dc
        new_flex_on_day.flex_cap_c2 = self.flex_cap_c2
        new_flex_on_day.Aggregation_Computed = self.Aggregation_Computed
        new_flex_on_day.spontanflexes_on_this_day = list()
        new_flex_on_day.fixDateflexes_on_this_day = list()
        return new_flex_on_day

    def compute_times_of_day(self, available_periods_of_day):
        if not CPCV:
            # possible Todo: min_start/max_start to add if not simple mode

            # list which contains all times of changes in capacity during this day
            self.flex_times_c.append(datetime.timedelta(0))
            self.flex_times_c.append(datetime.timedelta(days=1))

            # list which contains all times of changes in capacity during this day
            self.flex_times_dc.append(datetime.timedelta(0))
            self.flex_times_dc.append(datetime.timedelta(days=1))

            # list which contains all times of changes in power during this day
            self.power_times_dc.append(datetime.timedelta(0))
            self.power_times_dc.append(datetime.timedelta(days=1))

            # list which contains all times of changes in power during this day
            self.power_times_ch.append(datetime.timedelta(0))
            self.power_times_ch.append(datetime.timedelta(days=1))
            ap_c = 0
            # compute relevant times of day
            for entry in available_periods_of_day:
                if len(entry)==0:
                    continue
                periods = entry[0]
                #if periods.start
                ev = entry[1]
                if settingsContainer.getUserInteractionSimulation():
                    ev.compute_soc_min(ev.user.range, settingsContainer.getMinSoc())
                else:
                    ev.compute_min_energy(0.5, 0.35, settingsContainer.getMinSoc())
                count = 0
                count_dc = 0
                count_c_pow = 0
                count_dc_pow = 0

                for period in periods:

                    # string_field = list()
                    bool_table_of_times = list()
                    for i in range(9):
                        bool_table_of_times.append(False)
                    # contains boolean if times at idx is during this day or other days:
                    # index on 0: start_time, 1: max_end_time,2: min_end_time, 3: min_start2_time, 4: end_time
                    # no resets of count, count_dc necessary, as previous periods end before current period
                    if period.__class__ == helper_files.variables.AvailablePeriod:
                        if False:
                            # adapt period, s. t. it does not contain charging to min energy, which belongs to base charging
                            # not calculated during simulation, so that min_range/energy is flexible
                            start_energy = period.start_SOC * ev.battery_size * 0.01
                            if start_energy < ev.min_energy:
                                # start_time of available_period, when min_SOC/min_range is reached
                                new_start_time = ev.time_to_charge(ev.min_energy - start_energy, period.charging_power) + period.start_time
                                old_start_time = period.start_time
                                old_start_SOC = period.start_SOC

                                # adapt start_SOC correspondingly
                                new_start_SOC = (ev.min_energy/ev.battery_size) * 100
                                period.change_start(new_start_time, new_start_SOC)

                                # add charging to min_range/SOC to fix_charging_periods
                                self.fixCharging_periods.append([new_start_time - old_start_time, old_start_time, old_start_SOC, ev, period.charging_power])

                        # start = time.time()
                        Flex = compute_flex_bdry(period, ev)
                        # end = time.time()
                        # print("Flex computed")
                        # print(end-start)
                        # print("flex computed")
                        for i in range(9):
                            bool_table_of_times[i] = True
                        self.Flex_list.append([Flex, bool_table_of_times, 0])

                        # find first entry in current flex_list which has a time larger than this periods entry_start_time
                        # and insert new entry before this time
                        count = find_first_entry_with_larger_time_and_insert(self.flex_times_c, count, Flex.t_start)
                        count_dc = find_first_entry_with_larger_time_and_insert(self.flex_times_dc, count_dc, Flex.t_start)

                        # find first entry in current flex_list which has a time larger than this periods max_end/min_end time
                        count = find_first_entry_with_larger_time_and_insert(self.flex_times_c, count, Flex.t_max_end)
                        count_dc = find_first_entry_with_larger_time_and_insert(self.flex_times_dc, count_dc, Flex.t_min_end)

                        # find first entry in current flex_list which has a time larger than this periods end time
                        count = find_first_entry_with_larger_time_and_insert(self.flex_times_c, count, Flex.t_end)
                        count_dc = find_first_entry_with_larger_time_and_insert(self.flex_times_dc, count_dc, Flex.t_min_start2)
                        count_dc = find_first_entry_with_larger_time_and_insert(self.flex_times_dc, count_dc, Flex.t_end)


                        # find first entry in current flex_list which has a time larger than this periodsc harging start time
                        count_c_pow = find_first_entry_with_larger_time_and_insert(self.power_times_ch, count_c_pow, Flex.charging_start)
                        count_dc_pow = find_first_entry_with_larger_time_and_insert(self.power_times_dc, count_dc_pow, Flex.discharging_start)

                        # find first entry in current flex_list which has a time larger than this periodsc harging start time
                        count_c_pow = find_first_entry_with_larger_time_and_insert(self.power_times_ch, count_c_pow,
                                                                        Flex.charging_stop)
                        count_dc_pow = find_first_entry_with_larger_time_and_insert(self.power_times_dc, count_dc_pow,
                                                                         Flex.discharging_stop)
                        # print("other things computed")
                        # print(time.time()-end)
                    else:
                        if False:
                            start_energy = period[0].start_SOC * ev.battery_size * 0.01

                            day_adaption = False
                            if start_energy < ev.min_energy:

                                # start_time of available_period, when min_SOC/min_range is reached
                                new_start_time = ev.time_to_charge(ev.min_energy - start_energy,
                                                                   period[0].charging_power) + period[0].start_time
                                if new_start_time < period[0].start_time:
                                    # new start_time on next day (assumption: charging lasts less than one day)
                                    if period[1]==0:
                                        periods.remove(period)
                                        period[0].update_adaption_list(period[1])
                                        #available_periods_of_day[ap_c][0].remove(period)
                                        break

                                    else:
                                        #period[0].days -=1

                                        day_adaption = True
                                        period[0].update_adaption_list(period[1])
                                        period[1]-=1 # day on current period is updated


                                old_start_time = period[0].start_time
                                old_start_SOC = period[0].start_SOC

                                # adapt start_SOC correspondingly
                                new_start_SOC = (ev.min_energy / ev.battery_size) * 100
                                period[0].change_start(new_start_time, new_start_SOC, day_adaption)

                                # add charging to min_range/SOC to fix_charging_periods
                                self.fixCharging_periods.append(
                                    [new_start_time - old_start_time, old_start_time, old_start_SOC, ev,
                                     period[0].charging_power])
                            if period[0].day_adaption and day_adaption == False:
                                period[0].update_adaption_list(period[1])
                                period[1] -= 1


                        # start = time.time()
                        Flex = compute_flex_bdry(period[0], ev)



                        # end = time.time()
                        # print("Flex computed")
                        # print(end - start)
                        # print("flex computed")
                        if period[1] == 0:
                            # period starts at this day and lasts overnight
                            # find first entry in current flex_list which has a time larger than this periods entry_start_time
                            # and insert new entry before this time
                            count = find_first_entry_with_larger_time_and_insert(self.flex_times_c, count, Flex.t_start)
                            count_dc = find_first_entry_with_larger_time_and_insert(self.flex_times_dc, count_dc, Flex.t_start)
                            bool_table_of_times[0] = True
                        else:
                            # time of period on this day is not at the end, but on the start, so reset counts,
                            # otherwise no reset necessary, as other periods end before this period
                            count = 0
                            count_dc = 0
                        if period[1] == Flex.t_max_end.days:
                            # find first entry in current flex_list which has a time larger than this periods max_end
                            # substract days, such that only timedeltas < datetime.timedelta(days=1) are in list
                            count = find_first_entry_with_larger_time_and_insert(self.flex_times_c, count,
                                                                      Flex.t_max_end - datetime.timedelta(
                                                                          days=Flex.t_max_end.days))
                            bool_table_of_times[1] = True
                        if period[1] == Flex.t_min_end.days:
                            # substract days, such that only timedeltas < datetime.timedelta(days=1) are in list
                            count_dc = find_first_entry_with_larger_time_and_insert(self.flex_times_dc, count_dc,
                                                                         Flex.t_min_end - datetime.timedelta(
                                                                             days=Flex.t_min_end.days))
                            bool_table_of_times[2] = True
                        if period[1] == Flex.t_min_start2.days:
                            # substract days, such that only timedeltas < datetime.timedelta(days=1) are in list
                            count_dc = find_first_entry_with_larger_time_and_insert(self.flex_times_dc, count_dc,
                                                                         Flex.t_min_start2 - datetime.timedelta(
                                                                             days=Flex.t_min_start2.days))
                            bool_table_of_times[3] = True

                        if period[1] == Flex.t_end.days:
                            # substract days, such that only timedeltas < datetime.timedelta(days=1) are in list
                            count_dc = find_first_entry_with_larger_time_and_insert(self.flex_times_dc, count_dc,
                                                                         Flex.t_end - datetime.timedelta(
                                                                             days=Flex.t_end.days))
                            count = find_first_entry_with_larger_time_and_insert(self.flex_times_c, count,
                                                                      Flex.t_end - datetime.timedelta(
                                                                          days=Flex.t_end.days))
                            bool_table_of_times[4] = True

                        if period[1] == Flex.charging_start.days:
                            # substract days, such that only timedeltas < datetime.timedelta(days=1) are in list
                            count_c_pow = find_first_entry_with_larger_time_and_insert(self.power_times_ch, count_c_pow,
                                                                         Flex.charging_start - datetime.timedelta(
                                                                             days=Flex.charging_start.days))
                            bool_table_of_times[5] = True

                        if period[1] == Flex.charging_stop.days:
                            # substract days, such that only timedeltas < datetime.timedelta(days=1) are in list
                            count_c_pow = find_first_entry_with_larger_time_and_insert(self.power_times_ch, count_c_pow,
                                                                         Flex.charging_stop - datetime.timedelta(
                                                                             days=Flex.charging_stop.days))
                            bool_table_of_times[7] = True

                        if period[1] == Flex.discharging_start.days:
                            # substract days, such that only timedeltas < datetime.timedelta(days=1) are in list
                            count_c_pow = find_first_entry_with_larger_time_and_insert(self.power_times_dc, count_dc_pow,
                                                                         Flex.discharging_start - datetime.timedelta(
                                                                             days=Flex.discharging_start.days))
                            bool_table_of_times[6] = True

                        if period[1] == Flex.discharging_stop.days:
                            # substract days, such that only timedeltas < datetime.timedelta(days=1) are in list
                            count_c_pow = find_first_entry_with_larger_time_and_insert(self.power_times_dc, count_dc_pow,
                                                                         Flex.discharging_stop - datetime.timedelta(
                                                                             days=Flex.discharging_stop.days))
                            bool_table_of_times[8] = True

                        self.Flex_list.append([Flex, bool_table_of_times, period[1]])

                        if period[1] > Flex.available_period.days and Flex.t_start < Flex.t_end:
                            print("Error, days344")
                        # Test_times(flex_list_times_c)
                        # print("other things computed")
                        # print((time.time() - end))
                        # print("%0.4f" % (time.time() - end))
                ap_c+=1


    def compute_aggregated_Boundaries(self, available_periods):


        if self.Aggregation_Computed:
            return
        self.compute_times_of_day(available_periods)
        # initialize capacity lists with AggregatedFlex objects
        for ii in range(len(self.flex_times_c)):
            if ii > 0:
                self.flex_capacities_c.append(AggregatedFlex(self.flex_times_c[ii - 1], self.flex_times_c[ii]))
            else:
                self.flex_capacities_c.append(AggregatedFlex(self.flex_times_c[ii], self.flex_times_c[ii]))
        for ii in range(len(self.flex_times_dc)):
            if ii > 0:
                self.flex_capacities_dc.append(AggregatedFlex(self.flex_times_dc[ii - 1], self.flex_times_dc[ii]))
            else:
                self.flex_capacities_dc.append(AggregatedFlex(self.flex_times_dc[ii], self.flex_times_dc[ii]))

        for ii in range(len(self.power_times_dc)):
            if ii > 0:
                self.power_cap_dc.append(AggregatedFlex(self.power_times_dc[ii - 1], self.power_times_dc[ii]))
            else:
                self.power_cap_dc.append(AggregatedFlex(self.power_times_dc[ii], self.power_times_dc[ii]))

        for ii in range(len(self.power_times_ch)):
            if ii > 0:
                self.power_cap_ch.append(AggregatedFlex(self.power_times_ch[ii - 1], self.power_times_ch[ii]))
            else:
                self.power_cap_ch.append(AggregatedFlex(self.power_times_ch[ii], self.power_times_ch[ii]))



        counttt = 0
        # compute capacity at all times
        for entry in self.Flex_list:
            # if counttt == 0:
            # print("Stop")
            # go through the list with all flex_boundaries, find corresponding times in flex_times_c/dc list
            # and add capacities at these times
            Flex = entry[0]  # Flex_Boundary
            

            #if Flex.t_start>datetime.timedelta(seconds = 39659) and Flex.t_start < datetime.timedelta(seconds = 40000):
                #print("hi")
            bool_table_of_times = entry[1]  # which times of Flex_Boundary are during this day
            # for testing
            day = entry[2]
            if day > Flex.available_period.days and Flex.t_start < Flex.t_end:
                print("Error, days")
            idx_c_1 = None
            idx_c_2 = None
            idx_dc_1 = None
            idx_dc_2 = None
            idx_pow_1 = None
            idx_pow_2 = None
            # substract days, such that only timedeltas < datetime.timedelta(days=1) are in list
            times = [Flex.t_start - datetime.timedelta(Flex.t_start.days),
                     Flex.t_max_end - datetime.timedelta(Flex.t_max_end.days),
                     Flex.t_min_end - datetime.timedelta(Flex.t_min_end.days),
                     Flex.t_min_start2 - datetime.timedelta(Flex.t_min_start2.days),
                     Flex.t_end - datetime.timedelta(Flex.t_end.days),
                     Flex.charging_start - datetime.timedelta(Flex.charging_start.days),
                     Flex.discharging_start - datetime.timedelta(Flex.discharging_start.days),
                     Flex.charging_stop - datetime.timedelta(Flex.charging_stop.days),
                     Flex.discharging_stop - datetime.timedelta(Flex.discharging_stop.days)]


            for case in range(9):
                #if abs(times[case]-datetime.timedelta(seconds = 36610))<datetime.timedelta(seconds = 1) :
                  #  print("hi")
                if case <=4:
                    # only if time is on this day or end_time (case4) is not on this day
                    if bool_table_of_times[case] or case == 4:
                        # case0, case4 for charge (max) and discharge (min) boundaries
                        charge = True
                        discharge = True
                        if case == 1:
                            # only max boundaries (charge)
                            discharge = False
                        elif case == 2 or case == 3:
                            # only min boundaries (discharge)
                            charge = False

                        if charge:
                            if idx_c_1 == None:
                                # if this is the first loop run (case==0) or on earlier loop runs
                                # bool_table_of_times[case] was False (times not on this day)
                                idx_c_1 = 0  # start_index for changes in max_boundary
                            if idx_c_2 != None and case > 0:
                                # case 1 or 4: if on some earlier loop runs
                                # bool_table_of_times[case] was True (time on this day)
                                # start_index is the old one +1 (old one already updated)
                                idx_c_1 = idx_c_2 + 1

                            if bool_table_of_times[case]:
                                # time is on this day, so find it
                                idx_c_2 = self.flex_times_c.index(times[case], max(idx_c_1 - 2, 0))

                            else:
                                # case 4: end_time not on this day, so until end of day update all entries
                                idx_c_2 = len(self.flex_times_c) - 1

                            if case > 0:
                                # if case == 0, no updates necessary, as in this loop_run only the index is calculated,
                                # until these indices, no updates necessary (charging starts at earliest at start_time
                                if idx_c_1 <= idx_c_2:
                                    # for all entries between these indices, compute how the max_boundary changes
                                    # if some times are the same (f. e. : t_end = t_max_end): no updates,
                                    # as there are no indices between these times
                                    for idx in range(idx_c_1, idx_c_2 + 1):
                                        # update entries by max_boundary

                                        if case == 1 or (
                                                case == 4 and not bool_table_of_times[case] and not bool_table_of_times[
                                            1] and bool_table_of_times[0]):  # max_boundaries change until max_end
                                            # if t_max_start is during this day or
                                            # t_max_start and t-end not on this day, but t_start
                                            # --> charging between indices
                                            if (case == 1 and idx == idx_c_2):
                                                # fully charged, no computation necessary
                                                if idx == idx_c_1:
                                                    self.flex_capacities_c[idx].append_entry(Flex, Flex.e_max,
                                                                                         "max_at_start", day)
                                                else:
                                                    self.flex_capacities_c[idx].append_entry(Flex, Flex.e_max, "max", day)
                                            else:
                                                if idx == idx_c_1 and bool_table_of_times[0]:
                                                    modus = "ch_start"
                                                else:
                                                    modus = "charge_to_max"

                                                cap = Flex.vehicle.charge(
                                                        self.flex_times_c[idx] - self.flex_times_c[max(idx_c_1 - 1, 0)],
                                                        Flex.charging_power)
                                                self.flex_capacities_c[idx].append_entry(Flex, cap, modus, day)
                                                if not bool_table_of_times[0]:
                                                    # if t_start not on this day (in case 1),
                                                    # then energy_capacity computed above is not complete,
                                                    # as some charging happened on day before
                                                    # therefore, add one day, as Flex.t_start is one day earlier (assumption, that charging will not last more than one day
                                                    # possible TODO adaption for other "new" charging strategies: charging over more than 24 hours maybe possible
                                                    cap = Flex.vehicle.charge(self.flex_times_c[max(idx_c_1 - 1,0)]+datetime.timedelta(days = 1) - Flex.t_start,
                                                                                  Flex.charging_power)
                                                    self.flex_capacities_c[idx].add_capacity_on_entry(-1, cap)

                                        elif case == 4:  # max_boundary change by e_max
                                            # if t_end on this day or
                                            #  if t_end, t_max_end, t_start not on this day or
                                            # if t_end not on this day, but t_max_end
                                            # --> all indices increase by e_max
                                            self.flex_capacities_c[idx].append_entry(Flex, Flex.e_max, "max", day)

                                    # otherwise no changes to compute, as no entries between start and max_end
                            elif idx_c_2 == 0:
                                idx_c_2 -= 1  # as in next runs, this index will be increased
                        if discharge:
                            if idx_dc_1 == None:
                                # if this is the first loop run (case==0) or on earlier loop runs bool_table_of_times[case] was False (times not on this day)
                                idx_dc_1 = 0
                            if idx_dc_2 != None and case > 0:
                                # case 2,3 or 4: if on some earlier loop runs bool_table_of_times[case]
                                # was True (time on this day)
                                # start_index is the old one +1 (old one already updated)
                                idx_dc_1 = idx_dc_2 + 1
                            # find time entry
                            if bool_table_of_times[case]:
                                idx_dc_2 = self.flex_times_dc.index(times[case], max(idx_dc_1 - 2, 0))
                            else:
                                # case 4: time not on this day, so until end of day update all entries
                                idx_dc_2 = len(self.flex_times_dc) - 1

                            if case > 0:
                                # if case == 0, no updates necessary, as in this loop_run only the index is calculated, but until these indeces no updates necessary
                                if idx_dc_1 <= idx_dc_2:
                                    # for all entries between these indices, compute how the min_boundary changes
                                    for idx in range(idx_dc_1, idx_dc_2 + 1):
                                        # update entries by min_boundary
                                        if case == 2 or (
                                                case == 4 and not bool_table_of_times[case] and not bool_table_of_times[
                                            2] and not bool_table_of_times[3] and bool_table_of_times[
                                                    0]):  # min_boundaries change until min_end
                                            # if t_max_end is during this day or
                                            # if t_end, t_min_end, t_min_start2 not during this day, but t_start
                                            # --> discharging between indices
                                            if case == 2 and idx == idx_dc_2:
                                                # if t_min_end, then last entry is e_min
                                                if idx == idx_dc_1:
                                                    self.flex_capacities_dc[idx].append_entry(Flex, Flex.e_min, "min_at_start", day)
                                                else:
                                                    self.flex_capacities_dc[idx].append_entry(Flex, Flex.e_min, "min", day)
                                            else:
                                                # discharge energy: energy from time of start_index until current_index
                                                if Flex.e_min < 0:
                                                    if idx == idx_c_1 and bool_table_of_times[0]:
                                                        modus = "dc_start"
                                                    else:
                                                        modus = "discharge_to_min"
                                                    # only, if e_min is negative: discharging: (negative energy)
                                                    cap = Flex.vehicle.discharge(
                                                        self.flex_times_dc[idx]  - self.flex_times_dc[max(idx_dc_1 - 1,0)],
                                                        Flex.discharging_power)
                                                    self.flex_capacities_dc[idx].append_entry(Flex, -cap,
                                                                                              modus, day)
                                                    if not bool_table_of_times[0]:
                                                        # if t_start not on this day, then energy computed above
                                                        # contains only energy charged from time of start_index,
                                                        # but energy charged on day before since t_start has to be added
                                                        cap = Flex.vehicle.discharge(
                                                            self.flex_times_dc[max(idx_dc_1 - 1,0)] + datetime.timedelta(days = 1) - Flex.t_start,
                                                            Flex.discharging_power)
                                                        self.flex_capacities_dc[idx].add_capacity_on_entry(-1, -cap)
                                                else:
                                                    if idx == idx_c_1 and bool_table_of_times[0]:
                                                        modus = "ch_min_start"
                                                    else:
                                                        modus = "charge_to_min"
                                                    # if e_min is positive, charge until e_min
                                                    cap = Flex.vehicle.charge(
                                                        self.flex_times_dc[idx] - self.flex_times_dc[max(idx_dc_1 - 1,0)],
                                                        Flex.charging_power)
                                                    self.flex_capacities_dc[idx].append_entry(Flex, cap, "charge_to_min",
                                                                                              day)
                                                    if not bool_table_of_times[0]:
                                                        # if t_start not on this day, then energy computed above
                                                        # contains only energy charged from time of start_index,
                                                        # but energy charged on day before since t_start has to be added
                                                        cap = Flex.vehicle.charge(
                                                            self.flex_times_dc[max(idx_dc_1 - 1,0)] + datetime.timedelta(days = 1) - Flex.t_start,
                                                            Flex.charging_power)
                                                        self.flex_capacities_dc[idx].add_capacity_on_entry(-1, cap)



                                        elif case == 3 or (
                                                case == 4 and not bool_table_of_times[case] and not bool_table_of_times[
                                            3] and (bool_table_of_times[2] or (
                                                not bool_table_of_times[2] and not bool_table_of_times[0]))):
                                            # if t_min_start2 is during this day or
                                            # if t_end, t_min_start2 not on this day, but t_min_end or
                                            # if t_end, t_min_start2, t_min_end, t_start not on this day
                                            # -->add e_min between indices
                                            self.flex_capacities_dc[idx].append_entry(Flex, Flex.e_min, "min", day)
                                        elif case == 4:  # min_boundary change until t_end
                                            # if t_end is during this day
                                            # if t_end is  ´not during this day, but t_min_end
                                            if idx == idx_dc_2 and bool_table_of_times[case]:
                                                self.flex_capacities_dc[idx].append_entry(Flex, Flex.e_need, "need", day)
                                            else:
                                                cap = Flex.vehicle.charge(
                                                    self.flex_times_dc[idx] - self.flex_times_dc[max(idx_dc_1 - 1,0)],
                                                    Flex.charging_power) + Flex.e_min
                                                self.flex_capacities_dc[idx].append_entry(Flex, cap, "charge_to_need", day)
                                                if not bool_table_of_times[3]:
                                                    # if t_min_start2 not during this day, then some energy is charged
                                                    # on day before and has to be concerned as well

                                                    cap = Flex.vehicle.charge(
                                                        self.flex_times_dc[max(idx_dc_1 - 1,0)] - Flex.t_min_start2,
                                                        Flex.charging_power)
                                                    self.flex_capacities_dc[idx].add_capacity_on_entry(-1, cap)
                                    # otherwise no changes to compute, as no entries between start and min_end
                            elif idx_dc_2 == 0:
                                idx_dc_2 -= 1  # as in next runs, this index will be increased
                elif case == 7 or case == 8:
                    # compute start and end indices of (dis)charging_start/stop time
                    if case == 7:
                        #charging
                        start_idx = 5
                        times_list = self.power_times_ch
                        cap_list = self.power_cap_ch
                    else:
                        #discharging
                        start_idx = 6
                        times_list = self.power_times_dc
                        cap_list = self.power_cap_dc
                    if bool_table_of_times[start_idx]:
                        # times on this day, so find it
                        idx_pow_1 = times_list.index(times[start_idx], 0)+1
                    elif not bool_table_of_times[0]:

                        idx_pow_1 = 0
                    else:
                        # c rare case, that t_start is on this day, while (dis)charging_start not
                        idx_pow_1 = len(times_list)
                    if bool_table_of_times[case]:

                        idx_pow_2 = times_list.index(times[case], max(idx_pow_1-3,0))
                    else:
                        idx_pow_2 = len(times_list)-1

                    if idx_pow_1 <= idx_pow_2:
                        # for all entries between these indices, compute how the power_boundary change
                        for idx in range(idx_pow_1, idx_pow_2 + 1):
                            if case == 7:
                                cap_list[idx].append_entry(Flex, Flex.charging_power, "charge", day )
                            elif case == 8:
                                cap_list[idx].append_entry(Flex, Flex.discharging_power, "discharge", day)


            counttt += 1
            # print(counttt)
        self.Aggregation_Computed = True

    def compute_spontanflex(self, start_time, duration, flex_place, computed_spontanflex = None, flex_dependant = False, flex_dependant_strat = None):
        end_time = start_time + duration
        if computed_spontanflex == None:
            # insert new time entry at time list for the start and adjust capacities of these entries to know max boundary
            #if start_time == datetime.timedelta(0):
            #    idx_start = 0
            #else:
            idx_start = self.insert_new_entry_at_certain_time(start_time)+1
            spontan_flex = Spontanflex(start_time, end_time, flex_place, self.number_of_day)
        else:
            spontan_flex = computed_spontanflex
            idx_start = 0 # will be incremented by 1 later

        # in both cases, idx_end has to be computed
        # if end_time > 24h not, but by calling this method nothing wrong happens
        idx_end = self.insert_new_entry_at_certain_time(end_time)
        strat_pos = 0

        for charging_strategy in settingsContainer.getChargingStrategies():
            if flex_dependant and flex_dependant_strat!= None:
                if settingsContainer.getChargingStrategies()[flex_dependant_strat] != charging_strategy:
                    #only to be computed for strategy on which flexibility is computed
                    strat_pos = strat_pos +1
                    continue


            if computed_spontanflex == None:
                # if computation of spontanflex hasn't started on previous day, start computation here
                # dependant of charging strategy, E_curr of all vehicles has to be calculated
                spontan_flex.compute_power_profiles_at_start(self.flex_capacities_c[idx_start], strat_pos)

            # check other indices until end time: here only flexBoundaries, which are new (modus = "start...")
            for idx in range(idx_start+1, idx_end+1):
                    new_entries = self.flex_capacities_c[idx].find_new_entries()
                    if len(new_entries) > 0:
                        for entry in new_entries:
                            # and append to profile_list
                            if computed_spontanflex != None:
                                # increment all times by one day, as times are stored in relation to this day,
                                # but already computed spontanflex works with last day
                                entry[0].increment_times_by_day()


                            #if strat_pos == 0:
                            #    spontan_flex.append_to_checked_list(entry)
                            if not spontan_flex.append_to_checked_lists(entry[0], entry[1], strat_pos):
                                # if this vehicle already is involved in flexibility_calc computation (activated by other avialable period)
                                continue

                            spontan_flex.compute_profiles(entry[0], strat_pos)
            for vehicle in spontan_flex.checked_flex_boundaries_vehicles[strat_pos]:
                # reset flex_active (used to control, that every vehicle is only used once
                vehicle.set_flex_active(False)



            strat_pos += 1


        spontan_flex.compute_kpis()

        self.spontanflexes_on_this_day.append(spontan_flex)
        return spontan_flex
    
    def compute_aggregated_Boundaries_with_charging_strategy_difference(self, strat_pos, heuristic_pos, modus_pos, pos_in_flex_list, spontan = True):
        #for power
        if spontan:
            flex = self.spontanflexes_on_this_day[pos_in_flex_list]
        else:
            flex = self.fixDateflexes_on_this_day[pos_in_flex_list]

        if len(flex.aggregated_bdry_and_charging_strategy[strat_pos][heuristic_pos][modus_pos]) > 0:
            return
        if modus_pos == 0: #power == True:
            list1 = self.power_cap_ch
        elif modus_pos == 1: # and power == True:
            list1 = self.power_cap_dc
        idx_start_agg = max(self.find_first_entry_with_larger_time(list1, 0, flex.start), 0)
        idx_end_agg = self.find_first_entry_with_larger_time(list1, idx_start_agg-1, flex.end) #+ 1
        list_to_append = list()
        for idx in range(idx_start_agg, idx_end_agg + 1):
            list_to_append.append([list1[idx].end_time, list1[idx].total_capacity])
        flex.compute_aggregated_Boundaries_with_charging_strategy_difference(strat_pos, heuristic_pos, modus_pos, list_to_append)

    def compute_standard_load_profile(self, strat_pos,  pos_in_flex_list, spontan = True):
        #for power
        if spontan:
            flex = self.spontanflexes_on_this_day[pos_in_flex_list]
        else:
            flex = self.fixDateflexes_on_this_day[pos_in_flex_list]

        if len(flex.standard_load_profile[strat_pos]) > 0:
            return
        list1 = self.power_cap_ch

        idx_start_agg = max(self.find_first_entry_with_larger_time(list1, 0, flex.start), 0)
        idx_end_agg = self.find_first_entry_with_larger_time(list1, idx_start_agg-1, flex.end) #+ 1
        list_to_append = list()
        for idx in range(idx_start_agg, idx_end_agg + 1):
            list_to_append.append([list1[idx].end_time, list1[idx].total_capacity])
        flex.compute_standard_load_profile(strat_pos, list_to_append)
        flex.compute_flex_without_standard_profile_simple(strat_pos)

    def compute_momentary_potential(self, times, strat_pos=0, minus_strat=True):

        energy_capacities = list()
        power_capacities = list()
        count = 0
        for time in times:
            idx_start = self.insert_new_entry_at_certain_time(time) + 1
            energy, power = self.momentary_potentials.getAndComputeMomentaryPotentialAt(time, strat_pos,
                                                                                        max(0, count - 1),
                                                                                        self.flex_capacities_c[
                                                                                            idx_start], minus_strat)
            energy_capacities.append(energy)
            power_capacities.append(power)
            count += 1
        return energy_capacities, power_capacities

    def compute_fixDateflex(self, start_time, duration, activation_time, flex_place, computed_fixDateflex = None, flex_dependant = False, flex_dependant_strat = None):
        end_time = start_time + duration
        if computed_fixDateflex == None:
            # insert new time entry at time list for the start and adjust capacities of these entries to know max boundary
            idx_start = self.insert_new_entry_at_certain_time(start_time) + 1
            fixDate_flex = fixDateflex(start_time, end_time, activation_time, flex_place, self.number_of_day)
        else:
            fixDate_flex = computed_fixDateflex

            idx_start = 0  # will be incremented by 1 later

        # in both cases, idx_end has to be computed
        # if end_time > 24h not, but by calling this method nothing wrong happens
        idx_end = self.insert_new_entry_at_certain_time(end_time)
        strat_pos = 0
        fixDate_flex.determine_relevant_boundaries(self.flex_capacities_c[idx_start])
        for charging_strategy in settingsContainer.getChargingStrategies():
            if flex_dependant and flex_dependant_strat!= None:
                if settingsContainer.getChargingStrategies()[flex_dependant_strat] != charging_strategy:
                    #only to be computed for strategy on which flexibility is computed
                    continue
            if computed_fixDateflex == None:
                # if computation of spontanflex hasn't started on previous day, start computation here
                # dependant of charging strategy, E_curr of all vehicles has to be calculated
                fixDate_flex.compute_fixDateflex_profiles_at_start(strat_pos)
            # check other indices until end time: here only flexBoundaries, which are new (modus = "start...")
            for idx in range(idx_start + 1, idx_end + 1):
                new_entries = self.flex_capacities_c[idx].find_new_entries()
                if len(new_entries) > 0:
                    for entry in new_entries:
                        # and append to profile_list
                        if computed_fixDateflex != None:
                            # increment all times by one day, as times are stored in relation to this day,
                            # but already computed spontanflex works with last day
                            entry[0].increment_times_by_day()

                        if not fixDate_flex.append_to_checked_lists(entry[0], entry[1], strat_pos):
                            # if this vehicle already is involved in flexibility_calc computation (activated by other avialable period)
                            continue

                        fixDate_flex.compute_profiles(entry[0], strat_pos, "charge", entry[0])
                        fixDate_flex.compute_profiles(entry[0], strat_pos, "discharge", entry[0])
                        #if strat_pos == 0:
                          #  fixDate_flex.append_to_checked_list(entry)

            for vehicle in fixDate_flex.checked_flex_boundaries_vehicles[strat_pos]:
                # reset flex_active (used to control, that every vehicle is only used once
                vehicle.set_flex_active(False)
            strat_pos += 1
        fixDate_flex.compute_kpis()
        self.fixDateflexes_on_this_day.append(fixDate_flex)
        return fixDate_flex

    def insert_new_entry_at_certain_time(self, time):
        # insert new entry to times_list containing start_time and corresponding FlexBoundaries,...
        idx = find_first_entry_with_larger_time_and_insert(self.flex_times_c, 0, time)
        # copy previous entry and then adjust times/capacities
        if len(self.flex_times_c) > len(self.flex_capacities_c):
            self.flex_capacities_c.insert(idx, self.flex_capacities_c[idx].copy())
            entry_to_change = self.flex_capacities_c[idx]

            # adjust times of entries
            self.flex_capacities_c[idx].end_time = time
            self.flex_capacities_c[idx + 1].start_time = time

            if self.flex_capacities_c[idx].start_time >= time or self.flex_capacities_c[idx+1].end_time <= time:
                print("Error: insert entry at time")

            i = 0
            # adjust FlexBoundaries and capacities
            while i < len(self.flex_capacities_c[idx].FlexBoundaries):
                #if i == 22:
                   # print("hi")
                # find FlexBoundaries, which are fully charged on next (copied) entry, but not on new entry
                modus = self.flex_capacities_c[idx].modi[i]
                if self.flex_capacities_c[idx].days[i] > 0:
                    time_new = time + datetime.timedelta(days=self.flex_capacities_c[idx].days[i])
                else:
                    time_new = time
                if modus == "ch_start": #or modus == "max": #or modus == "max_at_start":
                    #if modus == "max_at_start":
                    #print("hi")
                    self.flex_capacities_c[idx+1].change_modus("charge_to_max",i)#delete_entry(i)
                    if self.flex_capacities_c[idx].FlexBoundaries[i].t_start <= time_new:
                        # t_start has to be smaller than the compare time, as otherwise FlexBoundary starts on next entry
                        #self.flex_capacities_c[idx].modi[i] = "charge_to_max"
                        # update total_capacity
                        cap = self.flex_capacities_c[idx].FlexBoundaries[i].vehicle.charge(
                            time_new - self.flex_capacities_c[idx].FlexBoundaries[i].t_start,
                            self.flex_capacities_c[idx].FlexBoundaries[i].charging_power)
                        if self.flex_capacities_c[idx].capacities[i] > cap:
                            self.flex_capacities_c[idx].total_capacity -= self.flex_capacities_c[idx].capacities[
                                                                              i] - cap
                        else:
                            print("Error1-spontanflex")
                        self.flex_capacities_c[idx].capacities[i] = cap
                    #i-=1

                if modus == "max" or modus == "max_at_start":

                    if self.flex_capacities_c[idx].FlexBoundaries[i].t_max_end > time_new:
                        # if t_max_end is larger then the time to compare, we know, that the FlexBoundary changed to
                        # max modus on the next entry, but is not fully charged for this new inserted entry
                        if self.flex_capacities_c[idx].FlexBoundaries[i].t_start <= time_new:
                            # t_start has to be smaller than the compare time, as otherwise FlexBoundary starts on next entry
                            self.flex_capacities_c[idx].change_modus("charge_to_max",i)
                            # update total_capacity
                            cap = self.flex_capacities_c[idx].FlexBoundaries[i].vehicle.charge(
                                time_new - self.flex_capacities_c[idx].FlexBoundaries[i].t_start,
                                self.flex_capacities_c[idx].FlexBoundaries[i].charging_power)
                            if self.flex_capacities_c[idx].capacities[i] > cap:
                                self.flex_capacities_c[idx].total_capacity -= self.flex_capacities_c[idx].capacities[i] - cap
                            else:
                                print("Error1-spontanflex")
                            self.flex_capacities_c[idx].capacities[i] = cap
                        else:
                            print("halloooo")
                            if self.flex_capacities_c[idx].FlexBoundaries[i].t_start != self.flex_capacities_c[idx].FlexBoundaries[i].t_max_end:
                                print("Error3-Spontanflex ")
                            self.flex_capacities_c[idx].delete_entry(i)
                            i -= 1
                    #else:

                        #print("hi")
                        # adjust capacities of charging vehicles



                elif modus == "charge_to_max":
                    # adjust capacities of charging vehicles
                    cap = self.flex_capacities_c[idx].FlexBoundaries[i].vehicle.charge(
                        time_new - self.flex_capacities_c[idx].FlexBoundaries[i].t_start,
                        self.flex_capacities_c[idx].FlexBoundaries[i].charging_power)
                    if self.flex_capacities_c[idx].capacities[i] > cap:
                        self.flex_capacities_c[idx].total_capacity -= self.flex_capacities_c[idx].capacities[i] - cap
                    else:
                        print("Error2-spontanflex")
                    self.flex_capacities_c[idx].capacities[i] = cap
                i += 1


        return idx

    def insert_new_entry_at_certain_time2(self, time):
        # insert new entry to times_list containing start_time and corresponding FlexBoundaries,...
        idx = find_first_entry_with_larger_time_and_insert2(self.flex_times_c, 0, time)
        # copy previous entry and then adjust times/capacities
        if len(self.flex_times_c) > len(self.flex_capacities_c):
            self.flex_capacities_c.insert(idx, self.flex_capacities_c[idx].copy())
            entry_to_change = self.flex_capacities_c[idx]

            # adjust times of entries
            self.flex_capacities_c[idx].end_time = time
            self.flex_capacities_c[idx + 1].start_time = time

            if self.flex_capacities_c[idx].start_time >= time or self.flex_capacities_c[idx+1].end_time <= time:
                print("Error: insert entry at time")

            i = 0
            # adjust FlexBoundaries and capacities
            while i < len(self.flex_capacities_c[idx].FlexBoundaries):
                #if i == 22:
                   # print("hi")
                # find FlexBoundaries, which are fully charged on next (copied) entry, but not on new entry
                modus = self.flex_capacities_c[idx].modi[i]
                if self.flex_capacities_c[idx].days[i] > 0:
                    time_new = time + datetime.timedelta(days=self.flex_capacities_c[idx].days[i])
                else:
                    time_new = time
                if modus == "ch_start": #or modus == "max": #or modus == "max_at_start":
                    #if modus == "max_at_start":
                    #print("hi")
                    self.flex_capacities_c[idx+1].change_modus("charge_to_max",i)#delete_entry(i)
                    if self.flex_capacities_c[idx].FlexBoundaries[i].t_start <= time_new:
                        # t_start has to be smaller than the compare time, as otherwise FlexBoundary starts on next entry
                        #self.flex_capacities_c[idx].modi[i] = "charge_to_max"
                        # update total_capacity
                        cap = self.flex_capacities_c[idx].FlexBoundaries[i].vehicle.charge(
                            time_new - self.flex_capacities_c[idx].FlexBoundaries[i].t_start,
                            self.flex_capacities_c[idx].FlexBoundaries[i].charging_power)
                        if self.flex_capacities_c[idx].capacities[i] > cap:
                            self.flex_capacities_c[idx].total_capacity -= self.flex_capacities_c[idx].capacities[
                                                                              i] - cap
                        else:
                            print("Error1-spontanflex")
                        self.flex_capacities_c[idx].capacities[i] = cap
                    #i-=1

                if modus == "max" or modus == "max_at_start":

                    if self.flex_capacities_c[idx].FlexBoundaries[i].t_max_end > time_new:
                        # if t_max_end is larger then the time to compare, we know, that the FlexBoundary changed to
                        # max modus on the next entry, but is not fully charged for this new inserted entry
                        if self.flex_capacities_c[idx].FlexBoundaries[i].t_start <= time_new:
                            # t_start has to be smaller than the compare time, as otherwise FlexBoundary starts on next entry
                            self.flex_capacities_c[idx].modi[i] = "charge_to_max"
                            # update total_capacity
                            cap = self.flex_capacities_c[idx].FlexBoundaries[i].vehicle.charge(
                                time_new - self.flex_capacities_c[idx].FlexBoundaries[i].t_start,
                                self.flex_capacities_c[idx].FlexBoundaries[i].charging_power)
                            if self.flex_capacities_c[idx].capacities[i] > cap:
                                self.flex_capacities_c[idx].total_capacity -= self.flex_capacities_c[idx].capacities[i] - cap
                            else:
                                print("Error1-spontanflex")
                            self.flex_capacities_c[idx].capacities[i] = cap
                        else:
                            print("halloooo")
                            if self.flex_capacities_c[idx].FlexBoundaries[i].t_start != self.flex_capacities_c[idx].FlexBoundaries[i].t_max_end:
                                print("Error3-Spontanflex ")
                            self.flex_capacities_c[idx].delete_entry(i)
                            i -= 1
                    #else:

                        #print("hi")
                        # adjust capacities of charging vehicles



                elif modus == "charge_to_max":
                    # adjust capacities of charging vehicles
                    cap = self.flex_capacities_c[idx].FlexBoundaries[i].vehicle.charge(
                        time_new - self.flex_capacities_c[idx].FlexBoundaries[i].t_start,
                        self.flex_capacities_c[idx].FlexBoundaries[i].charging_power)
                    if self.flex_capacities_c[idx].capacities[i] > cap:
                        self.flex_capacities_c[idx].total_capacity -= self.flex_capacities_c[idx].capacities[i] - cap
                    else:
                        print("Error2-spontanflex")
                    self.flex_capacities_c[idx].capacities[i] = cap
                i += 1


        return idx

    def visualize_aggregated_boundaries(self, start_time, duration, modus, power = True, original_duration = datetime.timedelta(0), relative_to_start_time = False, positive = False):
        end_time = start_time + duration
        if modus =="charge" and power == False:
            list1 = self.flex_capacities_c
            color = "red"
        elif modus == "discharge" and power == False:
            list1 = self.flex_capacities_dc
            color = "blue"
        elif modus == "charge" and power == True:
            list1 = self.power_cap_ch
            color = "red"
        elif modus == "discharge" and power == True:
            list1 = self.power_cap_dc
            color = "blue"
        else:
            print("Error: wrong modus, viz_agg_bound")
            return
        if power:
            idx_start = max(self.find_first_entry_with_larger_time(list1, 0, start_time), 0)
            idx_end = self.find_first_entry_with_larger_time(list1, idx_start, end_time)+1
        else:
            idx_start = max(self.find_first_entry_with_larger_time(list1, 0, start_time), 0)
            idx_end = self.find_first_entry_with_larger_time(list1, idx_start, end_time) + 1
        x = list()
        y = list()
        for idx in range(idx_start, idx_end):
            if idx < idx_end:
                if original_duration > datetime.timedelta(0):
                    if relative_to_start_time:
                        x.append((list1[idx].start_time + original_duration - duration - start_time).total_seconds() / 60)
                        x.append((list1[idx].end_time + original_duration - duration - start_time).total_seconds() / 60)
                    else:
                        x.append((list1[idx].start_time +original_duration-duration).total_seconds()/3600)
                        x.append((list1[idx].end_time + original_duration - duration).total_seconds() / 3600)
                else:
                    if relative_to_start_time:
                        x.append((list1[idx].start_time - start_time).total_seconds() / 60)
                        x.append((list1[idx].end_time - start_time).total_seconds() / 60)
                    else:
                        x.append((list1[idx].start_time).total_seconds() / 3600)
                        x.append((list1[idx].end_time ).total_seconds() / 3600) # x.append((list1[idx].end_time - start_time).total_seconds() / 60)
            if power and modus == "discharge" and not positive:
                y.append(-list1[idx].total_capacity)
                y.append(-list1[idx].total_capacity)
            else:
                y.append(list1[idx].total_capacity)
                y.append(list1[idx].total_capacity)
        #plt.plot(x,y, color = color, alpha = 0.4)
        plt.plot(x,y, color = "purple", alpha = 0.8)

    def find_first_entry_with_larger_time(self, flex_list, count, reference_time):
            while count < len(flex_list) - 1 and flex_list[count].end_time < reference_time:
                count += 1
            #if count > len(flex_list) - 1:
                #print("hi")
            #if flex_list[count].end_time > reference_time:
                # and insert new entry right before this time
                #flex_list.insert(count, reference_time)
            return count


def find_first_entry_with_larger_time_and_insert(flex_list, count, reference_time):
    while count < len(flex_list)-1 and flex_list[count] < reference_time:
        count += 1
    #if count > len(flex_list)-1:
        #print("hi")
    if flex_list[count] > reference_time:
        # and insert new entry right before this time
        flex_list.insert(count, reference_time)
    return count

def find_first_entry_with_larger_time_and_insert2(flex_list, count, reference_time):
    while count < len(flex_list)-1 and flex_list[count].end_time < reference_time:
        count += 1
    #if count > len(flex_list)-1:
        #print("hi")
    if flex_list[count].end_time > reference_time:
        # and insert new entry right before this time
        flex_list.insert(count, reference_time)
    return count

def compute_flexibility(spontanflex, risk, all_DaysList, start_time, duration, NumberOfDays, start_daytype,
                            activation_time=datetime.timedelta(0), Flex_place="Home", numberofday=-1, Daytype=0,
                        run = 0, ignore_first_days = 0, flex_dependant = False, flex_object = None, co2 = False,
                        concrete_strat = None, flex_dependant_strat = False):
        if duration > datetime.timedelta(days=1):
            print("Error: flexibility_calc only computed for durations smaller than 24 hours")
            return
        day_type = Daytype

        if day_type > 7:
            print(
                "Error: wrong daytype, insert value smaller than 1 ( = Unknown) or  1 = Monday, 2 = Tuesday,7 = Sunday...")

        end_time = start_time + duration
        if run >= len(all_DaysList):
            print("Error: run parameter too large for computed Runs")
        # list, which days to compute spontanflex of
        if numberofday >= 0 and numberofday < len(all_DaysList[run]):
            Days = [numberofday]
            if day_type <= -1:
                if all_DaysList[run][numberofday].day_type != day_type:
                    print(
                        "Warning: daytype and number of day do not fit together. flexibility_calc computed for inserted number of day")
        elif numberofday < 0:
            if risk == False:
                print("Warning: for visualize a specific flexibility_calc, not more than one flexibility_calc has to be computed (number_of_day should be not negative). Flexibility is computed for last day")
                Days = [-1]
            else:
                Days = compute_day_list(day_type, start_daytype, NumberOfDays, ignore_first_days)

        else:
            print("Error: number of day not simulated")
            return

        # compute flexibility_calc


        flex_list = list()
        count_runs = 0

        for DayList in all_DaysList:
            try:
                if flex_dependant:
                    print(count_runs)
                if not risk and count_runs < run:
                    count_runs += 1
                    continue
                flex_day_list = list()
                count_days = 0
                for day in Days:

                    if flex_dependant:
                        print(day)
                    alreadyComputed = False
                    # print(day)
                    if not flex_dependant:
                        if Flex_place == "Home":
                            flexibility = DayList[day].Flexibility_Home
                            if spontanflex and useAlreadyComputedFlexibilities:
                                for ii in range(len(flexibility.spontanflexes_on_this_day)):
                                    if flexibility.spontanflexes_on_this_day[-ii].compare(start_time, activation_time, duration, Flex_place, spontanflex) == "same":
                                        flex = flexibility.spontanflexes_on_this_day[-ii]
                                        alreadyComputed = True
                                        break
                            elif not spontanflex and useAlreadyComputedFlexibilities:
                                for ii in range(len(flexibility.fixDateflexes_on_this_day)):
                                    if flexibility.fixDateflexes_on_this_day[-ii].compare(start_time, activation_time, duration, Flex_place, spontanflex) == "same":
                                        flex = flexibility.fixDateflexes_on_this_day[-ii]
                                        alreadyComputed = True
                                        break
                            if not alreadyComputed:
                                av_periods = DayList[day].compute_available_periods_at_home()
                                if end_time > datetime.timedelta(days=1):
                                    flexibility_next_day = DayList[day + 1].Flexibility_Home
                                    av_periods2 = DayList[day + 1].compute_available_periods_at_home()

                        elif Flex_place == "Work":
                            flexibility = DayList[day].Flexibility_Work
                            if spontanflex and useAlreadyComputedFlexibilities:
                                for ii in range(len(flexibility.spontanflexes_on_this_day)):
                                    if flexibility.spontanflexes_on_this_day[-ii].compare(start_time, activation_time, duration,
                                                                                          Flex_place, spontanflex) == "same":
                                        flex = flexibility.spontanflexes_on_this_day[-ii]
                                        alreadyComputed = True
                                        break
                            elif not spontanflex and useAlreadyComputedFlexibilities:
                                for ii in range(len(flexibility.fixDateflexes_on_this_day)):
                                    if flexibility.fixDateflexes_on_this_day[-ii].compare(start_time, activation_time, duration,
                                                                                          Flex_place, spontanflex) == "same":
                                        flex = flexibility.fixDateflexes_on_this_day[-ii]
                                        alreadyComputed = True
                                        break
                            if not alreadyComputed:
                                av_periods = DayList[day].compute_available_periods_at_work()
                                if end_time > datetime.timedelta(days=1):
                                    flexibility_next_day = DayList[day + 1].Flexibility_Work
                                    av_periods2 = DayList[day + 1].compute_available_periods_at_work()

                        else:
                            flexibility = DayList[day].Flexibility_All
                            if spontanflex and useAlreadyComputedFlexibilities:
                                for ii in range(len(flexibility.spontanflexes_on_this_day)):
                                    if flexibility.spontanflexes_on_this_day[-ii].compare(start_time, activation_time, duration, Flex_place, spontanflex) == "same":
                                        flex = flexibility.spontanflexes_on_this_day[-ii]
                                        alreadyComputed = True
                                        break
                            elif not spontanflex and useAlreadyComputedFlexibilities:
                                for ii in range(len(flexibility.fixDateflexes_on_this_day)):
                                    if flexibility.fixDateflexes_on_this_day[-ii].compare(start_time, activation_time, duration, Flex_place, spontanflex) == "same":
                                        flex = flexibility.fixDateflexes_on_this_day[-ii]
                                        alreadyComputed = True
                                        break
                            if not alreadyComputed:
                                av_periods = DayList[day].available_periods
                                if end_time > datetime.timedelta(days=1):
                                    flexibility_next_day = DayList[day + 1].Flexibility_All
                                    av_periods2 = DayList[day + 1].available_periods
                    else:
                        # flex_dependant == True
                        # not overnight for this case

                        alreadyComputed = False
                        if Flex_place == "Home":
                            flexibility = DayList[day].Flexibility_Home
                            av_periods = DayList[day].compute_available_periods_at_home()
                            #if end_time > datetime.timedelta(days=1):
                              #      flexibility_next_day = DayList[day + 1].Flexibility_Home
                               #     av_periods2 = DayList[day + 1].compute_available_periods_at_home()

                        elif Flex_place == "Work":
                            flexibility = DayList[day].Flexibility_Work
                            av_periods = DayList[day].compute_available_periods_at_work()
                            # end_time > datetime.timedelta(days=1):
                             #       flexibility_next_day = DayList[day + 1].Flexibility_Work
                                #    av_periods2 = DayList[day + 1].compute_available_periods_at_work()
                        else:
                            av_periods = DayList[day].available_periods
                            #if end_time > datetime.timedelta(days=1):
                                         #                   flexibility_next_day = DayList[day + 1].Flexibility_All
                                                        #    av_periods2 = DayList[day + 1].available_periods
                        available_periods = adapt_available_periods(flex_object,  day, start_time, count_runs, count_days,
                                                                    co2, concrete_strat)
                        Test_adapt_available_periods(flex_object, count_days, count_runs, available_periods, day)
                        #available_periods2 = adapt_available_periods(av_periods2, flex_object)


                    if not alreadyComputed:
                        if end_time > datetime.timedelta(days=1):
                            if flex_dependant:
                                print("Error: No implementation for overnigth flex dependancy! Please only calculate deendancy during day")
                            # if duration lasts overnight, first compute spontanflex for start day, which works normally

                            if not flexibility.Aggregation_Computed:
                                flexibility.compute_aggregated_Boundaries(av_periods)
                            if spontanflex:
                                flex = flexibility.compute_spontanflex(start_time, duration, Flex_place)
                            else:
                                flex = flexibility.compute_fixDateflex(start_time, duration, activation_time, Flex_place)
                            if day + 1 >= len(DayList):
                                print("Computation of flexibility_calc not possible, as day not simulated")
                            else:
                                # then compute spontanflex of next day by using already computed spontan_flex:
                                # special call of compute_spontanflex

                                if not flexibility_next_day.Aggregation_Computed:
                                    flexibility_next_day.compute_aggregated_Boundaries(av_periods2)
                                if spontanflex:
                                    flex = flexibility_next_day.compute_spontanflex(datetime.timedelta(0),
                                                                             end_time - datetime.timedelta(days=1), Flex_place,
                                                                             flex)
                                else:
                                    flex = flexibility_next_day.compute_fixDateflex(datetime.timedelta(0),
                                                                             end_time - datetime.timedelta(days=1),
                                                                             datetime.timedelta(0), Flex_place,
                                                                             flex)

                        else:
                            if flex_dependant:

                                flex = list()

                                for strat_pos in range(len(settingsContainer.getChargingStrategies())):
                                    if concrete_strat != None:
                                        if  strat_pos != concrete_strat:
                                            flex.append(list())
                                            continue
                                        else:
                                            flex_dependant_strat2 = concrete_strat
                                    elif concrete_strat == None:
                                        if flex_dependant_strat:
                                            flex_dependant_strat2 = strat_pos
                                        else:
                                            flex_dependant_strat2 = None

                                    flex.append(list())
                                    for direction in [0,1]:
                                        if co2 and (direction == "charge") :
                                            continue
                                        av_periods = available_periods[strat_pos][direction]
                                        flexibility = flex_on_day(day)
                                        if not flexibility.Aggregation_Computed:
                                            #if day == 21 and direction == 1:
                                             #   print("hi")
                                            flexibility.compute_aggregated_Boundaries(av_periods)
                                        if spontanflex:

                                            flex_dep = flexibility.compute_spontanflex(start_time, duration, Flex_place, flex_dependant = True, flex_dependant_strat=flex_dependant_strat2)
                                        else:
                                            flex_dep = flexibility.compute_fixDateflex(start_time, duration, activation_time, Flex_place, flex_dependant = True, flex_dependant_strat=flex_dependant_strat2)
                                        flex[strat_pos].append(flex_dep)
                            else:
                                if not flexibility.Aggregation_Computed:
                                    flexibility.compute_aggregated_Boundaries(av_periods)
                                if spontanflex:
                                    flex = flexibility.compute_spontanflex(start_time, duration, Flex_place)
                                else:
                                    flex = flexibility.compute_fixDateflex(start_time, duration, activation_time, Flex_place)

                        for strat_pos in range(len(settingsContainer.getChargingStrategies())):
                            flexibility.compute_standard_load_profile(strat_pos, -1, spontanflex)
                    flex_day_list.append(flex)
                    count_days = count_days +1
                    #print(f"{day} day is computed")


                flex_list.append(flex_day_list)
                if not risk:
                    break
                print(f"{count_runs} run is computed")
                count_runs =count_runs +1
            except Exception as e:
                print(f"Error: {e}, {count_runs} is skipped")
                count_runs = count_runs +1

        return flex_list


def compute_flexibility_over_whole_day(spontanflex, risk, all_DaysList, duration, NumberOfDays, start_daytype,
                                        activation_time = datetime.timedelta(0), Flex_place = "Home", numberofday = -1,
                                        Daytype = 0, run =0, interval_size = datetime.timedelta(minutes = 10)):


    remainer = datetime.timedelta(days=1) % interval_size
    if remainer.total_seconds() >datetime.timedelta(minutes = 1).total_seconds():
        number_of_intervals = int(datetime.timedelta(days=1) / interval_size) + 1
    else:
        number_of_intervals = int(datetime.timedelta(days=1) / interval_size)

    times =[interval_size*i for i in range(number_of_intervals)]
    #all_flexes = list()
    all_quantiles = list()

    for time in times:
        flex_list = compute_flexibility(spontanflex, risk, all_DaysList, time, duration, NumberOfDays, start_daytype, activation_time,
                        Flex_place, numberofday, Daytype, run )
        #all_flexes.append(flex_list)
        risk_object = Risk_statistic(spontanflex,
                                              [i for i in range(len(settingsContainer.getChargingStrategies()))],
                                              [j for j in range(len(settingsContainer.getHeuristics()))], [0, 1])
        risk_object.compute_min_quarter_quantiles_from_flex_list(flex_list)
        #risk_object.visualize_quantiles(strat_pos, heuristic_pos, modus_pos)
        all_quantiles.append(risk_object.quantiles)
    save_list(all_quantiles, "quantiles")
    return all_quantiles

def visualize_flexibility_over_whole_day(strat_pos, heuristic_pos, modus_pos, only_mean = False, colors = None, all_quantiles = None, plt = None) :
    if all_quantiles == None:
        all_quantiles= open_file("quantiles")

    quantiles = list()
    number = len(all_quantiles)
    interval_size = datetime.timedelta(days=1) / number
    times = [interval_size.total_seconds()*i/3600 for i in range(int(datetime.timedelta(days = 1)/interval_size))]

    for quant in all_quantiles:
        if not only_mean:
            quantiles.append(quant[strat_pos][heuristic_pos][modus_pos])
        else:
            quantiles.append(quant[strat_pos][heuristic_pos][modus_pos][2]) #only append mean
    if only_mean:
        ylim = min(quantiles)- (max(quantiles) - min(quantiles))
    else:
        ylim = min(np.array(quantiles).transpose(1,0)[0])  - (min(np.array(quantiles).transpose(1,0)[2]) - \
           min(np.array(quantiles).transpose(1,0)[0]) )
    if not only_mean and colors != None:
        for i,q in enumerate(np.array(quantiles).transpose(1,0)):
            plt.plot(times, q, color = colors[i])
    else:
        plt.plot(times, quantiles)
    return ylim
