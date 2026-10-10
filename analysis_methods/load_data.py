import math
import pandas as pd
from simulation_model.PopulateUser import *


class charging_place(BaseModel):
    file_list : list = list()
    name:  str = None
    sessions: list = list()
    strange_sessions: list = list()
    errors: list = list()
    coressponding_sessions: list = list()

    def __init__(self,  name, *args, **kwargs):
        super().__init__(**kwargs)
        self.name = name
        self.file_list = list()
        self.sessions = list()
        self.errors = list()
        self.coressponding_sessions = list()

    def append_session(self,session):
        if len(self.sessions)==0:
            self.sessions.append(session)
            return

        count = 0
        for entry in self.sessions:
            if entry.end_date<session.end_date:
                count = count +1
                continue
            elif entry.end_date == session.end_date:
                if entry.end_time< session.end_time:
                    count = count + 1
                    continue

                else:
                    self.sessions.insert(count, session)
                    return
            else:
                self.sessions.insert(count, session)
                return
        self.sessions.append(session)

    def append_strange_session(self, session):
        self.strange_sessions.append(session)


    def append_error(self, error):
        self.errors.append(error)

    def find_corresponding_session(self, error):
        previous_entry = None
        for entry in self.sessions:
            if entry.end_date<error.date:
                previous_entry = entry
                continue
            elif entry.end_date == error.date:
                   if entry.end_time<error.time:
                        previous_entry = entry
                        continue
                   else:
                       self.coressponding_sessions.append([previous_entry, entry])
                       #self.plot_error(position = -1, energy= True)
                       #self.plot_error(position = -1, energy = False)
                       return entry
            else:
                self.coressponding_sessions.append([previous_entry, entry])
                return entry
            previous_entry = entry
        self.coressponding_sessions.append([previous_entry, entry])
        return entry

    def plot_error(self, position = None, energy=True):
        plt.figure()
        x = list()
        y = list()
        count = 0
        if energy:
            for entry in self.coressponding_sessions[position][0].time_series_energy:
                if count == 0:
                    date = entry.datee
                    x.append(entry.timee.hour*3600+entry.timee.minute*60 + entry.timee.second)
                    y.append(entry.value)
                else:
                    x.append(entry.timee.hour*3600+entry.timee.minute*60 + entry.timee.second+(entry.datee-date).total_seconds())
                    y.append(entry.value)
                count = count +1
        else:
            for entry in self.coressponding_sessions[position][0].time_series_power:
                if count == 0:
                    date = entry.datee
                    x.append(entry.timee.hour*3600+entry.timee.minute*60 + entry.timee.second)
                    y.append(entry.value)
                else:
                    x.append(entry.timee.hour*3600+entry.timee.minute*60 + entry.timee.second+(entry.datee-date).total_seconds())
                    y.append(entry.value)
                count = count +1

        plt.plot(x,y, label='previous_entry')
        #plt.show()
        #plt.figure()
        x = list()
        y = list()
        count = 0
        if energy:
            for entry in self.coressponding_sessions[position][1].time_series_energy:

                x.append(entry.timee.hour * 3600 + entry.timee.minute * 60 + entry.timee.second + (
                                entry.datee - date).total_seconds())
                y.append(entry.value)
                count = count + 1
        else:
            #count = 0
            for entry in self.coressponding_sessions[position][1].time_series_power:

                x.append(entry.timee.hour * 3600 + entry.timee.minute * 60 + entry.timee.second + (
                        entry.datee - date).total_seconds())
                y.append(entry.value)
                #count = count + 1
        plt.plot(x, y, label='entry')

        plt.axvline(x=self.errors[position].time.hour*3600 +self.errors[position].time.minute*60 + self.errors[position].time.second +(self.errors[position].date-date).total_seconds(), color='b', label='Error')
        plt.text(s=self.errors[position].errorMessage, x=self.errors[position].time.hour*3600 +self.errors[position].time.minute*60 + self.errors[position].time.second +(self.errors[position].date-date).total_seconds(), y=0)
        plt.legend()
        if not (self.errors[position].date-date).total_seconds()/(24*3600)>10:

            plt.show()
        else:
            print((self.errors[position].date-date).total_seconds()/(24*3600))
            plt.close()

    def append_timeseries(self, data, energy):
        self.sessions[-1].append_time_series(data, energy)

class session:
            start_date: datetime.date = None
            end_date: datetime.date = None
            start_time: nptime = None
            end_time: nptime = None
            energy: float = None
            duration: datetime.timedelta = None
            time_series_energy: list = list()
            time_series_power: list = list()

            def __init__(self, start, end, energy, *args, **kwargs):
                super().__init__(**kwargs)
                self.start_date = datetime.date(int(start[0:4]), int(start[5:7]), int(start[8:10]))
                self.end_date = datetime.date(int(end[0:4]), int(end[5:7]), int(end[8:10]))
                self.start_time = nptime(hour=int(start[11:13]), minute=int(start[14:16]), second=int(start[17:19]))
                self.end_time = nptime(hour=int(end[11:13]), minute=int(end[14:16]), second=int(end[17:19]))
                self.energy = energy
                self.time_series_energy = list()
                self.time_series_power = list()
                self.duration = self.end_date - self.start_date
                if self.start_time > self.end_time:
                    self.duration = self.duration + self.end_time - self.start_time + datetime.timedelta(days=1)
                else:
                    self.duration = self.duration + self.end_time - self.start_time

            def append_time_series(self, data, energy):
                lines = [list(), list()]
                for entry in data["Date"]:
                    lines[0].append(entry)
                for entry in data["Value"]:
                    lines[1].append(entry)
                lines = np.transpose(lines)
                if energy:
                    for line in lines:
                        self.time_series_energy.append(TimeSeries(line))
                else:
                    for line in lines:
                        self.time_series_power.append(TimeSeries(line))

            def plot_time_series(self, energy):
                x = list()
                y = list()

                count = 0
                if energy:
                    time_series = self.time_series_energy
                else:
                    time_series = self.time_series_power

                for entry in time_series:
                    if count == 0:
                        date = entry.datee
                        x.append(entry.timee.hour * 3600 + entry.timee.minute * 60 + entry.timee.second)
                        y.append(entry.value)
                    else:
                        x.append(entry.timee.hour * 3600 + entry.timee.minute * 60 + entry.timee.second + (
                                entry.datee - date).total_seconds())
                        y.append(entry.value)
                    count = count + 1
                plt.plot(x, y)
                plt.show()

            def compute_power(self):
                max_power = -1
                first_zero = False
                count = 0
                ch_end_time = -1
                ch_end_time2 = -1
                if len(self.time_series_power) > 0:
                    for entry in self.time_series_power:
                        if entry.value != 0:
                            if entry.value > max_power:
                                max_power = entry.value
                            elif not first_zero and count > 1:

                                first_zero = True
                                ch_end_time = entry.timee
                                ch_end_date = entry.datee
                        count = count + 1
                    if ch_end_time < 0:
                        ch_end_time = self.end_time

                end_energy = 0
                start_energy = self.time_series_energy[0].value

                count_no_charging = 0
                if len(self.time_series_energy) > 0:
                    for entry in self.time_series_energy:

                        if entry.value > end_energy:
                            end_energy = entry.value
                            if count_no_charging > 0:
                                count_no_charging = 0
                        else:

                            if count_no_charging == 0:
                                ch_end_time2 = entry.timee
                                ch_end_date2 = entry.datee
                            count_no_charging = count_no_charging + 1

                power = (end_energy - start_energy) / (self.start_time - ch_end_time2)
                if ch_end_time2 < 0:
                    ch_end_time2 = self.end_time

                return ch_end_time, ch_end_date, ch_end_time2, ch_end_date2, max_power, power

