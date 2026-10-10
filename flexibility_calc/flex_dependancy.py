import datetime

import helper_files.variables

from flexibility_calc.Spontanflex import *
from flexibility_calc.fixdateflex import *
from flexibility_calc.Risk import *
from flexibility_calc.momentary_potential import *
def adapt_available_periods( flex_object,   day, start_time, count_runs, count_days, co2, concrete_strat):
    current_flex = flex_object.flex_list[count_runs][count_days]
    vehicles =  [0 for i in range(settingsContainer.getNumberOfUsers())]
    all_available_periods = list()
    #if co2:
       # all_available_periods = list()
    #else:
    for strat_pos in range(len(settingsContainer.getChargingStrategies())):
            all_available_periods.append(list())
            for direction in [0,1]:
                all_available_periods[strat_pos].append(list())
    #available_periods = list()
    count = 0
    for profile in current_flex.profile_list:


        #nach ladestrategie unterschieden: danach wird für jeden Ladestrateige fall alternative ev verhalten berechnet.
        # Flexibilität wird dann wiederumg für jede Ladestrategie berechnet --> 3*3 = 9 Fälle statt 3
        # (macht Sinn, da für zweite flexberechnung macht entweder as late as oossible oder as soon as possible Sinn).
        if not profile.__class__ == flex_profile:
            continue
        if co2 and (profile.modus != "charge" or settingsContainer.getChargingStrategies()[profile.strat_pos] == "as soon as possible"):
            continue
        if concrete_strat != None and profile.strat_pos != concrete_strat:
            continue
        #vehicles.append(profile.bdry.vehicle)
        #if vehicles.__contains__(profile.bdry.vehicle):
         #   continue
        #else:
        #    vehicles.append(profile.bdry.vehicle)
        vehicles[profile.bdry.vehicle.ID] = vehicles[profile.bdry.vehicle.ID]+1
        if start_time<profile.start_time:
            #only intraday storaging
            #Todo several day storaging
            print("Error: only intraday sotraging implemented")
        if profile.end_time>= start_time:
            print("Error: sotrage period too slow")

        alternative_available_period_list = (
            adapt_Charging_after_flexibility_provision(profile, day))
        #adaption of alternative_available_periods_list? class==avialable_periods? wie bei compute_available_periods_at_home
        if profile.modus == "charge":
            modus = 0
        else:
            modus = 1

        all_available_periods[profile.strat_pos][modus].append([alternative_available_period_list, profile.bdry.vehicle])
        count = count +1
    return all_available_periods

