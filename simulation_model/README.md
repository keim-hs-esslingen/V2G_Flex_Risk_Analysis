# Simulationsmodell
Das Simulationsmodell wird durch die Methode 'run' mit den Input-Parametern 'NumberOfDays', 'NumberOfUsers', 'start_day', 'NumberOfRuns' ausgeführt (in 'Run.py'), welche den 'TC-Genereator' initialisiert.
Entsprechend der Anzahl an Simulationsläufen (Number_of_runs) wird  mehrmals ein Modell ausgeführt.
Die Modellausführung besteht aus zwei Schritten:

1) Initialisierung
2) Modelldurchführung

Als Ergebnis jeder einzelnen Ausführung werden eine 'Userlist', eine 'Vehiclelist' und eine 'Daylist' zurückgegeben.
Alle abgespeicherten Listen bilden zusammen mit den Modellparameter, das  Klassenobjekt 'model_data', welches durch die übergeordneten Methoden des Simulationstools verwendet werden. 

## Initialisierung
Bei der Initialisierung des Klassenobjekts 'model' werden die Listen 'vehicleList', 'Userlist' und 'Daylist' initilalisiert. Diese Listen werden bei der Durchführung befüllt. 
Die Listen 'Userlist' wird mithilfe der Methode PopulateUsers befüllt. Sie enthält Klassenobjekte der EV-Nutzenden (Klassenobjekt 'user') mit ihren verschiedenen Eigenschaften. 
Die 'VehicleList' enthält alle dazugehörigen Fahrzeuge (Klassenobjekt EV) und die Liste 'Daylist' alle zu simulierenden Tage (Klassenobjekte Day). 
Zusammen mit der Klasse Charging Station bilden die Klassen 'EV', 'User' und 'Day', wie in der Thesis beschrieben,  die Hauptkomponenten des Simulationsmodells ab. 

### PopulateUsers
#### User
Die Methode 'PopulateUsers' (Datei 'PopulateUser.py') nimmt anhand der Tabelle 'PopulateUsers' die Verteilung der Eigenschaften auf die EV-Nutzenden vor. 
Zu Beginn werden entsprechend der Anzahl an Nutzenden dementsprechend viele Nutzer initialisiert.  
Anschließend werden schrittweise die Zeilen der Tabelle mit den unterschiedlichen Eigenschaftskategorirn abgearbeitet. 
Dabei wird anhand der Wahrscheinlichkeit der einzelnen Attribute  (Differenz zwischen dem Eintrag in der entsprechenden Spalte und den Eintrag in er Spalte zuvor) einer zufälligen Auswahl mit der entsprechenden Anzahl an Nutzern diese Eigenschaft zugeteilt. 
Auch die Attribute 'without_workIng_station_access' und 'charging_every_day' werden entsprechend aufgeteilt. 
Bei den Studierenden wird beispielhaft eine Abhängigkeit unter den verschiedenen Eigenschaftskategorien abgebildet. 
Die Wahrscheinlichkeit 'numberofrutslstudents' gibt an, wie viele Studierenden auf dme Land wohnen und außerdem werden alle Studierende der Alterskategorie unter 40 zugeteilt. 

#### EVs
Jedem Nutzenden wird außerdem entsprechend des ökonomischen Status ein EV-Modell zugefügt. Diese Zuteilung erfolgt anhand der Wahrscheinlichkeiten aus der Tabelle 'EVModels'. 
Dabei hilft die Klasse 'EVModels_Probability' mit welcher die csv-Datei, als die die Tabelle abgespeichert ist, einliest und die entsprechenden Wahrscheinlichkeiten abspeichert. 
Mithilfe der Methode 'assign_ev' dieser Klasse kann anhand der abgespeicherten,  diskreten Wahrscheinlichkeitsdichtefunktion für die EVModels bei verschiedenen, ökonomischen Status ein Zufallswert erstellt werden, der die Zeilenanzahl in der Tabelle 'EVModels' beschreibt. 
Die Methode gibt dann direkt das EV Modell dieser Zeile als Klassenobjekt 'EVModell' zurück. Diese Klasse 'EVModels' enthält die Konfigurationen des EV-Modells ('battery_size', 'AC_power', DV_power,..) entsprechend der Attribute in der Tabelle 'EVModels'. 
Zudem wird abhängig von der Batteriegröße und dem Energieverbrauch, wie in Gleichung 5.25 eine Mindestreichweite berechnet:
#### Code-Beispiel:
if self.battery_size / self.ec_d_max > 2:
   min_range = self.ec_d_max * 0.5 