class TimeSeries:
            datee: datetime.date = None
            timee: datetime.time = None
            value: int = None

            def __init__(self, line, *args, **kwargs):
                super().__init__(**kwargs)
                datee = line[0]
                self.datee = datetime.date(int(datee[0:4]), int(datee[5:7]), int(datee[8:10]))
                self.timee = datetime.time(int(datee[11:13]), int(datee[14:16]), int(datee[17:19]))
                self.value = self.value = int(float((str(line[1])[0:len(line[1])-2])))  #line[1]


def load_Obelis_data(compute_charging_session = False, filename = "OBELIS_Ladevorgaenge_2022.csv", savename = "dataCharging/alreadyLoaded/Obelis_"):
    if compute_charging_session:
        ch_prob = ChargingStationTypesProbability()
        UserList, VehicleList,  = PopulateUser(settingsContainer.getNumberOfUsers(), ch_prob)

    with open(os.path.join("dataCharging/Charging_data_for_tests", filename)) as file:
        csv_reader = csv.reader(file, delimiter=';')
        data = list()
        start_times = list()
        ch_end_times = list()
        plugin_end_times = list()
        plugin_durations = list()
        ch_durations = list()
        count = 0
        count_wrong_data = 0
        for roww in csv_reader:
            break2 = False
            if count==0:
                count +=1
                continue
            #roww = row

            new_row = list()
            if roww[3]!= "Kundenparkplatz":
                continue
            for i in [6,7,9,8]:
                if i == 6 or i == 7:
                    year2 = int(roww[i][6:10])
                    month2 = int(roww[i][3:5])
                    day2 = int(roww[i][0:2])
                    entry2 = datetime.date(year = year2, month = month2, day =day2)
                    new_row.append(entry2)
                    entry = datetime.timedelta(hours=int(roww[i][11:13]), minutes=int(roww[i][14:16]))
                    if i == 7:
                        entry += datetime.timedelta(days=(new_row[2] - new_row[0]).days)
                elif i ==8:
                    entry = datetime.timedelta(seconds = float(roww[i])/10)
                elif i == 9:
                    entry = float(roww[i])/10000
                else: # i == 1:
                    continue
                new_row.append(entry)
            if compute_charging_session:
                recalculate = True
                rc_count = 0
                while recalculate:
                    user = UserList[random.randrange(0,100)]
                    ev = VehicleList[user.ev_id]
                    charging_rate = min(float(roww[i]), ev.DC_power)
                    charging_end = new_row[1] + ev.time_to_charge(new_row[4], charging_rate)
                    rc_count+=1

                    if charging_end <= new_row[3]:
                        recalculate = False
                    if rc_count > 100:
                        break2 = True
                        count_wrong_data += 1

                        break
                        print("Error: too much recalculations")
                if break2:
                    continue
                new_row.append(charging_end)
                new_row.append(charging_rate)

            start_times.append(new_row[1])
            ch_end_times.append(new_row[6]-datetime.timedelta(days = new_row[6].days))
            plugin_durations.append(new_row[5])
            ch_durations.append(new_row[6]-new_row[1])
            if abs((new_row[6]-new_row[1])-ev.time_to_charge(new_row[4], charging_rate)).total_seconds() >1e-8:
                print("Error-computation of duration in loaded data")
            plugin_end_times.append(new_row[3]-datetime.timedelta(days = new_row[3].days))
            count += 1
            data.append(new_row)
            if count % 1000 == 0:
                print(count)
        ch_modus = "_Obelis"
        save_list(data, savename + "+_whole")
        save_list(start_times, savename + ch_modus + "_start_times")
        save_list(ch_end_times, savename + ch_modus + "_ch_end_times")
        save_list(ch_durations, savename + ch_modus + "_ch_durations")
        save_list(plugin_durations, savename + ch_modus + "_plugin_durations")
        save_list(plugin_end_times, savename + ch_modus + "_plugin_end_times")


