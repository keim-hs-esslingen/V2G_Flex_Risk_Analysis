from helper_files.variables import *


def compute_charged_until_certain_time_according_to_Charging_strategy(FlexBoundary, time, charging_strategy):
    if charging_strategy == "as soon as possible":

        if FlexBoundary.t_max_end_alternative != None:
            t_max_end = FlexBoundary.t_max_end_alternative
            e_max = FlexBoundary.e_max_end_alternative
        else:
            e_max, t_max_end = FlexBoundary.compute_alternative_t_max_end()
        if t_max_end < time:
            # enough time to fully charge
            energy = e_max
        else:
            #min(e_max,...)
            energy = FlexBoundary.vehicle.charge(time-FlexBoundary.t_start, FlexBoundary.charging_power)  # energy charged until current time
        ch_rate = None
        time_start_charging_for_e_need = None
    elif charging_strategy == "as late as possible":
        if FlexBoundary.e_min > 0 and abs(FlexBoundary.e_min)>1e-12:

            print("Error: e_min always smaller or equal than zero! Not possible to set MIN_SOC higher than, "
                  "when the model was calculated, Recalculate model")

        elif FlexBoundary.start_time_eneed != None:
            time_start_charging_for_e_need = FlexBoundary.start_time_eneed
        else:
            if FlexBoundary.e_need > 0 or abs(FlexBoundary.e_need)<1e-12:

                # compute latest point to start charging, which is different from t_min_start2, as this is the point
                # to start charging, if discharged til e_min; but in this strategy no discharge until e_min
                time_start_charging_for_e_need = FlexBoundary.t_end - FlexBoundary.vehicle.time_to_charge(
                    FlexBoundary.e_need, FlexBoundary.charging_power)


            else:
                time_start_charging_for_e_need = FlexBoundary.t_end
        if time <= time_start_charging_for_e_need or FlexBoundary.e_need < 0:
            # charging not started
            energy = 0
        else:
            # charging started, so compute energy charged until start_time
            diff = time - time_start_charging_for_e_need
            energy = FlexBoundary.vehicle.charge(diff, FlexBoundary.charging_power)
        ch_rate = None

    elif charging_strategy == "as long as possible with minimum rate":
        if FlexBoundary.ch_rate_strategy_info != None:
            ch_rate = FlexBoundary.ch_rate_strategy_info
        else:
            # compute minimum charging_rate to charge energy in available time
            ch_rate = compute_min_charging_rate(FlexBoundary.available_period.available_time, FlexBoundary.e_max,
                                                FlexBoundary.charging_power)
        energy = min(FlexBoundary.vehicle.charge(time - FlexBoundary.t_start, ch_rate),
                             FlexBoundary.e_max)
        time_start_charging_for_e_need = None
    FlexBoundary.set_strategy_info(ch_rate, time_start_charging_for_e_need)
    return energy

def compute_min_charging_rate(available_time, energy, max_charging_rate):
    if not CPCV:
        ch_rate = max((3600*energy)/(available_time.total_seconds()), MIN_CHARGING_RATE)
        ch_rate = min(ch_rate, max_charging_rate)
    #else:
        # somehow find out in efficient way
    return ch_rate
# FlexBoundary.set_strategy_infor