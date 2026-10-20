# Reproduction of Paper Figures
For reproducing paper results/figures, look in file `ReadMe_PaperPlots` in folder `paper_plots`.
Additional data to reproduce all figures or analyze original models can be found in https://zenodo.org/records/23289603.
`README.md` in folder `model_and_scenario_generation` contains additional instructions, when this additional data is needed.

# EV Fleet Flexibility Simulation Tool

This repository contains a Python-based simulation tool designed to estimate the flexibility potential of an electric vehicle (EV) fleet. 
The tool evaluates how an aggregated fleet can provide upward or downward flexibility for electricity markets (e.g., frequency regulation, spot markets), using simulated mobility, charging behavior, and battery dynamics.
Two components 'flexibility calculation' and "simulation model".

---
# Extensive explanation in german in 'Simulationstool.pdf' how simulation model and flexibility calculation works


# Project Structure

## Directories

- **analysis_methods**: Analysis models and evaluation methods.
- **config**: Configuration settings and parameters.
- **dataCharging**: Charging data used for model validation. Some files exceed GitHub's 100 MB file size limit and have been removed from this repository: `alreadyLoaded/UK_charging_home_whole.pkl`, `modelData/VehicleList2.pkl` and `Charging_data_for_tests/electric-chargepoint-analysis-2017-raw-domestics-data.csv`. These are available at [LINK EINFUEGEN] and must be copied back into their respective folders before running scripts/plots that depend on them (e.g. Figure 12).
- **dataTC**: Trip chain data used by the simulation model.
- **flexibility_calc**: Methods for flexibility calculation.
- **helper_files**: Utility and helper functions.
- **models_final**: Final models used in the paper. The `.pkl` model files have been removed from this repository to save space and are available at [LINK EINFUEGEN]. Copy them back into this folder before running the scripts/plots that depend on them (Figure 12, Figure 18).
- **paper_plots**: Scenario evaluation and plotting scripts used for the paper.
- **parameter_variations2**: Results and models for parameter variation studies.
- **pl_variations**: Plug-in activity variation scenarios and corresponding models.
- **plugin**: Plug-in configuration scenarios. The `VehicleList_B4_SOC_AFTER30_SOC_PLUG40.pkl` needed for Figure 6 exceeds GitHub's 100 MB file size limit and has been removed from this repository. It is available at [LINK EINFUEGEN] and must be copied back into `plugin/B4_SOC_AFTER30_SOC_PLUG40/` before reproducing Figure 6.
- **scenarios**: Computed simulation scenarios.
- **scenarios_final**: Final scenarios used in the paper (e.g. for the correlation analysis).
- **simulation_model**: Core simulation model methods.
- **SimulationTool**: Common SimulationTool functions and implementations.

## Files

- **Installation.txt**: Installation instructions.
- **Known_bugs.txt**: List of known issues and limitations.
- **requirements.txt**: Required Python packages.
- **SimulationTool.pdf**: German documentation of the SimulationTool.
- **SimulationTool_main.py**: Main entry point containing example simulation runs.
- **test.py**: Test functions and validation scripts.
## 1. Purpose of the Tool

The tool models EV user behavior, charging behavior, and battery states on a **mesoscopic level**, without relying on local traffic maps. It simulates:
- Daily mobility patterns (trip chains)
- Charging events at home, work, and public locations
- Battery state of charge (SOC) evolution
- Flexibility that the fleet can provide (energy & power) during selected time windows

Two types of flexibility can be computed:
- **Specific flexibility**: For a single simulation day and a specific flex-time window  
- **Statistical flexibility**: Based on multiple days or runs (Monte‑Carlo style), to quantify risk and variability
- both with or without activation time (Preparation time for flexibility delivery)
---

## 2. Structure of the Tool
![img.png](figures/img.png)
The tool consists of two main components:

### **1. Simulation Model**
Generates:
- Users with individual attributes (age, mobility type, region, etc.)
- EV models with technical specs (battery size, charging power, consumption)
- Charging station distributions and with tehnical specs
- Daily trip chains & charging events  
- SOC trajectories of all vehicles

### **2. Flexibility Calculation**
Uses simulation outputs to compute:
- Available EVs during a flex window
- Energy and power limits based on SOC, mobility needs, and charging power
- Changeable load profiles (positive or negative flexibility)
- Effects of activation time (pre-conditioning SOC before flex window)
- Flexibility under different charging strategies and heuristics

