import argparse
import csv
import os
import sys
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
from fontTools.ttLib.woff2 import bboxFormat

# Projekt-Root ins sys.path und als Arbeitsverzeichnis setzen, damit die
# Top-Level-Imports und relativen Pfade (z.B. "models_final/...") unabhängig
# vom Startordner funktionieren.
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)
os.chdir(PROJECT_ROOT)

from analysis_methods.Charging_profile import compute_UK_ch_profiles, compute_charging_profile
from analysis_methods.work_data import build_profile
from config.settings import settingsContainer
from helper_files.variables import open_file

# ---------- KONFIG ----------

DEFAULT_MODEL = "models_final/model_pl_normal_agegroup_1"
LOCATIONS = ["home", "work", "public"]

MODEL_KIND = {
    "home": "Home",
    "work": "Work",
    "public": "Public",
}

REAL_PROFILE_FILE = {
    "home": "dataCharging/alreadyLoaded/UK_charging_home_whole",
    "work": "dataCharging/alreadyLoaded/lama_work_whole",
    "public": "dataCharging/alreadyLoaded/UK_charging_public_whole",
}

COLORS = {
    "home": "#1f77b4",
    "work": "#2ca02c",
    "public": "#ffbf00",
}


# ---------- MODEL HELPERS ----------

def find_all_models(base_dir="models_final"):
    all_models = Path(base_dir).glob("model_pl_normal_*.pkl")

    # ✅ filtere alle mit "_work"
    filtered = [
        m for m in all_models
        if "_work" not in m.name
    ]

    return sorted(filtered)

def load_model_profiles(model_path: str, locations):
    model_data = open_file(model_path)
    settingsContainer.updateSettings(model_data.model_settings, as_dict=True)

    vehicle_lists = model_data.VehicleLists
    start_day = int(settingsContainer.getStartDay())
    number_of_days = settingsContainer.getNumberOfDays()

    profiles = {}
    for location in locations:
        profiles[location] = compute_charging_profile(
            DayType=-1,
            VehicleList=vehicle_lists,
            start_day=start_day,
            kind=MODEL_KIND[location],
            number_of_days=number_of_days,
        )
    return profiles


def load_all_model_profiles(model_paths, locations):
    all_profiles = {}

    for model_file in model_paths:
        model_path = model_file.with_suffix("")
        name = model_file.stem.replace("model_pl_normal_", "")

        print(f"Lade Modell: {model_file}")

        try:
            profiles = load_model_profiles(str(model_path), locations)
            all_profiles[name] = profiles
        except Exception as e:
            print(f"Fehler bei {model_file}: {e}")

    return all_profiles


# ---------- PROFILE → XY ----------

def profile_to_xy(profile):
    x_values = []
    y_values = []

    powers = []
    for idx, interval in enumerate(profile.intervals_ChargingProfiles):
        x_values.append(idx * (profile.interval_size.total_seconds() / 3600.0))
        powers.append(float(interval.total_power))

    total = sum(powers)
    if total > 0:
        y_values = [(p / total) * 100 for p in powers]
    else:
        y_values = [0 for _ in powers]

    return x_values, y_values


# ---------- REAL PROFILE ----------

def load_real_profile(location, day_type):
    file_base = REAL_PROFILE_FILE[location]
    if not Path(file_base + ".pkl").exists():
        return None
    return compute_UK_ch_profiles(day_type, file_base)


def profile_real_to_xy(profile):
    return profile_to_xy(profile)


# ---------- MAIN ----------