else:
   min_range = self.ec_d_max * 0.35
self.min_energy = max(settingsContainer.getMinSoc() * 0.01 * self.battery_size, min_range)

Die Klasse 'EV' erbt von der Klasse 'EVModels', sodass mithilfe des zugeteilten 'EVModels' ein 'EV' initialisiert werden kann, das dem Nutzer zugeordnet werden kann. 
Dabei speichert das 'EV' den zugehörigen Nutzer ('user') als Klassenobjekt und das EV den Nutzer anhand der eine 'user_ID' ab, welche ebenfalls in 'PopulateUser' erstellt wird. 
Jedes neu erstellte 'EV' wird in der Liste 'Vehiclelist' abgespeichert. 

#### ChargingStations
Ähnlich funktioniert auch die Zuteilung der Heimladestation zum 'User'. Die Methode 'assign_chargingStation' der Klasse 'ChargingStation_Probability', welche in der 'Init'-Methode die Tabelle ChargingStationTypes' einliest, teilt je nach Ladestationsdestination ('home', 'public', 'work') eine Ladestation zu. 
Die Ladestation 'ChargingStation' hat die Eigenschaften 'Place' (Ladestationsdestination, siehe oben), den 'boolean' 'ac', der angibt ob die Ladestation AC oder DC laden kann ist die Lade- und Entladeleistung. 
Die Zuteilung erfolgt anhand der diskreten  Wahrscheiichkeitsdichtefunktion von Tabelle "ChargingStationTypes" der drei möglichen Destinationen. Dem 'User' wird für zu Hause eine feste 'ChargingStation' zugeteilt, die als KlassenAttributs abgespeichert wird. 

### Initialisierung 'DayList'
Neben der Methode 'PopulateUser' wird ausßerdem eine Liste an zu simulierenden Tagen des Klassenobjekts 'Day' mit den entsprechenden Wochentagen als Eigenschaften initialisiert. 
Es werden die Wochentage Montag bis Sonntag betrachtet, welche als Attribut 'day_type' abgespeichert werden (1-8 als string). 
Der erste simulierte Wochentag entspricht dem Parameter 'start_day', der zweite ist der darauffolgende Wochentag, usw... 

## Modelldurchführung
### Allgemein
Für die Durchführung der Simulation sind die weiteren Attributen und Methoden der Klassen 'EV', 'User', 'Day' und 'TripChainGenerator' relevant. 
#### Day
'Day' besitzt insbesondere die Methode 'simulate_day', welche einen Tag mit den Input-Eingaben 'Vehiclelist', 'UserList und dem 'TripChainGenerator' simuliert.
Außerdem gibt die Variable 'number_of_day' an, welcher zu simulierende Tag dieser Tag ist (Position in der 'DayList'). 
Außerdem hat die Klasse 'Day' noch Attribute für die Flexibiltitätsberechnung ( available_periods, Flexibility_All, Flexibility_Home, next_day_type)

#### EV
Das EV hat neben den unveränderlichen  Attributen, zu denen neben den Modellspezifikationen der zugehörige 'User' als Klassenobjekt und eine 'ID' gehören, gibt es veränderliche und speichernde Attribute. 
Speichernde Attribute sind Listen, die sich im Laufe der Simulation mit Informationen füllen. Diese werden mit wichtigen Informationen, wie den TripChains, den Ladezeitpunkten und den Soc-Werten befüllt (Listen mit total_). 
Die veränderlichen Variablen werden im Laufe der Simulation immer wider aktualisiert, da sie für Zwischenberechnungen und -Speicherungen verwendet werden. 
Dazu gehören beispielsweise 'sampled_trip_chain' und 'next_trip_chain', welche die aktuelle TripChain und die Trip chain des nächsten Tages beschreiben. 
'SOClist' enthält die Soc-Werte des aktuell simulierten Tages, 'CurrentStation' die aktuelle Ladestation, usw... 

