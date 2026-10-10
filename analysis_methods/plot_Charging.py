import matplotlib.pyplot as plt

from analysis_methods.Charging_statistic import *
from analysis_methods.Charging_profile import *
from analysis_methods.load_data import *


def plot_last_soc(ev_id, soc_during_day):
    last_socs = list()
    for ii in range(len(soc_during_day)):
        if len(soc_during_day[ii][ev_id].SOC) > 0:
            last_socs.append(soc_during_day[ii][ev_id].SOC[-1])
    plt.plot(np.array(last_socs))  # range(len(soc_during_day),
    plt.show()


def plot_Plugin():
    alphas = [0.1,0.3,1,3,10,100]
    need_SOC = 40
    number_count = 100
    current_SOC = [i/number_count for i in range(100*number_count)]
    current_SOC2 = current_SOC[need_SOC*number_count-1:-1]
    labels = list()
    for i in range(len(alphas)):
        p = list()
        p = [1 for i in range(need_SOC * number_count)]
        for c_SOC in current_SOC2:
            p.append(1 - pow(((c_SOC - need_SOC) / (100 - need_SOC)), alphas[i]))
        #for p3 in p2:
         #   p.append(p3)
        plt.plot(current_SOC, p)
        labels.append("alpha="+str(alphas[i]))
    plt.legend(labels)
    plt.xlabel("Ladezustand: State of Charge (in Prozent)")
    plt.ylabel("Wahrscheinlichkeit")
    plt.show()

def plot_histogramm(pos):
    #UserList, VehicleList, DayList = run(NumberOfDays, NumberOfUsers, DayType.MONDAY, NUMBEROFRUNS)
    # saving List
    #save_list('models/charging_profile-validation')
    # open list
    VehicleList_old = open_file('models/charging_profile-validation')

    allLists = compute_histogram_lists(VehicleList_old)
    save_list(allLists, "dataCharging/modelData/allLists")
    allLists = open_file("dataCharging/modelData/allLists")
    compute_histogramm(allLists[pos], safename="Ch_hist_model")


def plot_quantiles(x, y):
    plt.semilogy(x, y, label="relative error")
    y_positive = [abs(dist) for dist in y]
    mean_rel = np.mean(y)
    plt.axhline(y=mean_rel, linestyle="--", label="mean error")
    print(mean_rel)
    quantiles = [0.05, 0.25, 0.5, 0.75, 0.95]
    for quant in quantiles:
        q = np.quantile(y, quant)
        plt.axhline(y=q, linestyle="--", label="quantile" + str(quant))
        print(q)
    #plt.show()

def print_quantiles(list2):
    mean_rel = np.mean(list2)
    print(mean_rel)
    quantiles = [0.05, 0.25, 0.5, 0.75, 0.95]
    for quant in quantiles:
        q = np.quantile(list2, quant)
        #plt.axhline(y=q, linestyle="--", label="quantile" + str(quant))
        print(q)
def plot_UK_Data_histogram_start_time():
    start_times = open_file("UK_chargingstart_times")
    compute_histogramm(change_to_seconds(start_times), safename="Ch_hist_UKData")


