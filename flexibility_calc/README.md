# Flexibilitätsberechnung und -Visualisierung
## Aufbau
Die Flexibiltätsberechnung des Simulationstools wird über die Klasse 'flex_object' gesteuert. 
Grundsätzlich gibt es die zwei Berechnungsvarianten: statistische und spezifische Flexibiltät (über 'risk' - Parameter). 
Die zuletzt berechnete/n Flexibilität/en wird/werden als Klassenobjekt in dem Attribut 'flex_list' abgespeichert.
Im Falle der spezifischen Flexibiltät ist dies eine berechnete Flexibiltät und bei der statistischen alle berücksichtigten spez. Flexibilitäten. 
Die Berechnung der statistischen Kennwerte bei der stat. Flexibiltät wird beim Aufruf der Visualisierung (visualize_flexibilty) über ein sogenanntes 'risk_object' ausgelöst, welches als Klassenobjekt gespeichert wird. 
Zudem werden die Flexibiltätsspezifikationen der berechneten Flexibilität im 'flex_object abgespeichert.
Im Falle der spezifischen Flexibilität wird für die spätere Visualisierung  das verwendete 'flex_ond_day'-Objekt abgespeichert. 
Falls die Flexibiltät über Mitternacht geht, wird auch das entsprechende Objekt des nächsten Tages gespeichert.
Für die Berechnung der spezifischen Flexibiltäten wird die Methode 'compute_flexibilty' aufgerufen. 
Hierbei wird zudem zwischen der Berechnung mit und ohne Aktivierungszeit unterschieden ('fixdateflex' und 'spontanflex'). 
Diese beiden Berechnungen unterscheiden sich vor allem durch die SOC-Anpassung, welche im Falle der spontanen Flexibiltät nicht betrachtet werden muss. 
Die Visualierung erfolgt über die Methode 'visualize_flexibilty'. Dafür wird auf das zuletzt berechnete Flexibilitätsobjekt in der Liste 'flex_list' zugegriffen. 
Im Falle der spez. Flexibilität kann das Momentanpotential als Vergleich mit visualisiert werden. 
Hinsichtlich der Ladestartegien wird dies über die Methode 'visualize_aggregated_boundaries_wrt_ch_strategy' berechnet. 
Das Gesamt-Momentanpotential wird über die Methode 'visualize_aggregated_boundaries' aufgerufen und visualisiert. 
Über die Methoden 'visualize_spontanflex'/'...fixdateflex' wird die Visualisierung der berechneten spez. Flexibiltät aufgerufen. 
Im Falle der stat. Flexibiltät wird diese Methode für jede spez. Flex ausgelöst. Wichtig ist aber vor allem die Darstellung der Quantile. 
Dies geschieht über das 'risc object'. 
Dafür wird dieses initialisiert und die Methoden 'compute_min_quarte_quantiles' und 'visualize quantiels' aufgerufen.

Bevor genauer auf den Ablauf der Flexibilitätsberechnung eingegangen wird, sollen kurz einige wichtige Klassen dargestellt werden.

## Klassen
Neben der Klasse 'risk_object', welches für die Berechnung der stat. Flex aus übergebenen spez. Flexibilitäten zustaändig ist, gibt es die zwei Klassen 'fixdateflex' und 'spontanflex', welche die Berechnung der spez. Flexibilität für die unterschiedlichen Fälle mit und ohne Aktivierungszeit durchführen. 
Dafür wird auf das 'flex_one_day'-Objekt zurückgegriffen, welches die Energie- und Leistungsgrenzen über den Tagesverlauf des spezifizierten Tages berechnet. 
Hierfür werden sogenannte 'Flexboundary'-Objekte erstellt, welche, die Energie- und Leistungsgrenzen für ein Fahrzeug in einem Plug-In-Zeitraum berechnet. 
Diese Klasse wiederum greift auf die Klasse 'available_period' zurück, welche bei der Modellberechnung die verfügbaren Periode beschreibt (siehe Thesis). 
Aus den allgemeinen 'Flexboundary'-Objekten der Klase 'flex_one_day' erstellt die Flexibilitätsberechnung sogennnate 'Base...'- und 'flex_profile'-Objekte, welche für den konkreten Berechnungsfall die Lieferzeiten  und die lieferbare Energie berechnen. 
Objekte der Klassen 'Flex_profile' stellen das veränderte ladeverhalten dar und Objekte der Klasse 'base_profiles' das eigentliche Ladeverhalten. 
Neben den Klassen gibt es noch wichtige einzelne Methoden, wie 'compute_flex_bdry', welche aus einem Objekt der Klassse 'available periods' das FlexBoundary' erstellt, die Methode 'compute_energy_charged_according_to_ch_strategy', welche die Energie berechnet, die durch die Ladestartegien innerhalb des Plugin_Zeitraumes eines Fahrzeuges (übergeben durch die 'FlexBoundary') bis zu einem konkreten Punkt berechnet, 'compute_spontanflex' und '...fixdateflex', welche die Berechnung der Flexibiltät mithilfe der entsprechenden Klassen auslösen, 'compute_flexibilty', welche die allgemeine Flexibilitätsberechnung auslöst,...
Eine wichtige Datenstruktur ist die Klasse 'Aggregatedflex'. Sie speichert für einen Zeitintervall mit einer 'start_time' und 'end_time' mehrere Objekte, die aggregiert werden. 
In der Liste 'FlexBoundaries' der 'AggregatedFlex'-Klasse werden die entsprechenden Objekte abgespeichert und die Liste 'capacities' enthält die zugehörigen Kapazitäten, welche zur 'total_capacity' aufsummiert werden. 
Diese Klasse wird zum Aggregieren von 'FlexBoundary'-Objekten beim Berechnen der aggregierten Energie- und Leistungsgrenzen und bei der Berechnung der Flexibilität beim Aggregieren mehrerer Felxibiltätsprofile verwendet. 

