import json
import os
import re
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

# Resolved to an absolute path: Windows fails to open deeply nested files
# through long ".."-relative paths even when the final length is < 260 chars.
BASE_DIR = Path("../parameter_variations2").resolve()

TARGET_COMB = {"strat_pos": 0, "heuristic_pos": 1, "modus_pos": 1}


def long_path(path):
    # Bypasses Windows' 260-char MAX_PATH limit (some scenario paths exceed it).
    s = str(path)
    if os.name == "nt" and not s.startswith("\\\\?\\"):
        s = "\\\\?\\" + s
    return s


# =====================================================================
# HELPER
# =====================================================================

def extract_mean_energy(json_data):
    for rc in json_data["risk_combinations"]:
        if rc["combination"] == TARGET_COMB:
            return rc["quantiles_energy_kwh"]["mean"]
    return None


def extract_var_energy(json_data):
    for rc in json_data["risk_combinations"]:
        if rc["combination"] == TARGET_COMB:
            return rc["quantiles_energy_kwh"]["std"]
    return None


def classify_file(path):
    # Parsed from the sibling metadata.json content, not from the file name,
    # so scenario folders can be named/shortened freely. Only the fixed
    # "kpis.json" / "metadata.json" file names and the parent folder names
    # ("model_flexibilities" / "flex_scenarios") must stay as they are.
    path_str = str(path)

    info = {
        "type": None,
        "param": None,
        "value": None,
        "location": None,
    }

    metadata_path = path.with_name("metadata.json")
    try:
        with open(long_path(metadata_path)) as f:
            meta = json.load(f)
    except Exception:
        meta = {}

    # -------------------------
    # Flex scenarios
    # -------------------------
    if "flex_scenarios" in path_str:
        info["type"] = "flex"
        info["param"] = meta.get("flex_param_type")
        info["value"] = meta.get("flex_param_value")
        info["location"] = meta.get("flex_location")
        return info

    # -------------------------
    # Model flexibilities
    # -------------------------
    if "model_flexibilities" in path_str:
        info["type"] = "model"
        info["location"] = meta.get("flex_params", {}).get("flex_location")

        # Short internal name kept in the metadata, e.g. "model_battery10_simple_home"
        model_name = meta.get("model_params", {}).get("name", path.name)

        if "users" in model_name:
            info["param"] = "num_users"
        elif "model_alpha" in model_name:
            info["param"] = "plugin_alpha"
        elif "battery" in model_name and "_simple" in model_name:
            info["param"] = "battery_sizes_simple"
        elif "battery" in model_name:
            info["param"] = "battery_sizes"
        elif "power" in model_name:
            info["param"] = "power"

        pattern_by_param = {
            "num_users": r'users(\d+)(?:_(?:home|work))?',
            "plugin_alpha": r'alpha([\d_]+?)_(?:home|work)',
            "power": r'power([\d_]+?)_(?:home|work)',
            "battery_sizes_simple": r'battery([\d_]+?)_simple_(?:home|work)',
            "battery_sizes": r'battery([\d_]+?)_(?:home|work)',
        }
        pattern = pattern_by_param.get(info["param"])
        if pattern:
            match = re.search(pattern, model_name)
            if match:
                try:
                    info["value"] = float(match.group(1).replace("_", "."))
                except ValueError:
                    pass

    return info


# =====================================================================
# JSONs EINLESEN
# =====================================================================

rows = []

for file in BASE_DIR.rglob("kpis.json"):
    try:
        with open(long_path(file)) as f:
            data = json.load(f)

        mean_energy = extract_mean_energy(data)
        var_energy = extract_var_energy(data)

        if mean_energy is None:
            continue

        meta = classify_file(file)

        rows.append({
            "file": str(file),
            "type": meta["type"],
            "param": meta["param"],
            "value": meta["value"],
            "location": meta["location"],
            "mean_energy": mean_energy,
            "var_energy": var_energy,
        })

    except Exception as e:
        print(f"ERROR reading {file}: {e}")


df = pd.DataFrame(rows)

print("\nLoaded rows:", len(df))
print(df.head(20))

# Debug: Zeige plugin_alpha Werte
print("\n=== DEBUG: plugin_alpha values ===")
alpha_rows = df[df["param"] == "plugin_alpha"]
print(alpha_rows[["file", "value"]].to_string())