def number_of_charging_sessions_model(ch_modus, path = "dataCharging/modelData/" ):
        # UserList, VehicleList_old, DayList = run(100, 300, DayType.MONDAY, runs)
        # save_list(VehicleList_old, 'files_not_to_safe_in_git/VehicleList6')
        #allLists = compute_histogram_lists(VehicleList_old, ch_modus)
        allLists = open_file(path+"allLists"+ch_modus)
        # save_list(allLists, all_lists_name)
        VehicleList_old = open_file(path+"VehicleList2")
        number_of_users = len(allLists[9][0])
        number_of_sessions = [np.mean(np.array(allLists[9]).transpose(1,2,0)[i].flatten()) for i in range(number_of_users)]

        number_of_users = len(allLists[9][0])

        cluster1 = list()
        cluster2 = list()
        cluster3 = list()

        for i in range(number_of_users):
            if VehicleList_old[0][i].user.cluster == Cluster.Cluster1:
                cluster1.append(i)
            elif VehicleList_old[0][i].user.cluster == Cluster.Cluster2:
                cluster2.append(i)
            else:
                cluster3.append(i)


        save_list(number_of_sessions , "dataCharging/modelData/number_of_sessions_model")
        save_list(cluster1, "dataCharging/modelData/cluster1")
        save_list(cluster2, "dataCharging/modelData/cluster2")
        save_list(cluster3, "dataCharging/modelData/cluster3")

        #allLists = open_file("files_not_to_safe_in_git/allLists4")
        if False:
            print(np.mean(np.array(allLists[9]).flatten()))
            #x,y = np.histogram([np.mean(np.array(allLists[9]).transpose(1,2,0)[i].flatten()) for i in range(NumberOfUsers)], bins = 20)
            plt.hist([np.mean(np.array(allLists[9]).transpose(1,2,0)[i].flatten()) for i in range(number_of_users)], bins = 20)
            plt.show()
            print(np.histogram([np.mean(allLists[9][0][i]) for i in range(number_of_users)]))

            print(np.array(allLists[8]).flatten()/(NUMBEROFRUNS*number_of_users*NumberOfDays))
            print(np.quantile(np.array(allLists[9]).flatten(), 0.05))
            print(np.quantile(np.array(allLists[9]).flatten(), 0.25))
            print(np.quantile(np.array(allLists[9]).flatten(), 0.5))
            print(np.quantile(np.array(allLists[9]).flatten(), 0.75))
            print(np.quantile(np.array(allLists[9]).flatten(), 0.95))
            print(np.quantile(np.array(allLists[9]).flatten(), 0.99))
        #print(np.mean(np.array(allLists[10]).flatten()))
        return number_of_sessions


def number_of_charging_sessions_UK(ch_modus):
    # load_UK_Charging_data(ch_modus, True)
    compute_number_of_charging_sessions(ch_modus)

    number_of_charging2 = open_file("dataCharging/alreadyLoaded/UK_charging_" + ch_modus + "_number_of_charging_sessions_per_day")
    # energy_per_session = open_file("files_not_to_safe_in_git/UK_charging" + ch_modus + "_e_per_session")
    twentysessions_or_more = open_file("dataCharging/alreadyLoaded/UK_charging_" + ch_modus + "_20sessions_or_more")
    #number_of_charging = [number_of_charging2[i] for i in twentysessions_or_more]
    number_of_charging = open_file(
        "dataCharging/alreadyLoaded/UK_charging_" + ch_modus + "_number_of_charging_sessions_per_day_for_20sessions_or_more")
    return number_of_charging

def plot_number_of_charging_session_histogram(label, list, bins):
    bins_lgt = len(bins)
    binned, dumped = np.histogram(list, bins=bins)
    summ = sum(binned)
    binned3 = [binned[i] / summ for i in range(bins_lgt-1)]
    # plt.ylim(bottom=1e-10)
    last_bin = bins[-1]
    bins.__delitem__(-1)
    if label == "Cluster1" or label == "Cluster2" or label == "Cluster3":
        alpha = 0.5
    else:
        alpha = 1
    plt.plot([i for i in bins], binned3, "-",  label=label, alpha = alpha)
    bins.append(last_bin)


