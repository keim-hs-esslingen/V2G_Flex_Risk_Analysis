from __future__ import annotations
import argparse
from pathlib import Path
import numpy as np
import pandas as pd
from pathlib import Path
from typing import List, Optional
import pandas as pd
import argparse
from pathlib import Path
import math

import numpy as np
import pandas as pd


# Pandas engine hints
CSV_READ_KW = dict(dtype='object', engine='python')


def sniff_delimiter(sample_bytes: bytes, default=',') -> str:
    try:
        sample = sample_bytes.decode('utf-8', errors='ignore')
        dialect = csv.Sniffer().sniff(sample, delimiters=[',',';','\t','|',':'])
        return dialect.delimiter
    except Exception:
        return default


def read_csv_robust(path: Path) -> pd.DataFrame:
    """Read CSV with delimiter sniffing and encoding fallback.
    Returns empty DF on fatal errors.
    """
    # Sniff delimiter
    try:
        with open(path, 'rb') as fh:
            sample = fh.read(8192)
        delim = sniff_delimiter(sample)
    except Exception:
        delim = ','

    # Try utf-8-sig first
    for enc in ('utf-8-sig', 'utf-8', 'latin-1'):
        try:
            df = pd.read_csv(path, sep=delim, encoding=enc, **CSV_READ_KW)
            return df
        except Exception:
            continue
    # As last resort
    try:
        df = pd.read_csv(path, **CSV_READ_KW)
        return df
    except Exception:
        return pd.DataFrame()


def merge_all(root: Path, out_path: Path) -> Path:
    if not root.exists() or not root.is_dir():
        raise FileNotFoundError(f"Root folder not found: {root}")

    frames: List[pd.DataFrame] = []
    first_cols: Optional[List[str]] = None

    # NUR direkt unter `root`: ein Level
    for subdir in sorted([p for p in root.iterdir() if p.is_dir()]):
        # timeseries-Unterordner komplett überspringen
        if subdir.name.lower() == 'timeseries':
            continue

        # Alle CSVs direkt in diesem Unterordner (keine Rekursion)
        csv_files = sorted([p for p in subdir.iterdir()
                            if p.is_file() and p.suffix.lower() == '.csv'])

        for fpath in csv_files:
            df = read_csv_robust(fpath)
            # komplett leere/unlesbare überspringen
            if df.empty and df.shape[1] == 0:
                continue

            # Meta-Spalten hinzufügen
            df.insert(0, 'source_dir', str(subdir.relative_to(root)))
            df.insert(1, 'source_file', fpath.name)

            if first_cols is None:
                first_cols = list(df.columns)
            frames.append(df)

    if not frames:
        # Empty over_all with just meta cols
        empty = pd.DataFrame(columns=['source_dir','source_file'])
        empty.to_csv(out_path, index=False)
        return out_path

    # Union der Spalten (Reihenfolge der ersten Datei beibehalten)
    all_cols = list(first_cols)  # type: ignore[arg-type]
    seen = set(all_cols)
    for df in frames[1:]:
        for c in df.columns:
            if c not in seen:
                all_cols.append(c)
                seen.add(c)

    # reindex frames to union
    frames = [df.reindex(columns=all_cols) for df in frames]

    merged = pd.concat(frames, ignore_index=True)
    merged.to_csv(out_path, index=False, encoding='utf-8-sig')  # Excel-friendly
    return out_path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', type=str, default='../anonym_data',
                    help='Root folder containing subfolders with CSV files')
    ap.add_argument('--out', type=str, default='over_all.csv',
                    help='Output CSV filename')
    args = ap.parse_args()

    root = Path(args.root)
    out_path = Path(args.out)

    out_file = merge_all(root, out_path)
    print(f"Wrote merged CSV: {out_file} ({out_file.stat().st_size} bytes)")



#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
work_data.py

Erzeugt ein tageszeitliches Ladeprofil (0–24 Uhr, minutengenau) aus einer
CSV-Datei im Format von 'work_data' und plottet optional das Profil.

Neu:
- --plot: interaktive Anzeige der Plots (Minutenprofil und stündlich)
- --save_plots: PNGs speichern
- --plot_dir: Zielordner für PNGs

Nutzung (Beispiel):
    python work_data.py --in over_all.csv --out work_charging_profile.csv \
        --out_hourly work_charging_profile_hourly.csv --rated_kw 11 \
        --plot --save_plots --plot_dir out