def main():
    print("Starte Vergleich ALLER Modelle")

    model_paths = find_all_models()
    print(f"{len(model_paths)} Modelle gefunden")

    all_profiles = load_all_model_profiles(model_paths, LOCATIONS)

    fig, ax = plt.subplots(figsize=(12, 6))

    # ---------- 1. EINZELNE MODELLE (transparent) ----------
    for model_name, profiles in all_profiles.items():
        for location in LOCATIONS:
            x, y = profile_to_xy(profiles[location])

            ax.plot(
                x,
                y,
                color=COLORS[location],
                alpha=0.25,      # ✅ wichtig → viele Linien sichtbar aber nicht dominant
                linewidth=1
            )

    # ---------- 2. MITTELWERT (fett) ----------
    for location in LOCATIONS:
        all_y = []
        base_x = None

        for profiles in all_profiles.values():
            x, y = profile_to_xy(profiles[location])
            base_x = x
            all_y.append(y)

        if all_y:
            mean_y = np.mean(all_y, axis=0)

            ax.plot(
                base_x,
                mean_y,
                color=COLORS[location],
                linewidth=3,
                label=f"Mean {location}"
            )

    # ---------- 3. REAL PROFILE ----------
    if False:
        for location in LOCATIONS:
            real_profile = load_real_profile(location, day_type=8)

            if real_profile:
                x, y = profile_real_to_xy(real_profile)

                ax.plot(
                    x,
                    y,
                    color=COLORS[location],
                    linestyle="--",
                    linewidth=2,
                    label=f"Real {location}"
                )

    # ---------- ACHSEN ----------
    ax.set_xlabel("Time of day [h]")
    ax.set_ylabel("Share of total charging power [%]")
    ax.set_xlim(0, 24)
    ax.set_xticks(range(0, 25, 2))

    ax.grid(alpha=0.3)

    # ---------- LEGENDE ----------
    ax.legend(frameon=False, ncol=2)

    plt.tight_layout()

    # ---------- SPEICHERN ----------
    output = Path("figures/all_models_charging_profiles_Figure12.png")
    output.parent.mkdir(exist_ok=True)
    plt.savefig(output, dpi=300, bbox_inches="tight")

    print(f"Plot gespeichert: {output}")

    plt.show()

def get_attribute_color(model_name):
    if "homogroup" in model_name:
        return "blue"
    if "mobilitygroup" in model_name:
        return "green"
    if "regiontype" in model_name:
        return "red"
    if "agegroup" in model_name:
        return "orange"
    if "econstatus" in model_name:
        return "purple"
    return "gray"


def get_attribute_name(model_name):
    for attr in ["homogroup", "mobilitygroup", "regiontype", "agegroup", "econstatus"]:
        if attr in model_name:
            return attr
    return "other"


def main3():
    print("Starte Vergleich ALLER Modelle")

    model_paths = find_all_models()
    print(f"{len(model_paths)} Modelle gefunden")

    all_profiles = load_all_model_profiles(model_paths, LOCATIONS)

    # ✅ 3 Subplots: home, work, public
    fig, axes = plt.subplots(1, 3, figsize=(15, 5), sharey=True)

    if len(LOCATIONS) == 1:
        axes = [axes]

    for ax, location in zip(axes, LOCATIONS):

        # ---------- 1. EINZELNE MODELLE ----------
        for model_name, profiles in all_profiles.items():
            x, y = profile_to_xy(profiles[location])

            color = get_attribute_color(model_name)

            ax.plot(
                x,
                y,
                color=color,
                alpha=0.2,
                linewidth=1
            )

        # ---------- 2. MITTELWERTE PRO ATTRIBUT ----------
        attributes = ["homogroup", "mobilitygroup", "regiontype", "agegroup", "econstatus"]

        for attr in attributes:
            all_y = []
            base_x = None

            for model_name, profiles in all_profiles.items():
                if attr not in model_name:
                    continue

                x, y = profile_to_xy(profiles[location])
                base_x = x
                all_y.append(y)

            if False and all_y:
                mean_y = np.mean(all_y, axis=0)

                ax.plot(
                    base_x,
                    mean_y,
                    color=get_attribute_color(attr),
                    linewidth=3,
                    label=f"{attr}"
                )

        # ---------- 3. REAL PROFILE ----------
        real_profile = load_real_profile(location, day_type=8)

        if real_profile:
            x, y = profile_real_to_xy(real_profile)

            ax.plot(
                x,
                y,
                color="black",
                linestyle="--",
                linewidth=2,
                label="Real"
            )

        # ---------- Achsen ----------
        ax.set_title(location)
        ax.set_xlim(0, 24)
        ax.set_xticks(range(0, 25, 2))
        ax.grid(alpha=0.3)
        ax.set_xlabel("Time of day [h]")

    axes[0].set_ylabel("Share of total charging power [%]")

    # ---------- Legende (nur einmal) ----------
    axes[-1].legend(frameon=False)

    plt.tight_layout()

    # ---------- speichern ----------
    output = Path("figures/all_models_by_attribute_subplots.png")
    output.parent.mkdir(exist_ok=True)
    plt.savefig(output, dpi=300, bbox_inches="tight")

    print(f"Plot gespeichert: {output}")

    plt.show()
