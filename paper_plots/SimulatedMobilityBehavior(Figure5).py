import argparse
import os
import shutil
from pathlib import Path

import matplotlib.pyplot as plt

from helper_files.trip_chain_validation import trip_chain_validation


def resolve_model_base(model_arg: str) -> Path:
    p = Path(model_arg)
    if p.suffix == ".pkl":
        p = p.with_suffix("")
    if p.with_suffix(".pkl").exists():
        return p
    raise FileNotFoundError(f"Model file not found: {model_arg}")


def save_all_open_figures(output_dir: Path, prefix: str = "tripchain"):
    output_dir.mkdir(parents=True, exist_ok=True)
    fig_nums = plt.get_fignums()
    saved = []

    def _has_content(fig):
        if len(fig.axes) == 0:
            return False
        for ax in fig.axes:
            if ax.has_data():
                return True
            if len(ax.texts) > 0:
                return True
            if len(ax.images) > 0:
                return True
        return False

    for idx, fig_num in enumerate(fig_nums, start=1):
        fig = plt.figure(fig_num)
        # Always save the last figure as tripchain_10.png, even if empty
        if idx == len(fig_nums):
            out_file = output_dir / f"{prefix}_10.png"
            fig.savefig(out_file, dpi=300, bbox_inches="tight")
            fig.savefig("paper_plots/figures/trip_chain_validation_Figure5", dpi=300, bbox_inches="tight")
            saved.append(out_file)
        else:
            if not _has_content(fig):
                continue
            out_file = output_dir / f"{prefix}_{idx:02d}.png"
            fig.savefig(out_file, dpi=220, bbox_inches="tight")
            saved.append(out_file)

    return saved


def run_validation_with_model(
    model_base: Path | None,
    show_plots: bool,
    output_dir: Path,
    with_region_type: bool,
):
    # Change to parent directory (project root) to ensure correct relative paths for imports and config files
    project_root = Path(__file__).parent.parent
    original_cwd = Path.cwd()
    
    # Convert output_dir to absolute path BEFORE changing cwd
    output_dir = output_dir.resolve() if output_dir.is_absolute() else (original_cwd / output_dir).resolve()
    
    os.chdir(project_root)
    
    default_model = Path("scenarioC1")
    default_model_pkl = default_model.with_suffix(".pkl")
    backup_model_pkl = Path("model_tripchain2_backup.pkl")

    replaced_default = False

    try:
        if model_base is not None:
            src_pkl = model_base.with_suffix(".pkl")
            if default_model_pkl.exists():
                shutil.copy2(default_model_pkl, backup_model_pkl)
            shutil.copy2(src_pkl, default_model_pkl)
            replaced_default = True
            print(f"Using model for validation: {src_pkl}")

        if not show_plots:
            original_show = plt.show
            plt.show = lambda *args, **kwargs: None
        else:
            original_show = None

        # Enable broad plot coverage but keep dist_of_Purposes=False to avoid undefined legacy helper.
        # withregionType can fail for unexpected region ids in legacy data; keep it optional.
        try:
            trip_chain_validation(
                withregionType=with_region_type,
                parking_times_plot=True,
                plot_hist_distances=True,
                plot_driving=True,
                print_parking_time_on_day=True,
                dist_of_Purposes=False,
                share_of_Purposes=True,
                print_parking_duration=True,
            )
        except IndexError as exc:
            if with_region_type:
                print(
                    "Region-type plots failed with IndexError (legacy region ids). "
                    "Retrying without withregionType..."
                )
                trip_chain_validation(
                    withregionType=False,
                    parking_times_plot=True,
                    plot_hist_distances=True,
                    plot_driving=True,
                    print_parking_time_on_day=True,
                    dist_of_Purposes=False,
                    share_of_Purposes=True,
                    print_parking_duration=True,
                )
            else:
                raise exc

        # Modify the last figure (fig 10) BEFORE saving - remove x-axis labels and reposition legend
        all_figs = plt.get_fignums()
        if all_figs:
            last_fig = plt.figure(all_figs[-1])
            # Remove x-axis tick labels from all subplots
            for ax in last_fig.axes:
                ax.set_xticklabels([])
            
            # Reduce zorder of all lines in all subplots so legend appears on top
            for ax in last_fig.axes:
                for line in ax.get_lines():
                    line.set_zorder(1)
                ax.set_axisbelow(True)
                # Remove any existing legends
                if ax.get_legend():
                    ax.get_legend().remove()
            
            # Create a single legend using handles and labels from first subplot
            if last_fig.axes:
                first_ax = last_fig.axes[0]
                handles, labels = first_ax.get_legend_handles_labels()
                
                # Filter out "Home" from the legend
                filtered_handles = []
                filtered_labels = []
                for handle, label in zip(handles, labels):
                    if label != "Home":
                        filtered_handles.append(handle)
                        filtered_labels.append(label)
                
                # Add legend to the figure (not a subplot) - this ensures it's on top
                leg = last_fig.legend(
                    handles=filtered_handles,
                    labels=filtered_labels,
                    title="Driving / Parking after trip purpose",
                    loc='upper center',
                    ncol=5,
                    frameon=True,
                    fontsize=24,
                    title_fontsize=28,
                    framealpha=1.0,
                    fancybox=True,
                    shadow=True,
                    bbox_to_anchor=(0.5, 0.87),
                )
                # Set extremely high z-order
                leg.set_zorder(10000)
                leg.get_frame().set_zorder(10000)
                for text in leg.get_texts():
                    text.set_zorder(10000)
                leg.get_title().set_zorder(10000)

        saved = save_all_open_figures(output_dir=output_dir)
        
        print(f"Saved {len(saved)} plot(s) to {output_dir}")
        for file in saved:
            print(f"  - {file}")

    finally:
        if not show_plots and 'original_show' in locals() and original_show is not None:
            plt.show = original_show

        if replaced_default:
            if backup_model_pkl.exists():
                shutil.copy2(backup_model_pkl, default_model_pkl)
                backup_model_pkl.unlink(missing_ok=True)
            else:
                default_model_pkl.unlink(missing_ok=True)
        
        # Restore original working directory
        if 'original_cwd' in locals():
            os.chdir(original_cwd)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run trip chain validation with broad plotting and save all generated figures."
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Optional model path/prefix (.pkl optional). If set, temporarily used as default 'model.pkl'.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("../figures/tripchain_validation2"),
        help="Directory where generated plots are saved.",
    )
    parser.add_argument(
        "--show",
        action="store_true",
        help="Show plots interactively in addition to saving.",
    )
    parser.add_argument(
        "--with-region-type",
        action="store_true",
        help="Include legacy region-type plots (can fail on inconsistent region ids).",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    model_base = resolve_model_base(args.model) if args.model else None
    run_validation_with_model(
        model_base=model_base,
        show_plots=args.show,
        output_dir=args.output_dir,
        with_region_type=args.with_region_type,
    )


if __name__ == "__main__":
    main()
