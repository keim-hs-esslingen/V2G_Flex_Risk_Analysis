from simulation_model.EV import *
from simulation_model.ChargingStrategy import *
from helper_files.nptime import *
import datetime

class AggregatedFlex:
    total_capacity: float = None
    FlexBoundaries: list = None
    capacities: list = None
    start_time: datetime.timedelta = None
    end_time: datetime.timedelta = None
    modi: list = None
    # for testing
    days: list = None
    def __init__(self, start, end, **kwargs):
        super().__init__(**kwargs)
        self.total_capacity = 0
        self.FlexBoundaries = list()
        self.capacities = list()
        self.modi = list()
        self.days = list()
        self.start_time = start
        self.end_time = end

    def append_entry(self, FlexBoundary, capacity, modus, day):
        self.FlexBoundaries.append(FlexBoundary)
        self.capacities.append(capacity)
        self.modi.append(modus)
        self.total_capacity += capacity
        self.days.append(day)
        if FlexBoundary.__class__==flex_profile:
            if self.FlexBoundaries.count(FlexBoundary) != 1:
                print("Error-SF2: profile not in appended AggregatetFlex")
            if FlexBoundary.heuristic_dependant[settingsContainer.getHeuristics()[day]].rate != capacity:
                if FlexBoundary.modus == "charge" and not FlexBoundary.charge:
                    print("hii")
        elif FlexBoundary.__class__==base_profile:
            if self.FlexBoundaries.count(FlexBoundary) != 1:
                print("Error-SF2: profile not in appended AggregatetFlex")
            if FlexBoundary.rate != -capacity and FlexBoundary.modus == "discharge":
                print("Error-SF3: capacity wrong")

    def add_capacity_on_entry(self, pos, capacity):
        self.capacities[pos] += capacity
        self.total_capacity += capacity

    def copy(self):
        copied_entry = AggregatedFlex(start = self.start_time, end = self.end_time)
        copied_entry.total_capacity = self.total_capacity
        for i in range(len(self.FlexBoundaries)):
            copied_entry.FlexBoundaries.append(self.FlexBoundaries[i])
            copied_entry.capacities.append(self.capacities[i])
            copied_entry.modi.append(self.modi[i])
            copied_entry.days.append(self.days[i])
        return copied_entry

    def copy_and_change_profiles(self, time):
        copied_Flex = self.copy()
        self.set_start_time(time)
        copied_Flex.set_end_time(time)
        i = 0
        while i < len(copied_Flex.FlexBoundaries):
            if copied_Flex.modi[i] == "end":
                copied_Flex.change_modus("middle", i)
            #i += 1
        #i = 0
        #while i < len(self.FlexBoundaries):
            #elif copied_Flex.modi[i] == "start":
             #   copied_Flex.delete_entry(i)
              #  i -=1
            #elif copied_Flex.modi[i] == "start":

            i += 1
        return copied_Flex

    def find_new_entries(self):
        new_entries = list()
        for i in range(len(self.FlexBoundaries)):
            if self.modi[i] == "ch_start" or self.modi[i] == "ch_min_start" or self.modi[i] == "dc_start" or self.modi[i]=="max_at_start" or self.modi[i]=="min_at_start":
                new_entries.append([self.FlexBoundaries[i], self.days[i]])
        return new_entries

    def delete_entry(self, i):
        del self.days[i]
        del self.modi[i]
        del self.FlexBoundaries[i]
        self.total_capacity -= self.capacities[i]
        del self.capacities[i]

    def set_start_time(self, time):
        self.start_time = time

    def set_end_time(self, time):
        self.end_time = time

    def change_modus(self, modus, pos):
        self.modi[pos]= modus

