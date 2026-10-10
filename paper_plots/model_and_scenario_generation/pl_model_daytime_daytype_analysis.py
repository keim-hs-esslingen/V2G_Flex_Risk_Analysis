#flexibility calculation for investigation of daytype dependancy (for figure 18).

"""
PL Model Flexibility Analysis - Time of Day and Weekday
========================================================
Load model from models_final and calculate flexibility for:
- Different start times: 1.5, 8, 11.5, 13.5, 16.5, 18.5, 20, 22
- Different daytypes: 1=Monday, 2=Tuesday, ..., 7=Sunday
- Fixed duration: 15 minutes
- Spontanflex: False
- Location: Home
"""

import os
import datetime
from pathlib import Path
from test import start_tool

# Change to parent directory (project root) so that paths work correctly
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# =====================================================================
# CONFIGURATION
# =====================================================================

# List of model groups to analyze
MODEL_GROUPS = [
    "agegroup_4",
    "agegroup_1",
    "econstatus_1",
    "econstatus_5",
    "regiontype_5",
    "agegroup_1",
    "mobilitygroup_3",
    "mobilitygroup_1",
    "homogroup_2",
    "homogroup_1",
    "agegroup_3",

]

OUTPUT_BASE_DIR = "scenarios_final/pl_model_daytime_daytype_analysis"

START_TIMES = [1,4,7,10,13,16,19,22]#[1, 8, 11.5, 13.5, 16.5, 18.5, 20, 22]  # in hours
DAYTYPES = [1, 2, 3, 4, 5, 6, 7]  # 1=Monday to 7=Sunday

FLEX_DURATION = 15  # minutes
SPONTANFLEX = False
FLEX_PLACE = "Home"

# =====================================================================
# HELPER FUNCTIONS
# =====================================================================

def hours_to_timedelta(hours):
    """Convert decimal hours to datetime.timedelta"""
    hours_int = int(hours)
    minutes_int = int((hours - hours_int) * 60)
    return datetime.timedelta(hours=hours_int, minutes=minutes_int)


def daytype_name(daytype):
    """Get day name from daytype (1=Monday, 2=Tuesday, etc.)"""
    names = {1: "Monday", 2: "Tuesday", 3: "Wednesday", 4: "Thursday",
             5: "Friday", 6: "Saturday", 7: "Sunday"}
    return names.get(daytype, f"Day{daytype}")


# =====================================================================
# MAIN EXECUTION
# =====================================================================

def main():
    print("\n" + "="*80)
    print("  PL MODEL FLEXIBILITY ANALYSIS - TIME OF DAY & WEEKDAY")
    print("="*80)
    print(f"  Processing {len(MODEL_GROUPS)} model groups:")
    for group in MODEL_GROUPS:
        print(f"    - {group}")
    print("="*80)
    
    # Create output directory
    os.makedirs(OUTPUT_BASE_DIR, exist_ok=True)
    
    # Load simulation tool once
    simulation_tool = start_tool()
    
    total_scenario_count = 0
    
    # Iterate through all model groups
    for model_group in MODEL_GROUPS:
        model_path = f"models_final/model_pl_normal_{model_group}"
        
        print(f"\n{'='*80}")
        print(f"  PROCESSING MODEL GROUP: {model_group}")
        print(f"  Model: {model_path}")
        print(f"{'='*80}")
        
        # Load model
        model_file = f"{model_path}.pkl"
        if not os.path.exists(model_file):
            print(f"✗ Model file not found: {model_file}")
            continue
        
        try:
            simulation_tool.load_model(filename=model_path)
            print(f"✓ Model loaded successfully")
        except Exception as e:
            print(f"✗ Error loading model: {e}")
            continue
        
        # Iterate through all combinations for this model group
        group_scenario_count = 0
        
        for daytype in DAYTYPES:
            day_name = daytype_name(daytype)
            print(f"\n{'─'*80}")
            print(f"Processing daytype {daytype} ({day_name})")
            print(f"{'─'*80}")
            
            for start_time_hours in START_TIMES:
                group_scenario_count += 1
                total_scenario_count += 1
                
                # Create scenario name
                scenario_name = f"pl_{model_group}_daytype{daytype}_{day_name.lower()}_starttime{start_time_hours:.1f}h".replace(".", "_")
                
                # Convert hours to timedelta
                flex_start_time = hours_to_timedelta(start_time_hours)
                flex_duration = datetime.timedelta(minutes=FLEX_DURATION)
                
                # Create flex specifications
                flex_spec = {
                    "flexibility_specifications": {
                        "SPONTANFLEX": SPONTANFLEX,
                        "RISK": 1,
                        "FLEX_START_TIME": flex_start_time,
                        "FLEX_DURATION": flex_duration,
                        "FLEX_ACTIVATION_TIME": datetime.timedelta(0),
                        "FLEX_PLACE": FLEX_PLACE,
                        "FLEX_AT_NUMBER_OF_DAY": -1,
                        "FLEX_AT_NUMBER_OF_RUN": -1,
                        "FLEX_AT_DAYTYPE": daytype,
                    }
                }
                
                print(f"  [{total_scenario_count:3d}] Scenario: {scenario_name}")
                print(f"        Start time: {start_time_hours}h | Daytype: {daytype} ({day_name})")
                
                try:
                    # Calculate flexibility
                    simulation_tool.calculate_flexibility(flex_specifications=flex_spec)
                    
                    # Create scenario directory
                    scenario_dir = os.path.join(OUTPUT_BASE_DIR, scenario_name)
                    os.makedirs(scenario_dir, exist_ok=True)
                    
                    # Save KPIs as JSON
                    kpis_filename = os.path.join(scenario_dir, f"{scenario_name}_kpis")
                    simulation_tool.save_flex_kpis_as_json(filename=kpis_filename)
                    
                    print(f"        ✓ Saved to: {kpis_filename}.json")
                    
                except Exception as e:
                    print(f"        ✗ Error: {e}")
                    import traceback
                    traceback.print_exc()
        
        print(f"\n{'─'*80}")
        print(f"Model group '{model_group}' completed: {group_scenario_count} scenarios")
        print(f"{'─'*80}")
    
    print(f"\n{'='*80}")
    print(f"  COMPLETED")
    print(f"  Total scenarios processed: {total_scenario_count}")
    print(f"  Output directory: {OUTPUT_BASE_DIR}")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    main()