def load_UK_Charging_data(ch_modus = "home", compute_charging_session = False,
                          filename = "electric-chargepoint-analysis-2017-raw-domestics-data.csv",
                          savename = "dataCharging/alreadyLoaded/UK_charging_",
                          interval_duration = datetime.timedelta(minutes = 60)):

    if compute_charging_session:
        ch_prob = ChargingStationTypesProbability()
        UserList, VehicleList,  = PopulateUser(settingsContainer.getNumberOfUsers(), ch_prob)

    with open(os.path.join("dataCharging/Charging_data_for_tests", filename)) as file:
        csv_reader = csv.reader(file, delimiter=';')

        data = list()
        start_times = list()
        ch_end_times = list()
        plugin_end_times = list()
        plugin_durations = list()
        ch_durations = list()
        #durations = list()
        count = 0
        total_count = 0
        charging_stations = list()
        charging_stations_indeces = list()
        energies = list()
        Number_of_intervals = math.ceil(datetime.timedelta(days=1).total_seconds() / interval_duration.total_seconds())
        durations_per_interval = list()
        pl_durations_per_interval = list()
        energies_per_interval = list()
        for i in range(Number_of_intervals):
            durations_per_interval.append(list())
            pl_durations_per_interval.append(list())
            energies_per_interval.append(list())

        count_wrong_data = 0
        for row in csv_reader:
            if total_count==0:
                total_count +=1
                continue
            elif total_count == 1000000:
                break
            if ch_modus == "public":
                roww = row
            elif ch_modus == "home":
                roww = row[0].split(',')
            else:
                return
            break2 = False
            new_row = list()
            for i in range(len(roww)):
                if i ==2 or i == 4:
                    if ch_modus == "home":
                        year2 = int(roww[i][0:4])
                        month2 = int(roww[i][5:7])
                        day2 = int(roww[i][8:10])
                    elif ch_modus == "public":
                        year2 = int(roww[i][6:10])
                        month2 = int(roww[i][3:5])
                        day2 = int(roww[i][0:2])
                    entry = datetime.date(year = year2, month = month2, day =day2)
                elif i == 3 or i == 5:
                    entry = datetime.timedelta(hours=int(roww[i][0:2]), minutes=int(roww[i][3:5]), seconds = int(roww[i][6:8]))
                    if i == 5:

                        entry += datetime.timedelta(days =(new_row[2]-new_row[0]).days)
                elif i ==6:
                    entry = float(roww[i])
                elif i == 7:
                    entry = datetime.timedelta(hours = float(roww[i]))
                else: # i == 1:
                    continue
                new_row.append(entry)
            if compute_charging_session:
                recalculate = True
                rc_count = 0
                while recalculate:
                    user = UserList[random.randrange(0,100)]
                    if ch_modus == "home":
                        current_station = user.ChargingStation
                    elif ch_modus == "public":
                        ch_types_prob = ChargingStationTypesProbability()
                        current_station = ch_types_prob.assign_charging_station(ChargingStationPlace.PUBLIC)
                        ref = 22
                        number_fasts = 103326
                        while (total_count > number_fasts and current_station.power < ref) or (total_count <=number_fasts and current_station.power > ref):
                            current_station = ch_types_prob.assign_charging_station(ChargingStationPlace.PUBLIC)

                    ev = VehicleList[user.ev_id]
                    if current_station.ac:
                        charging_rate = min(current_station.power, ev.AC_power)
                    else:
                        charging_rate = min(current_station.power, ev.DC_power)
                    charging_end = new_row[1] + ev.time_to_charge(new_row[4], charging_rate)
                    if charging_end <= new_row[3]:
                        recalculate = False
                    rc_count += 1
                    if rc_count > 100:
                        break2 = True
                        count_wrong_data +=1
                        break
                        print("Error: too much recalculations")
                if break2:
                    total_count += 1
                    continue
                new_row.append(charging_end)
                new_row.append(charging_rate)
                new_row.append(roww[1])
            #charging stations
            ch_station = roww[1]
            if charging_stations.count(ch_station) >= 1:
                idxxx = charging_stations.index(ch_station)
                if ch_station != data[charging_stations_indeces[idxxx][-1]][-1]:
                    print("Error: wrong ch station")
                charging_stations_indeces[idxxx].append(count)

            else:
                charging_stations.append(ch_station)
                charging_stations_indeces.append(list())
                charging_stations_indeces[-1].append(count)
            start_times.append(new_row[1])
            ch_end_times.append(new_row[6]-datetime.timedelta(days = new_row[6].days))
            plugin_durations.append(new_row[5])
            ch_duration = new_row[6]-new_row[1]
            ch_durations.append(ch_duration)
            energies.append(new_row[4])
            interval = int(new_row[1].total_seconds() / interval_duration.total_seconds())
            energies_per_interval[interval].append(new_row[4])
            durations_per_interval[interval].append(ch_duration)
            pl_durations_per_interval[interval].append(new_row[5])
            if abs((new_row[6]-new_row[1])-ev.time_to_charge(new_row[4], charging_rate)).total_seconds() >1e-8:
                print("Error-computation of duration in loaded data")
            plugin_end_times.append(new_row[3]-datetime.timedelta(days = new_row[3].days))
            count += 1
            total_count +=1
            data.append(new_row)
            if count % 10000 == 0:
                print(str(count/10000) + "*10000")
                print(count_wrong_data)
                print(total_count)
        save_list(data, savename + ch_modus + "_whole")
        save_list(start_times, savename + ch_modus + "_start_times")
        save_list(ch_end_times, savename + ch_modus + "_ch_end_times")
        save_list(ch_durations, savename + ch_modus + "_ch_durations")
        save_list(plugin_durations, savename + ch_modus + "_plugin_durations")
        save_list(plugin_end_times, savename + ch_modus + "_plugin_end_times")
        save_list(charging_stations, savename + ch_modus + "_charging_stations")
        save_list(charging_stations_indeces, savename + ch_modus + "_charging_stations_indeces")
        save_list(energies, savename + ch_modus + "_energy_per_sessions")
        save_list(energies_per_interval, savename + ch_modus + "_energies_per_intervals")
        save_list(durations_per_interval, savename + ch_modus + "_ch_durations_per_intervals")
        save_list(pl_durations_per_interval, savename + ch_modus + "_pl_durations_per_intervals")