---

## 3. How It Works

The tool is controlled via functions of class Simulation from `SimulationTool\simulation.py`.  
![figures/function.png](figures/function.png)

Key operations include:

### **Run or load a model**
- `run_model(parameters)`  
  Runs the mobility and charging simulation for multiple days and users  
- `load_model(path)`  
  Loads previously saved model data  
- `save_model(path)`  
  Stores simulation outputs for reuse  

### **Calculate flexibility**
- `calculate_flexibility(parameters)`  
  Computes flexibility for:
  - Chosen charging strategies  
  - Selected heuristics  
  - Positive and negative flexibility  
  - Specific or statistical mode  
  - With or without activation time  

### **Visualize results**
- `visualize_flexibility(parameters)`  
  Creates power/energy flexibility plots  
  (can display or save images)

---

## 4. Input Parameters

There are three groups of inputs:

### **A. Model Parameters**
Control the simulation itself:
- Number of days, users, runs, start day (week day)
- Energy consumption model  
- Trip chain generation settings  
- Plug‑in behavior
- Charging station availability

### **B. Flexibility Parameters**
Specify how flexibility is calculated:
- Start time & duration of flex window
- Minimum SOC & tolerances
- Activation time (pre-conditioning)
- Allowed charging strategies:
  - *As soon as possible*
  - *As late as possible*
  - *As long as possible*
- Heuristics:
  - *Max at start*
  - *Constant*


### **C. Input Tables**
Define distributions:
- User attributes (`PopulateUser`)
- EV models and shares (`EVModels`)
- Charging station types & locations (`ChargingStationTypes`)

### Parameter/input adaption 
- adaption of parameters (A,B) within SimulationTool_Settings.json
- input Table adaption (C) within folder SimulationTool
---



## 5. Key Concepts

- **Trip chains** are generated using a probabilistic model (based on MiD 2018 data).
- **Plug‑in behavior** uses a probability model depending on SOC and mobility needs.
- **SOC simulation** uses constant consumption rates with variability.
- **Flexibility** is calculated as:
  - Difference between modified charging/ discharging and the “normal” load profile.
- **Two flexibility directions:**
  - **Positive**: EVs supply power (discharging)
  - **Negative**: EVs increase demand (charging)
- **Activation time** lets SOC be adjusted before the flex window, increasing available flexibility.

---

## 6. Output

The tool produces:
- SOC time series for all EVs
- Charging events and power curves
- Flexibility profiles (power over time)
- Aggregated flexibility (energy)
- Statistical distributions (quantiles, min, max, mean)

Visualizations include:
- Flex power curves for strategies & heuristics
- Statistical flexibility bands

---

## 7. Usage Example (High-Level)



```python
from test import start_tool

# 1. Start the simulation workflow
start_tool()

# 2. Run the model
run_model()

# 3. Calculate flexibility for a selected window
calculate_flexibility({
    "FLEX_START_TIME": 18,
    "FLEX_DURATION": 1,
    "SPONTANFLEX": False
})

# 4. Plot results
visualize_flexibility() 
```

## Example Run
Just run SimulationTool.py for example run. 
There are also further explanations for the usage of the simulation tool.
Parameters can be configured in file SimulationTool_Settings.py in folder SimulationTool.
Input tables can be adapted in csv files 'PopulateUsers', 'EVModels' abd 'ChargingStationTypes'
parameters and input tables are explained in detail in thesis


## Information on file structure
SimulationTool folder contains several example input tables for different scenarios, parameter file and most importantly
the file simulation.py defining the class SimulationTool and corresponding methods for the simulation tool 
main methods are start_tool, load_model, save_model, calculate_flexibility and visualize_flexibility
files for flexibility calculations are defined in folder flexibility_calc 
and files for simulation model are defined in folder simulation model

