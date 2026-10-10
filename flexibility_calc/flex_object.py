#import matplotlib.pyplot as plt

from flexibility_calc.flexibility import *
from flexibility_calc.Risk import *


class flex_object():
    spontanflex: bool = None
    start_time: datetime.timedelta = None

    duration: datetime.timedelta = None

    FLex_place: bool = None
    flex_list: list = None
    activation_time: datetime.timedelta = None
    number_of_day: int = None
    DayType: int = None
    #Charging_strategies: list = None
    #heuristics: list = None
    risk: bool = None
    risk_object: Risk_statistic = None
    next_day_flexibility: flex_on_day = None
    this_day_flexibility: flex_on_day = None
    ignore_first_days: int = None
    flex_dependant: bool = None
    co2: bool  = None




    def __init__(self, spontanflex, risk, start_time, duration, activation_time, Flex_place, numberofday=-1,
                 number_of_run = 0, DayType=0, ignore_first_days = 1, flex_dependant = False, co2 = False):
        self.spontanflex = spontanflex
        self.start_time = start_time
        self.duration = duration
        self.Flex_place= Flex_place
        self.number_of_day = numberofday
        self.DayType = DayType

        self.risk = risk
        self.number_of_run = number_of_run
        self.activation_time = activation_time
        self.ignore_first_days = ignore_first_days
        self.flex_dependant = flex_dependant
        self.co2 = co2

    def compute_flexibility(self, all_DaysList, NumberOfDays, start_daytype, flex_object = None, concrete_strat = None, flex_dependant_strat=True):
        flex_list = compute_flexibility(self.spontanflex, self.risk, all_DaysList, self.start_time, self.duration,
                                        NumberOfDays, int(start_daytype), self.activation_time, self.Flex_place,
                                        self.number_of_day, self.DayType, self.number_of_run, self.ignore_first_days,
                                        self.flex_dependant, flex_object, self.co2,  concrete_strat, flex_dependant_strat )
        self.flex_list = flex_list

        if self.risk:
            try:
                self.risk_object = Risk_statistic(
                    self.spontanflex,
                    [i for i in range(len(settingsContainer.getChargingStrategies()))],
                    [j for j in range(len(settingsContainer.getHeuristics()))],
                    [0, 1],
                    flex_dependant=self.flex_dependant
                )
                self.risk_object.compute_min_quarter_quantiles_from_flex_list(self.flex_list)
            except Exception as _e:
                print(f"Warnung: risk_object konnte nicht berechnet werden: {_e}")
                self.risk_object = None

        if not self.risk:
            if self.Flex_place == "Home":
                if self.number_of_day + 1 < len(all_DaysList[0]):
                    self.next_day_flexibility = all_DaysList[self.number_of_run][self.number_of_day+1].Flexibility_Home

                self.this_day_flexibility = all_DaysList[self.number_of_run][self.number_of_day].Flexibility_Home
            elif self.Flex_place == "Work":
                if self.number_of_day + 1 < len(all_DaysList[0]):
                    self.next_day_flexibility = all_DaysList[self.number_of_run][self.number_of_day+1].Flexibility_Work

                self.this_day_flexibility = all_DaysList[self.number_of_run][self.number_of_day].Flexibility_Work
            else:
                if self.number_of_day + 1 < len(all_DaysList[0]):
                    self.next_day_flexibility = all_DaysList[self.number_of_run][self.number_of_day+1].Flexibility_All
                self.this_day_flexibility = all_DaysList[self.number_of_run][self.number_of_day].Flexibility_All
            for strat_pos in range(len(settingsContainer.getChargingStrategies())):
                self.this_day_flexibility.compute_standard_load_profile(strat_pos, -1, self.spontanflex)

    def visualize_flexibility(self, strat_pos, heuristic_pos, modus_pos, viz_safe, viz_show, filename,
                              plot_momentary_potential = False, withlines = True, flex_dependant = False,
                              strat_pos_dep = None, modus_pos_dep= None, plot_labels = True):

        plt.rc('font', size=20)
        # strat_pos als array , heuristic and modus_pos as single number
        if self.risk:
            if not flex_dependant:
                plt.rc('font', size=20)
                if self.risk_object == None:
                    self.risk_object = Risk_statistic(self.spontanflex, [i for i in range(len(settingsContainer.getChargingStrategies()))], [j for j in range(len(settingsContainer.getHeuristics()))], [0,1])
                    self.risk_object.compute_min_quarter_quantiles_from_flex_list(self.flex_list)
                    labels = ["Minimum", "Maximum", "Durchschnitt", "0.05-Quantil", "0.25-Quantil", "0.5-Quantil",
                              "0.75-Quantil", "0.95-Quantil"]
                    labels.append("(alle Farben, nicht gestrichelt): \n Beispiele für berechnete \n spez. Flexibilität")

                number_of_calculations = len(np.array(self.flex_list).flatten())



                self.risk_object.visualize_quantiles(strat_pos[0], heuristic_pos, modus_pos)#, plot = plt)
                count = 0
                for flex in np.array(self.risk_object.flex_list).flatten().flatten():
                    if self.spontanflex:
                        flex.visualize_spontanflex(strat_pos[0], heuristic_pos, modus_pos, withlines=False,
                                                   with_energy=False, for_risk = True, plt = plt)
                    else:
                        flex.visualize_fixDate_flex(strat_pos[0], heuristic_pos, modus_pos, withlines=False,
                                                    with_energy = False, for_risk = True, plt = plt)
                    count += 1
                    #if count == 10:
                     #   break
                    # print("hi")
                if self.risk_object == None:
                    plt.legend(labels, ncol=2, loc="upper right", bbox_to_anchor=(1, 1), fontsize = 10)
                plt.xlim(right=self.duration.total_seconds() / 60 * 1.5, left=0)
                plt.ylim(top=self.risk_object.quantiles[strat_pos[0]][heuristic_pos][modus_pos][1]*2.2)
                if plot_labels:
                    plt.xlabel("Zeit in Minuten ab Startzeitpunkt des Flexibilitätzeitraumes")
                    plt.ylabel("Leistung in kw")
                plt.text(0.5, self.risk_object.quantiles[strat_pos[0]][heuristic_pos][modus_pos][1]+200,"berücksichtige spez. \n Flexibilitäten: " + str(number_of_calculations))
                for i in [3,4,6,7]:
                    plt.text(self.duration.total_seconds() / 60,
                             self.risk_object.quantiles[strat_pos[0]][heuristic_pos][modus_pos][i] + 1,
                             "Quantilwert: " + str(int(np.round(self.risk_object.quantiles[strat_pos[0]][heuristic_pos][modus_pos][i]))),
                             fontsize = 14)
                plt.text(self.duration.total_seconds() / 60,
                         self.risk_object.quantiles[strat_pos[0]][heuristic_pos][modus_pos][0] + 1,
                         "Wert des Minimums: " + str(int(np.round(self.risk_object.quantiles[strat_pos[0]][heuristic_pos][modus_pos][0]))),
                         fontsize = 14)
                plt.text(self.duration.total_seconds() / 60,
                         self.risk_object.quantiles[strat_pos[0]][heuristic_pos][modus_pos][1] + 1,
                         "Wert des Maximums: " + str(
                             int(np.round(self.risk_object.quantiles[strat_pos[0]][heuristic_pos][modus_pos][1]))),
                         fontsize=14)
                plt.text(self.duration.total_seconds() / 60,
                         self.risk_object.quantiles[strat_pos[0]][heuristic_pos][modus_pos][2] + 1,
                         "Durchschnittswert: " + str(
                             int(np.round(self.risk_object.quantiles[strat_pos[0]][heuristic_pos][modus_pos][2]))),
                         fontsize=14)

                if viz_show:

                    plt.show()
                if viz_safe:
                    plt.savefig(filename)
            else:
                if self.risk_object == None:
                    plt.rc('font', size=20)


                    self.risk_object = Risk_statistic(self.spontanflex, [i for i in range(len(settingsContainer.getChargingStrategies()))], [j for j in range(len(settingsContainer.getHeuristics()))], [0,1], flex_dependant= True)
                    self.risk_object.compute_min_quarter_quantiles_from_flex_list(self.flex_list)
                    labels = ["Minimum", "Maximum", "Durchschnitt", "0.05-Quantil", "0.25-Quantil", "0.5-Quantil",
                              "0.75-Quantil", "0.95-Quantil"]
                    self.risk_object.visualize_quantiles(strat_pos[0], heuristic_pos, modus_pos, False,
                                                         strat_pos_dep, modus_pos_dep)
                if viz_show:

                    plt.show()
                if viz_safe:
                        plt.savefig(filename)


        elif len(self.flex_list) > 1 or len(self.flex_list[0])>1:
            print("Error: length should be 1 if risk == False")

            # strat_pos als array , heuristic and modus_pos as single number
        else:
            labels = list()
            if modus_pos == 0:
                modus = "charge"
            else:
                modus = "discharge"

            count = 0
            for ii in strat_pos:
                label = str(ii+1)
                if plot_momentary_potential: # and self.spontanflex:
                    self.this_day_flexibility.visualize_aggregated_boundaries(self.start_time, self.duration, modus, power=True,
                                                                             relative_to_start_time=True,positive=True)
                    labels.append("Momentanpotential (MP) zum  \n Ent-/Laden")
                    # possible Todo: plotting momentary potential also for next day
                    self.this_day_flexibility.compute_aggregated_Boundaries_with_charging_strategy_difference(ii,
                                                                                                            heuristic_pos,
                                                                                                            modus_pos,
                                                                                                            -1,
                                                                                                            self.spontanflex)
                    #self.flex_list[0][0].visualize_aggregated_potential_wrt_ch_strategy(ii, heuristic_pos,  modus_pos)  # heuristic_pos basically irrelevant
                    labels.append("MP unter Berücksichtigung des eigent. \n Lastprofils bei Ladestrategie " + label)

                if self.spontanflex:
                    self.flex_list[0][0].visualize_spontanflex(ii, heuristic_pos, modus_pos, withlines = withlines, with_energy=False, plt = plt)
                else:
                    self.flex_list[0][0].visualize_fixDate_flex(ii,heuristic_pos,modus_pos, withlines = withlines, with_energy=False, plt = plt)


                labels.append("Flexibilität bei Ladestrategie "  + label)
                if count == 0:
                    for ij in ["maximale Leistung während \n der Flexibilitätsbereitstellung",
                               "minimale Leistung während \n der Flexibiliätsbereitstellung"]:  # , "avg " + Charging_strategies[ii]:
                        labels.append(ij)
                else:
                    for ij in ["maximale Leistung",
                                   "minimale Leistung"]:  # , "avg " + Charging_strategies[ii]:
                            labels.append(ij)
                count += 1

            # plt.show()
            end_time = self.start_time + self.duration


            if end_time > datetime.timedelta(days=1) and plot_momentary_potential:
                # flex.visualize_aggregated_boundaries(start_time, duration, modus, power=True)
                self.next_day_flexibility.visualize_aggregated_boundaries(datetime.timedelta(0), end_time - datetime.timedelta(days=1),
                                                      modus, power=True, original_duration=self.duration)
            #plt.legend(labels=labels, loc="lower right",  bbox_to_anchor=(1, 0), fontsize = 12)
            plt.xlim(right=self.duration.total_seconds() / 60 * 1.5, left = 0)
            if plot_labels:
                plt.xlabel("Zeit in Minuten ab Startzeitpunkt des Flexibilitätzeitraumes")
                plt.ylabel("Leistung in kw")

            # plt.rc('axes', labelsize=16)  # Schriftgröße der x- und y-Beschriftungen

            if viz_show:
                plt.show()
            if viz_safe:
                plt.savefig(filename)

    def visualize_flexibility_of_one_vehicle(self, heuristics=[0,1], modus=0, strat_pos=[0, 1, 2],  ev=None):

        plt.rc('font', size=21)
        if self.risk:
            print("only for specific flexibility")
            return

        flex = self.flex_list[0][0]

        # find flex boundary
        already_plotted = False
        for strategy in strat_pos:
            if not already_plotted:
                for flxbdry in flex.checked_flex_boundaries[strategy]:
                    #  only for testing:
                    #  #ev = flxbdry.vehicle

                    if flxbdry.vehicle.ID == ev.ID:
                        divisor = flxbdry.visualize_energy_boundaries(withChargingStrategies=True)
                        e_curr_old = flxbdry.e_curr
                        already_plotted = True
                        break

            count = 0
            for heuristic_pos in heuristics:
                if self.spontanflex:
                    list1 = flex.spontanflex_list[strategy][heuristic_pos][modus]
                else:
                    list1 = flex.fixDate_flex_list[strategy][heuristic_pos][modus]
                bdry_found = True
                for timesteps in list1:
                    for i,entry in enumerate(timesteps.FlexBoundaries):
                        if entry.bdry.vehicle.ID == ev.ID and entry.__class__== flex_profile:
                            day = flxbdry.available_period.days- entry.bdry.available_period.days
                            entry.plot_in_energy_boundary(divisor, heuristic_pos, e_curr_old, day)
                            bdry_found = True
                            if not self.spontanflex and count == 0:
                                for i,bdry1 in enumerate(flex.relevant_FlexBoundaries):
                                    if bdry1[0].vehicle.ID == ev.ID:
                                        whole_period = bdry1[2]
                                        break
                                if not whole_period:
                                    e_curr_activation = compute_charged_until_certain_time_according_to_Charging_strategy(
                                        flxbdry,  entry.start_time + datetime.timedelta(days = day)
                                             -settingsContainer.getFlexActivationTime(),
                                        settingsContainer.getChargingStrategies()[strategy])
                                else:
                                    e_curr_activation = 0

                                x = [max(entry.start_time + datetime.timedelta(days = day)
                                         -settingsContainer.getFlexActivationTime(), flxbdry.t_start).total_seconds()/divisor,
                                     (entry.start_time + datetime.timedelta(days = day)).total_seconds()/divisor]

                                y= [e_curr_activation, entry.bdry.e_curr-e_curr_old]

                                if strategy == 0:
                                    color = "green"
                                elif strategy == 1:
                                    color = "brown"
                                elif strategy == 2:
                                    color = "purple"
                                label = "SOC-Anpassung (" + str(strategy+1) + ")"
                                plt.plot(x, y, ":", alpha = 0.6, label = label, color= color)



                            #plt between charging strategy and changed strategy, if spontanflex
                            #plt.fill(
                            #    np.append(x1, x2[::-1]),
                            #    np.append(y1, y2[::-1]),
                            #    color='C0', alpha=0.3
                            #)
                            break
                    if bdry_found:
                        break
                count += 1
        #plt.legend(loc = "upper center", fontsize = 22, bbox_to_anchor=(0.4,1.1))
        plt.show()
        #flex == spontanflex or fixdateflex object
