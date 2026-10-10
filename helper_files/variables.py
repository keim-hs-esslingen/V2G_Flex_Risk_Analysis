from enum import Enum
from pydantic import BaseModel, conint, confloat
from typing import List, Union
from helper_files.nptime import nptime
import numpy as np
import pickle
from config.settings import *
import matplotlib.pyplot as plt

class Age(str, Enum):
    UNDER_FORTY = "01"
    FORTY_TO_SIXTY_FIVE = "02"
    OVER_SIXTY_FIVE = "03"
    UNKNOWN = "00"


class DayType(str, Enum):
    MONDAY = "01"
    TUESDAY = "02"
    WEDNESDAY = "03"
    THURSDAY = "04"
    FRIDAY = "05"
    SATURDAY = "06"
    SUNDAY = "07"
    HOLIDAY = "08"
    UNKNOWN = "00"


def get_distance_category(distance: confloat(ge=0.0)):
    if distance <= 5.0:
        return Distance.SHORT
    elif distance <= 15.0:
        return Distance.MEDIUM
    else:
        return Distance.LONG


class Distance(str, Enum):
    SHORT = "01"  # less than 5 km
    MEDIUM = "02"  # 5 km to 15 km
    LONG = "03"  # 15 km and more
    UNKNOWN = "00"


class HomogeneousGroup(str, Enum):
    WORKING_PERSON = "01"  # less than 5 km
    NON_WORKING_PERSON = "02"  # 5 km to 15 km
    STUDENT = "03"  # includes students, apprentices and pupils
    UNKNOWN = "00"


class MobilityGroup(str, Enum):
    CAR_USER = "01"  # uses mostly cars
    MULTI_MODAL = "02"  # uses multi modal means of transport
    NON_CAR_USER = "03"  # mostly doesnt use cars
    UNKNOWN = "00"


class Purpose(int, Enum):
    WORK = 1
    BUSINESS = 2
    EDUCATION = 3
    SHOPPING = 4
    PRIVATE_EXECUTIONS = 5
    COMPANIONSHIP = 6
    LEISURE = 7
    HOME = 8
    BACK = 9
    UNKNOWN = 0


class RegionType(str, Enum):
    URBAN_METROPOLIS = "71"
    URBAN_MAJOR_CITY = "72"
    URBAN_CITY_AREA = "73"
    URBAN_VILLAGE = "74"
    RURAL_CENTRAL_CITY = "75"
    RURAL_CITY_AREA = "76"
    RURAL_VILLAGE = "77"
    UNKNOWN = "00"


class Resolution(float, Enum):
    TIME = 0.5
    DISTANCE = 5.0
    SPEED = 5.0


def get_start_category(time: nptime):
    if time.hour <= 9:
        return Start.MORNING
    elif time.hour <= 13.0:
        return Start.MIDDAY
    elif time.hour <= 16.0:
        return Start.AFTERNOON
    elif time.hour <= 23.0:
        return Start.EVENING
    else:
        return Start.UNKNOWN


class Start(str, Enum):
    MORNING = "01"  # before 10am
    MIDDAY = "02"  # 10am to 2pm
    AFTERNOON = "03"  # 2pm to 5pm
    EVENING = "04"  # 5pm to midnight
    UNKNOWN = "00"


class StartLocation(str, Enum):
    AT_HOME = "01"
    NOT_AT_HOME = "02"
    UNKNOWN = "00"


class FederalState(str, Enum):
    SCHLESWIG_HOLSTEIN = "01"
    HAMBURG = "02"
    LOWER_SAXONY = "03"
    BREMEN = "04"
    NORTH_RHINE_WESTPHALIA = "05"
    HESSE = "06"
    RHINELAND_PALATINATE = "07"
    BADEN_WUERTTEMBERG = "08"
    BAVARIA = "09"
    SAARLAND = "10"
    BERLIN = "11"
    BRANDENBURG = "12"
    MECKLENBURG_WESTERN_POMERANIA = "13"
    SAXONY = "14"
    SAXONY_ANHALT = "15"
    THURINGIA = "16"
    UNKNOWN = "00"


