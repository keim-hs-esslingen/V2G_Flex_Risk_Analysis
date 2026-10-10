from simulation_model.EV import *
import math
Probability_StudentsInRuralAreas = 0.2

from config import settings



def PopulateUser(number_of_user, charging_station_types_prob, filepath = "SimulationTool/EVModels.csv"):
    # populate user generation
    ev_models = EVModels_Probability(filepath =  filepath)
    UserList = list()
    VehicleList = list()
    distributions = list()

    # Zur Laufzeit auf aktuelle CSV-Pfad zugreifen (nicht beim Import!)
    with open(settings.POPULATE_USERS_CSV_PATH, newline="") as file:
        csv_reader = csv.reader(file, delimiter=';')
        for row in csv_reader:
            distributions.append(row[1][1:-1].split(', '))
    
    # Konvertiere jeden Wert zu float (unterschiedliche Reihen können unterschiedliche Längen haben!)
    for i in range(len(distributions)):
        for j in range(len(distributions[i])):  # Nutze Länge DIESER Reihe, nicht der ersten!
            distributions[i][j] = float(distributions[i][j])

    if (distributions[2][2]-distributions[2][1]) > (distributions[4][0]) and distributions[4][2]!=0:
        print("more students than people under 40. Please increase number of people under 40 (Students always under 40)")
        return

    # assign region type (independant of other distributions)
    for i in range(number_of_user):
        ev_user: EVUser = EVUser(user_id=i)


        if i < number_of_user * distributions[0][0]:
            ev_user.region_type = RegionType.URBAN_METROPOLIS
        elif i < number_of_user * distributions[0][1]:
            ev_user.region_type = RegionType.URBAN_MAJOR_CITY
        elif i < number_of_user * distributions[0][2]:
            ev_user.region_type = RegionType.URBAN_CITY_AREA
        elif i < number_of_user * distributions[0][3]:
            ev_user.region_type = RegionType.URBAN_VILLAGE
        elif i < number_of_user * distributions[0][4]:
            ev_user.region_type = RegionType.RURAL_CENTRAL_CITY
        elif i < number_of_user * distributions[0][5]:
            ev_user.region_type = RegionType.RURAL_CITY_AREA
        elif i < number_of_user * distributions[0][6]:
            ev_user.region_type = RegionType.RURAL_VILLAGE
        elif i < number_of_user * distributions[0][7]:
            ev_user.region_type = RegionType.UNKNOWN
        UserList.append(ev_user)
    random.shuffle(UserList)

    #assign federal state, independant of other distributions
    for i in range(number_of_user):
        ev_user = UserList[i]
        if i < number_of_user * distributions[1][0]:
            ev_user.federal_state = FederalState.SCHLESWIG_HOLSTEIN
        elif i < number_of_user * distributions[1][1]:
            ev_user.federal_state = FederalState.HAMBURG
        elif i < number_of_user * distributions[1][2]:
            ev_user.federal_state = FederalState.LOWER_SAXONY
        elif i < number_of_user * distributions[1][3]:
            ev_user.federal_state = FederalState.BREMEN
        elif i < number_of_user * distributions[1][4]:
            ev_user.federal_state = FederalState.NORTH_RHINE_WESTPHALIA
        elif i < number_of_user * distributions[1][5]:
            ev_user.federal_state = FederalState.HESSE
        elif i < number_of_user * distributions[1][6]:
            ev_user.federal_state = FederalState.RHINELAND_PALATINATE
        elif i < number_of_user * distributions[1][7]:
            ev_user.federal_state = FederalState.BADEN_WUERTTEMBERG
        if i < number_of_user * distributions[1][8]:
            ev_user.federal_state = FederalState.BAVARIA
        elif i < number_of_user * distributions[1][9]:
            ev_user.federal_state = FederalState.SAARLAND
        elif i < number_of_user * distributions[1][10]:
            ev_user.federal_state = FederalState.BERLIN
        elif i < number_of_user * distributions[1][11]:
            ev_user.federal_state = FederalState.BRANDENBURG
        elif i < number_of_user * distributions[1][12]:
            ev_user.federal_state = FederalState.MECKLENBURG_WESTERN_POMERANIA
        elif i < number_of_user * distributions[1][13]:
            ev_user.federal_state = FederalState.SAXONY
        elif i < number_of_user * distributions[1][14]:
            ev_user.federal_state = FederalState.SAXONY_ANHALT
        elif i < number_of_user * distributions[1][15]:
            ev_user.federal_state = FederalState.THURINGIA
        elif i < number_of_user * distributions[1][16]:
            ev_user.federal_state = FederalState.UNKNOWN
    random.shuffle(UserList)


    counter_rural = 0
    number_of_students = math.floor((distributions[2][2] - distributions[2][1])*number_of_user)
    numberOfRuralStudents = math.floor(number_of_students * Probability_StudentsInRuralAreas)
    numberOfWorkingPeople=(distributions[2][0]) * number_of_user
    numberOfnotWorkingPeople=(distributions[2][1] - distributions[2][0]) * number_of_user
    switch_counter=0
    for i in range(number_of_user):
        ev_user = UserList[i]
        if i < number_of_user * distributions[2][0]:
            ev_user.homogeneous_group = HomogeneousGroup.WORKING_PERSON
            if np.random.rand() < settingsContainer.getWithoutWorkingStationAccess():
                # setting some users to have no access to charging station at work
                ev_user.plug_in_alphas[1] = 0
        elif i < number_of_user * distributions[2][1]:
            ev_user.homogeneous_group = HomogeneousGroup.NON_WORKING_PERSON
        elif i < number_of_user * distributions[2][2]:
            if ev_user.region_type == RegionType.RURAL_CENTRAL_CITY or ev_user.region_type == RegionType.RURAL_CITY_AREA or ev_user.region_type == RegionType.RURAL_VILLAGE:
                counter_rural=counter_rural+1
                if counter_rural<=numberOfRuralStudents:
                    ev_user.homogeneous_group = HomogeneousGroup.STUDENT
                else:
                    while (UserList[switch_counter].region_type == RegionType.RURAL_CENTRAL_CITY or UserList[switch_counter].region_type == RegionType.RURAL_CITY_AREA or UserList[switch_counter].region_type == RegionType.RURAL_VILLAGE):
                        if switch_counter < (numberOfWorkingPeople + numberOfnotWorkingPeople):
                            switch_counter =switch_counter+1
                        elif switch_counter == (numberOfWorkingPeople + numberOfnotWorkingPeople):
                            switch_counter = distributions[2][3]*number_of_user
                        elif switch_counter<number_of_user:
                            switch_counter = switch_counter + 1
                        elif switch_counter==number_of_user:
                            print("not enough rural peple for probability for rural students")
                            return
                    group = UserList[switch_counter].homogeneous_group
                    UserList[switch_counter].homogeneous_group = HomogeneousGroup.STUDENT
                    ev_user.homogeneous_group = group
            else: #always more urban than rural students
                ev_user.homogeneous_group = HomogeneousGroup.STUDENT
        elif i < number_of_user * distributions[2][3]:
            ev_user.homogeneous_group = HomogeneousGroup.UNKNOWN

    random.shuffle(UserList)

    for i in range(number_of_user):
        ev_user = UserList[i]
        if i < number_of_user * distributions[3][0]:
            ev_user.mobility_group = MobilityGroup.CAR_USER
        elif i < number_of_user * distributions[3][1]:
            ev_user.mobility_group = MobilityGroup.MULTI_MODAL
        elif i < number_of_user * distributions[3][2]:
            ev_user.mobility_group = MobilityGroup.NON_CAR_USER
        elif i < number_of_user * distributions[3][3]:
            ev_user.mobility_group = MobilityGroup.UNKNOWN

    random.shuffle(UserList)

    for i in range(number_of_user):
        ev_user = UserList[i]
        if i < number_of_user * distributions[5][0]:
            ev_user.start_location_of_first_trip = StartLocation.AT_HOME
        elif i < number_of_user * distributions[5][1]:
            ev_user.start_location_of_first_trip = StartLocation.NOT_AT_HOME
        elif i < number_of_user * distributions[5][2]:
            ev_user.start_location_of_first_trip = StartLocation.UNKNOWN

    random.shuffle(UserList)
    counter_students_in_under40=0
    counter_students_in_40to65 = 0
    counter_students_in_over65 = 0
    counter_students_in_unknown = 0
    user_counter=0
    while user_counter < math.floor((number_of_user * distributions[4][0]-number_of_students+counter_students_in_under40)):
        ev_user = UserList[user_counter]
        if ev_user.homogeneous_group == HomogeneousGroup.STUDENT:
            counter_students_in_under40 = counter_students_in_under40+1
        ev_user.age = ev_user.age.UNDER_FORTY
        user_counter=user_counter+1
    current_user_count=user_counter
    while user_counter < math.floor((number_of_user * (distributions[4][1] - distributions[4][0]) + current_user_count+counter_students_in_40to65)):
        ev_user = UserList[user_counter]
        if ev_user.homogeneous_group == HomogeneousGroup.STUDENT:
            counter_students_in_40to65 = counter_students_in_40to65 + 1
            ev_user.age = ev_user.age.UNDER_FORTY
        else:
            ev_user.age = ev_user.age.FORTY_TO_SIXTY_FIVE
        user_counter = user_counter + 1
    current_user_count = user_counter
    while user_counter < math.floor((number_of_user * (distributions[4][2] - distributions[4][1]) + current_user_count+counter_students_in_over65)):

        ev_user = UserList[user_counter]
        if ev_user.homogeneous_group == HomogeneousGroup.STUDENT:
            counter_students_in_over65 = counter_students_in_over65 + 1
            ev_user.age = ev_user.age.UNDER_FORTY
        else:
            ev_user.age = ev_user.age.OVER_SIXTY_FIVE
        user_counter = user_counter + 1
    current_user_count = user_counter
    while user_counter < number_of_user:
        ev_user = UserList[user_counter]
        if ev_user.homogeneous_group == HomogeneousGroup.STUDENT:
            ev_user.age = ev_user.age.UNDER_FORTY
        else:
            ev_user.age = ev_user.age.UNKNOWN
        user_counter = user_counter + 1

    # possible ToDo dependancy of economic status and student,age,...

    random.shuffle(UserList)
    current_share = settingsContainer.getUserInteractionSimRangeShares()[0]
    number = 0
    for i in range(number_of_user):
        ev_user = UserList[i]

        if i < number_of_user * current_share:
            ev_user.set_range(settingsContainer.getUserInteractionSimRanges()[number])
        else:
            number = number + 1
            if number < len(settingsContainer.getUserInteractionSimRanges()):
                current_share = settingsContainer.getUserInteractionSimRangeShares()[number]
                ev_user.set_range(settingsContainer.getUserInteractionSimRanges()[number])
            else:
                ev_user.set_range(settingsContainer.getUserInteractionSimRanges()[number])

    random.shuffle(UserList)

    for i in range(number_of_user):
        ev_user = UserList[i]
        if i < number_of_user * distributions[6][0]:
            ev_user.economic_status = ev_user.economic_status.VERYLOW
        elif i < number_of_user * distributions[6][1]:
            ev_user.economic_status = ev_user.economic_status.LOW
        elif i < number_of_user * distributions[6][2]:
            ev_user.economic_status = ev_user.economic_status.MEDIUM
        elif i < number_of_user * distributions[6][3]:
            ev_user.economic_status = ev_user.economic_status.HIGH
        elif i < number_of_user * distributions[6][4]:
            ev_user.economic_status = ev_user.economic_status.VERYHIGH
        elif i < number_of_user * distributions[6][5]:
            ev_user.economic_status = ev_user.economic_status.UNKNOWN

        # user gets home charging station possible TODO: users with no home charging station, as well
        ev_user.set_charging_station(charging_station_types_prob.assign_charging_station("home"))
        ev_user.set_charging_station_work(charging_station_types_prob.assign_charging_station("work"))


        #ev_user.set_working_distance(np.random.randint(0,40))
        EVModel = ev_models.assign_ev(ev_user.economic_status)
        # maybe later, one user with several vehicles possible, as well?
        # each EV gets an user, if later with households, then EVs with several users possible,            # different (different counters), generation of evs per household
        ev = EV(ev_id=ev_user.ID, ev_user=ev_user, battery_size=EVModel.battery_size, ac_power=EVModel.AC_power,
                   dc_power=EVModel.DC_power, ec_d_avg=EVModel.ec_d_avg, ec_d_min=EVModel.ec_d_min, ec_d_max = EVModel.ec_d_max)
        VehicleList.append(ev)
        ev_user.ev_id = ev.ID

    random.shuffle(UserList)
    for i in range(number_of_user):
        ev_user = UserList[i]
        if i < number_of_user*settingsContainer.getChargingEveryDayAfterLastTrip():
            ev_user.charge_every_day_on_evening = True

    random.shuffle(UserList)
    for i in range(number_of_user):
        ev_user = UserList[i]
        if i < number_of_user * user_Cluster1_share:
            ev_user.set_cluster(Cluster.Cluster1)
        elif i<number_of_user * (user_Cluster1_share+user_Cluster2_share):
            ev_user.set_cluster(Cluster.Cluster2)
        else:
            ev_user.set_cluster(Cluster.Cluster3)



    VehicleList.sort(key=lambda x: x.ID)


    return UserList, VehicleList