def main2():
    print("Starte Einzelplots für alle Modelle")

    model_paths = find_all_models()
    print(f"{len(model_paths)} Modelle gefunden")

    output_dir = Path("figures/individual_models")
    output_dir.mkdir(parents=True, exist_ok=True)

    for model_file in model_paths:

        model_path = model_file.with_suffix("")
        model_name = model_file.stem.replace("model_pl_normal_", "")

        print(f"\nPlotte Modell: {model_name}")

        try:
            profiles = load_model_profiles(str(model_path), LOCATIONS)
        except Exception as e:
            print(f"Fehler bei {model_name}: {e}")
            continue

        # ---------- Plot ----------
        fig, ax = plt.subplots(figsize=(10, 5))

        # Modell
        for location in LOCATIONS:
            x, y = profile_to_xy(profiles[location])

            ax.plot(
                x,
                y,
                color=COLORS[location],
                linewidth=2,
                label=f"Model {location}"
            )

        # Real Profile
        for location in LOCATIONS:
            real_profile = load_real_profile(location, day_type=8)

            if real_profile:
                x, y = profile_real_to_xy(real_profile)

                ax.plot(
                    x,
                    y,
                    color=COLORS[location],
                    linestyle="--",
                    linewidth=2,
                    label=f"Real {location}"
                )

        # ---------- Achsen ----------
        ax.set_title(model_name)
        ax.set_xlabel("Time of day [h]")
        ax.set_ylabel("Share of total charging power [%]")
        ax.set_xlim(0, 24)
        ax.set_xticks(range(0, 25, 2))
        ax.grid(alpha=0.3)

        ax.legend(frameon=False)

        plt.tight_layout()

        # ---------- Speichern ----------
        out_file = output_dir / f"{model_name}.png"
        plt.savefig(out_file, dpi=200, bbox_inches="tight")
        plt.close(fig)

        print(f"Gespeichert: {out_file}")

    print("\n✅ Alle Einzelplots erstellt")

def get_attribute_name(model_name):
    for attr in ["homogroup", "mobilitygroup", "regiontype", "agegroup", "econstatus"]:
        if attr in model_name:
            return attr
    return None

def main4():
    print("Starte Plots pro Attributkategorie")

    model_paths = find_all_models()
    print(f"{len(model_paths)} Modelle gefunden")

    all_profiles = load_all_model_profiles(model_paths, LOCATIONS)

    attributes = ["homogroup", "mobilitygroup", "regiontype", "agegroup", "econstatus"]

    output_dir = Path("figures/by_attribute")
    output_dir.mkdir(parents=True, exist_ok=True)

    for attr in attributes:

        print(f"\nPlotte Kategorie: {attr}")

        # ✅ nur Modelle dieser Kategorie
        subset = {
            name: profiles
            for name, profiles in all_profiles.items()
            if attr in name
        }

        if not subset:
            print(f"Keine Modelle für {attr}")
            continue

        # ✅ Figure mit 3 Subplots
        fig, axes = plt.subplots(1, 3, figsize=(15, 5), sharey=True)

        if len(LOCATIONS) == 1:
            axes = [axes]

        for ax, location in zip(axes, LOCATIONS):

            # ---------- 1. Einzelne Modelle ----------
            for model_name, profiles in subset.items():
                x, y = profile_to_xy(profiles[location])

                ax.plot(
                    x,
                    y,
                    color="gray",
                    alpha=0.3,
                    linewidth=1
                )

            # ---------- 2. Mittelwert ----------
            all_y = []
            base_x = None

            for profiles in subset.values():
                x, y = profile_to_xy(profiles[location])
                base_x = x
                all_y.append(y)

            if all_y:
                mean_y = np.mean(all_y, axis=0)

                ax.plot(
                    base_x,
                    mean_y,
                    color="red",
                    linewidth=3,
                    label="Mean"
                )

            # ---------- 3. Real ----------
            real_profile = load_real_profile(location, day_type=8)

            if real_profile:
                x, y = profile_real_to_xy(real_profile)

                ax.plot(
                    x,
                    y,
                    color="black",
                    linestyle="--",
                    linewidth=2,
                    label="Real"
                )

            # ---------- Achsen ----------
            ax.set_title(location)
            ax.set_xlim(0, 24)
            ax.set_xticks(range(0, 25, 2))
            ax.grid(alpha=0.3)
            ax.set_xlabel("Time of day [h]")

        axes[0].set_ylabel("Share of total charging power [%]")

        # ✅ Titel der gesamten Figure
        fig.suptitle(attr, fontsize=14)

        # ✅ Legende nur einmal
        axes[-1].legend(frameon=False)

        plt.tight_layout()

        # ---------- speichern ----------
        out_file = output_dir / f"{attr}.png"
        plt.savefig(out_file, dpi=220, bbox_inches="tight")
        plt.close(fig)

        print(f"Gespeichert: {out_file}")

    print("\n✅ Alle Attribut-Plots erstellt")

