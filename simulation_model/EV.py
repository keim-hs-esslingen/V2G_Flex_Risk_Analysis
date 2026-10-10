from simulation_model.ChargingStationAndUser import *

class EVModels_Probability(BaseModel):
    # This class reads EV types from the corresponding file.
    # This file contains in each row different EV models
    # and the probability distribution for these models for different economic status

    models: list = None
    all_probs = list()

    def __init__(self, filepath = "SimulationTool/EVModels.csv", *args, **kwargs):
        # reading file and append each row to list of local attribute types
        # possible ToDo: if there is now file, assign default values
        #  (or assign types not with file, but with manual input
        # -->dependant of implementation with angular and user interaction before simulation
        super().__init__(**kwargs)
        self.models = list()

        with open(os.path.join(filepath)) as file:
            csv_reader = csv.reader(file, delimiter=';')
            self.all_probs = [list(), list(), list(), list(), list(), list()]
            for row in csv_reader:
                without_number = row[1][1:-1].split(', ')
                for j in range(6):
                    self.all_probs[j].append(without_number[j+7])
                self.models.append(EVModel(battery_size=float(without_number[1]), ac_power=float(without_number[2]), dc_power=float(without_number[3]), ec_d_avg=float(without_number[4]), ec_d_min = float(without_number[5]), ec_d_max = float(without_number[6])))

    def assign_ev(self, economic_status):
        # gets an economic status and returns an EV choosing a model according the given probabilities

        return self.models[np.random.choice([j for j in range(0, len(self.models))],  p=self.all_probs[economic_status-1])]
        #self.types[np.random.choice([i for i in range(0,len(self.types))], p=self.probs_home_or_work)], charging_station_place)


class EVModel(BaseModel):
    battery_size: float = None
    AC_power: float = None
    DC_power: float = None
    discharge_AC_power: float = None
    discharge_DC_power: float = None
    # possible ToDo soc_saturation (CCCV)
    ec_d_avg: float = None  # in kwh/100km
    ec_d_min: float = None
    ec_d_max: float = None
    ec_d_range_avg: float = None
    current_available_period: AvailablePeriod = None
    min_energy: float = None
    # energy_consumption_parking: float

    def __init__(self, battery_size, ac_power, dc_power,  ec_d_avg, ec_d_min, ec_d_max, *args, **kwargs):
        super().__init__(**kwargs)
        self.battery_size = battery_size
        self.AC_power = ac_power
        self.DC_power = dc_power
        self.ec_d_avg = ec_d_avg
        self.ec_d_min = ec_d_min
        self.ec_d_max = ec_d_max
        self.ec_d_range_avg = (self.ec_d_max -self.ec_d_min)/2 + self.ec_d_min

        # possible Todo: discharge and charge with different powers
        self.discharge_AC_power = self.AC_power
        self.discharge_DC_power = self.DC_power
        # computing minimum range: large vehicles 50 km, small: 35 km



        if self.battery_size / self.ec_d_max > 2:
            min_range = self.ec_d_max * 0.5
        else:
            min_range = self.ec_d_max * 0.35
            # or energy for MIN_SOC

            # energy difference to minimum energy possible during flexibility_calc scenarios
        self.min_energy = max(settingsContainer.getMinSoc() * 0.01 * self.battery_size, min_range)

    def compute_min_energy(self, range_bdry_large, range_bdry_small, min_SOC):
        # computing minimum range: large vehicles 50 km, small: 35 km
        if self.battery_size / self.ec_d_max > 2:
            min_range = self.ec_d_max * range_bdry_large
        else:
            min_range = self.ec_d_max * range_bdry_small
        # or energy for MIN_SOC

        # energy difference to minimum energy possible during flexibility_calc scenarios
        self.min_energy = min(max(min_SOC * 0.01 * self.battery_size, min_range, self.min_energy),self.battery_size)

    def compute_soc_min(self, range, min_SOC):
        min_range = ((self.ec_d_max-self.ec_d_avg)/2 + self.ec_d_range_avg) * range/100
        self.min_energy = min(self.battery_size, max(min_SOC*0.01*self.battery_size, min_range))


