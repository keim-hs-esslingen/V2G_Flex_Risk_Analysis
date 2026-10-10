import os
import json
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from collections import defaultdict
import re

SCENARIOS_PATH = "../scenarios/model_pl_normal_agegroup_4"
OUTPUT_PATH = "figures"

def parse_scenario_name(folder_name):
    """Versuche mehrere Namensmuster robust zu parsen.
    Erwartete Teile: spontan (True/False), act (z.B. 0_1> 0.1), duration (int), t (z.B. 1_00 -> 1.0)
    Falls Parsing nicht möglich, wird None zurückgegeben.
    """
    try:
        name = folder_name
        # 1) spontan: suche True/False nach 'spont' oder 'spontan'
        spont = None
        m = re.search(r'spont(?:an)?[_-]?(True|False)', name, flags=re.IGNORECASE)
        if m:
            spont = True if m.group(1).lower() == 'true' else False
        else:
            # fallback: suche 'spontTrue' oder 'spontFalse' ohne Trennzeichen
            m2 = re.search(r'spont(True|False)', name, flags=re.IGNORECASE)
            if m2:
                spont = True if m2.group(1).lower() == 'true' else False

        # 2) act: Zahlenfolge nach 'act' (kann '_' als dezimaltrenner haben)
        # Beispiele: act0, act0_1, act0_25, act1_00
        act = None
        # robustes Pattern: optionaler Separator nach 'act' und beliebige Ziffern/Unterstriche/Punkte
        m = re.search(r'act[_-]?([0-9_\.]+)', name)
        if m:
            # strip trailing underscores/dots (e.g. '0_1_' -> '0_1') then replace '_'->'.' and convert
            raw = m.group(1)
            raw = raw.rstrip('_.')
            act_str = raw.replace('_', '.')
            try:
                act = float(act_str)
            except:
                act = None

        # 3) duration: integer nach 'duration'
        duration = None
        m = re.search(r'duration[_-]?([0-9]+)', name)
        if m:
            try:
                duration = int(m.group(1))
            except:
                duration = None

        # 4) start time: tNN oder _tNN
        start_time = None
        # Suche das letzte Vorkommen von '_t' oder 't' gefolgt von Zahlen
        m = re.search(r'[_-]t([0-9_\.]+)$', name)
        if not m:
            m = re.search(r'_t([0-9_\.]+)', name)
        if not m:
            m = re.search(r't([0-9_\.]+)', name)
        if m:
            t_str = m.group(1).replace('_', '.')
            try:
                start_time = float(t_str)
            except:
                start_time = None

        # Wenn mindestens act und start_time oder duration vorhanden sind, geben wir ein dict zurück
        if spont is None and act is None and duration is None and start_time is None:
            return None

        return {
            "spontanflex": spont,
            "act_time": act,
            "duration": duration,
            "start_time": start_time,
            "folder_name": folder_name
        }
    except Exception:
        return None