#### User
Der 'User' besitzt neben den Attributen zu allen Eigenschaftskategorien ebenfalls eine aktuelle und die nächste TripChain, eine ID und die zugehörige 'ev_id'. 
Ein weiteres wichtiges Attribut sind die Plug-In alphas 'plug_in_alphas', welche das Plug-In-Verhalten beschreiben. 

#### TipChainGenerator
Der 'TripChainGenerator' (Datei TripChainGenerator.py) wurde von Schlund (2021) mit kleinen Veränderungen übernommen. 
Die originale Version ist im Ordner 'Original TC-Generator' zu finden. 
Wichtig ist hierbei die Klasse 'TripChain', welche mehrere Trips enthält (siehe Datei variables.py). 
Diese Trips der Klasse 'Trip' haben die Attribute 'departure', 'arrival', 'duration', 'distance', 'speed', 'Purpose' und 'staytime' (Parkzeit am Ende des Trips). 
Mithilfe der Methode 'sample_trip_chain' kann eine 'TripChain' generiert werden. Diese Methode der Klasse 'TripChainGenerator' ist vom Attribut 'User', 'Seed', 'daytype', den abgespeicherten bedingten Wahrscheinlichkeiten und 'end_at_home' (gibt an ob der Trip zu Hause enden soll) abhängig. 
Vor jedem Aufruf der Methode muss somit der 'User' entsprechend des aktuellen 'User' und des Wochentags aktualisiert werden. 
Zudem wird der 'seed' geändert, der die Zufallsgenerieung steuert. Außerdem gibt das Attribut 'end_at_home' an, ob der Trip zu Hause enden soll oder nicht. 

### Durchführung mit simulate day
Zunächst wird für jeden 'User' eine 'Tripchain' generiert. Dies ist die 'TripChain' für den nächsten Tag, da für das Plugin-Modell auch die erste Fahrt des nächsten Tages wichtig ist. 
Am ersten Tag der Simulation werden deshalb zwei 'TripChain' generiert: Für den aktuellen und für den nächsten Tag. 
Mit der Methode 'calcuate_end_at_home' wird anhand der angenommenen Wahrscheinlichkeiten (siehe Thesis) ein 'boolean' ausgerechnet der angibt, ob die nächste Fahrt zu Huade oder nicht zu Hause enden soll. 
Anschließend wird die 'TripChain' nach Schlund (2021) generiert. Die 'TripChains' werden dabei auch auf Richtigkeit kontrolliert, da es vorkommen kann, dass manche Fahrten erst am nächsten Tag starten. 
In solchen Fällen werden neue 'Tripchains' generiert, die nur Fahrten an einem Tag enthalten. 
Das Ende einer Fahrt am nächsten Tag, also eine Fahrt über Nacht ist aber möglich. 
Zur Überprüfung der Richtigkeit einer 'TripChain' dient die Methode 'sample_Trip_chain_valid'. 
Anschließend wird dem zugehörigen 'EV' die 'TriCchain' zugeordnet. Dabei wird überprüft, ob diese 'TripChain' mit dem EV überhaupt möglich ist. 
Dies macht eine Erweiterung mit mehreren 'User' je Auto in zukünftigen Arbeiten möglich. 
Die Methode prüft außerdem die Ankunftszeit der letzten Fahrt welche auch nach Mitternacht sein kann und stellt sicher, dass das die neue 'TripChain' nicht früher als dieses Ende beginnt.
Nachdem jedem 'User' und den zugehörigen 'EV's eine bzw. zwei 'TripChain's zugewiesen wurden, wird nun  schrittweise bei jedem 'EV' die Simulation eines Tages mit der Methode mit der Methode 'simulate_day' durchgeführt.

