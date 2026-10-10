import datetime

from SimulationTool.simulation import *
from flexibility_calc.flexibility import *

Charging_strategies = settingsContainer.getChargingStrategies()
heuristics = settingsContainer.getHeuristics()

def Test_Spontanflex(spontanflex, spont = True):
    total_energy = list()
    if spont:
        flex_list = spontanflex.spontanflex_list
    else:
        flex_list = spontanflex.fixDate_flex_list
    for i in range(len(Charging_strategies)):
        total_energy.append([0, 0])
    for entry in spontanflex.profile_list:
        if spontanflex.profile_list.count(entry)>1:
            print("Error1-spontanflex-computation: profiles several times appended")
        # check if profiles appended to all AggregatedFlex entries, which are within profile time
        start_time = entry.start_time

        if  entry.__class__==flex_profile:
            if entry.modus == "charge":
                modus_pos = 0
            else:
                modus_pos = 1
        elif entry.__class__==base_profile:
            modus_pos = entry.modus_pos

        for strat_pos in range(len(Charging_strategies)):
            for heuristic_pos in range(len(heuristics)):
                if entry.__class__==flex_profile:
                    end_time = entry.heuristic_dependant[heuristics[heuristic_pos]].charging_end
                else:
                    end_time = entry.end_time
                listttt = flex_list[strat_pos][heuristic_pos][modus_pos].copy()
                listttt.pop(0)
                for AggFlex in listttt:
                    if start_time < AggFlex.end_time and end_time >= AggFlex.end_time and entry.strat_pos == strat_pos:
                        if AggFlex.FlexBoundaries.count(entry) != 1:
                            if not(entry.__class__==base_profile and entry.energy == 0):
                                print("Error-SF2: profile not in appended AggregatedFlex")
                        else:
                            index= AggFlex.FlexBoundaries.index(entry)
                            if False:
                                if AggFlex.end_time == start_time:

                                    if AggFlex.modi[index] != "start":
                                        print("Error-SF4: profile appended wrongly")
                                elif AggFlex.end_time == end_time:
                                    if AggFlex.modi[index] != "end":
                                        print("Error-SF5: profile appended wrongly")
                                elif AggFlex.modi[index] != "middle":
                                    print("Error-SF6: profile appended wrongly")
                    elif AggFlex.FlexBoundaries.count(entry) and AggFlex.end_time != spontanflex.start_time:
                        print("Error-SF3: profile in wrong AggregatedFlex")
            if entry.__class__ == flex_profile:
                energy = ((entry.heuristic_dependant[heuristics[0]].charging_end-start_time).total_seconds()/3600)*entry.heuristic_dependant[heuristics[0]].rate
            else:

                energy = entry.rate* (entry.end_time-entry.start_time).total_seconds()/3600
                if entry.strategy == Charging_strategies[2]:
                    energy = min(energy, entry.bdry.e_max)

                #if entry.modus_pos == 0:
                    #energy = -energy
            if entry.__class__ == flex_profile and modus_pos == 1 and not entry.charge:
                energy = -energy
            if entry.__class__==flex_profile and abs(energy - entry.heuristic_dependant[heuristics[0]].energy) > 1e-8:
                print("Error13-SF: wrong energy")
            elif entry.__class__==base_profile and abs(energy - entry.energy) > 1e-8:
                print("Error14-SF: wrong energy")
            if entry.strat_pos == strat_pos:
                if entry.__class__ == flex_profile:
                    if modus_pos == 1:  #and not entry.charge:
                        total_energy[strat_pos][modus_pos] -= energy
                        #if entry.charge:
                         #   print("hi")
                    #elif modus_pos ==1 and entry.charge:
                     #   total_energy[strat_pos][modus_pos] -= energy
                    else:
                        total_energy[strat_pos][modus_pos] += energy
                elif entry.__class__ == base_profile:
                    if modus_pos == 1:
                        total_energy[strat_pos][modus_pos] += energy
                    else:
                        total_energy[strat_pos][modus_pos] -= energy

    for strat_pos in range(len(Charging_strategies)):
        # check energy
        for mo in range(2):
            if abs(total_energy[strat_pos][mo]-spontanflex.total_capacity[strat_pos][mo]) > 1e-6:
                print("Error11-SF: Energy computed wrongly")
            if spontanflex.total_capacity[strat_pos][mo] < -1e-10:
                print(strat_pos)
                print(modus_pos)
                print("Error15-SF: energy negative")
        for heuristic_pos in range(len(heuristics)):
            for modus_pos in range(2):
                # Test if times and capacities are correct
                Times = list()
                Times2 = list()
                times_end = spontanflex.start
                for entry in flex_list[strat_pos][heuristic_pos][modus_pos]:
                    # times
                    # start_time always the same like previous end time
                    if entry.start_time != times_end:
                        print("Error - SF7: times-spontanflex-computation")
                    Times.append(entry.end_time)
                    Times2.append(entry.start_time)
                    times_end = entry.end_time

                    # capacities
                    capp = 0
                    for pos in range(len(entry.FlexBoundaries)):
                        orig_cap = entry.capacities[pos]
                        prof = entry.FlexBoundaries[pos]
                        if prof.__class__ == flex_profile:
                            cap = prof.heuristic_dependant[heuristics[heuristic_pos]].rate
                            # check if rate is computed correct:
                            if prof.profile == "flex" and heuristics[heuristic_pos] == "as long as possible with minimum rate":
                                # under the assumption that available_time and energy are computed correctly
                                rate = compute_min_charging_rate(prof.available_time, abs(prof.energy), prof.bdry.charging_power)
                            else:
                                if modus_pos == 0:
                                    rate = prof.bdry.charging_power
                                else:
                                    rate = prof.bdry.discharging_power
                                if prof.energy == 0:
                                    rate = 0


                            if rate != prof.heuristic_dependant[heuristics[heuristic_pos]].rate:
                                print("Error: 12-SF: rate not correct")
                            if modus_pos == 1 and prof.charge:
                                rate = -rate
                            cap = rate
                            capp += cap
                            if abs(cap - orig_cap) > 1e-10:
                                print("Error8-SF: comparison; caps not the same")
                        else:
                            if modus_pos == 0:
                                cap = -prof.rate
                            else:
                                cap = prof.rate
                            capp += cap
                            if abs(cap - orig_cap) > 1e-10:
                                print("Error15-SF: comparison; caps not the same")
                    if abs(capp - entry.total_capacity) > 1e-10:
                        print("Error9-SF")
                    if entry.total_capacity<0 and abs(entry.total_capacity)> 1e-8 and heuristics[heuristic_pos]== "max at start": # shouldn_t happen
                        print("Error16-SF: total charging power flexibility_calc negative")



                Test_times(Times)
                Test_times(Times2)