class FlexBoundary:
    e_max: float = None
    e_curr: float = None
    e_min: float = None
    e_need: float = None
    charging_power: float = None
    discharging_power: float = None
    charging_start: datetime.timedelta = None
    charging_stop: datetime.timedelta = None
    discharging_start: datetime.timedelta = None
    discharging_stop: datetime.timedelta = None
    t_min_start: datetime.timedelta = None
    t_min_end: datetime.timedelta = None
    t_max_start: datetime.timedelta = None
    t_max_end: datetime.timedelta = None
    t_min_start2: datetime.timedelta = None
    t_end: datetime.timedelta = None
    t_start: datetime.timedelta = None
    available_period: AvailablePeriod = None
    vehicle: EV = None
    ch_rate_strategy_info: float = None
    start_time_eneed: datetime.timedelta = None
    t_max_end_alternative: datetime.timedelta = None
    e_max_end_alternative: float = None

    def increment_times_by_day(self):
        self.t_min_start += datetime.timedelta(days = 1)
        self.t_min_end += datetime.timedelta(days = 1)
        self.t_max_start += datetime.timedelta(days = 1)
        self.t_max_end += datetime.timedelta(days = 1)
        self.t_min_start2 += datetime.timedelta(days = 1)
        self.t_end += datetime.timedelta(days = 1)
        self.t_start += datetime.timedelta(days = 1)
        if self.start_time_eneed != None:
            self.start_time_eneed += datetime.timedelta(days = 1)
        if self.t_max_end_alternative != None:
            self.t_max_end_alternative += datetime.timedelta(days = 1)

    def copy_and_change(self, new_start_time, e_curr, old_day, strategy_reset=True):

        days = datetime.timedelta(days=old_day)
        if new_start_time +days < self.t_start:
            print("Error: t_start smaller than new start_time")
        new_start_SOC=(e_curr/self.vehicle.battery_size)*100
        new_available_period = self.available_period.copy_and_change(new_start_time, new_start_SOC, old_day)
        new_available_period.compute_available_time() # not used to check availability, but to compute available_time
        ChangedFlexBoundary = FlexBoundary(new_available_period, self.vehicle)
        ChangedFlexBoundary.t_start = new_start_time
        ChangedFlexBoundary.e_curr = e_curr
        ChangedFlexBoundary.e_max = max(self.e_max - (e_curr-self.e_curr),0)
        ChangedFlexBoundary.e_min = self.e_min - (e_curr - self.e_curr)
        ChangedFlexBoundary.e_need = self.e_need - (e_curr - self.e_curr)
        ChangedFlexBoundary.charging_power = self.charging_power
        ChangedFlexBoundary.discharging_power = self.discharging_power
        ChangedFlexBoundary.charging_start = max(self.charging_start - days, new_start_time)
        ChangedFlexBoundary.charging_stop = max(self.charging_stop- days, new_start_time)
        ChangedFlexBoundary.discharging_start = max(self.discharging_start - days, new_start_time)
        ChangedFlexBoundary.discharging_stop = max(self.discharging_stop -days, new_start_time)
        ChangedFlexBoundary.t_end = self.t_end - days
        ChangedFlexBoundary.ch_rate_strategy_info = self.ch_rate_strategy_info
        if abs((ChangedFlexBoundary.t_end-ChangedFlexBoundary.t_start)-ChangedFlexBoundary.available_period.available_time).total_seconds() > 1e-8 and old_day != 0:
            print("Error: computation, available_time")
        if not strategy_reset:
            if self.start_time_eneed != None:
                ChangedFlexBoundary.start_time_eneed = max(self.start_time_eneed-days, new_start_time)
            if self.t_max_end_alternative != None:
                ChangedFlexBoundary.t_max_end_alternative = max(self.t_max_end_alternative-days, new_start_time)
                ChangedFlexBoundary.e_max_end_alternative = max(self.e_max_end_alternative - (e_curr-self.e_curr),0)

        return ChangedFlexBoundary

    def copy(self):
        ChangedFlexBoundary = FlexBoundary(self.available_period, self.vehicle)
        ChangedFlexBoundary.t_start = self.t_start
        ChangedFlexBoundary.e_curr = self.e_curr
        ChangedFlexBoundary.e_max = self.e_max
        ChangedFlexBoundary.e_min = self.e_min
        ChangedFlexBoundary.e_need = self.e_need
        ChangedFlexBoundary.charging_power = self.charging_power
        ChangedFlexBoundary.discharging_power = self.discharging_power
        ChangedFlexBoundary.charging_start = max(self.charging_start, self.t_start)
        ChangedFlexBoundary.charging_stop = max(self.charging_stop, self.t_start)
        ChangedFlexBoundary.discharging_start = max(self.discharging_start, self.t_start)
        ChangedFlexBoundary.discharging_stop = max(self.discharging_stop, self.t_start)
        ChangedFlexBoundary.t_end = self.t_end
        ChangedFlexBoundary.t_min_start = self.t_min_start
        ChangedFlexBoundary.t_min_end = self.t_min_end
        ChangedFlexBoundary.t_max_start = self.t_max_start
        ChangedFlexBoundary.t_max_end = self.t_max_end
        ChangedFlexBoundary.t_min_start2 = self.t_min_start2
        ChangedFlexBoundary.ch_rate_strategy_info = self.ch_rate_strategy_info
        ChangedFlexBoundary.start_time_eneed = self.start_time_eneed
        ChangedFlexBoundary.t_max_end_alternative = self.t_max_end_alternative
        ChangedFlexBoundary.e_max_end_alternative = self.e_max_end_alternative

        return ChangedFlexBoundary

    def __init__(self, available_period, vehicle, *args, **kwargs):
        super().__init__(**kwargs)
        self.vehicle = vehicle
        self.available_period = available_period
        self.t_start = available_period.start_time.to_timedelta()
        self.t_end = self.t_start + available_period.available_time

    def compute_boundaries(self, simple):
        #start = time.time()
        self.compute_energy_boundaries()
        #end = time.time()
        #print("EnergyBoundaries")
        #print(end -start)
        if simple:
            self.compute_simple_power_boundaries()
            #start = time.time()
            #print("powerBoundaries")
            #print(start-end)
            self.compute_simple_times()
            #end = time.time()
            #print("simpletimes")
            #print(end-start)
            #self.visualize_energy_boundaries()
            #print("visualization")
            #print(time.time()-end)
        #´else:

            # self.compute_complex_times()

    def compute_simple_times(self):
        self.t_max_start = self.t_start
        #compute times after charging e_min or e_max
        time_after_charge_emax = self.t_start + self.vehicle.time_to_charge(self.e_max, self.available_period.charging_power)
        time_after_charge_emin = self.t_start + self.vehicle.time_to_discharge(abs(self.e_min), self.available_period.discharging_power)
        #special casses: not enough time for (dis)charging e_max/e_min
        # --> adapt boundaries: e_max:maximum energy to charge which is possible
        self.e_max, self.t_max_end = self.adapt_boundaries_if_too_less_time(self.e_max, time_after_charge_emax, "charge")
        if self.e_max<self.e_need-0.1:
            print("Error5: flx-cst")
            #shouldn't happen, as enough time to charge e_need in availablel period

        if self.e_min < 0:
            # --> adapt boundaries: e_min:maximum energy to discharge, which is possible
            self.e_min, self.t_min_end = self.adapt_boundaries_if_too_less_time(self.e_min, time_after_charge_emin, "discharge")
            self.t_min_start = self.t_start
            self.e_need = max(self.e_min, self.e_need) # update e_need, if e_need is smaller than e_min
        else:
            #e_min>=0 --> t_min_start is time, when e_min is reached
            self.t_min_start = self.t_start + self.vehicle.time_to_charge(self.e_min, self.available_period.charging_power)
            # t_min_start < endtime, as otherwise this time period is not flexible
            if self.t_min_start > self.t_end:
                print("flx-cst: Error4")
            self.t_min_end = self.t_min_start # time, when e_min is reached
        #time, when charging has to start at latest to reach e_need
        self.t_min_start2 = self.t_end - self.vehicle.time_to_charge(self.e_need - self.e_min, self.available_period.charging_power)
        #if t_min_start2 is smaller then t_min_end, then e_min can't be reached,
        # but there could be a larger "e_min" onto which discharging and charging to e_need aftwerwards is possible
        if self.t_min_start2 < self.t_min_end:
            # adapt e_min, as no time to charge min_SOC after discharging to e_min
            self.determine_energy_to_discharge_without_restricting_minSOC()


            # update t_min_start2, if there has been changes to e_min
            self.t_min_start2 = self.t_end - self.vehicle.time_to_charge(self.e_need - self.e_min, self.available_period.charging_power)

        if self.t_min_start2 < self.t_min_end:
            if self.t_min_end - self.t_min_start2 > datetime.timedelta(microseconds=2):
                print("Error3.1")
            print("flx-cst: Error3") # adaption of e_min not complete

    def determine_energy_to_discharge_without_restricting_minSOC(self, earliest_charging_start_time = None ):
        if self.e_min > 0:
            print("flx-cst: Error1")
            # only possible, if emin < 0, as otherwise availble period not flexible (t_min_end = t_min_start

        if not CPCV:
            if self.e_need >= 0:
                # calculate time to charge e_need
                time_to_charge_eneed = self.vehicle.time_to_charge(self.e_need, self.available_period.charging_power)
            else:
                # claculate time for discharging to e_need, because then remaining time can be used optimally: after discharging, only charging until e_need necessary
                time_to_charge_eneed = self.vehicle.time_to_discharge(abs(self.e_need),
                                                                      self.available_period.discharging_power)
                # time_after_charge_eneed = self.t_start + time_to_charge_eneed
                if time_to_charge_eneed > self.available_period.available_time:
                    # error, if not able to discharge e_need
                    # e_need>=e_min, and due to adapt_boundaries_if_too_less_time, enough time to discharge to "new" e_min
                    # also enough time to discharge to e_need
                    print("Error6: flx-cst")
            # time remaining for discharging before charging e_need
            remaining_time = self.available_period.available_time - time_to_charge_eneed  # > 0, as e_need has to be charged at least, otherwise no available period

            if remaining_time < datetime.timedelta(0):
                print("flx-cst: Error2")

            # calculate relation from charging_power/discharging_power

            charge_time, discharge_time = self.compute_disCharge_time(remaining_time, earliest_charging_start_time)
            self.e_min = - self.vehicle.discharge(discharge_time, self.available_period.discharging_power)
            self.t_min_end = self.t_start + discharge_time
            if charge_time + discharge_time > remaining_time:
                print("flx-cst: Error7")
            if self.e_need < 0:
                # add e_need to the previous calculated e_min, as e_need is discharged in available_time-remainingtime
                self.e_min = self.e_min + self.e_need
                self.t_min_end = self.t_min_end + time_to_charge_eneed
                # update t_min_start2, if there has been changes to e_min

        self.t_min_start2 = self.t_end - self.vehicle.time_to_charge(self.e_need - self.e_min,
                                                                             self.available_period.charging_power)

    def compute_disCharge_time(self, remaining_time,  earliest_charging_start_time):
        if earliest_charging_start_time == None:
            case = 1
        else:
            if self.e_need <= 0:
                timepoint_start_charging_eneed = self.t_start + self.available_period.available_time
            else:
                timepoint_start_charging_eneed = self.t_start + remaining_time
            if timepoint_start_charging_eneed <= earliest_charging_start_time:
                #if self.e_need <0:
                #    print("Error: earliest_charging_start_time <= end_time of flex period")
                case = 2
            else:
                #compute energy, whihc can be charged in time available to charge (earlier times would lead to charging in two directions during flex periods
                energy_possible_to_charge = self.vehicle.charge(timepoint_start_charging_eneed - earliest_charging_start_time, self.charging_power)
                time_to_discharge_max_possible_energy = self.vehicle.time_to_discharge(energy_possible_to_charge, self.discharging_power)
                if time_to_discharge_max_possible_energy + self.t_start > earliest_charging_start_time:
                    case = 1
                else:
                    case = 3
        if case == 1:
            relation = self.available_period.discharging_power / self.available_period.charging_power
            discharge_time = floor_timedelta(remaining_time,
                                             relation + 1)  # divide by relation, but round down, so that discharge_time is in relation larger than charge_time
            charge_time = remaining_time - discharge_time
        elif case == 2:
            # charging starts before earlies_charging_start_time, so as no two directions during period, only charging:
            charge_time = datetime.timedelta(0)
            discharge_time = datetime.timedelta(0)
        elif case == 3:
            discharge_time = time_to_discharge_max_possible_energy
            charge_time = timepoint_start_charging_eneed - earliest_charging_start_time

        return charge_time, discharge_time

    def adapt_boundaries_if_too_less_time(self, boundary, time_needed, modus):
        # boundary: e_max or e_min, --> e_max>=0, e_min < 0
        boundary_new = boundary

        if time_needed > self.t_end:
            if modus == "discharge":
                boundary_new = - self.vehicle.discharge(self.t_end - self.t_start,
                                                 self.available_period.discharging_power)
                #e_min still < 0, as time_needed otherwise not too large
            elif modus == "charge":
                boundary_new = self.vehicle.charge(self.t_end - self.t_start,
                                                  self.available_period.charging_power)
                #--> new e_max still >0, as time_needed otherwise not too large
        boundary_time_new = min(time_needed, self.t_end)

        return boundary_new, boundary_time_new

    # def compute_complex_times(self):

    def compute_energy_boundaries(self, max_SOC = None):
        if max_SOC== None:
            max_SOC = settingsContainer.getMaxSoc()
        # current energy in battery
        self.e_curr = self.available_period.start_SOC * 0.01 * self.vehicle.battery_size

        self.e_min = self.vehicle.min_energy-self.e_curr #(caclulation of flexbility possible afterwards, not dependant
        # on simulation calculation

        # energy difference to minimum energy in the end of flexibility_calc period
        self.e_need = max(self.available_period.min_SOC * 0.01 * self.vehicle.battery_size - self.e_curr, self.e_min)

        # if min_SOC > MAX_SOC, MIN_SOC, otherwise max_SOC
        # e_max >=0 for no discharge duty
        self.e_max = max(max(max_SOC * 0.01 * self.vehicle.battery_size- self.e_curr, self.e_need), 0)

    def compute_simple_power_boundaries(self):

        # add one minute, if at start or end charging/discharging is not possible, as the soc is not enough/ too large
        if self.e_max == 0:
            self.charging_start = self.t_start + datetime.timedelta(minutes=1)
            self.discharging_start = self.t_start
        else:
            self.charging_start = self.t_start
            if self.e_min == 0:
                self.discharging_start = self.t_start + datetime.timedelta(minutes=1)
            else:
                self.discharging_start = self.t_start
        if self.available_period.min_SOC >= settingsContainer.getMaxSoc():
            self.discharging_stop = self.t_end - datetime.timedelta(minutes=1)
            self.charging_stop = self.t_end
        else:
            self.discharging_stop = self.t_end
            self.charging_stop = self.t_end

        # possible ToDO for not cpcv other calculation, as not constant over time
        self.charging_power = self.available_period.charging_power
        self.discharging_power = self.available_period.discharging_power

    def compute_alternative_t_max_end(self, max_SOC=100):
        e_max_alternative =  max(max(max_SOC * 0.01 * self.vehicle.battery_size - self.e_curr, self.e_need), 0)
        time_after_charge_emax = self.t_start + self.vehicle.time_to_charge(e_max_alternative,
                                                                            self.available_period.charging_power)

        e_max_alternative, t_max_end_alternative = self.adapt_boundaries_if_too_less_time(e_max_alternative, time_after_charge_emax,
                                                                            "charge")
        self.t_max_end_alternative = t_max_end_alternative
        self.e_max_end_alternative = e_max_alternative
        if e_max_alternative - 1e-8 > (self.vehicle.battery_size-self.e_curr):
            print("Error: alternative_t_max_end")
        return  e_max_alternative, t_max_end_alternative

    def set_strategy_info(self, ch_rate, time):
        self.ch_rate_strategy_info = ch_rate
        self.start_time_eneed = time

    def visualize_energy_boundaries(self, safe=False, file="figures/energy/default", withChargingStrategies = True):
        if not CPCV:
            plt.figure()
            if self.available_period.available_time>datetime.timedelta(hours=6):
                divisor=3600
                label="Zeit in Stunden" # after start
            else:
                divisor=60
                label="Zeit in Minuten"
            y1 = [0, self.e_max, self.e_max]
            #x1 = [(self.t_max_start.total_seconds()- self.t_start.total_seconds())/divisor, (self.t_max_end.total_seconds()- self.t_start.total_seconds())/divisor, (self.t_end.total_seconds()- self.t_start.total_seconds())/divisor]
            y2 = [0, self.e_min, self.e_min, self.e_need]
            #x2 = [(self.t_start.total_seconds()- self.t_start.total_seconds())/divisor, (self.t_min_end.total_seconds()- self.t_start.total_seconds())/divisor, (self.t_min_start2.total_seconds()- self.t_start.total_seconds())/divisor, (self.t_end.total_seconds()- self.t_start.total_seconds())/divisor]
            y0 = [0, 0, 0, 0]
            x1 = [(self.t_max_start.total_seconds() ) / divisor,
                  (self.t_max_end.total_seconds() ) / divisor,
                  (self.t_end.total_seconds() ) / divisor]
            #y2 = [0, self.e_min, self.e_min, self.e_need]
            x2 = [(self.t_start.total_seconds() ) / divisor,
                  (self.t_min_end.total_seconds() ) / divisor,
                  (self.t_min_start2.total_seconds() ) / divisor,
                  (self.t_end.total_seconds() ) / divisor]

            e_before_start = -self.e_curr/2
            t_before_start = (self.t_start - self.vehicle.time_to_charge(-e_before_start, self.charging_power)).total_seconds()/divisor

            if False:
                count = 0

                y2.insert(0, e_before_start)
                x2.insert(0,t_before_start)
            if self.e_min>0:
                start_t=self.t_min_end
                start_e=self.e_min
            if self.e_need>0:
                end_e=self.e_need
            print(self.e_need)

            plt.rc('font', size=22)
            plt.plot(x1, y1, color="red", label= "obere Grenze")
            plt.plot(x2, y2, color="blue", label = "untere Grenze")


            plt.axhline(y = self.e_max, color = 'red', alpha=0.4, linestyle = '--', label='e_max')
            plt.legend(loc = 'upper left')
            plt.axhline(y=self.e_min, color='blue', alpha=0.4, linestyle='--', label='e_min')
            plt.legend(loc='upper left')
            plt.axhline(y=self.e_need, color='yellow', alpha=0.4, linestyle='--', label='e_need')
            plt.legend(loc='upper center', bbox_to_anchor=(0.5, 1.1),
                      ncol=3, fancybox=True, shadow=True)




            if withChargingStrategies:
                self.compute_alternative_t_max_end()
                if self.e_need > 0:
                    start_e_need = self.t_end - self.vehicle.time_to_charge(self.e_need, self.charging_power)
                else:
                    start_e_need = self.t_end
                #plt.plot([0, (self.t_end.total_seconds()- self.t_start.total_seconds())/divisor],[0, self.e_max], linestyle = '-.', color = 'purple', label = 'charging as long as possible')
                #plt.plot([0, (self.t_max_end_alternative.total_seconds() - self.t_start.total_seconds())/divisor, (self.t_end.total_seconds() - self.t_start.total_seconds()) / divisor], [0, (self.vehicle.battery_size -self.e_curr), (self.vehicle.battery_size -self.e_curr)],
                #         linestyle='-.', color='green', label='charging as soon as possible')
                #plt.plot([0, (self.t_end.total_seconds() - self.t_start.total_seconds()) / divisor], [0, self.e_need],
                #         linestyle='-.', color='brown', label='charging as late as possible')
                plt.plot([self.t_start.total_seconds()/divisor, (self.t_end.total_seconds() ) / divisor], [0, self.e_max],
                         linestyle='-.', color='purple', label='Ladestrategie 3')
                plt.plot([self.t_start.total_seconds()/divisor, (self.t_max_end_alternative.total_seconds() ) / divisor,
                          (self.t_end.total_seconds() ) / divisor],
                         [0, (self.vehicle.battery_size - self.e_curr), (self.vehicle.battery_size - self.e_curr)],
                         linestyle='-.', color='green', label='Ladestrategie 1')
                plt.plot([self.t_start.total_seconds()/divisor, start_e_need.total_seconds()/divisor, (self.t_end.total_seconds() ) / divisor], [0, 0, max(self.e_need,0)],
                         linestyle='-.', color='brown', label='Ladestrategie 2')
                plt.legend(loc='upper center', bbox_to_anchor=(0.5, 1.35),
                           ncol=3, fancybox=True, shadow=True)

            plt.ylabel("Energie in kwh")
            plt.xlabel(label)
            #plt.rc('axes', labelsize=40)
            #plt.rc('xtick', labelsize=40)
            #plt.rc('ytick', labelsize=40)
            plt.fill(
                np.append(x1, x2[::-1]),
                np.append(y1, y2[::-1]),
                color='C0', alpha=0.3
            )
            #y_=
            #plt.fill_between(x1, y1, y0[0:3], color ='C0', alpha=0.3)
            #plt.fill_between(x2, y2, y0, color = 'C0', alpha=0.3)


            if safe:
                plt.savefig("figures/energy/"+file)

            #plt.fill_between(x2, y1, y2, color='C1', alpha=0.3)
            return divisor

    def visualize_power_boundaries(self, safe=False, withChargingStrategies = False):
        # possible Todo: CPCV
        if not CPCV:
            plt.figure()
            if self.available_period.available_time>datetime.timedelta(hours=6):
                divisor=3600
                label="time in hours" # after start
            else:
                divisor=60
                label="time in minutes"
            y1 = [0, self.charging_power, self.charging_power, 0]
            x1 = [self.t_start.total_seconds()/divisor, self.charging_start.total_seconds()/divisor, self.charging_stop.total_seconds()/divisor, self.t_end.total_seconds()/divisor]
            y2 = [0, -self.discharging_power, -self.discharging_power, 0]
            x2 = [self.t_start.total_seconds()/divisor, self.discharging_start.total_seconds()/divisor, self.discharging_stop.total_seconds()/divisor, self.t_end.total_seconds()/divisor]
            y0 = [0, 0, 0, 0]
            plt.rc('font', size=22)
            plt.plot(x1, y1, color = 'red', label = 'upper boundary')
            plt.plot(x2, y2, color = 'blue', label = 'lower boundary')
            plt.fill_between(x1, y1, y0, color='red', alpha=0.3)
            plt.fill_between(x2, y2, y0, color='blue', alpha=0.3)

            plt.ylabel("power in kw")
            plt.xlabel(label)
            if withChargingStrategies:
                self.compute_alternative_t_max_end()
                #plt.plot([0, (self.t_end.total_seconds()- self.t_start.total_seconds())/divisor],[0, self.e_max], linestyle = '-.', color = 'purple', label = 'charging as long as possible')
                #plt.plot([0, (self.t_max_end_alternative.total_seconds() - self.t_start.total_seconds())/divisor, (self.t_end.total_seconds() - self.t_start.total_seconds()) / divisor], [0, (self.vehicle.battery_size -self.e_curr), (self.vehicle.battery_size -self.e_curr)],
                #         linestyle='-.', color='green', label='charging as soon as possible')
                #plt.plot([0, (self.t_end.total_seconds() - self.t_start.total_seconds()) / divisor], [0, self.e_need],
                #         linestyle='-.', color='brown', label='charging as late as possible')
                plt.plot([self.t_start.total_seconds()/divisor, self.t_start.total_seconds()/divisor, self.t_end.total_seconds()/divisor, self.t_end.total_seconds()/divisor], [0, self.e_max/((self.t_end - self.t_start).total_seconds()/3600), self.e_max/((self.t_end - self.t_start).total_seconds()/3600), 0],
                         linestyle='-.', color='purple', label='charging as long as possible')
                plt.plot([self.t_start.total_seconds()/divisor, self.t_start.total_seconds()/divisor, (self.t_max_end_alternative.total_seconds() ) / divisor, (self.t_max_end_alternative.total_seconds() ) / divisor,
                          (self.t_end.total_seconds() ) / divisor],
                         [0, (self.charging_power), (self.charging_power),0,0 ],
                         linestyle='-.', color='green', label='charging as soon as possible')
                start_e_need = self.t_end - self.vehicle.time_to_charge(self.e_need, self.charging_power)

                plt.plot([ self.t_start.total_seconds()/divisor, start_e_need.total_seconds()/divisor, start_e_need.total_seconds()/divisor, (self.t_end.total_seconds() ) / divisor, (self.t_end.total_seconds() ) / divisor], [0, 0, self.charging_power, self.charging_power, 0],
                         linestyle='-.', color='brown', label='charging as late as possible')
            plt.legend(loc='upper center', bbox_to_anchor=(0.5, 1.35),
                       ncol=3, fancybox=True, shadow=True)
            plt.show()
            if safe:
                plt.savefig("figures/power/"+str(self.vehicle.ID)+str(int(self.t_start.total_seconds())))
            #plt.close()