def compare_number_charging_sessions(ch_modus, bins = 50, withcluster = False):
    plt.xlim(right=3)
    number_ch_sess_UK = number_of_charging_sessions_UK(ch_modus)
    number_ch_sess_model_without_cluster = number_of_charging_sessions_model(ch_modus)
    if withcluster:
        number_ch_sess_model_cluster = number_of_charging_sessions_model(ch_modus, 'models/charging_profile-validation/')


    #compute_histogramm(number_ch_sess_UK, "data", bins, None, time_adaption = False)
    bins = [0.05 * i for i in range(60)]
    label = "reale Daten"
    plot_number_of_charging_session_histogram(label, number_ch_sess_UK, bins)

    #plt.hist(number_ch_sess_UK, bins = bins)
    label = "Szenario PL3a"
    plot_number_of_charging_session_histogram(label, number_ch_sess_model_without_cluster, bins)
    if withcluster:
        label = "Szenario PL3b"
        plot_number_of_charging_session_histogram(label, number_ch_sess_model_cluster, bins)

    plt.ylabel("relative Häufikeit")
    plt.xlabel("Anzahl an Ladevorgängen je Tag")
    #plt.show()
    if withcluster:
        cluster1 = open_file("dataCharging/modelData/cluster1")
        cluster2 = open_file("dataCharging/modelData/cluster2")
        cluster3 = open_file("dataCharging/modelData/cluster3")
    number_ch_sess_model1 = list()
    number_ch_sess_model2 = list()
    number_ch_sess_model3 = list()
    if withcluster:
        for i in cluster1:
            number_ch_sess_model1.append(number_ch_sess_model_cluster[i])
        for i in cluster2:
            number_ch_sess_model2.append(number_ch_sess_model_cluster[i])
        for i in cluster3:
            number_ch_sess_model3.append(number_ch_sess_model_cluster[i])
        plot_number_of_charging_session_histogram("Cluster1", number_ch_sess_model1, bins)
        plot_number_of_charging_session_histogram("Cluster2", number_ch_sess_model2, bins)
        plot_number_of_charging_session_histogram("Cluster3", number_ch_sess_model3, bins)
        plt.legend()
        plt.show()
        print("cluster1")
        print_quantiles(number_ch_sess_model1)
        print("cluster2")
        print_quantiles(number_ch_sess_model2)
        if user_Cluster1_share+user_Cluster2_share<1:
            print("cluster3")
            print_quantiles(number_ch_sess_model3)
    #plt.figure()
    #plt.hist(number_ch_sess_UK, bins=bins, density = True)
    # compute_histogramm(number_ch_sess_model, "model", bins, None, time_adaption = False)
    #plt.hist(number_ch_sess_model, bins=bins, densitiy = True)
    #plt.show()

    #error
    #plt.figure()
    #dist_rel, dist_abs = compare_histogramm(number_ch_sess_UK, number_ch_sess_model, bins)


    #plot_quantiles(x=[i / 2 for i in range(bins)], y=dist_abs)
    #plt.ylim(bottom=1e-16)
    #plt.show()

    print("Quantiles model")
    print(np.quantile(number_ch_sess_model_without_cluster, 0.05))
    print(np.quantile(number_ch_sess_model_without_cluster, 0.25))
    print(np.quantile(number_ch_sess_model_without_cluster, 0.5))
    print(np.quantile(number_ch_sess_model_without_cluster, 0.75))
    print(np.quantile(number_ch_sess_model_without_cluster, 0.95))
    print(np.quantile(number_ch_sess_model_without_cluster, 0.99))
    print("mean:", np.mean(number_ch_sess_model_without_cluster))

    if withcluster:
        print("cluster model")
        print(np.quantile(number_ch_sess_model_cluster, 0.05))
        print(np.quantile(number_ch_sess_model_cluster, 0.25))
        print(np.quantile(number_ch_sess_model_cluster, 0.5))
        print(np.quantile(number_ch_sess_model_cluster, 0.75))
        print(np.quantile(number_ch_sess_model_cluster, 0.95))
        print(np.quantile(number_ch_sess_model_cluster, 0.99))
        print("mean:", np.mean(number_ch_sess_model_cluster))

    print("Quantiles UK data")
    print(np.quantile(number_ch_sess_UK, 0.05))
    print(np.quantile(number_ch_sess_UK, 0.25))
    print(np.quantile(number_ch_sess_UK, 0.5))
    print(np.quantile(number_ch_sess_UK, 0.75))
    print(np.quantile(number_ch_sess_UK, 0.95))
    print(np.quantile(number_ch_sess_UK, 0.99))
    print("mean:", np.mean(number_ch_sess_UK))