def get_staytime_category(time: datetime.timedelta):
    if time is None:
        return StayTime.UNKNOWN
    if time.total_seconds()/3600 <= 1.0:
        return StayTime.SHORT
    elif time.total_seconds()/3600 <= 4.0:
        return StayTime.MEDUIM
    elif time.total_seconds()/3600 <= 24.0:
        return StayTime.LONG
    else:
        return StayTime.UNKNOWN


class StayTime(str, Enum):
    SHORT = "01"  # up to one hour
    MEDUIM = "02"  # one to four hours
    LONG = "03"  # four to 24 hours
    UNKNOWN = "00"



class TripChainInput(BaseModel):
    region_type: RegionType = RegionType.UNKNOWN
    federal_state: FederalState = FederalState.UNKNOWN
    homogeneous_group: HomogeneousGroup = HomogeneousGroup.UNKNOWN
    mobility_group: MobilityGroup = MobilityGroup.UNKNOWN
    age: Age = Age.UNKNOWN
    start_location_of_first_trip: StartLocation = StartLocation.UNKNOWN
    day_type: DayType = DayType.UNKNOWN


class Trip(BaseModel):
    departure: nptime
    distance: confloat(ge=0.0)
    duration: datetime.timedelta
    mean_speed = confloat(ge=0.0)
    arrival: nptime
    purpose: Purpose
    staytime: Union[datetime.timedelta, None]
    numberInChain: int


class TripChain(BaseModel):
    length: conint(ge=0)
    purpose_chain: List[Purpose]
    trips: List[Trip]
    last_time_on_next_day: bool = False
    last_trip_arrival: nptime = None

    def sampled_trip_chain_valid(self, cluster):
        #checks, if trip chain is valid: no departure on next day. Only arrival on next day is ok
        #sets last_time_on_next_day to true if arrival of last trip is on next day
        self.last_time_on_next_day = False
        valid = True
        if self.length > 1:
            # check
            for ii in range(1, self.length+1):
                #for ij in range(ii+1, self.length+1):
                    self.last_trip_arrival = self.trips[-ii].arrival
                    # check if some entries of day before took overnight, so that plug in_start of next day is not 0 o clock
                    if self.last_trip_arrival < self.trips[-ii].departure:

                        if ii==1:
                            self.last_time_on_next_day = True
                        else:
                            #if ii>1: this means, there are other trips after this trip (this is not the last trip)
                            valid = False
                            #return
                    elif ii+1 <= self.length and self.last_trip_arrival < self.trips[-ii-1].arrival:
                        #trip ends and begins on next day
                        valid = False
                    if ii < self.length and self.trips[ii].departure<self.trips[ii-1].arrival:
                        valid = False

        elif self.length == 1:
            if self.trips[-1].arrival < self.trips[-1].departure:
                self.last_time_on_next_day = True
        if valid and self.length >=1:
            self.last_trip_arrival = self.trips[-1].arrival


        if with_cluster and not self.check_cluster_category(cluster):
            valid = False
        return valid

    def check_cluster_category(self, cluster):
        if cluster == Cluster.Cluster3:
            return True

        count_trips_to_home = 0
        for trip in self.trips:
            if get_purposes_category(trip.purpose) == ChargingStationPlace.HOME:
                count_trips_to_home +=1

        if count_trips_to_home>=2:
            return cluster == Cluster.Cluster1

        elif count_trips_to_home ==1:

            if cluster == Cluster.Cluster1:
                randn = np.random.rand()
                if randn < 0.5:
                    return True
                else:
                    return False
            elif cluster == Cluster.Cluster2:
                randn = np.random.rand()
                if randn<0.5:
                    return True
                else:
                    return False
        elif cluster == Cluster.Cluster2:
            randn = np.random.rand()
            if randn < 0.9:
                return True
            else:
                return False

        elif cluster == Cluster.Cluster1:
            #randn = np.random.rand()
            #if randn < 0.1:
             #   return True
            #else:
                return False

    def copy(self):
        tc = TripChain(length=self.length, purpose_chain=self.purpose_chain.copy(), trips=self.trips.copy(), last_time_on_next_day = self.last_time_on_next_day, last_trip_arrival = self.last_trip_arrival)
        return tc


class Cluster(str, Enum):
    Cluster1 = "many trips to home"
    Cluster2 = "few trips to home"
    Cluster3 = ""

