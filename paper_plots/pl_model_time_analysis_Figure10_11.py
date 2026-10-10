"""
PL Model Variation - Time of Day Analysis
==========================================
For strat_pos=1, heuristic_pos=1, modus_pos=1:
- Plot mean_energy by time of day (1, 3, 5, ..., 23 hours)
- Separate subplots for Work and Home
- Different lines for different plugin_alpha values
"""

import json
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import re

BASE_DIR = Path("../pl_variations/start_time_sensitivity")
STATS_DIR = Path("../pl_variations/trip_plugin_statistics")

TARGET_COMB = {"strat_pos": 1, "heuristic_pos": 1, "modus_pos": 1}

# =====================================================================
# HELPER FUNCTIONS
# =====================================================================

def extract_mean_energy(json_data):
    """Extract mean energy for the target risk combination"""
    for rc in json_data["risk_combinations"]:
        if rc["combination"] == TARGET_COMB:
            return rc["quantiles_energy_kwh"]["mean"]
    return None


def extract_time_from_filename(filename):
    """Extract hour from filename like 'starttime_1_home_...' or 'starttime_13_home_...'"""
    match = re.search(r'starttime_(\d+)_', filename)
    if match:
        return int(match.group(1))
    return None


def extract_location_from_filename(filename):
    """Extract location (Home or Work) from filename like 'starttime_1_home_...' or 'starttime_1_work_...'"""
    if '_home_' in filename:
        return 'Home'
    elif '_work_' in filename:
        return 'Work'
    return None


def extract_plugin_alpha_from_folder(folder_name):
    """Extract plugin_alpha value from folder name like 'model_alpha0_1_home' or 'model_alpha0_1_work'
    Special case: 'model_plugin_alpha_simple_home/work' returns 'simple' """
    
    # Check for simple models
    if 'simple' in folder_name:
        return 'simple'
    
    # Format: model_alpha{value}_{location}
    match = re.search(r'model_alpha([\d_]+?)_(?:home|work)$', folder_name)
    if match:
        val_str = match.group(1).replace("_", ".")
        try:
            return float(val_str)
        except:
            pass
    return None