def Test_Model(VehicleList):

    for run in range(settingsContainer.getNumberOfRuns()):
        #if run < 30:
         #   continue
        print(run)
        for vehicle in VehicleList[run]:
            for day in range(settingsContainer.getNumberOfDays()):
                if run == 2 and vehicle.ID == 55 and day == 15:
                    print("Hi")
                if vehicle.total_trip_chain_list[day]!= None:
                    if len(vehicle.total_plugin_list[day])>0:
                        count = 0
                        count_available_periods = 0
                        count_base_charging = 0
                        home = False
                        skip_first = False
                        if len(vehicle.total_plugin_list[day]) != len(vehicle.total_Charging_list[day]):
                            if vehicle.total_plugin_list[day][0][0] != nptime(0):
                                print("Error - M1a: charging list and plugin list do not have same length")
                            else:
                                skip_first = True
                        elif vehicle.total_plugin_list[day][0][0] == nptime(0):
                            counter2 = 0
                            while counter2 < day and len(vehicle.total_Charging_list[day-counter2])== 0:
                                counter2 += 1
                            if counter2 < day:
                                if vehicle.total_SOC_list[day].states[0] != "Charging":
                                    print("Error: - M1b: charging list and plugin list do not have same length")
                            else:
                                home = True # home at the beginning


                        idx = -1
                        for plugin in vehicle.total_plugin_list[day]:
                            if count > 0:
                                home = False

                            if len(vehicle.total_plugin_list[day]) == 1 and len(vehicle.total_Charging_list[day])==0:
                                break
                            elif not skip_first:
                                    if plugin[0]!=vehicle.total_Charging_list[day][count].start:
                                        print("Error - M2: charging start time differs from plug in time")
                                    elif plugin[1]< vehicle.total_Charging_list[day][count].end:
                                        print("Error -M3: charging lasts longer than plugin time")

                                    trip_count = count

                                    count_trips_with_plugin = 0
                                    trip_found = False
                                    for trip_idx in range(0, len(vehicle.total_trip_chain_list[day].trips)):
                                        trip = vehicle.total_trip_chain_list[day].trips[trip_idx]
                                        if trip.arrival != plugin[0]:
                                            if day > 0 and vehicle.total_trip_chain_list[day - 1].last_time_on_next_day and plugin[0] ==vehicle.total_trip_chain_list[day - 1].trips[-1].arrival:
                                                trip_found = True
                                                break
                                            else:
                                                #if trip.departure == plugin[1]:
                                                    #break
                                                continue

                                        else:
                                            count_trips_with_plugin +=1
                                            if trip_idx+1 < len(vehicle.total_trip_chain_list[day].trips) and plugin[1]>vehicle.total_trip_chain_list[day].trips[trip_idx+1].departure:
                                                print("Error -M4: plugin end after departure")
                                            elif trip_idx+1 == len(vehicle.total_trip_chain_list[day].trips):
                                                if plugin[1]!= nptime(23,59,59,999999) and not (vehicle.total_trip_chain_list[day].last_time_on_next_day and vehicle.total_trip_chain_list[day].last_trip_arrival==plugin[1]):
                                                    print("Error -M5: plugin and trips don't fit together")
                                                if get_purposes_category(trip.purpose) == ChargingStationPlace.HOME:

                                                    home = True
                                                    if vehicle.total_Charging_list[day][count].station != vehicle.user.ChargingStation:
                                                        print("Error -M6: wrong charging station")
                                                #trip_found = True
                                                break
                                            else:
                                                if get_purposes_category(trip.purpose) == ChargingStationPlace.HOME:

                                                    home = True
                                                    if vehicle.total_Charging_list[day][count].station != vehicle.user.ChargingStation:
                                                        print("Error -M6: wrong charging station")
                                                trip_found = True

                                                break
                                                #print("hi")
                                        #else: should be public or work station , difficult to check
                                    if vehicle.total_SOC_list[day].states.count("Charging") != len(vehicle.total_Charging_list[day]):
                                        print("Error -M7: soc list and charging list do not fit togehter")
                                    else:
                                        idx = vehicle.total_SOC_list[day].states.index("Charging", idx+1)
                                        if vehicle.total_SOC_list[day].SOC[idx] != vehicle.total_Charging_list[day][count].soc_before_charging:
                                            print("Error -M8: wrong soc at beginning of charging")
                                        elif idx < len(vehicle.total_SOC_list[day].SOC) and vehicle.total_SOC_list[day].SOC[idx+1] != vehicle.total_Charging_list[day][count].soc_after_charging:
                                            print("Error -M9: wrong soc at end of charging")
                                        else:
                                            #check charged energy
                                            energy = vehicle.charge(vehicle.total_SOC_list[day].times[idx+1]-vehicle.total_SOC_list[day].times[idx], vehicle.total_Charging_list[day][count].rate)
                                            if abs((energy /vehicle.battery_size)*100 - (vehicle.total_SOC_list[day].SOC[idx+1]-vehicle.total_SOC_list[day].SOC[idx]))>1e-8:
                                                print("Error -M10: SOC computation/charging")
                                            if vehicle.total_SOC_list[day].SOC[idx+1]!= 100:
                                                if plugin[1]!= vehicle.total_Charging_list[day][count].end:
                                                    print("Error -M11: if not fully charged, charging end time should equal plugin end time")
                                                elif plugin[1] != nptime(23,59,59,999999) :
                                                    maybe_available = False
                                                else:
                                                    maybe_available = True
                                                    #print("hi")
                                            else:
                                                maybe_available = True
                                            if maybe_available:
                                                if vehicle.total_SOC_list[day].states[idx+1] != "parkingPluggedIn":
                                                    print("Error -14: wrong SOC status in SOC list")

                                                if plugin[1] == vehicle.total_Charging_list[day][count].end and plugin[1]!= nptime(23,59,59,999999):
                                                    print("Error -M12: if fully charged, charging end time should not equal plugin end time")
                                                    # except special casee, that charged exactly full in available time
                                                driving_idx = idx+3
                                            else: #maybe available = False (base charging
                                                driving_idx = idx +2
                                                if vehicle.total_SOC_list[day].states[idx+1] != "Driving":
                                                    if vehicle.total_trip_chain_list[day].last_time_on_next_day and vehicle.total_SOC_list[day].states[idx+1] != "parkingPluggedIn":
                                                        print("Error -14b: wrong SOC status in SOC list")
                                                    else:
                                                        count +=1
                                                        continue
                                                if plugin[1] != vehicle.total_Charging_list[day][count].end:
                                                    print("Error -M12b: if not fully charged, charging end time should  equal plugin end time")


                                            plugin_end = plugin[1].to_timedelta()
                                            charging_end = vehicle.total_Charging_list[day][count].end.to_timedelta()
                                            charging_power = vehicle.total_Charging_list[day][count].rate
                                            home = vehicle.total_Charging_list[day][count].station.Place == 'home'
                                            #available periods
                                            if trip_idx < len(vehicle.total_trip_chain_list[day].trips)-1 or (len(vehicle.total_trip_chain_list[day].trips) > 0 and vehicle.total_trip_chain_list[day].trips[0].departure == plugin[1]):
                                                    min_SOC = min(max(vehicle.total_SOC_list[day].SOC[idx + 1] -
                                                    vehicle.total_SOC_list[day].SOC[driving_idx] + settingsContainer.getSocTol(), settingsContainer.getMinSoc()), 100)
                                            elif trip_idx == len(vehicle.total_trip_chain_list[day].trips) - 1:
                                                #if not trip_found:
                                                    counter = 1
                                                    while day+counter < settingsContainer.getNumberOfDays() and len(vehicle.total_trip_chain_list[day + counter].trips) == 0:
                                                            counter += 1
                                                    if day +counter >= settingsContainer.getNumberOfDays():
                                                        count +=1
                                                        continue
                                                    if vehicle.total_SOC_list[day + counter].states.count(
                                                            "Driving")==0:
                                                            print("Error, driving not in list")
                                                    idx2 = vehicle.total_SOC_list[day + counter].states.index(
                                                            "Driving")+1
                                                    min_SOC = min(vehicle.total_SOC_list[day+counter].SOC[idx2- 1] -
                                                               vehicle.total_SOC_list[day + counter].SOC[
                                                                   idx2] + settingsContainer.getSocTol(),100)
                                                    if plugin[1] == nptime(23, 59, 59, 999999):
                                                        plugin_end = vehicle.total_SOC_list[day+counter].times[idx2].to_timedelta() + datetime.timedelta(days = counter)
                                                    if vehicle.total_Charging_list[day][count].end == nptime(23,59,59,999999):
                                                        if len(vehicle.total_SOC_list[day+1].times)==1:
                                                            print("hi")
                                                        charging_end = vehicle.total_SOC_list[day+1].times[1].to_timedelta() + datetime.timedelta(days = 1)
                                                #else:
                                                #    min_SOC = min(vehicle.total_SOC_list[day].SOC[idx + 1] -
                                                 #                 vehicle.total_SOC_list[day].SOC[
                                                 #                     driving_idx] + SOC_TOL, 100)
                                            start_SOC = vehicle.total_SOC_list[day].SOC[idx]

                                            if min_SOC > start_SOC:
                                                Time_to_charge = vehicle.time_to_charge(
                                                    (min_SOC - start_SOC) * 0.01 * vehicle.battery_size, charging_power)

                                            else:
                                                Time_to_charge = datetime.timedelta(0)
                                            Time_to_charge2 = vehicle.time_to_charge((100 - start_SOC) * 0.01 * vehicle.battery_size, charging_power)
                                            charging_start = vehicle.total_Charging_list[day][count].start.to_timedelta()
                                            if charging_start == datetime.timedelta(0) and day > 0:
                                                charging_start = vehicle.total_Charging_list[day-1][-1].start.to_timedelta() - datetime.timedelta(days = 1)
                                            if (charging_end-charging_start)>=Time_to_charge2-datetime.timedelta(microseconds=100000):
                                                Available = True
                                            else:
                                                Available = False
                                            if Available and maybe_available and ((plugin_end-charging_end) > settingsContainer.getMinFlexTime() or ((plugin_end - (charging_start + Time_to_charge)) > settingsContainer.getMinFlexTime())):
                                                        if len(vehicle.total_available_period_list[day])-1< count_available_periods:
                                                            counter3= 1
                                                            while day+counter3 < settingsContainer.getNumberOfDays() and vehicle.total_plugin_list[day+counter3][0][1]== nptime(23,59,59,999999):
                                                                counter3 += 1
                                                            if day + counter3 >= settingsContainer.getNumberOfDays():
                                                                continue
                                                            else:
                                                                print("hi")
                                                        curr_ap =vehicle.total_available_period_list[day][count_available_periods]

                                                        count_available_periods += 1
                                            else:

                                                        # base charging
                                                        if len(vehicle.total_base_charging_periods_list[day])-1< count_base_charging:
                                                            print("hi")
                                                        curr_ap = vehicle.total_base_charging_periods_list[day][count_base_charging]

                                                        count_base_charging += 1

                                            if curr_ap.__class__ != AvailablePeriod:
                                                        day2 = curr_ap[1]
                                                        curr_ap = curr_ap[0]

                                                        if day2 == 0:
                                                            start_time = vehicle.total_Charging_list[day][count].start
                                                        else:
                                                            start_time = vehicle.total_Charging_list[day-day2][-1].start
                                                        if curr_ap.start_time != start_time:
                                                            print(
                                                                "Error -M13a: available period and plugin do not fit together")
                                                        #elif # not urgent TODO check other variables for available periods lasting overnigth
                                            else:
                                                        if curr_ap.start_time != vehicle.total_Charging_list[day][count].start:
                                                                print("Error -M13a: available period and plugin do not fit together")
                                                        elif curr_ap.end_time.to_timedelta() != plugin_end:#plugin[1]:
                                                                print(
                                                                    "Error -M13b: available period and plugin do not fit together")
                                                        elif curr_ap.start_SOC != start_SOC:
                                                                print(
                                                                    "Error -M13c: available period and plugin do not fit together")
                                                        elif home != curr_ap.home:
                                                                print(
                                                                    "Error -M13d: available period and plugin do not fit together")
                                                        elif min_SOC!= curr_ap.min_SOC:
                                                                if day != 0:
                                                                    print(
                                                                    "Error -M13f: available period and plugin do not fit together")
                                                            #else: charging_power,discharging_power,days to check





                            count += 1
                        #check soc_list:
                        # Driving, Only Parking und SOC/times richtig für alle trips
                        if len(vehicle.total_SOC_list[day].states) != len(vehicle.total_SOC_list[day].SOC) and len(vehicle.total_SOC_list[day].SOC)!= len(vehicle.total_SOC_list[day].times):
                            print("Error -M15: SOC list lists with different sizes")

                    count_trip = 0
                    count_charging = 0
                    count_plugged_in = 0
                    for i in range(len(vehicle.total_SOC_list[day].states)-1):
                            current_state = vehicle.total_SOC_list[day].states[i]
                            if current_state == "Driving":
                                if vehicle.total_SOC_list[day].states[i+1]!= "OnlyParking" and vehicle.total_SOC_list[day].states[i+1] != "Charging":
                                    print("Error -M16a: SOC list states not correct")
                                SOC_difference = (vehicle.total_SOC_list[day].SOC[i]-vehicle.total_SOC_list[day].SOC[i+1])
                                if settingsContainer.getEnergyConsmuption() == "constant":
                                    energy_consumed = (vehicle.ec_d_avg * (vehicle.total_trip_chain_list[day].trips[count_trip].distance))/vehicle.battery_size  *1.2

                                    if abs(SOC_difference - energy_consumed)>1e-8:
                                        print("Error - M17a: wrong calculation of energy consumption")
                                if vehicle.total_trip_chain_list[day].trips[count_trip].arrival != vehicle.total_SOC_list[day].times[i+1]:
                                    print("Error - M18a: wrong time in SOC List")
                                elif vehicle.total_trip_chain_list[day].trips[count_trip].departure != vehicle.total_SOC_list[day].times[i]:
                                    print("Error - M19a: wrong time in SOC List")
                                count_trip +=1
                            elif current_state == "Charging" or current_state == "parkingPluggedIn" or current_state == "OnlyParking":
                                if vehicle.total_SOC_list[day].states[i+1]!= "parkingPluggedIn" and vehicle.total_SOC_list[day].states[i+1] != "Driving":
                                    print("Error -M16b: SOC list states not correct")
                                if current_state == "Charging":
                                    if i < len(vehicle.total_SOC_list[day].SOC):
                                        SOC_difference = (vehicle.total_SOC_list[day].SOC[i+1] -
                                                          vehicle.total_SOC_list[day].SOC[i])
                                        energy_charged = vehicle.charge(
                                            vehicle.total_SOC_list[day].times[i+1] - vehicle.total_SOC_list[day].times[i], vehicle.total_Charging_list[day][count_charging].rate) / vehicle.battery_size
                                        if abs(SOC_difference - energy_charged * 100) > 1e-8:
                                            print("Error - M17b: wrong calculation of energy cahrging")
                                        if vehicle.total_Charging_list[day][count_charging].end != \
                                                vehicle.total_SOC_list[day].times[i+1]:
                                            print("Error - M18b: wrong time in SOC List")
                                        elif vehicle.total_Charging_list[day][count_charging].start != \
                                                vehicle.total_SOC_list[day].times[i ]:
                                            print("Error - M19b: wrong time in SOC List")
                                    count_charging += 1
                                    if i +1 < len(vehicle.total_SOC_list[day].states) and vehicle.total_SOC_list[day].states[i+1] != "parkingPluggedIn":

                                        if vehicle.total_plugin_list[day][count_plugged_in][1] != \
                                                vehicle.total_SOC_list[day].times[i + 1]:
                                            print("Error - M18c: wrong time in SOC List")
                                        elif vehicle.total_plugin_list[day][count_plugged_in][0] != \
                                                vehicle.total_SOC_list[day].times[i]:
                                            if i - 1 >= 0 and vehicle.total_SOC_list[day].states[i - 1] == "Charging":
                                                if vehicle.total_plugin_list[day][count_plugged_in][0] != \
                                                        vehicle.total_SOC_list[day].times[i - 1]:
                                                    print("Error - M19c1: wrong time in SOC List")
                                            else:  # if i==0:
                                                print("Error - M19c2: wrong time in SOC List")
                                        count_plugged_in += 1

                                elif current_state == "parkingPluggedIn":
                                    if i < len(vehicle.total_SOC_list[day].SOC):
                                        SOC_difference = (vehicle.total_SOC_list[day].SOC[i+1] -
                                                          vehicle.total_SOC_list[day].SOC[i])

                                        if abs(SOC_difference) > 1e-8:
                                            print("Error - M17c: wrong calculation of SOC during parking")
                                        if len(vehicle.total_plugin_list[day])<=count_plugged_in:
                                            print("hi")
                                        if vehicle.total_plugin_list[day][count_plugged_in][1] != \
                                                vehicle.total_SOC_list[day].times[i+1]:
                                            print("Error - M18c: wrong time in SOC List")
                                        elif vehicle.total_plugin_list[day][count_plugged_in][0] != \
                                                vehicle.total_SOC_list[day].times[i]:
                                            if i-1>= 0 and vehicle.total_SOC_list[day].states[i-1]== "Charging":
                                                if vehicle.total_plugin_list[day][count_plugged_in][0] != \
                                                vehicle.total_SOC_list[day].times[i-1]:
                                                    print("Error - M19c1: wrong time in SOC List")
                                            else :#if i==0:
                                                print("Error - M19c2: wrong time in SOC List")

                                    count_plugged_in += 1