# =====================================================================
# PLOTS
# =====================================================================

plots_dir = BASE_DIR / "analysis_plots"
plots_dir.mkdir(exist_ok=True)


# ----------------------------------------------------------
# 1. MODEL EFFECTS
# ----------------------------------------------------------
for param in ["num_users", "plugin_alpha", "power", "battery_sizes_simple"]:
    subset = df[(df["type"] == "model") & (df["param"] == param)]

    if subset.empty:
        continue

    # Optional: Aggregation falls mehrere Werte pro Kombination existieren
    subset_agg = subset.groupby(["value", "location"])["mean_energy"].mean().reset_index()

    plt.figure()

    for loc in ["Home",
         "Work"]:
        sub = subset_agg[subset_agg["location"] == loc].sort_values("value")

        if not sub.empty:
            plt.plot(sub["value"], sub["mean_energy"], marker="o", label=loc)

    plt.xlabel(param)
    plt.ylabel("Mean Energy (kWh)")
    plt.title(f"Model variation: {param} (by location)")
    plt.legend()
    plt.grid()

    plt.savefig(plots_dir / f"model_{param}_by_location.png")
    plt.close()
# ----------------------------------------------------------
# 2. DURATION EFFECT (Home vs Work)
# ----------------------------------------------------------
# Nur flex_scenarios vom Basis-Modell verwenden
subset = df[(df["type"] == "flex") & (df["param"] == "duration")]

# Aggregiere falls mehrere Werte pro Duration/Location (Durchschnitt nehmen)
subset_agg = subset.groupby(["value", "location"])["mean_energy"].mean().reset_index()

if not subset_agg.empty:
    plt.figure()

    for loc in ["Home",
         "Work"]:
        sub = subset_agg[subset_agg["location"] == loc].sort_values("value")
        if not sub.empty:
            plt.plot(sub["value"], sub["mean_energy"], marker="o", label=loc)

    plt.xlabel("Duration (minutes)")
    plt.ylabel("Mean Energy (kWh)")
    plt.title("Flex Duration Effect (Base Model)")
    plt.legend()
    plt.grid()

    plt.savefig(plots_dir / "flex_duration.png")
    plt.close()


# ----------------------------------------------------------
# 3. ACTIVATION TIME EFFECT
# ----------------------------------------------------------
# Nur flex_scenarios vom Basis-Modell verwenden
subset = df[(df["type"] == "flex") & (df["param"] == "activation_time")]

# Aggregiere falls mehrere Werte pro Activation_Time/Location (Durchschnitt nehmen)
subset_agg = subset.groupby(["value", "location"])["mean_energy"].mean().reset_index()

if not subset_agg.empty:
    plt.figure()

    for loc in ["Home", "Work"]:
        sub = subset_agg[subset_agg["location"] == loc].sort_values("value")
        if not sub.empty:
            plt.plot(sub["value"], sub["mean_energy"], marker="o", label=loc)

    plt.xlabel("Activation Time (%)")
    plt.ylabel("Mean Energy (kWh)")
    plt.title("Activation Time Effect (Base Model)")
    plt.legend()
    plt.grid()

    plt.savefig(plots_dir / "activation_time.png")
    plt.close()


# ----------------------------------------------------------
# 4. GLOBAL DISTRIBUTION
# ----------------------------------------------------------
plt.figure()
plt.hist(df["mean_energy"], bins=30)

plt.xlabel("Mean Energy (kWh)")
plt.ylabel("Count")
plt.title("Distribution of all scenarios")

plt.grid()
plt.savefig(plots_dir / "distribution.png")
plt.close()



# ----------------------------------------------------------
# 5. COMBINED PERCENTAGE-CHANGE OVERVIEW (Home vs Work)
# ----------------------------------------------------------


BASE_VALUES = {
    "num_users": 100,
    "plugin_alpha": 2.5,
    "power": 44,
    #"battery_sizes": 80,
    "battery_sizes_simple": 80,
    "duration": 30,
    "activation_time": 50,
}

PARAM_LABELS = {
    "num_users": "Fleet Size",
    "plugin_alpha": "Plugin Activity",
    "power": "Charging Power",
    #"battery_sizes": "Battery Size",
    "battery_sizes_simple": "Battery Size",
    "duration": "Flexibility Duration",
    "activation_time": "Activation Time",
}