### Available periods
Bevor auf den genauen Berechnungsablauf der Methode 'compute_flexibilty' eingegangen wird, wird die Berechnung der 'available_period's erläutert (Klasse in Datei variables.py), da diese anders als die restliche Flexibilitätsberechnungen bereits bei der Modellberechnung durchgeführt wird. 
Dies geschieht mit der Variable 'current_available_period' des EVs. Diese Variable wird während der Methode 'soc_during_trip' laufend aktualisiert. 
Wird das Fahrzeug angesteckt, wird die Ankunftszeit eines 'Trip's als Startzeit der Periode abgespeichert. 
Daneben sind die Informationen der verfügbaren Leistung, der zu diesem Zeitpunkt aktuelle SOC-Wert und eine Information, ob die Ladestation zu Hause oder an einer anderen Destination verwendet wird. 
Außerdem wird im nächsten Aufruf der Methode die Abfahrtsteit des nächsten Trips  als Ende der Periode abgespeichert. 
Zudem wird der 'SOC_need' (Siehe Thesis) berechnet (Methode 'getSOC_for_next_trip')
Die Variable 'current_avialable_period' wird auch über mehrere Tage hinweg befüllt, da eine verfügbare Periode auch über die Nacht gehen kann.
Die Perioden werden in der Liste 'available periods' zwischengespeichert, wenn eine Fahrt beginnt und somit die Endzeit der Periode bekannt ist.
Dauert eine Periode über Nacht und somit über mehrere Tage, wird die Periode für jeden dieser Tage abgespeichert, sodass bei der späteren Felxibiltätsberechnung die entsprechenden Tage alle relevanten Periode enthalten. Die verfügbaren Perioden werden als Liste in den Objkten der Klasse 'Day' ebenfalls abgespeichert.
Nicht jede Periode wird abgespeichert. Dies hängt mit den in der Thesis formulierten Bedingungen an die relevante Fahrzeugmenge zusammen. 
Es werden anhand des Parameters V2G_Aailability manche Perioden aussortiert. Mit der Methode 'Check_Availability' wird die in der Thesis beschriebene flexible Zeit berechnet. 
Für die Berechnung der Energiegrenzen wird zudem nur der verfügbare Plug-in-Zeitraum berücksichtigt. 
Das heißt die Zeit bis zum Laden der Mindestreichweite 'min_range' wird von der 'available_period' abgezogen. 
Dies geschieht mithilfe der Methode 'period_adaption' der Klasse 'available_period'. 
Der nicht betrachtete Anfangszeitraum wird in der Liste 'base_charging_periods' des zugehörigen 'EV's abgespeichert. 
In der variable 'last_period' wird immer die 'current_available_period# am Ende eines Tages abgespeichert. 
Im Falle vom Abbrechen der Methode 'soc_during_day# und dem erneuten rekursiven Aufruf, wird die 'current_available_period' in 'initialize_next-day' auf diese 'last_period' gesetzt, um die entsprechenden Einstellungen am Anfang des Tages wieder zurückzusetzen.




### Compute_flexibilty
(Datei flexibility.py)
#### Ablauf
Die Methode hat zwei Abschnitt
1) Befüllung der 'daylist' und Überprüfen der Parameter
2) Berechnung der 'flex_list' (spez. Flexibilität bzw mehrere spez. Flexibilitäten) 