def load_lama_data(ch_modus = "work", compute_charging_session = True,
                   filename = "data/KI-LAN_Ladedaten_Marquardt_Anonymisiert/anonym_data",
                   savename = "dataCharging/alreadyLoaded/lama_",
                   interval_duration = datetime.timedelta(minutes = 60)):
    ### initialization
    data = list()
    start_times = list()
    ch_end_times = list()
    plugin_end_times = list()
    plugin_durations = list()
    ch_durations = list()
    # durations = list()
    count = 0
    total_count = 0
    charging_stations = list()
    charging_stations_indeces = list()
    energies = list()
    Number_of_intervals = math.ceil(datetime.timedelta(days=1).total_seconds() / interval_duration.total_seconds())
    durations_per_interval = list()
    pl_durations_per_interval = list()
    energies_per_interval = list()
    for i in range(Number_of_intervals):
        durations_per_interval.append(list())
        pl_durations_per_interval.append(list())
        energies_per_interval.append(list())

    if compute_charging_session:
        ch_prob = ChargingStationTypesProbability()
        UserList, VehicleList,  = PopulateUser(settingsContainer.getNumberOfUsers(), ch_prob)

    directory = "dataCharging/Charging_data_for_tests/data/KI-LAN_Ladedaten_Marquardt_Anonymisiert/anonym_data"

    file_list = list()
    ###load_data
    for root, dirs, files in os.walk(directory, topdown=False):
        count_wrong_data = 0
        if root[-10:] == "timeseries":
            ch_place = charging_place(root[57:-11])
        elif ch_place.name != files[0][12:-4]:
            ch_place = charging_place(files[0][12:-4])
        for file in files:

            f = os.path.join(root, file)
            if os.path.isfile(f):
                if root[-10:] == "timeseries":
                    if file == "timeseries_IMPORTED_ACTIVE_ENERGY_REGISTER.csv":
                        energy = True
                    elif file == "timeseries_IMPORTED_ACTIVE_POWER.csv":
                        energy = False
                    else:
                        
                        continue
                ch_place.file_list.append([pd.read_csv(f, on_bad_lines='skip'), energy])

        if root[-10:] != "timeseries":
            file_list.append(ch_place)
    # read data out
    for ch_place2 in file_list[0:-2]:
        print(ch_place2.name)

        new_row = list()
        counter = 0
        break2 = False
        if   True or len(ch_place2.file_list) > 2:
            pos = -1
            entries1 = [entry for entry in ch_place2.file_list[pos][0]["Started"]][0]
            entries2 = [entry for entry in ch_place2.file_list[pos][0]["Ended"]][0]
            entries3 = [entry for entry in ch_place2.file_list[pos][0]["Consumed Energy"]][0]



            ch_session_start_date = datetime.date(year = int(entries1[0:4]), month = int(entries1[5:7]), day = int(entries1[8:10]))
            ch_session_start_time = datetime.timedelta(hours = int(entries1[11:13]), minutes = int(entries1[14:16]), seconds= int(entries1[17:19]))

            if type(entries3) == str:
                continue
                entries3 = 0
                
            ch_session_energy = entries3/1000
            #ch_session_plugin_start = ch_session_start_date

            if True: #len(ch_place2.file_list) > 2:
                if entries2 != ' ' and len(ch_place2.file_list[0]) > 0:
                    ch_place2.append_session(session(entries1, entries2, entries3))
                else:
                    ch_place2.append_strange_session([entries1, entries2, entries3])
                if True:
                    if len(ch_place2.file_list) > 1  and len(ch_place2.file_list[0]) > 0 and len(ch_place2.sessions) > 0:
                        # for entry in ch_place2.file_list[0]:
                        ch_place2.append_timeseries(ch_place2.file_list[1][0], ch_place2.file_list[1][1])
                    if len(ch_place2.file_list[0]) > 1 and len(ch_place2.file_list[0][0]) > 1 and len(ch_place2.sessions) > 0:
                        # for entry in ch_place2.file_list[0]:
                        ch_place2.append_timeseries(ch_place2.file_list[0][0], ch_place2.file_list[0][1])
            #else:
               

            if len(ch_place2.sessions)>0:

                ch_session_plugin_end_date = datetime.date(year=int(entries2[0:4]), month=int(entries2[5:7]),
                                                           day=int(entries2[8:10]))
                ch_session_plugin_end_time = datetime.timedelta(hours=int(entries2[11:13]), minutes=int(entries2[14:16]),
                                                                seconds=int(entries2[17:19])) + datetime.timedelta(
                    days=(ch_session_plugin_end_date - ch_session_start_date).days)
                ch_session_pl_duration = ch_session_plugin_end_date - ch_session_start_date + ch_session_plugin_end_time - ch_session_start_time


            # ladevorgängee simulieren

                if compute_charging_session:
                    recalculate = True
                    rc_count = 0
                    while recalculate:
                        user = UserList[random.randrange(0,100)]
                        if ch_modus == "work":
                            # same distribution of
                            ch_types_prob = ChargingStationTypesProbability()
                            current_station = ch_types_prob.assign_charging_station(ChargingStationPlace.WORK)


                        else:
                            print("lama only for work modus")

                        ev = VehicleList[user.ev_id]
                        if current_station.ac:
                            charging_rate = min(current_station.power, ev.AC_power)
                        else:
                            charging_rate = min(current_station.power, ev.DC_power)
                        charging_end = ch_session_start_time + ev.time_to_charge(ch_session_energy, charging_rate)
                        if charging_end <= ch_session_plugin_end_time:
                            recalculate = False
                        rc_count += 1
                        if rc_count > 100:
                            break2 = True
                            count_wrong_data +=1
                            break
                            print("Error: too much recalculations")

                    if break2:
                        total_count += 1
                        continue
                    ch_session_end_time = charging_end
                    ch_session_rate = charging_rate
                    charging_end_date=ch_session_start_date + charging_end

                if False and (len(ch_place2.sessions[-1].time_series_power) > 0 or len(
                    ch_place2.sessions[-1].time_series_energy) > 0):
                    ch_end_time, ch_end_date, ch_end_time2, ch_end_date2, max_power, power = ch_place2.sessions[-1].compute_power()
                    ch_session_end_date = ch_end_date2
                    ch_session_end_time = ch_end_time2.to_timedelta() + ch_end_date2 - ch_session_start_date
                    ch_session_rate = power
            else:
                continue







            new_row.append(ch_session_start_date)
            new_row.append(ch_session_start_time)


            new_row.append(ch_session_plugin_end_date)
            new_row.append(ch_session_plugin_end_time)
            new_row.append(ch_session_energy)
            new_row.append(ch_session_pl_duration)
            new_row.append(ch_session_end_time)
            new_row.append(ch_session_rate)




            start_times.append(new_row[1])
            ch_end_times.append(new_row[6] - datetime.timedelta(days=new_row[6].days))
            plugin_durations.append(new_row[5])
            ch_duration = new_row[6] - new_row[1]
            ch_durations.append(ch_duration)
            energies.append(new_row[4])
            interval = int(new_row[1].total_seconds() / interval_duration.total_seconds())
            energies_per_interval[interval].append(new_row[4])
            durations_per_interval[interval].append(ch_duration)
            pl_durations_per_interval[interval].append(new_row[5])
            if abs((new_row[6] - new_row[1]) - ev.time_to_charge(new_row[4], charging_rate)).total_seconds() > 1e-8:
                print("Error-computation of duration in loaded data")
            plugin_end_times.append(new_row[3] - datetime.timedelta(days=new_row[3].days))
            #count += 1
            #total_count += 1
            data.append(new_row)
            #if count % 10000 == 0:
             #   print(str(count / 10000) + "*10000")
              #  print(count_wrong_data)
               # print(total_count)


    save_list(data, savename + ch_modus + "_whole")
    save_list(start_times, savename + ch_modus + "_start_times")
    save_list(ch_end_times, savename + ch_modus + "_ch_end_times")
    save_list(ch_durations, savename + ch_modus + "_ch_durations")
    save_list(plugin_durations, savename + ch_modus + "_plugin_durations")
    save_list(plugin_end_times, savename + ch_modus + "_plugin_end_times")
    save_list(charging_stations, savename + ch_modus + "_charging_stations")
    save_list(charging_stations_indeces, savename + ch_modus + "_charging_stations_indeces")
    save_list(energies, savename + ch_modus + "_energy_per_sessions")
    save_list(energies_per_interval, savename + ch_modus + "_energies_per_intervals")
    save_list(durations_per_interval, savename + ch_modus + "_ch_durations_per_intervals")
    save_list(pl_durations_per_interval, savename + ch_modus + "_pl_durations_per_intervals")
##TODO: load_data methode für lama Daten: muss DAteien erzeugen analog zu UK_Charging und Histogramm-Vergleich ermöglichen.
        #Aufgabe: load lama anaolog zu UK Charging:
        #Anforderungen an load lama: lädt Lama-Daten und speichert  die Listen als Dateien analog zu load_UK_Charging mit Endungen:

        # whole (alle Listen),   "_start_times" (Ladestartzeiten), "_ch_end_times" (Ladeendzeiten),+ "_ch_durations" (Ladedauern),
        # "_plugin_durations" (Plug-In-Dauern),"_plugin_end_times" (Plug-In-Endzeiten),
                    #--> diese Listen sind die Wichtigesten (oben) und vermutlich auch einfacher zu erstellen: Ch_end_times und duration noch etwas schwierige, da sie extra aus timeseries berechnet werden müssen.
                    # Erstmal wichtig, Listen für Plug-in duration und plugin-start und plug-in end.
        # "_charging_stations" (Ladestationen), # "_charging_stations_indeces: als leere list(), da nicht notwenidg
#       ,"_energy_per_sessions"(geladene Energie)
        # ,"_energies_per_intervals" (geladene Energie je Zeitintervall,"_ch_durations_per_intervals","_pl_durations_per_intervals" ) --> Diese drei Listen je Zeitintervall erstmal nicht wichtig!

        # load UK_Charging Data lädt UK_Data von andrere csv Datei (für Ladedaten an Ladestationen zu Hause). Wir wollen Ladedaten bei der Arbiet (modus = "work" bei Simulation)
        # Hierfür gibt es die Daten des Projekts "Lama". Lamadaten müssen eingelesen werden und die Listen entpsrechend befüllt werden, sodass diese Listen mit den Dateinamen von dieser Methode geöffent werden können
        #Anschließend können Histogramme mi Lamadaten und Daten aus der Simulation verglichen werden. Modus ist immer "work" (Daten zum Laden bei der Arbeit).
        # Dateistruktur ist bei den lamadaten leider ganz anders, deswegen muss das Einlesen anderes erfolgen. Als Orientierung gibt es bereits die Datei load_lama, welche die Dateien beriets geöffnet und verarbeitet hat
        # Allerdings nicht so, wie wir es brauchen: Listen wie oben beschrieben, enthalten die Zeiten zu jedem Ladevorgang als datetime.timedelta Objekt. --> Zeiten aus lamadaten müssen umgewandelt werden.
        #Die zZeiten dort beschrieben die Pllug-Out Zeit.
