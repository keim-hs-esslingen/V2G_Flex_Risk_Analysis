from simulation_model.ChargingStationAndUser import *


def change_to_seconds(list_old):
    list_new = list()
    for entry in list_old:
        list_new.append(entry.total_seconds())
    return list_new

def compute_histogramm(list2, label, bins = 24, safename = "Ch_hist",time_adaption=True, plug_in_duration = False,
                        withlabels = True, plot1 = None):
    #for entry in list2:
    #plt.hist(list2, bins)
    #binned, dump = np.histogram(list2, bins, density=True)
    if time_adaption:
        if plug_in_duration:
            bins_lgt = bins
            bins = [ i * 10000 for i in range(0, bins)]

            #bins.append(3000000)

        else:
            bins_lgt = bins
            bins = [(24/(bins_lgt-1))*i*3600 for i in range(0, bins)]
            #bins.append(200000)


    else:
        bins_lgt = bins
        bins = [ i * 4 for i in range(0, bins)]
    binned2, dump2 = np.histogram(list2, bins)
    #print(binned2)
    summ=sum(binned2)
    binned3 = [binned2[i]/summ for i in range(bins_lgt-1)]
    if time_adaption:
        dump2 = [i for i in range(bins_lgt)]
    else:
        dump2 = bins


    #print(binned3)
    #plt.ylim(bottom=1e-10)
    if plot1 == None:
        if withlabels:
            plot1.plot(dump2[1:], binned3, label=label)
        else:
            plot1.plot(dump2[1:], binned3)
        #plt.plot([i for i in range(bins_lgt)], binned3, label = label)
        #plt.semilogy([i for i in range(bins)], binned, label = label)
        #plt.show()
        if safename!= None:
            plot1.savefig("figures/Charging_histogram/" + safename)
    else:
        if withlabels:
            plot1.plot(dump2[1:], binned3, label=label)
        else:
            plot1.plot(dump2[1:], binned3)
        # plt.plot([i for i in range(bins_lgt)], binned3, label = label)
        # plt.semilogy([i for i in range(bins)], binned, label = label)
        # plt.show()
        if safename != None:
            plot1.savefig("figures/Charging_histogram/" + safename)


def compare_histogramm(list1, list2, bins):
    binned1, dump = np.histogram(list1, bins, density=True)
    binned2, dump2 = np.histogram(list2, bins, density=True)
    dist_rel = list()
    dist_abs = list()
    #summ = sum(binned1)
    for i in range(len(binned1)):
        dist_abs_val = binned1[i] - binned2[i]
        dist_rel.append(dist_abs_val/binned1[i])
        dist_abs.append(dist_abs_val)
    return dist_rel, dist_abs

def compute_number_of_charging_sessions(ch_modus):

    savename = "dataCharging/alreadyLoaded/UK_charging_"
    ch_stations = open_file(savename + ch_modus + "_charging_stations" )
    ch_indeces = open_file(savename + ch_modus + "_charging_stations_indeces")
    all_rows = open_file(savename + ch_modus + "_whole")
    count_ch_station = 0
    number_of_sessions = list()
    energy_per_session  = list()
    larger_than_20sessions = list()
    for ch_station_indeces in ch_indeces:

        energy_per_session.append(list())
        counter = 0
        for index in ch_station_indeces:

            current_row = all_rows[index]
            if counter == 0:
                min = current_row[0]
                max = current_row[2]
            else:
                if current_row[0]<min:
                    min = current_row[0]
                if current_row[2]> max:
                    max = current_row[2]
            if current_row[-1] != ch_stations[count_ch_station]:
                print("Error: ch_station not correct")
            energy_per_session[count_ch_station].append(current_row[4])
            counter += 1

        total_time_period = max - min

        number_of_sess = len(ch_station_indeces)/(total_time_period.days+1)
        ch_sessions_per_day = number_of_sess

        #if len(ch_station_indeces)>=5 and total_time_period>datetime.timedelta(days =100) and ch_sessions_per_day<5:
        larger_than_20sessions.append(count_ch_station)

        number_of_sessions.append(ch_sessions_per_day)
        count_ch_station +=1
    save_list(number_of_sessions, "dataCharging/alreadyLoaded/UK_charging_" +ch_modus + "_number_of_charging_sessions_per_day")
    save_list(energy_per_session,
              "dataCharging/alreadyLoaded/UK_charging_" + ch_modus + "_e_per_session")
    save_list(larger_than_20sessions, "dataCharging/alreadyLoaded/UK_charging_" + ch_modus + "_20sessions_or_more")
    number_of_sessions2 = [number_of_sessions[i] for i in larger_than_20sessions]
    save_list(number_of_sessions2, "dataCharging/alreadyLoaded/UK_charging_" + ch_modus + "_number_of_charging_sessions_per_day_for_20sessions_or_more")