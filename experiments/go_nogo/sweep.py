"""
VARUNA Go/No-Go Experiment — Parameter Sweep
=============================================
Runs the full slick_age × traffic_density × forcing_error grid
with Monte Carlo repetitions, and saves results as CSV.
"""

import sys
import time
import json
import numpy as np
import pandas as pd
from pathlib import Path
from dataclasses import asdict
from concurrent.futures import ProcessPoolExecutor, as_completed

# Add parent to path for import
sys.path.insert(0, str(Path(__file__).parent))
from core import run_single_trial, TrialResult


# ─── Sweep Configuration ────────────────────────────────────────────────────

SWEEP_CONFIG = {
    # The parameter grid
    "slick_ages_hours": [2, 6, 12, 24, 48],
    "traffic_densities": [5, 10, 20, 50],
    "forcing_errors": ["low", "medium", "high"],

    # Monte Carlo repetitions per cell
    "trials_per_cell": 50,  # Start with 50, increase to 100 if results are noisy

    # Physics parameters (fixed across sweep)
    "n_forward_particles": 500,
    "n_backward_particles_per_member": 200,
    "n_ensemble_members": 30,
    "dt_seconds": 900.0,  # 15-minute timesteps

    # Release location (arbitrary — results should be location-independent
    # for synthetic uniform currents)
    "release_lon": 72.0,
    "release_lat": 15.0,
}

# Quick test config — use this first to verify everything works
QUICK_TEST_CONFIG = {
    "slick_ages_hours": [6, 24],
    "traffic_densities": [5, 20],
    "forcing_errors": ["medium"],
    "trials_per_cell": 5,
    "n_forward_particles": 300,
    "n_backward_particles_per_member": 100,
    "n_ensemble_members": 15,
    "dt_seconds": 900.0,
    "release_lon": 72.0,
    "release_lat": 15.0,
}


# ─── Worker Function ────────────────────────────────────────────────────────

def run_trial_worker(args):
    """Worker function for parallel execution."""
    slick_age, n_vessels, forcing_error, trial_id, config = args

    try:
        result = run_single_trial(
            slick_age_hours=slick_age,
            n_vessels=n_vessels,
            forcing_error=forcing_error,
            trial_id=trial_id,
            release_lon=config["release_lon"],
            release_lat=config["release_lat"],
            n_forward_particles=config["n_forward_particles"],
            n_backward_particles_per_member=config["n_backward_particles_per_member"],
            n_ensemble_members=config["n_ensemble_members"],
            dt_seconds=config["dt_seconds"],
        )

        return {
            "slick_age_hours": result.slick_age_hours,
            "n_vessels": result.n_vessels,
            "forcing_error": result.forcing_error,
            "trial_id": result.trial_id,
            "top1_correct": result.top1_correct,
            "top3_correct": result.top3_correct,
            "baseline_correct": result.baseline_correct,
            "guilty_rank": result.guilty_rank,
            "guilty_probability": result.guilty_probability,
            "latent_probability": result.latent_probability,
            "top1_name": result.top1_name,
        }
    except Exception as e:
        return {
            "slick_age_hours": slick_age,
            "n_vessels": n_vessels,
            "forcing_error": forcing_error,
            "trial_id": trial_id,
            "error": str(e),
        }


# ─── Main Sweep ─────────────────────────────────────────────────────────────