def Test_times(list):
    # Testing times creaated
    count = 0
    for ii in list:
        if count + 1 < len(list):
              if ii > list[count + 1]:
                    print("Error: Test-times")
        count += 1

def Test_Flex(cap_list):
    # under assumption that right modus was chosen and
    for entry in cap_list:
        if abs(sum(entry.capacities) - entry.total_capacity) > 1e-10:
            print("Error1")
        capp = 0
        for i in range(len(entry.modi)):
            bdry = entry.FlexBoundaries[i]
            modus = entry.modi[i]
            orig_cap = entry.capacities[i]
            end = entry.end_time + datetime.timedelta(days = entry.days[i])
            start = entry.start_time + datetime.timedelta(days = entry.days[i])
            if modus == "max":
                if not(bdry.t_max_end <= end and bdry.t_end >= start):
                    print("Error10: wrong modus")
                cap = bdry.e_max
                capp += cap
            elif modus == "min":
                if not(bdry.t_min_end <= end and bdry.t_min_start2 >= start):
                    print("Error9: wrong modus")
                cap = bdry.e_min
                capp += cap
            elif modus == "charge_to_max" or modus == "ch_start":
                if not(bdry.t_start <= end and bdry.t_max_end >= start):
                    print("Error4: wrong modus")
                if bdry.t_start < end:
                    if bdry.t_start > start:
                        print("Error11")
                    cap = bdry.vehicle.charge(end-start, bdry.charging_power)
                elif bdry.t_start == end:
                    cap = 0
                if bdry.t_start < start:
                    cap += bdry.vehicle.charge(start-bdry.t_start, bdry.charging_power)
                capp += cap
            elif modus == "charge_to_min" or modus == "ch_min_start":
                if bdry.e_min < 0:
                    print("Error1-Test-Flex")
                if not(bdry.t_start <= end and bdry.t_min_end >= start):
                    print("Error5: wrong modus")
                if bdry.t_start < end:
                    if bdry.t_start > start:
                        print("Error11")
                    cap = bdry.vehicle.charge(end - start, bdry.charging_power)
                elif bdry.t_start == end:
                    cap = 0
                if bdry.t_start < start:
                    cap += bdry.vehicle.charge(start - bdry.t_start, bdry.charging_power)
                capp += cap
            elif modus == "discharge_to_min" or modus == "dc_start":
                if bdry.e_min > 0:
                    print("Error1-Test-Flex")
                if not(bdry.t_start <= end and bdry.t_min_end >= start):
                    print("Error6: wrong modus")
                if bdry.t_start < end:
                    if bdry.t_start > start:
                        print("Error11")
                    cap = - bdry.vehicle.discharge(end - start, bdry.discharging_power)
                elif bdry.t_start == end:
                    cap = 0
                if bdry.t_start < start:
                    cap -= bdry.vehicle.discharge(start - bdry.t_start, bdry.discharging_power)
                capp += cap
            elif modus == "charge_to_need":
                if not(bdry.t_min_start2 <= end and bdry.t_end >= start):
                    print("Error7: wrong modus")
                if bdry.t_min_start2 < end:
                    if bdry.t_min_start2 > start:
                        print("Error11")
                    cap = bdry.vehicle.charge(end - start, bdry.charging_power)+bdry.e_min
                elif bdry.t_start == end:
                    cap = 0
                if bdry.t_min_start2 < start:
                    cap += bdry.vehicle.charge(start - bdry.t_min_start2, bdry.charging_power)
                capp += cap
            elif modus == "need":
                if bdry.t_end != end:
                    print("Error8: wrong modus")
                cap = bdry.e_need
                capp += cap
            elif modus == "start":
                cap = 0
                capp += cap
            else:
                print("wrong modus")
            if abs(cap-orig_cap) > 1e-10:
                print("Error2: comparison; caps not the same")
        if abs(capp-entry.total_capacity) > 1e-10:
            print("Error3")

       # print(entry.total_capacity)