#### EV.Simulate_day
##### Allgemein 
Die Methode 'simulate_day' gliedert sich in drei Teile:
1) Initialisierung: ('initalize_next_day')
2) Soc-Wert-Berechnung über den Tag: ('socduring_day')
3) Abspeichern der simulierten Daten (z.B. SOC-Werte)

Eine wichtige Datenstruktur ist die SOC-Liste (Klasse 'SOCDuringDay' in Datei 'variables.py'). Sie enthält alle wichtigen Zeiten während eines Tages, die entsprechenden SOC-Werte und den Zustand beschrieben als 'String' zu den jeweiligen Zeiten. 
Da Ladevorgänge und Energieverbrauch konstant sind, reicht es die SOC-Werte zu Beginn und dem Ende dieser Prozesse abzuspeichern. 
Dies sind die einzigen Prozesse mit SOC-Veränderungen. Außerdem wird immer der Soc Wert am Beginn einer Fahrt abgespeichert. 
Tagesspezifisch werden bei jedem 'EV' außerdem die  generierten 'Trip chain's, die Plugin-Zeiten und die sogenannten 'AvailablePeriods'  bzw 'base_chargin_periods' abgespeichert (Siehe Flexibiltitätberechmug).
Die entsprechenden Zwischenspeicherungslisten (PlugIn_Times, Charging_Times, SOC_list,available_periods, base_charging_periods) werden für jeden Tag neu befüllt und am Ende der Simulation eines Tages in einer Gesamtliste (total_SOC_list, total_Charging_list,  total_driving_list, total_trip_chain_list,  total_plugin_list, total_available_period_list, total_base_charging_periods_list) abgespeichert. 
Die Methode 'simulate_one_day' ist rekursiv. Das liegt daran, dass nach jeder SOC-Veränderung überprüft wird ob ein negativer SOC-Wert ausgerechnet wurde. 
Ist dies der Fall wird 'simulate_day' erneut aufgerufen um den Tag nochmals zu simulieren. 
Zwar wird das Plugin-Modell so umgesetzt, dass immer angesteckt wird um den Mobiltätsbedarf der nächsten Fahrt zu garantieren, aber es kann trotzdem sein, dass  eine Fahrt zu viel Soc verbraucht, da die Plugin-Dauer zuvor zu kurz war. In der Realität würden die 'User' eventuell vorausschauend laden, was aber nicht implementiert ist. 

##### Initialisierung 
Die Methode 'initilaize_next_day' kann durch zwei Aufrufe erfolgen: Der vorgesehene Fall am Anfang einer Simulation eines Tages oder durch einen rekursiven Aufruf. 
Im standardmäßigen Fall  wird der Ausgangs-SOC-Wert am Anfang des Tages auf den Wert des Ende des letzten Tages gesetzt. 
Dies ist der letzte SOC-Wert der SOC-Liste 'SOCList' des vorigen Tages. 
Demnach wird der bisherige letzte SOC-Wert als erster Wert übernommen. 
Die erste Zeit wird auf 0:00 gesetzt. Zu Beginn der Simulation werden die SOC-Listen mit zufälligen SOC-Werte zwischen 70 und 100 befüllt. 
Außerdem wird im Falle, dass eine Fahrt am vorherigen Tag über Mitternacht dauerte, die erste Zeit der SOC-Liste angepasst. 
Im rekursiven Fall werden veränderliche Variablen, wie die aktuelle Ladestation 'currentStation' und die 'Current_available_period' auf den Zustand am Ende des vorigen Tages zurückgesetzt. 
Auch, die Information, ob am Tag zuvor angesteckt war, muss für dieen Fall auf andere Weise implementiert werden (mithilfe Attribut 'last_period') 