##### Teil 1
Im ersten Teil der Methode werden die übergegebenen Parameter auf die Richtigkeit überprüft. 
Dabei wird auch die Liste 'Days' befüllt, die die Positionen der zu berücksichtigen den Tage enthält. Diese Liste besteht entweder aus dem Wert der Spezifikation 'flex_at_number_of_day' oder falls dieser auf eine Zahl kleiner als 0 gesetzt wurde, entweder im Falle der spez. Flexibilität nur die Position - 1, was dem letzten simulierten Tag enspricht, oder im Falle der stat. Flexibiltät mehrere Positionen, die durch die Methode 'compute_day_list' (Datei variables.py) berechnet werden. 
Diese Methode befüllt die Liste entweder mit allen simulierten Tagen oder falls 'Flex_at_Daytype' zwischen 1 und 7 liegt, nur die Tage die diesem Wochentag entsprechen. 
Werden mehr als 10 Tage simuliert, werden die ersten 10 Tage ignoriert, um den Einfluss der Startannahmen zu verringern (Start-SOC am ersten Tag) 
##### Teil 2
Im zweiten Teil der Methode, wird nun die Liste 'days' für jeden Simulationslauf (variable 'run') durchlaufen. 
Bei der spez. Flexibilität wird nur der durch den Parameter 'flex_at_number_of_run' spezifizierte Simulationslauf berücksichtigt. 
Es wird zwischen den zwei Fällen Flexibilität zu Hause (Parameter 'flex_at_home' bzw in dieser Methode Variable 'home')  und an allen Destination unterschieden.
Zudem weird überprüft, ob die entsprechende Flexibilitäten bereits berechnet wurden, um doppelte Berechnungen zu vermeiden. 
Falls die Flexibilität schon berechnet wurde, wird die Liste 'flex_list' mit der bereits berechneten Flexibiltät aufgefüllt, falls nicht wird die Flexibiltät berechnet. 
Dafür wird wiederum zwischen dem Fall, dass der Flexibiltätszeitraum über Nacht geht und dem standardmäßigen Fall, dass er nicht über Nacht geht, unterschieden. 
Für ersteren sind die 'available_periods' beider Tage wichtig. Diese 'available_periods' wurden bereits im Modell berechnet und werden nun aus dem Klassenobjekt des relevanten Tages kopiert. 
Es ist eine Liste aller 'available_periods' aller EVs an diesem Tag. Im Falle der Flexibilitätsberchnung zu Hause dürfen nicht alle abgespeicherten 'available_periods' berücksichtigt werden, sondern nur diejenigen, die an Ladestationen zu Hause stattfinden. 
Die Methode 'compute_avialable_periods' überprüft die Destination der Ladestationen aller 'available_period's und gibt die relevanten Perioden zurück. 
Für die Vorbereitung der Flexibilitätsberechnung werden nun aus diesen 'available_periods' die aggregierte Energigrenzen berechnet, falls dies nicht bereits durch vorherige Aufrufe  geschehen ist (Methode 'compute_aggregate_Bundaries'). 
Anschließend kann mithilfe der Methode 'compute_spontanflex' oder 'fixdateflex' die Flexibilität für den expliziten Tag berechnet werden. 
Im Falle der Flexibilität über Nacht wird die Flexibiltät des ersten Tages bis 0 Uhr berechnet und dann die Flexibiltät am zweiten Tag hinzugefügt. 
Dafür wird im Methodenaufruf der Methoden 'computespontanflex' oder '...fixdateflex' das Klassenobjekt des ersten Tages übergeben. 
Für diesen Fall müssen die aggregierten Grenzen beider Tage berechnet werden. 
##### Teilmethoden der Flexibilitätsberechnung
###### Compute_aggregated_boundaries
(Datei flexibility.py (flex_one_day-Klasse))
Diese Methode ist eine Methode der Klasse 'flex-_one_day'. Jedes Objekt der Klasse 'day' besitzt eine Attribut dieser Klasse, welches die Flexibilitäten und die Energie- und Lesitungsgrenzen dieser Klasse speichert. 
Die Klasse hat die Listen 'flex_capacities_c/dc', welche die Energiegrenzen an wichtigen Zeitpunkten der aggregierten Energiegrenzen bezüglich des Ladens und des Entladen abspeichern. 
Die entsprechenden Zeiten werden in den Listen 'flex_times_c' und '...dc' abgespeichert. Analog gibt es diese Listen für die Leistungsgrenzen. 
Der Parameter 'aggregation_computed' gibt an, ob die Berechnung bereit stattgefunden hat und die Listen schon befüllt sind. 
In den Listen 'fixdateflexes_of_day' und 'spontanflexes_of_day' werden die berechneten Flexibilitäten dieses Tages abgespeichert. 
Mit der Methode 'compute_aggregated_boundaries', werden die Listen der Energie- und Lesitungsgrenzen befüllt. 
Die Listen '...capacities' bestehen aus mehreren 'AggregatedFlex'-Objekren, welche zusammen den Zeitraum dieses Tages abbilden und in Intervalle unterteilen. 
Jedes 'AggregatedFlex'-Objekt hat einen Startzeitpunkt und Endzeitpunkt. Der Endzeitpinkt entspricht dem Startzeitpunkt des nächsten Objektes.  
Die Zeiten entspringen aus der entsprechenden Liste 'flex_times...'. 
Für diese Zeitintervalle werden die relevanten verfügbaren Plug-in-Zeiträume aller verfügbaren Fahrzeuge abgespeichert. 
Für diese verfügbaren Plugin-Zeiträume werden aber nicht nur die Start- und Endzeiten betrachtet, sondern die Energie- und Leistungsgrenzen. 
Hierfür werden 'FlexBoundary'-Objekte definiert. Diese 'FlexBoundary'-Objekte enthalten den verfügbaren Plugin-Zeitraum eines Fahrzeuges mit weiteren relevanten Zeiten für die Energie- und Leistungsgrenzen. 
Auf die Leistungsgrenzen weird hier allerdings nicht mehr genauer eingegangen, da diese für die spätere Flexibiltätsberechnung nach der Berechnungsart dieser Klasse nicht relevant sind. 
'compute_aggregated_boundaries' berücksichtigt zunächst für die 'flex_times_c' die relevanten Zeiten 'start', 'end' und 't_max_start' und für 'flex_times_dc' die Zeiten 't_start', 't_end', 't_min_start', 't_min_start_2'. 
In der Methode 'compute_times' werden für alle 'available_periods' die 'FlexBoundary'-Objekte berechnet. 
Aus diesen Objekten resultieren die Zeiten, die relevant sind, um die Grenzen eindeutig zu beschreiben. 
Die Liste 'flex_times' wird nun so befüllt, dass sie alle diese Zeiten chronologisch enthält. Die berechneten 'FlexBoundary'-Objekte werden in der 'FlexBoundaries'-Liste abgespeichert. 
Anschließend werden die 'flex_capacities'-Listen mit den 'AggregatedFlex'-Objekten befüllt. 
Dafür wird jedes 'FlexBoundary'-Objekt zu den Intervallen zugeteilt, in welchem die entsprechenden Fahrzeuge verfügbar sind. 
Beim Hinzufügen von 'FlexBoundary'-Objekten wird das 'AggregatedFlex'-Objekt auf mehrere Weisen aktualisiert. 
Zum einen wird die 'FlexBoundary' zu der Liste 'FlexBoundaries' hinzugefügt. Der Liste 'capacities' wird die Lade- oder Entladeleistung hinzufgefügt. 
Der 'modus'-Liste wird die dem 'FlexBoundary'-Objekt zugehörige Modus hinzugefügt, der beschreibt,  welcher Teil von emin(t) oder emax(t) zu diesem Zeitpunkt abgebildet wird: 
"Laden nach Emax" oder "Emax schon geladen" bzw. "laden nach emin", "emin schon geladen" oder "laden von eneed". 
Zudem wird die 'days' Liste erweitert. Sie enthält eine Variable, an welchem Tag der  zugehörigen 'available period' sich die 'FlexBoundary' am berücksichtigten Tag befindet 
(eine 'available_period' kann mehrere Tage gehen und die Zeiten sind aber als 'nptime'-Objekt abgespeichert, welches nur Zeiten kleiner zwischen 0 und 24 Uhr abspeichert, sodass der Tag auch spezififziert werden muss).

