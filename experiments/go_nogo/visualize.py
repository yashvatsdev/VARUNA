"""
VARUNA Go/No-Go Experiment — Visualization
===========================================
Generates the key plots from sweep results:
  1. Accuracy-vs-Slick-Age curves (THE evidence slide)
  2. Accuracy-vs-Traffic-Density
  3. Heatmap grid (age × density)
  4. Single-trial Φ field visualization
"""

import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))


def set_style():
    """Set a clean, professional plot style."""
    plt.rcParams.update({
        'figure.facecolor': '#0d1117',
        'axes.facecolor': '#161b22',
        'text.color': '#e6edf3',
        'axes.labelcolor': '#e6edf3',
        'xtick.color': '#8b949e',
        'ytick.color': '#8b949e',
        'axes.edgecolor': '#30363d',
        'grid.color': '#21262d',
        'grid.alpha': 0.8,
        'font.family': 'sans-serif',
        'font.size': 11,
        'axes.titlesize': 14,
        'axes.labelsize': 12,
        'legend.fontsize': 10,
        'figure.dpi': 150,
    })


# ─── Plot 1: Accuracy vs Slick Age (THE KEY PLOT) ───────────────────────────

def plot_accuracy_vs_age(df: pd.DataFrame, output_dir: Path, n_vessels: int = 20):
    """
    Plot top-1 and top-3 accuracy vs slick age at a fixed traffic density.
    This is THE evidence slide for the demo.
    """
    set_style()
    subset = df[df['n_vessels'] == n_vessels]

    if subset.empty:
        # Fallback: use the closest available density
        available = sorted(df['n_vessels'].unique())
        n_vessels = min(available, key=lambda x: abs(x - 20))
        subset = df[df['n_vessels'] == n_vessels]

    agg = subset.groupby('slick_age_hours').agg(
        varuna_top1=('top1_correct', 'mean'),
        varuna_top3=('top3_correct', 'mean'),
        baseline=('baseline_correct', 'mean'),
        varuna_top1_std=('top1_correct', 'std'),
        baseline_std=('baseline_correct', 'std'),
        n=('trial_id', 'count'),
    ).reset_index()

    # Confidence intervals (95%)
    agg['varuna_ci'] = 1.96 * agg['varuna_top1_std'] / np.sqrt(agg['n'])
    agg['baseline_ci'] = 1.96 * agg['baseline_std'] / np.sqrt(agg['n'])

    fig, ax = plt.subplots(figsize=(10, 6))

    ages = agg['slick_age_hours']

    # VARUNA Top-1
    ax.plot(ages, agg['varuna_top1'] * 100, 'o-',
            color='#58a6ff', linewidth=2.5, markersize=8,
            label='VARUNA (Top-1)', zorder=5)
    ax.fill_between(ages,
                     (agg['varuna_top1'] - agg['varuna_ci']) * 100,
                     (agg['varuna_top1'] + agg['varuna_ci']) * 100,
                     alpha=0.2, color='#58a6ff')

    # VARUNA Top-3
    ax.plot(ages, agg['varuna_top3'] * 100, 's--',
            color='#7ee787', linewidth=2, markersize=7,
            label='VARUNA (Top-3)', zorder=4)

    # Baseline
    ax.plot(ages, agg['baseline'] * 100, 'D-.',
            color='#f85149', linewidth=2, markersize=7,
            label='Nearest-Vessel Baseline', zorder=3)
    ax.fill_between(ages,
                     (agg['baseline'] - agg['baseline_ci']) * 100,
                     (agg['baseline'] + agg['baseline_ci']) * 100,
                     alpha=0.15, color='#f85149')

    # Random guess line
    ax.axhline(y=100 / n_vessels, color='#484f58', linestyle=':',
               linewidth=1, label=f'Random guess (1/{n_vessels})')

    # The 24h reference line
    ax.axvline(x=24, color='#ffa657', linestyle='--', linewidth=1, alpha=0.5)
    ax.annotate('India\'s\noperational\ndefault', xy=(24, 5),
                fontsize=9, color='#ffa657', ha='center')

    ax.set_xlabel('Slick Age (hours)')
    ax.set_ylabel('Attribution Accuracy (%)')
    ax.set_title(f'Attribution Accuracy vs Slick Age\n({n_vessels} vessels, all forcing errors)',
                 fontweight='bold')
    ax.legend(loc='upper right', framealpha=0.8,
              facecolor='#161b22', edgecolor='#30363d')
    ax.set_xlim(0, max(ages) + 2)
    ax.set_ylim(0, 105)
    ax.grid(True, alpha=0.3)
    ax.set_xticks(ages)

    fig.tight_layout()
    save_path = output_dir / "accuracy_vs_age.png"
    fig.savefig(save_path, bbox_inches='tight')
    plt.close(fig)
    print(f"  Saved: {save_path}")


