import csv
import os

from helper_files.import_packages import *
from simulation_model.ChargingStationAndUser import EVUser


class TripChainGenerator(BaseModel):
    # trip_chain_input: TripChainInput = TripChainInput()
    # Here: instead of TripChainInput --> EVUser

    conditional_distributions: dict = None
    user: EVUser = None
    daytype: DayType = DayType.UNKNOWN
    end_at_home: bool = True
    seed: Union[int, None] = None  # seed none oder int

    def __init__(self, *args, **kwargs):
        super().__init__(**kwargs)
        self.conditional_distributions = dict()
        # set the random generator

        # read in the conditional distributions
        files = os.listdir("dataTC")
        for filename in files:
            if filename[-3:] == "csv":
                key = filename[:-4]
                distribution = dict()
                with open(os.path.join("dataTC", filename)) as file:
                    csv_reader = csv.reader(file, delimiter=';')
                    if key == "PurposesValues":
                        for row in csv_reader:
                            array = row[1][1:-1].split(', ')
                            for i in range(len(array)):
                                array[i] = array[i][1:-1]
                            distribution[int(row[0])] = array
                    else:
                        for row in csv_reader:
                            array = row[1][1:-1].split(', ')
                            for i in range(len(array)):
                                array[i] = float(array[i])
                            distribution[row[0]] = array
                self.conditional_distributions[key] = distribution

    def get_distribution(
            self,
            variable: str,
            key: Union[str, conint(ge=0)]
    ) -> Union[List[confloat(ge=0.0, le=1.0)], str]:

        return self.conditional_distributions[variable][key]

    def sample_trip_chain_length(self) -> conint(ge=0, le=12):

        key = self.user.mobility_group + self.user.start_location_of_first_trip + self.daytype \
              + self.user.homogeneous_group
        return generate_int_from_cumulative_distribution(
            self.get_distribution(
                variable=VariableNames.TRIP_CHAIN_LENGTH,
                key=key
            )
        )

    def sample_purpose_chain(
            self,
            trip_chain_length: conint(ge=0, le=12)
    ) -> [List[Purpose], bool]:
        if trip_chain_length == 0:
            return [[],True] #return true, but not relevant
        else:
            variable = VariableNames.PURPOSES + str(trip_chain_length)
            key = self.user.start_location_of_first_trip + self.user.homogeneous_group + \
                  self.daytype + self.user.age
            sampled_index = generate_int_from_cumulative_distribution(
                self.get_distribution(
                    variable=variable,
                    key=key
                )
            )
            sampled_purpose_chain = list(self.get_distribution(
                VariableNames.PURPOSES_VALUES,
                trip_chain_length
            )[sampled_index])

            PurposeChain = [Purpose(int(value)) for value in sampled_purpose_chain]
            if PurposeChain[-1] != Purpose.HOME:
                    last_trip_ending_at_home = False
            else:
                    last_trip_ending_at_home = True

            return [PurposeChain, last_trip_ending_at_home]

    def _sample_distance(self, purpose, staytime):
        if purpose == Purpose.WORK and self.user.fix_working_distance is not None:
            return self.user.fix_working_distance
        key = get_staytime_category(staytime) + stringify(purpose.value) + self.user.mobility_group + \
              self.user.region_type
        sampled_category = generate_int_from_cumulative_distribution(
            self.get_distribution(
                variable=VariableNames.DISTANCE,
                key=key
            )
        )
        return max((sampled_category + random.random()) * Resolution.DISTANCE, settingsContainer.getMinimumDistance())

    def _sample_first_start(
            self,
            trip_chain_length: conint(ge=0, le=12),
            purpose: Purpose,
            next_purpose: Purpose
    ) -> nptime:
        key = stringify(trip_chain_length) + stringify(purpose.value) + stringify(next_purpose.value)
        sampled_category = generate_int_from_cumulative_distribution(
            self.get_distribution(
                variable=VariableNames.FIRST_START,
                key=key
            )
        )
        time: confloat(ge=0.0)=(sampled_category + random.random()) * Resolution.TIME
        hour=int(time)
        minute=(time-float(hour))*60
        second=(minute-int(minute))*60
        return nptime( hour=hour, minute=int(minute), second=int(second))

    def _sample_staytime(self, start, purpose, next_purpose, trip_chain_length):
        key = stringify(purpose.value) + stringify(trip_chain_length) + get_start_category(start) + stringify(next_purpose.value)
        sampled_category = generate_int_from_cumulative_distribution(
            self.get_distribution(
                variable=VariableNames.STAYTIME,
                key=key
            )
        )
        return datetime.timedelta(minutes=(sampled_category + random.random()) * Resolution.TIME*60)

    def _sample_speed(self, start, distance):
        key = get_distance_category(distance) + self.user.federal_state + get_start_category(start) + \
              self.user.age
        sampled_category = generate_int_from_cumulative_distribution(
            self.get_distribution(
                variable=VariableNames.SPEED,
                key=key
            )
        )
        return max((sampled_category + random.random()) * Resolution.SPEED, settingsContainer.getMinimumSpeed())

    def sample_trip(self, start, purpose, next_purpose, trip_chain_length, numberInChain, last=False) -> Trip:
        if last:
            staytime = None
        else:
            staytime = self._sample_staytime(start=start, purpose=purpose, next_purpose=next_purpose,
                                             trip_chain_length=trip_chain_length)
        distance = self._sample_distance(purpose=purpose, staytime=staytime)
        speed = self._sample_speed(start=start, distance=distance)
        duration = datetime.timedelta(minutes=(distance / speed)*60)
        end = start + duration
        return Trip(departure=start, distance=distance, duration=duration, mean_speed=speed, arrival=end,
                    purpose=purpose, staytime=staytime,  numberInChain=numberInChain)

    def sample_trip_chain(self, end_at_home):
        self.end_at_home = end_at_home
        length = self.sample_trip_chain_length()
        result = self.sample_purpose_chain(length)
        purpose_chain= result[0]
        last_trip_ending_at_home = result[1]
        #last_trip_ending_at_home = end_at_home # without adaption according to given probabilities
        if length>0:
            counter = 0
            while end_at_home != last_trip_ending_at_home:
                result = self.sample_purpose_chain(length)
                purpose_chain = result[0]
                last_trip_ending_at_home = result[1]
                counter+=1
                if counter > 100:
                    break


        return self.sample_trip_chain_from_purpose_chain(purpose_chain=purpose_chain)

    def sample_trip_chain_from_purpose_chain(self,
                                             purpose_chain: List[Purpose], recursive_count = 1
                                             ) -> TripChain:

        trip_chain = TripChain(length=len(purpose_chain), purpose_chain=purpose_chain, trips=[])
        if not purpose_chain:
            return trip_chain

        # first start
        index = 0
        last = (index + 1 == trip_chain.length)
        purpose, next_purpose = get_purposes(purpose_chain=purpose_chain, index=index, last=last)
        start = self._sample_first_start(trip_chain_length=trip_chain.length,
                                              purpose=purpose,
                                              next_purpose=next_purpose)

        # sample trips
        while index < trip_chain.length:
            trip_chain.trips.append(self.sample_trip(start=start, purpose=purpose, next_purpose=next_purpose,
                                                     trip_chain_length=trip_chain.length, last=last,  numberInChain=index))
            if last:
                seed_counter = 2
                while not trip_chain.sampled_trip_chain_valid(self.user.cluster):
                    self.set_seed(self.seed * seed_counter * recursive_count)
                    if recursive_count ==2:
                        # compute new purpose chain/length, as old purpose chain/length do not lead to valid trip chain
                        trip_chain = self.sample_trip_chain(self.end_at_home)
                        #print("new purpose chain computed")
                    else:
                        trip_chain = self.sample_trip_chain_from_purpose_chain(purpose_chain, recursive_count+1)
                    seed_counter = seed_counter + 1
                    if seed_counter > 100:
                        breakpoint()
                return trip_chain

            index += 1
            last = (index + 1 == trip_chain.length)
            purpose, next_purpose = get_purposes(purpose_chain=purpose_chain, index=index, last=last)
            start = trip_chain.trips[-1].arrival + trip_chain.trips[-1].staytime

    def set_seed(self, seed):
        self.seed = seed
        random.seed(self.seed)
        #seed for random functions

    def set_user(self, user):
        self.user = user

    def set_daytype(self, daytype):
        self.daytype = daytype




                #seed_counter = seed_counter + 1
                #generator.set_seed(user.ID * int(day_type) * (seed + 1) * seed_counter)
                #user.sampled_trip_chain = generator.sample_trip_chain()