fig, axes = plt.subplots(1, 2, figsize=(14, 6), sharey=True)

for ax, loc in zip(axes, ["Work", "Home"]):
    for param, base_val in BASE_VALUES.items():
        # Select relevant rows for this param and location
        p_type = "flex" if param in ("duration", "activation_time") else "model"
        subset = df[(df["type"] == p_type) & (df["param"] == param) & (df["location"] == loc)]
        if subset.empty:
            continue

        subset_agg = subset.groupby("value")["mean_energy"].mean().reset_index().sort_values("value")

        # Base mean_energy: value closest to base_val
        base_row = subset_agg.iloc[(subset_agg["value"] - base_val).abs().argsort()[:1]]
        base_energy = base_row["mean_energy"].values[0]

        if base_energy == 0:
            continue

        x_pct = (subset_agg["value"] - base_val) / base_val * 100
        y_pct = (subset_agg["mean_energy"] - base_energy) / base_energy * 100

        ax.plot(x_pct.values, y_pct.values, marker="o", label=PARAM_LABELS[param])

    #ax.set_xscale("symlog", linthresh=5)
    ax.axhline(0, color="black", linewidth=0.8, linestyle="--")
    ax.axvline(0, color="black", linewidth=0.8, linestyle="--")
    ax.set_title(f"Charging Location: {loc}", fontsize = 22)
    ax.grid(True, alpha=0.4)
    ax.tick_params(axis='both', labelsize=18)


axes[0].set_ylabel("AvgEn change from base value (%)", fontsize = 22)
fig.supxlabel("Parameter change from base value (%)", fontsize=22)

handles, labels = axes[0].get_legend_handles_labels()
fig.legend(handles, labels, loc="lower center", bbox_to_anchor=(0.5, -0.15), ncol=3, fontsize=18)

fig.tight_layout()

fig.savefig(plots_dir / "combined_pct_change.png", dpi=300, bbox_inches="tight")
fig.savefig( "figures/combined_pct_change_Figure16.png", dpi=300, bbox_inches="tight")

plt.close(fig)



#5.2


fig, axes = plt.subplots(1, 2, figsize=(14, 6), sharey=True)

for ax, loc in zip(axes, ["Work", "Home"]):
    for param, base_val in BASE_VALUES.items():
        # Select relevant rows for this param and location
        p_type = "flex" if param in ("duration", "activation_time") else "model"
        subset = df[(df["type"] == p_type) & (df["param"] == param) & (df["location"] == loc)]
        if subset.empty:
            continue

        subset_agg = subset.groupby("value")["mean_energy"].mean().reset_index().sort_values("value")

        # Base mean_energy: value closest to base_val
        x_pct = (subset_agg["value"] - base_val) / base_val * 100

        # Energieänderung relativ zum jeweils vorherigen Schritt
        y_pct = subset_agg["mean_energy"].pct_change() * 100

        # erster Punkt hat keinen Vorgänger
        y_pct.iloc[0] = 0
        ax.plot(x_pct.values, y_pct.values, marker="o", label=PARAM_LABELS[param])

    #ax.set_xscale("symlog", linthresh=5)
    ax.axhline(0, color="black", linewidth=0.8, linestyle="--")
    ax.axvline(0, color="black", linewidth=0.8, linestyle="--")
    ax.set_title(f"Charging Location: {loc}", fontsize = 22)
    ax.grid(True, alpha=0.4)
    ax.tick_params(axis='both', labelsize=18)


axes[0].set_ylabel("AvgEn change from base value (%)", fontsize = 16)
fig.supxlabel("Parameter change from base value (%)", fontsize=20)

handles, labels = axes[0].get_legend_handles_labels()
fig.legend(handles, labels, loc="lower center", bbox_to_anchor=(0.5, -0.08), ncol=3, fontsize=18)

fig.tight_layout()

fig.savefig(plots_dir / "combined_pct_change2.png", dpi=600, bbox_inches="tight")
plt.close(fig)

# ----------------------------------------------------------
# 6. INCREMENTAL CHANGE OVERVIEW (step index relative to base)
# ----------------------------------------------------------
# X-axis: step number relative to the base value (0 = base, -1 = one step below, +1 = one step above)
#         Each point represents the step ARRIVING at that index.
# Y-axis: % change of mean_energy from the previous step to the current one