def plot_histogramm_comparison(modus, ch_modus = "home", plot_alone = False,plug_in_duration = False,withlabels = False,
                               filename_UK = "electric-chargepoint-analysis-2017-raw-domestics-data.csv",
                               bins = 24, interval = 0, plot1 = None, allLists= None, load_data = False,
                               compute_Vehicle_list = False, save_computations = False, compute_all_lists = False):





    if ch_modus == "_Obelis":
        ch_modus2 = "work"
        file_start = "Obelis_"
    elif ch_modus == "lama":
        #TODO: load_data methode für lama Daten: muss DAteien erzeugen analog zu UK_Charging und Histogramm-Vergleich ermöglichen.
        #Aufgabe: load lama anaolog zu UK Charging:
        #Anforderungen an load lama: lädt Lama-Daten und speichert  die Listen als Dateien analog zu load_UK_Charging mit Endungen:
        # whole (alle Listen),   "_start_times" (Ladestartzeiten), "_ch_end_times" (Ladeendzeiten),+ "_ch_durations" (Ladedauern),
        # "_plugin_durations" (Plug-In-Dauern),"_plugin_end_times" (Plug-In-Endzeiten), "_charging_stations" (Ladestationen),
        # "_charging_stations_indeces: als leere list(), da nicht notwenidg ,"_energy_per_sessions"(geladene Energie)
        # ,"_energies_per_intervals" (geladene Energie je Zeitintervall,"_ch_durations_per_intervals","_pl_durations_per_intervals" ) --> Diese drei Listen je Zeitintervall erstmal nicht wichtig!

        # load UK_Charging Data lädt UK_Data von andrere csv Datei (für Ladedaten an Ladestationen zu Hause). Wir wollen Ladedaten bei der Arbiet (modus = "work" bei Simulation)
        # Hierfür gibt es die Daten des Projekts "Lama". Lamadaten müssen eingelesen werden und die Listen entpsrechend befüllt werden, sodass diese Listen mit den Dateinamen von dieser Methode geöffent werden können
        #Anschließend können Histogramme mi Lamadaten und Daten aus der Simulation verglichen werden. Modus ist immer "work" (Daten zum Laden bei der Arbeit).
        ch_modus = "work"
        ch_modus2 = "work"
        file_start = "lama_"
    else:
        ch_modus2 = ch_modus
        file_start = "UK_Charging_"

    if load_data:
        if ch_modus == "lama":
            load_lama_data(ch_modus=ch_modus, filename=filename_UK, compute_charging_session=True)
        else:
            load_UK_Charging_data(ch_modus=ch_modus, filename=filename_UK, compute_charging_session=True)
    print("list loaded")
    if compute_Vehicle_list:

        UserList, VehicleList, DayList = run(NumberOfDays, NumberOfUsers, DayType.MONDAY, NUMBEROFRUNS)
        #saving List
        if save_computations:
            save_list(VehicleList, 'VehicleList')
    else:
        VehicleList = open_file('dataCharging/modelData/VehicleList2')

    all_lists_name = "dataCharging/modelData/allLists" + str(ch_modus)
    if not compute_all_lists:
         allLists = open_file(all_lists_name)
    else:
        #--> already computed
        allLists = compute_histogram_lists(VehicleList, ch_modus2)
        if save_computations:
            save_list(allLists, all_lists_name)


    open_filename = 'dataCharging/alreadyLoaded/' +file_start + ch_modus +"_" +modus +"s"
    # pos for default case, that all parameters to compute corresponding lists are set to true in compute_histogramm_lists
    if modus == "start_time":
        data = open_file( open_filename)
        pos = 1
    elif modus == "ch_end_time":
        data = open_file( open_filename)
        pos = 3
    elif modus == "ch_duration":
        data = open_file( open_filename)
        pos = 5
    elif modus == "plugin_end_time":
        data = open_file( open_filename)
        pos = 6
    elif modus == "plugin_duration":
        data = open_file( open_filename)
        pos = 8
    elif modus == "energy_per_session":
        data = open_file(open_filename)
        pos = 11
    elif modus == "ch_durations_per_interval":
        data = open_file(open_filename)
        pos = 16

    elif modus == "energies_per_interval":
        data = open_file(open_filename)
        pos = 17
    else:
        print("Error: wrong modus, histogram comparison")

    if pos == 16 or pos == 17:
        data = data[interval]
        data_model = allLists[pos][interval]
    else:
        data_model = allLists[pos]

    if pos == 11 or pos == 17:
        data_real = data
        compute_histogramm(data_model, "Modell", bins, None, time_adaption=False, withlabels=withlabels, plot1 = plot1)
        compute_histogramm(data_real, "reale Daten", bins, None, time_adaption=False, withlabels=withlabels, plot1 =plot1)
    else:
        data_real = change_to_seconds(data)

        compute_histogramm(data_model, "Modell", bins, None, plug_in_duration=plug_in_duration, withlabels=withlabels, plot1 =plot1)
        compute_histogramm(data_real, "reale Daten", bins, None, plug_in_duration=plug_in_duration, withlabels=withlabels, plot1 =plot1)

    if plot_alone:
        plt.legend()
        plt.ylabel("relative Häufigkeit")
        xlabel = str(modus)+"in hours"
        plt.xlabel(xlabel)
        plt.figure()
        dist_rel, dist_abs = compare_histogramm(data_model, data_real, bins)

        plot_quantiles(x = [i/2 for i in range(bins)], y = dist_abs)
        plt.ylim(bottom = 1e-16)
        plt.show()