Nach dem Aufruf von 'compute_aggregated_boundary'  beinhalten Die 'flex_capacities' die Zeitintervalle mit allen in diesen Zeitintervallen verfügbaren Fahrzeugen und den zugehörigen Energiegrenzen. 
Die zeitabhängigen Energiegrenzen (emin(t) emax(t))  werden über den Modus beschrieben, der angibt, in welchem Zustand sich die zeitanhängige Energiegrenze in den Zeitintervallen befinden. 

###### Flx bdry
(Datei AggregatedFlex.py)
Ein 'FlexBoundary'-Objekt bildet die Energiegrenzen eines verfügbaren Plugin-Zeitraumes ab, wie sie in der Thesis abgebildet und beschrieben wurden. 
Das Objekt speichert das zugehörige Fahrzeug, die 'available_period', die Energiewerte 'E_curr', 'E_max', 'E_min' und 'E_need' und mehrere Zeiten. 
Diese Variablen werden aus der bei der Initialisierung übergebenen 'available period' berechnet. 
Für diese Berchnung ist die Methode 'compute_boundary' zuständig, welche aus den drei Teilmethoden 'compute_energy_boundary', 'compute_power_bdry' und 'compute_simple_times' besteht. 
'Compute_energy_bdry' berechnet direkt aus der 'available period' die intialen Energievariablen für 'E_min' und 'E_max' , welche die Grenzen beschreiben, was maximal bis MAX_SOC bzw MIN_SOC geladen werden kann 
Die Methode 'compute_simple_times' berechnet aus diesen initialen Energievariablen die zugehörigen Zeiten, wann die Energiegrenzen 'E_max' 'E_min' mit der gegebenen 'charging_power' erreicht werden können. 
't_start' ist der Startzeitpunkt des verfügbaren Plug-in-Zeitraumes (plv_s in der Thesis), 't_end' das Ende, 't_max_start' der frühestmögliche Zeitpunkt zum Erreichen der max Grenze', 't_min_start' analog zu e_min, 't_min_start2' ist der Zeitpunkt ab dem laden gestartet werden muss, um e_need zu erreichen, wenn zuvor maximal entladen wurde. 
Im Laufe der Methode werden die initialen Energiewerte für 'E_max' und 'E_min' angepasst, falls diese nicht mit der verfügbaren Zeit zusammenpassen. 
Zunächst wird 't_max_start' direkt aus der Zeit berechnet, die es benötigt das initialen 'e_max' zu laden und Analog t_min_start (mithilfe der Methoden 'time_to_charge/discharge' des evs). 
Mithilfe der Methode 'adapt_bdry_if_too_less_time' wird nun der Fall berücksichtigt, dass die initialen Werte für 'E_min' und 'E_max' im  verfügbaren Zeitraum nicht erreicht werden können. 
Ist dies der Fall werden die Zeit und die Grenze entsprechend angepasst. Dafür wird die Zeit berechnet, die es benötigt die Energie zu laden und mit der verfügbaren Zeit verglichen. 
Bei beiden Werte für 'E_max' und 'E_Min' ist das die Enegie, die mit maximaler Power erreicht werden kann. 
Für 'E_min' sind diese Berechnung nur nötig, falls 'E_min' kleiner als 0 ist. 
Bei der Berechnung von 't_minstart'  kann es zu einer weiteren Anpassung von 'E_min' kommen. 
Bisher wurde nur das Erreichen von 'E_min' berücksichtigt. Das Erreichen von 'E_need'  nach dem Entladen wurde bisher ignoriert. 
Hierfür wird zunächst der Zeitpunkt berechnet, ab dem geladen werden müsste, um 'e_need' ausgehend von geladener Energie 'E_min' (evtl negariv: entladener Energie) zu erreichen. 
Kommt es zu Überschneidungen zwischen diesem Zeitpunkt und dem zuvor berechneten Zeitpunkt 't_min_start' muss 'E_min' weiter angepasst werden, da nicht genügend Zeit vorhanden ist 'E_min' zu entladen und dann wieder 'E_need' zu laden. 
Diesen Fall behandelt die Methode 'determine_energy_without_restrchting_min_soc'. 
Diese Methode funktioniert wie in Gleichung 5.33) in der Thesis. Von der verfügbaren Zeit wird die Zeit abgezogen, die es benötigt 'e_need' zu laden und die restliche Zeit kann nun je nach Verhältnis der Ladelesitung zur Entladeleistung in  Entlade- und Ladezeit aufgeteilt werden. 
In gelxubing 5.33) wurde das Verhältnis 1 zu 1 angenommen, sodass für beide Teile gelcih viel Zeit übrig ist. Falls 'e_need' kleiner als Null ist, wird zur Entladezeit auch die Zeit zum entladen für 'e_need' hinzugefügt. 
Andernfalls gehört diese Zeit zur Ladezeit. Die Energiegrenze 'emin(t)' besteht  aus Entladen von 'e_min', Wiederaufladen dieser Emergie und Laden von 'e_need', falls 'e_need' größer null. 
Falls 'e_need' kleiner Null, dann kann erst 'e_need' entladen werden, dann der Rest bis zu 'e_min' und schließlich wieder aufgeladen bis zu 'e_need'.
Die Zeiten 't_min_start' und 't_min_start2' werden entsprechend aus der Lade- und Entladezeit für die Fälle 'e_need' größer oder kleiner Null berechnet. 

