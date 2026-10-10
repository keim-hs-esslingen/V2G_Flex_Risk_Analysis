from simulation_model.Run import *

class Aggregated_ChargingProfile:
    total_power: float = None
    ChargingProfiles: list = None
    capacities: list = None
    start_time: datetime.timedelta = None
    end_time: datetime.timedelta = None
    rel_total_power: float = None

    def __init__(self, start, end, **kwargs):
        super().__init__(**kwargs)
        self.total_power= 0
        self.ChargingProfiles = list()
        self.capacities = list()
        self.start_time = start
        self.end_time = end
        self.rel_total_power =0

    def append_entry(self, ChargingSession):
        self.ChargingProfiles.append(ChargingSession)
        self.capacities.append(ChargingSession.rate)
        self.total_power += ChargingSession.rate

    def compute_relative_to_value(self, value):
        self.rel_total_power = (self.total_power/value)*100
        return self.rel_total_power


class Several_Charging_Profiles:
    intervals_ChargingProfiles: list = None
    times: list = list()
    interval_size: datetime.timedelta = None
    start: datetime.timedelta = None
    end: datetime.timedelta = None
    total_duration = None
    total_power: float = None
    number_of_intervals: int = None
    number_of_vehicles: int = None

    def __init__(self, start, end, interval_size, **kwargs):
        super().__init__(**kwargs)
        self.start = start
        self.end = end
        self.interval_size = interval_size
        self.total_duration = self.end - self.start
        self.intervals_ChargingProfiles = list()
        self.total_power = 0
        self.number_of_intervals = math.ceil(self.total_duration.total_seconds()/self.interval_size.total_seconds())
        self.number_of_vehicles = None

    def compute_intervals(self):
        start = self.start
        end = self.start+self.interval_size
        for i in range(self.number_of_intervals):
            self.intervals_ChargingProfiles.append(Aggregated_ChargingProfile(start, end))
            if i == self.number_of_intervals - 2:
                end = self.end
            else:
                end += self.interval_size
            start += self.interval_size

    def append_Charging_session(self, Charging_Session):
        if not Charging_Session.start.__class__ == datetime.timedelta:
            start = Charging_Session.start.to_timedelta()
            end = Charging_Session.end.to_timedelta()
        else:
            start = Charging_Session.start
            end = Charging_Session.end
        interval_start = math.floor((start-self.start)/self.interval_size)
        interval_end = math.floor((end-self.start-datetime.timedelta(seconds=1))/self.interval_size)
        for interval in range(interval_start, interval_end +1):
            self.intervals_ChargingProfiles[interval].append_entry(Charging_Session)
            if self.intervals_ChargingProfiles[interval].start_time > end or self.intervals_ChargingProfiles[interval].end_time < start:
                print("Error-CH-profile computation, wrong interval")
        self.total_power += Charging_Session.rate

    def visualize_profile(self, number_of_vehicles = None):
        y = list()
        x = list()
        count = 0
        for entry in self.intervals_ChargingProfiles:
            if number_of_vehicles!=None:
                y.append(entry.compute_relative_to_value(number_of_vehicles))
            else:
                y.append(entry.compute_relative_to_value(self.total_power))
            x.append(count*(self.interval_size.total_seconds()/3600))
            count +=1

        plt.plot(x,y)

    def compare_profiles(self, cmp_profile):
        # premise: same interval_size
        if self.interval_size != cmp_profile.interval_size:
            print("Please only compare profiles with the same interval size")
            return
        dist_relative = list()
        dist_absolute = list()
        for i in range(self.number_of_intervals):
            self.intervals_ChargingProfiles[i].compute_relative_to_value(self.total_power)
            cmp_profile.intervals_ChargingProfiles[i].compute_relative_to_value(cmp_profile.total_power)
            dist_abs = self.intervals_ChargingProfiles[i].rel_total_power - cmp_profile.intervals_ChargingProfiles[i].rel_total_power
            dist_relative.append(dist_abs/self.intervals_ChargingProfiles[i].total_power)
            dist_absolute.append(dist_abs)
        return dist_relative, dist_absolute

    def set_number_of_vehicles(self, number_of_vehciels):
        self.number_of_vehicles = number_of_vehciels