def load_all_scenarios():
    """Load all scenarios with full statistics"""
    scenario_data = defaultdict(list)

    scenario_dirs = sorted([d for d in Path(SCENARIOS_PATH).iterdir() if d.is_dir()])
    print(f"Loading {len(scenario_dirs)} scenarios from {SCENARIOS_PATH}...")

    for scenario_dir in scenario_dirs:
        try:
            params = parse_scenario_name(scenario_dir.name)
            if not params:
                continue

            json_files = list(scenario_dir.glob("*_kpis.json"))
            if not json_files:
                continue

            with open(json_files[0], 'r', encoding='utf-8') as f:
                json_data = json.load(f)

            if not json_data.get("risk_combinations"):
                continue

            # Keep act_time as parsed (None if not present). Do not coerce None -> 0 here.
            scenario_key = (
                params["spontanflex"],
                params["act_time"],
                params["duration"],
                params["start_time"]
            )

            risk_combos = json_data["risk_combinations"]
            scenario_data[scenario_key].append((scenario_dir.name, risk_combos))

        except Exception as e:
            # defensiver Umgang mit fehlerhaften Dateien
            print(f"Fehler beim Verarbeiten von {scenario_dir}: {e}")
            continue

    data_by_scenario_and_acttime = {}  # {(S, M, H, act_time): [(start_time, mean, q25, q75, std, var), ...]}

    for scenario_key, duplicate_scenarios in scenario_data.items():
        spont, act, dur, start_time = scenario_key

        selected_scenario = None
        if len(duplicate_scenarios) > 1:
            for scenario_name, risk_combos in duplicate_scenarios:
                has_nonzero = any(
                    rc.get("quantiles_energy_kwh", {}).get("mean", 0) > 0 
                    for rc in risk_combos
                )
                if has_nonzero:
                    selected_scenario = (scenario_name, risk_combos)
                    break

            if selected_scenario is None:
                selected_scenario = duplicate_scenarios[0]
        else:
            selected_scenario = duplicate_scenarios[0]

        scenario_name, risk_combos = selected_scenario

        for risk_comb in risk_combos:
            quantiles = risk_comb.get("quantiles_energy_kwh", {})
            energy_mean = quantiles.get("mean")
            energy_q05 = quantiles.get("q05")
            energy_q25 = quantiles.get("q25")
            energy_q75 = quantiles.get("q75")
            energy_q95 = quantiles.get("q95")
            energy_min = quantiles.get("min")
            energy_max = quantiles.get("max")
            energy_std = quantiles.get("std")
            energy_var = quantiles.get("var")

            strat = risk_comb["combination"].get("strat_pos")
            modus = risk_comb["combination"].get("modus_pos")
            heur = risk_comb["combination"].get("heuristic_pos")

            # NEW: show only heuristic_pos == 1 (hide all h0)
            if heur is None or heur == 0:
                continue

            # Skip S0_M0_H0 (already covered by heur==0 check, but keep for clarity)
            if strat == 0 and modus == 0 and heur == 0:
                continue

            # Skip 0-energy EXCEPT for S0_M0_H1
            if energy_mean is None or (energy_mean == 0 and not (strat == 0 and modus == 0 and heur == 1)):
                continue

            # For spontTrue with duration=15, treat as activation_time=0
            if spont == True and dur == 15:
                act_for_plot = 0.0
            else:
                # use parsed act (may be None) — only convert to numeric if present
                act_for_plot = act if act is not None else None

            # Use act_for_plot as-is in the combo key (rounded if numeric), keep None distinct
            combo_act_key = round(act_for_plot, 4) if isinstance(act_for_plot, (int, float)) else None

            combo_key = (strat, modus, heur, combo_act_key)

            if combo_key not in data_by_scenario_and_acttime:
                data_by_scenario_and_acttime[combo_key] = []

            data_by_scenario_and_acttime[combo_key].append({
                "start_time": start_time,
                "mean": energy_mean,
                "q05": energy_q05 if energy_q05 is not None else energy_mean,
                "q25": energy_q25 if energy_q25 is not None else energy_mean,
                "q75": energy_q75 if energy_q75 is not None else energy_mean,
                "q95": energy_q95 if energy_q95 is not None else energy_mean,
                "min": energy_min if energy_min is not None else energy_mean,
                "max": energy_max if energy_max is not None else energy_mean,
                "std": energy_std if energy_std is not None else 0,
                "var": energy_var if energy_var is not None else 0
            })

    print(f"Loaded data for energy values")
    return data_by_scenario_and_acttime