###### 'compute_spontanflex'
(Datei Spontanflex.py)
Die Methode 'compute_spontanflex' der Klasse 'flex_one_day' steuert die Berechnung der Flexibilität ohne Aktivieurngzeit. 
Falls kein Spontanflex-Objekt übergeben wird, wird ein neues erstellt. Mithilfe der klasseneigenen Methode 'Insert_new_entry_at_certain_time' wird die 'flex_capacities_c'-Liste mit Einträgen zum Startzeiptunkt un Endzeitpunkt der Flexibilität erweitert. 
Dieser neue Eintrag enthält alle verfügbaren 'FlexBoundaries'-Objekte an diesen Zeitpunkten, welche durch Kopieren aus den Nachbarintervallen übernommen werden. Die Intervallzeiten werden enstprechend angepasst.
Alle Intervalle zwischen diesen beiden Einträgen werden nun nach und nach abgearbeitet, um alle verfügbaren Fahrzeuge, zu denen diese 'FlexBoundary'-Objekte gehören bei der Flexibilitätsberechnung zu berücksichtigen. 
Die Flexibilität wird dabei immer gleich für alle Ladestrategien und Heuristiken berechnet, die in den entsprechenden Parametern abgespeichert sind. 
Es wird auch sowohl die positive als auch die negative Flexibilität berechnet.
Die Berechnung beginnt mit der Methode 'compute_power_profiles_at_start' des 'spontanflex'-Objektes.

