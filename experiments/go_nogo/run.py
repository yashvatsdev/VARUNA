"""
VARUNA Go/No-Go Experiment — Main Entry Point
==============================================

Run this file to execute the entire go/no-go experiment.

Usage:
    python run.py              # Quick test (20 trials, ~2 min)
    python run.py --full       # Full sweep (3000 trials, ~2-4 hours)
    python run.py --visualize  # Generate plots from saved results

The quick test runs 2 slick ages × 2 densities × 5 trials to verify
everything works. The full sweep runs the complete 5×4×3×50 grid.
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))


def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="VARUNA Go/No-Go Discriminability Experiment",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run.py                  Quick test (~2 min)
  python run.py --full           Full sweep (~2-4 hours)
  python run.py --visualize      Generate plots from saved results
  python run.py --single         Run and visualize a single trial
        """
    )
    parser.add_argument("--quick", action="store_true", default=True,
                        help="Run quick test (default)")
    parser.add_argument("--full", action="store_true",
                        help="Run full 3000-trial sweep")
    parser.add_argument("--visualize", action="store_true",
                        help="Only generate plots from existing results")
    parser.add_argument("--single", action="store_true",
                        help="Run and visualize a single trial")
    parser.add_argument("--workers", type=int, default=1,
                        help="Parallel workers for sweep")
    args = parser.parse_args()

    print()
    print("=" * 62)
    print("  VARUNA GRID -- Go/No-Go Discriminability Experiment")
    print("  SIH 2026 | SIH26143 | Week 1 Proof")
    print("=" * 62)
    print()

    base_dir = Path(__file__).parent

    if args.single:
        print("  Mode: Single trial visualization")
        print("  Running one trial with slick_age=24h, 20 vessels...\n")
        from visualize import plot_single_trial
        output_dir = base_dir / "results" / "single_trial"
        output_dir.mkdir(parents=True, exist_ok=True)
        plot_single_trial(output_dir, slick_age=24.0, n_vessels=20)
        print(f"\n  Done! Check: {output_dir}")
        return

    if args.visualize:
        print("  Mode: Generate plots from existing results\n")
        from visualize import generate_all_plots
        if args.full:
            results_dir = base_dir / "results" / "full_sweep"
        else:
            results_dir = base_dir / "results" / "quick_test"
        generate_all_plots(results_dir)
        return

    # Run sweep
    from sweep import run_sweep, SWEEP_CONFIG, QUICK_TEST_CONFIG
    from visualize import generate_all_plots

    if args.full:
        config = SWEEP_CONFIG
        label = "full_sweep"
        print("  Mode: FULL SWEEP")
        print("  5 ages × 4 densities × 3 error levels × 50 trials = 3,000 runs")
        print("  Estimated time: 2-4 hours\n")
    else:
        config = QUICK_TEST_CONFIG
        label = "quick_test"
        print("  Mode: QUICK TEST")
        print("  2 ages × 2 densities × 1 error level × 5 trials = 20 runs")
        print("  Estimated time: 2-5 minutes\n")

    output_dir = base_dir / "results" / label

    # Run the sweep
    start = time.time()
    df = run_sweep(config, output_dir, max_workers=args.workers)
    elapsed = time.time() - start

    # Generate plots
    print(f"\n  Generating plots...")
    generate_all_plots(output_dir)

    print(f"\n{'='*60}")
    print(f"  EXPERIMENT COMPLETE")
    print(f"  Total time: {elapsed:.1f}s ({elapsed/60:.1f} min)")
    print(f"  Results: {output_dir / 'sweep_results.csv'}")
    print(f"  Plots:   {output_dir}")
    print(f"{'='*60}")

    # Final go/no-go advice
    if 24 in df['slick_age_hours'].values and 20 in df['n_vessels'].values:
        key = df[(df['slick_age_hours'] == 24) & (df['n_vessels'] == 20)]
        if not key.empty:
            acc = key['top1_correct'].mean()
            base = key['baseline_correct'].mean()
            print(f"\n  ★ KEY RESULT: Top-1 at 24h/20v = {acc:.1%} (baseline: {base:.1%})")
            if acc >= 0.5:
                print(f"  ★ RECOMMENDATION: GO ✅ — Proceed with full RDPA implementation")
            elif acc >= 0.25:
                print(f"  ⚠ RECOMMENDATION: CONDITIONAL — Add emission priors, re-test")
            else:
                print(f"  ✗ RECOMMENDATION: NO-GO ❌ — Consider pivot")
    print()


if __name__ == "__main__":
    main()