fig2, axes2 = plt.subplots(1, 2, figsize=(14, 6), sharey=True)

for ax, loc in zip(axes2, ["Work", "Home"]):
    for param, base_val in BASE_VALUES.items():
        p_type = "flex" if param in ("duration", "activation_time") else "model"
        subset = df[(df["type"] == p_type) & (df["param"] == param) & (df["location"] == loc)]
        if subset.empty:
            continue

        subset_agg = subset.groupby("value")["mean_energy"].mean().reset_index().sort_values("value")

        if len(subset_agg) < 2:
            continue

        vals = subset_agg["value"].values
        energies = subset_agg["mean_energy"].values

        # Find index of the value closest to base_val
        base_idx = int((abs(vals - base_val)).argmin())
        base_energy = energies[base_idx]

        if base_energy == 0:
            continue

        # Step indices for each transition i-1 → i, placed at index i relative to base
        step_indices = [i - base_idx for i in range(1, len(vals))]

        # Y-axis: cumulative % change of energy[i] relative to base (same as combined_pct_change)
        y_pct = [(energies[i] - base_energy) / base_energy * 100 for i in range(1, len(vals))]

        ax.plot(step_indices, y_pct, marker="o", label=PARAM_LABELS[param])

    ax.axhline(0, color="black", linewidth=0.8, linestyle="--")
    ax.axvline(0, color="black", linewidth=0.8, linestyle="--")
    ax.set_title(loc)
    ax.xaxis.set_major_locator(plt.MaxNLocator(integer=True))
    ax.grid(True, alpha=0.4)

axes2[0].set_ylabel("Mean energy change from base value (%)")
fig2.supxlabel("Step index relative to base scenario (0 = base)", fontsize=16)

handles, labels = axes2[0].get_legend_handles_labels()
fig2.legend(handles, labels, loc="lower center", bbox_to_anchor=(0.5, -0.08), ncol=len(labels), fontsize=18)

fig2.suptitle("Incremental sensitivity: All parameters (per-step % energy change)", fontsize=13)
fig2.tight_layout()

fig2.savefig(plots_dir / "combined_incremental_change.png", dpi=150, bbox_inches="tight")
plt.close(fig2)

#6.2
# ----------------------------------------------------------
# 6. INCREMENTAL CHANGE OVERVIEW (step index relative to base)
# ----------------------------------------------------------
# X-axis: step number relative to the base value
#         (0 = base, -1 = one step below, +1 = one step above)
#
# Y-axis: % change of mean_energy from the PREVIOUS step
#         to the current step
import numpy as np
fig2, axes2 = plt.subplots(1, 2, figsize=(14, 6), sharey=True)

for ax, loc in zip(axes2, ["Work", "Home"]):

    for param, base_val in BASE_VALUES.items():

        p_type = "flex" if param in ("duration", "activation_time") else "model"

        subset = df[
            (df["type"] == p_type)
            & (df["param"] == param)
            & (df["location"] == loc)
        ]

        if subset.empty:
            continue

        subset_agg = (
            subset
            .groupby("value")["mean_energy"]
            .mean()
            .reset_index()
            .sort_values("value")
        )

        if len(subset_agg) < 2:
            continue

        vals = subset_agg["value"].values
        energies = subset_agg["mean_energy"].values

        # Index of value closest to base value
        base_idx = int(np.abs(vals - base_val).argmin())

        # X positions: arrival step relative to base
        step_indices = [i - base_idx for i in range(1, len(vals))]

        # Y positions: % change relative to previous step
        y_pct = [
            (energies[i] - energies[i - 1]) / energies[i - 1] * 100
            if energies[i - 1] != 0
            else np.nan
            for i in range(1, len(vals))
        ]

        ax.plot(
            step_indices,
            y_pct,
            marker="o",
            linewidth=2,
            label=PARAM_LABELS[param]
        )

    ax.axhline(0, color="black", linewidth=0.8, linestyle="--")
    ax.axvline(0, color="black", linewidth=0.8, linestyle="--")

    ax.set_title(loc, fontsize=16)

    ax.xaxis.set_major_locator(plt.MaxNLocator(integer=True))
    ax.grid(True, alpha=0.4)
    ax.tick_params(axis="both", labelsize=14)

axes2[0].set_ylabel(
    "Mean energy change from previous step (%)",
    fontsize=16
)