'analysis_methods' contains several methods used for charging profile validation and analysis of charging data
'trip_chain_validation.py' contains methods for running validations on trip chain model (mobility behavior)
'test.py' contains several tes methods for verification of simulation model and flexibility calculation
'SimulationTool.py', 'SimulationTool2.py', 'SimulationTool3.py' example runs of SimulationTool
'Simulationstool.pdf' german extensive explanation of Simulation tool
'requirements.txt' contains required installed packages for running simulation tool
'plugin_validation.py' contains methods for running validations on plugin model (plugin behavior)
'pl_calibration.py' contains methods of the plug in calibration
'model.pkl' example model 
'Installation.txt' describes how the python tool can be installed
'flex_validation' contains methods for validation of flexibility calculations
'SimulationTool' contains methods for Simulation tool computation
'simulation_model' contains method for simulation model computation
'helper_files' contains methods and files used in the implementation of the tool
'flexibility_calc' contains methods for flexibility calculation
'figures' is the folder, where imgages can be saved
'dataTC' contains all distributions used by the TC model


# Detailed explanation of Input Parameters & Tables

The simulation tool uses three categories of inputs:
- **Model Parameters** – control trip generation, plug‑in behavior, SOC simulation.
- **Flexibility Parameters** – define how flexibility is computed and visualized.
- **Input Tables** – define distributions and technical specifications (users, EV models, charging stations).

---

## 1) Model Parameters

### 1.1 Model Specifications
- **NUMBER_OF_DAYS** *(int)*  
  Number of consecutive simulation days. Enables multi‑day SOC evolution.  
  *Effect*: Affects the simulation model; indirectly affects flexibility results.

- **NUMBER_OF_RUNS** *(int)*  
  Number of independent simulation runs with newly sampled users. Supports variability and risk assessment.  
  *Effect*: Simulation model & statistical flexibility.

- **NUMBER_OF_USERS** *(int)*  
  Fleet size (1 user ↔ 1 EV). Controls total energy demand and flexibility potential.  
  *Effect*: Simulation model → flexibility.

- **START_DAY** *(str; “01”–“07”)*  
  Weekday of the first simulated day. Influences trip distributions and “end at home” likelihood.

---

### 1.2 Trip Generation Parameters
- **MINIMUM_SPEED** *(float, km/h)*  
  Minimum allowed trip speed. Prevents unrealistic travel times.  
  *Effect*: Simulation model.

- **MINIMUM_DISTANCE** *(float, km)*  
  Minimum trip distance. Ensures realistic consumption behavior.  
  *Effect*: Simulation model.

- **ENERGY_CONSUMPTION** *("constant" | "constant in range")*  
  Consumption model during trips: either a fixed average value or a normal distribution restricted by EV-specific min/max.  
  *Effect*: Influences SOC decay → affects flexibility 

---

### 1.3 Plug‑In Behavior Parameters
- **PLUG_IN_SIMPLE** *(bool)*  
  - `false`: use probabilistic plug‑in model based on SOC and mobility needs.  
  - `true`: plug in after every trip.  
  *Effect*: Strong influence on availability windows for flexibility.

- **PLUG_IN_ALPHA_HOME / WORK / PUBLIC** *(list[float])*  
  Activity rates controlling plug‑in probability per location.  
  One value = global constant, two values = user‑specific random draw.  
  Higher values → more frequent plug‑ins even at higher SOC.

- **MIN_SOC_PLUG_IN** *(int, %)*  
  At or below this SOC, the vehicle *always* plugs in. Ensures mobility security.

- **CHARGING_EVERY_DAY_AFTER_LAST_TRIP** *(0–1)*  
  Share of users who always charge after the last trip of the day.

- **WITHOUT_WORKING_STATION_ACCESS** *(0–1)*  
  Share of users who have **no access** to workplace charging.

**Plug‑In Model Principle**  
After each trip, a plug‑in probability is computed from:
- current SOC,
- required SOC for next trip,
- tolerance buffer,
- location (home, work, public).  
If SOC is too low, plug‑in happens deterministically.  
More plug‑in events → more charging windows → greater flexibility potential.

---

## 2) Flexibility Parameters

### 2.1 Flex Window & Activation
- **FLEX_START_TIME** *(hours)*  
  Start time of the flexibility window.

- **FLEX_DURATION** *(timedelta)*  
  Duration of the flexibility window.

- **SPONTANFLEX** *(bool)*  
  - `true`: no activation time (similar to frequency regulation markets).  
  - `false`: activation time may be used (preparation time before flexibility delievery).