def create_scenarios_plot(data):
    """Create subplots for each scenario showing activation times
    Layout: 2 columns (negative, positive flexibility direction), rows for charging strategies
    """

    # Get all unique (S, M, H) combinations
    all_combos = []
    for combo_key in data.keys():
        s, m, h, act = combo_key
        smh = (s, m, h)
        if smh not in all_combos:
            all_combos.append(smh)

    all_combos = sorted(all_combos)
    print(f"Found {len(all_combos)} scenarios")

    # Get all available activation times
    all_act_times = sorted(set(combo_key[3] for combo_key in data.keys()))
    act_times = [at for at in all_act_times if at is not None]
    act_times = sorted(act_times)
    excluded_act_times = {1.0, 0.5, 0.12}
    act_times = [at for at in act_times if at not in excluded_act_times]
    act_times_minutes = [round(at * 60) for at in act_times]
    print(f"Activation times: {act_times_minutes} minutes")

    # Get unique strategies and modes
    s_values = sorted(set(s for s, _, _ in all_combos))  # Charging strategies -> rows
    m_values = sorted(set(m for _, m, _ in all_combos))  # Modes (0=negative, 1=positive) -> columns

    # Layout: rows = strategies, columns = 2 (negative, positive)
    n_rows = len(s_values)
    n_cols = len(m_values)  # Should be 2

    fig, axes = plt.subplots(
        n_rows,
        n_cols,
        figsize=(9 * n_cols, 8 * n_rows),
        squeeze=False
    )

    s_map = {s: i for i, s in enumerate(s_values)}  # Strategy -> row
    m_map = {m: i for i, m in enumerate(m_values)}  # Mode -> column

    # Colors for activation times
    if len(act_times) > 0:
        colors_act = plt.cm.cool(np.linspace(0, 1, len(act_times)))
        color_map_act = {at: colors_act[i] for i, at in enumerate(act_times)}
    else:
        color_map_act = {}

    # Collect all values for y-axis scaling
    all_displayed_energy = []
    all_displayed_var = []
    
    for s, m, h in all_combos:
        for act_time in act_times:
            combo_key = (s, m, h, round(act_time, 4))
            if combo_key not in data:
                continue
            values = data[combo_key]
            for val_dict in values:
                all_displayed_energy.extend([val_dict["mean"], val_dict["q25"], val_dict["q75"]])
                if val_dict["var"] > 0:
                    all_displayed_var.append(val_dict["var"])

    if all_displayed_energy:
        y_min = min(all_displayed_energy)
        y_max = max(all_displayed_energy)
    else:
        y_min = 0
        y_max = 100

    if all_displayed_var:
        var_min = 0
        var_max = max(all_displayed_var)
    else:
        var_min = 0
        var_max = 100

    # Plotting
    ax_first = None
    ax2_first = None
    
    ch_map = {0: "ASAP", 1: "ALaAP", 2: "ALoAP"}
    
    for plot_idx, (s, m, h) in enumerate(all_combos):
        row = s_map[s]  # Strategy -> row
        col = m_map[m]  # Mode (0=negative, 1=positive) -> column

        ax = axes[row, col]
        ax2 = ax.twinx()

        if ax_first is None:
            ax_first = ax
            ax2_first = ax2

        for act_time in act_times:
            combo_key = (s, m, h, round(act_time, 4))

            if combo_key not in data:
                continue

            values = data[combo_key]
            values = sorted(values, key=lambda x: x["start_time"])

            start_times = [v["start_time"] for v in values]
            means = [v["mean"] for v in values]
            q25s = [v["q25"] for v in values]
            q75s = [v["q75"] for v in values]
            vars_list = [v["var"] for v in values]

            color = color_map_act[act_time]
            act_minutes = round(act_time * 60)

            ax.fill_between(start_times, q25s, q75s, 
                            color=color, alpha=0.25, label=f"Act={act_minutes}min (Q25-Q75)")

            ax.plot(start_times, means, marker='o', label=f"Act={act_minutes}min (mean)",
                   color=color, linestyle='-', linewidth=3.0, markersize=7, alpha=0.9)

            ax2.plot(start_times, vars_list, color=color, linestyle=':', 
                    linewidth=2.0, alpha=0.5, label=f"Act={act_minutes}min (var)")

        # No title in subplot
        ax.set_title("", fontsize=1)
        
        ax.set_xlabel("Time of day [h]", fontsize=32)
        ax.tick_params(axis='x', labelsize=28)
        ax.tick_params(axis='y', labelsize=28)
        ax2.tick_params(axis='y', labelsize=28, labelcolor='gray')

        # Left Y-axis only in first column
        if col == 0:
            ax.set_ylabel("AvgEn (kWh)", fontsize=32)
        else:
            ax.set_ylabel("")

        # Right Y-axis only in last column
        if col == n_cols - 1:
            ax2.set_ylabel("Variance (Var)", fontsize=32, color='gray')
        else:
            ax2.set_ylabel("")

        ax.set_ylim(y_min, y_max)
        ax2.set_ylim(var_min, var_max)
        ax.grid(True, alpha=0.3)

    # Add row titles for Charging Strategy (on the left side)
    for row_idx, s in enumerate(s_values):
        ch_str = ch_map.get(s, f"S{s}")
        ch_str_lines = f"Charging Strategy:{ch_str}"
        # Position at the vertical middle of each subplot row
        y_pos = 0.935 - (row_idx + 0.5) * ((0.92 - 0.10) / n_rows)
        fig.text(0.03, y_pos, ch_str_lines, 
                fontsize=30,  rotation=90, va='center', ha='center')

    # Add column titles for Flexibility Direction (on the top)
    for col_idx, m in enumerate(m_values):
        r_str = "Negative" if m == 0 else "Positive"
        direction_str = f"Flexibility\nDirection: {r_str}"
        # Position column title in the middle of each subplot column
        subplot_region_width = 0.93 - 0.12
        subplot_width = subplot_region_width / n_cols
        x_pos = 0.12 + (col_idx + 0.5) * subplot_width
        if col_idx > 0:
            x_pos += 0.03  # Slight shift for right column
        fig.text(x_pos, 0.94, direction_str, fontsize=30,  ha='center')

    # Create legend with 3 columns
    lines1, labels1 = ax_first.get_legend_handles_labels()
    lines2, labels2 = ax2_first.get_legend_handles_labels()
    
    fig.legend(lines1 + lines2, labels1 + labels2, fontsize=28, loc='lower center',
              ncol=3, bbox_to_anchor=(0.5, 0.02))

    plt.subplots_adjust(left=0.12, right=0.93, top=0.93, bottom=0.15, hspace=0.25, wspace=0.25)
    os.makedirs(OUTPUT_PATH, exist_ok=True)
    plt.savefig(f"{OUTPUT_PATH}/scenarios_by_activation_time_Figure7.png", dpi=300, bbox_inches='tight')
    print(f"\nSaved: scenarios_by_activation_time.png")
    plt.close()

    # Print summary
    print(f"\nPlot info:")
    print(f"  - Layout: {n_rows} rows (charging strategies) × {n_cols} cols (flexibility directions)")
    print(f"  - Per subplot: {len(act_times)} activation times")
    print(f"  - Activation times shown as different colors")
    print(f"  - Left Y-axis: Energy (kWh) with Q25-Q75 bands (mean)")
    print(f"  - Right Y-axis: Variance (var)")

if __name__ == "__main__":
    os.makedirs(OUTPUT_PATH, exist_ok=True)

    print("Loading scenarios...")
    data = load_all_scenarios()

    print("\nCreating scenario-based plots with activation time variations...")
    create_scenarios_plot(data)

    print("\nDone!")
