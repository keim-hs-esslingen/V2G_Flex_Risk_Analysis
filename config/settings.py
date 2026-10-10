import datetime
import json
import csv
import os
#from config.evModelSettings import EVModelSettings
#from config.chargingStationTypesSettings import ChargingsStationTypesSettings
#from config.populateUserSettings import PopulateUserSettings


POPULATE_USERS_CSV_PATH = os.path.join(
    "SimulationTool", "PopulateUsers_working09.csv"
)

def set_populate_users_csv_path(path: str):
    global POPULATE_USERS_CSV_PATH
    POPULATE_USERS_CSV_PATH = path


class _SettingsContainer():
    # model settings
    def __init__(self):
        #self.evModel = EVModelSettings()
        #self.chargingStationTypes = ChargingsStationTypesSettings()
        self.userInteractionSimulation = False
        self.userInteractionSimRanges = [50, 100, 200, 250]
        self.userInteractionSimRangeShares = [0.3, 0.7,0.9, 1]
        #self.populateUser = PopulateUserSettings()


        # trip-generation
        self.MINIMUM_SPEED: float = 20.0#20.0  # km/h ##
        self.MINIMUM_DISTANCE: float = 0.5  # km
        self.ENERGY_CONSUMPTION: str = "constant in range"

        # user
        self.USER_CLUSTER1_SHARE: float = 0.3  # 0.25
        self.USER_CLUSTER2_SHARE: float = 0.5
        self.WITH_CLUSTER: bool = False

        # charging
        self.CPCV: bool = False

        # plug-in
        self.PLUG_IN_ALPHA_PUBLIC: list = [0.4] ##
        self.PLUG_IN_ALPHA_WORK: list = [0.3, 0.6] ##
        self.PLUG_IN_ALPHA_HOME: list = [1.4,1.8]  # für Uniform ##
        self.PLUG_IN_SIMPLE: bool = False ##
        self.MIN_SOC_AFTER_LAST_TRIP: int = 50
        self.MIN_SOC_AFTER_LAST_TRIP_ACTIVE: bool = True
        self.MIN_SOC_PLUG_IN: int = 60
        self.WITHOUT_WORKING_STATION_ACCESS: float = 0
        self.CHARGING_EVERY_DAY_AFTER_LAST_TRIP: float = 0  # 0.5 ##

        # model_specifications
        self.NUMBER_OF_DAYS: int = 25 ##
        self.NUMBER_OF_USERS: int = 100 ##
        self.NUMBER_OF_RUNS: int = 5 ##
        self.START_DAY: str = "01"

        # flexibility_calculation
        self.MIN_FLEX_TIME: datetime.timedelta = datetime.timedelta(minutes=30)
        self.MIN_SOC: int = 60 ##
        self.SOC_TOL: int = 10
        self.MAX_SOC: int = 95
        self.MIN_CHARGING_RATE: float = 0  # 2.3
        self.CHARGING_STRATEGIES: list = ["as soon as possible", "as late as possible", "as long as possible with minimum rate"] ##
        self.HEURISTICS: list = ["max at start", "as long as possible with minimum rate"] ##
        self.MIN_DELIEVERY_TIME: datetime.timedelta = datetime.timedelta(0)  # datetime.timedelta(minutes=2) # this time has to be delievered at least during flexibility_calc delievery periods
        self.SIMPLE_BOUNDARIES: bool = True
        self.V2G_AVAILABILITY: int = 100  # Factor, between 0 and 100: how much percent of population take part on V2G: # if factor = 50: --> available vehicles take part on V2G with 50 % probability

        # flexibility_calc calculation specifications
        self.SPONTAN_FLEX: bool =  True

        self.FLEX_START_TIME: datetime.timedelta = datetime.timedelta(hours = 0)
        self.FLEX_DURATION: datetime.timedelta = datetime.timedelta(minutes = 15)
        self.FLEX_ACTIVATION_TIME: datetime.timedelta = datetime.timedelta(hours = 5)
        self.FLEX_PLACE: str = "Home"
        self.RISK: bool = True
        self.FLEX_AT_NUMBER_OF_DAY: int = -1
        self.FLEX_AT_NUMBER_OF_RUN: int = 0
        self.FLEX_AT_DAYTYPE: int = 0
        self.FLEX_DEPENDANT: bool = False

        # flexibility_calc visualization specifications
        self.VIZ_CHARGING_STRATEGIES: list = [0]
        self.VIZ_HEURISTICS: int = 0
        self.VIZ_MODUS: int = 0
        self.VIZ_SHOW: bool = True
        self.VIZ_SAVE: bool = False
        self.VIZ_FILENAME: str = "img/flexibility_calc"

    def getMinimumSpeed(self): return self.MINIMUM_SPEED



    def setMinimumSpeed(self, element: float): self.MINIMUM_SPEED = element

    def getUserInteractionSimulation(self):
        return self.userInteractionSimulation
    def setUserInteractionSimulation(self, element: bool): self.userInteractionSimulation = element

    def getUserInteractionSimRanges(self):
        return self.userInteractionSimRanges

    def setUserInteractionSimRanges(self, element: list): self.userInteractionSimRanges = element

    def setUserInteractionSimRangeShares(self, element: list): self.userInteractionSimRangeShares = element


    def getUserInteractionSimRangeShares(self): return self.userInteractionSimRangeShares


    def getStartDay(self): return self.START_DAY

    def setStartDay(self, element: str): self.START_DAY = element


    def getMinimumDistance(self): return self.MINIMUM_DISTANCE
    def setMinimumDistance(self, element: float): self.MINIMUM_DISTANCE = element

    def getEnergyConsmuption(self): return self.ENERGY_CONSUMPTION
    def setEnergyConsmuption(self, element: str):
        self.ENERGY_CONSUMPTION = element


    def getUserCluster1Share(self): return self.USER_CLUSTER1_SHARE
    def setUserCluster1Share(self, element: float): self.USER_CLUSTER1_SHARE = element

    def getUserCluster2Share(self): return self.USER_CLUSTER2_SHARE
    def setUserCluster2Share(self, element: float): self.USER_CLUSTER2_SHARE = element

    def getWithCluster(self): return self.WITH_CLUSTER
    def setWithCluster(self, element: bool): self.WITH_CLUSTER = element

    def getCPCV(self): return self.CPCV
    def setCPCV(self, element: bool): self.CPCV = element

    def getWithoutWorkingStationAccess(self): return self.WITHOUT_WORKING_STATION_ACCESS
    def setWithoutWorkingStationAccess(self, element: float): self.WITHOUT_WORKING_STATION_ACCESS = element

    def getChargingEveryDayAfterLastTrip(self): return self.CHARGING_EVERY_DAY_AFTER_LAST_TRIP
    def setChargingEveryDayAfterLastTrip(self, element: float): self.CHARGING_EVERY_DAY_AFTER_LAST_TRIP = element

    def getPlugInAlphaPublic(self): return self.PLUG_IN_ALPHA_PUBLIC
    def setPlugInAlphaPublic(self, element: list):
        self.PLUG_IN_ALPHA_PUBLIC = element

    def getPlugInAlphaWork(self): return self.PLUG_IN_ALPHA_WORK
    def setPlugInAlphaWork(self, element: list):
        self.PLUG_IN_ALPHA_WORK = element

    def getPlugInAlphaHome(self): return self.PLUG_IN_ALPHA_HOME
    def setPlugInAlphaHome(self, element: list):
        self.PLUG_IN_ALPHA_HOME = element

    def getPlugInSimple(self): return self.PLUG_IN_SIMPLE
    def setPlugInSimple(self, element: bool): self.PLUG_IN_SIMPLE = element

    def getMinSocAfterLastTrip(self): return self.MIN_SOC_AFTER_LAST_TRIP
    def setMinSocAfterLastTrip(self, element: int):
        self.MIN_SOC_AFTER_LAST_TRIP = element


    def getMinSocAfterLastTripActive(self): return self.MIN_SOC_AFTER_LAST_TRIP_ACTIVE
    def setMinSocAfterLastTripActive(self, element: bool): self.MIN_SOC_AFTER_LAST_TRIP_ACTIVE = element

    def getMinSocPlugIn(self): return self.MIN_SOC_PLUG_IN

    def setMinSocPlugIn(self, element: int):
        self.MIN_SOC_PLUG_IN = element

    def getNumberOfDays(self): return self.NUMBER_OF_DAYS
    def setNumberOfDays(self, element: int):
        self.NUMBER_OF_DAYS = element


    def getNumberOfUsers(self): return self.NUMBER_OF_USERS
    def setNumberOfUsers(self, element: int):
        self.NUMBER_OF_USERS = element

    def getNumberOfRuns(self): return self.NUMBER_OF_RUNS
    def setNumberOfRuns(self, element: int):
        self.NUMBER_OF_RUNS = element


    def getMinFlexTime(self): return self.MIN_FLEX_TIME
    def setMinFlexTime(self, element: datetime):
        if element.__class__ == datetime.timedelta:
            self.MIN_FLEX_TIME = element
        else:
            self.MIN_FLEX_TIME = datetime.timedelta(minutes=element)


    def getMinSoc(self): return self.MIN_SOC
    def setMinSoc(self, element: int):
        self.MIN_SOC = element

    def getSocTol(self): return self.SOC_TOL
    def setSocTol(self, element: int):
        self.SOC_TOL = element


    def getMaxSoc(self): return self.MAX_SOC
    def setMaxSoc(self, element: int):
        self.MAX_SOC = element

    def getMinChargingRate(self): return self.MIN_CHARGING_RATE
    def setMinChargingRate(self, element: float):
        self.MIN_CHARGING_RATE = element

    def getChargingStrategies(self): return self.CHARGING_STRATEGIES
    def setChargingStrategies(self, element: list):
       self.CHARGING_STRATEGIES = element

    def getHeuristics(self): return self.HEURISTICS
    def setHeuristics(self, element: list):
       self.HEURISTICS = element

    def getMinDeliveryTime(self): return self.MIN_DELIEVERY_TIME
    def setMinDeliveryTime(self, element: datetime):
        if element.__class__ == datetime.timedelta:
            self.MIN_DELIEVERY_TIME = element
        else:
            self.MIN_DELIEVERY_TIME = datetime.timedelta(minutes=element)

    def getSimpleBoundaries(self): return self.SIMPLE_BOUNDARIES
    def setSimpleBoundaries(self, element: bool): self.SIMPLE_BOUNDARIES = element

    def getV2GAvailability(self): return self.V2G_AVAILABILITY
    def setV2GAvailability(self, element: int): self.V2G_AVAILABILITY = element


    # flexibility_calc specifications
    def getSpontanflex(self): return self.SPONTAN_FLEX

    def setSpontanflex(self, element: bool): self.SPONTAN_FLEX = element

    def getRisk(self): return self.RISK

    def setRisk(self, element: bool): self.RISK = element

    def getFlexStartTime(self): return self.FLEX_START_TIME

    def setFlexStartTime(self, element: datetime):
        if element.__class__ == datetime.timedelta:
            self.FLEX_START_TIME = element
        else:
            self.FLEX_START_TIME = datetime.timedelta(hours = element)


    def getFlexDuration(self): return self.FLEX_DURATION

    def setFlexDuration(self, element: datetime):
        if element.__class__ == datetime.timedelta:
            self.FLEX_DURATION = element
        else:
            self.FLEX_DURATION = datetime.timedelta(minutes=element)



    def getFlexActivationTime(self): return self.FLEX_ACTIVATION_TIME

    def setFlexActivationTime(self, element: datetime):

        if element.__class__ == datetime.timedelta:
            self.FLEX_ACTIVATION_TIME = element
        else:
            self.FLEX_ACTIVATION_TIME = datetime.timedelta(hours=element)


    def getFlexPlace(self): return self.FLEX_PLACE

    def setFlexPlace(self, element: str): self.FLEX_PLACE = element

    def getFlexAtNumberOfDay(self): return self.FLEX_AT_NUMBER_OF_DAY

    def setFlexAtNumberOfDay(self, element: int):
        self.FLEX_AT_NUMBER_OF_DAY = element

    def setFlexDependant(self, element: bool):
        self.FLEX_DEPENDANT = element

    def getFlexDependant(self): return self.FLEX_DEPENDANT

    def getFlexAtNumberOfRun(self): return self.FLEX_AT_NUMBER_OF_RUN

    def setFlexAtNumberOfRun(self, element: int):
        self.FLEX_AT_NUMBER_OF_RUN = element


    def getFlexAtDaytype(self): return self.FLEX_AT_DAYTYPE

    def setFlexAtDaytype(self, element: int):
        self.FLEX_AT_DAYTYPE = element


    # visualization specifications
    def getVisChargingStrategies(self): return self.VIZ_CHARGING_STRATEGIES

    def setVisChargingStrategies(self, element: list):
        self.VIZ_CHARGING_STRATEGIES = element

    def getVisHeuristics(self): return self.VIZ_HEURISTICS

    def setVisHeuristics(self, element: int):
        self.VIZ_HEURISTICS = element

    def getVisModus(self): return self.VIZ_MODUS

    def setVisModus(self, element: int):
        self.VIZ_MODUS = element

    def getVisShow(self): return self.VIZ_SHOW

    def setVisShow(self, element: bool):
       self.VIZ_SHOW = element

    def getVisSave(self): return self.VIZ_SAVE

    def setVisSave(self, element: bool):
        self.VIZ_SAVE = element

    def getVisFilename(self): return self.VIZ_FILENAME

    def setVisFilename(self, element: str):
        self.VIZ_FILENAME = element

    def updateSettings(self, _json, as_dict = False):
        if as_dict:
            _settings = _json
        else:
            _settings = json.loads(_json)

        categories = ["trip-generation", "user", "charging", "plug-in", "model_specifications", "flexibility_calculation", "flexibility_specifications", "viz_flexibility_specifications"]

        for category in categories:
            self.parseCategory(category, _settings)
        self.check_settings()

    def check_settings(self):
        #number of run < Number_of_Runs
        if self.getMinSoc() >= self.getMaxSoc():
            print("Min SOC larger than Max SOC")
            print("values resetted to default values")
            self.setMinSoc(40)
            self.setMaxSoc(95)
        # possible Todo: min charging rate smaller than smallest charging power of charging stations
        if self.getNumberOfDays() * self.getNumberOfRuns() * self.getNumberOfUsers() >= 1000000:
            print("Calculation could last very long")
        if self.FLEX_AT_NUMBER_OF_RUN >= self.getNumberOfRuns():
            print(str(self.FLEX_AT_NUMBER_OF_RUN) + " resetted, as it was too large")

    def parseCategory(self, _category, _settings):
        #Set Common Settings
        for category in _settings:
            if (category == _category):
                #print("_category", _category, _settings[category])
                if (_settings[category]):
                    #print("yes")
                    for key in _settings[category]:
                        # Skip None values to avoid TypeError in setSettingValue when comparisons are made
                        value = _settings[category][key]
                        if value is None:
                            # don't attempt to set settings that were not provided
                            continue
                        #print("Set " + _category +  " Setting: ", key, " = ", _settings[category][key])
                        self.setSettingValue(key, value)
                #else:
                    #print("no")

    def setSettingValue(self, key, value):
        match key:
            case "MINIMUM_SPEED":
                if value > 10 and value < 100:
                    self.setMinimumSpeed(value)
                else:
                    print("value for" + key + "not in feasible value range")
                    print("value set to default value: " + str(self.getMinimumSpeed()))

            case "MINIMUM_DISTANCE":
                if value >= 0 and value < 100:
                    self.setMinimumDistance(value)
                else:
                    print("value for" + key + "not in feasible value range")
                    print("value set to default value: " + str(self.getMinimumDistance()))

            case "ENERGY_CONSUMPTION":
                if value == "constant" or value == "constant in range":
                    self.setEnergyConsmuption(value)
                else:
                    print("value for" + key + "not in feasible value range")
                    print("value set to default value: " + str(self.getEnergyConsmuption()))

            case "USER_CLUSTER1_SHARE":
                if value <1 and value >=0:
                    self.setUserCluster1Share(value)
                else:
                    print("value for" + key + "not in feasible value range")
                    print("value set to default value: " + str(self.getUserCluster1Share()))

            case "USER_CLUSTER2_SHARE":
                if value < 1 and value >= 0:
                    self.setUserCluster2Share(value)
                else:
                    print("value for" + key + "not in feasible value range")
                    print("value set to default value: " + str(self.getUserCluster2Share()))

            case "WITH_CLUSTER": self.setWithCluster(value)
            case "CPCV": self.setCPCV(value)
            case "WITHOUT_WORKING_STATION_ACCESS":
                if value < 1 and value >= 0:
                    self.setWithoutWorkingStationAccess(value)
                else:
                    print("value for" + key + "not in feasible value range")
                    print("value set to default value: " + str(self.getWithoutWorkingStationAccess()))

            case "CHARGING_EVERY_DAY_AFTER_LAST_TRIP":
                if value <= 1 and value >= 0:
                    self.setChargingEveryDayAfterLastTrip(value)
                else:
                    print("value for" + key + "not in feasible value range")
                    print("value set to default value: " + str(self.getChargingEveryDayAfterLastTrip()))

            case "PLUG_IN_ALPHA_PUBLIC":
                value_ok = True
                for value_ in value:
                    if value_ < 0:
                        value_ok = False
                        break
                if value_ok:
                    self.setPlugInAlphaPublic(value)
                else:
                    print("value for" + key + "not in feasible value range")
                    print("value set to default value: " + str(self.getPlugInAlphaPublic()))
            case "PLUG_IN_ALPHA_WORK":
                value_ok = True
                for value_ in value:
                    if value_ < 0:
                        value_ok = False
                        break
                if value_ok:
                    self.setPlugInAlphaWork(value)
                else:
                    print("value for" + key + "not in feasible value range")
                    print("value set to default value: " + str(self.getPlugInAlphaWork()))

            case "PLUG_IN_ALPHA_HOME":
                value_ok = True
                for value_ in value:
                    if value_ < 0:
                        value_ok = False
                        break
                if value_ok:
                    self.setPlugInAlphaHome(value)
                else:
                    print("value for" + key + "not in feasible value range")
                    print("value set to default value: " + str(self.getPlugInAlphaHome()))

            case "PLUG_IN_SIMPLE": self.setPlugInSimple(value)

            case "MIN_SOC_AFTER_LAST_TRIP_ACTIVE": self.setMinSocAfterLastTripActive(value)

            case "MIN_SOC_AFTER_LAST_TRIP":
                if value <= 100 and value >= 0:
                    self.setMinSocAfterLastTrip(value)
                else:
                    print("value for" + key + "not in feasible value range")
                    print("value set to default value: " + str(self.getMinSocAfterLastTrip()))

            case "MIN_SOC_PLUG_IN":
                if value <= 100 and value >= 0:
                    self.setMinSocPlugIn(value)
                else:
                    print("value for" + key + "not in feasible value range")
                    print("value set to default value: " + str(self.getMinSocPlugIn()))

            case "NUMBER_OF_DAYS":
                if value <= 5000 and value >= 1:
                    self.setNumberOfDays(value)
                else:
                    print("value for" + key + "not in feasible value range")
                    print("value set to default value: " + str(self.getNumberOfDays()))

            case "NUMBER_OF_USERS":
                if value <= 5000 and value >= 1:
                    self.setNumberOfUsers(value)
                else:
                    print("value for" + key + "not in feasible value range")
                    print("value set to default value: " + str(self.getNumberOfUsers()))

            case "NUMBER_OF_RUNS":
                if value <= 5000 and value >= 1:
                    self.setNumberOfRuns(value)
                else:
                    print("value for" + key + "not in feasible value range")
                    print("value set to default value: " + str(self.getNumberOfRuns()))

            case "START_DAY":
                value_ = int(value)
                if value_ <= 8 and value_ >= 0:
                    self.setStartDay(value)
                else:
                    print("value for" + key + "not in feasible value range")
                    print("value set to default value: " + str(self.getStartDay()))

            case "MIN_FLEX_TIME":
                if value.__class__ == datetime.timedelta:
                    cmp_value1 = datetime.timedelta(minutes = 720)
                    cmp_value2 = datetime.timedelta(minutes = 0)
                else:
                    cmp_value1 = 720
                    cmp_value2 = 0
                if value <= cmp_value1  and value >= cmp_value2 :
                    self.setMinFlexTime(value)
                else:
                    print("value for" + key + "not in feasible value range")
                    print("value set to default value: " + str(self.getMinFlexTime()))

            case "MIN_SOC":
                if value <= 80 and value >= 0:
                    self.setMinSoc(value)
                else:
                    print("value for" + key + "not in feasible value range")
                    print("value set to default value: " + str(self.getMinSoc()))

            case "SOC_TOL":
                if value <= 50 and value >= 0:
                    self.setSocTol(value)
                else:
                    print("value for" + key + "not in feasible value range")
                    print("value set to default value: " + str(self.getSocTol()))

            case "MAX_SOC":
                if value <= 100 and value >= 80:
                    self.setMaxSoc(value)
                else:
                    print("value for" + key + "not in feasible value range")
                    print("value set to default value: " + str(self.getMaxSoc()))

            case "MIN_CHARGING_RATE":
                if value <= 3.7 and value >= 0:
                    self.setMinChargingRate(value)
                else:
                    print("value for" + key + "not in feasible value range")
                    print("value set to default value: " + str(self.getMinChargingRate()))

            case "CHARGING_STRATEGIES":
                values_ok = True
                for value_ in value:
                    if value_ != "as soon as possible" and value_ != "as late as possible" and value_ != "as long as possible with minimum rate":
                        values_ok = False
                        break
                if values_ok:
                    self.setChargingStrategies(value)
                else:
                    print("value for" + key + "not in feasible value range")
                    print(value)
                    print("value set to default value: " + str(self.getChargingStrategies()))

            case "HEURISTICS":
                values_ok = True
                for value_ in value:
                    if value_ != "max at start" and value_ != "as long as possible with minimum rate":
                        values_ok = False
                        break
                if values_ok:
                    self.setHeuristics(value)
                else:
                    print("value for" + key + "not in feasible value range")
                    print("value set to default value: " + str(self.getHeuristics()))

            case "MIN_DELIEVERY_TIME":
                if value.__class__ == datetime.timedelta:
                    cmp_value1 = datetime.timedelta(minutes = 30)
                    cmp_value2 = datetime.timedelta(minutes = 0)
                else:
                    cmp_value1 = 30
                    cmp_value2 = 0
                if value <= cmp_value1 and value >= cmp_value2:
                    self.setMinDeliveryTime(value)
                else:
                    print("value for" + key + "not in feasible value range")
                    print("value set to default value: " + str(self.getMinDeliveryTime()))

            case "SIMPLE_BOUNDARIES": self.setSimpleBoundaries(value)

            case "V2G_AVAILABILITY": self.setV2GAvailability(value)

            case "SPONTANFLEX": self.setSpontanflex(value)
            case "RISK": self.setRisk(value)
            case "FLEX_START_TIME":
                if value.__class__ == datetime.timedelta:
                    cmp_value1 = datetime.timedelta(hours = 24)
                    cmp_value2 = datetime.timedelta(minutes=0)
                else:
                    cmp_value1 = 24
                    cmp_value2 = 0
                if  value < cmp_value2 or value >= cmp_value1:
                    self.setFlexStartTime(datetime.timedelta(0))
                    print("value for" + key + "not in feasible value range")
                    print("value set to default value: " + str(self.getFlexStartTime()))
                else:
                    self.setFlexStartTime(value)

            case "FLEX_DURATION":
                if value.__class__ == datetime.timedelta:
                    cmp_value1 = datetime.timedelta(minutes=720)
                    cmp_value2 = datetime.timedelta(minutes=0)
                else:
                    cmp_value1 = 720
                    cmp_value2 = 0
                if value < cmp_value2 or value > cmp_value1:
                    self.setFlexDuration(datetime.timedelta(minutes = 10))
                    print("value for" + key + "not in feasible value range")
                    print("value set to default value: " + str(self.getFlexDuration()))
                else:
                    self.setFlexDuration(value)
            case "FLEX_ACTIVATION_TIME":
                if value.__class__ == datetime.timedelta:
                    cmp_value1 = datetime.timedelta(hours=48)
                    cmp_value2 = datetime.timedelta(minutes=0)
                else:
                    cmp_value1 = 48
                    cmp_value2 = 0
                if value < cmp_value2 or value > cmp_value1:
                    self.setFlexActivationTime(datetime.timedelta(hours = 4))
                    print("value for" + key + "not in feasible value range")
                    print("value set to default value: " + str(self.getFlexActivationTime()))
                else:
                    self.setFlexActivationTime(value)
            case "FLEX_PLACE": self.setFlexPlace(value)
            case "FLEX_AT_NUMBER_OF_DAY":
                if value > 7:
                    print("value for" + key + "not in feasible value range")
                    print("value set to default value: " + str(self.getFlexAtNumberOfDay()))
                else:
                    self.setFlexAtNumberOfDay(value)
            case "FLEX_AT_NUMBER_OF_RUN":
                if value >= self.getNumberOfRuns():
                    print("value for" + key + "not in feasible value range")
                    print("value set to default value: " + str(self.getFlexAtNumberOfRun()))
                else:
                    self.setFlexAtNumberOfRun(value)

            case "FLEX_DEPENDANT":
                self.setFlexDependant(value)
            case "FLEX_AT_DAYTYPE":
                if value > 7:
                    print("value for" + key + "not in feasible value range")
                    print("value set to default value: " + str(self.getFlexAtDaytype()))
                else:
                    self.setFlexAtDaytype(value)
            case "VIZ_CHARGING_STRATEGIES":
                values_ok = True
                for value_ in value:
                    if value_ != 0 and value_ != 1 and value_ != 2:
                        values_ok = False
                        break
                if values_ok:
                    self.setVisChargingStrategies(value)
                else:
                    print("value for" + key + "not in feasible value range")
                    print("value set to default value: " + str(self.getVisChargingStrategies()))
            case "VIZ_HEURISTICS":
                if value != 1 and value != 0:
                    print("value for " + key + "not in feasible value range")
                    print("value set to default value: " + str(self.getVisHeuristics()))
                else:
                    self.setVisHeuristics(value)
            case "VIZ_MODUS":
                if value != 1 and value != 0:
                    print("value for" + key + "not in feasible value range")
                    print("value set to default value: " + str(self.getVisModus()))
                else:
                    self.setVisModus(value)
            case "VIZ_SHOW": self.setVisShow(value)
            case "VIZ_SAVE": self.setVisSave(value)
            case "VIZ_FILENAME": self.setVisFilename(value)
            case "USER_INTERACTION_SIMULATION": self.setUserInteractionSimulation(value)
            case "USER_INTERACTION_SIM_RANGE_SHARES": self.setUserInteractionSimRangeShares(value)
            case "USER_INTERACTION_SIM_RANGES": self.setUserInteractionSimRanges(value)

        pass

    def getSettingsAsJson(self):
        json = {
            "trip-generation":{
                "MINIMUM_SPEED": self.getMinimumSpeed(),
                "MINIMUM_DISTANCE": self.getMinimumDistance(),
                "ENERGY_CONSUMPTION": self.getEnergyConsmuption(),
            },
            "user":{
                "USER_CLUSTER1_SHARE": self.getUserCluster1Share(),
                "USER_CLUSTER2_SHARE": self.getUserCluster2Share(),
                "WITH_CLUSTER": self.getWithCluster(),

            },
            "plug-in":{
                "PLUG_IN_SIMPLE": self.getPlugInSimple(),
                "PLUG_IN_ALPHA_PUBLIC": self.getPlugInAlphaPublic(),
                "PLUG_IN_ALPHA_WORK": self.getPlugInAlphaWork(),
                "PLUG_IN_ALPHA_HOME": self.getPlugInAlphaHome(),
                "MIN_SOC_AFTER_LAST_TRIP_ACTIVE": self.getMinSocAfterLastTripActive(),
                "MIN_SOC_AFTER_LAST_TRIP": self.getMinSocAfterLastTrip(),
                "MIN_SOC_PLUG_IN": self.getMinSocPlugIn(),
                "WITHOUT_WORKING_STATION_ACCESS": self.getWithoutWorkingStationAccess(),
                "CHARGING_EVERY_DAY_AFTER_LAST_TRIP": self.getChargingEveryDayAfterLastTrip()
                },
            "model_specifications":{
                "NUMBER_OF_DAYS": self.getNumberOfDays(),
                "NUMBER_OF_USERS": self.getNumberOfUsers(),
                "NUMBER_OF_RUNS": self.getNumberOfRuns(),
                "START_DAY": self.getStartDay()
            },
            "flexibility_calculation":{
                "MIN_FLEX_TIME": self.getMinFlexTime(),
                "MIN_SOC": self.getMinSoc(),
                "SOC_TOL": self.getSocTol(),
                "MAX_SOC": self.getMaxSoc(),
                "MIN_CHARGING_RATE": self.getMinChargingRate(),
                "CHARGING_STRATEGIES": self.getChargingStrategies(),
                "HEURISTICS": self.getHeuristics(),
                "MIN_DELIEVERY_TIME": self.getMinDeliveryTime(),
                "SIMPLE_BOUNDARIES": self.getSimpleBoundaries(),
                "V2G_AVAILABILITY": self.getV2GAvailability(),
                "USER_INTERACTION_SIMULATION": self.getUserInteractionSimulation(),
                "USER_INTERACTION_SIM_RANGE_SHARES": self.getUserInteractionSimRangeShares(),
                "USER_INTERACTION_SIM_RANGES": self.getUserInteractionSimRanges(),

            },
            "flexibility_specifications": {
                "SPONTAN_FLEX": self.getSpontanflex(),
                "RISK": self.getRisk(),
                "FLEX_START_TIME": self.getFlexStartTime(),
                "FLEX_DURATION": self.getFlexDuration(),
                "FLEX_ACTIVATION_TIME": self.getFlexActivationTime(),
                "FLEX_PLACE": self.getFlexPlace(),
                "FLEX_AT_NUMBER_OF_DAY": self.getFlexAtNumberOfDay(),
                "FLEX_AT_NUMBER_OF_RUN": self.getFlexAtNumberOfRun(),
                "FLEX_AT_DAYTYPE": self.getFlexAtDaytype(),
                "FLEX_DEPENDANT": self.getFlexDependant(),
            },
            "viz_flexibility_specifications": {
                "VIZ_CHARGING_STRATEGIES": self.getVisChargingStrategies(),
                "VIZ_HEURISTICS": self.getVisHeuristics(),
                "VIZ_MODUS": self.getVisModus(),
                "VIZ_SHOW": self.getVisShow(),
                "VIZ_SAVE": self.getVisSave(),
                "VIZ_FILENAME": self.getVisFilename(),
            }
        }
        return json

    def getModelSettingsAsJson(self):
        json = {
            "trip-generation": {
                "MINIMUM_SPEED": self.getMinimumSpeed(),
                "MINIMUM_DISTANCE": self.getMinimumDistance(),
                "ENERGY_CONSUMPTION": self.getEnergyConsmuption(),
            },
            "user": {
                "USER_CLUSTER1_SHARE": self.getUserCluster1Share(),
                "USER_CLUSTER2_SHARE": self.getUserCluster2Share(),
                "WITH_CLUSTER": self.getWithCluster(),

            },
            "plug-in": {
                "PLUG_IN_SIMPLE": self.getPlugInSimple(),
                "PLUG_IN_ALPHA_PUBLIC": self.getPlugInAlphaPublic(),
                "PLUG_IN_ALPHA_WORK": self.getPlugInAlphaWork(),
                "PLUG_IN_ALPHA_HOME": self.getPlugInAlphaHome(),
                "MIN_SOC_AFTER_LAST_TRIP_ACTIVE": self.getMinSocAfterLastTripActive(),
                "MIN_SOC_AFTER_LAST_TRIP": self.getMinSocAfterLastTrip(),
                "MIN_SOC_PLUG_IN": self.getMinSocPlugIn(),
                "WITHOUT_WORKING_STATION_ACCESS": self.getWithoutWorkingStationAccess(),
                "CHARGING_EVERY_DAY_AFTER_LAST_TRIP": self.getChargingEveryDayAfterLastTrip()
            },
            "model_specifications": {
                "NUMBER_OF_DAYS": self.getNumberOfDays(),
                "NUMBER_OF_USERS": self.getNumberOfUsers(),
                "NUMBER_OF_RUNS": self.getNumberOfRuns(),
                "START_DAY": self.getStartDay()
            },
            "flexibility_calculations": {
                "MIN_SOC": self.getMinSoc(),
                "SOC_TOL": self.getSocTol(),
                "USER_INTERACTION_SIMULATION": self.getUserInteractionSimulation(),
                "USER_INTERACTION_SIM_RANGE_SHARES": self.getUserInteractionSimRangeShares(),
                "USER_INTERACTION_SIM_RANGES": self.getUserInteractionSimRanges(),
            }
        }
        return json

    def copy(self):
        Settings_copy = _SettingsContainer()
        json_setting = self.getSettingsAsJson()
        Settings_copy.updateSettings(json_setting, as_dict=True)
        return Settings_copy

settingsContainer = _SettingsContainer()

# settings not to adapt with json file, not relevant for simulation tool
SIMPLE = True # not implemented for value == False
CPCV = False # not implemented for value == True
with_cluster = False # not implemented properly for value == True --> set to true for computing new scenarios like Scenario PL 3b
user_Cluster1_share = 0.3
user_Cluster2_share = 0.5
useAlreadyComputedFlexibilities = True
MIN_CHARGING_RATE = 0