def plot_ch_profilesanderrorsUkandmodel():
    plt.rc('font', size=20)
    # load UK data already computed --> saved already as file
    # load_UK_Charging_data(compute_charging_session=True)

    kinds = ["Home", "Work", "Public"]

    # method to compute profile:  "start_time":
    day_profiles = compute_ch_profile(kinds)
    #save_list(day_profiles, "dataCharging/modelData/day_profiles")
    # already saved, so only open computed file
    #day_profiles = open_file("dataCharging/modelData/day_profiles")

    day_profiles[0].visualize_profile()
    day_profiles[1].visualize_profile()
    day_profiles[2].visualize_profile()

    # UK profile already saved in file
    #day_profile = compute_UK_ch_profiles(8, "dataCharging/alreadyLoaded//UK_charging_home_whole")
    #save_list(day_profile, "dataCharging/alreadyLoaded//day_profile_UK_home")
    day_profile = open_file("dataCharging/alreadyLoaded/day_profile_UK_home")

    #dayprofile2 = compute_UK_ch_profiles(8, "dataCharging/alreadyLoaded///UK_charging_public_whole")
    #save_list(dayprofile2, "dataCharging/alreadyLoaded//day_profile_UK_public")
    dayprofile2 = open_file("dataCharging/alreadyLoaded/day_profile_UK_public")

    day_profile.visualize_profile()
    dayprofile2.visualize_profile()
    #plt.legend(labels = [kinds[0]+" - Modell", kinds[1]+" - Modell", kinds[2]+" - Modell", "Zu Hause - reale Daten", "öffentlich - reale Daten"])
    plt.legend(labels=["Zu Hause - Modell", "öffentlich - Modell", "bei der Arbeit - Modell", "Zu Hause - reale Daten",
                       "öffentlich - reale Daten"], loc = "upper right")
    plt.xlabel("Zeit in h")
    plt.ylabel("Leistung relativ zur gesamten geladenen Leistung ")
    plt.show()
    plt.figure()
    dist_rel, dist_abs = day_profiles[0].compare_profiles(day_profile)

    plt.plot([i * (day_profile.interval_size.total_seconds() / 3600) for i in range(day_profile.number_of_intervals)],
             dist_abs, label="relative error")

    dist_abs_positive = [abs(dist) for dist in dist_abs]
    print("mean error:")
    print(np.mean(dist_abs_positive))

    mean_rel = np.mean(dist_abs)
    plt.axhline(y=mean_rel, linestyle="--", label="mean error")
    print(mean_rel)
    quantiles = [0.05, 0.25, 0.5, 0.75, 0.95]
    for quant in quantiles:
        q = np.quantile(dist_abs, quant)
        plt.axhline(y=q, linestyle="--", label="quantile" + str(quant))
        print(q)
    plt.show()