class VariableNames(str, Enum):
    TRIP_CHAIN_LENGTH = "TripChainLength"
    PURPOSES_VALUES = "PurposesValues"
    PURPOSES = "Purposes"
    FIRST_START = "FirstStart"
    STAYTIME = "StayTime"
    DISTANCE = "Distance"
    SPEED = "Speed"


def get_purposes_category(purpose):
    if purpose == 0:
        num = np.random.randint(0, 3)
        arr = [1,8,3]
        purpose = arr[num]
    if purpose == 9:
        num = np.random.randint(0, 2)
        arr = [1,3]
        purpose = arr[num]
    if purpose == 1 or purpose == 2:
        return ChargingStationPlace.WORK
    elif purpose ==8:
        return ChargingStationPlace.HOME
    else:
        return ChargingStationPlace.PUBLIC


class ChargingStationPlace(str, Enum):
    PUBLIC = "public"
    WORK = "work"
    HOME = "home"


class EVState(str, Enum):
    DRIVING = "Driving"
    PARKING_PLUGGED_IN = "parkingPluggedIn"
    ONLY_PARKING = "OnlyParking"
    CHARGING = "Charging"


class SOCDuringDay(BaseModel):
    states = list()
    times = list()
    SOC = list()

    def __init__(self):
        super().__init__()

        start_soc = np.random.randint(70, 100)
        self.SOC.append(start_soc)
        self.states.append("ParkingPluggedIn")
        self.times.append(nptime(0, 0))


    def get_soc(self):
        return self.SOC[-1]

    def append_entry(self, state, time, soc):
        self.states.append(state)
        self.times.append(time)
        if soc < 0:
            self.SOC.append(0)
            #print(soc)
            return False
        else:
            self.SOC.append(soc)
            return True



class EconomicStatus(int, Enum):
    VERYLOW = 1
    LOW = 2
    MEDIUM = 3
    HIGH = 4
    VERYHIGH = 5
    UNKNOWN = 6


class AvailablePeriod(BaseModel):
    start_time: nptime = None # in hour, minutes (not including days <24
    end_time: nptime = None # in hour, minutes (not including days <24)
    min_SOC: float = None
    start_SOC: float = None
    charging_power: float = None
    discharging_power: float = None
    days: int = None # number of days, the available period appears
    available_time: datetime.timedelta = None # duration
    flex_time: datetime.timedelta = None    # duration of avaialable_period - time to charge obligatory energy
    home: bool = None
    work: bool = None
    day_adaption: bool = None
    day_adaption_list: list = None

    def __init__(self, starttime=nptime(0,0), endtime=nptime(0,0), min_SOC=100, start_SOC=20, charging_power=10, discharging_power=10, days=0, home = True, work = False):
        super().__init__()
        self.start_time = starttime
        self.end_time = endtime
        self.min_SOC = min_SOC
        self.start_SOC = start_SOC
        self.charging_power = charging_power
        self.discharging_power = discharging_power
        self.days = days # counts number of days the available period appears
        self.home = home
        self.work = work
        self.day_adaption = False
        self.day_adaption_list = [False for i in range(self.days+1)]

    def compute_available_time(self):
        self.available_time = self.end_time - self.start_time  # duration of available_period
        if self.available_time < datetime.timedelta(0, 0):
            # if available_time is negative, as endtime is smaller than starttime (nptime not involves day), add one day for positive number
            self.available_time = self.available_time + datetime.timedelta(days=1)
            if self.days >= 1:
                # if available period appears on several days the total duration is these number of days -1 (as end time was smaller than start time)
                # if endtime> startime (avaialbale_time was negative), then the duration days are the same like "appear days"
                available_time_days = self.days - 1
            else:
                breakpoint()
                print("Error: check_availability")
        else:
            available_time_days = self.days
        self.available_time = self.available_time + datetime.timedelta(days=available_time_days)


    def check_availability(self, ev ):
        self.compute_available_time()
        if self.min_SOC - self.start_SOC > 0:
            self.flex_time = self.available_time-ev.time_to_charge((self.min_SOC - self.start_SOC)*0.01*ev.battery_size, self.charging_power)
        else:
            self.flex_time = self.available_time

        if self.flex_time > settingsContainer.getMinFlexTime():
            return True
        else:
            return False

    #def available_period_in_time_sequence(self, start_time, end_time):
    def copy_and_change(self, start_time, new_start_SOC, old_day):
        if start_time.__class__==datetime.timedelta:
            start_time = nptime.from_timedelta(start_time)

        new_Period = AvailablePeriod(start_time, self.end_time, self.min_SOC, new_start_SOC, self.charging_power, self.discharging_power, self.days-old_day)
        return new_Period

    def change_start(self, start_time, start_SOC, day_adaption = False):
        self.start_time = start_time
        self.start_SOC = start_SOC
        self.compute_available_time()
        if day_adaption:
            self.day_adaption = True
    def  set_day_adaption(self, day_adaption):
        self.day_adaption = day_adaption

    def update_adaption_list(self, pos):
        self.day_adaption_list[pos]=True
        if sum (self.day_adaption_list)== len(self.day_adaption_list):
            self.day_adaption = False

    def set_home(self, home_new):
        self.home = home_new

    def set_work(self, work_new):
        self.work = work_new

    def set_minSOC(self, min_SOC):
        self.min_SOC = min_SOC

    def period_adaption(self, ev, start_energy):


            # start_time of available_period, when min_SOC/min_range is reached
            new_start_time = ev.time_to_charge(ev.min_energy - start_energy,
                                               self.charging_power) + self.start_time
            next_day = False
            days = 0
            if new_start_time < self.start_time:
                # new start_time on next day (assumption: charging lasts less than one day)
                next_day = True
                self.days -=1
                days = 1

            old_start_time = self.start_time
            old_start_SOC = self.start_SOC

            # adapt start_SOC correspondingly
            new_start_SOC = (ev.min_energy / ev.battery_size) * 100 +1e-13
            self.change_start(new_start_time, new_start_SOC)

            # add charging to min_range/SOC to fix_charging_periods

            return next_day, AvailablePeriod(starttime=old_start_time, endtime=new_start_time, min_SOC=self.min_SOC,
                                   start_SOC=old_start_SOC, charging_power=self.charging_power,
                                   discharging_power=self.discharging_power, days=days, home = self.home, work = self.work)

    def same_available_period(self, available_period):
        if self.available_time!= available_period.available_time or self.start_time != available_period.start_time or (
            self.end_time != available_period.end_time or self.days != available_period.days or
                self.min_SOC != available_period.min_SOC or self.start_SOC != available_period.start_SOC):
            return False
        else:
            return True







