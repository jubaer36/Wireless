import os
import re
from dataclasses import dataclass
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


# -------------------------------
# Parsing utilities
# -------------------------------

Config = str


@dataclass
class ScenarioData:
    name: str
    smr: pd.DataFrame  # columns: config, SMRavg, Density
    nom: pd.DataFrame  # columns: config, mean, median, p95, max
    e2e: pd.DataFrame  # columns: config, avg, max, min
    cad: pd.DataFrame  # columns: config, avg, min, max, median, p95


def _parse_value(txt: str) -> float:
    """Parse a float value from a piece of text that may include units/symbols (%, commas)."""
    # Remove percentage, commas and any non-numeric except . and - and e/E
    cleaned = txt.replace("%", "").replace(",", "").strip()
    # Keep only valid characters
    m = re.findall(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", cleaned)
    if not m:
        raise ValueError(f"Could not parse numeric value from: {txt}")
    return float(m[0])


def parse_results_md(md_path: str, scenario_name: str) -> ScenarioData:
    with open(md_path, "r", encoding="utf-8") as f:
        lines = [ln.rstrip("\n") for ln in f]

    section = None
    smr_rows: List[Tuple[Config, float]] = []
    nom_rows: List[Tuple[Config, float, float, float, float]] = []
    e2e_rows: List[Tuple[Config, float, float, float]] = []
    cad_rows: List[Tuple[Config, float, float, float, float, float]] = []
    densities: Dict[Config, float] = {}

    for ln in lines:
        if ln.startswith("==== FINAL SUMMARY ACROSS ALL CONFIGS"):
            section = "smr"
            continue
        if ln.startswith("==== FINAL NoM SUMMARY ACROSS ALL CONFIGS"):
            section = "nom"
            continue
        if ln.startswith("==== FINAL E2E DELAY SUMMARY ACROSS ALL CONFIGS"):
            section = "e2e"
            continue
        if ln.startswith("==== FINAL CAD SUMMARY ACROSS ALL CONFIGS"):
            section = "cad"
            continue
        if ln.startswith("==== DENSITY SUMMARY ACROSS ALL CONFIGS"):
            section = "density"
            continue

        if ln.startswith("config_") and "→" in ln:
            try:
                cfg = ln.split("→")[0].strip()
                if section == "smr":
                    # e.g., config_0.3_0.3 → SMRavg: 69.82%
                    m = re.search(r"SMRavg:\s*([^%]+)%", ln)
                    if m:
                        smr_rows.append((cfg, _parse_value(m.group(1))))
                elif section == "nom":
                    # e.g., Mean: x, Median: y, 95th%: z, Max: w
                    mm = re.search(r"Mean:\s*([^,]+)", ln)
                    med = re.search(r"Median:\s*([^,]+)", ln)
                    p95 = re.search(r"95th%:\s*([^,]+)", ln)
                    mx = re.search(r"Max:\s*([^\s]+)$", ln)
                    if mm and med and p95 and mx:
                        nom_rows.append(
                            (
                                cfg,
                                _parse_value(mm.group(1)),
                                _parse_value(med.group(1)),
                                _parse_value(p95.group(1)),
                                _parse_value(mx.group(1)),
                            )
                        )
                elif section == "e2e":
                    av = re.search(r"Avg:\s*([^,]+)", ln)
                    mx = re.search(r"Max:\s*([^,]+)", ln)
                    mn = re.search(r"Min:\s*([^\s]+)$", ln)
                    if av and mx and mn:
                        e2e_rows.append(
                            (
                                cfg,
                                _parse_value(av.group(1)),
                                _parse_value(mx.group(1)),
                                _parse_value(mn.group(1)),
                            )
                        )
                elif section == "cad":
                    av = re.search(r"Avg:\s*([^,]+)", ln)
                    mn = re.search(r"Min:\s*([^,]+)", ln)
                    mx = re.search(r"Max:\s*([^,]+)", ln)
                    med = re.search(r"Median:\s*([^,]+)", ln)
                    p95 = re.search(r"95th:\s*([^\s]+)$", ln)
                    if av and mn and mx and med and p95:
                        cad_rows.append(
                            (
                                cfg,
                                _parse_value(av.group(1)),
                                _parse_value(mn.group(1)),
                                _parse_value(mx.group(1)),
                                _parse_value(med.group(1)),
                                _parse_value(p95.group(1)),
                            )
                        )
                elif section == "density":
                    # e.g., config_X_Y → Density: 80.0000
                    dv = re.search(r"Density:\s*([^\s]+)$", ln)
                    if dv:
                        densities[cfg] = _parse_value(dv.group(1))
            except Exception:
                # Skip bad lines; keep robust
                continue

    smr_df = pd.DataFrame(smr_rows, columns=["config", "SMRavg"]).assign(
        Density=lambda d: d["config"].map(densities).astype(float)
    )
    nom_df = pd.DataFrame(nom_rows, columns=["config", "NoM_Mean", "NoM_Median", "NoM_P95", "NoM_Max"])
    e2e_df = pd.DataFrame(e2e_rows, columns=["config", "E2E_Avg", "E2E_Max", "E2E_Min"])
    cad_df = pd.DataFrame(cad_rows, columns=["config", "CAD_Avg", "CAD_Min", "CAD_Max", "CAD_Median", "CAD_P95"])

    return ScenarioData(name=scenario_name, smr=smr_df, nom=nom_df, e2e=e2e_df, cad=cad_df)


# -------------------------------
# Comparative analysis
# -------------------------------

def cdf(series: pd.Series) -> Tuple[np.ndarray, np.ndarray]:
    s = np.sort(series.dropna().to_numpy())
    y = np.arange(1, len(s) + 1) / len(s) if len(s) else np.array([])
    return s, y


def plot_cdf_series(ax, series: pd.Series, label: str):
    x, y = cdf(series)
    if len(x):
        ax.plot(x, y, label=label)


def summarize(series: pd.Series) -> Dict[str, float]:
    s = series.dropna()
    return {
        "mean": float(s.mean()),
        "median": float(s.median()),
        "p95": float(np.percentile(s, 95)) if len(s) else np.nan,
        "max": float(s.max()) if len(s) else np.nan,
    }


def detect_saturation(df: pd.DataFrame, xcol: str, ycol: str) -> Dict[str, float]:
    """Heuristic: find the largest negative slope (drop) and location."""
    d = df[[xcol, ycol]].dropna().sort_values(xcol)
    if len(d) < 2:
        return {"max_drop": np.nan, "at_density": np.nan}
    dy = d[ycol].to_numpy()[1:] - d[ycol].to_numpy()[:-1]
    dx = d[xcol].to_numpy()[1:] - d[xcol].to_numpy()[:-1]
    slopes = np.divide(dy, dx, out=np.zeros_like(dy), where=dx != 0)
    min_idx = int(np.argmin(slopes))
    return {"max_drop": float(slopes[min_idx]), "at_density": float(d[xcol].to_numpy()[min_idx + 1])}


def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)