#        #Die Ladeendzeit kann schon früher sein, ist aber nicht beschrieben --> in timeserie schauen, wann maximale energie erreicht wurde


        # Erstmal einfache Listen: Plug-In-Zeiten und Dauer und diese mit Simulation vergleichen. NIcht nur histogramm

def load_UK_Charging_data_and_append(ch_modus = "home", compute_charging_session = False,
                                     filename = "electric-chargepoint-analysis-2017-raw-domestics-data3.csv",
                                     savename = "dataCharging/alreadyLoaded/UK_charging2",
                                     interval_duration=datetime.timedelta(minutes=60)
                                     ):
    # adapt with energies_per_interval,...
    if compute_charging_session:
        ch_prob = ChargingStationTypesProbability()
        UserList, VehicleList,  = PopulateUser(settingsContainer.getNumberOfUsers(), ch_prob)
    charging_stations = open_file(savename + ch_modus + "_charging_stations")
    charging_stations_indeces = open_file(savename + ch_modus + "_charging_stations_indeces")
    data = open_file(savename + ch_modus + "_whole")
    start_times = open_file(savename + ch_modus + "_start_times")
    ch_end_times = open_file(savename + ch_modus + "_ch_end_times")
    plugin_end_times = open_file(savename + ch_modus + "_plugin_end_times")
    plugin_durations = open_file(savename + ch_modus + "_plugin_durations")
    ch_durations = open_file(savename + ch_modus + "_ch_durations")
    energies = open_file(savename + ch_modus + "_energy_per_sessions")
    energies_per_interval = open_file(savename + ch_modus + "_energies_per_intervals")
    durations_per_interval = open_file(savename + ch_modus + "_ch_durations_per_intervals")
    pl_durations_per_interval = open_file(savename + ch_modus + "_pl_durations_per_intervals")

    savename = savename + "2"
    with open(os.path.join("dataCharging/Charging_data_for_tests", filename)) as file:

        csv_reader = csv.reader(file, delimiter=';')



        #durations = list()
        count = len(data)
        total_count = 0

        count_wrong_data = 0
        for row in csv_reader:
            if total_count==0:
                total_count +=1
                continue
            #elif total_count == 1000000:
               # break
            if ch_modus == "public":
                roww = row
            elif ch_modus == "home":
                roww = row[0].split(',')
            else:
                return
            break2 = False
            new_row = list()
            for i in range(len(roww)):
                if i ==2 or i == 4:
                    if ch_modus == "home":
                        year2 = int(roww[i][0:4])
                        month2 = int(roww[i][5:7])
                        day2 = int(roww[i][8:10])
                    elif ch_modus == "public":
                        year2 = int(roww[i][6:10])
                        month2 = int(roww[i][3:5])
                        day2 = int(roww[i][0:2])
                    entry = datetime.date(year = year2, month = month2, day =day2)
                elif i == 3 or i == 5:
                    entry = datetime.timedelta(hours=int(roww[i][0:2]), minutes=int(roww[i][3:5]), seconds = int(roww[i][6:8]))
                    if i == 5:

                        entry += datetime.timedelta(days =(new_row[2]-new_row[0]).days)
                elif i ==6:
                    entry = float(roww[i])
                elif i == 7:
                    entry = datetime.timedelta(hours = float(roww[i]))
                else: # i == 1:

                    continue
                new_row.append(entry)
            if compute_charging_session:
                recalculate = True
                rc_count = 0
                while recalculate:
                    user = UserList[random.randrange(0,100)]
                    if ch_modus == "home":
                        current_station = user.ChargingStation
                    elif ch_modus == "public":
                        ch_types_prob = ChargingStationTypesProbability()
                        current_station = ch_types_prob.assign_charging_station(ChargingStationPlace.PUBLIC)
                        ref = 22
                        number_fasts = 103326
                        while (total_count > number_fasts and current_station.power < ref) or (total_count <=number_fasts and current_station.power > ref):
                            current_station = ch_types_prob.assign_charging_station(ChargingStationPlace.PUBLIC)

                    ev = VehicleList[user.ev_id]
                    if current_station.ac:
                        charging_rate = min(current_station.power, ev.AC_power)
                    else:
                        charging_rate = min(current_station.power, ev.DC_power)
                    charging_end = new_row[1] + ev.time_to_charge(new_row[4], charging_rate)
                    if charging_end <= new_row[3]:
                        recalculate = False
                    rc_count += 1
                    if rc_count > 100:
                        break2 = True
                        count_wrong_data +=1
                        break
                        print("Error: too much recalculations")
                if break2:
                    total_count += 1
                    continue
                new_row.append(charging_end)
                new_row.append(charging_rate)
                new_row.append(roww[1])
            #charging stations
            ch_station = roww[1]
            if charging_stations.count(ch_station) >= 1:
                idxxx = charging_stations.index(ch_station)
                if ch_station != data[charging_stations_indeces[idxxx][-1]][-1]:
                    print("Error: wrong ch station")
                charging_stations_indeces[idxxx].append(count)

            else:
                charging_stations.append(ch_station)
                charging_stations_indeces.append(list())
                charging_stations_indeces[-1].append(count)
            start_times.append(new_row[1])
            ch_end_times.append(new_row[6]-datetime.timedelta(days = new_row[6].days))
            plugin_durations.append(new_row[5])
            ch_duration = new_row[6] - new_row[1]
            ch_durations.append(ch_duration)
            energies.append(new_row[4])
            interval = int(new_row[1].total_seconds() / interval_duration.total_seconds())
            energies_per_interval[interval].append(new_row[4])
            durations_per_interval[interval].append(ch_duration)
            pl_durations_per_interval[interval].append(new_row[5])
            if abs((new_row[6]-new_row[1])-ev.time_to_charge(new_row[4], charging_rate)).total_seconds() >1e-8:
                print("Error-computation of duration in loaded data")
            plugin_end_times.append(new_row[3]-datetime.timedelta(days = new_row[3].days))
            count += 1
            total_count +=1
            data.append(new_row)
            if count % 10000 == 0:
                print(str(count/10000) + "*10000")
                print(count_wrong_data)
                print(total_count)
        save_list(data, savename + ch_modus + "whole")
        save_list(start_times, savename + ch_modus + "_start_times")
        save_list(ch_end_times, savename + ch_modus + "_ch_end_times")
        save_list(ch_durations, savename + ch_modus + "_ch_durations")
        save_list(plugin_durations, savename + ch_modus + "_plugin_durations")
        save_list(plugin_end_times, savename + ch_modus + "_plugin_end_times")
        save_list(charging_stations, savename + ch_modus + "charging_stations")
        save_list(charging_stations_indeces, savename + ch_modus + "charging_stations_indeces")
        save_list(energies, savename + ch_modus + "_energy_per_sessions")
        save_list(energies_per_interval, savename + ch_modus + "_energies_per_intervals")
        save_list(durations_per_interval, savename + ch_modus + "_ch_durations_per_intervals")
        save_list(pl_durations_per_interval, savename + ch_modus + "_pl_durations_per_intervals")