fig2.supxlabel(
    "Step index relative to base scenario (0 = base)",
    fontsize=16
)

handles, labels = axes2[0].get_legend_handles_labels()
fig2.legend(handles, labels, loc="lower center", bbox_to_anchor=(0.5, -0.08), ncol=len(labels), fontsize=18)

fig2.suptitle(
    "Incremental sensitivity: per-step energy change",
    fontsize=16
)

fig2.tight_layout()

fig2.savefig(
    plots_dir / "combined_incremental_change2.png",
    dpi=600,
    bbox_inches="tight"
)

plt.close(fig2)

# ----------------------------------------------------------
# 6.3 INCREMENTAL CHANGE (excluding lowest plugin_alpha, using lowest as base)
# ----------------------------------------------------------
# Same as 6 but:
# - Exclude the lowest plugin_alpha value
# - Use the lowest remaining value as base scenario
# - Y-axis: cumulative % change relative to base (not relative to previous step)

fig3, axes3 = plt.subplots(1, 2, figsize=(14, 6), sharey=True)

for ax, loc in zip(axes3, ["Work", "Home"]):
    for param, base_val in BASE_VALUES.items():
        p_type = "flex" if param in ("duration", "activation_time") else "model"
        subset = df[
            (df["type"] == p_type)
            & (df["param"] == param)
            & (df["location"] == loc)
        ]

        if subset.empty:
            continue

        subset_agg = (
            subset
            .groupby("value")["mean_energy"]
            .mean()
            .reset_index()
            .sort_values("value")
        )

        if len(subset_agg) < 2:
            continue

        vals = subset_agg["value"].values
        energies = subset_agg["mean_energy"].values

        # For plugin_alpha: exclude the lowest value
        if param == "plugin_alpha":
            vals = vals[1:]
            energies = energies[1:]
            if len(vals) < 1:
                continue

        # Use lowest remaining value as base
        base_idx = 0
        base_val_lowest = vals[base_idx]
        base_energy = energies[base_idx]

        if base_energy == 0:
            continue

        # X positions: % change of parameter value relative to lowest
        x_pct = (vals - base_val_lowest) / base_val_lowest * 100

        # Y positions: cumulative % change relative to base (starting from 0% at base)
        y_pct = [(energies[i] - base_energy) / base_energy * 100 for i in range(len(vals))]

        ax.plot(
            x_pct,
            y_pct,
            marker="o",
            linewidth=2,
            label=PARAM_LABELS[param]
        )

    ax.axhline(0, color="black", linewidth=0.8, linestyle="--")
    ax.axvline(0, color="black", linewidth=0.8, linestyle="--")

    ax.set_title(loc, fontsize=16)

    ax.grid(True, alpha=0.4)
    ax.tick_params(axis="both", labelsize=14)

axes3[0].set_ylabel(
    "Mean energy change from base value (%)",
    fontsize=16
)

fig3.supxlabel(
    "Parameter change from lowest scenario (%)",
    fontsize=16
)

handles, labels = axes3[0].get_legend_handles_labels()
fig3.legend(handles, labels, loc="lower center", bbox_to_anchor=(0.5, -0.08), ncol=len(labels), fontsize=18)

fig3.suptitle(
    "Incremental sensitivity: cumulative % change (lowest scenario as base, plugin_alpha min excluded)",
    fontsize=16
)

fig3.tight_layout()

fig3.savefig(
    plots_dir / "combined_incremental_change_lowest_base.png",
    dpi=600,
    bbox_inches="tight"
)

plt.close(fig3)


# ----------------------------------------------------------
fig3, axes3 = plt.subplots(1, 2, figsize=(14, 6), sharey=True)

for ax, loc in zip(axes3, ["Work", "Home"]):
    for param, base_val in BASE_VALUES.items():
        p_type = "flex" if param in ("duration", "activation_time") else "model"
        subset = df[(df["type"] == p_type) & (df["param"] == param) & (df["location"] == loc)]
        if subset.empty:
            continue

        subset_agg = subset.groupby("value")["var_energy"].mean().reset_index().sort_values("value")

        # Base variance: value closest to base_val
        base_row = subset_agg.iloc[(subset_agg["value"] - base_val).abs().argsort()[:1]]
        base_var = base_row["var_energy"].values[0]

        if base_var == 0:
            continue

        x_pct = (subset_agg["value"] - base_val) / base_val * 100
        y_pct = (subset_agg["var_energy"] - base_var) / base_var * 100

        ax.plot(x_pct.values, y_pct.values, marker="o", label=PARAM_LABELS[param])

    ax.axhline(0, color="black", linewidth=0.8, linestyle="--")
    ax.axvline(0, color="black", linewidth=0.8, linestyle="--")
    ax.set_title(f"Charging Location: {loc}", fontsize = 20)
    ax.grid(True, alpha=0.4)
    ax.tick_params(axis='both', labelsize=18)