def plot_number_of_charging_sessions(with_other_categories = False):
        plt.rc('font', size=15)
        print_number_of_trips = False
        #UserList, VehicleList_old, DayList = run(100, 300, DayType.MONDAY, runs)
        #save_list(VehicleList_old, 'files_not_to_safe_in_git/VehicleList6')
        #VehicleList_old = open_file('VehicleList2')
        all_lists_name = "allLists" + str("home")
        # --> already computed
        #allLists = compute_histogram_lists(VehicleList_old, "home")
        #save_list(allLists, all_lists_name)
        allLists = open_file(all_lists_name)

        bins = [0.1 * i for i in range(50)]
        label = "UK"

        if with_other_categories:
            number_of_users = len(allLists[12][0])
            print("chargings at public")
            public = number_of_charging_sessions_model("public")
            print(np.mean(public))
            VehicleList_old = open_file('VehicleList2')
            allLists = compute_histogram_lists(VehicleList_old, "work")

            work = number_of_charging_sessions_model("work")
            print("chargings at work")
            print(np.mean(work))
        number_of_users = len(allLists[12][0])
        compare_number_charging_sessions("home", bins = 100)

        print("chargings at home")
        number_of_chargings_at_home = np.array(allLists[15]).flatten()
        print(np.mean(number_of_chargings_at_home))
        plt.hist(number_of_chargings_at_home, bins=20)
        plt.show()
        plt.figure()
        print_quantiles(number_of_chargings_at_home)
        print("number_of_chargings_at home2")
        number_of_chargings_at_home2 = np.array(
            [np.mean(np.array(allLists[15]).transpose(1, 2, 0)[i].flatten()) for i in range(number_of_users)])
        plt.hist(number_of_chargings_at_home2, bins=20)
        plt.show()
        plt.figure()

        print_quantiles(number_of_chargings_at_home2)
        print("number of charging sessions")
        plot_number_of_charging_session_histogram(label, number_of_chargings_at_home, bins)

        plt.show()

        plt.figure()

        if print_number_of_trips:
            number_of_trips = np.array(allLists[12]).flatten()
            print("number_of trips")
            plt.hist(number_of_trips, bins=20)
            plt.show()
            plt.figure()
            print("number_of_trips2")
            number_of_trips2 = np.array(
                [np.mean(np.array(allLists[12]).transpose(1, 2, 0)[i].flatten()) for i in range(number_of_users)])
            plt.hist(number_of_trips2, bins=20)
            plt.show()
            plt.figure()
            print_quantiles(number_of_trips2)

            print("trips to home")
            number_of_trips_to_home = np.array(allLists[14]).flatten()
            plt.hist(number_of_trips_to_home, bins=20)

            plt.show()
            print_quantiles(number_of_trips_to_home)
            print("trips to home2")
            number_of_trips_to_home2 = np.array(
                [np.mean(np.array(allLists[14]).transpose(1, 2, 0)[i].flatten()) for i in range(number_of_users)])
            plt.hist(number_of_trips_to_home2, bins=20)
            plt.show()
            plt.figure()
            print_quantiles(number_of_trips_to_home2)

        print("not at home charging share")
        number_of_users = len(allLists[13][0])
        not_at_home_charging_share = np.array(allLists[13]).flatten()
        print(np.mean(not_at_home_charging_share))
        plt.hist(not_at_home_charging_share, bins=20)


        plt.show()
        plt.figure()