def Test_right_Boundaries(times_list, times_list_dc, cap_list, cap_list_dc, Flex_list):
    for entry in Flex_list:
        Flex = entry[0]
        bool_table = entry[1]

        # substract days, such that only timedeltas < datetime.timedelta(days=1) are in list
        times = [Flex.t_start - datetime.timedelta(Flex.t_start.days),
                     Flex.t_max_end - datetime.timedelta(Flex.t_max_end.days),
                     Flex.t_min_end - datetime.timedelta(Flex.t_min_end.days),
                     Flex.t_min_start2 - datetime.timedelta(Flex.t_min_start2.days),
                     Flex.t_end - datetime.timedelta(Flex.t_end.days)]
        start_time_c = None
        start_time_dc = None
        end_time = None
        for case in range(5):
            if bool_table[case]:
                if start_time_c== None and (case == 1 or case == 0):
                    if case==4:
                        start_time_c=0
                    else:
                        start_time_c=times[case]
                if start_time_dc== None and (case ==2 or case == 0 or case ==3):
                    if case==4:
                        start_time_dc=0
                    else:
                        start_time_dc=times[case]

                if case == 4:
                    end_time = times[case]
            elif case == 4:
                end_time = datetime.timedelta(days=1)
        if start_time_c == None:
            start_time_c = datetime.timedelta(0)
        if start_time_dc == None:
            start_time_dc = datetime.timedelta(0)
        start_idx_c = times_list.index(start_time_c, 0)+1
        end_idx_c = times_list.index(end_time, start_idx_c-1)
        start_idx_dc = times_list_dc.index(start_time_dc, 0)+1
        end_idx_dc = times_list_dc.index(end_time, start_idx_dc-1)

        for idx in range(start_idx_c, end_idx_c):
            if cap_list[idx].FlexBoundaries.count(Flex)==0:
                print("Error: Flex not in list")
            found = cap_list[idx].FlexBoundaries.index(Flex)
            if cap_list[idx].FlexBoundaries.count(Flex) >1:
                print("Error: Flex several times in list")

        for idx in range(start_idx_dc, end_idx_dc):

            if cap_list_dc[idx].FlexBoundaries.count(Flex)==0:
                print("Error: Flex not in list")
            found = cap_list_dc[idx].FlexBoundaries.index(Flex)
            if cap_list_dc[idx].FlexBoundaries.count(Flex) > 1:
                print("Error: Flex several times in list")