def compute_histogram_lists( VehicleList, ch_modus = "home", DayType = -1, start_day = 0, compute_start_time=True,
                             compute_ch_duration=True, compute_ch_end_time = True, compute_plugin_duration= True,
                             compute_plugin_end_time = True, duration = datetime.timedelta(minutes = 60),
                             duration_duration =datetime.timedelta(minutes = 60),  total_start_time_list = None,
                             total_ch_end_time_list = None, total_ch_duration_list = None, compute_energies = True,
                             total_plugin_end_time_list = None, total_plugin_duration_list = None,
                             compute_durations_per_interval = True, compute_energies_per_interval = True, compute_cluster_list = True, clustering_with_adapted_pl_dur = True):

    if ch_modus == "home":
        cmp_place = ChargingStationPlace.HOME
    elif ch_modus == "public":
        cmp_place = ChargingStationPlace.PUBLIC
    elif ch_modus == "work":
        cmp_place = ChargingStationPlace.WORK
    elif ch_modus == "all":
        cmp_place = None

    cluster_lists = list()
    for i in range(7):
        cluster_lists.append([list() for i in range(4)])
    allLists = list()
    Number_of_intervals = math.ceil(datetime.timedelta(days=1).total_seconds() / duration.total_seconds())
    NumberOfDurationIntervals = math.ceil(
        datetime.timedelta(days=1).total_seconds() / duration_duration.total_seconds())

    if compute_start_time:
        if total_start_time_list == None:
            total_start_time_list = list()
            start_time_append = True
        start_time_list = list()
        for i in range(Number_of_intervals):
            start_time_list.append(list())

    if compute_ch_end_time:
        if total_ch_end_time_list == None:
            total_ch_end_time_list = list()
            ch_end_time_append = True
        ch_end_time_list = list()
        for i in range(Number_of_intervals):
            ch_end_time_list.append(list())

    if compute_ch_duration:
        if total_ch_duration_list == None:
            total_ch_duration_list = list()
            ch_Duration_append = True
        ch_duration_list = list()
        for i in range(NumberOfDurationIntervals):
            ch_duration_list.append(list())

    if compute_plugin_end_time:
        if total_plugin_end_time_list == None:
            total_plugin_end_time_list = list()
            plugin_end_time_append = True
        plugin_end_time_list = list()
        for i in range(Number_of_intervals):
            plugin_end_time_list.append(list())

    if compute_plugin_duration:
        if total_plugin_duration_list == None:
            total_plugin_duration_list = list()
            plugin_Duration_append = True
        plugin_duration_per_interval = list()
        for i in range(Number_of_intervals):
            plugin_duration_per_interval.append(list())

    if compute_durations_per_interval:
        durations_per_interval = list()
        #duration_list2 = list()

        for i in range(Number_of_intervals):
            durations_per_interval.append(list())
            #duration_list2.append(list())
            #for i in range(NumberOfDurationIntervals):
               # duration_list2[i].append(list())

    if compute_energies_per_interval:
        energies_per_interval = list()
        energy_list2 = list()

        for i in range(Number_of_intervals):
            energies_per_interval.append(list())
            #energy_list2.append(list())
           # for i in range(NumberOfDurationIntervals):
            #    energy_list2[i].append(list())

    if compute_energies:
        energies = list()

    Days = compute_day_list(DayType, start_day, settingsContainer.getNumberOfDays())

    count = 0
    if start_time_append or plugin_Duration_append or compute_durations_per_interval or compute_energies_per_interval or \
            plugin_end_time_append or ch_end_time_append or ch_Duration_append:

        number_of_charging_sessions = [[[0 for j in range(len(Days))] for i in range(len(VehicleList[0]))] for ij in range(len(VehicleList))]
        energy_per_charging_sessions = [[[list() for j in range(len(Days))] for i in range(len(VehicleList[0]))] for ij in range(len(VehicleList))]

        trip_distance_on_day = [[[0 for j in range(len(Days))] for i in range(len(VehicleList[0]))] for ij in range(len(VehicleList))]
        number_of_trips = [[[0 for j in range(len(Days))] for i in range(len(VehicleList[0]))] for ij in range(len(VehicleList))]
        not_at_home_charging_share = [[0  for i in range(len(VehicleList[0]))] for ij in range(len(VehicleList))]
        number_of_trips_to_ch_modus = [[[0 for j in range(len(Days))] for i in range(len(VehicleList[0]))] for ij in range(len(VehicleList))]
        number_of_chargins_at_ch_modus = [[[0 for j in range(len(Days))] for i in range(len(VehicleList[0]))] for ij in range(len(VehicleList))]

        #at_home_charging = [[0  for i in range(len(VehicleList[0]))] for ij in range(len(VehicleList))]

        for runs in range(len(VehicleList)):
            for Vehicle in VehicleList[runs]:
                not_at_home_charging_count = 0
                at_home_charger = 0
                count_day = 0
                for day in range(len(Days)):
                    count_ch_modus_trips = 0
                    for trip in Vehicle.total_trip_chain_list[day].trips:
                        if get_purposes_category(trip.purpose) == ChargingStationPlace.HOME:
                            count_ch_modus_trips+=1
                    number_of_trips_to_ch_modus[runs][Vehicle.ID][day] = count_ch_modus_trips

                    count_ch_sess = 0
                    count_ch_modus_chargings=0
                    for i in range(len(Vehicle.total_Charging_list[day])):
                        if i == len(Vehicle.total_Charging_list[day])-1:
                            #last charging session

                            if Vehicle.total_trip_chain_list[day].last_time_on_next_day:
                                continue
                            if Vehicle.total_Charging_list[day][-1].station.Place != "home":
                                not_at_home_charging_count +=1
                            else:
                                at_home_charger +=1


                        if Vehicle.total_Charging_list[day][i].station.Place== cmp_place or cmp_place== None:
                            count_ch_modus_chargings +=1
                            if Vehicle.total_Charging_list[day][i].start.to_timedelta().total_seconds() == 0:
                                start_at_zero = True
                            else:
                                start_at_zero = False
                            if not start_at_zero:
                                count_ch_sess += 1
                                if start_time_append:
                                # do not consider sessions starting at 0

                                    total_start_time_list.append(Vehicle.total_Charging_list[day][i].start.to_timedelta().total_seconds())
                            if ch_Duration_append:
                                energy = None
                                # check for sessions starting or ending at midnight (last overnight)
                                if Vehicle.total_Charging_list[day][i].end < nptime(23, 59, 59, 999999) and (not start_at_zero):
                                    ch_duration = (Vehicle.total_Charging_list[day][i].end - Vehicle.total_Charging_list[day][i].start).total_seconds()
                                    total_ch_duration_list.append(ch_duration)
                                    if compute_durations_per_interval:
                                        interval = int(Vehicle.total_Charging_list[day][
                                                           i].start.to_timedelta().total_seconds() / duration.total_seconds())
                                        durations_per_interval[interval].append(ch_duration)

                                    energy = Vehicle.total_Charging_list[day][i].compute_charged_energy(Vehicle)
                                    energy_per_charging_sessions[runs][Vehicle.ID][count_day].append(energy)
                                elif (not start_at_zero) and day + 1 < settingsContainer.getNumberOfDays():
                                    # charging lasts not longer than 24 hours !
                                    ch_duration = (Vehicle.total_Charging_list[day+1][0].end - Vehicle.total_Charging_list[day][i].start + datetime.timedelta(days = 1)).total_seconds()
                                    total_ch_duration_list.append(ch_duration)
                                    if compute_durations_per_interval:
                                        interval = int(Vehicle.total_Charging_list[day][
                                                           i].start.to_timedelta().total_seconds() / duration.total_seconds())
                                        durations_per_interval[interval].append(ch_duration)
                                    energy = Vehicle.total_Charging_list[day][i].compute_charged_energy(Vehicle) + Vehicle.total_Charging_list[day+1][0].compute_charged_energy(Vehicle)
                                    energy_per_charging_sessions[runs][Vehicle.ID][count_day].append(energy)
                                if compute_energies_per_interval and energy != None:
                                    interval = int(Vehicle.total_Charging_list[day][
                                                       i].start.to_timedelta().total_seconds() / duration.total_seconds())
                                    energies_per_interval[interval].append(energy)
                                if compute_energies != None and energy != None:
                                    energies.append(energy)
                                #else: # not considering last charging session or sessions starting at zero
                                # (pretend double added session, as entries starting at zero are either at the begining
                                # of the model or when continuing charging from previous day, which is checked by
                                # [day +1] -check in line 474 above from here
                            if ch_end_time_append:
                                # do not consider sessions ending at midnight, as these are the overnights sessions
                                if Vehicle.total_Charging_list[day][i].end < nptime(23, 59, 59, 999999):
                                    total_ch_end_time_list.append(Vehicle.total_Charging_list[day][i].end.to_timedelta().total_seconds())



                    number_of_chargins_at_ch_modus[runs][Vehicle.ID][day] = count_ch_modus_chargings
                    number_of_charging_sessions[runs][Vehicle.ID][count_day] = count_ch_sess
                    trip_distance_on_day[runs][Vehicle.ID][count_day] = sum([trip.distance for trip in Vehicle.total_trip_chain_list[day].trips])
                    number_of_trips[runs][Vehicle.ID][count_day] = Vehicle.total_trip_chain_list[day].length
                    for i in range(len(Vehicle.total_plugin_list[day])):

                        if i == len(Vehicle.total_plugin_list[day])-1:
                            #last charging session
                            if Vehicle.total_trip_chain_list[day].last_time_on_next_day:
                                continue
                        if len(Vehicle.total_plugin_list[day]) != len(Vehicle.total_Charging_list[day]):
                            #if len(Vehicle.total_Charging_list[day]) > 0:
                            if Vehicle.total_plugin_list[day][0][0] != nptime(0):
                                print("Error: assumption length equal, wrong")
                            elif i >0:
                                station_place = Vehicle.total_Charging_list[day][i-1].station.Place
                            elif i == 0:

                                jk = 1
                                if day-jk < 0:
                                    continue
                                else:
                                    while len(Vehicle.total_Charging_list[day-jk])==0:
                                        jk+=1
                                station_place = Vehicle.total_Charging_list[day-jk][-1].station.Place
                        else:
                            station_place = Vehicle.total_Charging_list[day][i].station.Place
                        if station_place == cmp_place or cmp_place== None:
                            if plugin_end_time_append:
                                # do not consider sessions ending at midnight, as these are the overnights sessions
                                # Vehicle - plugin list same length like charging list

                                if Vehicle.total_plugin_list[day][i][1] < nptime(23, 59, 59, 999999):
                                    total_plugin_end_time_list.append(
                                        Vehicle.total_plugin_list[day][i][1].to_timedelta().total_seconds())

                            if plugin_Duration_append:
                                if Vehicle.total_plugin_list[day][i][0].to_timedelta().total_seconds() == 0:
                                    plugin_start_at_zero = True
                                else:

                                    plugin_start_at_zero = False
                                # check for plug ins starting or ending at midnight (last overnight)
                                if Vehicle.total_plugin_list[day][i][1] < nptime(23, 59, 59, 999999) and (
                                        not plugin_start_at_zero):
                                    pl_dur = (Vehicle.total_plugin_list[day][i][1] -
                                                                       Vehicle.total_plugin_list[day][
                                                                           i][0]).total_seconds()
                                    total_plugin_duration_list.append(pl_dur)
                                    interval = int(Vehicle.total_plugin_list[day][
                                                                           i][0].to_timedelta().total_seconds() / duration.total_seconds())
                                    plugin_duration_per_interval[interval].append(pl_dur)

                                    #plug-out, duration, plug-in, power
                                    cluster = check_cluster(pl_dur, Vehicle.total_plugin_list[day][i][0])
                                    cluster_lists[cluster][0].append(pl_dur) #pl_duration
                                    cluster_lists[cluster][1].append(Vehicle.total_plugin_list[day][i][0].to_timedelta().total_seconds()) #plug-in time
                                    cluster_lists[cluster][2].append(Vehicle.total_plugin_list[day][i][1].to_timedelta().total_seconds()) #plug-out time
                                    cluster_lists[cluster][3].append(0) #power
                                    ##TODO: Methode, die plug-in session zu cluster hinzufügt:
                                    #https: // www.mdpi.com / 1996 - 1073 / 15 / 18 / 6575
                                    #plug-in duration=pd, plug-in: pi; plug-out: po
                                    #hier cluster 1,5, 6,7:
                                    #1: pi zwischen 4-10:00 und pd>5h; pd>pi-5h für 10-15:00 und pd<-pi +25
                                    #5:pi zwischen 10:00-24:00:
                                    #pi 10-15:00: pd<pi-5h 1) für 10<pi<13:00: pd>15-pi und 2) für 13:00<pi<24:00: pd>2h
                                    #pi 15:00-24: -8/9 pi +23,3333 <pd
                                    #7: pi 4-10: pd = 2 bisv5h; 10-13: pd > 2 & pd<-pi+15
                                    #6: pd  <2h


                                elif (not plugin_start_at_zero):
                                    day_to_check = day + 1
                                    while day_to_check < settingsContainer.getNumberOfDays() and Vehicle.total_plugin_list[day_to_check][
                                        0][1] == nptime(23, 59, 59, 999999):
                                        day_to_check += 1
                                    if day_to_check < settingsContainer.getNumberOfDays():
                                        pl_dur = (Vehicle.total_plugin_list[day_to_check][
                                                                               0][1] - Vehicle.total_plugin_list[day][i][0]
                                                                           + datetime.timedelta(
                                                    days=day_to_check-day)).total_seconds()
                                        
                                        total_plugin_duration_list.append(pl_dur)
                                        interval = int(Vehicle.total_plugin_list[day][
                                                                           i][0].to_timedelta().total_seconds() / duration.total_seconds())
                                        plugin_duration_per_interval[interval].append(pl_dur)

                                        if clustering_with_adapted_pl_dur:
                                            cluster = check_cluster(pl_dur-datetime.timedelta(days=day_to_check-day-1).total_seconds(), Vehicle.total_plugin_list[day][i][0])
                                            cluster_lists[cluster][0].append(pl_dur-datetime.timedelta(days=day_to_check-day-1).total_seconds())  # pl_duration
                                            cluster_lists[cluster][1].append(Vehicle.total_plugin_list[day][i][
                                                                                 0].to_timedelta().total_seconds())  # plug-in time
                                            cluster_lists[cluster][2].append(Vehicle.total_plugin_list[day_to_check][0][
                                                                                 1].to_timedelta().total_seconds())  # plug-out time
                                            cluster_lists[cluster][3].append(0)  #power # power
                                        else:
                                            cluster = check_cluster(pl_dur,
                                                                    Vehicle.total_plugin_list[day][i][0])
                                            cluster_lists[cluster][0].append(pl_dur)  # pl_duration
                                            cluster_lists[cluster][1].append(Vehicle.total_plugin_list[day][i][
                                                                                 0].to_timedelta().total_seconds())  # plug-in time
                                            cluster_lists[cluster][2].append(Vehicle.total_plugin_list[day_to_check][0][
                                                                                 1].to_timedelta().total_seconds())  # plug-out time
                                            cluster_lists[cluster][3].append(0)  # power # power
                                        ##TODO: Methode, die plug-in session zu cluster hinzufügt:
                                        # https: // www.mdpi.com / 1996 - 1073 / 15 / 18 / 6575
                                        # hier cluster 2,3,4, 6 (wenn day_to Check = day +1 und zeit sehr kurz danach
                                        #cluster 2: pi 3:30-13:30 und pd > -pi +33; 13:30 -18:00 pi und pd>19,5
                                        #für pi 3:30-18:00: pd < -pi +37,5
                                        #clzuster 3: pi 13:30-18:00 & pd < 19.5; 18:00-03:30: pd<-pi+37,5
                                        # 13:30-27:30: pd>-pi+33
                                        #cluster 4: rest, vor allem pd>-pi+37,5

                                else:
                                    if Vehicle.total_plugin_list[day][i][1] != nptime(23, 59, 59, 999999):
                                        if not plugin_start_at_zero:
                                            print("Error: plugin duration")
                                # else: # not considering last plugin session or sessions starting at zero
                                # (pretend double added session, as entries starting at zero are either at the begining
                                # of the model or when continuing charging from previous day, which is checked by
                                # while loop some lines above from here

                    count_day += 1
                not_at_home_charging_share[runs][Vehicle.ID]= not_at_home_charging_count / (not_at_home_charging_count + at_home_charger)


            print(count)
            count +=1

    if compute_start_time:
        for entry in total_start_time_list:
            interval = int(entry / duration.total_seconds())
            start_time_list[interval].append(entry)
        allLists.append(start_time_list)
        allLists.append(total_start_time_list)
    if compute_ch_end_time:
        for entry in total_ch_end_time_list:
            interval = int(entry / duration.total_seconds())
            ch_end_time_list[interval].append(entry)
        allLists.append(ch_end_time_list)
        allLists.append(total_ch_end_time_list)
    if compute_ch_duration:
        for entry in total_ch_duration_list:
            interval = int(entry/duration_duration.total_seconds())
            ch_duration_list[interval].append(entry)
        allLists.append(ch_duration_list)
        allLists.append(total_ch_duration_list)

    if compute_plugin_end_time:

        allLists.append(total_plugin_end_time_list)
    if compute_plugin_duration:

        allLists.append(plugin_duration_per_interval)
        allLists.append(total_plugin_duration_list)



    allLists.append(number_of_charging_sessions)
    allLists.append(trip_distance_on_day)
    allLists.append(energies)
    allLists.append(number_of_trips)
    allLists.append(not_at_home_charging_share)
    allLists.append(number_of_trips_to_ch_modus)
    allLists.append(number_of_chargins_at_ch_modus)

    if compute_durations_per_interval:
        #for interval in range(Number_of_intervals):
            #duration_list3 = list()
            #for entry in durations_per_interval[interval]:
               # interval2 = int(entry / duration_duration.total_seconds())
                #duration_list2[interval][interval2].append(entry)
        #allLists.append(duration_list2)
        allLists.append(durations_per_interval)

    if compute_energies_per_interval:
        allLists.append(energies_per_interval)

    if compute_cluster_list:
        allLists.append(cluster_lists)

    return allLists