axes3[0].set_ylabel("Change of Std. deviation from base value (%)", fontsize = 22)
fig3.supxlabel("Parameter change from base value (%)", fontsize=22)

handles, labels = axes3[0].get_legend_handles_labels()
fig3.legend(handles, labels, loc="lower center", bbox_to_anchor=(0.5, -0.15), ncol=3, fontsize=18)

fig3.tight_layout()

fig3.savefig(plots_dir / "combined_pct_change_variance.png", dpi=300, bbox_inches="tight")
fig3.savefig("figures/combined_pct_change_variance_Figure17.png", dpi=300, bbox_inches="tight")
plt.close(fig3)

# ----------------------------------------------------------
# 8. ALPHA: ENERGY RANGE (min/max band) + HOME/WORK SHARE
# ----------------------------------------------------------
alpha_data = df[(df["type"] == "model") & (df["param"] == "plugin_alpha")].copy()
alpha_agg = alpha_data.groupby(["value", "location"])["mean_energy"].mean().reset_index()

pivot_alpha = alpha_agg.pivot(index="value", columns="location", values="mean_energy").sort_index()

if "Home" in pivot_alpha.columns and "Work" in pivot_alpha.columns:
    pivot_alpha["min_e"] = pivot_alpha[["Home", "Work"]].min(axis=1)
    pivot_alpha["max_e"] = pivot_alpha[["Home", "Work"]].max(axis=1)
    pivot_alpha["total"]      = pivot_alpha["Home"] + pivot_alpha["Work"]
    pivot_alpha["home_share"] = pivot_alpha["Home"] / pivot_alpha["total"] * 100
    pivot_alpha["work_share"] = pivot_alpha["Work"] / pivot_alpha["total"] * 100

    fig, ax1 = plt.subplots(figsize=(9, 5))

    # ---- primary axis: energy band + lines ----
    ax1.fill_between(
        pivot_alpha.index,
        pivot_alpha["min_e"],
        pivot_alpha["max_e"],
        alpha=0.18, color="steelblue",
        label="Energy range (Home–Work)"
    )
    ax1.plot(pivot_alpha.index, pivot_alpha["Home"], marker="o",
             color="steelblue", linewidth=2, label="Home energy (kWh)")
    ax1.plot(pivot_alpha.index, pivot_alpha["Work"], marker="s",
             color="darkorange", linewidth=2, label="Work energy (kWh)")

    ax1.set_xlabel("Plugin Alpha", fontsize=14)
    ax1.set_ylabel("Mean Energy (kWh)", fontsize=14)
    ax1.tick_params(axis="both", labelsize=12)
    ax1.set_xscale("log")
    ax1.set_xticks(pivot_alpha.index)
    ax1.get_xaxis().set_major_formatter(plt.ScalarFormatter())
    ax1.grid(True, alpha=0.3)

    # ---- secondary axis: home / work share ----
    ax2 = ax1.twinx()
    ax2.plot(pivot_alpha.index, pivot_alpha["home_share"], marker="o",
             color="steelblue", linewidth=2, linestyle="--", alpha=0.65,
             label="Home share (%)")
    ax2.plot(pivot_alpha.index, pivot_alpha["work_share"], marker="s",
             color="darkorange", linewidth=2, linestyle="--", alpha=0.65,
             label="Work share (%)")
    ax2.set_ylabel("Share (%)", fontsize=14)
    ax2.tick_params(axis="y", labelsize=12)
    ax2.set_ylim(0, 100)

    # ---- combined legend ----
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper left", fontsize=11)

    fig.tight_layout()
    fig.savefig(plots_dir / "alpha_energy_range_share.png", dpi=300)
    plt.close(fig)
    print("Saved: alpha_energy_range_share.png")


print(f"\nPlots gespeichert in: {plots_dir}")