##flexibility_calc variables


# saving List
def save_list(list, filename='myList'):
    with open(filename +'.pkl', 'wb') as f:
        pickle.dump(list, f)


def open_file(name):
    with open(name+'.pkl', 'rb') as f:
        mynewlist = pickle.load(f)
    print("file loaded")
    return mynewlist


def delta_to_nptime(time):
    time = time - datetime.timedelta(days = time.days)
    in_seconds = time.total_seconds()
    hours = in_seconds/3600
    minutes = hours/60
    seconds = minutes/60
    microseconds = seconds/1000000
    return nptime(hour = int(hours), minute = int(minutes), second = int(seconds), microsecond=int(microseconds))


def compute_day_list(DayType, start_daytype, Number_of_days, ignore_first_days=1):
    # list, which days to compute spontanflex of
    if DayType <= 0:

        Days = [i for i in range(ignore_first_days,Number_of_days)]
    elif DayType > 0 and DayType < 8:
        start = 0
        current_type = start_daytype
        while current_type != DayType:
            start += 1
            current_type += 1
            if current_type > 7:
                current_type = 1
        Days = list()#[7 * i + start for i in range(int(Number_of_days / 7)+1)]
        for i in range(int(Number_of_days/7)):
            if 7*i +start > ignore_first_days:
                Days.append(7*i +start)

    else:
        print("Error: wrong daytype, insert value between -1,0 = Unknown, 1 = Monday, 2 = Tuesday,7 = Sunday...")
        return
    return Days




def calculate_end_at_home_bool(Daytype):
    #probabilities from page 83 (schlund Doktorarbeit)
    if int(Daytype)==1 or int(Daytype)==3 or int(Daytype)==7:
        p = 0.026
    elif int(Daytype)==2:
        p = 0.027
    elif int(Daytype)==4:
        p = 0.031
    elif int(Daytype)==5:
        p = 0.05
    elif int(Daytype)==6:
        p = 0.105
    #if random number larger than p, then trip should end at home
    return np.random.rand()>p