- **FLEX_ACTIVATION_TIME** *(timedelta)*  
  Time before the flex window during which SOC can be adjusted.  
  Allows SOC pre-conditioning → increases available flexibility.

---

### 2.2 SOC Limits & Mobility Protection
- **MIN_SOC** *(%)*  
  Minimum SOC allowed during the flex window.  
  Limits discharging → reduces **positive flexibility**.

- **MAX_SOC** *(%)*  
  Maximum SOC allowed during flex calculations.  
  Limits charging → reduces **negative flexibility**.

- **SOC_TOL** *(%)*  
  Additional safety reserve in SOC demand estimation.  
  Larger tolerance → smaller flexibility margins.

---

### 2.3 EV Availability Filters
- **MIN_FLEX_TIME** *(minutes)*  
  Minimum time window after fulfilling mobility requirements in which flexibility can be delivered.

- **MIN_DELIEVERY_TIME** *(minutes)*  
  Minimum overlap of plug‑in time with the flex window.

- **V2G_AVAILABILITY** *(0–100 %)*  
  Share of plugged‑in EVs actually available for V2G.  
  Models technical and behavioral availability.

- **FLEX_AT_HOME** *(bool)*  
  If `true`, flexibility is only computed at home charging stations.

---

### 2.4 Selecting Days / Runs (Specific vs. Statistical Flexibility)
- **RISK** *(bool)*  
  - `true`: statistical flexibility across many days/runs (quantiles, min/max, mean).  
  - `false`: compute only one specific flexibility profile.

- **FLEX_AT_NUMBER_OF_DAY** *(int | −1)*  
  Select a specific simulation day or enable multiple days.

- **FLEX_AT_NUMBER_OF_RUN** *(int)*  
  Select a specific run (only for specific flexibility).

- **FLEX_AT_DAYTYPE** *(int | <0)*  
  Choose a weekday (1=Mon…7=Sun) or all (<0).

---

### 2.5 Charging Strategies & Flexibility Heuristics
- **CHARGING_STRATEGIES** *(list[str])*  
  Define the **baseline charging behavior** (normal load profile):
  - `"as soon as possible"`  charging as soon as the vehicle is plugged
  - `"as late as possible"`  charging starts at the latest time possible to reach the required min soc at the end of the plug-in time
  - `"as long as possible"`  charging start as soon as the vehicles is plugged, but not with full power. Charging power is chosen such that the whole plug-in period the vehicle is charged with a constant power

  These strongly influence the “no-flex” reference profile used to compute flexibility.

- **HEURISTICS** *(list[str])*  
  Define *how* the allowed energy is delivered during the flex window:
  - `"max at start"` – discharge/charge at max power early  
  - `"constant"` – distribute energy evenly across the window  

  Same energy → different flexibility power profiles.

---

### 2.6 Visualization Parameters
- **VIZ_CHARGING_STRATEGIES** *(list[int])* – selected charging strategies for visualization  
- **VIZ_HEURISTICS** *(int)* – selected heuristic  
- **VIZ_MODUS** *(0=positive flex | 1=negative flex)*  
- **VIZ_SHOW / VIZ_SAVE / VIZ_FILENAME** – control display and exporting of plots  

**Parameter Consistency Note**  
When loading a precomputed model, some parameters *must match* those used during model creation (e.g. `MIN_SOC`, `SOC_TOL`, `MIN_FLEX_TIME`, `V2G_AVAILABILITY`).

---

## 3) Input Tables

### 3.1 `PopulateUser` — User Attribute Distributions
Defines cumulative distributions for each user attribute category (values ≤ 1).  
Categories:
- RegionType  
- FederalState  
- HomogeneousGroup  
- MobilityGroup  
- StartDestination (AT_HOME / NOT_AT_HOME)  
- AgeGroup  
- EconomicStatus  

Possible Attributes:

| **Attribute Category** | **Possible Attributes** |
|------------------------|-------------------------|
| **Region Type**        | URBAN_METROPOLIS, URBAN_MAJOR_CITY, URBAN_CITY_AREA, URBAN_VILLAGE, RURAL_CENTRAL_CITY, RURAL_CITY_AREA, RURAL_VILLAGE, UNKNOWN |
| **Federal State**      | SCHLESWIG_HOLSTEIN, HAMBURG, LOWER_SAXONY, BREMEN, NORTH_RHINE_WESTPHALIA, HESSE, RHINELAND_PALATINATE, BADEN_WUERTTEMBERG, BAVARIA, SAARLAND, BERLIN, BRANDENBURG, MECKLENBURG_WESTERN_POMERANIA, SAXONY, THURINGIA, UNKNOWN |
| **Homogeneous Group**  | WORKING_PERSON, NON_WORKING_PERSON, STUDENT, UNKNOWN |
| **Mobility Group**     | CAR_USER, MULTI_MODAL, NON_CAR_USER, UNKNOWN |
| **Start Destination**  | AT_HOME, NOT_AT_HOME, UNKNOWN |
| **Age Group**          | UNDER_FORTY, FORTY_TO_SIXTY_FIVE, OVER_SIXTY_FIVE, UNKNOWN |
| **Economic Status**    | VERYLOW, LOW, MEDIUM, HIGH, VERYHIGH, UNKNOWN |

Example table:


| ID | Cumulative Values |
|----|-------------------|
| 1 | [0.115, 0.242, 0.536, 0.621, 0.674, 0.833, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1] |
| 2 | [0.034, 0.064, 0.143, 0.153, 0.308, 0.429, 0.466, 0.581, 0.912, 0.92, 0.925, 0.942, 0.962, 0.978, 0.985, 1, 1] |
| 3 | [0.628, 0.961, 0.999, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1] |
| 4 | [0.517, 0.823, 0.838, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1] |
| 5 | [0.179, 0.767, 0.998, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1] |
| 6 | [0.898, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1] |
| 7 | [0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1] |

For example in line 3, the cumulative distribution of the mobility group among all users in the simulation is given.
62.8% are working persons, 96.1-62.8 are non working, 99.9-96-1 are students


**Impact**  
Defines heterogeneity in mobility patterns → affects trip chaining → affects plug‑in timing and flexibility availability.

Default tables often use many `UNKNOWN` entries → generic population behavior.

---

### 3.2 `EVModels` — EV Technical Data & Status-Based Shares
Columns include:
- model name  
- battery capacity (kWh)  
- AC/DC charging power (kW)  
- average, min, max energy consumption (Wh/10km)  
- shares by EconomicStatus (columns sum to 1 per status group)

Example table:

## EV Models (from Input Table)

| ID | Model Name            | Battery (kWh) | AC Power (kW) | DC Power (kW) | Avg Cons. (Wh/10km) | Min Cons. | Max Cons. | VeryLow | Low  | Medium | High | VeryHigh | Unknown |
|----|------------------------|----------------|----------------|----------------|------------------------|-----------|-----------|----------|-------|---------|-------|-----------|---------|
| 1  | VW ID 5                | 77   | 11  | 143 | 17.9 | 11.6 | 23.7 | 0    | 0    | 0.02 | 0.2  | 0.15 | 0.1 |
| 2  | Hyundai Kona 64        | 64   | 11  | 77  | 16.4 | 11   | 23.3 | 0    | 0    | 0.125 | 0.15 | 0    | 0.1 |
| 3  | Hyundai Kona 39        | 39.2 | 7   | 44  | 16.3 | 10.6 | 23.1 | 0    | 0.04 | 0.125 | 0    | 0    | 0.05 |
| 4  | Fiat 500 Small         | 21.3 | 11  | 50  | 15.8 | 10.1 | 22.4 | 0    | 0.4  | 0.15  | 0    | 0    | 0.05 |
| 5  | Opel Corsa             | 46.3 | 7.4 | 101 | 15.7 | 10.5 | 22.6 | 0    | 0.05 | 0.25  | 0    | 0    | 0.1 |
| 6  | Renault Zoe            | 52   | 22  | 46  | 16.8 | 10.9 | 23.6 | 0    | 0.01 | 0.25  | 0    | 0    | 0.1 |
| 7  | Tesla Model 3          | 57.5 | 11  | 170 | 13.7 | 9.3  | 18.9 | 0    | 0    | 0     | 0.23 | 0.15 | 0.05 |
| 8  | Tesla Model 3 (large)  | 75   | 11  | 250 | 14.9 | 10.3 | 20.5 | 0    | 0    | 0     | 0.01 | 0.25 | 0.05 |
| 9  | Tesla Model Y          | 57.5 | 11  | 170 | 16.4 | 11.3 | 23   | 0    | 0    | 0     | 0.2  | 0.2  | 0.1 |
| 10 | Smart Fortwo           | 16.7 | 4.6 | 4.6 | 16.7 | 10.4 | 23.9 | 0.5  | 0.3  | 0     | 0    | 0    | 0.1 |
| 11 | VW UP                  | 32.2 | 7.2 | 37  | 15.8 | 10.3 | 22.3 | 0.5  | 0.2  | 0     | 0    | 0    | 0.1 |
| 12 | VW ID 3                | 58   | 11  | 124 | 16.6 | 11.2 | 23.2 | 0    | 0    | 0     | 0.01 | 0.25 | 0.1 |
| 13 | BMW i3                 | 37.9 | 11  | 49  | 16.1 | 10.5 | 23   | 0    | 0    | 0.08  | 0.2  | 0    | 0 |