import matplotlib.pyplot as plt
from pathlib import Path
import numpy as np


def get_attribute_name(model_name):
    for attr in ["homogroup", "mobilitygroup", "regiontype", "agegroup", "econstatus"]:
        if attr in model_name:
            return attr
    return None


def main5():
    print("Starte Plots pro Attributkategorie (alle Modelle einzeln)")

    model_paths = find_all_models()
    print(f"{len(model_paths)} Modelle gefunden")

    all_profiles = load_all_model_profiles(model_paths, LOCATIONS)

    attributes = ["homogroup", "mobilitygroup", "regiontype", "agegroup", "econstatus"]

    output_dir = Path("figures/by_attribute_lines")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Farbpalette (automatisch viele Farben)
    cmap = plt.cm.get_cmap("tab10")  # gut unterscheidbar

    for attr in attributes:

        print(f"\nPlotte Kategorie: {attr}")

        # ✅ nur Modelle dieser Kategorie
        subset = {
            name: profiles
            for name, profiles in all_profiles.items()
            if attr in name
        }

        if not subset:
            print(f"Keine Modelle für {attr}")
            continue

        model_names = sorted(subset.keys())

        fig, axes = plt.subplots(1, 3, figsize=(15, 5), sharey=True)

        if len(LOCATIONS) == 1:
            axes = [axes]

        for ax, location in zip(axes, LOCATIONS):

            for i, model_name in enumerate(model_names):
                profiles = subset[model_name]

                x, y = profile_to_xy(profiles[location])

                color = cmap(i % 10)  # rotiert Farben wenn >10 Modelle

                ax.plot(
                    x,
                    y,
                    color=color,
                    linewidth=2,
                    label=model_name
                )

            ax.set_title(location, fontsize = 20)
            ax.set_xlim(0, 24)
            ax.set_xticks(range(0, 25, 2))
            ax.grid(alpha=0.3)
            ax.set_xlabel("Time of day [h]")

        axes[0].set_ylabel("Share of total charging power [%]")

        fig.suptitle(attr, fontsize=14)

        # ✅ Legende NUR EINMAL (rechts)
        axes[-1].legend(
            loc="upper left",
            bbox_to_anchor=(1.02, 1),
            frameon=False
        )

        plt.tight_layout(rect=(0, 0, 0.80, 1))

        out_file = output_dir / f"{attr}.png"
        plt.savefig(out_file, dpi=220, bbox_inches="tight")
        plt.close(fig)

        print(f"Gespeichert: {out_file}")

    print("\n✅ Fertig")


import matplotlib.pyplot as plt
from pathlib import Path


import matplotlib.pyplot as plt
from pathlib import Path


import matplotlib.pyplot as plt
import matplotlib.lines as mlines
from pathlib import Path
import matplotlib.cm as cm


def extract_variant(model_name):
    # z.B. model_pl_normal_regiontype_3 → 3
    return model_name.split("_")[-1]


import matplotlib.pyplot as plt
import matplotlib.lines as mlines
from pathlib import Path
import matplotlib.cm as cm


def extract_variant(model_name):
    # z.B. model_pl_normal_regiontype_3 → 3
    return model_name.split("_")[-1]