# ─── Plot 2: Accuracy vs Traffic Density ─────────────────────────────────────

def plot_accuracy_vs_density(df: pd.DataFrame, output_dir: Path,
                              slick_age: float = 24.0):
    """Plot accuracy vs number of vessels at a fixed slick age."""
    set_style()
    subset = df[df['slick_age_hours'] == slick_age]

    if subset.empty:
        available = sorted(df['slick_age_hours'].unique())
        slick_age = min(available, key=lambda x: abs(x - 24))
        subset = df[df['slick_age_hours'] == slick_age]

    agg = subset.groupby('n_vessels').agg(
        varuna_top1=('top1_correct', 'mean'),
        varuna_top3=('top3_correct', 'mean'),
        baseline=('baseline_correct', 'mean'),
    ).reset_index()

    fig, ax = plt.subplots(figsize=(10, 6))

    densities = agg['n_vessels']

    ax.plot(densities, agg['varuna_top1'] * 100, 'o-',
            color='#58a6ff', linewidth=2.5, markersize=8,
            label='VARUNA (Top-1)')
    ax.plot(densities, agg['varuna_top3'] * 100, 's--',
            color='#7ee787', linewidth=2, markersize=7,
            label='VARUNA (Top-3)')
    ax.plot(densities, agg['baseline'] * 100, 'D-.',
            color='#f85149', linewidth=2, markersize=7,
            label='Nearest-Vessel Baseline')

    # Random guess line (1/N)
    guess = [100 / n for n in densities]
    ax.plot(densities, guess, ':',
            color='#484f58', linewidth=1, label='Random guess (1/N)')

    # 20-vessel reference
    ax.axvline(x=20, color='#ffa657', linestyle='--', linewidth=1, alpha=0.5)
    ax.annotate('Target\ndensity', xy=(20, 5),
                fontsize=9, color='#ffa657', ha='center')

    ax.set_xlabel('Number of Vessels in Envelope')
    ax.set_ylabel('Attribution Accuracy (%)')
    ax.set_title(f'Attribution Accuracy vs Traffic Density\n'
                 f'(Slick age: {slick_age:.0f}h, all forcing errors)',
                 fontweight='bold')
    ax.legend(loc='upper right', framealpha=0.8,
              facecolor='#161b22', edgecolor='#30363d')
    ax.set_ylim(0, 105)
    ax.grid(True, alpha=0.3)
    ax.set_xticks(densities)

    fig.tight_layout()
    save_path = output_dir / "accuracy_vs_density.png"
    fig.savefig(save_path, bbox_inches='tight')
    plt.close(fig)
    print(f"  Saved: {save_path}")


# ─── Plot 3: Heatmap Grid ───────────────────────────────────────────────────

