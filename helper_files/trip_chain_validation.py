import datetime
import os
import sys
import math
import numpy as np

# Ensure project root is on sys.path so package imports work when running this script
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import matplotlib.pyplot as plt

from SimulationTool.simulation import *
from analysis_methods.plot_Charging import *
from helper_files.variables import *


# Minimal helper: some repos expect a plot_pie_mobility helper; implement a simple one here
def plot_pie_mobility(data, Purposes, colors=None):
    """Simple pie-chart helper used by trip_chain_validation. Keeps labels and shows the plot."""
    plt.figure()
    if colors is None:
        colors = plt.cm.tab20.colors
    plt.pie(data, labels=Purposes, colors=colors[:len(data)], autopct='%1.1f%%')
    plt.axis('equal')
    plt.show()



def trip_chain_validation(withregionType = False, parking_times_plot = True,  plot_hist_distances = False,
                          plot_driving = True, print_parking_time_on_day = True, dist_of_Purposes = False,
                          share_of_Purposes = False, print_parking_duration = True):

    # Construct correct path to settings file from project root
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    settings_file = os.path.join(project_root, 'SimulationTool', 'SimulationTool_Settings.json')
    simulation_tool = start_tool(settings_file)
    strategies = [0, 1, 2]
    runs = 10
    # model already computed: only load it
    #simulation_tool.run_model(number_of_runs=runs, number_of_users=300, number_of_days=100)

    #simulation_tool.save_model()
    simulation_tool.load_model()

    # initialization
    share_purpose_per_ts = [[[0 for i in range(10)] for i in range(6 * 24)] for i in range(7)]
    share_purpose_per_ts2 = [[[0 for i in range(10)] for i in range(6 * 24)] for i in range(7)]
    share_drv_purpose_per_ts2 = [[[0 for i in range(10)] for i in range(6 * 24)] for i in range(7)]
    share_purpose_per_ts4 = [[[0 for i in range(10)] for i in range(6 * 24)] for i in range(7)]
    share_drv_purpose_per_ts = [[[0 for i in range(10)] for i in range(6 * 24)] for i in range(7)]

    dist_region_type = [list() for i in range(7)]
    dist_region_type2 = [list() for i in range(7)]
    dist_purposes = [0 for i in range(9)]
    dist_purposes2 = [list() for i in range(9)]

    mean_per_years = list()
    mean_per_trips = list()
    share_purposes = list()
    share_distpurposes = list()
    distPurposes = list()
    park_times = list()
    parking_durations = list()
    total_trips = 0
    mobility = 0
    parking_times = [datetime.timedelta(0) for i in range(10)]
    driving_times = datetime.timedelta(0)
    all_dists = list()

    for run in range(runs):
        for i in range(len(simulation_tool.model_data.VehicleLists[run])):

            idx = int(simulation_tool.model_data.VehicleLists[run][i].user.region_type) - 71
            location = 8  # starting at home
            start = int(settingsContainer.getStartDay()) - 1
            daytype = start

            # going through every simulated day
            for day in range(100):

                if daytype > 6:
                    daytype = 0

                value = 0
                # if there are trips for specified ev
                if simulation_tool.model_data.VehicleLists[run][i].total_trip_chain_list[day].length > 0:
                    count = 0
                    idx_start = 0
                    idx_end = idx_start  # ensure idx_end is defined even if no parking_times updates occur
                    for trip in simulation_tool.model_data.VehicleLists[run][i].total_trip_chain_list[day].trips:
                        if count == 0:
                            parking_times[location] += trip.departure.to_timedelta()

                            #parking_durations.append(trip.departure.to_timedelta())
                            if parking_times_plot:
                                idx_end = math.ceil(trip.departure.to_timedelta().total_seconds() / 600)
                                daytype2 = daytype
                                for index in range(idx_start, idx_end):
                                    if index >= 6 * 24:
                                        idx2 = index - 6 * 24
                                        daytype2 = daytype + 1
                                        if daytype2 > 6:
                                            daytype2 = 0
                                    else:
                                        idx2 = index

                                    share_purpose_per_ts[daytype2][idx2][location] += 1

                        value += trip.distance
                        idx_purpose = int(trip.purpose) - 1
                        dist_purposes[idx_purpose] += 1
                        if withregionType:
                            dist_region_type2[idx].append(trip.distance)
                        dist_purposes2[idx_purpose].append(trip.distance)

                        all_dists.append(trip.distance)
                        total_trips += 1
                        # parking
                        location = int(trip.purpose)
                        count += 1
                        minus = False
                        # ensure time_to_add exists before potential append
                        time_to_add = datetime.timedelta(0)
                        if count < simulation_tool.model_data.VehicleLists[run][i].total_trip_chain_list[day].length:
                            parking_durations.append(trip.staytime)
                            parking_times[location] += trip.staytime
                            if parking_times_plot:
                                idx_start = math.floor(trip.arrival.to_timedelta().total_seconds() / 600)
                                idx_end = math.ceil(
                                    (trip.staytime.total_seconds() + trip.arrival.to_timedelta().total_seconds()) / 600)



                        elif count == simulation_tool.model_data.VehicleLists[run][i].total_trip_chain_list[day].length:
                            if not simulation_tool.model_data.VehicleLists[run][i].total_trip_chain_list[
                                day].last_time_on_next_day:
                                parking_times[location] += datetime.timedelta(days=1) - trip.arrival.to_timedelta()
                                iiii= 1
                                while  day +iiii <len(simulation_tool.model_data.VehicleLists[run][i].total_trip_chain_list) and len(simulation_tool.model_data.VehicleLists[run][i].total_trip_chain_list[day+iiii].trips)==0:
                                    iiii=iiii+1
                                if day +iiii <len(simulation_tool.model_data.VehicleLists[run][i].total_trip_chain_list):
                                    time_to_add = datetime.timedelta(days=1) - trip.arrival.to_timedelta() + simulation_tool.model_data.VehicleLists[run][i].total_trip_chain_list[day+iiii].trips[0].departure.to_timedelta() + datetime.timedelta(days=iiii-1)
                                parking_durations.append(time_to_add)

                                if parking_times_plot:
                                    idx_start = math.floor(trip.arrival.to_timedelta().total_seconds() / 600)
                                    idx_end = 144

                            else:
                                iiii = 1
                                while  day + iiii < len(
                                        simulation_tool.model_data.VehicleLists[run][i].total_trip_chain_list) and len(simulation_tool.model_data.VehicleLists[run][i].total_trip_chain_list[
                                              day + iiii].trips) == 0 :
                                    iiii = iiii + 1
                                if day + iiii < len(
                                        simulation_tool.model_data.VehicleLists[run][i].total_trip_chain_list):
                                    time_to_add =  - trip.arrival.to_timedelta()+simulation_tool.model_data.VehicleLists[run][i].total_trip_chain_list[
                                                      day + iiii].trips[0].departure.to_timedelta() + datetime.timedelta(days=iiii - 1)
                                parking_durations.append(time_to_add)
                                parking_times[location] -= trip.arrival.to_timedelta()
                                if parking_times_plot:
                                    idx_start = 144
                                    idx_end = math.ceil(trip.arrival.to_timedelta().total_seconds() / 600) + 144
                                    minus = True
                        if parking_times_plot:
                            daytype2 = daytype
                            for index in range(idx_start, idx_end):
                                if index >= 6 * 24:
                                    idx2 = index - 6 * 24
                                    daytype2 = daytype + 1
                                    if daytype2 > 6:
                                        daytype2 = 0
                                else:
                                    idx2 = index
                                if minus:
                                    share_purpose_per_ts[daytype2][idx2][location] -= 1
                                else:
                                    share_purpose_per_ts[daytype2][idx2][location] += 1

                        driving_times += trip.duration
                        # determine time sections to add driving and parking times to abbildung 46 like picture share purpose per ts
                        index1start = math.floor(trip.departure.to_timedelta().total_seconds() / 600)
                        index1end = math.ceil(trip.arrival.to_timedelta().total_seconds() / 600)
                        daytype2 = daytype
                        for indexx in (index1start, index1end):
                            if indexx >= 6 * 24:
                                idx2 = indexx - 6 * 24
                                daytype2 = daytype + 1
                                if daytype2 > 6:
                                    daytype2 = 0
                            else:
                                idx2 = indexx
                            share_drv_purpose_per_ts[daytype2][idx2][location] += 1

                    mobility += 1
                else:
                    parking_times[location] += datetime.timedelta(days=1)
                    if parking_times_plot:
                        for indexx in range(0, 144):
                            share_purpose_per_ts[daytype][indexx][location] += 1

                if withregionType:
                    dist_region_type[idx].append(value)
                daytype += 1
    print("mean parking duration:"+str(np.mean(parking_durations)))
    save_list(parking_durations, 'dataCharging/modelData/parking_durations')
    if withregionType:
        for entry in dist_region_type:
            mean_per_year = np.array(entry).mean()  # *365.25
            # print(mean_per_year)
            mean_per_years.append(mean_per_year)
        for entry in dist_region_type2:
            mean_per_trip = np.array(entry).mean()  # *365.25
            # print(mean_per_year)
            mean_per_trips.append(mean_per_trip)
            #all_dists = list()

        print("mean distance per region type")
        print(mean_per_years)
        print("mean trip distance per region type")
        print(mean_per_trips)

    Purposes = ["Arbeit", "dienstlich", "Ausbildung", "Einkauf", "Erledigung", "Begleitung", "Freizeit", "nach Hause",
                "zurück"]
    if share_of_Purposes:
        for entry in dist_purposes:
            share_purposes.append(entry / total_trips)
        print("share of purposes on drives")
        print(share_purposes)
        plt.rc('font', size=25)
        # plt.rc('axes', labelsize=16)
        plt.bar(np.arange(len(Purposes)), share_purposes, align='center')
        plt.xticks([0, 1, 2, 3, 4, 5, 6, 7, 8], [1, 2, 3, 4, 5, 6, 7, 8, 9], fontsize=25)
        plt.ylabel('Anteil an allen Fahrten', fontsize=35)
        plt.xlabel('Fahrtzwecke', fontsize=35)
        plt.rc('axes', labelsize=25)

        plt.figure()

        share_purposes.__delitem__(-1)
        share_purposes.__delitem__(-1)
        share_purposes2 = [i / sum(share_purposes) for i in share_purposes]
        print("share purposes modified - without back and home drives ")
        print(share_purposes2)
        # print(sum(share_purposes2)) --> should be zero

    if dist_of_Purposes:
        for entry in dist_purposes2:
            distPurposes.append(np.mean(np.array(entry)))

        disPurposesss = [sum(entry) for entry in dist_purposes2]
        disPurposesss.__delitem__(-2)
        # disPurposesss.__delitem__(-1)
        disPurposesss = [entry / sum(disPurposesss) for entry in disPurposesss]

        Purposes.__delitem__(-2)
        # Purposes.__delitem__(-1)
        disPurp = [int(entry * 100) for entry in disPurposesss]
        print("dist purpses - mean on trips")
        print(distPurposes)
        print("dist purposes - share on total kilometres")
        print(disPurposesss)
        plot_pie_mobility(data=disPurp, Purposes=Purposes,
                          colors=["deepskyblue", "steelblue", "midnightblue", "darkred", "orangered", "yellowgreen",
                                  "gold", "grey"])
        plt.figure()

        plt.close()
        plt.figure()
        Purposes.__delitem__(-1)
        plot_pie_mobility(data=[27.0, 21.0, 1.0, 8.0, 13.0, 6.0, 24.0], Purposes=Purposes,
                          colors=["deepskyblue", "steelblue", "midnightblue", "darkred", "orangered", "yellowgreen",
                                  "gold"])
        plt.figure()

    if print_parking_time_on_day:
        total_time = datetime.timedelta(0)
        for entry in parking_times:
            time1 = entry / (runs * 300 * 100)
            park_times.append(time1)
            total_time += time1
        print("parking times")
        print(park_times)
        print(driving_times / (runs * 300 * 100))
        print(total_time + driving_times / (runs * 300 * 100))

    if plot_hist_distances:
        plt.hist(all_dists, cumulative=True, histtype='step', bins=200)
        plt.show()
        plt.close()
        print("quantiles of distance")
        print(np.quantile(np.array(all_dists), 0.97))
        print(np.quantile(np.array(all_dists), 0.93))
        print(np.quantile(np.array(all_dists), 0.5))
        print(np.quantile(np.array(all_dists), 0.33))
        print("mean distance")
        print(np.mean(np.array(all_dists)))
    print("mobility quote")
    print(mobility / (runs * 300 * 100))
    # visualize_energies()
    # testmompot()
    # myfile()

    # plot trip chain profile
    if plot_driving or parking_times_plot:

        for daytype in range(7):

            for loc in range(1, 10):
                if loc > 1:
                    for time in range(len(share_drv_purpose_per_ts[0])):
                        share_drv_purpose_per_ts2[daytype][time][loc] = share_drv_purpose_per_ts[daytype][time][loc] + \
                                                                        share_drv_purpose_per_ts2[daytype][time][
                                                                            loc - 1]
                        if loc == 9:
                            share_purpose_per_ts[daytype][time][0] = share_drv_purpose_per_ts2[daytype][time][loc]


        share_drv_purpose_per_ts3 = np.array(share_drv_purpose_per_ts2).transpose(0, 2, 1)
        if plot_driving:
            for daytype in range(7):

                for loc in range(1, 10):
                    plt.plot(range(len(share_drv_purpose_per_ts3[daytype][loc])),
                             share_drv_purpose_per_ts3[daytype][loc],
                             label=Purpose(loc))
                plt.figure()

        # plt.show()
        plt.figure()
    if parking_times_plot:
        Purposes = [
            "Driving",
            "Work",
            "Business",
            "Education",
            "Shopping",
            "Private errands",
            "Companionship",
            "Leisure",
            "Back to Previous",
            "Home",
        ]
        DayTypes = [
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
            "Sunday",
        ]

        for daytype in range(7):
            max_driving_share = 0
            for time in range(len(share_purpose_per_ts[0])):
                # change 8 and 9 column
                copy = share_purpose_per_ts[daytype][time][9]
                share_purpose_per_ts[daytype][time][9] = share_purpose_per_ts[daytype][time][8]
                share_purpose_per_ts[daytype][time][8] = copy
                for loc in range(10):
                    if loc > 0:
                        share_purpose_per_ts2[daytype][time][loc] = share_purpose_per_ts[daytype][time][loc] + \
                                                                    share_purpose_per_ts2[daytype][time][loc - 1]
                    else:
                        share_purpose_per_ts2[daytype][time][loc] = share_purpose_per_ts[daytype][time][loc]
                    if loc == 9:
                        share_purpose_per_ts4[daytype][time] = [
                            share_purpose_per_ts2[daytype][time][loc2] / share_purpose_per_ts2[daytype][time][9] for
                            loc2 in range(10)]
                        max_driving_share = max(max_driving_share, share_purpose_per_ts2[daytype][time][0] /
                            share_purpose_per_ts2[daytype][time][9])
            print("maximum driving share on ")
            print(daytype)
            print(max_driving_share)

        share_purpose_per_ts3 = np.array(share_purpose_per_ts4).transpose(0, 2, 1)
        plt.rc('font', size=16)
        fig, axes = plt.subplots(1, 7, sharey=True, figsize=(22, 10))
        #fig.suptitle('Standort der PKWs während durschnittlicher Tagesverläufe')
        # ax1.plot(x, y)
        # ax2.plot(x, -y)
        overnight_stays_not_at_home = list()
        for daytype in range(7):
            for loc in range(10):
                axes[daytype].plot(
                    range(len(share_purpose_per_ts3[daytype][loc])),
                    share_purpose_per_ts3[daytype][loc],
                    label=Purposes[loc]
                )
                axes[daytype].set_title(DayTypes[daytype], fontsize=25)
                axes[daytype].tick_params(axis='x', labelrotation=0, labelsize=20)

                axes[daytype].set_ylim(0, 0.6)
                if loc == 8:
                    overnight_stays_not_at_home.append(
                        share_purpose_per_ts3[daytype][loc][0] - share_purpose_per_ts3[daytype][0][0]
                    )
            # Set axis labels only for leftmost and bottom plots
            if daytype == 0:
                axes[daytype].set_ylabel('Cumulative share of EVs', fontsize = 28)
                axes[daytype].tick_params(axis = 'y', labelsize = 24)
            axes[daytype].set_xlabel('Time of day', fontsize = 28)
            # Set x-axis ticks at 36, 72 and 108
            axes[daytype].set_xticks([36, 72, 108])
            # Remove x-axis tick labels
            axes[daytype].set_xticklabels([])
            axes[daytype].grid(True, axis='both', alpha=0.3)

        # Legend in upper center area
        axes[0].legend(
            title="Driving/Parked after trip purpose",
            loc='upper center',
            ncol = 5,
            bbox_to_anchor=(4, 0.95),
            frameon=True,
            fontsize=20,
            title_fontsize=20,
        )
        fig.subplots_adjust(left=0.08, right=0.97, bottom=0.16, top=0.90, wspace=0.15)

        #plt.xticks( [0, 72], ["00:00 Uhr", "12:00 Uhr"], fontsize=25)
        plt.show()
        print(overnight_stays_not_at_home)