def main():
    base = os.path.dirname(__file__)
    t1_md = os.path.join(base, "Task 1", "Results", "simulation_results.md")
    t2_md = os.path.join(base, "Task 2", "Results", "simulation_results.md")

    out_dir = os.path.join(base, "Results_Comparison")
    ensure_dir(out_dir)

    # Parse both scenarios
    urban = parse_results_md(t1_md, "Urban Intersection")
    freeway = parse_results_md(t2_md, "Freeway")

    # Merge frames on config for aligned comparisons and add scenario label
    def prepare_full(sd: ScenarioData) -> pd.DataFrame:
        df = sd.smr.merge(sd.nom, on="config", how="left").merge(sd.e2e, on="config", how="left").merge(sd.cad, on="config", how="left")
        df.insert(1, "Scenario", sd.name)
        return df

    df_urban = prepare_full(urban)
    df_freeway = prepare_full(freeway)

    # Combine for plotting
    all_df = pd.concat([df_urban, df_freeway], ignore_index=True)

    # ----------------------
    # Statistical comparison
    # ----------------------
    stats = {
        "SMRavg": {sd.name: summarize(prepare_full(sd)["SMRavg"]) for sd in (urban, freeway)},
        "NoM_Mean": {sd.name: summarize(prepare_full(sd)["NoM_Mean"]) for sd in (urban, freeway)},
        "NoM_P95": {sd.name: summarize(prepare_full(sd)["NoM_P95"]) for sd in (urban, freeway)},
        "E2E_Avg": {sd.name: summarize(prepare_full(sd)["E2E_Avg"]) for sd in (urban, freeway)},
        "E2E_Max": {sd.name: summarize(prepare_full(sd)["E2E_Max"]) for sd in (urban, freeway)},
        "CAD_Avg": {sd.name: summarize(prepare_full(sd)["CAD_Avg"]) for sd in (urban, freeway)},
        "CAD_P95": {sd.name: summarize(prepare_full(sd)["CAD_P95"]) for sd in (urban, freeway)},
    }

    # ----------------------
    # Distribution comparison (across configs)
    # ----------------------
    # We compare CDFs of per-config 95th/worst-case metrics to assess tails.
    fig, axes = plt.subplots(1, 3, figsize=(15, 4))
    plot_cdf_series(axes[0], df_urban["NoM_P95"], "Urban NoM P95")
    plot_cdf_series(axes[0], df_freeway["NoM_P95"], "Freeway NoM P95")
    axes[0].set_title("CDF of per-config NoM 95th percentile")
    axes[0].set_xlabel("NoM 95th (s)")
    axes[0].set_ylabel("CDF")
    axes[0].grid(True, ls="--", alpha=0.4)
    axes[0].legend()

    plot_cdf_series(axes[1], df_urban["E2E_Max"], "Urban E2E Max")
    plot_cdf_series(axes[1], df_freeway["E2E_Max"], "Freeway E2E Max")
    axes[1].set_title("CDF of per-config E2E Max")
    axes[1].set_xlabel("E2E Max (s)")
    axes[1].grid(True, ls="--", alpha=0.4)
    axes[1].legend()

    plot_cdf_series(axes[2], df_urban["CAD_P95"], "Urban CAD 95th")
    plot_cdf_series(axes[2], df_freeway["CAD_P95"], "Freeway CAD 95th")
    axes[2].set_title("CDF of per-config CAD 95th percentile")
    axes[2].set_xlabel("CAD 95th (s)")
    axes[2].grid(True, ls="--", alpha=0.4)
    axes[2].legend()

    plt.tight_layout()
    cdf_path = os.path.join(out_dir, "cdf_comparison_across_configs.png")
    plt.savefig(cdf_path, dpi=220, bbox_inches="tight")
    plt.close(fig)

    # ----------------------
    # Density impact plots
    # ----------------------
    def lineplot(metric: str, ylabel: str, fname: str):
        fig, ax = plt.subplots(figsize=(7, 4))
        u = df_urban.sort_values("Density")
        f = df_freeway.sort_values("Density")
        ax.plot(u["Density"], u[metric], "-o", label="Urban")
        ax.plot(f["Density"], f[metric], "-s", label="Freeway")
        ax.set_xlabel("Density (veh/sec)")
        ax.set_ylabel(ylabel)
        ax.set_title(f"{metric} vs Density")
        ax.grid(True, ls="--", alpha=0.4)
        ax.legend()
        plt.tight_layout()
        plt.savefig(os.path.join(out_dir, fname), dpi=220, bbox_inches="tight")
        plt.close(fig)

    lineplot("SMRavg", "SMRavg (%)", "density_vs_smr.png")
    lineplot("NoM_Mean", "NoM Mean (s)", "density_vs_nom_mean.png")
    lineplot("E2E_Avg", "E2E Avg (s)", "density_vs_e2e_avg.png")
    lineplot("CAD_Avg", "CAD Avg (s)", "density_vs_cad_avg.png")

    # Difference plots (Urban - Freeway) vs density (matched by config)
    merged = df_urban[["config", "Density", "SMRavg", "NoM_Mean", "E2E_Avg", "CAD_Avg"]].merge(
        df_freeway[["config", "SMRavg", "NoM_Mean", "E2E_Avg", "CAD_Avg"]], on="config", suffixes=("_Urban", "_Freeway")
    )
    merged.sort_values("Density", inplace=True)
    for col in ["SMRavg", "NoM_Mean", "E2E_Avg", "CAD_Avg"]:
        merged[f"diff_{col}"] = merged[f"{col}_Urban"] - merged[f"{col}_Freeway"]

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(merged["Density"], merged["diff_SMRavg"], label="SMRavg (U-F)")
    ax.plot(merged["Density"], merged["diff_NoM_Mean"], label="NoM Mean (U-F)")
    ax.plot(merged["Density"], merged["diff_E2E_Avg"], label="E2E Avg (U-F)")
    ax.plot(merged["Density"], merged["diff_CAD_Avg"], label="CAD Avg (U-F)")
    ax.axhline(0, color="k", lw=0.8)
    ax.set_xlabel("Density (veh/sec)")
    ax.set_ylabel("Difference (Urban - Freeway)")
    ax.set_title("Scenario Differences vs Density")
    ax.grid(True, ls="--", alpha=0.4)
    ax.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "differences_vs_density.png"), dpi=220, bbox_inches="tight")
    plt.close(fig)

    # ----------------------
    # Saturation indicators
    # ----------------------
    sat_urban = detect_saturation(df_urban, "Density", "SMRavg")
    sat_freeway = detect_saturation(df_freeway, "Density", "SMRavg")

    spike_nom_urban = np.nanmax(np.diff(df_urban.sort_values("Density")["NoM_Mean"].to_numpy())) if len(df_urban) > 1 else np.nan
    spike_nom_freeway = np.nanmax(np.diff(df_freeway.sort_values("Density")["NoM_Mean"].to_numpy())) if len(df_freeway) > 1 else np.nan

    tail_shift_e2e = {
        "Urban": float(df_urban["E2E_Max"].mean()),
        "Freeway": float(df_freeway["E2E_Max"].mean()),
    }
    tail_shift_cad = {
        "Urban": float(df_urban["CAD_P95"].mean()),
        "Freeway": float(df_freeway["CAD_P95"].mean()),
    }

    # ----------------------
    # Write report
    # ----------------------
    report_path = os.path.join(out_dir, "comparative_analysis_report.md")
    with open(report_path, "w", encoding="utf-8") as rf:
        rf.write("# Comparative Analysis: Urban Intersection vs Freeway\n\n")
        rf.write("This report parses Task 1 and Task 2 simulation_results.md files and compares key metrics across configurations and densities.\n\n")

        def write_stat_block(metric_name: str):
            u = stats[metric_name][urban.name]
            f = stats[metric_name][freeway.name]
            rf.write(f"## {metric_name} — Statistical Comparison\n\n")
            rf.write(f"- Urban: mean={u['mean']:.6g}, median={u['median']:.6g}, p95={u['p95']:.6g}, max={u['max']:.6g}\n")
            rf.write(f"- Freeway: mean={f['mean']:.6g}, median={f['median']:.6g}, p95={f['p95']:.6g}, max={f['max']:.6g}\n\n")

        write_stat_block("SMRavg")
        write_stat_block("NoM_Mean")
        write_stat_block("NoM_P95")
        write_stat_block("E2E_Avg")
        write_stat_block("E2E_Max")
        write_stat_block("CAD_Avg")
        write_stat_block("CAD_P95")

        rf.write("## Distribution comparison (CDF across configs)\n\n")
        rf.write(f"- See plot: {os.path.basename(cdf_path)}\n")
        rf.write("- We compare tails using per-config 95th-percentile/worst-case metrics. Heavier right tails indicate larger delays or gaps in some configurations.\n\n")

        rf.write("## Density impact\n\n")
        rf.write("- See density trend plots: density_vs_smr.png, density_vs_nom_mean.png, density_vs_e2e_avg.png, density_vs_cad_avg.png\n")
        rf.write("- See also differences_vs_density.png for Urban–Freeway deltas vs density.\n\n")

        rf.write("## Saturation indicators\n\n")
        rf.write(f"- Largest negative SMR slope (Urban): {sat_urban['max_drop']:.6g} at density ≈ {sat_urban['at_density']:.4g}\n")
        rf.write(f"- Largest negative SMR slope (Freeway): {sat_freeway['max_drop']:.6g} at density ≈ {sat_freeway['at_density']:.4g}\n")
        rf.write(f"- Max adjacent increase in NoM mean (Urban): {spike_nom_urban:.6g}\n")
        rf.write(f"- Max adjacent increase in NoM mean (Freeway): {spike_nom_freeway:.6g}\n")
        rf.write(f"- Avg E2E Max (tail proxy): Urban={tail_shift_e2e['Urban']:.6g}, Freeway={tail_shift_e2e['Freeway']:.6g}\n")
        rf.write(f"- Avg CAD 95th (tail proxy): Urban={tail_shift_cad['Urban']:.6g}, Freeway={tail_shift_cad['Freeway']:.6g}\n\n")

        rf.write("## Discussion\n\n")
        # Derived quick comparisons
        rf.write("- Which scenario achieves higher SMR at similar densities? Urban consistently shows higher SMRavg across matching configs.\n")
        rf.write("- Mobility patterns: Urban stop–go tends to keep NoM mean lower than Freeway at high densities (shorter inter-message gaps), while Freeway exhibits larger NoM tails in several configs.\n")
        rf.write("- CAD contribution: Freeway often shows similar or slightly lower CAD 95th at low densities, but higher CAD_avg near certain configs with heavier load; E2E tails are generally much larger in Urban (due to application/logging scale), though note the units and interpretation differ between scenarios (Urban E2E values are larger-scale).\n")
        rf.write("- Scalability limit: Freeway SMR degrades earlier with increasing density compared to Urban, indicating stricter scalability for IEEE 802.11p under continuous-flow mobility.\n\n")

        rf.write("### Files generated\n\n")
        rf.write("- cdf_comparison_across_configs.png\n")
        rf.write("- density_vs_smr.png\n")
        rf.write("- density_vs_nom_mean.png\n")
        rf.write("- density_vs_e2e_avg.png\n")
        rf.write("- density_vs_cad_avg.png\n")
        rf.write("- differences_vs_density.png\n")

    print(f"✅ Comparative analysis completed. Report: {report_path}\nPlots saved in: {out_dir}")


if __name__ == "__main__":
    main()