def plot_accuracy_heatmap(df: pd.DataFrame, output_dir: Path):
    """Plot a heatmap of top-1 accuracy across age × density."""
    set_style()

    agg = df.groupby(['slick_age_hours', 'n_vessels']).agg(
        varuna_top1=('top1_correct', 'mean'),
        baseline=('baseline_correct', 'mean'),
    ).reset_index()

    # Create pivot tables
    varuna_pivot = agg.pivot(index='n_vessels', columns='slick_age_hours',
                             values='varuna_top1')
    baseline_pivot = agg.pivot(index='n_vessels', columns='slick_age_hours',
                               values='baseline')
    delta_pivot = varuna_pivot - baseline_pivot

    fig, axes = plt.subplots(1, 3, figsize=(18, 5))

    for ax, data, title, cmap in [
        (axes[0], varuna_pivot, 'VARUNA Top-1 Accuracy', 'Blues'),
        (axes[1], baseline_pivot, 'Baseline (Nearest Vessel)', 'Reds'),
        (axes[2], delta_pivot, 'VARUNA − Baseline (Δ)', 'RdYlGn'),
    ]:
        im = ax.imshow(data.values, cmap=cmap, aspect='auto',
                        vmin=0 if 'Δ' not in title else -0.3,
                        vmax=1 if 'Δ' not in title else 0.5)

        # Annotate cells
        for i in range(data.shape[0]):
            for j in range(data.shape[1]):
                val = data.values[i, j]
                color = 'white' if val < 0.5 else 'black'
                if 'Δ' in title:
                    color = 'white' if abs(val) > 0.2 else 'black'
                ax.text(j, i, f'{val:.0%}', ha='center', va='center',
                        fontsize=10, fontweight='bold', color=color)

        ax.set_xticks(range(len(data.columns)))
        ax.set_xticklabels([f'{c:.0f}h' for c in data.columns])
        ax.set_yticks(range(len(data.index)))
        ax.set_yticklabels([f'{r:.0f}' for r in data.index])
        ax.set_xlabel('Slick Age')
        ax.set_ylabel('Vessels')
        ax.set_title(title, fontweight='bold')
        plt.colorbar(im, ax=ax, shrink=0.8)

    fig.suptitle('Go/No-Go Discriminability Grid', fontsize=16,
                 fontweight='bold', y=1.02)
    fig.tight_layout()

    save_path = output_dir / "accuracy_heatmap.png"
    fig.savefig(save_path, bbox_inches='tight')
    plt.close(fig)
    print(f"  Saved: {save_path}")


# ─── Plot 4: Single Trial Visualization ─────────────────────────────────────

