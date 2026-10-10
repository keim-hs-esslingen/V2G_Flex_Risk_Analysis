import csv
import os

from helper_files.import_packages import *


class ChargingStation(BaseModel):
    Place: ChargingStationPlace = None
    availability: int = 100  # in percent
    power: float = None
    ac: bool = None
    discharge_power: float = None

    def __init__(self, power, ac, place, availability=100):
        super().__init__()
        self.power = power
        self.Place = place
        self.ac = ac
        self.availability = availability
        # possible ToDo: not the same for charging and discharging power
        self.discharge_power = self.power


class ChargingStationTypesProbability(BaseModel):
    # This class reads charging station types from the corresponding file.
    # This file contains in each row charging stations with different charging powers
    # and the probability of the appearance of these chargingStation types in home/work (2nd column) or in public areas.
    power_list: list = None
    ac_list: list = None
    probs_public = list()
    probs_home = list()
    probs_work = list()

    def __init__(self, filepath = "SimulationTool/ChargingStationTypes.csv", *args, **kwargs):
        # reading file and append each row to list of local attribute types
        # possible ToDo:  if there is no file, assign default values
        #  (or assign types not with file, but with manual input)
        # -->dependant of implementation with angular and user interaction before simulation
        super().__init__(**kwargs)
        if filepath is None:
            filepath = "SimulationTool/ChargingStationTypes.csv"
        self.power_list = list()
        self.ac_list = list()
        self.probs_public = list()
        self.probs_home = list()
        self.probs_work = list()
        with open(os.path.join(filepath)) as file:
            csv_reader = csv.reader(file, delimiter=';')
            for row in csv_reader:
                without_number = row[1][1:-1].split(', ')
                self.probs_public.append(without_number[4])
                self.probs_home.append(without_number[2])
                self.probs_work.append(without_number[3])
                self.power_list.append(without_number[0])
                self.ac_list.append(without_number[1])

    def assign_charging_station(self, charging_station_place):
        # gets a ChargingStation place and returns a chargingStation choosing a type according the given probabilities
        if charging_station_place == ChargingStationPlace.HOME:
            # returns charging Station belonging to home of user
            cs_num = np.random.choice(range(0, len(self.power_list)), p=self.probs_home)
            return ChargingStation(float(self.power_list[cs_num]), self.ac_list[cs_num], charging_station_place)
        elif charging_station_place == ChargingStationPlace.WORK:
            # returns charging Station belonging to home of user
            cs_num = np.random.choice(range(0, len(self.power_list)), p=self.probs_work)
            return ChargingStation(float(self.power_list[cs_num]), self.ac_list[cs_num], charging_station_place)
        elif charging_station_place == ChargingStationPlace.PUBLIC:
            cs_num = np.random.choice(range(0, len(self.power_list)), p=self.probs_public)
            return ChargingStation(float(self.power_list[cs_num]), self.ac_list[cs_num], charging_station_place)


class EVUser(BaseModel):
    # trip chain characteristics
    region_type: RegionType = RegionType.UNKNOWN
    federal_state: FederalState = FederalState.UNKNOWN
    homogeneous_group: HomogeneousGroup = HomogeneousGroup.UNKNOWN
    mobility_group: MobilityGroup = MobilityGroup.UNKNOWN
    age: Age = Age.UNKNOWN
    start_location_of_first_trip: StartLocation = StartLocation.UNKNOWN
    plug_in_alphas: list = None
    charge_every_day_on_evening: bool = None


    ev_id: int = None
    economic_status: EconomicStatus = None
    sampled_trip_chain: TripChain = None
    next_trip_chain: TripChain = None
    # idea: Trip chain should contain car_id list: for each trip, car id, which car is used
    fix_working_distance: confloat(ge=settingsContainer.getMinimumDistance()) = None  # fix_working_distance mit wertebereich ab ge=...)

    ID: int = None
    ChargingStation: ChargingStation = None
    ChargingStation_work: ChargingStation = None
    # EV: EV = None  # later, as array: if more than on ev per user is possible
    cluster: Cluster = None
    range: float = None

    def __init__(self, user_id, economic_status=None, working_distance=None, charge_every_day=False, rangee = 200,  *args, **kwargs):
        super().__init__(**kwargs)
        self.ID = user_id
        if economic_status == None:
            self.economic_status = EconomicStatus(random.randint(1, 5)) #als default in methode ging nicht
        else:
            self.economic_status = economic_status
        self.fix_working_distance = working_distance
        self.plug_in_alphas = list()
        self.charge_every_day_on_evening = charge_every_day
        for alpha in [settingsContainer.getPlugInAlphaHome(),settingsContainer.getPlugInAlphaWork(), settingsContainer.getPlugInAlphaPublic()]:

            if alpha.__class__ == list:
                if len(alpha)== 2:

                    self.plug_in_alphas.append(normal_range(alpha[0], alpha[1]))
                elif len(alpha)==1:
                    self.plug_in_alphas.append(alpha[0])
            else:
                self.plug_in_alphas.append(alpha)
        self.range = rangee

    def set_cluster(self, cluster):
        self.cluster = cluster

    def set_charging_station(self, Charging_Station):
        self.ChargingStation = Charging_Station

    def set_charging_station_work(self, Charging_Station):
        self.ChargingStation_work = Charging_Station


    def set_working_distance(self, value: confloat(ge=settingsContainer.getMinimumDistance())):
        self.fix_working_distance = value

    def set_economic_status(self, value: EconomicStatus):
        self.economic_status = value

    def set_range(self, rangee):
        self.range = rangee

    def set_plugin_alphas(self, alphas):
        self.plug_in_alphas = alphas

    def plug_in_decision_simple(self, current_trip):

        # simple version:

        plug_in_start = self.sampled_trip_chain.trips[current_trip.numberInChain].arrival


        return plug_in_start

    def plug_in_decision_complex(self, current_SOC, need_SOC, chstation_place, current_trip, alpha = None):

        if alpha == None:
            if chstation_place == "home":
                alpha = self.plug_in_alphas[0]
            elif chstation_place == "work":
                alpha = self.plug_in_alphas[1]
            elif chstation_place == "public":
                alpha = self.plug_in_alphas[2]
        # else: alpha is given as parameter: for adaptions in plug-in behaviour:
        # --> no/less/more/always plug-ins in certain situations, for example for short durations, less plug-in porbability

        if current_SOC <= need_SOC:
            return self.sampled_trip_chain.trips[current_trip.numberInChain].arrival
        else:
            p = 1 - pow(((current_SOC - need_SOC) / (100 - need_SOC)), alpha)
            # if alpha == 0 (e. g if user has no access to charging station at work), p = 0 as well --> return False
            if np.random.rand() < p:
                return self.sampled_trip_chain.trips[current_trip.numberInChain].arrival
            else:
                return -1

    def set_trip_chain(self, trip_chain, next = False):
        if next:
            self.next_trip_chain = trip_chain
        else:
            self.sampled_trip_chain = trip_chain


class ChargingSession:
    start: datetime.timedelta = None
    end: datetime.timedelta = None
    soc_after_charging: float = None
    soc_before_charging: float = None
    station: ChargingStation = None

    rate: float = None

    def __init__(self, start, end, soc_after_charging, soc_before_charging, station, rate, *args, **kwargs):
        super().__init__(**kwargs)
        self.start = start
        self.end = end
        self.soc_after_charging = soc_after_charging
        self.soc_before_charging = soc_before_charging
        self.station = station
        self.rate = rate

    def compute_charged_energy(self, Vehicle):
        return Vehicle.charge(self.end -self.start, self.rate)