def compute_flex_bdry(available_period, ev):
    flex_boundary = FlexBoundary(available_period, ev)
    flex_boundary.compute_boundaries(SIMPLE)
    return flex_boundary


class flex_profile:
    modus: str = None
    rate: float = None
    bdry: FlexBoundary = None
    start_time: datetime.timedelta = None
    end_time: datetime.timedelta = None
    whole_time: bool = None
    available_time: datetime.timedelta = None
    energy: float = None
    charging_end: float = None
    heuristic_dependant: dict = None
    profile: str = None
    strat_pos: int = None
    charge: bool = None

    def __init__(self, bdry, modus, strat_pos, spontanflex = True, *args, **kwargs):
        super().__init__(**kwargs)
        self.bdry = bdry
        self.strat_pos = strat_pos
        self.modus = modus

        if modus == "charge":
            if not spontanflex and strat_pos == 0:
                bdry.compute_alternative_t_max_end()
                self.energy = bdry.e_max_end_alternative
            else:
                self.energy = bdry.e_max
            self.rate = self.bdry.charging_power
            self.charge = True
        elif modus == "discharge":
            self.energy = bdry.e_min
            self.rate = self.bdry.discharging_power
            self.charge = False
        else:
            print("Error-flexprofile")
        self.heuristic_dependant = {settingsContainer.getHeuristics()[0]: HeuristicInformation(self.rate, self.energy)}
        for heuristic in settingsContainer.getHeuristics():
            self.heuristic_dependant[heuristic] = HeuristicInformation(self.rate, self.energy)

    def compute_flex_profile(self, start_time_Flex, end_time_Flex):
        if self.modus == "charge":
            if settingsContainer.getChargingStrategies()[self.strat_pos] == "as soon as possible" and settingsContainer.getSpontanflex():
                # no charging capacity, as either charged with full power by charging strategy as well or no capacity left
                return
            time = self.bdry.t_max_end  # vehicle.time_to_charge(remaining_charging_energy, ch_rate)
            self.end_time = self.bdry.t_end
            cmp_time = self.bdry.t_max_end

        #   if Charging_strategies[self.strat_pos] == "as soon as possible" and self.cmp_time < end_time_Flex and self.bdry.t_max_end_alternative < end_time_Flex and self.bdry.t_max_end_alternative > start_time_Flex and self.energy >0:


                ## for this ch_strategy, charging only can differ if t_max_end_alternative is before end_time_Flex and
                ## charging for charging strategy hasn't been finished (t_max_end_alternative after start_time_flex)
                ## as in all other cases, charging lasts over whole period and is the same
                ## Furthermore only adaption if old e_max isn't already reached, otherwise  keep with charging strategy
             #   cmp_time = self.bdry.t_max_end_alternative
              #  self.energy = self.bdry.e_max_end_alternative

               # return
                #cmp_time = self.bdry.t_max_end_alternative
                #self.energy = self.bdry.e_max_end_alternative


        else: # self.modus == "discharge":
            time = self.bdry.t_min_end  # vehicle.time_to_discharge(remaining_discharging_energy, dc_rate)
            self.end_time = self.bdry.t_min_start2
            cmp_time = self.bdry.t_min_end
            # There is the posibility to discharge longer then min_end, if one discharges less then e_min,
            # however how much less? --> new heuristc/optimization to fully activate this potential,
            # but here, discharging only until t_min_end is possible
        if self.end_time < end_time_Flex or self.bdry.t_start > start_time_Flex:
            self.whole_time = False
        else:
            self.whole_time = True
        self.start_time = max(self.bdry.t_start, start_time_Flex)
        self.end_time = min(self.end_time, end_time_Flex)
        self.available_time = self.end_time - self.start_time
        if self.modus == "charge" and self.energy > 0 or (self.modus == "discharge" and self.energy < 0 and self.end_time== end_time_Flex):
            # if there is energy to charge or "space" to discharge and in discharge mode no additional energy has to be charged
            if time >= end_time_Flex:
                # can be (dis)charged with full power over the whole flex period
                self.profile = "basis"
            else:
                # fully charged with full power before end of flex period
                if self.whole_time:
                    self.profile = "flex"
                else:
                    # available_period ends before flex period
                    if self.bdry.t_end == cmp_time:
                        # charging with full power until end of available period possible,
                        # in discharge case discharging until t_min_end possible
                        self.profile = "basis"
                    else:
                        self.profile = "flex"

        elif self.modus == "discharge":
            # cases, in which in discharge mode it is charged
            if self.energy > 0:
                print("Error: energy always below 0, as discharge mode and e_min is charged before (fixCharging_list")
                # case, where charged like in charging strategy
                # min energy to be charged, so no discharging in the flex_profile possible
            #    self.end_time = min(self.bdry.t_min_end, end_time_Flex)
            #    self.profile = "basis"
            #    charge = True
            #    if self.bdry.t_min_start2 < end_time_Flex:
            #        # if e_need has to be charged in this period as well
            #        if self.bdry.e_need >= 0:
                        # new prfoiel
            #        else:
            #            print("Error: computation of flex_profiles")
            #            # not possible, as e_ned >= e_min
            #elif
            if self.end_time < end_time_Flex:
                # determine time point to start charging for e_need, if not discahrging before (not min_start2)
                if self.bdry.e_need >= 0 and self.bdry.t_end <= end_time_Flex:
                    # charging for e_need definietly in this period
                    self.end_time = min(self.bdry.t_end, end_time_Flex)
                    charge = True
                    self.energy = self.bdry.e_need # (wrong direction --> negative)
                    if self.bdry.t_min_start2>self.start_time:
                        self.profile = "flex"
                    else:
                        self.profile = "basis"
                else:
                    # there is time to discharge, but, we want not to charge afterwards withing flex_period
                    # so adapt e_min, t_min_end, so that charging after flex_period is possible
                    self.bdry.determine_energy_to_discharge_without_restricting_minSOC(end_time_Flex)

                    if self.bdry.t_min_start2 < end_time_Flex and self.bdry.e_need >=0:
                        # if newly computed t_min_start2 is within flex_period
                        if self.bdry.t_end < end_time_Flex:
                            self.energy = self.bdry.e_need
                            self.end_time = self.bdry.t_end
                        else:
                            self.end_time = end_time_Flex
                            self.energy = self.bdry.vehicle.charge(self.end_time-self.bdry.t_min_start2, self.bdry.charging_power)

                        charge = True

                        if self.bdry.t_min_start2 > self.start_time:
                            self.profile = "flex"
                        else:
                            self.profile = "basis"
                    else:
                        if self.bdry.t_min_start2 >= end_time_Flex or self.bdry.t_end < end_time_Flex:
                            # t_min_start is not within flex_period or e_need is smaller than zero
                            charge = False
                            self.energy = self.bdry.e_min
                            self.end_time = min(end_time_Flex, self.bdry.t_end)
                            if self.bdry.t_min_end < self.end_time-datetime.timedelta(microseconds=1000):
                                self.profile = "flex"
                            else:
                                self.profile = "basis"
                        else:
                            print("Error: t_min_start2 should be larger than end_time Flex")
                self.available_time = self.end_time - self.start_time
                if self.end_time < end_time_Flex:
                    self.whole_time = False
                elif self.start_time == start_time_Flex:
                    self.whole_time = True
                self.charge = charge
                if charge:
                    self.rate = self.bdry.charging_power

    def compute_flex_values(self):
        if self.available_time > settingsContainer.getMinDeliveryTime():
            for heuristic in settingsContainer.getHeuristics():
                if self.profile == "flex" and heuristic == "as long as possible with minimum rate":
                    # compute minimum charging rate to charge energy in available time without going under MIN_RATE
                    # or larger then self.bdry.charging_power
                    rate = compute_min_charging_rate(self.available_time, abs(self.energy), self.rate)
                else:
                    rate = self.rate
                # else:
                    # if Optimization or other heuristics; for Optimization first compute all profiles,
                    # But here, only other heuristic max_at_start: (here also if flex_profile: starting with max power
                    # in this case, rate already initialized

                # --> t_max_end < end_time_of_flex_period
                if self.modus == "charge" or self.charge:
                    # compute energy, as rate changed in heuristic2 and if t_max_end/t_min_end < end_time at heuristic1
                    # for latter case, take old energy
                    if self.energy > 0:
                        self.heuristic_dependant[heuristic].energy = min(self.bdry.vehicle.charge(self.available_time, rate), abs(self.energy))
                        self.heuristic_dependant[
                            heuristic].charging_end = self.start_time + self.bdry.vehicle.time_to_charge(
                            self.heuristic_dependant[heuristic].energy, rate)
                        #if self.charge:
                            #self.heuristic_dependant[heuristic].energy = - self.heuristic_dependant[heuristic].energy

                    elif self.energy == 0:
                        self.heuristic_dependant[heuristic].energy = 0
                        rate = 0
                        self.heuristic_dependant[heuristic].charging_end = self.end_time
                    else:
                        print("Error: energy should be smaller than zero")
                    if self.profile == "flex" and heuristic == "as long as possible with minimum rate":
                        if self.heuristic_dependant[heuristic].charging_end < self.end_time:
                            if rate > MIN_CHARGING_RATE:
                                print("Error: min ch_rate")
                else: # self.modus == "discharge":
                    self.heuristic_dependant[heuristic].energy = max(-self.bdry.vehicle.discharge(self.available_time, rate), self.energy)
                    self.heuristic_dependant[heuristic].charging_end = self.start_time + self.bdry.vehicle.time_to_discharge(- self.heuristic_dependant[heuristic].energy, rate)
                    if self.profile == "flex" and heuristic == "as long as possible with minimum rate":
                        if self.heuristic_dependant[heuristic].charging_end < self.end_time:
                            if rate > MIN_CHARGING_RATE:
                                print("Error: min ch_rate")
                self.heuristic_dependant[heuristic].rate = rate

    def compute_potential_values(self):
        if self.profile != "basis":
            print("Error: only base profiles for potential calculation")

    def plot_in_energy_boundary(self, divisor, heuristic_pos,  e_curr_old, day):
        label = "verändertes Laden (" + str(self.strat_pos+1) + ") bei Heuristik " + str(heuristic_pos+1)
        if self.strat_pos == 0:
            if heuristic_pos == 0:
                color = "lime"
            else:
                color = "darkgreen"
        elif self.strat_pos == 1:
            if heuristic_pos == 0:
                color = "lightcoral"
            else:
                color = "tomato"
        elif self.strat_pos == 2:
            if heuristic_pos == 0:
                color = "mediumorchid"
            else:
                color = "magenta"

        if not CPCV:
            x1 = (self.start_time.total_seconds() + datetime.timedelta(days = day).total_seconds()) / divisor
            y1 = self.bdry.e_curr-e_curr_old
            plt.plot([x1,
                      (self.heuristic_dependant[settingsContainer.getHeuristics()[heuristic_pos]].charging_end.total_seconds()
                       + datetime.timedelta(days = day).total_seconds() )/ divisor],
                         [y1, self.bdry.e_curr+self.heuristic_dependant[settingsContainer.getHeuristics()[heuristic_pos]].energy-e_curr_old],
                     linestyle='-', linewidth = 3, label = label, color = color )
            plt.plot(x1,y1, "o", color = "black")