def run_sweep(config: dict, output_dir: Path, max_workers: int = 4):
    """
    Run the full parameter sweep.

    Args:
        config: sweep configuration dict
        output_dir: directory to save results
        max_workers: number of parallel workers
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # Build the list of all trials
    trials = []
    for slick_age in config["slick_ages_hours"]:
        for n_vessels in config["traffic_densities"]:
            for forcing_error in config["forcing_errors"]:
                for trial_id in range(config["trials_per_cell"]):
                    trials.append((slick_age, n_vessels, forcing_error, trial_id, config))

    total = len(trials)
    print(f"\n{'='*70}")
    print(f"  VARUNA Go/No-Go Discriminability Sweep")
    print(f"  {len(config['slick_ages_hours'])} ages × "
          f"{len(config['traffic_densities'])} densities × "
          f"{len(config['forcing_errors'])} error levels × "
          f"{config['trials_per_cell']} trials = {total} total runs")
    print(f"  Workers: {max_workers}")
    print(f"{'='*70}\n")

    results = []
    errors = 0
    start_time = time.time()

    # Run trials (sequential for now — can parallelise later)
    # Note: ProcessPoolExecutor has overhead on Windows. For quick test,
    # sequential is often faster. For full sweep, enable parallel.
    use_parallel = total > 50

    if use_parallel and max_workers > 1:
        print(f"  Running {total} trials in parallel ({max_workers} workers)...\n")
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(run_trial_worker, t): t for t in trials}
            for i, future in enumerate(as_completed(futures), 1):
                result = future.result()
                if "error" in result:
                    errors += 1
                    print(f"  [{i}/{total}] ERROR: {result['error']}")
                else:
                    results.append(result)
                    if i % 10 == 0 or i == total:
                        elapsed = time.time() - start_time
                        rate = i / elapsed
                        eta = (total - i) / rate if rate > 0 else 0
                        correct = result['top1_correct']
                        marker = "✓" if correct else "✗"
                        print(f"  [{i}/{total}] age={result['slick_age_hours']}h "
                              f"vessels={result['n_vessels']} "
                              f"error={result['forcing_error']} "
                              f"{marker} "
                              f"({elapsed:.0f}s elapsed, ~{eta:.0f}s remaining)")
    else:
        print(f"  Running {total} trials sequentially...\n")
        for i, trial in enumerate(trials, 1):
            result = run_trial_worker(trial)
            if "error" in result:
                errors += 1
                print(f"  [{i}/{total}] ERROR: {result['error']}")
            else:
                results.append(result)
                if i % 5 == 0 or i == total:
                    elapsed = time.time() - start_time
                    rate = i / elapsed
                    eta = (total - i) / rate if rate > 0 else 0
                    correct = result['top1_correct']
                    marker = "✓" if correct else "✗"
                    print(f"  [{i}/{total}] age={result['slick_age_hours']}h "
                          f"vessels={result['n_vessels']} "
                          f"error={result['forcing_error']} "
                          f"{marker} "
                          f"({elapsed:.0f}s elapsed, ~{eta:.0f}s remaining)")

    elapsed = time.time() - start_time

    # Save results
    df = pd.DataFrame(results)
    csv_path = output_dir / "sweep_results.csv"
    df.to_csv(csv_path, index=False)
    print(f"\n  Results saved to: {csv_path}")
    print(f"  Total time: {elapsed:.1f}s ({elapsed/60:.1f} min)")
    print(f"  Trials completed: {len(results)}, errors: {errors}")

    # Print quick summary
    print_summary(df)

    return df


def print_summary(df: pd.DataFrame):
    """Print a quick summary of results to the console."""
    print(f"\n{'='*70}")
    print(f"  QUICK SUMMARY — Top-1 Accuracy (VARUNA vs Baseline)")
    print(f"{'='*70}\n")

    # Aggregate by slick_age and n_vessels (averaging over forcing error)
    pivot = df.groupby(["slick_age_hours", "n_vessels"]).agg(
        varuna_top1=("top1_correct", "mean"),
        varuna_top3=("top3_correct", "mean"),
        baseline=("baseline_correct", "mean"),
        avg_guilty_prob=("guilty_probability", "mean"),
        avg_guilty_rank=("guilty_rank", "mean"),
        n_trials=("trial_id", "count"),
    ).reset_index()

    # Print as table
    print(f"  {'Age':>5}  {'Vessels':>7}  {'VARUNA Top-1':>12}  {'VARUNA Top-3':>12}  "
          f"{'Baseline':>8}  {'Δ':>6}  {'Avg Rank':>8}  {'Avg P(guilty)':>13}")
    print(f"  {'─'*5}  {'─'*7}  {'─'*12}  {'─'*12}  {'─'*8}  {'─'*6}  {'─'*8}  {'─'*13}")

    for _, row in pivot.iterrows():
        delta = row['varuna_top1'] - row['baseline']
        delta_str = f"+{delta:.0%}" if delta >= 0 else f"{delta:.0%}"
        marker = "★" if delta > 0.1 else ("≈" if abs(delta) < 0.05 else "▼")

        print(f"  {row['slick_age_hours']:5.0f}h  {row['n_vessels']:7.0f}  "
              f"{row['varuna_top1']:12.1%}  {row['varuna_top3']:12.1%}  "
              f"{row['baseline']:8.1%}  {delta_str:>5} {marker} "
              f"{row['avg_guilty_rank']:8.1f}  {row['avg_guilty_prob']:13.3f}")

    # The go/no-go number
    key_row = pivot[
        (pivot['slick_age_hours'] == 24) &
        (pivot['n_vessels'] == 20)
    ]
    if not key_row.empty:
        acc = key_row['varuna_top1'].values[0]
        base = key_row['baseline'].values[0]
        print(f"\n  {'='*70}")
        print(f"  ★ KEY METRIC: Top-1 at 24h / 20 vessels = {acc:.1%} "
              f"(baseline: {base:.1%})")
        if acc >= 0.5:
            print(f"  ★ DECISION: GO ✅ — posterior is discriminative!")
        elif acc >= 0.25:
            print(f"  ⚠ DECISION: CONDITIONAL — try emission priors to boost")
        else:
            print(f"  ✗ DECISION: NO-GO ❌ — posterior is flat, pivot needed")
        print(f"  {'='*70}")
    else:
        print(f"\n  (Key metric cell 24h/20v not found in this sweep)")


# ─── Entry Point ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="VARUNA Go/No-Go Sweep")
    parser.add_argument("--quick", action="store_true",
                        help="Run quick test (2 ages × 2 densities × 5 trials)")
    parser.add_argument("--full", action="store_true",
                        help="Run full sweep (5×4×3×50 = 3000 trials)")
    parser.add_argument("--workers", type=int, default=1,
                        help="Number of parallel workers (default: 1)")
    parser.add_argument("--output", type=str, default=None,
                        help="Output directory")
    args = parser.parse_args()

    if args.quick:
        config = QUICK_TEST_CONFIG
        label = "quick_test"
    elif args.full:
        config = SWEEP_CONFIG
        label = "full_sweep"
    else:
        # Default: quick test
        config = QUICK_TEST_CONFIG
        label = "quick_test"

    output_dir = Path(args.output) if args.output else Path(__file__).parent / "results" / label
    run_sweep(config, output_dir, max_workers=args.workers)
