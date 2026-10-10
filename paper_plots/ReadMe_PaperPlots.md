## Reproducing the Analyses

Most scripts listed below have already been executed and the corresponding models and scenarios are included in this repository. Therefore, rerunning them is generally not required.

Please note that some scripts were originally executed from the project root directory (`v2g_simulationtool`). Depending on the current folder structure, individual scripts may require path adjustments or relocation to the project root before execution.

## Scripts Used for the Paper

The analysis and plotting scripts are generally named according to the corresponding figures presented in the paper. Several scripts are responsible for generating models and scenarios, while others perform evaluations and create the final figures.

### Parameter Variation

- **generation_parameter_variations.py**  
  Generates the parameter variation scenarios used in Figures 16 and 17. The script orchestrates model generation, flexibility calculations, and the systematic storage of results in the `parameter_variations2` folder.

### Day-Type Dependency Analysis

- **pl_model_daytime_daytype_analysis.py**  
  Performs the day-type dependency analysis. The script executes the required flexibility calculations and stores the results in a structured manner.

### Plug-in Activity Variation

- **pl_model_variation.py**  
  Generates the plug-in activity variation scenarios investigated in Figures 10 and 11. The script orchestrates model generation, flexibility calculations, and result storage in the `pl_variations` folder.

### Plug-in Configuration

- **plugin_validation2.py**  
  Generates the plug-in configuration scenarios presented in Table 4 and stores the resulting models in the `plugin` folder.

- **plugin_analysis.py**  
  Analyzes the plug-in configuration scenarios from Table 4 by calculating performance metrics and ranking the scenarios according to these metrics.

### Main Scenario Generation

- **SimulationTool_main_populateUsers_tabelle.py**  
  Generates the models used in several sections and figures of the paper. Generated models are stored in `models_final`, while the corresponding flexibility scenarios are stored in `scenarios_final`. The script coordinates model generation, flexibility calculations, and result management.

### Activation Time Analysis

- **SimulationTool_main_activiatontime_scenarios.py**  
  Performs the flexibility calculations for the activation-time scenarios presented in Figure 7.

### Mobility Scenario Analysis

- **SimulationTool_main_selected_mobility.py**  
  Performs the flexibility calculations used for Figure 13. With adjusted parameters, the script was also used for the analysis of Scenario B.