def print_statistics_summary(df_energy):
    """
    Gebe Tabelle mit:
    - Ratios (charging/trips: total, home, work, public)
    - Max mean_energy (normalisiert auf simple_Home/simple_Work oder alpha=10 als Fallback)
    """
    print("\n" + "=" * 160)
    print("  ENERGY & CHARGING STATISTICS BY SCENARIO")
    print("=" * 160)
    
    # Aggregiere mean_energy pro Szenario (plugin_alpha + location)
    energy_by_scenario = {}
    max_energy_home = 0
    max_energy_work = 0
    
    if not df_energy.empty:
        for (alpha, location), group in df_energy.groupby(['plugin_alpha', 'location']):
            max_energy = group['mean_energy'].max()
            scenario_key = f"alpha_{alpha}_{location}"
            energy_by_scenario[scenario_key] = max_energy
            
            # Finde max pro Location
            if location == 'Home':
                if max_energy > max_energy_home:
                    max_energy_home = max_energy
            else:  # Work
                if max_energy > max_energy_work:
                    max_energy_work = max_energy
    
    # Lade Ratios aus Statistics JSONs
    ratios_by_scenario = {}
    if STATS_DIR.exists():
        for json_file in sorted(STATS_DIR.glob("*_statistics.json")):
            try:
                with open(json_file) as f:
                    data = json.load(f)
                
                stats = data.get("statistics", {})
                
                # Extrahiere alpha und location aus Dateinamen
                filename = json_file.stem  # z.B. "model_alpha0_1_home_statistics"
                
                # Konstruiere scenario_key
                if 'simple' in filename:
                    alpha_val = 'simple'
                else:
                    # Extrahiere alpha value: model_alpha0_1_home -> 0.1, model_alpha10_0_home -> 10.0
                    match = re.search(r'model_alpha([\d_]+?)_(home|work)', filename)
                    if match:
                        alpha_str = match.group(1).replace('_', '.')
                        alpha_val = float(alpha_str)
                    else:
                        continue
                
                # Location aus Dateinamen
                if '_home' in filename:
                    location = 'Home'
                elif '_work' in filename:
                    location = 'Work'
                else:
                    continue
                
                scenario_key = f"alpha_{alpha_val}_{location}"
                ratios_by_scenario[scenario_key] = {
                    "total": stats.get("avg_ratio_charging_to_trips", 0),
                    "home": stats.get("avg_ratio_home_charging_to_trips", 0),
                    "work": stats.get("avg_ratio_work_charging_to_trips", 0),
                    "public": stats.get("avg_ratio_public_charging_to_trips", 0),
                }
            except Exception as e:
                print(f"  ERROR reading {json_file}: {e}")
    
    # Sortiere Szenarien mit 'simple' am Ende
    sorted_scenarios = sorted(energy_by_scenario.keys(), 
                              key=lambda x: (('simple' in x), x))
    
    # Ausgabe
    print(f"\n{'Scenario':<28} {'Ratios (Ch/Trips)':<50} {'Energy':<35}")
    print(f"{'':28} {'Total':<10} {'Home':<10} {'Work':<10} {'Public':<10} {'Max (kWh)':<12} {'vs Ref %':<12}")
    print("-" * 160)
    
    for scenario_key in sorted_scenarios:
        max_energy = energy_by_scenario[scenario_key]
        
        # Bestimme Referenzwert je nach Location
        if 'Home' in scenario_key:
            ref_energy = max_energy_home
            ref_label = "simple_Home" if energy_by_scenario.get("alpha_simple_Home") else "alpha_10.0_Home"
        else:  # Work
            ref_energy = max_energy_work
            ref_label = "simple_Work" if energy_by_scenario.get("alpha_simple_Work") else "alpha_10.0_Work"
        
        normalized = (max_energy / ref_energy * 100) if ref_energy > 0 else 0
        
        # Hole Ratios
        ratios = ratios_by_scenario.get(scenario_key, {"total": 0, "home": 0, "work": 0, "public": 0})
        ratio_total = ratios.get("total", 0)
        ratio_home = ratios.get("home", 0)
        ratio_work = ratios.get("work", 0)
        ratio_public = ratios.get("public", 0)
        
        print(f"{scenario_key:<28} {ratio_total:<10.4f} {ratio_home:<10.4f} {ratio_work:<10.4f} {ratio_public:<10.4f} {max_energy:<12.2f} {normalized:<12.1f}%")
    
    # Reference summary
    home_ref = "simple_Home" if energy_by_scenario.get("alpha_simple_Home") else "alpha_10.0_Home"
    work_ref = "simple_Work" if energy_by_scenario.get("alpha_simple_Work") else "alpha_10.0_Work"
    print(f"\nReference: Home={home_ref} ({max_energy_home:.2f} kWh), Work={work_ref} ({max_energy_work:.2f} kWh)")
    print("=" * 160 + "\n")


def build_statistics_df(df_energy):
    """Return a DataFrame with max_energy + ratios per (alpha, location)."""
    energy_by_scenario = {}
    if not df_energy.empty:
        for (alpha, location), group in df_energy.groupby(['plugin_alpha', 'location']):
            energy_by_scenario[f"alpha_{alpha}_{location}"] = group['mean_energy'].max()

    ratios_by_scenario = {}
    if STATS_DIR.exists():
        for json_file in sorted(STATS_DIR.glob("*_statistics.json")):
            try:
                with open(json_file) as f:
                    data = json.load(f)
                stats = data.get("statistics", {})
                filename = json_file.stem
                if 'simple' in filename:
                    alpha_val = 'simple'
                else:
                    match = re.search(r'model_alpha([\d_]+?)_(home|work)', filename)
                    if not match:
                        continue
                    alpha_val = float(match.group(1).replace('_', '.'))
                location = 'Home' if '_home' in filename else ('Work' if '_work' in filename else None)
                if location is None:
                    continue
                key = f"alpha_{alpha_val}_{location}"
                ratios_by_scenario[key] = {
                    "total":  stats.get("avg_ratio_charging_to_trips", 0),
                    "home":   stats.get("avg_ratio_home_charging_to_trips", 0),
                    "work":   stats.get("avg_ratio_work_charging_to_trips", 0),
                    "public": stats.get("avg_ratio_public_charging_to_trips", 0),
                }
            except Exception as e:
                print(f"  ERROR reading {json_file}: {e}")

    all_keys = set(energy_by_scenario) | set(ratios_by_scenario)
    records = []
    for key in all_keys:
        parts = key.split("_")          # alpha_{val}_{Loc}
        location = parts[-1]
        alpha_raw = "_".join(parts[1:-1])
        try:
            alpha_num = float(alpha_raw)
        except ValueError:
            alpha_num = None            # 'simple'

        r = ratios_by_scenario.get(key, {})
        records.append({
            "scenario_key": key,
            "alpha":        alpha_raw,
            "alpha_num":    alpha_num,
            "location":     location,
            "max_energy":   energy_by_scenario.get(key, None),
            "ratio_total":  r.get("total",  0),
            "ratio_home":   r.get("home",   0),
            "ratio_work":   r.get("work",   0),
            "ratio_public": r.get("public", 0),
        })

    return pd.DataFrame(records)