def Test_adapt_available_periods(flex_object, count_days, count_runs, all_available_periods, dayyy):
    flex = flex_object.flex_list[count_runs][count_days]
    for strat_pos in range(len(settingsContainer.getChargingStrategies())):
        for modus in [0,1]:
            for available_periods in all_available_periods[strat_pos][modus]:

                available_periods2 = recalculate_av_periods(available_periods[0])
                for profile in flex.profile_list:
                    if not profile.bdry.vehicle.ID == available_periods[1].ID:
                        continue
                    #if profile.bdry.vehicle.ID == 21 and dayyy == 21 and strat_pos == 0 and modus == 1:
                       # print("hi")


                    if profile.modus == "charge":
                        profile_modus  = 0
                    else:
                        profile_modus  = 1

                    if profile.__class__ == base_profile:
                        continue
                    elif profile.strat_pos == strat_pos and profile.modus :
                        old_available_periods = profile.bdry.vehicle.total_available_period_list[dayyy]
                        old_available_periods2 = recalculate_av_periods(old_available_periods)

                        start_ap = None
                        start_ap_pos = 0
                        for ap in old_available_periods2:

                            if ap[2] <= profile.start_time:
                                start_ap_pos = start_ap_pos +1
                                start_ap = ap
                                continue
                            else:

                                break
                        if start_ap == None:
                            start_ap = ap
                        lengt_per = len(old_available_periods2)
                        pos = 0

                        while pos < start_ap_pos-1:
                            old_available_periods2.__delitem__(0)
                            pos = pos +1

                        if start_ap == None:
                            start_ap = ap




                        vehicle = profile.bdry.vehicle
                        ch_times = vehicle.total_Charging_list[dayyy]
                        pl_times = vehicle.total_plugin_list[dayyy]
                        if len(old_available_periods2)> len(available_periods2) and profile.bdry.available_period.end_time.to_timedelta() !=profile.end_time:
                            if settingsContainer.getChargingStrategies()[strat_pos] == "as soon as possible" and modus == 0:
                                print("Error taap2")
                            else:


                                if settingsContainer.getChargingStrategies()[strat_pos] == "as soon as possible":

                                    if profile.heuristic_dependant["max at start"].energy <0:
                                        if start_ap[0].available_time- vehicle.time_to_charge(((100-start_ap[0].start_SOC)*vehicle.battery_size)/100-profile.heuristic_dependant["max at start"].energy, start_ap[0].charging_power)>datetime.timedelta(0):
                                            print("Error taap3: enough time to fully charge")
                                    else:
                                       if  (start_ap[0].available_time-(profile.end_time - profile.start_time) -
                                            vehicle.time_to_charge((start_ap[0].start_SOC*vehicle.battery_size)/100-profile.heuristic_dependant["max at start"].energy), start_ap[0].charging_power) > datetime.timedelta(0):
                                            print("Error taap4: enough time to fully charge")
                                elif settingsContainer.getChargingStrategies()[strat_pos] == "as late as possible":

                                    founded = False
                                    ap_before = None
                                    for avp in old_available_periods2:
                                        #avp = avp[0]

                                        for ap in available_periods2:


                                            if avp[2] <= ap[2] and avp[3] >= ap[2]:
                                                continue
                                            else:
                                                founded = True
                                                break
                                        if founded:
                                            break
                                        ap_before = avp
                                    if profile_modus == 1 and ap[0].start_SOC <= ap[0].min_SOC:
                                        print("Error: saatf13")
                                    pos = 0
                                    for soc_entry in vehicle.total_SOC_list[dayyy].times:
                                        if avp[2]< soc_entry.to_timedelta():
                                            break
                                        pos = pos +1
                                    if ap_before!= None:
                                        last_soc = ap_before[0].min_SOC - (100 - avp[0].start_SOC)  #
                                    else:
                                        last_soc = avp[0].start_SOC
                                    if vehicle.total_SOC_list[dayyy].states[pos]== "Driving":
                                        if last_soc != vehicle.total_SOC_list[dayyy].SOC[pos-1]-vehicle.total_SOC_list[dayyy].SOC[pos]:
                                            print("Error: taap5")



                                    if avp[0].available_time - vehicle.time_to_charge(((avp[0].min_SOC-last_soc)*vehicle.battery_size)/100, avp[0].charging_power) <datetime.timedelta(0):
                                        print("Error: taap6")

                                elif settingsContainer.getChargingStrategies()[strat_pos] == "as long as possible with minimum rate":
                                    founded = False
                                    ap_before = None
                                    for avp in old_available_periods2:

                                        for ap in available_periods2:


                                            if avp[2] <= ap[2] and avp[3] >= ap[2]:
                                                continue
                                            else:
                                                founded = True
                                                break
                                        if founded:
                                            break
                                        ap_before = avp
                                    pos = 0
                                    for soc_entry in vehicle.total_SOC_list[dayyy].times:
                                        if avp[2] < soc_entry.to_timedelta():
                                            break
                                        pos = pos + 1
                                    if ap_before!= None:
                                        bdry = FlexBoundary(ap_before[0], vehicle)
                                        bdry.compute_energy_boundaries()
                                        last_soc = ((bdry.e_max + bdry.e_curr)/vehicle.battery_size)*100 - (100 - avp[0].start_SOC)  #
                                    else:
                                        last_soc = avp[0].start_SOC
                                    if vehicle.total_SOC_list[dayyy].states[pos] == "Driving":
                                        if last_soc != vehicle.total_SOC_list[dayyy].SOC[
                                            pos - 1] - vehicle.total_SOC_list[dayyy].SOC[
                                            pos]:
                                            print("Error: taap5")

                                    if avp[0].available_time - vehicle.time_to_charge(
                                            ((avp[0].min_SOC - last_soc) * vehicle.battery_size) / 100, avp[0].charging_power) < datetime.timedelta(0):
                                        print("Error: taap6")








                        elif len(old_available_periods2)<len(available_periods2):
                            print("Error taap1")
                        elif len(old_available_periods2)== len(available_periods2) or profile.bdry.available_period.end_time.to_timedelta() !=profile.end_time:
                            #print("soc adaption hat keinen großen einfluss auf available periods")

                            if settingsContainer.getChargingStrategies()[strat_pos] == "as soon as possible" and modus == 0:
                                pos = 0
                                for ap in old_available_periods2:
                                    if not ap[0].same_available_period(available_periods2[pos][0]):
                                        print("Error taap7")
                                    pos = pos +1

                            else:


                                if settingsContainer.getChargingStrategies()[strat_pos] == "as soon as possible":
                                    pos_ap = start_ap_pos
                                    first_adapted = False
                                    while pos_ap < len(old_available_periods2):

                                        ap = old_available_periods2[pos_ap]

                                        if not ap[0].same_available_period(available_periods2[pos_ap][0]):
                                            avp = available_periods2[pos_ap][0]
                                            if ap[0].start_time< avp.start_time and first_adapted:
                                                if not first_adapted:
                                                    first_adapted = True
                                                    if pos_ap -1 >0:
                                                        last_ap = old_available_periods2[pos_ap-1]
                                                        if last_ap[0].available_time - (
                                                            vehicle.time_to_charge(((100-last_ap[0].start_SOC)*vehicle.battery_size)/100-profile.heuristic_dependant["max at start"].energy, start_ap[0].charging_power)>datetime.timedelta(0)):
                                                            print(
                                                                "Error taap9: there should be enough time to charge full")
                                                    if 0 != pos_ap:
                                                        print("Error: taap10: available period before this should be adapted as well(?)")
                                                else:

                                                    if pos_ap - 1 > 0:
                                                        last_ap = old_available_periods2[pos_ap - 1]
                                                        if last_ap[0].available_time - (
                                                                vehicle.time_to_charge(((100 - last_ap[
                                                                    0].start_SOC) * vehicle.battery_size) / 100 - profile.heuristic_dependant["max at start"].energy,
                                                                                       start_ap[
                                                                                           0].charging_power) > datetime.timedelta(
                                                            0)):
                                                            print(
                                                                "Error taap9: there should be enough time to charge full")



                                            else:
                                                if ap[0].start_SOC > avp.start_SOC:
                                                    if start_ap != None and start_ap[3] -profile.end_time > datetime.timedelta(0):
                                                        if vehicle.time_to_charge(vehicle.battery_size-(profile.bdry.e_curr + profile.heuristic_dependant["max at start"].energy), start_ap[0].charging_power)<(start_ap[3]-profile.end_time):


                                                            print("Error taap8: only start time should be different in special cases")
                                                else:
                                                    print(
                                                        "Error taap8: only start time should be different in special cases")


                                        pos_ap = pos_ap + 1




                                elif settingsContainer.getChargingStrategies()[strat_pos] == "as late as possible":
                                    #if profile_modus == 1:
                                     #   print("Error: saatf13")
                                    if start_ap[0].available_time-vehicle.time_to_charge(((start_ap[0].min_SOC-start_ap[0].start_SOC)/100)*(
                                                                                         vehicle.battery_size)-profile.heuristic_dependant["max at start"].energy,start_ap[0].charging_power) < datetime.timedelta(0):
                                        print("Error: saatf10")
                                        # bei erster old available enough time to charge min_soc und profile.heuristic_dependant["max at start"].energy
                                    pos_ap = start_ap_pos
                                    first_adapted = False
                                    while pos_ap < len(old_available_periods2):


                                        ap = old_available_periods2[pos_ap]

                                        if  ap[0].same_available_period(available_periods2[pos_ap][0]):
                                            if pos_ap>0 and available_periods2[pos_ap-1][0].min_SOC!=100:
                                                if len(old_available_periods)==len(pl_times):
                                                    print("Error: saatf11: shouldnt be the same")
                                                else:
                                                    pos_ch = 0
                                                    while old_available_periods2[pos_ap-1][2] >= pl_times[pos_ch][0].to_timedelta() and (
                                                          old_available_periods2[pos_ap-1][2] >= pl_times[pos_ch][1].to_timedelta()):
                                                         pos_ch = pos_ch +1

                                                    if pl_times[pos_ch+1][1].to_timedelta() == available_periods2[pos_ap][0].end_time.to_timedelta():
                                                        #no other
                                                        print("Error: saatf11: no other charging decision between two available periods to charge full, so start soc should be different")




                                            elif pos_ap == 0 and len(old_available_periods2) != len(old_available_periods):
                                                if len(old_available_periods)-len(old_available_periods2)-1 > 0 and (
                                                     old_available_periods[len(old_available_periods-len(old_available_periods2))-1].min_SOC != 100):
                                                        print("Error: saatf15: shouldnt be the same")
                                        else:
                                            avp = available_periods2[pos_ap][0]
                                            if avp.end_time!= ap[0].end_time:
                                                print("Error: saatf12")
                                            else:
                                                if avp.start_SOC > ap[0].start_SOC and profile.heuristic_dependant["max at start"].energy<=0:
                                                    print("Error: saarf14")
                                                if avp.start_time > ap[0].start_time and abs(avp.start_SOC -avp.min_SOC)>1e-12:
                                                    print("Error: saarf14")

                                                if ap[0].available_time - (
                                                                vehicle.time_to_charge(((100 - ap[
                                                                    0].start_SOC) * vehicle.battery_size) / 100 ,
                                                                                       ap[
                                                                                           0].charging_power)) <datetime.timedelta(
                                                            0):
                                                            print(
                                                                "Error taap15: there should be enough time to charge")







                                        pos_ap = pos_ap + 1




                                elif settingsContainer.getChargingStrategies()[strat_pos] == "as long as possible with minimum rate":
                                    # todo
                                    # start_soc ==soc_max -energy consumed von zwischentrips, auper bei ersten war nicht genug zeit um profile energy aufzufangen
                                    # in available period enough time to charge min soc
                                    # end_time similar

                                    if start_ap[0].available_time - vehicle.time_to_charge(
                                            ((start_ap[0].min_SOC-start_ap[0].start_SOC)/ 100) * (
                                                    vehicle.battery_size) - profile.heuristic_dependant["max at start"].energy,
                                                    start_ap[0].charging_power) < datetime.timedelta(0):
                                        print("Error: saatf10")
                                        # bei erster old available enough time to charge min_soc und profile.heuristic_dependant["max at start"].energy
                                    pos_ap = start_ap_pos
                                    first_adapted = False
                                    while pos_ap < len(old_available_periods2):

                                        ap = old_available_periods2[pos_ap]

                                        if ap[0].same_available_period(available_periods2[pos_ap][0]):
                                            if pos_ap > 0 and available_periods2[pos_ap - 1][0].min_SOC != 100:
                                                print("Error: saatf11: shouldnt be the same")
                                            elif pos_ap == 0 and len(old_available_periods2) != len(
                                                    old_available_periods):
                                                if len(old_available_periods) - len(
                                                        old_available_periods2) - 1 > 0 and (
                                                        old_available_periods[len(old_available_periods - len(
                                                            old_available_periods2)) - 1].min_SOC != 100):
                                                    print("Error: saatf15: shouldnt be the same")

                                        else:
                                            avp = available_periods2[pos_ap][0]
                                            if avp.end_time != ap[0].end_time:
                                                #print("Error: saatf12")
                                                a=0
                                            else:
                                                if avp.start_SOC > ap[0].start_SOC:
                                                    print("Error: saarf14")
                                                if avp.start_time > ap[0].start_time and abs(avp.start_SOC-avp.min_SOC) > 1e-12:
                                                    print("Error: saarf14")

                                                if ap[0].available_time - (
                                                        vehicle.time_to_charge(((100 - ap[
                                                            0].start_SOC) * vehicle.battery_size) / 100,
                                                                               ap[
                                                                                   0].charging_power)) < datetime.timedelta(
                                                    0):
                                                    print(
                                                        "Error taap15: there should be enough time to charge")
                                        pos_ap = pos_ap +1

                    else:
                        continue





