# Comparative Analysis: Urban Intersection vs Freeway

This report parses Task 1 and Task 2 simulation_results.md files and compares key metrics across configurations and densities.

## SMRavg — Statistical Comparison

- Urban: mean=67.5535, median=69.26, p95=70.422, max=71.35
- Freeway: mean=63.6682, median=64.53, p95=65.676, max=65.86

## NoM_Mean — Statistical Comparison

- Urban: mean=0.250993, median=0.241755, p95=0.31841, max=0.338324
- Freeway: mean=0.37869, median=0.386694, p95=0.44935, max=0.505792

## NoM_P95 — Statistical Comparison

- Urban: mean=0.905892, median=0.899998, p95=1.32, max=1.4
- Freeway: mean=1.25294, median=1.2, p95=1.82, max=1.9

## E2E_Avg — Statistical Comparison

- Urban: mean=0.0459469, median=0.062201, p95=0.0708534, max=0.078455
- Freeway: mean=0.000122471, median=0.000122, p95=0.0001312, max=0.000132

## E2E_Max — Statistical Comparison

- Urban: mean=61.3398, median=83.0539, p95=86.2825, max=87.2747
- Freeway: mean=0.000381294, median=0.000389, p95=0.00061, max=0.00061

## CAD_Avg — Statistical Comparison

- Urban: mean=1.65706e-05, median=1.73956e-05, p95=2.157e-05, max=2.4691e-05
- Freeway: mean=1.5233e-05, median=1.49357e-05, p95=2.24843e-05, max=2.38576e-05

## CAD_P95 — Statistical Comparison

- Urban: mean=9.34536e-05, median=0.000103929, p95=0.000143968, max=0.000147588
- Freeway: mean=8.11081e-05, median=9.94461e-05, p95=0.000134527, max=0.000143547

## Distribution comparison (CDF across configs)

- See plot: cdf_comparison_across_configs.png
- We compare tails using per-config 95th-percentile/worst-case metrics. Heavier right tails indicate larger delays or gaps in some configurations.

## Density impact

- See density trend plots: density_vs_smr.png, density_vs_nom_mean.png, density_vs_e2e_avg.png, density_vs_cad_avg.png
- See also differences_vs_density.png for Urban–Freeway deltas vs density.

## Saturation indicators

- Largest negative SMR slope (Urban): -0.661538 at density ≈ 13.6
- Largest negative SMR slope (Freeway): -0.678571 at density ≈ 8.4
- Max adjacent increase in NoM mean (Urban): 0.113709
- Max adjacent increase in NoM mean (Freeway): 0.167234
- Avg E2E Max (tail proxy): Urban=61.3398, Freeway=0.000381294
- Avg CAD 95th (tail proxy): Urban=9.34536e-05, Freeway=8.11081e-05

## Discussion

- Which scenario achieves higher SMR at similar densities? Urban consistently shows higher SMRavg across matching configs.
- Mobility patterns: Urban stop–go tends to keep NoM mean lower than Freeway at high densities (shorter inter-message gaps), while Freeway exhibits larger NoM tails in several configs.
- CAD contribution: Freeway often shows similar or slightly lower CAD 95th at low densities, but higher CAD_avg near certain configs with heavier load; E2E tails are generally much larger in Urban (due to application/logging scale), though note the units and interpretation differ between scenarios (Urban E2E values are larger-scale).
- Scalability limit: Freeway SMR degrades earlier with increasing density compared to Urban, indicating stricter scalability for IEEE 802.11p under continuous-flow mobility.

### Files generated

- cdf_comparison_across_configs.png
- density_vs_smr.png
- density_vs_nom_mean.png
- density_vs_e2e_avg.png
- density_vs_cad_avg.png
- differences_vs_density.png