def plot_statistics_summary(df_energy, plots_dir):
    """
    Two subplots (Home | Work).
    Primary y-axis  : max mean_energy (kWh)  – bar
    Secondary y-axis: plugin/trip ratios (total, home, work) – lines
    X-axis          : alpha values (numeric only, 'simple' excluded)
    """
    stat_df = build_statistics_df(df_energy)

    # numeric alphas sorted, then 'simple' appended at the right
    numeric_df = stat_df[stat_df["alpha_num"].notna()].copy().sort_values("alpha_num")
    simple_df  = stat_df[stat_df["alpha_num"].isna()].copy()
    stat_df = pd.concat([numeric_df, simple_df], ignore_index=True)

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    ratio_colors = {"ratio_total": "black", "ratio_home": "steelblue", "ratio_work": "darkorange", "ratio_public": "green"}
    ratio_labels = {"ratio_total": "Ratio total", "ratio_home": "Ratio home", "ratio_work": "Ratio work", "ratio_public": "Ratio public"}

    for ax1, location in zip(axes, ["Home", "Work"]):
        sub = stat_df[stat_df["location"] == location].copy()
        if sub.empty:
            ax1.set_title(location)
            continue

        x_idx = list(range(len(sub)))
        x_labels = ["100% plugin" if a == "simple" else str(v)
                    for a, v in zip(sub["alpha"], sub["alpha_num"])]

        # ---- primary: energy bar ----
        ax1.bar(x_idx, sub["max_energy"].values, color="steelblue", alpha=0.35,
                label="Max energy (kWh)", zorder=2)
        ax1.set_ylabel("Max AvgEn of Day (kWh)", fontsize=20)
        ax1.set_xlabel("Plugin Activity (α)", fontsize=20)
        ax1.set_xticks(list(x_idx))
        ax1.set_xticklabels(x_labels, rotation=45, ha="right", fontsize=20)
        ax1.set_title(f"Charging location: {location}", fontsize=20)
        ax1.tick_params(axis="y", labelsize=20)
        ax1.grid(True, axis="y", alpha=0.3, zorder=0)
        ax1.set_ylim(top = sub["max_energy"].max() * 1.25)

        # ---- secondary: ratios ----
        ax2 = ax1.twinx()
        for col, color in ratio_colors.items():
            if sub[col].sum() == 0:
                continue
            ax2.plot(list(x_idx), sub[col].values, marker="o", color=color,
                     linewidth=2, linestyle="--", label=ratio_labels[col])
        ax2.set_ylabel("Plugin / Trip Ratio", fontsize=20)
        ax2.tick_params(axis="y", labelsize=20)
        ax2.set_ylim(bottom=0, top = 1)

        # ---- combined legend ----
        if location == "Home":
            h1, l1 = ax1.get_legend_handles_labels()
            h2, l2 = ax2.get_legend_handles_labels()
            # Legende zentral unter den Plots
            fig.legend(h1 + h2, l1 + l2, fontsize=20, loc="lower center", bbox_to_anchor=(0.5, -0.35), ncol=5, frameon=True)

    fig.subplots_adjust(bottom=0.12, wspace=0.35, left=0.05, right=0.95)
    out = plots_dir / "alpha_energy_and_ratios.png"
    fig.savefig(out, dpi=300, bbox_inches="tight")
    fig.savefig("figures/Figure11", dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {out}")


# =====================================================================
# LOAD DATA
# =====================================================================

rows = []

# Iterate through all plugin_alpha folders
for alpha_folder in sorted(BASE_DIR.iterdir()):
    if not alpha_folder.is_dir():
        continue
    
    plugin_alpha = extract_plugin_alpha_from_folder(alpha_folder.name)
    #if plugin_alpha in [20,40,80, 1000]:
     #   continue
    
    # Extract location from folder name (home or work)
    folder_location = None
    if alpha_folder.name.endswith('_home'):
        folder_location = 'Home'
    elif alpha_folder.name.endswith('_work'):
        folder_location = 'Work'
    
    if plugin_alpha is None or folder_location is None:
        continue
    
    # Load all JSON files from this folder (recursively!)
    for json_file in alpha_folder.rglob("*_kpis.json"):
        try:
            with open(json_file) as f:
                data = json.load(f)
            
            mean_energy = extract_mean_energy(data)
            if mean_energy is None:
                continue
            
            hour = extract_time_from_filename(json_file.name)
            file_location = extract_location_from_filename(json_file.name)
            
            if hour is None or file_location is None:
                continue
            
            rows.append({
                "plugin_alpha": plugin_alpha,
                "location": folder_location,  # From folder
                "file_location": file_location,  # From filename
                "hour": hour,
                "mean_energy": mean_energy,
            })
        
        except Exception as e:
            print(f"ERROR reading {json_file}: {e}")


df = pd.DataFrame(rows)

print(f"\nLoaded rows: {len(df)}")
print(df.head(20))
print(f"\nUnique plugin_alpha values: {sorted(df['plugin_alpha'].unique(), key=lambda x: (x != 'simple', x if x != 'simple' else float('inf')))}")
print(f"Unique hours: {sorted(df['hour'].unique())}")

# Print statistics summary with energy data
print_statistics_summary(df)

# =====================================================================
# PLOTTING
# =====================================================================

plots_dir = BASE_DIR / "analysis_plots"
plots_dir.mkdir(exist_ok=True)

# Plot the statistics table (energy + ratios vs alpha)
plot_statistics_summary(df, plots_dir)

# Subplots (Home + Work)
fig, axes = plt.subplots(1, 2, figsize=(14, 6))
axes = axes.flatten()

for ax, location in zip(axes, ["Home", "Work"]):
    alpha_values = sorted(df["plugin_alpha"].unique(), key=lambda x: (x != 'simple', x if x != 'simple' else float('inf')))

    # ✅ Max pro Location
    loc_max = df[df["location"] == location]["mean_energy"].max()

    for alpha in alpha_values:
        subset = df[
            (df["location"] == location) &
            (df["plugin_alpha"] == alpha)
        ]

        if subset.empty:
            continue

        subset_sorted = subset.sort_values("hour").copy()

        # ✅ Normierung pro Location
        subset_sorted["mean_energy_pct"] = (
            subset_sorted["mean_energy"] / loc_max
        ) * 100

        # Label: "simple" → "100% plugin", numbers → "α={alpha}"
        if alpha == 'simple':
            label = "100% plugin"
        else:
            # Entferne .0 von ganzzahligen Floats
            try:
                alpha_float = float(alpha)
                if alpha_float == int(alpha_float):
                    label = f"α={int(alpha_float)}"
                else:
                    label = f"α={alpha}"
            except:
                label = f"α={alpha}"

        ax.plot(
            subset_sorted["hour"],
            subset_sorted["mean_energy_pct"],
            marker="o",
            label=label,
            linewidth=2
        )

    ax.set_xlabel("Time of Day (hour)", fontsize = 20)
    ax.set_ylabel("Average Energy (AvgEn) (%)", fontsize = 20)
    ax.set_title(f"Charging Location: {location}", fontsize = 20)
    ax.tick_params(axis='both', labelsize=20)



    ax.set_xticks([1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23])
    ax.set_ylim(0, 100)
    ax.grid(True, alpha=0.3)
# statt:
# ax.legend(loc="lower center", fontsize=16, ncol=5)

handles, labels = axes[0].get_legend_handles_labels()

fig.legend(
    handles,
    labels,
    loc="lower center",
    bbox_to_anchor=(0.5, 0),
    ncol=5,
    fontsize=20
)

# mehr Platz unten reservieren
fig.tight_layout(rect=[0, 0.25, 1, 1])

fig.savefig(
    plots_dir / "timeofday_by_plugin_alpha.png",
    dpi=300,
    bbox_inches="tight"
)
fig.savefig(
    "figures/Figure10.png",
    dpi=300,
    bbox_inches="tight"
)
plt.close(fig)


