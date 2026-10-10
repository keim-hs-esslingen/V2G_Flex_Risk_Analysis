#from old_files.compare_flex_parameters import *
import datetime
import matplotlib.pyplot as plt
import os.path
import sys

# Projekt-Root vor die Standardbibliothek setzen, damit "test" das lokale
# test.py (nicht das gleichnamige stdlib-Paket) auflöst, egal aus welchem
# Ordner das Skript gestartet wird.
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)
# start_tool() erwartet relative Pfade (z.B. "SimulationTool/..."), daher
# muss das Arbeitsverzeichnis unabhängig vom Startordner das Projekt-Root sein.
os.chdir(PROJECT_ROOT)
from test import *

def run_example(num, load_model = False,  runs=1):


    simulation_tool = start_tool()

    name_model = "models/flex-validation/Szenario_flex_duration" + str(num)

    if load_model:
        simulation_tool.load_model(name_model)
    else:
        simulation_tool.run_model(number_of_runs=runs, number_of_users=100, number_of_days=100)
        simulation_tool.save_model(name_model)




    return simulation_tool

def vis_example( szen ):
    if szen == 1:
        #6. 8b)
        heuristics = [0,1]
        sim_tool = run_example(1, load_model=True)
        pos = 6
        start_time = datetime.timedelta(hours=10, minutes=3)
        spontan_flex = True
        flex_duration = datetime.timedelta(hours=2)
        flex_at_number_of_day = 2
        activation_time = None
        modus = 0
    elif szen ==2:
        # 6. 8a)
        heuristics = [0,1]
        sim_tool = run_example(1, load_model=True)
        pos = 6
        start_time = datetime.timedelta(hours=10, minutes=3)
        spontan_flex = True
        flex_duration = datetime.timedelta(hours=2)
        flex_at_number_of_day = 3
        activation_time = None
        modus = 1
    elif szen ==3:
        #6.8c
        heuristics = [1]
        sim_tool = run_example(1, load_model=True)
        flex_duration = datetime.timedelta(hours=2)
        flex_at_number_of_day = 2
        start_time = datetime.timedelta(hours=10, minutes=3)
        activation_time = datetime.timedelta(hours=1.3)
        pos = 6
        spontan_flex = False
        modus = 0
    elif szen ==4:
        # 6.8d/e
        heuristics = [1]
        sim_tool = run_example(1, load_model=True)
        flex_duration = datetime.timedelta(hours=2)
        flex_at_number_of_day = 3
        start_time = datetime.timedelta(hours=12, minutes=30) #11,3 -->d
        activation_time = datetime.timedelta(hours=1.3)
        pos = 6
        spontan_flex = False
        modus = 1



    sim_tool.calculate_flexibility(spontan_flex=spontan_flex, risk=False,
                                   flex_start_time=start_time,
                                   flex_duration=flex_duration,
                                   flex_activation_time=activation_time,
                                   flex_place=None,
                                   flex_at_number_of_day=flex_at_number_of_day, flex_at_number_of_run=None,
                                   flex_at_daytype=None)


    # sim_tool.visualize_flexibility(viz_charging_strategy = [0,1, 2], viz_heuristic = None, viz_modus = 0,viz_safe = None,
    #                              filename = None, viz_show = None)

    ev = sim_tool.model_data.VehicleLists[0][pos]
    # for ev in sim_tool.model_data.VehicleLists[0]:
    sim_tool.flexibility_object.visualize_flexibility_of_one_vehicle(ev=ev, modus=modus, heuristics=heuristics, plot_momentary_potential = True)