Falls das 'EV' am Ende des vorigen Tages angesteckt war (Variable 'available'==True), dann wird die Methode 'charging_at_beginning_of_the_day' aufgerufen: 
Diese Methode berechnet ausgehend vom aktuellen SOC-Wert und mithilfe der Trip-Abfahrtszeit des ersten Trips wie viel Energie noch vor der Abfahrt geladen werden kann. 
Falls vollgeladen werden kann, wird die entsprechende Lade-Endzeit abgespeichert. 
Ansonsten wird bis zur Abfahrt mit maximaler Leitung geladen. Im Simulationsmodell wird immer mit der Ladestrategie 1 gerechnet. 
Erst bei der Flexibiltätsberchnung werden andere Ladestrategien berücksichtigt. 
#### SOC-Wert-Berechnung
Die Methode 'SOC_during_day' durchläuft iterativ jeden Trip der 'TripChain' eines 'EV's mit der Methode 'soc_during_trip'. 
Diese gibt einen 'boolean' zurück, ob die Methode unterbrochen wurde. Dies ist der Fall, wenn ein Soc_Wert nach einer Fahrt kleiner als 0 ist. 
Falls dies der Fall ist wird eine neue 'TripChain' für den 'User' und dem aktuellen 'EV' generiert, 'initialze_next_day' mit dem Parameter 'recursive' auf 'True' aufgerufen und  'soc_during_day' rekursiv erneut aufgerufen. 
'Soc_during_trip durchläuft die folgenden Schritte:
1) Aktualisierung der SOC-Liste mit Status "Driving" (Beginn der Fahrt) 
2) Berechnung des Energieverbrauchs, der Soc-Veränderung und dementsprechende Aktualisierung der SOC-Liste 
3) Plugin-Entscheidung abhängig von Destination der Ladestation
4) falls Plug-in, Definition und Berechnung des Ladevorgangs und dementsprechende Aktualisierung der SOC-Liste



###### Code-Beispiel: Energiverbrauch analog zu Definition in Thesis:

    if settingsContainer.getEnergyConsmuption() == "constant":
            rate = self.ec_d_avg

        elif settingsContainer.getEnergyConsmuption() == "constant in range":

            rate = np.random.normal(self.ec_d_avg)
            while rate > self.ec_d_max or rate < self.ec_d_min:
                rate = np.random.normal(self.ec_d_avg)

        energy_consumed = rate * (distance)

Die Destination der Ladestation wird abhängig von der Trip-Variable 'purpose' des aktuellen 'trip' analog zur Thesis berechnet.
##### Codebeispiel für Plug-In-Decision

        if current_SOC <= need_SOC:
            return self.sampled_trip_chain.trips[current_trip.numberInChain].arrival
        else:
            p = 1 - pow(((current_SOC - need_SOC) / (100 - need_SOC)), alpha)
            # if alpha == 0 (e. g if user has no access to charging station at work), p = 0 as well --> return False
            if np.random.rand() < p:
                return self.sampled_trip_chain.trips[current_trip.numberInChain].arrival
            else:
                return -1
##### Anmerkung zu 4) 
Falls Destination der Ladestation ('Place') == 'Home, dann Ladestation des 'User', ansonsten wird eine öffentliche Ladestataion oder Ladestation bei der Arbeit zugewiesen.
Entsprechend wird die 'CurrentStation' aktualisiert.
Bei Ladevorgängen wird die KLasse 'CharingSession' (Datei 'ChargingStationAndUser') verwendet und über Ladestation, Leistung, SOC-Werte vor und nach dem Ladevorgang und durch die Ladezeiten charakterisiert. 
##### Methode charging_full_if_possible
Berechnet die Zeit, in der bis zum Ende der Plug-In-Zeit geladen werden kann (bis Mitternacht oder nächsten Trip - im Falle von Mitternacht rechnet 'charging_at_beginning_of_the_day' den Rest am nächsten Tag (aufgerufen in 'initialize_next_day')
1) Wie viel muss bis zum SOC-Wert 100 geladen werden?
2) Kann in der vefübaren Zeit voll geladen werden? 
3) Falls 2) nein, dann wie viel Energie kann geladen werden? Wie ist dann der SOC ?
--> Hierfür: Berechnung anhand von Leistung des EVs und der zugewiesenen Ladestation die Ladelesitung (Gleichung 5.7 in Thesis) 