###### 'compute_power_profiles_at_start'
(Datei Spontanflex.py)
An die Methode wird das 'Aggregatedflex'-Objekt mit den 'FlexBoundary'-Objekten zum Start des Flexibilitätszeiraumes übergeben.
Die Methode durchläuft alle 'FlexBoundary'-Objekte und berechnet je nach Ladestrategie die Energie, die bis zum Startzeiptunkt des Flexibilitätszeiraumes geladen wurde mithilfe der Methode 'Compute_charged_until_acdoridng_charging_szrategy' (Datei ChargingStrategy.py in 'simulation_model'). 
In dieser Methode wird das Verhalten der drei Ladestrategien analog zur Thesis definiert.
Mithilfe dieser geladenen Energie wird ein neues 'FlexBoundary'-Objekt erstellt, welches den Startzeiptunkt des Flexibilitätszeiraumes als Startpunkt hat und nicht mehr den Startzeiptunkt des Plug-In.Zeitraumes des zugehörigen EVs. 
Hierzu werden die Energiegrenzen des alten Objektes entsprechend der bisher geladenen Energie neu berechnet. 
Diese neue Berechnung erfolgt mithilfe der Methoden 'copy_and_change' und 'compute_simple_time'. 
Mit dieser neuen 'FlexBoundary'-Objekten kann die Methode 'compute_profiles' aufgerufen werden. 