def main6():
    print("Starte große Subplot-Figure mit sauberer Legende")
    attribute_titles = {
        "regiontype": "Region Type",
        "agegroup": "Age Group",
        "econstatus": "Economic Status",
        "mobilitygroup": "Mobility Group",
        "homogroup": "Homogeneous Group"
    }
    model_paths = find_all_models()
    all_profiles = load_all_model_profiles(model_paths, LOCATIONS)

    attributes = ["homogroup", "mobilitygroup", "regiontype", "agegroup", "econstatus"]
    selected_locations = ["home", "work"]

    # ✅ ---------- 1. ALLE VARIANTEN GLOBAL SAMMELN ----------
    variant_ids = set()

    for model_name in all_profiles.keys():
        try:
            variant_ids.add(extract_variant(model_name))
        except:
            continue

    variant_ids = sorted(variant_ids, key=int)

    print(f"Gefundene Varianten: {variant_ids}")

    # ✅ ---------- 2. STABILE FARBZUORDNUNG ----------
    cmap = cm.get_cmap("tab10", len(variant_ids))

    variant_colors = {
        variant: cmap(i)
        for i, variant in enumerate(variant_ids)
    }

    # ✅ ---------- 3. SUBPLOTS ----------
    fig, axes = plt.subplots(
         len(attributes), 2,
        figsize=(16, 24),
        sharex=True,
        sharey=False
    )

    for row_idx, attr in enumerate(attributes):

        subset = {
            name: profiles
            for name, profiles in all_profiles.items()
            if attr in name
        }

        if not subset:
            continue

        for col_idx, location in enumerate(selected_locations):

            ax = axes[row_idx][col_idx]

            for model_name, profiles in subset.items():

                variant = extract_variant(model_name)
                color = variant_colors[variant]

                x, y = profile_to_xy(profiles[location])

                ax.plot(
                    x,
                    y,
                    color=color,
                    linewidth=1.8,
                    alpha=0.9
                )

            ax.set_xlim(0, 24)

            ax.set_xticks(range(0, 25, 6))
            ax.tick_params(axis='both', labelsize=24)
            ax.grid(alpha=0.20)

            if row_idx == len(attributes) - 1:
                ax.set_xlabel("Time [h]", fontsize = 24)

    # ✅ ---------- TITEL-PLATZIERUNG ----------
    # Spalten-Titel oben ("Charging Location: Home", "Charging Location: Work")
    fig.text(0.33, 0.945, "Charging Location: Home", ha='center', fontsize=24)
    fig.text(0.79, 0.945, "Charging Location: Work", ha='center', fontsize=24)
#vorher 0.27, 0.955, 0.73
    home_max = 0
    work_max = 0

    for row_idx in range(len(attributes)):
        home_max = max(home_max, max(axes[row_idx, 0].get_ylim()))
        work_max = max(work_max, max(axes[row_idx, 1].get_ylim()))

    for row_idx in range(len(attributes)):
        axes[row_idx, 0].set_ylim(0, home_max)
        axes[row_idx, 1].set_ylim(0, work_max)

    # ✅ ---------- 4. LEGENDE (ALLE VARIANTEN!) ----------
    handles = []
    labels = []

    for variant in variant_ids:
        handles.append(
            mlines.Line2D([], [], color=variant_colors[variant], linewidth=2)
        )
        labels.append(str(variant))

    fig.legend(
        handles,
        labels,
        title="Attribute number within attribute category (see table 1 for attribute assignment)",
        loc="lower center",
        title_fontsize = 24,
        ncol=len(variant_ids),
        fontsize=26,
        bbox_to_anchor=(0.5, 0.10)
    )

    # ✅ ---------- 5. LAYOUT FIX (WICHTIG!) ----------
    plt.tight_layout(rect=(0.07, 0.15, 1, 0.94), h_pad=1.5)
    # ↑ sorgt dafür, dass Titel links und Legende sichtbar bleiben

    # Zeilen-Titel links (Attribute vertikal, zweizeilig, manuell definiert)
    # Positionierung erst nach tight_layout, damit die tatsächliche Achsenhöhe genutzt wird
    row_labels = [
        "Homogeneous\nGroup",
        "Mobility\nGroup",
        "Region\nType",
        "Age\nGroup",
        "Economic\nStatus"
    ]

    for row_idx, label_text in enumerate(row_labels):
        bbox = axes[row_idx, 0].get_position()
        y_pos = (bbox.y0 + bbox.y1) / 2

        fig.text(bbox.x0 - 0.05, y_pos, label_text,
                 ha='right', va='center', fontsize=24, rotation=90, linespacing=1.5)

    # ---------- speichern ----------
    output = Path("paper_plots/figures/all_attributes_compact_fixed_Figure12.png")
    output.parent.mkdir(exist_ok=True)
    plt.savefig(output, dpi=300, bbox_inches="tight")

    print(f"Plot gespeichert: {output}")

    plt.show()









# ---------- RUN ----------
if __name__ == "__main__":
    main6()