def adapt_Charging_after_flexibility_provision(profile, dayy):


        #alternative_charging_periods = list()
        #alternative_plug_in_periods = list()
        #alternative_SOC_list = list()
        ev = profile.bdry.vehicle

        alternative_available_period_list = list()
        Charging_times = ev.total_Charging_list[dayy]
        plugin_times = ev.total_plugin_list[dayy]
        available_periods_given = ev.total_available_period_list[dayy]
        soc_list = ev.total_SOC_list[dayy]
        # available_period_pos = 0
        #soc = None
        # profile adaption:
        pos = 0
        # find available period corresponding to profile
        #adapt available_periods in unified format:
        available_periods = list()
        for available_period in available_periods_given:

            if available_period.__class__ != AvailablePeriod:
                day = available_period[1]
                available_period = available_period[0]
                if day > 0:
                    start_time = nptime(0, 0).to_timedelta()
                    end_time = available_period.end_time.to_timedelta() + datetime.timedelta(days = available_period.days-day)
                else:
                    end_time = nptime(23, 59, 59, 999999).to_timedelta()
                    start_time = available_period.start_time.to_timedelta()
                with_days = True
            else:
                day = 0
                start_time = available_period.start_time.to_timedelta()
                end_time = available_period.end_time.to_timedelta()
                with_days = False
            available_periods.append([available_period, day, start_time, end_time, with_days])

        if profile.bdry.vehicle.ID == 3 and dayy == 47 and profile.strat_pos == 1 and profile.modus == "charge":
            print("hi5")
        for ap in available_periods:


            start_time = ap[2]
            end_time = ap[3]
            day = ap[1]
            #available_period = ap[0]
            if not (start_time<= profile.start_time and end_time >= profile.start_time):
                pos = pos + 1
                continue
            else:
                # and compute soc after profile activation

                # computing soc_need

                energy_after_period = profile.heuristic_dependant[settingsContainer.getHeuristics()[0]].energy + profile.bdry.e_curr
                new_bdry = profile.bdry.copy_and_change(profile.end_time, energy_after_period, 0)
                new_bdry.compute_simple_times()
                new_bdry.compute_alternative_t_max_end()

                if settingsContainer.getChargingStrategies()[profile.strat_pos] == "as soon as possible":
                    soc_after_avp1 = ((new_bdry.e_max_end_alternative + new_bdry.e_curr) / ev.battery_size) * 100
                elif settingsContainer.getChargingStrategies()[profile.strat_pos] == "as late as possible":
                    soc_after_avp1 = ((max(new_bdry.e_need,0) + new_bdry.e_curr) / ev.battery_size) * 100
                elif settingsContainer.getChargingStrategies()[profile.strat_pos] == "as long as possible with minimum rate":
                    soc_after_avp1 = ((max(new_bdry.e_max,0) + new_bdry.e_curr) / ev.battery_size) * 100

                if profile.end_time < ap[3]:
                    if with_days and new_bdry.available_period.days>0:
                        alternative_available_period_list.append([new_bdry.available_period,0])
                    else:
                        alternative_available_period_list.append(new_bdry.available_period)
                pos = pos + 1
                break
        pos_ch = 0
        pos_soc_list = 0
        for ch_session in Charging_times:
            #if not (ch_session.start.to_timedelta() <= profile.start_time and ch_session.end.to_timedelta() >= profile.start_time):
            if ch_session.start.to_timedelta()<= profile.start_time:
                pos_ch = pos_ch + 1


                continue
            else:
                break
        #pos_ch = pos_ch + 1
        for entry in soc_list.times:
            if entry.to_timedelta() <= profile.start_time:
                pos_soc_list= pos_soc_list + 1

                continue
            else:
                break
        pos_soc_list = max(0, pos_soc_list -1)

        current_soc = soc_after_avp1

        while pos < len(available_periods) and pos_ch < len(Charging_times):
            if (Charging_times[pos_ch].start.to_timedelta() <= available_periods[pos][2] and
                    Charging_times[pos_ch].end.to_timedelta() >= available_periods[pos][2]):
                #subtract energy consumed

                while  soc_list.states[pos_soc_list]!= "Driving":
                    pos_soc_list = pos_soc_list +1

                pos_soc_list = pos_soc_list +1
                soc_consumed = soc_list.SOC[pos_soc_list-1] - soc_list.SOC[pos_soc_list]
                start_soc = current_soc -soc_consumed
                # compute new available period with soc according to strategy and flex provision
                start_time = Charging_times[pos_ch].start.to_timedelta()
                if start_soc < 0:
                    print("Error acafp4")
                if start_soc != available_periods[pos][0].start_SOC:
                    current_available_period = available_periods[pos][0].copy_and_change(start_time, start_soc, available_periods[pos][1])
                    # only availale periods which last long enough are appended:
                    if current_available_period.check_availability(ev):

                        start_energy = current_available_period.start_SOC * ev.battery_size * 0.01
                        ap_on_next_day = False
                        if start_energy < ev.min_energy:
                            ap_on_next_day, base_charging = current_available_period.period_adaption(ev, start_energy)

                        if not ap_on_next_day:
                            if available_periods[pos][4]:
                                alternative_available_period_list.append([current_available_period, available_periods[pos][1]])
                                if available_periods[pos][1]!= 0:
                                    print("Error acafp3")
                            else:
                                alternative_available_period_list.append(current_available_period)
                else:
                    if settingsContainer.getChargingStrategies()[profile.strat_pos] == "as soon as possible":
                    #    #no adaption of available_periods necessary
                        while pos < len(available_periods_given):
                            alternative_available_period_list.append(available_periods_given[pos])
                            pos = pos +1
                        return alternative_available_period_list
                    else:
                        if available_periods[pos][4]:
                            alternative_available_period_list.append([available_periods[pos][0], available_periods[pos][1]])
                        else:
                            alternative_available_period_list.append(available_periods[pos][0])

                new_bdry = FlexBoundary(available_periods[pos][0], ev)
                new_bdry.compute_boundaries(True)
                if settingsContainer.getChargingStrategies()[profile.strat_pos] == "as soon as possible":
                    new_bdry.compute_alternative_t_max_end()
                    current_soc = ((new_bdry.e_max_end_alternative + new_bdry.e_curr) / ev.battery_size) * 100
                elif settingsContainer.getChargingStrategies()[profile.strat_pos] == "as late as possible":
                    current_soc = ((max(new_bdry.e_need,0) + new_bdry.e_curr) / ev.battery_size) * 100
                elif settingsContainer.getChargingStrategies()[profile.strat_pos] == "as long as possible with minimum rate":
                    current_soc = ((max(new_bdry.e_max,0) + new_bdry.e_curr) / ev.battery_size) * 100
                pos = pos + 1

            else:
                # subtract energy consumed
                while soc_list.states[pos_soc_list]!= "Driving":
                    pos_soc_list = pos_soc_list +1
                pos_soc_list = pos_soc_list +1
                soc_consumed = soc_list.SOC[pos_soc_list-1] - soc_list.SOC[pos_soc_list]
                current_soc = current_soc -soc_consumed
                if len(plugin_times)>len(Charging_times):
                    pos_pl = pos_ch +1
                elif len(plugin_times)== len(Charging_times):
                    pos_pl = pos_ch
                elif len(plugin_times)<len(Charging_times):
                    print("Error: acafp3")
                ev.set_current_station(Charging_times[pos_ch].station)
                charging_end, soc_after_charging, charging_rate = (
                    ev.charging_full_if_possible(plugin_times[pos_pl][0], plugin_times[pos_pl][1], current_soc))
                #charging full, even in charging strategy as late or as long as possible, as this is no available period:
                #Therefore no flexibility delivery possible. Charging stratgy not important, as no flexibility provision
                # charging full acceptable

                current_soc = soc_after_charging
            pos_ch = pos_ch + 1

        # Todo adaption of alternative_available_periods_list? class==avialable_periods? testn
        # available_periods mit mehreren Tagen?
        return alternative_available_period_list

        if False:
            for ch_session in Charging_times:
                if ch_session.start >= profile.start_time:
                    if ch_session.end >= profile.start_time:
                        if settingsContainer.getChargingStrategies()[profile.strat_pos] == "as soon as possible":
                            soc = ch_session.soc_after_charging
                        elif settingsContainer.getChargingStrategies()[profile.strat_pos] == "as late as possible":
                            for available_period in available_periods:
                                if not (
                                        available_period.start_time <= ch_session.start and available_period.end_time >= ch_session.start):
                                    continue
                                else:
                                    # computing soc_need
                                    soc = min(ch_session.soc_after_charging,
                                              max((self.min_energy / self.battery_size) * 100),
                                              available_period.min_SOC)
                                    break
                            if soc == None:
                                print("Error acafp")
                        elif settingsContainer.getChargingStrategies()[profile.strat_pos] == "as long as possible":
                            # computing soc_max
                            for available_period in available_periods:
                                if not (
                                        available_period.start_time <= ch_session.start and available_period.end_time >= ch_session.start):
                                    continue
                                else:
                                    # computing soc_need
                                    soc = max((self.min_energy / self.battery_size) * 100, available_period.min_SOC)
                                    break
                            if soc == None:
                                print("Error acafp")
                            soc = min(ch_session.soc_after_charging, max(settingsContainer.getMaxSoc(), soc))
                        # Charging behaviour between flexes according to strategy, compute_flexibility für zweite flexbereitstellung ebenfalls für gleiche ladestrategie
                        # base charging profiel, sodass echtes ladestrategieverhalten nachgebildet wird (nicht immer vollgeladen) base chargin als profile für flexberechnung
                        # Idee: bis zum
                    else:
                        print("todo")
                else:
                    print("todo")

def recalculate_av_periods(available_periods_given):
        available_periods = list()
        for available_period in available_periods_given:

            if available_period.__class__ != AvailablePeriod:
                day = available_period[1]
                available_period = available_period[0]
                if day > 0:
                    start_time = nptime(0, 0).to_timedelta()
                    end_time = available_period.end_time.to_timedelta() + datetime.timedelta(days = available_period.days-day)
                else:
                    end_time = nptime(23, 59, 59, 999999).to_timedelta()
                    start_time = available_period.start_time.to_timedelta()
                with_days = True
            else:
                day = 0
                start_time = available_period.start_time.to_timedelta()
                end_time = available_period.end_time.to_timedelta()
                with_days = False
            available_periods.append([available_period, day, start_time, end_time, with_days])

        return available_periods