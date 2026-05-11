#!/bin/bash
#SBATCH -J desi-outliers
#SBATCH -A desi
#SBATCH -C cpu
#SBATCH -q regular
#SBATCH -t 4:00:00
#SBATCH -N 1
#SBATCH -c 128
#SBATCH --mem=0
#SBATCH -o logs/slurm-%j.out
#SBATCH -e logs/slurm-%j.err
#SBATCH --open-mode=append

module load python

cd /pscratch/sd/f/forero/desi-outliers

srun -n 1 python scripts/plot_outliers_by_program.py
srun -n 1 python scripts/plot_outliers_by_fiber.py
srun -n 1 python scripts/plot_outliers_per_tile.py
srun -n 1 python scripts/plot_outliers_per_petal.py
srun -n 1 python scripts/plot_outliers_by_radius_loa.py
srun -n 1 python scripts/plot_outliers_by_radius_per_petal_loa.py
srun -n 1 python scripts/plot_outlier_overlap_loa_matterhorn.py
srun -n 1 python scripts/plot_outlier_fraction_vs_qa_per_fiber_loa.py
srun -n 1 python scripts/plot_qa_correlation_per_petal_loa.py
srun -n 1 python scripts/plot_bad_petal_vs_outliers_loa.py
srun -n 1 python scripts/plot_tsnr_vs_outliers_loa.py dark
srun -n 1 python scripts/plot_tsnr_vs_outliers_loa.py bright
srun -n 1 python scripts/plot_tsnr_vs_outliers_loa.py backup
srun -n 1 python scripts/plot_outliers_per_month_matterhorn.py
srun -n 1 python scripts/plot_outliers_heatmap_month_petal_matterhorn.py
srun -n 1 python scripts/make_dark_common_outliers_html.py
srun -n 1 python scripts/make_high_outlier_fibers_html.py
