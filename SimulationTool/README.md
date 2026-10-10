# Simulation tool
Bei der objektorientierten Implementierung des Simulationstools in python wird wie beim Konzept zwischen den Komponenten Simulationsmodell und Flexibilitätsberechnung unterschieden. 
Zunächst wird noch auf die generelle Struktur des Simulationstools eingegangen.

## Struktur 
Die Funktionsweise wurde bereits in der Masterarbeit beschrieben. 
Basis des Tools ist  die Klasse simulation_Tool mit den für den Nutzenden wichtigen Methoden:
 'load_model', 'save_model', 'run_model', 'calculate_flexibility' und 'visualize_flexibility', welche in einer main-Methode   ausgeführt werden können. Zudem können über die... Datei die Parameztereinstekkungen vorgenommen werden. 
Die Klassendefinition findet sich in der Datei 'simulation.py'
Das Tool kann mit der Methode 'start_tool' gestartet werden (siehe Beispiel in 'SimulationTool-Thesis.py')

Die Parametereinstellungen werden in 'SimulationTool_Settings.json' definiert. 
Bei jedem Start des Simulationstools werden diese Parameter in einer Klasse abgespeichert (settingsContainer), auf die im Laufe der Simulation und der Flexibilitätsberechnung mit get-Methoden zugegriffen werden kann. 
Außerdem können in den Tabellen 'PopulateUsers', 'EVModels' und 'ChargingStationTypes' die Verteilungen der Eigenschaften der EV user, der Ladestationen und der EV Modelle verändert werden.
Die Weiteren Tabellen sind Beispielkonfigurationen für andere Szenarien.

## Klasse SimulationTool
Aufgabe der Klasse 'simulationTool' ist die Koordination zwischen den Komponenten Flexibilitätsberechnung, Simulationsmodell und den Parameztereinstekkungen  durch die Umsetzung der in der Thesis beschriebenen Funktionsweise. 
Damit dies reibungslos gewährleistet ist, besitzt die Klasse die Attribute 'model_data' und 'flexibility_object', welche das zuletzt berechnete oder geladene Modell und die zuletzt berechnete Flexibilität abspeichern. 
Die Methode start_tool (außerhalb der Klasse) startet das Simulationstools, lädt die globalen Parameter aus der Parametereinstellungsdatei und speichert diese als internes Klassenattribut des Simulationstools  ab (settings). 
Diese Abspeicherung gewährleistet das Zurücksetzen der globalen Parametern nach Berechnungen mit anderen Modell- oder Flexibilitätsspezifikationen oder dem Laden alter Modelle. 
Dies bewirkt, dass innerhalb einer Ausführung des Tools mehrere verschiedene Berechnungen ausgeführt werden können.
Dies hat den Vorteil, dass innerhalb der Methode, in der das Simulationstool gesteuert wird, durch nutzerdefinierte Methoden mehrere unterschiedliche  Berechnungen miteinander verglichen werden können. 

### Methoden der Klasse
#### load_model
'load_model' lädt ein an einem übergebenen Speicherort als pkl-Datei abgespeichertes Modell. 
Ist kein Speicherort gegeben wird der Default-Dateiname 'model' verwendet. Die Methode überschreibt die globalen Parameter mit den Modell-Parametern des geladenen Modells, damit die globalen Parameter beim Aufruf durch  weitere Methoden dem aktuellen Modell entsprechen. 
Das geladene Modell wird im Attribut 'model_data' abgespeichert. 

#### save_model
'save_model' speichert das Modell des Klassenattribut 'model_data' an einem angegebenen Speicherort als pkl datei. 
Ist kein Speicherort angegeben, wird analog zu load_moddl der Standarddateiname 'model' innerhalb des Projektordners ausgewählt. 

#### run_model
'run_model' führt die Methode 'run' mit den übergegebenen Modellspezifikationen aus.
 Werden keine Spezifikationen übergeben, werden die  globalen Parameter auf die entsprechendne Parametereinstellungen (Attribut: settings)  zurückgesetzt. 
Nach der Modell-Berechnung wird das Modell dem Attribut 'model_data' zugewiesen. 

#### calculate_flexibility
'Calculate_flexibilty' verwendet analog zu 'run_model' die übergebenen Spezifikationen oder setzt die entsprechenden globalen Parameter zurück auf die Parametereinstellungen. 
Es wird die Methode 'compute_flexibility' der Flexibiltätsberchnung ausgeführt. Die berechnete Flexibilität wird innerhalb des 'flexibility_object' abgespeichert. 
Zudem wird die Flexibiltät auch am entsprechenden Simulationstag bei den Modelldaten 'model_data' abgespeichert. 

#### visualize_flexibility
'visualize_flexibilty' verwendet ebenfalls Spezifikationen oder überschreibt die globalen Parameter durch die ursprünglichen parametereinstellungen (Attribut settings) und verwendet diese bei Aufruf der Methode 'visualize_flexibilty' des 'flex_object'. 
