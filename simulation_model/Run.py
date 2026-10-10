from config.settings import _SettingsContainer
from simulation_model.model import *
from config.settings import * # settingsContainer


class model_data():

    UserLists : list
    VehicleLists : list
    DayLists : list
    model_settings: _SettingsContainer = None
    name: str = None

    def __init__(self, UserLists, VehicleLists, DayLists, model_settings, name = None):
        self.UserLists = UserLists
        self.VehicleLists = VehicleLists
        self.DayLists = DayLists
        self.model_settings = model_settings
        self.name = name


def run(NumberOfDays, NumberOfUsers, start_day, NumberOfRuns, name, ch_filepath, ev_filepath ):
    UserList_allruns = list()
    VehicleList_allruns = list()
    DayList_allruns = list()

    for i in range(NumberOfRuns):
        print("Number of run:", i)
        # exemplary model creation

        tc_generator = TripChainGenerator()
        ch_types_prob = ChargingStationTypesProbability(ch_filepath)

        # ----------------------------------initialization------------------------------------------
        model = Model(NumberOfDays, NumberOfUsers, start_day, ch_types_prob, tc_generator, filepath = ev_filepath)

        # -----------------------------------------Simulation----------------------------------------

        model.simulate_mobility_and_charging(seed = i)
        UserList_allruns.append(model.UserList.copy())
        VehicleList_allruns.append(model.VehicleList.copy())
        DayList_allruns.append(model.day_list.copy())

    return model_data(UserList_allruns, VehicleList_allruns, DayList_allruns, settingsContainer.getModelSettingsAsJson(), name)