def plot_single_trial(output_dir: Path, slick_age: float = 24.0, n_vessels: int = 20):
    """
    Run and visualize a single trial to show what Φ looks like.
    This is for debugging and understanding the mechanism.
    """
    from core import (
        CurrentField, WindField, simulate_release, run_backward_ensemble,
        build_phi_field, generate_guilty_track, generate_traffic,
        compute_posterior, nearest_vessel_baseline,
    )

    set_style()

    # Setup
    current = CurrentField(base_u=0.25, base_v=0.10)
    wind = WindField(base_u=-6.0, base_v=2.0)
    release_lon, release_lat = 72.0, 15.0
    release_time = 0.0
    obs_time = slick_age

    # Forward drift
    obs_lons, obs_lats = simulate_release(
        release_lon, release_lat, release_time, slick_age,
        n_particles=500, current=current, wind=wind,
    )

    # Backward ensemble
    ensemble = run_backward_ensemble(
        obs_lons, obs_lats, obs_time, slick_age * 1.3,
        n_particles_per_member=200, n_members=30,
        current=current, wind=wind,
        forcing_error_level="medium",
    )

    # Build Φ
    phi = build_phi_field(ensemble, bin_width_hours=max(0.5, slick_age / 10))

    # Generate tracks
    guilty = generate_guilty_track(release_lon, release_lat, release_time)
    innocent = generate_traffic(
        n_vessels - 1, release_lon, release_lat, 0.3,
        release_time - slick_age, obs_time + 6,
        release_lon, release_lat, release_time,
    )
    all_tracks = [guilty] + innocent

    # Score
    posterior = compute_posterior(all_tracks, phi)

    # ─── Visualize ───
    fig = plt.figure(figsize=(16, 10))
    gs = gridspec.GridSpec(2, 2, figure=fig, hspace=0.3, wspace=0.3)

    # Panel 1: Observed slick + vessel tracks
    ax1 = fig.add_subplot(gs[0, 0])
    ax1.scatter(obs_lons, obs_lats, s=1, c='#ffa657', alpha=0.5, label='Observed slick')
    ax1.plot(release_lon, release_lat, 'r*', markersize=15, zorder=10,
             label='True release point')

    for track in all_tracks:
        color = '#58a6ff' if track.is_guilty else '#484f58'
        lw = 2 if track.is_guilty else 0.8
        alpha = 1.0 if track.is_guilty else 0.4
        ax1.plot(track.lons, track.lats, color=color, linewidth=lw, alpha=alpha)

    ax1.set_title(f'Scene: {n_vessels} vessels, {slick_age:.0f}h old slick')
    ax1.set_xlabel('Longitude')
    ax1.set_ylabel('Latitude')
    ax1.legend(fontsize=8)

    # Panel 2: Backward particles (all ensemble members at the target time)
    ax2 = fig.add_subplot(gs[0, 1])
    for hist_lons, hist_lats, hist_times in ensemble:
        # Get particles at the time closest to release
        target_idx = np.argmin(np.abs(hist_times - release_time))
        ax2.scatter(hist_lons[:, target_idx], hist_lats[:, target_idx],
                    s=1, alpha=0.15, c='#58a6ff')

    ax2.plot(release_lon, release_lat, 'r*', markersize=15, zorder=10,
             label='True release')
    ax2.set_title(f'Backward particles at t=release ({30} members)')
    ax2.set_xlabel('Longitude')
    ax2.set_ylabel('Latitude')
    ax2.legend(fontsize=8)

    # Panel 3: Φ field as contour plot at release time
    ax3 = fig.add_subplot(gs[1, 0])
    # Evaluate Φ on a grid
    target_bin = np.argmin(np.abs(phi.time_bins - release_time))
    if target_bin in phi.kdes:
        # Get extent from backward particles
        all_bk_lons = []
        all_bk_lats = []
        for hist_lons, hist_lats, _ in ensemble:
            target_idx_2 = np.argmin(np.abs(hist_times - release_time))
            all_bk_lons.extend(hist_lons[:, target_idx_2])
            all_bk_lats.extend(hist_lats[:, target_idx_2])

        lon_min, lon_max = min(all_bk_lons), max(all_bk_lons)
        lat_min, lat_max = min(all_bk_lats), max(all_bk_lats)
        margin = max(lon_max - lon_min, lat_max - lat_min) * 0.2
        lon_min -= margin
        lon_max += margin
        lat_min -= margin
        lat_max += margin

        grid_lon = np.linspace(lon_min, lon_max, 100)
        grid_lat = np.linspace(lat_min, lat_max, 100)
        LON, LAT = np.meshgrid(grid_lon, grid_lat)
        positions = np.vstack([LON.ravel(), LAT.ravel()])

        try:
            Z = phi.kdes[target_bin](positions).reshape(100, 100)
            contour = ax3.contourf(LON, LAT, Z, levels=30, cmap='hot')
            plt.colorbar(contour, ax=ax3, label='Φ density')
        except Exception:
            ax3.text(0.5, 0.5, 'KDE evaluation failed',
                     transform=ax3.transAxes, ha='center')

    ax3.plot(release_lon, release_lat, 'c*', markersize=15, zorder=10,
             label='True release')
    for track in all_tracks:
        color = '#58a6ff' if track.is_guilty else '#484f58'
        lw = 2 if track.is_guilty else 0.5
        alpha = 1.0 if track.is_guilty else 0.3
        ax3.plot(track.lons, track.lats, color=color, linewidth=lw, alpha=alpha)
    ax3.set_title('Φ field at release time + vessel tracks')
    ax3.set_xlabel('Longitude')
    ax3.set_ylabel('Latitude')
    ax3.legend(fontsize=8)

    # Panel 4: Posterior bar chart
    ax4 = fig.add_subplot(gs[1, 1])
    sorted_posterior = sorted(posterior.items(), key=lambda x: x[1], reverse=True)
    top_k = sorted_posterior[:10]  # show top 10
    names = [p[0] for p in top_k]
    probs = [p[1] for p in top_k]
    colors = ['#58a6ff' if n == 'GUILTY' else
              '#ffa657' if n == 'LATENT_SOURCE' else
              '#484f58' for n in names]

    bars = ax4.barh(range(len(names)), probs, color=colors)
    ax4.set_yticks(range(len(names)))
    ax4.set_yticklabels(names, fontsize=9)
    ax4.set_xlabel('Posterior Probability')
    ax4.set_title('Attribution Posterior (top 10)')
    ax4.invert_yaxis()

    # Add value labels
    for bar, prob in zip(bars, probs):
        ax4.text(bar.get_width() + 0.01, bar.get_y() + bar.get_height()/2,
                 f'{prob:.3f}', va='center', fontsize=9, color='#e6edf3')

    fig.suptitle(f'VARUNA Go/No-Go — Single Trial Visualization\n'
                 f'Slick age: {slick_age:.0f}h | Vessels: {n_vessels} | '
                 f'Forcing error: medium',
                 fontsize=14, fontweight='bold')

    save_path = output_dir / "single_trial_visualization.png"
    fig.savefig(save_path, bbox_inches='tight')
    plt.close(fig)
    print(f"  Saved: {save_path}")