class base_profile:
    modus: str = None
    rate: float = None
    bdry: FlexBoundary = None
    start_time: datetime.timedelta = None
    end_time: datetime.timedelta = None
    #whole_time: bool = None
    available_time: datetime.timedelta = None
    energy: float = None
    #charging_end: float = None
    #heuristic_dependant: dict = None
    #profile: str = None
    strategy: str = None
    strat_pos: int = None
    modus_pos: int = None

    #charge: bool = None

    def __init__(self, bdry, strat_pos, modus_pos,  *args, **kwargs):
        super().__init__(**kwargs)
        self.bdry = bdry
        self.strategy = settingsContainer.getChargingStrategies()[strat_pos]
        self.strat_pos = strat_pos
        # all charging strategies include only charging, not discharging
        self.rate = self.bdry.charging_power
        self.energy = 0
        self.modus_pos = modus_pos
        #self.heuristic_dependant = {heuristics[0]: HeuristicInformation(self.rate, self.energy)}
        #for heuristic in heuristics:
         ##   self.heuristic_dependant[heuristic] = HeuristicInformation(self.rate, self.energy)

    def set_modus_pos(self, modus_pos):
        self.modus_pos = modus_pos

    def compute_base_profile(self, start_time_Flex, end_time_Flex):

        if self.strategy == "as soon as possible":
            self.energy = compute_charged_until_certain_time_according_to_Charging_strategy(self.bdry, min(self.bdry.t_end, end_time_Flex), self.strategy)
            if self.energy == 0:
                self.rate = 0
            self.start_time = max(self.bdry.t_start, start_time_Flex)
            #if self.start_time.total_seconds() == 25200 and self.energy >= 0.3581729 and self.energy < 0.36:
                #print("hi")
            self.end_time = min(self.bdry.t_max_end_alternative, end_time_Flex)
            #e_max, t_max_end = self.bdry.compute_alternative_t_max_end()
            # in charging strategies, ev is charged full
            #self.end_time = min(t_max_end, end_time_Flex)
            #self.start_time = max(self.bdry.t_start, start_time_Flex)
            #if t_max_end <= end_time_Flex:
            #    self.energy = e_max # as charging started in this profile--> start_time_Flex <= bdry.t_start!!
            #    if not self.bdry.t_start>=start_time_Flex:
            #        print("Error: bdry for profile should start at or later than start_time_Flex: wrong assumption")
            #else:
            #    self.energy = self.bdry.vehicle.charge(self.end_time-self.start_time, self.rate)
        elif self.strategy == "as late as possible":
            self.energy = compute_charged_until_certain_time_according_to_Charging_strategy(self.bdry,
                                                                                            min(self.bdry.t_end,
                                                                                                end_time_Flex),
                                                                                            self.strategy)

            self.end_time = min(self.bdry.t_end, end_time_Flex)
            if self.energy == 0:
                self.rate = 0
            self.start_time = max(self.bdry.t_start, start_time_Flex, self.bdry.start_time_eneed)


            #if self.bdry.start_time_eneed != None:
            #    time_start_charging_for_e_need = self.bdry.start_time_eneed

            #else:
            #    if self.bdry.e_need > 0:
            #        if self.bdry.t_start < start_time_Flex:
            #            print("Error:123")
                    # compute latest point to start charging, which is different from t_min_start2, as this is the point
                    # to start charging, if discharged until e_min; but in this strategy no discharge until e_min
            #        time_start_charging_for_e_need = self.bdry.t_end - self.bdry.vehicle.time_to_charge(
            #                self.bdry.e_need, self.bdry.charging_power) #- datetime.timedelta(seconds=1)
            #    else:
            #        time_start_charging_for_e_need = self.bdry.t_end

            #if self.end_time <= time_start_charging_for_e_need or self.bdry.e_need <= 0:
                # charging not started
            #    self.energy = 0
            #    self.rate = 0
            #    self.start_time = self.end_time
            #else:
                # charging started, so compute energy charged until start_time
            #    self.start_time = max(time_start_charging_for_e_need, start_time_Flex, self.bdry.t_start)
            #    diff = self.end_time - self.start_time
            #    self.energy = self.bdry.vehicle.charge(diff, self.bdry.charging_power)


        elif self.strategy == "as long as possible with minimum rate":
            self.energy = compute_charged_until_certain_time_according_to_Charging_strategy(self.bdry,
                                                                                            min(self.bdry.t_end,
                                                                                                end_time_Flex),
                                                                                            self.strategy)
            self.rate = self.bdry.ch_rate_strategy_info
            self.end_time = min(self.bdry.t_end, end_time_Flex)
            #if self.bdry.t_start < start_time_Flex:
            #    print("Error: base_profile")
            self.start_time = max(self.bdry.t_start, start_time_Flex)
            if self.energy == 0:
                self.rate = 0
            if self.energy == self.bdry.e_max and self.energy != 0:
                possible_energy = self.bdry.vehicle.charge(self.end_time - self.bdry.t_start, self.rate)
                self.end_time = self.bdry.vehicle.time_to_charge(possible_energy, self.rate) + self.bdry.t_start

            #self.end_time = min(self.bdry.t_end, end_time_Flex)
            #if self.bdry.ch_rate_strategy_info!= None:
            #    ch_rate = self.bdry.ch_rate_strategy_info
            #else:
            #    if self.bdry.t_start < start_time_Flex:
            #        print("Error:123")
            #    else:
                    #compute min charging_rate
            #        ch_rate = compute_min_charging_rate(self.bdry.available_period.available_time,
            #                                            self.bdry.e_max,
            #                                            self.bdry.charging_power)
            #possible_energy = self.bdry.vehicle.charge(self.end_time - self.bdry.t_start, ch_rate)
            #energy_charged = min(possible_energy, self.bdry.e_max)
            #if possible_energy > self.bdry.e_max:
            #    self.end_time = self.bdry.vehicle.time_to_charge(possible_energy, ch_rate)+self.start_time


            #if self.bdry.e_curr >= self.bdry.e_max:
            #    self.energy = 0
            #    self.rate = 0
            #else:
            #    self.energy = energy_charged
            #    self.rate = ch_rate
        else:
            print("Error: Charging strategy not implemented")
        self.available_time = self.end_time - self.start_time