def plot_energy_comparision():
        print("------------energy comparision:")
        modus = "energies_per_interval"
        mean=list()
        mean_length = list()
        mean_distance = list()
        for ch_modus in ["public", "home"]:
            print("--------------", ch_modus)
            # open list
            # load_UK_Charging_data(ch_modus=ch_modus, filename=filename_UK, compute_charging_session=True)
            VehicleList_old = open_file('models/charging_profile-validation/VehicleList2')
            if ch_modus == "_Obelis":
                ch_modus2 = "work"
                file_start = "Obelis_"
            else:
                ch_modus2 = ch_modus
                file_start = "UK_Charging_"
            all_lists_name = "dataCharging/modelData/allLists" + str(ch_modus2)
            # --> already computed
            allLists = compute_histogram_lists(VehicleList_old, ch_modus2)
            save_list(allLists, all_lists_name)
            allLists = open_file(all_lists_name)

            open_filename = 'dataCharging/alreadyLoaded/' + file_start + ch_modus + "_" + modus + "s"
            data_real = open_file(open_filename)
            data_model= allLists[17]
            means_per_interval_model = list()
            means_per_interval_real = list()
            for interval in range(len(data_model)):
                means_per_interval_model.append(np.mean(np.array(data_model[interval])))
                means_per_interval_real.append(np.mean(np.array(data_real[interval])))
            print("plotting mean energy charged in sessions at times:")
            plt.plot(range(len(data_model)), means_per_interval_real, label = "real")
            plt.plot(range(len(data_model)), means_per_interval_model, label = "model")
            plt.legend()
            plt.show()
            plt.figure()

            print("average energy per session:")
            modus = "energy_per_session"
            open_filename = 'dataCharging/alreadyLoaded/' + file_start + ch_modus + "_" + modus + "s"
            data_real = open_file(open_filename)
            data_model = allLists[11]
            print("real: ",np.mean(np.array(data_real)))
            print("model: ", np.mean(np.array(data_model)))
            mean.append(np.mean(np.array(data_model)))
            mean_length.append(len(data_model))
            mean_distance.append(np.mean(np.array(allLists[10]).flatten()))
        ch_modus2 = "work"
        all_lists_name = "dataCharging/modelData/allLists" + str(ch_modus2)
        # --> already computed
        allLists = compute_histogram_lists(VehicleList_old, ch_modus2)
        save_list(allLists, all_lists_name)
        allLists = open_file(all_lists_name)
        data_model = allLists[11]
        mean.append(np.mean(np.array(data_model)))
        mean_length.append(len(data_model))
        mean_distance.append(np.mean(np.array(allLists[10]).flatten()))
        print("total mean energy charged")
        print(sum([mean[i]*mean_length[i] for i in range(3)])/(sum(mean_length)))
        print("total mean distance driven")
        print(sum(mean_distance))