def Test_aggregated_power_boundaries(flex):

    for entry in flex.power_cap_ch:
        if abs(sum(entry.capacities) - entry.total_capacity) > 1e-10:
            print("Error1")
        capp = 0
        for i in range(len(entry.modi)):
            bdry = entry.FlexBoundaries[i]
            modus = entry.modi[i]
            orig_cap = entry.capacities[i]
            end = entry.end_time + datetime.timedelta(days=entry.days[i])
            start = entry.start_time + datetime.timedelta(days=entry.days[i])
            if modus == "charge":
                if not (bdry.charging_start <= end and bdry.charging_stop >= start):
                    print("Error10: wrong modus")
                cap = bdry.charging_power
                capp += cap
            elif modus == "discharge":
                if not (bdry.discharging_start <= end and bdry.discharging_stop >= start):
                    print("Error9: wrong modus")
                cap = bdry.discharging_power
                capp += cap
                if abs(cap - orig_cap) > 1e-10:
                    print("Error2: comparison; caps not the same")
        if abs(capp - entry.total_capacity) > 1e-10:
            print("Error3")

def Test_right_boundaries_appended_to_Spontanflex(spontanflex):
    checked_boundaries = list()
    #for entry in spontanflex.checked_flex_boundaries:
        #checked_boundaries.append(entry[0])
    for strat_pos in range(len(Charging_strategies)):
        count = 0
        for entry in spontanflex.checked_flex_boundaries[strat_pos]:
            if len(spontanflex.checked_flex_boundaries_days[strat_pos]) != len(spontanflex.checked_flex_boundaries[strat_pos]):
                print("Error SPntanflex")
            entry = [entry, spontanflex.checked_flex_boundaries_days[strat_pos][count]]
            if spontanflex.checked_flex_boundaries[strat_pos].count(entry[0]) > 1:
                print("Error 1, Spontanflex: entry several times")

            times = [entry[0].t_start - datetime.timedelta(days = entry[1]),
                 entry[0].t_max_end - datetime.timedelta(days = entry[1]),
                 entry[0].t_min_end - datetime.timedelta(days = entry[1]),
                 entry[0].t_min_start2 - datetime.timedelta(days = entry[1]),
                 entry[0].t_end - datetime.timedelta(days = entry[1])]
            bool_table_of_times = [(times[i]>=datetime.timedelta(0) and times[i]<datetime.timedelta(days=1)) for i in range(len(times))]
            start_time =times[0]
            end_time =times[4]
            if entry[1] != 0 and entry[1] <entry[0].available_period.days:
                whole_day = True
            else:
                whole_day = False
            if not(start_time <spontanflex.end and end_time > spontanflex.start):
                if not(whole_day):
                    print("Error 2, Spontanflex: bdry not suitable")
            elif not(whole_day):
                if bool_table_of_times[4] and end_time  < spontanflex.start:
                    print("error 3: SPontanflex")
                elif bool_table_of_times[0] and start_time > spontanflex.end:
                    print("error 3: SPontanflex")
            count += 1