def flex_validation(plot_ev_specific = False, plot_spec_flex = False, plot_exampe_3_larger_2_for_pos = False,
                    plot_soc_comparison = False, plot_duration_comparison = False,
                    plot_statistical_flex_over_whole_day = False, plot_statistic = False, compare_flexibility_parameters =False):
    if plot_ev_specific:
        # Method to validate flexibility calculations

        # -----------------------------------------spontanflex vehicle spezific---------------------------------------------
        # picture 6.8b (Energiegrenzen bei einem Fahrzeug mit allen Ladestrategien und verändertem Ladeverhalten bei den
        # implementierten Heuristiken während einer berechneten Flexibilitätslieferung für zwei Stunden
        vis_example(1)
        # picture 6.8a (Energiegrenzen bei einem Fahrzeug mit allen Ladestrategien und verändertem Ladeverhalten bei den
        # implementierten Heuristiken während einer berechneten Flexibilitätslieferung für zwei Stunden
        vis_example(2)


        # -----------------------------------------spontanflex vehicle spezific---------------------------------------------
        # picture 6.8c (Energiegrenzen bei einem Fahrzeug mit allen Ladestrategien und verändertem Ladeverhalten bei den
        # implementierten Heuristiken während einer berechneten Flexibilitätslieferung für zwei Stunden
        vis_example(3)
        # picture 6.8d/e(Energiegrenzen bei einem Fahrzeug mit allen Ladestrategien und verändertem Ladeverhalten bei den
        # implementierten Heuristiken während einer berechneten Flexibilitätslieferung für zwei Stunden
        vis_example(4)
    if plot_spec_flex:
        #Abbildung 6.9
        sim_tool = run_example(1, load_model = True)
        sim_tool.calculate_flexibility(spontan_flex=True, risk=False,
                                   flex_start_time=datetime.timedelta(hours=11, minutes=3),
                                   flex_duration=datetime.timedelta(minutes=15),
                                   flex_activation_time=datetime.timedelta(hours=0.25),
                                   flex_place=None,
                                   flex_at_number_of_day=3, flex_at_number_of_run=None,
                                   flex_at_daytype=None)
    #2, 17:3
        #a)
        sim_tool.visualize_flexibility(viz_charging_strategy = [0,1,2], viz_heuristic = 0, viz_modus = 0,viz_safe = None,
                                  filename = None, viz_show = None)
        #b)
        sim_tool.visualize_flexibility(viz_charging_strategy=[0, 1, 2], viz_heuristic=1, viz_modus=0, viz_safe=None,
                                       filename=None, viz_show=None)
        #c)
        sim_tool.visualize_flexibility(viz_charging_strategy=[0, 1, 2], viz_heuristic=1, viz_modus=1, viz_safe=None,
                                       filename=None, viz_show=None)

    if plot_exampe_3_larger_2_for_pos:
        #Anhang
        sim_tool = run_example(1, load_model=True)
        for i in range(24):
            sim_tool.calculate_flexibility(spontan_flex=True, risk=False,
                                   flex_start_time=datetime.timedelta(hours=i, minutes=3),
                                   flex_duration=datetime.timedelta(minutes=15),
                                   flex_activation_time=datetime.timedelta(hours=0.25),
                                   flex_place=None,
                                   flex_at_number_of_day=3, flex_at_number_of_run=None,
                                   flex_at_daytype=None)
        #for strat_pos in [0,1,2]:

            if sim_tool.flexibility_object.flex_list[0][0].total_capacity[2][1] >\
                    sim_tool.flexibility_object.flex_list[0][0].total_capacity[0][1]:

                sim_tool.visualize_flexibility(viz_charging_strategy=[0,1,2], viz_heuristic=1, viz_modus=1, viz_safe=None,
                                   filename=None, viz_show=None)
                break

    if plot_soc_comparison:
        # 6.10
        # anhang für duration 2h
        sim_tool = run_example(1, load_model=True)
        labels = list()
        for i in [0,20,40,60,80,100, 120, 140,200,400,1000,2880]:
            sim_tool.calculate_flexibility(spontan_flex=False, risk=False,
                                               flex_start_time=datetime.timedelta(hours=10, minutes=3),
                                               flex_duration=datetime.timedelta(minutes = 15),
                                               flex_activation_time=datetime.timedelta(minutes=i),
                                               flex_place=None,
                                               flex_at_number_of_day=3, flex_at_number_of_run=None,
                                               flex_at_daytype=None)
            if i == 2880:
                plot_momentary = True
                labels.append("MP hinsichtlich \n der Ladestrategie")
            else:
                plot_momentary = False

            sim_tool.visualize_flexibility(viz_charging_strategy=[1], viz_heuristic=1, viz_modus=1,
                                                   viz_safe=None,filename=None, viz_show=False,
                                           plot_momentary=plot_momentary, withlines = False)
            label = "Aktivierungszeit: " + str(i) + " min"
            labels.append(label)
        plt.legend(labels = labels)
        plt.show()
    if plot_duration_comparison:
        # 6.11
        #for j in np.arange(16,20,0.5):
            sim_tool = run_example(1, load_model=True)
            labels = list()
            plt.figure(figsize=(14, 6))
            for i in [10,30,60,120]: #[0.1,0.3,0.5,1,2,4,10]:
                sim_tool.calculate_flexibility(spontan_flex=True, risk=False,
                                                   flex_start_time=datetime.timedelta(hours=19, minutes=33),
                                                   flex_duration=datetime.timedelta(seconds = i*60),
                                                   flex_activation_time=datetime.timedelta(minutes=120),
                                                   flex_place=None,
                                                   flex_at_number_of_day=4, flex_at_number_of_run=None,
                                                   flex_at_daytype=None)

                if i == 120:
                    plot_momentary = True
                    labels.append("MFP")
                else:
                    plot_momentary = False
                sim_tool.visualize_flexibility(viz_charging_strategy=[1], viz_heuristic=1, viz_modus=0,
                                                       viz_safe=None, filename=None, viz_show=False,
                                               plot_momentary=plot_momentary, withlines = False, plot_labels = False)
                label = "Duration: " + str(i) + " min"
                labels.append(label)

            plt.xlabel("Time in minutes from start of flexibility delievery period (FDP)", fontsize = 24)
            plt.ylabel("Power in kw", fontsize = 24)
            #plt.xlim(0, 180)
            plt.legend(labels=labels, loc="lower right", fontsize=20, ncol = 2)
            plt.savefig("paper_plots/figures/duration_comparison_Figure2.png", dpi=300, bbox_inches="tight")
            print("Saved: paper_plots/figures/duration_comparison_Figure2.png")
            plt.show()


    if plot_statistical_flex_over_whole_day:
        interval_size = datetime.timedelta(hours = 1)
        runs = 3
        plt.rc('font',size = 15)
        if True:
            plt.subplots_adjust(left=0.15)
            print("1")
            #--------------------all quantiles for wednesday: positive at home, spontan, as long as possible --------------------------
            sim_tool = run_example(22, load_model=True, runs=runs)
            Daytype = 3
            #interval_size = datetime.timedelta(minutes = 360)

            quantiles = compute_flexibility_over_whole_day(spontanflex=True, risk=True, all_DaysList=sim_tool.model_data.DayLists,
                            duration = datetime.timedelta(minutes = 15), NumberOfDays = settingsContainer.getNumberOfDays(),
                            start_daytype = 1, activation_time = datetime.timedelta(0), Flex_place = "Home", numberofday = -1,
                                            Daytype = Daytype, run =0, interval_size =interval_size)
            plotting_over_whole_day(strategies = [1], modus_pos = 1, loc = "upper right", fontsize = 13, ylim_top = 1300, quantiles = quantiles)
            plt.show()
            #plt.savefig("figures/quantiles_day")


        # --------------------all strategies for wednesday : positive at home, spontan --------------------------
        if True:
                print("3")
                if True:

                    plt.subplots_adjust(left=0.15)
                    plt.figure()
                    labels = ["L_strat 1 - Mittwoch", "L_strat 2 - Mittwoch", "L_strat 3 - Mittwoch"]
                    plotting_over_whole_day(strategies = [0,1,2], modus_pos = 1, plotting = False, plot_ylim=True)

                                # --------------------all strategies for saturday and sunday : positive at home, spontan --------------------------
                    #within plot before
                    Daytype = 6
                    compute_flexibility_over_whole_day(spontanflex=True, risk=True, all_DaysList=sim_tool.model_data.DayLists,
                                                       duration=datetime.timedelta(minutes=15),
                                                       NumberOfDays=settingsContainer.getNumberOfDays(),
                                                       start_daytype=1, activation_time=datetime.timedelta(0), Flex_place="Home",
                                                       numberofday=-1,
                                                       Daytype=Daytype, run=0, interval_size=interval_size)
                    labels.append("L_strat 1 - Samstag")
                    labels.append("L_strat 2 - Samstag")
                    labels.append("L_strat 3 - Samstag")
                    plotting_over_whole_day(strategies = [0,1,2], modus_pos = 1,plotting = False, plot_ylim=False)

                    Daytype = 7
                    compute_flexibility_over_whole_day(spontanflex=True, risk=True, all_DaysList=sim_tool.model_data.DayLists,
                                                       duration=datetime.timedelta(minutes=15),
                                                       NumberOfDays=settingsContainer.getNumberOfDays(),
                                                       start_daytype=1, activation_time=datetime.timedelta(0), Flex_Place="Home",
                                                       numberofday=-1,
                                                       Daytype=Daytype, run=0, interval_size=interval_size)
                    labels.append("L_strat 1 - Sonntag")
                    labels.append("L_strat 2 - Sonntag")
                    labels.append("L_strat 3 - Sonntag")
                    #plt.savefig("figures/several_days")
                    plotting_over_whole_day(strategies = [0,1,2], modus_pos = 1, labels = labels, nc_col = 2, fontsize = 12, plotting = False, loc = "lower left", plot_ylim=False)
                    plt.subplots_adjust(left=0.15)
                    plt.show()
              # plt.subplots_adjust(left=0.1, right=0.9, top=0.9, bottom=0.1)

        if False:
            sim_tool = run_example(22, load_model=True, runs=runs)
            print("4")
            # ------as long as possible: negative at home, activaiton_time = 0, 5, 10, 15 minutes, wednesday--------------
            plt.figure()
            Daytype = 3
            labels = list()
            for act_time in [0, 5, 10, 15,2880]: #0.7, 1,4, 12, 24]:


                compute_flexibility_over_whole_day(spontanflex=False, risk=True, all_DaysList=sim_tool.model_data.DayLists,
                                               duration=datetime.timedelta(minutes=15),
                                               NumberOfDays=settingsContainer.getNumberOfDays(),
                                               start_daytype=1, activation_time=datetime.timedelta(minutes = act_time), Flex_place="Home",
                                               numberofday=-1,
                                               Daytype=Daytype, run=0, interval_size=interval_size)



                ylim = visualize_flexibility_over_whole_day(2, 1, 0, only_mean=True)
                if act_time > 60:
                    labels.append("Akt.-zeit: " + str(int(act_time/60)) + " h")
                else:
                    labels.append("Akt.-zeit: "+str(act_time) + " min")
            plt.ylim(bottom = -50)
            plt.subplots_adjust(left=0.15)
            plt.legend(labels, loc="lower left", ncol = 2, fontsize = 13)
            plt.xlabel("Zeit in Stunden ab 00:00 Uhr")
            plt.ylabel("Leistung in kw")
            #plt.savefig("figures/akt_time_day")
            plt.show()
            plotting_over_whole_day(strategies=[0, 1, 2], modus_pos=0, plotting=True, plot_ylim=False, loc = "center left", nc_col=1)
            plt.ylim =0
            plt.figure()
              # plt.subplots_adjust(left=0.1, right=0.9, top=0.9, bottom=0.1)

        if True:
            print("2")
            sim_tool = run_example(22, load_model=True, runs=runs)
            plt.subplots_adjust(left=0.15)
            #sim_tool = run_example(22, load_model=True, runs=runs)

            # --------------------all quantiles for wednesday: positive at home, activation, as long as possible --------------------------
            Daytype = 3
            #interval_size = datetime.timedelta(minutes=360)

            quantiles2 = compute_flexibility_over_whole_day(spontanflex=False, risk=True, all_DaysList=sim_tool.model_data.DayLists,
                                               duration=datetime.timedelta(minutes=15),
                                               NumberOfDays=settingsContainer.getNumberOfDays(),
                                               start_daytype=1, activation_time=datetime.timedelta(hours = 4), Flex_place="Home",
                                               numberofday=-1,
                                               Daytype=Daytype, run=0, interval_size=interval_size)
            if True:
                plotting_over_whole_day(strategies = [1], modus_pos = 1, without_legend = False, loc = "upper right", fontsize=13, ylim_top = 1300, quantiles = quantiles2)
                plt.show()
                #plt.savefig("figures/quantiles2_day")

        if False:
            # --------------------all strategies Wednesday positive all, spontan, not at home ---------
            print("5")
            sim_tool=run_example(22, load_model=True, runs =runs)
            plt.figure()
            plt.subplots_adjust(left=0.15)
            labels = ["L_strat 1 - Mittwoch", "L_strat 2 - Mittwoch", "L_strat 3 - Mittwoch"]
            Daytype = 3
            compute_flexibility_over_whole_day(spontanflex=True, risk=True, all_DaysList=sim_tool.model_data.DayLists,
                                               duration=datetime.timedelta(minutes=15),
                                               NumberOfDays=settingsContainer.getNumberOfDays(),
                                               start_daytype=1, activation_time=datetime.timedelta(0), Flex_place = "all",
                                               numberofday=-1,
                                               Daytype=Daytype, run=0, interval_size=interval_size)
            plotting_over_whole_day(strategies=[0, 1, 2], modus_pos=1, plotting=False, plot_ylim=False)


            # --------------------all strategies for sunday and saturday : positive not at home, spontan --------------------------
            # within plot before
            Daytype = 6
            compute_flexibility_over_whole_day(spontanflex=True, risk=True, all_DaysList=sim_tool.model_data.DayLists,
                                               duration=datetime.timedelta(minutes=15),
                                               NumberOfDays=settingsContainer.getNumberOfDays(),
                                               start_daytype=1, activation_time=datetime.timedelta(0), Flex_place = "all",
                                               numberofday=-1,
                                               Daytype=Daytype, run=0, interval_size=interval_size)
            labels.append("L_strat 1 - Samstag")
            labels.append("L_strat 2 - Samstag")
            labels.append("L_strat 3 - Samstag")
            plotting_over_whole_day(strategies=[0, 1, 2], modus_pos=1, plotting=False, plot_ylim=False)

            Daytype = 7
            compute_flexibility_over_whole_day(spontanflex=True, risk=True, all_DaysList=sim_tool.model_data.DayLists,
                                               duration=datetime.timedelta(minutes=15),
                                               NumberOfDays=settingsContainer.getNumberOfDays(),
                                               start_daytype=1, activation_time=datetime.timedelta(0), Flex_place = "all",
                                               numberofday=-1,
                                               Daytype=Daytype, run=0, interval_size=interval_size)
            labels.append("L_strat 1 - Sonntag")
            labels.append("L_strat 2 - Sonntag")
            labels.append("L_strat 3 - Sonntag")
            plt.ylim(bottom = 380)
            plotting_over_whole_day(strategies=[0, 1, 2], modus_pos=1, labels=labels, nc_col=2, fontsize=12, plotting=False,
                                    loc="lower left", plot_ylim=False)
            #plt.savefig("figures/several_days2")
            plt.show()






    if plot_statistic:
        positive = True

        # example 1:
        #plt.rc(fontsize = 15)
        #sim_tool = run_example(1, load_model=True)
        sim_tool = run_example(10, load_model=True, runs =1)
        sim_tool.calculate_flexibility(spontan_flex=True, risk=True,
                                       flex_start_time=datetime.timedelta(hours=11, minutes=3),
                                       flex_duration=datetime.timedelta(minutes=15),
                                       flex_activation_time=datetime.timedelta(hours=0.25),
                                       flex_place=None,
                                       flex_at_number_of_day=-1, flex_at_number_of_run=None,
                                       flex_at_daytype=None)
        # 2, 17:3
        if positive:

            sim_tool.visualize_flexibility(viz_charging_strategy=[2], viz_heuristic=1, viz_modus=1, viz_safe=None,
                                       filename=None, viz_show=True, withlines=False)
        else:
            sim_tool.visualize_flexibility(viz_charging_strategy=[2], viz_heuristic=1, viz_modus=0, viz_safe=None,
                                           filename=None, viz_show=True, withlines=False)

        # for different MAX_SOC scenarios, set MAX_SOC in SimulationTool_settings.json

    if compare_flexibility_parameters:
        #running thi several times with different parameters for results
        positive = True
        #be careful: set parameters accoridnlgy in simulationTool_settings.json.
        # 98: MIN_SOC = 40  --> main scenario
        # 99: MIN_SOC = 60
        #100: MIN_SOC = 80
        # 101: SOC_TOL = 0
        #102: SOC_TOL = 20
        #103: MIN_FLEX_TIME = 0 minutes
        # 104: MIN_FLEX_TIME = 120 minutes
        # 105 V2G_AVAILABILITY = 30
        # 106: V2G_AVAILABILITY = 70
        # 110: Änderung: MIN_SOC_PLUG_IN = 30, SOC_TOL = 50,
        # 11: " und SOC_TOL = 0

        # example 1:
        # plt.rc(fontsize = 15)
        # sim_tool = run_example(1, load_model=True)
        sim_tool = run_example(100, load_model=True, runs=3)

        sim_tool.calculate_flexibility(spontan_flex=True, risk=True,
                                       flex_start_time=datetime.timedelta(hours=11, minutes=3),
                                       flex_duration=datetime.timedelta(minutes=60),
                                       flex_activation_time=datetime.timedelta(hours=0.25),
                                       flex_place=None,
                                       flex_at_number_of_day=-1, flex_at_number_of_run=None,
                                       flex_at_daytype=None)
        # 2, 17:3
        if positive:

            sim_tool.visualize_flexibility(viz_charging_strategy=[2], viz_heuristic=1, viz_modus=1, viz_safe=None,
                                           filename=None, viz_show=True, withlines=False)
        else:
            sim_tool.visualize_flexibility(viz_charging_strategy=[2], viz_heuristic=1, viz_modus=0, viz_safe=None,
                                           filename=None, viz_show=True, withlines=False)





    sim_tool = run_example(1, load_model=True)
    sim_tool.calculate_flexibility(spontan_flex=False, risk=False,
                                   flex_start_time=datetime.timedelta(hours=10, minutes=3),
                                   flex_duration=datetime.timedelta(minutes=15),
                                   flex_activation_time=datetime.timedelta(minutes=1000),
                                   flex_place=None,
                                   flex_at_number_of_day=3, flex_at_number_of_run=None,
                                   flex_at_daytype=None)
    sim_tool.visualize_flexibility(viz_charging_strategy=[1], viz_heuristic=1, viz_modus=1,
                                   viz_safe=None,
                                   filename=None, viz_show=True)


