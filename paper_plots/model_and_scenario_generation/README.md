
# Model and Scenario Generation

The scripts in this folder generate the underlying simulation models and scenarios used for the
paper figures. They have already been run; the full, raw simulation models (`.pkl` files, several
GB in total) are **not** kept in this repository to save space. Only the data required to reproduce
the paper figures (derived statistics, KPIs, JSON summaries, plots) is still included. Re-running a
script below regenerates its `.pkl` models from scratch if they are missing. (With slightly different results due to the stochastic nature of the simulation.)


## plugin_validation2.py / plug-in_analysis.py → `plugin/`

`plugin_validation2.py` simulates one model per plug-in-behavior scenario (e.g. `D4_CH1`,
`B4_SOC_AFTER30_SOC_PLUG40`, ...) and originally saved both `model_<scenario>.pkl` and
`VehicleList_<scenario>.pkl` per scenario folder under `plugin/`. `plug-in_analysis.py` reads the
`VehicleList_<scenario>.pkl` files and computes the histogram error (`histogram_errors.json`) against
real-world charging data for each scenario.

Used for: **Figure 6** (`NormalizedHistogramms_plugin(Figure6).py` picks the scenario with the lowest
average RMSE from `histogram_errors.json` and plots it).

Kept in the repo: `histogram_errors.json`, `hist_*.png`, `stats_*.json`, `Settings_*.json` per scenario.
Removed: `model_<scenario>.pkl` and `VehicleList_<scenario>.pkl` for all scenarios. The
`VehicleList_B4_SOC_AFTER30_SOC_PLUG40.pkl` of the best-scoring scenario (needed for Figure 6) exceeds
GitHub's 100 MB file size limit and has therefore also been removed; it is available at
[LINK EINFUEGEN] and must be copied back into `plugin/B4_SOC_AFTER30_SOC_PLUG40/` before reproducing
Figure 6. `plugin_validation2.py` can be re-run to regenerate all models and vehicle lists if needed.

Similarly, `NormalizedHistogramms_plugin(Figure6).py` and `plug-in_analysis.py` read real-world
comparison data from `dataCharging/`. The file `dataCharging/alreadyLoaded/UK_charging_home_whole.pkl`
(also needed for Figure 12) exceeds the 100 MB limit and was removed together with
`dataCharging/modelData/VehicleList2.pkl` and
`dataCharging/Charging_data_for_tests/electric-chargepoint-analysis-2017-raw-domestics-data.csv`.
All three are available at [LINK EINFUEGEN] and must be copied back into their original locations
before running the affected scripts/figures.

## pl_model_variation.py → `pl_variations/`

Computes a set of base models (varying `plugin_alpha`, home/work) and, for each, derives time-of-day
sensitivity and trip/plug-in statistics.

Used for: **Figure 10/11** (`pl_model_time_analysis_Figure10_11.py`), which only reads the derived
JSON files in `start_time_sensitivity/` and `trip_plugin_statistics/`.

Kept in the repo: `start_time_sensitivity/`, `trip_plugin_statistics/`, `charging_specs/`, `ev_specs/`.
Removed: `pl_variations/models/*.pkl` (the base models themselves are not needed to reproduce the
figures, only as a cache to avoid re-simulating when this script is re-run).

## generate_parameter_variations.py → `parameter_variations2/`

Computes base models for parameter sweeps (`num_users`, `plugin_alpha`, `power`, `battery_sizes`) and
derives flexibility scenarios and KPIs from them.

Used for: **Figure 16/17** (`parameter_variation_analysis_Figure16_17.py`), which only reads the
derived data in `flex_scenarios/` and `model_flexibilities/`.

Kept in the repo: `flex_scenarios/`, `model_flexibilities/`, `analysis_plots/`, `charging_specs/`,
`ev_specs/`. Removed: `parameter_variations2/models/*.pkl` (same reasoning as above).

## SimulationTool_main_*.py → `models_final/` and `scenarios_final/`

`SimulationTool_main_activationtime_scenarios.py`, `SimulationTool_main_populateUsers_tabelle.py` and
`SimulationTool_main_selected_mobility.py` generate one model per population-table variant
(`model_pl_normal_<group>.pkl`, stored in `models_final/`) and compute scenarios from them into
`scenarios_final/`.

Used for: **Figure 8, 9, 13, 14, 15** (read `scenarios_final/`).

`pl_model_daytime_daytype_analysis.py` loads existing `models_final/model_pl_normal_<group>.pkl`
models directly and computes flexibility for different start times/daytypes into
`scenarios_final/pl_model_daytime_daytype_analysis/`.

Used for: **Figure 18** (`wochentag_plot_FIgure18.py`).

Unlike `plugin/`, `pl_variations/` and `parameter_variations2/`, the `models_final/*.pkl` files are
**not** just a recompute cache — they are loaded directly by `plot_model_mobility_influences(Figure12).py`
(**Figure 12**) and by `pl_model_daytime_daytype_analysis.py` (**Figure 18**).

Due to their size, the `models_final/*.pkl` files have been removed from this repository and are
available at [LINK EINFUEGEN]. **Figure 12 and Figure 18 cannot be reproduced until these files are
copied back into `models_final/`.**