# ─── Plot 5: Forcing Error Comparison ────────────────────────────────────────

def plot_forcing_error_effect(df: pd.DataFrame, output_dir: Path,
                               n_vessels: int = 20):
    """Show how forcing error level affects accuracy."""
    set_style()
    subset = df[df['n_vessels'] == n_vessels]

    if subset.empty:
        available = sorted(df['n_vessels'].unique())
        n_vessels = min(available, key=lambda x: abs(x - 20))
        subset = df[df['n_vessels'] == n_vessels]

    fig, ax = plt.subplots(figsize=(10, 6))

    colors = {'low': '#7ee787', 'medium': '#58a6ff', 'high': '#f85149'}

    for error_level in ['low', 'medium', 'high']:
        sub = subset[subset['forcing_error'] == error_level]
        if sub.empty:
            continue
        agg = sub.groupby('slick_age_hours').agg(
            acc=('top1_correct', 'mean'),
        ).reset_index()
        ax.plot(agg['slick_age_hours'], agg['acc'] * 100, 'o-',
                color=colors[error_level], linewidth=2, markersize=7,
                label=f'Forcing error: {error_level}')

    ax.set_xlabel('Slick Age (hours)')
    ax.set_ylabel('Top-1 Accuracy (%)')
    ax.set_title(f'Effect of Forcing Error on Attribution\n({n_vessels} vessels)',
                 fontweight='bold')
    ax.legend(framealpha=0.8, facecolor='#161b22', edgecolor='#30363d')
    ax.set_ylim(0, 105)
    ax.grid(True, alpha=0.3)

    fig.tight_layout()
    save_path = output_dir / "forcing_error_effect.png"
    fig.savefig(save_path, bbox_inches='tight')
    plt.close(fig)
    print(f"  Saved: {save_path}")


# ─── Main ────────────────────────────────────────────────────────────────────

def generate_all_plots(results_dir: Path):
    """Generate all plots from saved sweep results."""
    csv_path = results_dir / "sweep_results.csv"

    if not csv_path.exists():
        print(f"  ERROR: {csv_path} not found. Run sweep.py first.")
        return

    df = pd.read_csv(csv_path)
    print(f"\n  Loaded {len(df)} trial results from {csv_path}")
    print(f"  Generating plots...\n")

    plot_accuracy_vs_age(df, results_dir)
    plot_accuracy_vs_density(df, results_dir)

    if len(df['slick_age_hours'].unique()) > 1 and len(df['n_vessels'].unique()) > 1:
        plot_accuracy_heatmap(df, results_dir)

    if len(df['forcing_error'].unique()) > 1:
        plot_forcing_error_effect(df, results_dir)

    # Single trial visualization
    print(f"  Running single trial visualization...")
    plot_single_trial(results_dir)

    print(f"\n  All plots saved to: {results_dir}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Generate go/no-go plots")
    parser.add_argument("--results-dir", type=str, default=None,
                        help="Directory containing sweep_results.csv")
    args = parser.parse_args()

    if args.results_dir:
        results_dir = Path(args.results_dir)
    else:
        # Look for most recent results
        base = Path(__file__).parent / "results"
        if (base / "full_sweep").exists():
            results_dir = base / "full_sweep"
        elif (base / "quick_test").exists():
            results_dir = base / "quick_test"
        else:
            print("No results found. Run sweep.py first.")
            sys.exit(1)

    generate_all_plots(results_dir)