def  check_cluster(pl_dur, pi):
   if pl_dur.__class__ == datetime.timedelta:
        pl_dur = pl_dur.total_seconds()
   pl_dur = pl_dur/3600
   if pi.__class__!=datetime.timedelta:
        pi = pi.to_timedelta().total_seconds()/3600
   else:
       pi = pi.total_seconds()/3600
   if pi <3.5:
        pi = pi+24
   if pl_dur <= 2:
       cluster = 6
   elif pl_dur <= 5:
       if (pi > 3.5 and pi <= 10):
        cluster = 7
       elif (pi > 10 and pi <= 13):
           if pl_dur <= -pi +15:
                cluster = 7
           else:
               cluster = 5
       elif  pi<=24 and -8/9 * pi +70/3 > pl_dur:
               cluster = 5

       else:
           cluster = 4
   elif pl_dur <= -pi +25:
       if pi <=10:
           cluster = 1
       else:
           if pl_dur > pi -5:
               cluster = 1
           elif pl_dur < -8/9 * pi +70/3:
               cluster = 5
           else:
               cluster = 4
   elif pl_dur > -pi +37.5:
       cluster = 4
   elif pi > 3.5 and pi <= 13.5 and pl_dur>-pi +33:
       cluster = 2
   elif pi>13.5 and pi <=18:
       if pl_dur > 19: #19,5
            cluster = 2
       elif pl_dur> -pi +31:#+33
            cluster = 3
       else:
           cluster = 4
   elif pl_dur>-pi +31 and pi > 18 and pi <=27.5:
       cluster = 3
   else:
       cluster = 4
   return cluster-1
                    # plug-in duration=pd, plug-in: pi; plug-out: po
                    # hier cluster 1,5, 6,7:
                    # 1: pi zwischen 4-10:00 und pd>5h; pd>pi-5h für 10-15:00 und pd<-pi +25
                    # 5:pi zwischen 10:00-24:00:
                    # pi 10-15:00: pd<pi-5h 1) für 10<pi<13:00: pd>15-pi und 2) für 13:00<pi<24:00: pd>2h
                    # pi 15:00-24: -8/9 pi +23,3333 >pd
                    # 7: pi 4-10: pd = 2 bisv5h; 10-13: pd > 2 & pd<-pi+15
                    # 6: pd  <2h

                    ##TODO: Methode, die plug-in session zu cluster hinzufügt:
                    # https: // www.mdpi.com / 1996 - 1073 / 15 / 18 / 6575
                    # hier cluster 2,3,4, 6 (wenn day_to Check = day +1 und zeit sehr kurz danach
                    # cluster 2: pi 3:30-13:30 und pd > -pi +33; 13:30 -18:00 pi und pd>19,5
                    # für pi 3:30-18:00: pd < -pi +37,5
                    # clzuster 3: pi 13:30-18:00 & pd < 19.5; 18:00-03:30: pd<-pi+37,5
                    # 13:30-27:30: pd>-pi+33
                    # cluster 4: rest, vor allem pd>-pi+37,5

if __name__ == "__main__":
    load_lama_data()