def compare_fixDate_with_spontanflex(fixDate_flex, spontan_flex):
    for strat_pos in range(len(Charging_strategies)):
        for modus_pos in [0,1]:
            for heuristic_pos in range(len(heuristics)):
                if len(fixDate_flex.fixDate_flex_list[strat_pos][heuristic_pos][modus_pos]) != len(spontan_flex.spontanflex_list[strat_pos][heuristic_pos][modus_pos]):
                    print("Error: flex comparison")
                else:
                    count = 0
                    for entry in fixDate_flex.fixDate_flex_list[strat_pos][heuristic_pos][modus_pos]:
                        if abs(entry.total_capacity-spontan_flex.spontanflex_list[strat_pos][heuristic_pos][modus_pos][count].total_capacity)> 1e-7:
                            print("Error2: flex comparison")
                        count += 1


def compare_available_periods(ap1, ap2):
    same = False
    if ap1.start_time!= ap2.start_time:
        print("NottheSame")
    elif ap1.end_time!= ap2.end_time:
        print("NottheSame")
    elif ap1.min_SOC != ap2.min_SOC:
        print("NottheSame")
    elif ap1.start_SOC != ap2.start_SOC:
        print("NottheSame")
    elif ap1.charging_power != ap2.charging_power:
        print("NottheSame")
    elif ap1.discharging_power!= ap2.discharging_power:
        print("NottheSame")
    elif ap1.days != ap2.days:
        print("NottheSame")
    elif ap1.min_SOC != ap2.min_SOC:
        print("NottheSame")
    else:
        same = True

    return same


def test_momentary_potential_independant_of_strategy(flex_one_day, times, strat_pos):
    for time in times:
        idx = flex_one_day.momentary_potentials.times[strat_pos].index(time)
        entry = flex_one_day.momentary_potentials.entries[strat_pos][idx]
        index = flex_one_day.flex_times_c.index(time)
        my_cap_e = [0,0]
        my_cap_p = [0,0]
        pos = 0
        for bdry in flex_one_day.flex_capacities_c[index].FlexBoundaries:
            old_day = flex_one_day.flex_capacities_c[index].days[pos]
            # if pos ==28:
            #   print("hi")
            charging_strategy = settingsContainer.getChargingStrategies()[strat_pos]
            energy = compute_charged_until_certain_time_according_to_Charging_strategy(bdry, time + datetime.timedelta(
                days=old_day),
                                                                                       charging_strategy)

            new_bdry = bdry.copy_and_change(time, bdry.e_curr + energy, old_day)
            # new_bdry.compute_boundaries(True) #evtl weg
            new_bdry.compute_simple_times()
            i = 0
            while i < len(entry.boundaries0) and bdry.vehicle.ID != entry.boundaries0[i].vehicle.ID:
                i+= 1
            if i == len(entry.boundaries0):
                if bdry.t_max_end - datetime.timedelta(days = old_day) - time > settingsContainer.getMinDeliveryTime() and bdry.e_max>0:
                    print("Error- mp_without_strat1: bdry not appended")
            else:

                if abs(new_bdry.e_max - (bdry.e_max-energy))>1e-8:
                    if settingsContainer.getChargingStrategies()[strat_pos] == "as soon as possible":
                        print("Error-  mp_without_strat1: should be possible to reach e_max")

                my_cap_e[0] += new_bdry.e_max
                if new_bdry.e_max != 0:
                    my_cap_p[0] += bdry.charging_power

            i = 0
            while i < len(entry.boundaries1) and bdry.vehicle.ID != entry.boundaries1[i].vehicle.ID:
                i += 1
            if i == len(entry.boundaries1):
                if new_bdry.t_min_end -  time > settingsContainer.getMinDeliveryTime():
                    print("Error- mp_without_strat2: bdry not appended")
            else:
                #new_bdry = bdry.copy_and_change(time, bdry.e_curr + energy, old_day)
                # new_bdry.compute_boundaries(True) #evtl weg
                #new_bdry.compute_simple_times()
                if new_bdry.e_min <=0:
                    if ((bdry.e_min-energy)-new_bdry.e_min) > 1e-8:
                        print("Error mp: e_min wrong")
                    if new_bdry.t_min_end - time > settingsContainer.getMinDeliveryTime():

                        my_cap_e[1] += new_bdry.e_min#bdry.e_min - energy
                        if new_bdry.e_min != 0:
                            my_cap_p[1] += bdry.discharging_power
                else:
                    print("Error: mp")

            pos += 1

        energy = entry.getTotalEnergy()
        power = entry.getTotalPower()
        if abs(my_cap_e[0]-energy[0])>1e-8:
            print("Error- mp_without_strat3: wrong energy computed")
        if abs(my_cap_e[1]-energy[1])>1e-8:
            print("Error- mp_without_strat4: wrong energy computed")
        if abs(my_cap_p[0]-power[0])>1e-8:
            print("Error- mp_without_strat5: wrong power computed")
        if abs(my_cap_p[1]-power[1])>1e-8:
            print("Error- mp_without_strat6: wrong power computed")