def compute_charging_profile(DayType, VehicleList, start_day, kind, number_of_days):
    day_profile = Several_Charging_Profiles(datetime.timedelta(0), datetime.timedelta(days=1), datetime.timedelta(minutes = 10))
    day_profile.compute_intervals()
    if kind == "Home":
        cmp_place = ChargingStationPlace.HOME
    elif kind == "Work":
        cmp_place = ChargingStationPlace.WORK
    elif kind == "Public":
        cmp_place = ChargingStationPlace.PUBLIC

    Days = compute_day_list(DayType, start_day, number_of_days)

    for runs in range(settingsContainer.getNumberOfRuns()):
        for Vehicle in VehicleList[runs]:
            for day in Days:
                for i in range(len(Vehicle.total_Charging_list[day])):
                    current_session = Vehicle.total_Charging_list[day][i]
                    if current_session.station.Place == cmp_place:
                        day_profile.append_Charging_session(current_session)

        # print(runs)
    day_profile.set_number_of_vehicles(runs*len(VehicleList[runs])*len(Days))
    return day_profile

def compute_ch_profile(kinds, calib = False):
    start_day = settingsContainer.getStartDay()
    number_of_days = settingsContainer.getNumberOfDays()
    # if model should be run again
    if calib:
        model_data= run(number_of_days,settingsContainer.getNumberOfUsers(), start_day, settingsContainer.getNumberOfRuns())
        # saving List
        VehicleLists = model_data.VehicleLists
        save_list(VehicleLists, "models/charging_profile-validation/VehicleList2")
    # open list
    VehicleLists = open_file('models/charging_profile-validation/VehicleList2')

    day_profiles = list()
    for kind in kinds:
        day_kind= compute_charging_profile(-1, VehicleLists, int(start_day), kind, number_of_days)
        day_profiles.append(day_kind)
    return day_profiles


def compute_day_list(DayType, start_daytype, Number_of_days, ignore_first_days=1):
    # list, which days to compute spontanflex of
    if DayType <= 0:

        Days = [i for i in range(ignore_first_days,Number_of_days)]
    elif DayType > 0 and DayType < 8:
        start = 0
        while start_daytype != start:
            start += 1
        Days = list()#[7 * i + start for i in range(int(Number_of_days / 7)+1)]
        for i in range(int(Number_of_days/7)+1):
            if 7*i +start > ignore_first_days:
                Days.append(7*i +start)

    else:
        print("Error: wrong daytype, insert value between -1,0 = Unknown, 1 = Monday, 2 = Tuesday,7 = Sunday...")
        return
    return Days


def compute_UK_ch_profiles(DayType, filename="dataCharging/alreadyLoaded/UK_charging_whole"):
    day_profile = Several_Charging_Profiles(datetime.timedelta(0), datetime.timedelta(days=1),
                                            datetime.timedelta(minutes=10))
    day_profile.compute_intervals()

    #Days = compute_day_list(DayType, start_day)
    count = 0
    data = open_file(filename)
    for entry in data:

        if count %1000 == 0:
            print(count)
        #if count > 0 and count % 1000000 == 0:
            #return day_profile
        count +=1
        sessions = list()
        if entry[6] > datetime.timedelta(days=1):
            end = datetime.timedelta(days=1)
            append = False
            all_append = False
            if DayType != 8:
                if DayType < 7 and DayType >= 0:
                    all_append = False
                    if entry[0].weekday() == DayType:
                        append = True
                else:
                    print("Error: Daytype between 0 and 8: for Monday until Sunday and Unknown (8)")
                    return
            else:
                append = True
                all_append = True
            session = ChargingSession(entry[1], end, 0, 0, None, rate=entry[7])
            sessions.append(session)
            for i in range(1, entry[6].days+1):
                if all_append or DayType == (entry[0] + datetime.timedelta(days = i)).weekday():
                    start = datetime.timedelta(0)
                    if i < entry[6].days:
                        end = datetime.timedelta(days = 1)
                    else:
                        end = entry[6] - datetime.timedelta(days = i)
                    session = ChargingSession(start, end, 0, 0, None, rate=entry[7])

                    sessions.append(session)

        else:
            append = False
            if DayType != 8:
                if DayType < 7 and DayType >= 0:
                    if entry[0].weekday() == DayType:
                        append = True
                else:
                    print("Error: Daytype between 0 and 8: for Monday until Sunday and Unknown (8)")
                    return
            else:
                append = True
            if append:
                session = ChargingSession(entry[1], entry[6], 0,0, None, rate=entry[7])
                sessions.append(session)
        for session in sessions:
            day_profile.append_Charging_session(session)
    #day_profile.set_number_of_vehicles(runs * len(VehicleList[runs]) * len(Days))

    return day_profile