###### 'Compute profiles' 
(Datei Spontanflex.py)
Diese Methode berechnet sogenannte Flexibiltätsprofile für das Laden und Entladen von Energie und speichert diese ab. 
Hierzu werden Objekte der Klasse 'flex_profile' erstellt (Datei AggregatedFlex.py), welche für die Berchnung des veränderten leistungprofiles verwendet werden können. 
Die Profile werden initialisiert mit der zugehörigen 'FlexBoundary', der Ladestartegie und dem Modus, der beschreibt, ob positive oder negative Flexibilität berechnet werden soll. 
Mit der Methode 'Compute_profile' der Klasse 'flex_profile' kann dann das Profil genauer berechnet werden. 
Zunächst wird die Überschneidung des Flexibilitätszeiraumes mit dem verfügbaren Zeitraum des 'FlexBoundary'-Objektes berechnet. 
Dies muss nicht unbedingt der gesamte Flexibiltätszeitruam sein, da es sein kann, dass das Fahrzeug schon früher losfahren muss. 
Je nach Modus wird nun die maximale Energie berechnet die maximal in diesem Zeitraum entladen oder geladen werden kann ohne die Grenzen zu verletzen. 
Für das maximale Laden ist dies einfach die Energie 'E_max', welche für die neuen 'FlexBoundaries' ausgerechnet wurde. 
Für  das Entladen muss die Grenze zum Ende des Flexibilitätszeitraumes berücksichtigt werden.  
Hierfür wird zuerst überprüft, ob der Zeitpunkt 't_min_start2', der Zeitpunkt, ab dem 'e_min' wieder für 'e_need' ansteigt, kleiner ist als das Ende des Flexibilitätszeiraumes. 
Falls das nicht der Fall ist, kann so viel wie möglich entladen werden ohne dabei 'E_min' zu unterschreiten. 
Die untere Grenze für die verfügbare Energie ist 'E_min' analog zum Fall beim Laden. 
Falls 't_min_start2' kleiner ist und auch 't_end' kleiner und 'e_need' größer Null, muss im Flexibilitätszeitruam 'E_need' geladen werden (Auch bei positiver Flexibilität) 
Falls dies nicht der Fall ist, wird mithilfe der Methode 'determine_energy_without_restricting_minSOC' emin(t=fe) die maximal verfügbare Energie berechnet. 
Dazu wird der Zeitpunkt berechnet, ab dem geladen werden muss. Ist dieser kleiner als Null muss ebenfalls Energie geladen werden. 
Falls nicht, kann entladen werden. 
Es wird für alle Fälle die Energie, die geladen oder entladen werden muss berechnet. 
Außerdem gibt das Attribut 'profile' an ob diese Energie mit voller lestung über den gesamten Zeitraum geladen werden kann (Profil =Base) oder ob sonst die Grenze überschritten würde und die volle Leistung über den gesamten Zeitraum zu viel wäre. 
Der zweite Fall wird mit profile=flexible gekennzeichnet, da die verfügbare Energie auf verschiedene Arten geliefert werden kann.
'compute_flex_values' berechnet anhand der gespeicherten Energiegrenze für diesen Zeitraum und der verfügbaren Leistung die tatsächlich verfügbare Energie. 
Diese ist für beide Heuristiken gleich. Die Heuristiken unterscheiden sich aber, wie die Flexibilitätsprofile mit "flexible" Kennzeichnung für das Attribut 'profile' verwendet werden. 
'compute_flex_values' wird nur ausgerufen, wenn die verfügbare Zeit des Profiles (Überschneidung Flexibilitätszeitraum und plugin-Zeitraum) genügend groß ist (>MIN_DELIEVERY_TIME) und nicht der Fall der Ladestrategie 'as soon as possible' bei negativer Flexibilität eingetreten ist. 
In diesen Fällen ist das veränderte Leistungprofil gleich zum Eigentlichen Leistungsprofile, weswegen diese aus der Berchnung ausgeschlossen werden können. 
Es werden nur 'FlexBoundary's betrachtet, bei denen Unterschiede zwischen eigentlichen und veränderten Leistungsprofile vorhanden sind. 
Das veränderte Leistungsprofil wird durch das berechnete 'flex_profile' mehrere Fahrzeuge berechnet. 
Zu jedem 'flex_profile' das berechnet wird, wird nun auch ein 'base_profile' (Klasse baseprofile in Datei AggregatedFlex.py) berechnet, welches die Energie berechnet, die durch die Ladestartegien verbraucht würde. 
Die beiden berechneten Flexibilitätsprofile für eine 'FlexBoundary' werden nun zur 'spontanflexlist' hinzugefügt. 
Dieses besteht analog zu den "AggregatedBoundaries"('flex_capacities_c'/'...dc') aus einer Liste mit 'Aggregtaedflex'-Einträgen für jeweilige Intervalle innerhalb des Flexibilitätszeitraumes. 
Wird ein neues 'flex_profile'/'bsae_profile' berechnet, wird es zu allen relevanten Intervallen das 'flex_profile' hinzugefügt. 
Es wird eine capacity -(Leistung die entladen wird) hinzugefügt. Falls die End- und oder Starzzeit des Flexibilitätsprofiles noch nicht als Intervallgrenze besteht (ein 'AggregatedFlex'-Objekt nicht diese starzzeit/Endzeit hat) wird ein neuer 'Aggregateflex'-Eintrag erstellt (falls noch nicht vorhanden).
Das Erstellen neuer Einträge bedeutet das Kopieren alter benachbarter Einträge und die Abänderung der Zeiten der 'Aggregatedflex'-Einträge. 
Die 'Aggregatedflex'-Objekte enthalten Start- und Endzeiten der Intervalle für die Sie die Kapazität berechnen. 
Beim Erstellen neuer Einträge müssen also die Zeiten der benachbarten Einträge aktialisiert werden. 
Beim Hinzufügen neuer Flexibilitätsprofile zu einem Intervall wird außerdem die Varibale 'total_capacity' aktualisiert. 
Die 'spontanflex' wird so schrittweise durch die Berechnung und das Hinzufügen der Flexibilitätsprofile berechnet. 
Am Ende repesäntiert die 'total_capacity' bei den 'Aggregatedflex'-Objekten die Leistung in diesem Intervall. 
Es wird zwischen dem Hinzufügen von 'Base_profiles' (append_strategy_capacity') und 'flex_'profiles' ('append_power_capacity') unterschieden. 
Base. Profiles entsprechen dem eigentlichen Leistungsprofile und werden bei positiver Flexibilität hinzuaddiert und bei negativer Flexibilität substrahiert.
'flex_profiles' werden entpslrchrn ihres Modus entweder hinzu addiert oder substrahiert (entladen oder geladen) .

###### Weiteres Vorgehen in 'compute_spontanflex'/ 'compute_fixDate_flex' nach 'compute_power_profiles_at_start'
Nach der Methode 'compute_power_profiles' wird für jeden weiteren Intervall innerhalb der "aggregatedboundaries" (flex_capacites_c) überprüft, ob neue Fahrzeuge hinzugekommen sind, die bisher noch nicht betrachtet wurden.
Ist dies der Fall wird für die entsprechenden 'FlexBoundary' ebenfalls 'compute_power_profile' aufgerufen. 
Eine Anpassung der 'FlexBoundary' wie bei 'compute_power_profiles_at_start' ist nicht notwendig, da die 'FlexBoundary' zu diesem Zeitpunkt startet und somit schon auf dem richtigen Stand ist 

###### 'compute_fixDate_flex'
(Datei 'fixDateflex.py')

Die Berechnung von der 'fixdateflex' funktioniert analog zur Berechnung der 'spontanflex' mit der Klasse 'fixDateflex' nur, dass vor 'compute_power_profiles_at_start' noch die SOC-Anpassung vorgenommen wird. 
Hierzu wird vor dem Aufruf der Methode 'compute_power_profiles_at_start' die Methode 'determine_relevant_boundaries' aufgerufen. 
Diese Methode geht alle 'FlexBoundary'-Objekte des ersten Intervalls in der 'flex_capacities_c'-Liste durch und bestimmt die Startzeiptunkte der Soc-Anpassung.
Dabei hilft die Methode 'determine_SOC_adaption_at_startpoint'. 
Zu jeder relevanten 'FlexBoundary' wird der boolean 'whole_peeiod' abgespeichert, der angibt, ob die Plug-In-Periode innerhalb der Aktivierungszeit oder das 'EV' schon zuvor angesteckt wurde. 
Der entsprechende Start der SOC_Anpassung wird ebenfalls abgespeichert. 
In 'compute_power_profiles_at_start' wird nun die SOC-Anpassung vorgenommen. 
Falls 'whole_period' == 'True' gilt, muss das 'FlexBoundary'-Objekt nicht angepasst werden, um die Energie zu berechnen, die bis zum Aktiveirungsstaftzeitpunkt geladen wurde, da die 'FlexBoundary'-Objekte immer den Start es Plug-In-Zeitraumes repräsentieren und die entsprechenden Energiegrenzen speichern. 
Für den Fall  'whole_period' == 'False' muss die bereits geladene Energie allerdings berechnet werden. 
Hierbei hilft die Methode 'compute_charged_until_certain_time_according_to_Charging_strategy', welche genau diese Energie bestimmt. 
Anhand dieser Energie wird ein neues 'FlexBoundary'-Objekt mit neuen Energiegrenzen zum Zeitpunkt des Startzeitpunktes des Aktivierungszeitraumes berechnet. 
Dafür gibt es die Methode 'Copy_and_change' der Klasse 'FlexBoundary', die das bisherige 'FlexBoundary'-Objekt kopiert und anhand der geladenen Energie aktualisiert. 
Zudem können mit der bereits beschriebenen Methode 'compute_sinple_times' die Zeiten zum Erreichen der Grenzen entsprechend angepasst werden. 
Im nächsten Schritt kann nun mit diesen Energiegrenzen berechnet werden, wie viel Energie bis zum Start der Flexibilitätsbereitsellung geladen bzw. Entladen werden kann. 
Dies ist entweder die Energie der Energiegrenzen oder falls die Zeit nicht ausreicht die Energie, die im Aktivierungszeittrraum geladen werden kann. 
Für die SOC-Anpassung für die positive Flexibilität wird dementsprechend geladen und für die negative Flexibilität entladen. 
Beide Fälle werden berechnet und in den Variablen 'e_curr_new_max' und 'e_curr_new_min' abgespeichert. 
Anschließend wird erneut mithilfe der Methode 'Copy_and_change' nun das 'FlexBoundary'-Objekt aktualisiert und damit für die Profilberechnung mit 'compute_profiles' vorbereitet.
Diese Methode wird mit dem entsprechenden 'FlexBoundary'-Objekt, das nun verändert wurde, aufgerufen (bei der Berechnung der "spontanen Flexibilität" war es das gleiche 'FlexBoundary'-Objekt, da keine Anpassung vorgenommen wurde). 
Zudem wird das alte 'FlexBoundary'-Objekt zur Berechnung der 'Base_profiles' (für das eigentliches Lastprofil) hinzugezogen. 


### 'Visualize_flexibilty'
(Datei 'flex_object')
#### spezifische Flexibilität
Im Falle der spez. Flex wird mithilfe der Methode 'visualize_spontanflex' oder 'visualize_fixdateflex' die spezifische flex visualisiert. 
Innerhalb dieser Methode wird, falls so gewollt, zudem das Gesamt-Momentanpotential und das Momentanpotential hinsichtlich der Ladestrategien ebenfalls abgebildet. 
Das Gesamtmomentanpotential ergibt sich direkt aus der 'flex_capacities_c'-Liste mit den abgespeicherten 'total_capacitie's für die entsprechenden Intervalle. 
Hinsichtlich der Ladestrategien ist die Berechnung etwas komplizierter, worauf hier aber nicht genauer eingegangen wird.
#### statistische Flexibilität
Im Falle der stat. Flexibiltät wird ein 'risk_object' erstellt  (Klasse 'risk' in Datei 'risk.py') und mit den berchneten spez. Flexibilitäten befüllt. 
Die Methode 'compute_min_quarter_quantiles_from_flex_list' berechnet aus diesen Flexibiltäten die Quantile, das Maximum, das Minimum und den Durchschnitt.
Mit 'visualize_quantile' werden die Quantile als horizontale Linie dargestellt. 
Die Berechnung der Quantile innerhalb von 'compute_min_quarter_quantiles_from_flex_list' erfolgt durch den Aufruf mehrerer Methoden. 
'compute_statistics_of_flexes' berechnet das Minimum, Maximum und den Durchschnitt der einzelnen Leistingsprofils der spez. Flexibiltä und speichert diese in einer jeweiligen Liste an. 
'compute_statistic_values' der Klasse 'fixdateFlex' berechnet das Mimima, Maxima, Durchschnitt des Leistungsprofils der spezifischen Flexibiltität und gibt diese zurück. 
Nach dieser Methode berechnet 'compute_quantile' nun die Quantile bzw. Minimimum, Maximum und Durchschnitt aus den statistischen Werten aller spezifische Flexibilitäten. 
Je nach übergebenen Statistik-Modus wird das minimale, maximale oder der Durchschnitt der Leistingsprofle hinzugezogen. 
Die statistische Flexibilität der Thesis wurde durch das Mimima der spez. Flex definiert, weshalb die Methode 'compute_min_quarter_quantiles_from_flex_list', wie der Name schon sagt, die Berechnung mit dem Modus "min" aufruft. 
Die stat. Werte werden in der Liste 'quantiles' abgespeichert, welche dann von 'visualize_quantiles' zur Visualisierung verwendet werden