def test_momentary_potential_dependant_of_strategy(flex_one_day, times, strat_pos):
    for time in times:
        idx = flex_one_day.momentary_potentials.times[strat_pos].index(time)
        entry = flex_one_day.momentary_potentials.entries[strat_pos][idx]
        index = flex_one_day.flex_times_c.index(time)
        my_cap_e = [0,0]
        my_cap_p = [0,0]
        strat_energy = 0
        pos = 0
        for bdry in flex_one_day.flex_capacities_c[index].FlexBoundaries:
            old_day = flex_one_day.flex_capacities_c[index].days[pos]
            if pos ==6:
                kl = 0
               #print("hi")
            charging_strategy = settingsContainer.getChargingStrategies()[strat_pos]
            energy = compute_charged_until_certain_time_according_to_Charging_strategy(bdry, time + datetime.timedelta(
                days=old_day),
                                                                                       charging_strategy)


            new_bdry = bdry.copy_and_change(time, bdry.e_curr + energy, old_day)
            # new_bdry.compute_boundaries(True) #evtl weg
            new_bdry.compute_simple_times()
            if new_bdry.ch_rate_strategy_info == None:
                rate = bdry.charging_power
            else:
                rate = bdry.ch_rate_strategy_info

            i = 0
            while i < len(entry.profiles) and (bdry.vehicle.ID != entry.profiles[i].bdry.vehicle.ID or (entry.profiles[i].__class__ == flex_profile and entry.profiles[i].modus == "discharge") or (entry.profiles[i].__class__ == base_profile) ):
                if (bdry.vehicle.ID == entry.profiles[i].bdry.vehicle.ID):
                    if (entry.profiles[i].__class__ == flex_profile and entry.profiles[i].modus == "charge") and (
                                entry.profiles[i].__class__ != base_profile):
                        print("hi")
                i+= 1
            if i == len(entry.profiles):
                if new_bdry.t_max_end - time > settingsContainer.getMinDeliveryTime() and bdry.e_max>0:
                    if settingsContainer.getChargingStrategies()[strat_pos] != "as soon as possible":
                        print("Error- mp_with_strat1: bdry not appended")

            else:

                if abs(new_bdry.e_max - (bdry.e_max-energy))>1e-8:
                    if new_bdry.e_curr  < bdry.vehicle.battery_size and  bdry.e_max+bdry.e_curr < new_bdry.e_curr and settingsContainer.getChargingStrategies()[strat_pos] != "as soon as possible":
                            print("Error-  mp_without_strat1: should be possible to reach e_max")

                if (new_bdry.t_max_end - time )> settingsContainer.getMinDeliveryTime():
                    energ = compute_charged_until_certain_time_according_to_Charging_strategy(new_bdry, max(new_bdry.t_max_end , time), charging_strategy)
                    if energ == 0:
                        rate = 0
                    strat_energy += energ
                    if abs(new_bdry.e_max - entry.profiles[i].energy) > 1e-8:
                        print("Error")
                    if entry.profiles[i + 1].__class__ == base_profile and entry.profiles[i + 1].modus_pos == 0:
                        if entry.profiles[i + 1].energy != energ:
                            print("Error")
                    elif entry.profiles[i + 2].__class__ == base_profile and entry.profiles[i + 2].modus_pos == 0:
                        if entry.profiles[i + 2].energy != energ:
                            print("Error")
                    elif energ > 0:
                        if entry.profiles[i].available_time == None or entry.profiles[
                            i].available_time <= settingsContainer.getMinDeliveryTime():
                            print("Error")
                    if new_bdry.e_max - energ > 1e-8:
                        my_cap_e[0] += new_bdry.e_max - energ

                        if new_bdry.e_max != 0:
                            my_cap_p[0] += bdry.charging_power - rate

            i = 0
            while i < len(entry.profiles) and (bdry.vehicle.ID != entry.profiles[i].bdry.vehicle.ID or (entry.profiles[i].__class__ == flex_profile and entry.profiles[i].modus == "charge") or (entry.profiles[i].__class__ == base_profile) ):
                if (bdry.vehicle.ID == entry.profiles[i].bdry.vehicle.ID):
                    if (entry.profiles[i].__class__ == flex_profile and entry.profiles[i].modus == "discharge") and (
                        entry.profiles[i].__class__ != base_profile):
                        print("hi")
                i += 1
            if i == len(entry.profiles):
                if new_bdry.t_min_end - time > settingsContainer.getMinDeliveryTime():
                    print("Error- mp_with_strat1 bdry not appended")
            else:
                if new_bdry.e_min < 0:
                    if ((bdry.e_min-energy)-new_bdry.e_min) > 1e-8:
                        print("Error mp: e_min wrong")
                    if new_bdry.t_min_end - time > settingsContainer.getMinDeliveryTime():
                        new_bdry = bdry.copy_and_change(time, bdry.e_curr + energy, old_day)
                        # new_bdry.compute_boundaries(True) #evtl weg
                        new_bdry.compute_simple_times()
                        if new_bdry.e_curr < bdry.e_curr:
                            print("Error2")
                        energ = compute_charged_until_certain_time_according_to_Charging_strategy(new_bdry,
                                                                                                  max(new_bdry.t_min_end ,time),
                                                                                                  charging_strategy)

                        if new_bdry.ch_rate_strategy_info == None:
                            rate = bdry.charging_power
                        else:
                            rate = bdry.ch_rate_strategy_info
                        strat_energy += energ
                        if energ == 0:
                            rate = 0
                        my_cap_e[1] += -(new_bdry.e_min - energ)#bdry.e_min - energy
                        if new_bdry.e_min != entry.profiles[i].energy:
                            print("Error")
                        if entry.profiles[i+2].__class__ == base_profile and entry.profiles[i+2].modus_pos == 1:
                            if entry.profiles[i+2].energy != energ:
                                print("Error")
                        elif entry.profiles[i+3].__class__ == base_profile and entry.profiles[i+3].modus_pos == 1:
                            if entry.profiles[i+3].energy != energ:
                                print("Error")
                        elif energ > 0:
                            if entry.profiles[i].available_time == None or  entry.profiles[i].available_time <= settingsContainer.getMinDeliveryTime():
                                print("Error")
                        if new_bdry.e_min != 0:
                            if entry.profiles[i].available_time != None and entry.profiles[i].available_time > settingsContainer.getMinDeliveryTime() and entry.profiles[i].profile != None:
                                my_cap_p[1] += bdry.discharging_power + rate
                            else:
                                print("hiii")
                            if entry.profiles[i].charge:
                                print("shouldn't happen")
                                rate = -rate
                            #my_cap_p[1] += bdry.discharging_power + rate


            pos += 1
        energy = entry.getTotalEnergyMinusStrat()

        #if abs(entry.total_energy_strat -strat_energy) > 1e-8:
            #print("Error- mp_with_strat1 not computed correctly")
        power = entry.getTotalPowerMinusStrat()
        if abs(my_cap_e[0]-energy[0])>1e-8:
            print("Error- mp_with_strat1 wrong energy computed")
        if abs(my_cap_e[1]-energy[1])>1e-8:
            print("Error- mp_with_strat1 wrong energy computed")
        if abs(my_cap_p[0]-power[0])>1e-8:
            print("Error- mp_with_strat1 wrong power computed")
        if abs(my_cap_p[1]-power[1])>1e-8:
            print("Error- mp_with_strat1 wrong power computed")






def test_settings():
        simulation_tool = start_tool("analysis_methods/TestTool_Settings.json")
        energy_consumption = ["constant", "constant in range"]
        # so überprüfen:
        # "WITHOUT_WORKING_STATION_ACCESS": 0.25,
        # "CHARGING_EVERY_DAY_AFTER_LAST_TRIP": 0.75
        min_flex_time = [0, 30, 720]
        min_soc = [0, 40, 80]
        soc_tol = [0, 20, 50]
        max_soc = [80]
        # als parameter deaktivieren

        min_delievery_time = [0, 10, 30]

        min_speed = [8, 50]
        min_dist = [0, 50]
        min_soc_after = [0, 50, 100]
        min_soc_plugin = [0, 40, 100]
        min_soc_after_active = [True, False]
        start_day = ["00", "01", "02", "03", "04", "05", "06", "07"]
        # model:
        count = 0
        for k in range(100):
            for j in range(8):
                count += 1
                json_new = {"trip-generation":
                                {"MINIMUM_SPEED": randomfromarray(min_speed),
                                 "MINIMUM_DISTANCE": randomfromarray(min_dist),
                                 "ENERGY_CONSUMPTION": randomfromarray(energy_consumption)
                                 },
                            "plug-in": {
                                "MIN_SOC_AFTER_LAST_TRIP_ACTIVE": True,
                                "MIN_SOC_AFTER_LAST_TRIP": randomfromarray(min_soc_after),  # 100
                                "MIN_SOC_PLUGIN": randomfromarray(min_soc_plugin)
                            }
                            }
                simulation_tool.set_settings(json_new, as_dict=True)
                simulation_tool.run_model(start_day=start_day[j], number_of_runs=1, number_of_users=25,
                                          number_of_days=20)
                # Number of days/users/runs is working

                # flex calculation:
                json_new = {"flex_calculation":
                                {"MIN_FLEX_TIME": randomfromarray(min_flex_time),
                                 "MIN_SOC": randomfromarray(min_soc),
                                 "SOC_TOL": randomfromarray(soc_tol),
                                 "MAX_SOC": randomfromarray(max_soc),
                                 "MIN_DELIEVERY_TIME": randomfromarray(min_delievery_time),
                                 "MIN_SOC_AFTER_LAST_TRIP_ACTIVE": randomfromarray(min_soc_after_active),
                                 "MIN_SOC_AFTER_LAST_TRIP": randomfromarray(min_soc_after),
                                 "MIN_SOC_PLUG_IN": randomfromarray(min_soc_plugin)
                                 },
                            }
                simulation_tool.set_settings(json_new, True)
                test_tool(simulation_tool)
                print("-------------------------------------------------------")
                print("SETTING" + str(count) + "IS TESTED")
                print("-------------------------------------------------------")
                print(settingsContainer.getSettingsAsJson())