**Impact**
- Determines SOC evolution and achievable charging/discharging power  
- Affects mobility demand (battery size vs trip length)  
- Defines variability between EVs in the fleet  

---

### 3.3 `ChargingStationTypes` — Station Power Levels & Shares
Columns:
- charging power (kW)  
- type (AC or DC)  
- shares for: home, work, public (each column sums to 1)

Example table:

| ID | Power (kW) | AC (1)/DC (0) | Home Share | Work Share | Public Share |
|----|------------|----------------|------------|------------|--------------|
| 0  | 3.7   | 1 | 0.3  | 0    | 0    |
| 1  | 7.2   | 1 | 0.5  | 0.05 | 0.05 |
| 2  | 11    | 1 | 0.15 | 0.75 | 0.05 |
| 3  | 22    | 1 | 0.05 | 0.2  | 0.3  |
| 4  | 50    | 0 | 0    | 0    | 0.1  |
| 5  | 80    | 0 | 0    | 0    | 0.1  |
| 6  | 100   | 0 | 0    | 0    | 0.15 |
| 7  | 150   | 0 | 0    | 0    | 0.2  |
| 8  | 350   | 0 | 0    | 0    | 0.05 |


**Impact**
- Defines charging performance at each location  
- Higher DC shares → shorter charging times, higher possible flexibility  
- Home-station distribution strongly affects `FLEX_AT_HOME` results  

---

## 4) Relationships & Practical Notes

- **Baseline vs. flexibility profile**  
  `CHARGING_STRATEGIES` define the baseline load profile.  
  Flexibility = difference between baseline and modified charging behavior within valid SOC & power limits.

- **Activation time increases flexibility**  
  `FLEX_ACTIVATION_TIME` enables SOC pre-conditioning → larger reachable energy margins.

- **Availability filters matter**  
  `MIN_FLEX_TIME`, `MIN_DELIEVERY_TIME`, `V2G_AVAILABILITY` determine how many EVs are eligible.

- **Mobility constraints must be met**  
  `MIN_SOC` protects mobility needs; `MAX_SOC` limits battery stress.

---

## 5) Quick Reference Table

| Area | Key Parameters | Primary Effect |
|------|----------------|----------------|
| Mobility / Plug‑In | `PLUG_IN_ALPHA_*`, `PLUG_IN_SIMPLE`, `MIN_SOC_PLUG_IN`, `WITHOUT_WORKING_STATION_ACCESS` | Determines number & timing of plug‑in windows |
| Energy / Power Limits | EV battery & `ChargingStationTypes` | Limits for SOC & charging/discharging power |
| Flexibility Limits | `MIN_SOC`, `MAX_SOC`, `SOC_TOL` | Bounds energy movement within window |
| Availability | `V2G_AVAILABILITY`, `MIN_FLEX_TIME`, `MIN_DELIEVERY_TIME`, `FLEX_AT_HOME` | Defines eligible EV pool |
| Profile Shape | `CHARGING_STRATEGIES`, `HEURISTICS`, `FLEX_ACTIVATION_TIME` | Baseline load and flexibility profile shape |
| Risk / Statistics | `NUMBER_OF_RUNS`, `NUMBER_OF_DAYS`, `RISK`, `FLEX_AT_*` | Statistical flexibility evaluation |

``