def plot_ch_durations_per_interval():
    print("------------comparision of ch_durations per interval:")
    modus = "ch_durations_per_interval"
    #VehicleList_old = open_file('models/charging_profile-validation/VehicleList2')
    for ch_modus in ["public", "home"]:
        print("--------------", ch_modus)
        # open list
        # load_UK_Charging_data(ch_modus=ch_modus, filename=filename_UK, compute_charging_session=True)

        if ch_modus == "_Obelis":
            ch_modus2 = "work"
            file_start = "Obelis_"
        else:
            ch_modus2 = ch_modus
            file_start = "UK_Charging_"
        all_lists_name = "dataCharging/modelData/allLists" + str(ch_modus2)
        # --> already computed
        # allLists = compute_histogram_lists(VehicleList_old, ch_modus2)
        # save_list(allLists, all_lists_name)
        allLists = open_file(all_lists_name)

        open_filename = 'dataCharging/alreadyLoaded/' + file_start + ch_modus + "_" + modus + "s"

        data_real = open_file(open_filename)
        data_model = allLists[16]
        means_per_interval_model = list()
        means_per_interval_real = list()
        for interval in range(len(data_model)):
            means_per_interval_model.append(np.mean(np.array(data_model[interval])))
            means_per_interval_real.append(np.mean(change_to_seconds(np.array(data_real[interval]))))

        print("plotting mean charging duration at times:")
        plt.plot(range(len(data_model)), means_per_interval_real, label="real")
        plt.plot(range(len(data_real)), means_per_interval_model, label="model")
        plt.legend()
        plt.show()
        plt.figure()

        print("average charging time per session:")
        modus2 = "ch_duration"
        open_filename = 'dataCharging/alreadyLoaded/' + file_start + ch_modus + "_" + modus2 + "s"
        data_real = open_file(open_filename)
        data_model = allLists[5]
        print("real:", np.mean(np.array(data_real).flatten()))
        print("model:", np.mean(np.array(data_model).flatten()) / 3600)


def plot_pl_durations_per_interval():
        print("------------comparision of pl_durations per interval:")
        modus = "pl_durations_per_interval"
        for ch_modus in ["home", "public"]:
            print("--------------", ch_modus)
            # open list
            # load_UK_Charging_data(ch_modus=ch_modus, filename=filename_UK, compute_charging_session=True)
            VehicleList_old = open_file('models/charging_profile-validation/VehicleList2')
            if ch_modus == "_Obelis":
                ch_modus2 = "work"
                file_start = "Obelis_"
            else:
                ch_modus2 = ch_modus
                file_start = "UK_Charging_"
            all_lists_name = "dataCharging/modelData/allLists" + str(ch_modus2)
            # --> already computed
            allLists = compute_histogram_lists(VehicleList_old, ch_modus2)
            save_list(allLists, all_lists_name)
            allLists = open_file(all_lists_name)

            open_filename = 'dataCharging/alreadyLoaded/' + file_start + ch_modus + "_" + modus + "s"

            data_real = open_file(open_filename)
            data_model = allLists[7]
            means_per_interval_model = list()
            means_per_interval_real = list()
            total_mean1 = 0
            total_mean2 = 0
            total_length1 = 0
            total_length2 = 0
            for interval in range(len(data_model)):
                mean1 = np.mean(np.array(data_model[interval]))
                mean2 = np.mean(change_to_seconds(np.array(data_real[interval])))
                means_per_interval_model.append(mean1)
                means_per_interval_real.append(mean2)
                total_mean1 +=mean1 * len(data_model[interval])
                total_mean2 +=mean2 * len(data_real[interval])
                total_length1 += len(data_model[interval])
                total_length2 += len(data_real[interval])

            print("plotting mean plug-in duration at times:")
            print(means_per_interval_real)
            print(means_per_interval_model)
            plt.plot(range(len(data_model)), means_per_interval_real, label = "real")
            plt.plot(range(len(data_model)), means_per_interval_model, label = "model")
            plt.legend()
            plt.show()
            plt.figure()

            print("average plug-in time per session:")
            modus2 = "plugin_duration"
            #open_filename = 'dataCharging/alreadyLoaded/' + file_start + ch_modus + "_" + modus2 + "s"
            #data_real = open_file(open_filename)
            #data_model = allLists[8]
            print("real:", total_mean2/total_length2)
            print("model:", total_mean1/total_length1)
            #print("real:", np.mean(data_real))
            #print("model:", np.mean(data_model))