def test_tool(simulation_tool=None, viz=False):
        if simulation_tool == None:
            simulation_tool = start_tool()
            simulation_tool.run_model()
            simulation_tool.save_model()
            #simulation_tool.load_model()

        # simulation_tool.updateSettings(simulation_tool.model_data.model_settings, as_dict = True)
        # Test_Model(simulation_tool.model_data.VehicleLists)
        # minimum speed/distance so mal testen

        for i in range(3, 10):
            print("new i")
            print(i)
            for place in ["Home", "Work", "all"]:
                print("----" + str(place))
                for risk in [ False]:
                    print("--------" + str(risk))
                    for spontanflex in [ False]:
                        print("------------" + str(spontanflex))

                            # print(day)
                        for daytype in [0]:
                                day = -1
                                print("----------------Calculation")
                                simulation_tool.calculate_flexibility(spontan_flex=spontanflex, risk=risk,
                                                                      flex_start_time=datetime.timedelta(hours=i * 2),
                                                                      flex_duration=datetime.timedelta(minutes=10),
                                                                      flex_activation_time=datetime.timedelta(0),
                                                                      flex_place=place, flex_at_number_of_day=day,
                                                                      flex_at_number_of_run=0, flex_at_daytype=daytype)
                                if risk:
                                    days = compute_day_list(daytype, settingsContainer.getStartDay(),
                                                            settingsContainer.getNumberOfDays(), ignore_first_days=10)
                                    runs = [i for i in range(settingsContainer.getNumberOfRuns())]
                                else:
                                    days = [day]
                                    runs = [0]
                                for run in runs:
                                    for day_i in days:
                                        # print("----------------Testing flex")
                                        if place == "Home":
                                            if spontanflex:
                                                flex = simulation_tool.model_data.DayLists[run][
                                                    day_i].Flexibility_Home.spontanflexes_on_this_day[-1]
                                            else:
                                                flex = simulation_tool.model_data.DayLists[run][
                                                    day_i].Flexibility_Home.fixDateflexes_on_this_day[-1]
                                        elif place == "Work":
                                            if spontanflex:
                                                flex = simulation_tool.model_data.DayLists[run][
                                                    day_i].Flexibility_Work.spontanflexes_on_this_day[-1]
                                            else:
                                                flex = simulation_tool.model_data.DayLists[run][
                                                    day_i].Flexibility_Work.fixDateflexes_on_this_day[-1]
                                        else:
                                            if spontanflex:
                                                flex = simulation_tool.model_data.DayLists[run][
                                                    day_i].Flexibility_All.spontanflexes_on_this_day[-1]
                                            else:
                                                flex = simulation_tool.model_data.DayLists[run][
                                                    day_i].Flexibility_All.fixDateflexes_on_this_day[-1]
                                        Test_Spontanflex(flex, spontanflex)  # for spontanflex computed not overnight
                                        # print("---------------------------flex tested")
                                        Test_right_boundaries_appended_to_Spontanflex(flex)
                                        # print("--------------------------boundaries tested")
                                # print("Visualization")
                                if viz:
                                    for heur in [0, 1]:
                                        for mod in [0, 1]:
                                            if risk:
                                                for strat_pos in [0, 1, 2]:
                                                    simulation_tool.visualize_flexibility(
                                                        viz_charging_strategy=[strat_pos],
                                                        viz_heuristic=heur,
                                                        viz_modus=mod)
                                            else:
                                                simulation_tool.visualize_flexibility(viz_charging_strategy=[0, 2, 1],
                                                                                      viz_heuristic=heur,
                                                                                      viz_modus=mod)

def test_mom_pot():
    simulation_tool = start_tool()
    strategies = [0, 1, 2]
    times = [datetime.timedelta(hours=i/2) for i in range(48)]
    # model already comupted: only load it
    #simulation_tool.run_model(number_of_runs=1, number_of_users=100, number_of_days=100)
    simulation_tool.load_model()

    #for i in range(len(simulation_tool.model_data.DayLists[0][4].Flexibility_Home.flex_capacities_c[2].FlexBoundaries)):
     #   simulation_tool.model_data.DayLists[0][4].Flexibility_Home.flex_capacities_c[2].FlexBoundaries[i].visualize_energy_boundaries()
    simulation_tool.set_settings(simulation_tool.model_data.model_settings, True)
    compute_mom_potential(simulation_tool.model_data.DayLists, times, strategies, settingsContainer.getNumberOfDays(),
                          settingsContainer.getNumberOfRuns(), settingsContainer.getStartDay(), Home=True,
                          numberofday=-1, Daytype=0, minus_strat=True)
    compute_mom_potential(simulation_tool.model_data.DayLists, times, strategies, settingsContainer.getNumberOfDays(),
                          settingsContainer.getNumberOfRuns(), settingsContainer.getStartDay(), Home=True,
                          numberofday=-1, Daytype=0, minus_strat=False)
    simulation_tool.save_model()

    for run in range(0, settingsContainer.getNumberOfRuns()):

        for ii in range(1,settingsContainer.getNumberOfDays()):
            print("testing " + str(run) + "----" + str(ii))

            for strat_pos in strategies:
                test_momentary_potential_dependant_of_strategy(
                    simulation_tool.model_data.DayLists[run][ii].Flexibility_Home, times, strat_pos)
                #test_momentary_potential_independant_of_strategy(
                 #   simulation_tool.model_data.DayLists[run][ii].Flexibility_Home, times, strat_pos)



def randomfromarray(array):
    pos = np.random.randint(len(array))
    return array[pos]



if __name__ == "__main__":
    test_tool()
    #test_settings()
    #test_mom_pot()
