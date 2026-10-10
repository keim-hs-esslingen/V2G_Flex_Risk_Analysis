from simulation_model.TripChainGenerator import *
from simulation_model.PopulateUser import *
from flexibility_calc.flexibility import *

class Day:
    day_type: DayType = None
    available_periods: list = None
    number_of_day: int = None
    Flexibility_All: flex_on_day = None
    Flexibility_Home: flex_on_day = None
    Flexibility_Work: flex_on_day = None
    next_day_type: DayType = None

    def __init__(self, daytype, number_of_day):
        self.day_type = daytype
        self.available_periods = list()
        self.number_of_day = number_of_day
        self.Flexibility_All = flex_on_day(self.number_of_day)
        self.Flexibility_Home = flex_on_day(self.number_of_day)
        self.Flexibility_Work = flex_on_day(self.number_of_day)
        next_day_type = int(daytype) +1
        if next_day_type > 7:
            next_day_type = 1
        self.next_day_type = DayType("0" + str(next_day_type))


    def simulate_one_day(self, seed, user_list, ev_list, generator, charging_station_types, start = False):
        # Settings for trip generation
        #generator.set_daytype(self.day_type)

        counter = 0
        # sampling with different seeds
        for user in user_list:
            generator.set_daytype(self.next_day_type)
            counter = counter+1
            # ---------------------------TripChainGeneration----------------------------------------

            generator.set_seed(user.ID*int(self.day_type)+(seed+1)+13)
            generator.set_user(user)
            end_at_home = calculate_end_at_home_bool(self.next_day_type)
            user.set_trip_chain(generator.sample_trip_chain(end_at_home), next=True)
            #if user.ev_id == 768:
             #   print("hi")
            ev_list[user.ev_id].recalculate_user_chain_if_necessary(generator, self.next_day_type, seed, next=True)
            if start:
                generator.set_seed(user.ID * int(self.day_type) * (seed + 1)*197)
                generator.set_daytype(self.day_type)
                user.set_trip_chain(generator.sample_trip_chain(end_at_home = calculate_end_at_home_bool(self.day_type)), next = False)
                ev_list[user.ev_id].recalculate_user_chain_if_necessary(generator, self.day_type, seed, next=False)

            #check_sampled_trip_chain()
            #if counter==10:

            # form users sampled trip chains compute the trip chains of the corresponding cars
            # (may be different, if one car has several users (households)

        generator.set_daytype(self.day_type)
        counter = 0
        for ev in ev_list:
            #if counter == 53:
                #print("hi")
            # d = 0
            # compute car trips
            # here, simply one car for one user, therefore user trip chain equals car trip chain
            # However, taking households and several cars per household or user into account,
            # the car chain is different from user trip chain
            if start:
                ev.compute_car_trip_chain(next=False)

            ev.simulate_day(charging_station_types, generator, self.day_type, seed)
            self.available_periods.append([ev.total_available_period_list[-1], ev])

            # print(counter)

            counter = counter + 1

    def compute_available_periods_at_home(self):
        available_periods_home = list()
        for entry in self.available_periods:
            periods = entry[0]
            ev = entry[1]


            if not settingsContainer.getUserInteractionSimulation():
               ev.compute_min_energy(0.5, 0.35, settingsContainer.getMinSoc())
            else:
                ev.compute_soc_min(ev.user.range, settingsContainer.getMinSoc())

            periods_list = list()
            for period in periods:

                if period.__class__ == helper_files.variables.AvailablePeriod:
                    if period.home:
                        periods_list.append(period)
                else:
                    if period[0].home:
                        periods_list.append(period)
            if len(periods_list)>0:
                available_periods_home.append([periods_list, ev])
        return available_periods_home

    def compute_available_periods_at_work(self):
        available_periods_work = list()
        for entry in self.available_periods:
            periods = entry[0]
            ev = entry[1]


            if not settingsContainer.getUserInteractionSimulation():
               ev.compute_min_energy(0.5, 0.35, settingsContainer.getMinSoc())
            else:
                ev.compute_soc_min(ev.user.range, settingsContainer.getMinSoc())

            periods_list = list()
            for period in periods:

                if period.__class__ == helper_files.variables.AvailablePeriod:
                    if period.work:
                        periods_list.append(period)
                else:
                    if period[0].work:
                        periods_list.append(period)
            if len(periods_list)>0:
                available_periods_work.append([periods_list, ev])
        return available_periods_work

class Model(BaseModel):
    ev_list: list = list()
    User_list: list = list()
    day_list: list = list()
    DrivingTimes: list = list()
    Plugin_Times: list = list()
    Charging_Times: list = list()
    UserList: list = list()
    VehicleList: list = list()
    TC_Generator: TripChainGenerator = None
    charging_station_types_prob: ChargingStationTypesProbability = None
    start_day: DayType = None


    def __init__(self, NumberOfDays, NumberOfUsers, start_day, ch_types_prob, tc_generator,  filepath = "SimulationTool/EVModels.csv", *args, **kwargs):
        super().__init__(**kwargs)

        self.charging_station_types_prob = ch_types_prob

        # create TripChainGenerator
        self.TC_Generator = tc_generator

        # -----------------------------populate user generation--------------------------------------
        self.UserList, self.VehicleList = PopulateUser(NumberOfUsers, self.charging_station_types_prob, filepath)
        self.start_day = start_day
        self.day_list = list()
        day_1 = Day(self.start_day, 0)
        self.day_list.append(day_1)
        day_type = int(self.start_day)
        for ii in range(1, NumberOfDays):
            day_type = day_type + 1
            if day_type == 8:
                day_type = 1
            current_Day = Day("0" + str(day_type), ii)
            self.day_list.append(current_Day)

    def simulate_mobility_and_charging(self, seed = None):
        if seed == None:
            current_time = datetime.datetime.now()
            seed = current_time.microsecond+current_time.second +current_time.minute +current_time.hour + current_time.day



        for day in self.day_list:
            if day.number_of_day == 0:
                day.simulate_one_day(seed, self.UserList, self.VehicleList, self.TC_Generator,
                                     self.charging_station_types_prob, start = True)
            else:
                day.simulate_one_day(seed, self.UserList, self.VehicleList, self.TC_Generator, self.charging_station_types_prob)
            seed += 1
            #print(day.number_of_day)
            #if day.number_of_day == 53:
             #   print("hi")




def find_first_entry_with_larger_time_efficient(flex_list, count, reference_time):
    lower_border = count
    upper_border = len(flex_list)-1
    diff = upper_border - lower_border
    while diff >=2:
        current_pos = (diff // 2) + lower_border # floor operation: round down
        if flex_list[current_pos] < reference_time:
            lower_border = current_pos +1
        else:
            upper_border = current_pos
        diff = upper_border-lower_border
    if lower_border == upper_border:
        index=lower_border
    else:
        if flex_list[lower_border] < reference_time:
            index = upper_border
            if flex_list[index] < reference_time:
                print("Error-idx-calculation")
        else:
            index = lower_border
            if flex_list[max(index-1,0)] > reference_time:
                print("Error-idx-calculation")

    flex_list.insert(index, reference_time)
    return index