class HeuristicInformation:
    rate: float = None
    charging_end: datetime.timedelta = None
    energy: float = None

    def __init__(self, rate, energy, *args, **kwargs):
        super().__init__(**kwargs)
        self.rate = rate
        self.energy = energy


def compute_min_charging_rate(available_time, energy, max_charging_rate):
    if not CPCV:
        ch_rate = max((3600*energy)/(available_time.total_seconds()), MIN_CHARGING_RATE)
        ch_rate = min(ch_rate, max_charging_rate)
    #else:
        # somehow find out in efficient way
    return ch_rate


class specific_Flex_object:
    start_time: datetime.timedelta = None
    activation_time: datetime.timedelta = None
    duration: datetime.timedelta = None
    spontanflex: bool = None
    flex_place: str = None

    def __init__(self, start_time, activation_time, duration, spontanflex, flex_place,  *args, **kwargs):
        self.start_time = start_time
        self.activation_time = activation_time
        self.duration = duration
        self.spontanflex = spontanflex
        self.flex_place = flex_place
        # maybe if necessary, later add number of day/ run and daytype
    def __copy__(self):
        return specific_Flex_object(self.start_time, self.activation_time, self.duration, self.spontanflex, self.flex_place)

    def compare(self, start_time, activation_time, duration, flex_place, spontanflex):
        if self.spontanflex == spontanflex:
            if self.flex_place== flex_place:
                if self.start_time == start_time:
                    if self.activation_time == activation_time:
                        if self.duration == duration:
                            return "same"
        return "not the same"



class KPIs:
    """Container für Flexibilitäts-Kennzahlen eines (Strategie, Heuristik, Modus)-Tripels."""
    number_of_vehicles: int
    avg_soc : float
    avg_time : float
    avg_en : float
    avg_den : float

    def __init__(self, number_of_vehicles=None, avg_soc = None, avg_time = None, avg_en = None, avg_den = None):
        self.number_of_vehicles = number_of_vehicles
        self.avg_time = avg_time
        self.avg_en = avg_en
        self.avg_den = avg_den
        self.avg_soc = avg_soc