def cluster_comparison():
    sim_tool = start_tool()
    if False:
            # running model without cluster --> setting with_cluster in settings.py to false line 23

            sim_tool.run_model(100, 300, "01", 10)  # 0 dran
            sim_tool.save_model("models/charging_profile-validation/Szenario-PL3a")
            sim_tool.load_model("models/charging_profile-validation/Szenario-PL3a")
            save_list(sim_tool.model_data.VehicleLists, "VehicleList2")
            VehicleList_old = open_file('VehicleList2')
            all_lists_name = "allLists" + str("home")
            # --> already computed
            allLists = compute_histogram_lists(sim_tool.model_data.VehicleLists, "home")
            save_list(allLists, all_lists_name)

    if False:
            # running model with cluster--setting to tru in settings.py line 750
            #with_cluster = True
            sim_tool.run_model(100,100,"01",2) #0 dran
            sim_tool.save_model("models/charging_profile-validation/Szenario-PL3b")
            sim_tool.load_model("models/charging_profile-validation/Szenario-PL3b")
            #with_cluster = True
            save_list(sim_tool.model_data.VehicleLists,"models/charging_profile-validation/VehicleList2")
            all_lists_name = "models/charging_profile-validation/allLists" + str("home")
            # --> already computed
            allLists = compute_histogram_lists(sim_tool.model_data.VehicleLists, "home")
            save_list(allLists, all_lists_name)

    plot_number_of_charging_sessions(with_other_categories=False)

if __name__ == "__main__":
    trip_chain_validation()