def plotting_over_whole_day( strategies = [0,1,2], modus_pos = 1, labels = None, plotting = True, plot_ylim = True,
                             nc_col = 2, fontsize = 15, loc = "lower left", ylim_top = None, without_legend = False, quantiles = None):


    if len(strategies)> 1:
        if labels == None:
            labels = ["L_strat 1", "L_strat 2", "L_strat 3"]
        for i in [0, 1, 2]:
            ylim = visualize_flexibility_over_whole_day(i, 1, modus_pos, only_mean=True)


    else:
        ylim = visualize_flexibility_over_whole_day(strategies[0], 1, modus_pos, only_mean=False,
                                                    colors = ['blue', 'red', 'orange', 'purple', 'cyan', 'green', 'pink', 'magenta'], all_quantiles = quantiles)
        if labels == None:
            labels = ["Min.", "Max.", "Durchsch.", "0.05-Q.", "0.25-Q.", "0.5-Q.", "0.75-Q.",
              "0.95-Q."]


    if not without_legend:
        plt.legend(labels, loc=loc,ncol = nc_col, fontsize = fontsize)
    if plot_ylim:
        plt.ylim(bottom = ylim)
    if ylim_top != None and plot_ylim:
        plt.ylim(top = ylim_top )
    plt.xlabel("Zeit in Stunden ab 00:00 Uhr")
    plt.ylabel("Leistung in kw")
    if plotting:
        plt.show()
#def load_fig(filename):
 #   fig = plt.f

if __name__ == "__main__":
    flex_validation(False, False, False, False, True,False, False, False)