"""



# ---- Optional: Matplotlib nur importieren, wenn geplottet/gespeichert wird
def _lazy_import_matplotlib():
    import matplotlib
    # Falls kein Display verfügbar ist (z.B. auf Servern), ein non-interaktives Backend wählen:
    try:
        import os
        if os.environ.get("DISPLAY", "") == "":
            matplotlib.use("Agg")
    except Exception:
        pass
    import matplotlib.pyplot as plt
    return matplotlib, plt


# ----------------------------- Helpers -----------------------------

def find_col(df: pd.DataFrame, candidates):
    cols = {c.lower(): c for c in df.columns}
    for cand in candidates:
        lc = cand.lower()
        if lc in cols:
            return cols[lc]
        norm = lc.replace(' ', '').replace('-', '')
        for k, v in cols.items():
            if k.replace(' ', '').replace('-', '') == norm:
                return v
    raise KeyError(f"Could not find any of columns {candidates} in {list(df.columns)}")


def parse_datetime_series(s: pd.Series) -> pd.Series:
    return pd.to_datetime(s, errors='coerce', utc=False)


def hhmm_from_minute(m: int) -> str:
    h = m // 60
    mi = m % 60
    return f"{h:02d}:{mi:02d}"


def auto_energy_to_kwh(energy_series: pd.Series) -> pd.Series:
    s = pd.to_numeric(energy_series, errors='coerce')
    med = s.dropna().median()
    if med is not None and med > 200:
        return s / 1000.0  # Wh -> kWh
    return s  # bereits kWh


def accumulate_interval_onto_profile(profile_kw: np.ndarray,
                                     start_ts: pd.Timestamp,
                                     end_ts: pd.Timestamp,
                                     rated_kw: float,
                                     energy_kwh: float):
    if pd.isna(start_ts) or pd.isna(end_ts) or end_ts <= start_ts:
        return
    if energy_kwh is None or rated_kw <= 0:
        return

    seconds_needed = (energy_kwh / rated_kw) * 3600.0
    if seconds_needed <= 0:
        return

    end_by_energy = start_ts + pd.to_timedelta(seconds_needed, unit='s')
    cutoff = min(end_ts, end_by_energy)
    if cutoff <= start_ts:
        return

    def add_segment(a: pd.Timestamp, b: pd.Timestamp):
        a_floor = a.floor('min')
        b_floor = b.floor('min')
        first_idx = int((a_floor.hour * 60) + a_floor.minute)
        last_idx = int((b_floor.hour * 60) + b_floor.minute)

        if a_floor == b_floor:
            frac = (b - a).total_seconds() / 60.0
            if 0 <= first_idx < 1440:
                profile_kw[first_idx] += rated_kw * min(max(frac, 0.0), 1.0)
            return

        first_frac = ((a_floor + pd.Timedelta(minutes=1)) - a).total_seconds() / 60.0
        if 0 <= first_idx < 1440:
            profile_kw[first_idx] += rated_kw * min(max(first_frac, 0.0), 1.0)

        for m in range(first_idx + 1, last_idx):
            if 0 <= m < 1440:
                profile_kw[m] += rated_kw

        if b != b_floor:
            last_frac = (b - b_floor).total_seconds() / 60.0
            if 0 <= last_idx < 1440:
                profile_kw[last_idx] += rated_kw * min(max(last_frac, 0.0), 1.0)

    t0 = start_ts
    t1 = cutoff

    if t0.normalize() == t1.normalize():
        add_segment(t0, t1)
    else:
        end_of_day = (t0.normalize() + pd.Timedelta(days=1))
        add_segment(t0, end_of_day - pd.Timedelta(microseconds=1))
        start_of_cutoff_day = t1.normalize()
        add_segment(start_of_cutoff_day, t1)


# ----------------------------- Core -----------------------------

def build_profile(in_csv: Path,
                  out_csv: Path,
                  out_hourly: Path | None,
                  rated_kw: float = 11.0):
    df = pd.read_csv(in_csv, dtype='object', engine='python')

    col_started = find_col(df, ['Started'])
    col_ended   = find_col(df, ['Ended'])
    col_energy  = find_col(df, ['Consumed Energy', 'ConsumedEnergy', 'Energy'])

    df['started_dt'] = parse_datetime_series(df[col_started])
    df['ended_dt']   = parse_datetime_series(df[col_ended])
    df['energy_kwh'] = auto_energy_to_kwh(df[col_energy])

    df = df.dropna(subset=['started_dt', 'ended_dt', 'energy_kwh'])
    df = df[df['ended_dt'] > df['started_dt']]
    df = df[df['energy_kwh'] > 0]

    profile = np.zeros(1440, dtype=float)
    for _, row in df.iterrows():
        start_ts   = row['started_dt']
        end_ts     = row['ended_dt']
        energy_kwh = float(row['energy_kwh'])
        accumulate_interval_onto_profile(profile, start_ts, end_ts, rated_kw, energy_kwh)

    out = pd.DataFrame({
        'minute_of_day': np.arange(1440, dtype=int),
        'time_hhmm': [hhmm_from_minute(i) for i in range(1440)],
        'power_kW': np.round(profile, 6)
    })
    out.to_csv(out_csv, index=False, encoding='utf-8-sig')

    hourly = None
    if out_hourly is not None:
        hourly = (out.assign(hour=lambda d: d['minute_of_day'] // 60)
                        .groupby('hour', as_index=False)['power_kW'].sum())
        hourly.rename(columns={'power_kW': 'power_kW_sum_per_hour'}, inplace=True)
        hourly.to_csv(out_hourly, index=False, encoding='utf-8-sig')

    return out, hourly


# ----------------------------- Plotting -----------------------------

def plot_profiles(minute_df: pd.DataFrame,
                  hourly_df: pd.DataFrame | None,
                  save_plots: bool,
                  plot_dir: Path,
                  show_plots: bool):
    matplotlib, plt = _lazy_import_matplotlib()
    plot_dir.mkdir(parents=True, exist_ok=True)

    # 1) Minutenprofil
    fig1, ax1 = plt.subplots(figsize=(12, 4))
    ax1.plot(minute_df['time_hhmm'], minute_df['power_kW'], color='#0078d4', lw=1.5)
    ax1.set_title('Charging Profile per Minute (0–24 h)')
    ax1.set_xlabel('Time of day (HH:MM)')
    ax1.set_ylabel('Power [kW] (minute-weighted)')
    # Weniger X-Ticks für Lesbarkeit
    xticks_idx = np.arange(0, 1440, 60)  # jede Stunde ein Tick
    ax1.set_xticks(xticks_idx)
    ax1.set_xticklabels([f"{h:02d}:00" for h in range(24)], rotation=0)
    ax1.grid(True, linestyle='--', alpha=0.3)
    fig1.tight_layout()

    if save_plots:
        f1 = plot_dir / 'work_charging_profile_minute.png'
        fig1.savefig(f1, dpi=150)
        print(f"Saved plot: {f1}")

    # 2) Stundensummen
    if hourly_df is not None:
        fig2, ax2 = plt.subplots(figsize=(12, 4))
        ax2.bar(hourly_df['hour'], hourly_df['power_kW_sum_per_hour'],
                color='#00b294', edgecolor='black', linewidth=0.6)
        ax2.set_title('Charging Profile per Hour (sum of kW over minutes)')
        ax2.set_xlabel('Hour of day')
        ax2.set_ylabel('Sum of power per hour [kW·min]')
        ax2.set_xticks(np.arange(0, 24, 1))
        ax2.grid(axis='y', linestyle='--', alpha=0.3)
        fig2.tight_layout()

        if save_plots:
            f2 = plot_dir / 'work_charging_profile_hourly.png'
            fig2.savefig(f2, dpi=150)
            print(f"Saved plot: {f2}")

        if show_plots:
            plt.show()
    else:
        if show_plots:
            plt.show()


# ----------------------------- CLI -----------------------------

def main2():
    ap = argparse.ArgumentParser()
    ap.add_argument('--in', dest='in_csv', required=True,
                    help='Pfad zur work_data.csv / over_all.csv')
    ap.add_argument('--out', dest='out_csv', default='work_charging_profile.csv',
                    help='Zieldatei (Minutenprofil)')
    ap.add_argument('--out_hourly', dest='out_hourly', default='work_charging_profile_hourly.csv',
                    help='Zieldatei (Stundensummen)')
    ap.add_argument('--rated_kw', type=float, default=11.0,
                    help='Konstante Ladeleistung in kW (Default: 11)')

    # Plot-Flags
    ap.add_argument('--plot', action='store_true',
                    help='Plotte das Minuten- und ggf. Stundenprofil')
    ap.add_argument('--save_plots', action='store_true',
                    help='Speichere PNG-Plots')
    ap.add_argument('--plot_dir', type=str, default='.',
                    help='Ordner, in den die Plots geschrieben werden (Default: aktueller Ordner)')

    args = ap.parse_args()

    in_csv = Path(args.in_csv)
    out_csv = Path(args.out_csv)
    out_hourly = Path(args.out_hourly) if args.out_hourly else None

    minute_df, hourly_df = build_profile(in_csv, out_csv, out_hourly, rated_kw=args.rated_kw)
    print(f"Wrote: {out_csv}")
    if out_hourly is not None:
        print(f"Wrote: {out_hourly}")

    if args.plot or args.save_plots:
        plot_profiles(minute_df, hourly_df, save_plots=args.save_plots,
                      plot_dir=Path(args.plot_dir), show_plots=args.plot)



if __name__ == '__main__':
    #main()
    main2()