class EV(EVModel):
    ID: int = None
    user: EVUser = None  # later as array, if more than one user per ev is possible
    sampled_trip_chain: TripChain = None # EV trip chain may be different from EVuser trip chain, if no 1:1 relation
    next_trip_chain: TripChain = None
    PlugIn_Times = list()
    Charging_Times = list()
    SOC_list: SOCDuringDay = SOCDuringDay()
    previous_day_last_trip_arrival: nptime = None
    current_station: ChargingStation = None

    current_available_period: AvailablePeriod = None
    last_period: AvailablePeriod = None
    available_periods = list()
    base_charging_periods = list()
    total_SOC_list = list()
    total_Charging_list = list()
    total_driving_list = list()
    total_trip_chain_list = list()
    total_plugin_list = list()
    total_available_period_list = list()
    total_base_charging_periods_list = list()
    Available: bool = None
    flex_active: bool = None

    def __init__(self, ev_id, ev_user,  *args, **kwargs):
        super().__init__(**kwargs)
        self.ID = ev_id
        self.user = ev_user
        if self.user.ChargingStation.ac:
            self.current_available_period = AvailablePeriod(start_SOC=self.SOC_list.get_soc(), charging_power=min(self.AC_power, self.user.ChargingStation.power),
                                                        discharging_power=min(self.discharge_AC_power, self.user.ChargingStation.power), days = -1)
        else:
            self.current_available_period = AvailablePeriod(start_SOC=self.SOC_list.get_soc(), charging_power=min(self.DC_power, self.user.ChargingStation.power),
                                                        discharging_power=min(self.discharge_DC_power, self.user.ChargingStation.power), days = -1)  #in initizalize_next_day days are incremented to 0 (start_value)

        self.Available = True
        self.last_period = self.current_available_period
        self.flex_active = False
        if settingsContainer.getUserInteractionSimulation():
                     self.compute_soc_min(self.user.range, settingsContainer.getMinSoc())
        else:
                     self.compute_min_energy(self.ec_d_max, self.ec_d_min, settingsContainer.getMinSoc())


    def append_entry_and_check(self, state, time, soc):
        if not self.SOC_list.append_entry(state, time, soc):
            self.SOC_list.SOC[-1] = 0
            #self.user.sampled_trip_chain
            #self.initialize_next_day()
        #elif self.SOC_list.get_soc()<10
            # check if posponinng trips is possible

    def simulate_day(self, charging_station_types_prob, generator, day_type, seed):

        self.initialize_next_day()

        self.total_driving_list.append([[trip.departure, trip.arrival] for trip in self.sampled_trip_chain.trips])
        self.soc_during_day(charging_station_types_prob, generator, day_type, seed)
        self.total_plugin_list.append(self.PlugIn_Times.copy())
        #print([self.PlugIn_Times[i][1] for i in range(len(self.PlugIn_Times))])
        self.total_Charging_list.append(self.Charging_Times.copy())
        self.total_SOC_list.append(self.SOC_list.copy())
        self.total_trip_chain_list.append(self.sampled_trip_chain)
        #if len(self.total_trip_chain_list)>1 and self.sampled_trip_chain.length>0 and self.total_trip_chain_list[-2].length>0:
        #    if self.sampled_trip_chain.trips[-1] == self.total_trip_chain_list[-2].trips[-1]:
            #    print("Error: seed")


        # append available_period, which last several days, to all days, where it occurs
        if len(self.available_periods) > 0 and self.available_periods[0].days > 0:


            counter = 1


            while counter <= self.available_periods[0].days:
                # append also information, on which day of the available period, the corresponding day belongs to
                self.total_available_period_list[len(self.total_available_period_list)-counter].append([self.available_periods[0], self.available_periods[0].days - counter])
                counter = counter + 1
            self.available_periods[0] = [self.available_periods[0], self.available_periods[0].days]
        self.total_available_period_list.append(self.available_periods)


        # append base_charging period, which last several days to all days, where it occurs
        if len(self.base_charging_periods) > 0:
            if self.base_charging_periods[0].__class__ != AvailablePeriod:
                breakpoint()
            if self.base_charging_periods[0].days > 0:
                counter = 1
                # if self.available_periods[0].days >3:
                # print("hi")
                while counter <= self.base_charging_periods[0].days:
                    # append also information, on which day of the available period, the corresponding day belongs to
                    self.total_base_charging_periods_list[len(self.total_base_charging_periods_list)-counter].append([self.base_charging_periods[0], self.base_charging_periods[0].days - counter])
                    if counter > len(self.total_base_charging_periods_list):
                        print("Error: calculation of base_charging periods")
                        breakpoint()
                    counter = counter + 1
                self.base_charging_periods[0] = [self.base_charging_periods[0], self.base_charging_periods[0].days]
        self.total_base_charging_periods_list.append(self.base_charging_periods)

    def soc_during_trip(self, trip, last_trip_on_next_day, charging_station_types_prob, last_trip = False):
       # computes SOC during one trip and parking/charging after trip until next trip starrts
       # fügt Plug_in_Times, Charging_Times an lokale Liste an
       # assumptions: charging_start=plugIn_start, plugin_end=start of next trip
        if trip.departure == self.SOC_list.times[-1]:
            self.SOC_list.states[-1] = "Driving"
            # TODO: not urgent: special case: trip begins at zero:
            if len(self.SOC_list.states)==1 and len(self.total_SOC_list)>0 and self.total_SOC_list[-1].SOC[-1]==100:
                self.Available = True
            else:
            #oder: len(self.SOC_list)==1 # falls erster Trip, dann einfach Available von vorher übernehmen, aber richtig mit rekursiv, ...?oberes vllt besser
                self.Available = False
        else:
            if not self.SOC_list.append_entry("Driving", trip.departure, self.SOC_list.get_soc()):
                return False

        self.current_available_period.end_time = trip.departure
        energy_consumed = self.energy_consumption(trip.distance, trip.duration)

        if not self.SOC_list.append_entry("OnlyParking", trip.arrival, self.SOC_list.get_soc() - energy_consumed / self.battery_size):
            return False
        else:
            #need_SOC = min(max(self.SOC_list.SOC[-2]-self.SOC_list.SOC[-1]+settingsContainer.getSocTol(), settingsContainer.getMinSoc()), 100)
            #self.current_available_period.min_SOC = need_SOC
            if np.random.rand() * 100 < settingsContainer.getV2GAvailability():
                if self.Available and self.current_available_period.check_availability(self):
                # self.current_available_period.compute_FlexBoundary(self, simple=SIMPLE)
                    #self.current_available_period
                    start_energy = self.current_available_period.start_SOC * self.battery_size * 0.01
                    ap_on_next_day = False

                    if start_energy < self.min_energy:


                        ap_on_next_day, base_charging = self.current_available_period.period_adaption(self, start_energy)
                        self.base_charging_periods.append(base_charging)
                    self.available_periods.append(self.current_available_period)
                    if self.current_available_period.start_SOC<(self.min_energy/self.battery_size)*100:
                        print("hi")

            elif self.current_available_period.start_time != None:
                self.base_charging_periods.append(self.current_available_period)
            # reset variable and
            self.Available = True
            # initialize potential next AvailablePeriod
            self.current_available_period = AvailablePeriod(start_SOC=self.SOC_list.get_soc(), charging_power=self.AC_power,
                                                        discharging_power=self.discharge_AC_power)

        charging_station_place = get_purposes_category(trip.purpose)
        SOC_needed_computed, plugging_in = self.getSOC_for_next_trip(last_trip, trip, max(settingsContainer.getMinSoc(), self.min_energy/self.battery_size * 100))
        self.current_available_period.set_minSOC(SOC_needed_computed)

        if settingsContainer.getPlugInSimple() and plugging_in:
            plugin_start = self.user.plug_in_decision_simple(trip)
        else:
            SOC_for_next_trip, plugging_in = self.getSOC_for_next_trip(last_trip, trip, max(settingsContainer.getMinSocPlugIn(), self.min_energy/self.battery_size * 100))
            if plugging_in:
                plugin_start = self.user.plug_in_decision_complex(self.SOC_list.get_soc(), SOC_for_next_trip, charging_station_place, trip)
            else:

                plugin_start = -1
        if plugin_start == -1:
                self.current_available_period.start_time = None
                self.Available = False
                # no plug_in, no available period
        elif plugin_start> nptime(0):

                self.current_available_period.start_time = plugin_start
                if trip.staytime == None: #or (nptime(23, 59, 59, 999999)-trip.arrival) < trip.staytime:
                    if last_trip_on_next_day:
                        plugin_end = trip.arrival
                    else:
                        plugin_end = nptime(23, 59, 59, 999999)
                else:
                    plugin_end = trip.arrival+trip.staytime
                self.PlugIn_Times.append([plugin_start, plugin_end])

                if plugin_start == trip.arrival:
                    self.SOC_list.states[-1] = "Charging"
                else:
                    if not self.SOC_list.append_entry("Charging", plugin_start, self.SOC_list.get_soc()):
                        return False


                if charging_station_place == ChargingStationPlace.HOME:
                    self.current_station = self.user.ChargingStation

                elif charging_station_place == ChargingStationPlace.WORK:
                    self.current_available_period.set_home(False)
                    self.current_available_period.set_work(True)
                    self.current_station = self.user.ChargingStation_work
                else:
                    self.current_available_period.set_home(False)
                    self.current_station = charging_station_types_prob.assign_charging_station(charging_station_place)

                charging_end, soc_after_charging, charging_rate = self.charging_full_if_possible(plugin_start, plugin_end)

                self.Charging_Times.append(ChargingSession(plugin_start, charging_end, soc_after_charging, self.SOC_list.get_soc(), self.current_station, charging_rate))


                if not self.SOC_list.append_entry("parkingPluggedIn", charging_end,  soc_after_charging):
                    return False
        else:
                print("Error: plug-in determination")
        return True

    def energy_consumption(self, distance, duration=0, max_consumption_if_range = None):
        # computes energy consumption dependent on distance and the energy_consumption parameter

        if settingsContainer.getEnergyConsmuption() == "constant":
            rate = self.ec_d_avg

        elif settingsContainer.getEnergyConsmuption() == "constant in range":

            rate = np.random.normal(self.ec_d_avg)
            while rate > self.ec_d_max or rate < self.ec_d_min:
                rate = np.random.normal(self.ec_d_avg)

        if max_consumption_if_range == True:
            rate = self.ec_d_max
        energy_consumed = rate * (distance) #*1.2#*10

        #else: other cases
        # possible Todo:  mit Fahrzyklen

        return energy_consumed

    def  getSOC_for_next_trip(self, last_trip, trip, min_soc):
        plugging_in = True
        if last_trip:
                if self.user.charge_every_day_on_evening:
                    SOC_for_next_trip = 100
                elif settingsContainer.getMinSocAfterLastTripActive():
                    SOC_for_next_trip = settingsContainer.getMinSocAfterLastTrip()
                else:
                    if self.next_trip_chain.length>0:
                        SOC_for_next_trip_bn = max(self.energy_consumption(self.next_trip_chain.trips[0].distance,
                                                        max_consumption_if_range=True) / self.battery_size
                                + settingsContainer.getSocTol(), 100)
                        SOC_for_next_trip, plugging_in = self.compute_needed_SOC(SOC_for_next_trip_bn, trip, min_soc)


                    else:
                        SOC_for_next_trip = min_soc

        else:
            SOC_for_next_trip_bn = min(
                self.energy_consumption(self.sampled_trip_chain.trips[trip.numberInChain + 1].distance,
                                        max_consumption_if_range=True) / self.battery_size +
                settingsContainer.getSocTol(), 100)

            SOC_for_next_trip, plugging_in = self.compute_needed_SOC(SOC_for_next_trip_bn, trip, min_soc)

        return SOC_for_next_trip, plugging_in

    def charging_full_if_possible(self, plugin_start, plugin_end, current_soc = None):
        # computes if there is enough charging time for 100 SOC.
        # if not, it computes soc at the end of charging time
        # uses constant charging rate from the corresponding current station
        # possible Todo CCCV
        time_for_charging = plugin_end - plugin_start
        if time_for_charging < datetime.timedelta(0):
            #if time for charging is negative, which means plugin_end is smaller then plugin_start
            # which means that plugin_end is on next day, the computed timedelta is positive
            time_for_charging = time_for_charging + datetime.timedelta(days=1)
        if current_soc== None:
            current_soc = self.SOC_list.get_soc()
        if self.current_station.ac:
            charging_rate = min(self.current_station.power, self.AC_power)
            discharging_rate = min(self.current_station.discharge_power, self.discharge_AC_power)
        else:
            charging_rate = min(self.current_station.power, self.DC_power)
            discharging_rate = min(self.current_station.discharge_power, self.discharge_DC_power)
        self.current_available_period.charging_power = charging_rate
        self.current_available_period.discharging_power = discharging_rate
        energy_to_charge = self.battery_size*(100-current_soc)*0.01
        #time_to_fully_charge = datetime.timedelta(hours=energy_to_charge/charging_rate)
        time_to_fully_charge = self.time_to_charge(energy_to_charge, charging_rate)
        if time_to_fully_charge > time_for_charging:
            charged_energy = self.charge(time_for_charging, charging_rate)
            soc_after_charging = current_soc+(charged_energy/self.battery_size)*100
            charging_end = plugin_end
        else:
            soc_after_charging = 100
            charging_end = plugin_start+time_to_fully_charge
        return charging_end, soc_after_charging, charging_rate

    def time_to_charge(self, energy, charging_rate, cpcv=False, start_soc=0):
        if not cpcv:
            # constant charging
            if charging_rate ==0:
                print("Error: charging rate zero")
            time_to_charge = datetime.timedelta(hours=energy / charging_rate)
        #else:
            #charging more complex
        return time_to_charge

    def charge(self, time_to_charge, charging_rate, cpcv=False, start_soc = 0):
        if not cpcv:
            # constant charging
            if time_to_charge.__class__==datetime.timedelta:
                time = time_to_charge.total_seconds()
                charged_energy = (time/3600) * charging_rate
            else:
                charged_energy = (time_to_charge.seconds/3600 + time_to_charge.microseconds/3600000000)*charging_rate
    # else:
    # charging more complex
        return charged_energy

    def discharge(self, time_to_charge, discharging_rate, cpcv = False, start_soc = 0):
        if not cpcv:
            # constant charging
            discharged_energy = (time_to_charge.seconds/3600 + time_to_charge.microseconds/3600000000)*discharging_rate
    # else:
    # charging more complex
        return discharged_energy

    def time_to_discharge(self, energy, discharging_rate, start_soc = 0, cpcv=False):
        if not cpcv:
            # constant charging
            time_to_discharge = datetime.timedelta(hours = energy / discharging_rate)
        #else:
            #charging more complex
        return time_to_discharge

    def soc_during_day(self, charging_station_types_prob, generator, day_type, seed, recursive_count =0):
        interrupted = False

        for trip in self.sampled_trip_chain.trips:

            if not self.soc_during_trip(trip, self.sampled_trip_chain.last_time_on_next_day, charging_station_types_prob, trip.numberInChain == self.sampled_trip_chain.length -1):
                #if trip has negative soc, recalculate it
                interrupted = True

                break
            elif trip == self.sampled_trip_chain.trips[-1]:
                self.last_period = self.current_available_period


        if interrupted:
            if recursive_count == 100:
                print("Error: Please recalculate: Something real rare happened")
                breakpoint()
            #recalculate trip chain, if SOC during trip returned False
            generator.set_seed(generator.seed * 31)
            end_at_home = calculate_end_at_home_bool(day_type)
            #end_at_work = calculate_end_at_work_bool(day_type)
            self.user.set_trip_chain(generator.sample_trip_chain(end_at_home = end_at_home), next = False)
            # if user chain and ev chain are not the same, and a car has more users somehow recalculate previous calculated cars with this user, as well or guarantee no changes there by
            self.recalculate_user_chain_if_necessary(generator, day_type, generator.seed*3, next = False)

            # reinitialize with the knowledge that this is a recursive call to use old values
            self.initialize_next_day(recursive=True)

            self.soc_during_day(charging_station_types_prob, generator, day_type, generator.seed*3, recursive_count+1)
        else:
            #reset last trip arrival
            self.previous_day_last_trip_arrival = nptime(0, 0)

            self.user.set_trip_chain(next=False, trip_chain=self.user.next_trip_chain.copy())

    def compute_car_trip_chain(self, next = True):
        # if car trip is different from user trip chain, but in this version not
        if next:
            self.next_trip_chain = self.user.next_trip_chain.copy()
        else:
            self.sampled_trip_chain = self.user.sampled_trip_chain.copy()
        #if self.sampled_trip_chain.length > 0 and self.sampled_trip_chain.trips[0].departure < nptime(4, 4, 4, 4):
            #print("hi2")

    def initialize_next_day(self, recursive=False):
        plugin_start = nptime(0, 0, 0)
        self.SOC_list.states = list()

        if recursive:
            soc = self.SOC_list.SOC[0]
            if self.last_period.start_time!= None:

                if self.previous_day_last_trip_arrival > nptime(0, 0):

                    plugin_start = self.previous_day_last_trip_arrival

                # find charging station of last session
                # saved in total Charaging list as last entry, even if self.previous_day_last_trip_arrival > nptime(0,0),
                # as then Charging session with duration of 0 seconds is appended to charging list
                #
                counter = 1
                while counter <= len(self.total_Charging_list) and len(self.total_Charging_list[-counter]) == 0:
                    counter = counter + 1
                if counter <= len(self.total_Charging_list):
                    self.current_station = self.total_Charging_list[-counter][-1].station
                else:
                    self.current_station = self.user.ChargingStation
                self.current_available_period = self.last_period
                self.Available = True
            else:
                if self.total_SOC_list[-1].states[-1]!="OnlyParking":
                    print("hi6")
                self.current_available_period = self.last_period
                self.Available = False
            self.compute_car_trip_chain(next=False)
        else:

            soc = self.SOC_list.get_soc()

            if self.sampled_trip_chain != None and self.sampled_trip_chain.last_time_on_next_day:
                    # in not recursive calls, this variable is resetted, in recursive calls not,
                    self.previous_day_last_trip_arrival = self.SOC_list.times[-1]
                    plugin_start = self.previous_day_last_trip_arrival

            else:
                self.previous_day_last_trip_arrival = nptime(0, 0)
                self.current_available_period.days = self.current_available_period.days + 1

            self.compute_car_trip_chain(next=False)
            self.compute_car_trip_chain(next=True)

        self.PlugIn_Times = list()
        self.available_periods = list()
        self.base_charging_periods = list()
        self.Charging_Times = list()
        self.SOC_list.SOC = list()
        self.SOC_list.times = list()



        if self.Available:
            self.SOC_list.append_entry("parkingPluggedIn", plugin_start, soc)
            self.charging_at_beginning_of_the_day(plugin_start)

        else:
            if len(self.total_SOC_list) > 0 and len(self.total_SOC_list[-1].SOC) > 0 and self.total_SOC_list[-1].SOC[-1]!= 100 and self.total_SOC_list[-1].states[-1]!= "OnlyParking":
                print("Error -initialization")

            self.SOC_list.append_entry("OnlyParking", plugin_start, soc)

    def check_user_chain_possible_with_car(self, next = False):
        if next:
            if self.next_trip_chain != None and \
                    self.next_trip_chain.length > 0 and \
                    self.next_trip_chain.last_time_on_next_day and \
                    self.user.next_trip_chain.length > 0 and \
                    self.next_trip_chain.trips[-1].arrival > self.user.next_trip_chain.trips[0].departure:
                return False
            else:
                return True
        else:
            if self.total_trip_chain_list!= None and \
                    len(self.total_trip_chain_list) > 0 and \
                    self.total_trip_chain_list[-1].length > 0 and \
                    self.total_trip_chain_list[-1].last_time_on_next_day and \
                    self.user.sampled_trip_chain.length > 0 and \
                    self.total_trip_chain_list[-1].trips[-1].arrival > self.user.sampled_trip_chain.trips[0].departure:



                    #self.sampled_trip_chain != None and \
                    #self.sampled_trip_chain.length > 0 and \
                    #self.sampled_trip_chain.last_time_on_next_day and \
                    #self.user.sampled_trip_chain.length > 0 and \
                    #self.sampled_trip_chain.trips[-1].arrival > self.user.sampled_trip_chain.trips[0].departure:
                return False
            else:
                return True

    def recalculate_user_chain_if_necessary(self, generator, day_type, seed, next = True):
        seed_counter = 0
        while not self.check_user_chain_possible_with_car(next):
            seed_counter = seed_counter + 1
            generator.set_seed(self.user.ID * int(day_type) * (seed + 1) * seed_counter)
            end_at_home = calculate_end_at_home_bool(day_type)
            self.user.set_trip_chain(generator.sample_trip_chain(end_at_home = end_at_home), next)
            if seed_counter > 20:
                print("Endlosschleife bei user chain berechnen?!")
                break

    def charging_at_beginning_of_the_day(self, plugin_start):
        if self.SOC_list.SOC[-1] != 100:
            self.SOC_list.states[0] = "Charging"

            if self.current_station == None:
                self.current_station = self.user.ChargingStation
            if self.sampled_trip_chain.length > 0:
                plugin_end = self.sampled_trip_chain.trips[0].departure
            else:
                plugin_end = nptime(23, 59, 59, 999999)

            charging_end, soc_after_charging, charging_rate = self.charging_full_if_possible(plugin_start, plugin_end)

            self.Charging_Times.append(ChargingSession(plugin_start, charging_end, soc_after_charging, self.SOC_list.get_soc(), self.current_station, charging_rate))

            self.SOC_list.append_entry("parkingPluggedIn", charging_end, soc_after_charging)
        if self.sampled_trip_chain.length > 0:
            plugin_end = self.sampled_trip_chain.trips[0].departure
        else:
            plugin_end = nptime(23, 59, 59, 999999)
        self.PlugIn_Times.append([plugin_start, plugin_end])

    def set_flex_active(self, active):
        self.flex_active = active

    def compute_needed_SOC (self, SOC_for_next_trip_bn, trip, min_soc):
        plugging_in = True
        if settingsContainer.getUserInteractionSimulation():
            current_time = datetime.datetime.now()


            np.random.seed(17 + 13 * self.ID*(current_time.day+current_time.minute + current_time.second + current_time.hour)) #+ current_time.microsecond))
            uncertainty = np.random.lognormal(0, 1) * SOC_for_next_trip_bn / 10
            if SOC_for_next_trip_bn + uncertainty > (self.min_energy / self.battery_size) * 100:
                if SOC_for_next_trip_bn + uncertainty > 80:
                    # notavailable
                    SOC_for_next_trip = 100
                    plugging_in = False
                else:
                    SOC_for_next_trip = 80
            else:
                SOC_for_next_trip = max(SOC_for_next_trip_bn, min_soc)
        else:
            SOC_for_next_trip = max(SOC_for_next_trip_bn, min_soc)
        return SOC_for_next_trip, plugging_in

    def set_current_station(self, station):
        self.current_station = station


