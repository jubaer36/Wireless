# -*- coding: utf-8 -*-
"""Wireless
Calculate SMR and SMRavg from .sca file and veinsCurrentVehiclesInfo.csv file
"""

import pandas as pd
import re
import os
import sys
import glob

# ==============================================
# REDIRECT OUTPUT TO FILE
# ==============================================
results_dir = "/mnt/Work/Assignments/Wireless/Assignment 2/Task 2/Results"
os.makedirs(results_dir, exist_ok=True)
output_file = os.path.join(results_dir, "simulation_results.md")

# Create a class to write to both file and console
class Logger:
    def __init__(self, filename):
        self.terminal = sys.stdout
        self.log = open(filename, "w", encoding="utf-8")
    
    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)
    
    def flush(self):
        self.terminal.flush()
        self.log.flush()
    
    def close(self):
        self.log.close()

# Redirect stdout to both console and file
logger = Logger(output_file)
sys.stdout = logger

print("# Wireless Network Simulation Analysis Report")
print("=" * 80)
print()

# ==============================================
# 0️⃣ FIND ALL CONFIGURATION FOLDERS (config_X_Y with floats)
# ==============================================
base_path = "/mnt/Work/Assignments/Wireless/Assignment 2/Task 1"  # <-- FIXED BASE PATH
config_folders = glob.glob(os.path.join(base_path, "config_*_*"))

# Arrays to store results across configurations
SMRavg_list = []
config_info = []  # To store (X, Y) pairs for reference

# Loop over each config_X_Y directory
for config_path in config_folders:

    # Extract float X and Y values from folder name
    match = re.search(r"config_([0-9]*\.?[0-9]+)_([0-9]*\.?[0-9]+)", config_path)
    if not match:
        continue  # Skip if folder does not match pattern

    X_period = float(match.group(1))   # 1st number (float)
    Y_period = float(match.group(2))   # 2nd number (float)

    config_info.append((X_period, Y_period))

    # Dynamic file paths for this configuration
    csv_file = f"{config_path}/veinsCurrentVehiclesInfo.csv"
    sca_file = f"{config_path}/WithBeaconing-#0.sca"

    # ==============================================
    # 1️⃣ READ CSV: Potential Receivers (Ntotal)
    # ==============================================
    df_csv = pd.read_csv(csv_file)

    df_csv.rename(columns={
        "Simulation Time": "time",
        "Sender": "sender",
        "Packet Type": "packet",
        "Number of Vehicles": "Ntotal"
    }, inplace=True)

    # ==============================================
    # 2️⃣ READ .sca FILE: Successful Receptions (Nrecv)
    # ==============================================
    node_receptions = {}

    with open(sca_file, "r") as f:
        for line in f:
            match = re.search(r"node\[(\d+)\].*ReceivedBroadcasts\s+(\d+)", line)
            if match:
                node = f"node[{match.group(1)}]"
                count = int(match.group(2))
                node_receptions[node] = count

    df_csv["Nrecv"] = df_csv["sender"].map(node_receptions).fillna(0)

    # ==============================================
    # 3️⃣ CALCULATE SMR & SMRavg
    # ==============================================
    df_csv["SMR(%)"] = (df_csv["Nrecv"] / df_csv["Ntotal"]) * 100
    total_potential_receivers = df_csv["Ntotal"].sum()
    total_successful_receptions = df_csv["Nrecv"].sum()
    SMRavg = (total_successful_receptions / total_potential_receivers) * 100/1000

    # Store this configuration's SMRavg
    SMRavg_list.append(SMRavg)

    # ==============================================
    # 4️⃣ PRINT REPORT (PER CONFIG)
    # ==============================================
    print(f"\n===== Simulation Reliability Report for config_{X_period}_{Y_period} =====")
    print(f"Total Transmissions: {len(df_csv)}")
    print(f"Total Potential Receivers (ΣNtotal): {total_potential_receivers}")
    print(f"Total Successful Receptions (ΣNrecv): {total_successful_receptions}")
    print(f"Average SMR (SMRavg): {SMRavg:.2f}%\n")

    print("----- First 10 SMR Entries -----")
    print(df_csv[["time", "sender", "Ntotal", "Nrecv", "SMR(%)"]].head(10))

# ==============================================
# 🔚 FINAL SUMMARY FOR ALL CONFIGURATIONS
# ==============================================
print("\n==== FINAL SUMMARY ACROSS ALL CONFIGS ====")
for (X, Y), smr in zip(config_info, SMRavg_list):
    print(f"config_{X}_{Y} → SMRavg: {smr:.2f}%")

print("\n✅ All SMRavg values collected in: SMRavg_list")

"""# NoM Calculation

NoM is calculated by using the {veinsMacLayerMessageInfo.csv} file
"""
# ==========================================================
# ==========================================================
# ==========================================================
# ==========================================================
# ==========================================================
# ==========================================================
# ==========================================================
# ==========================================================
# ==========================================================

import pandas as pd
import os
import re
import glob

# ==============================================
# 0️⃣ FIND ALL CONFIGURATION FOLDERS (config_X_Y with floats allowed)
# ==============================================
base_path = "/mnt/Work/Assignments/Wireless/Assignment 2/Task 1"  # <-- FIXED BASE PATH
config_folders = glob.glob(os.path.join(base_path, "config_*_*"))

# Arrays to store results across configurations
config_info = []           # To store (X, Y)
mean_NoM_list = []         # Global Mean NoM per config
median_NoM_list = []       # Global Median NoM per config
p95_NoM_list = []          # 95th Percentile NoM per config
max_NoM_list = []          # Max NoM per config

# Loop over each config_X_Y directory
for config_path in config_folders:

    # ✅ Extract full decimal values from folder name: config_X_Y
    match = re.search(r"config_([0-9]*\.?[0-9]+)_([0-9]*\.?[0-9]+)", config_path)
    if not match:
        continue

    X_period = float(match.group(1))
    Y_period = float(match.group(2))
    config_info.append((X_period, Y_period))

    # Dynamic file path for current config
    mac_csv = f"{config_path}/veinsMacLayerMessageInfo.csv"

    # ==============================================
    # 1️⃣ READ CSV (Reception Events Log)
    # ==============================================
    df_mac = pd.read_csv(mac_csv)

    df_mac.rename(columns={
        "Sender": "sender",
        "Receiver": "receiver",
        "Clock Time at Reception Event": "time"
    }, inplace=True)

    # ==============================================
    # 2️⃣ SORT DATA
    # ==============================================
    df_mac = df_mac.sort_values(by=["receiver", "sender", "time"])

    # ==============================================
    # 3️⃣ CALCULATE NoM PER SENDER–RECEIVER PAIR
    # ==============================================
    results = []

    for (sender, receiver), group in df_mac.groupby(["sender", "receiver"]):
        times = group["time"].values
        if len(times) > 1:
            gaps = times[1:] - times[:-1]
            NoM = gaps.max()
        else:
            NoM = 0

        results.append({
            "Sender": sender,
            "Receiver": receiver,
            "Total Messages Received": len(times),
            "NoM (seconds)": NoM
        })

    df_nom = pd.DataFrame(results)

    # ==============================================
    # 4️⃣ GLOBAL NoM METRICS FOR THIS CONFIG
    # ==============================================
    Global_Mean_NoM = df_nom["NoM (seconds)"].mean()
    Global_Median_NoM = df_nom["NoM (seconds)"].median()
    Global_95th_NoM = df_nom["NoM (seconds)"].quantile(0.95)
    Global_Max_NoM = df_nom["NoM (seconds)"].max()

    # Store in arrays
    mean_NoM_list.append(Global_Mean_NoM)
    median_NoM_list.append(Global_Median_NoM)
    p95_NoM_list.append(Global_95th_NoM)
    max_NoM_list.append(Global_Max_NoM)

    # ==============================================
    # 5️⃣ PRINT REPORT (PER CONFIG)
    # ==============================================
    print(f"\n===== NoM Metrics for config_{X_period}_{Y_period} =====")
    print(f"🌐 Mean NoM               : {Global_Mean_NoM:.6f} sec")
    print(f"🌐 Median NoM (50th %)    : {Global_Median_NoM:.6f} sec")
    print(f"🌐 95th Percentile NoM    : {Global_95th_NoM:.6f} sec")
    print(f"🌐 Max NoM                : {Global_Max_NoM:.6f} sec\n")


# ==============================================
# 🔚 FINAL SUMMARY ACROSS ALL CONFIGS
# ==============================================
print("\n==== FINAL NoM SUMMARY ACROSS ALL CONFIGS ====")
for (X, Y), m, med, p95, mx in zip(config_info, mean_NoM_list, median_NoM_list, p95_NoM_list, max_NoM_list):
    print(f"config_{X}_{Y} → Mean: {m:.6f}, Median: {med:.6f}, 95th%: {p95:.6f}, Max: {mx:.6f}")

print("\n✅ All NoM metrics stored in:")
print("mean_NoM_list, median_NoM_list, p95_NoM_list, max_NoM_list")

"""# END to END DELAY

End to End delay is calculated by using the {veinsApplLayerMessageInfo.csv} file
"""

# ==========================================================
# ==========================================================
# ==========================================================
# ==========================================================
# ==========================================================
# ==========================================================
# ==========================================================
# ==========================================================
# ==========================================================

import pandas as pd
import os
import re
import glob

# ==============================================
# 0️⃣ FIND ALL CONFIGURATION FOLDERS (Supports Floats)
# ==============================================
base_path = "/mnt/Work/Assignments/Wireless/Assignment 2/Task 1"  # <-- FIXED BASE PATH
config_folders = glob.glob(os.path.join(base_path, "config_*_*"))

# Arrays to store results across configurations
config_info = []       # Stores (X, Y)
avg_delay_list = []    # Average E2E delay per config
max_delay_list = []    # Max E2E delay per config
min_delay_list = []    # Min E2E delay per config

# ==============================================
# LOOP THROUGH EACH CONFIG FOLDER
# ==============================================
for config_path in config_folders:

    # ✅ Extract full float X and Y values (e.g., 3.5 or 2.0)
    match = re.search(r"config_([0-9]*\.?[0-9]+)_([0-9]*\.?[0-9]+)", config_path)
    if not match:
        continue

    X_period = float(match.group(1))
    Y_period = float(match.group(2))
    config_info.append((X_period, Y_period))

    # Dynamic path for this configuration
    file_path = f"{config_path}/veinsApplLayerMessageInfo.csv"

    try:
        df = pd.read_csv(file_path)
    except FileNotFoundError:
        print(f"⚠️ File not found in {config_path}, skipping...")
        continue

    # ============================================================
    # Validate Required Columns
    # ============================================================
    required_columns = ["Receiver", "Sender", "Packet Type", "Delay"]
    if not all(col in df.columns for col in required_columns):
        print(f"⚠️ Missing Columns in {config_path}, skipping...")
        continue

    # ============================================================
    # Convert Delay to Numeric
    # ============================================================
    df["Delay"] = pd.to_numeric(df["Delay"], errors="coerce")
    df = df.dropna(subset=["Delay"])

    # ============================================================
    # Global E2E Delay Metrics (Store in lists)
    # ============================================================
    avg_delay = df["Delay"].mean()
    max_delay = df["Delay"].max()
    min_delay = df["Delay"].min()

    avg_delay_list.append(avg_delay)
    max_delay_list.append(max_delay)
    min_delay_list.append(min_delay)

    # ============================================================
    # Print Per Configuration Summary
    # ============================================================
    print(f"\n===== E2E Delay Metrics for config_{X_period}_{Y_period} =====")
    print(f"Total Packets Analyzed   : {len(df)}")
    print(f"Average E2E Delay (s)     : {avg_delay:.6f}")
    print(f"Maximum E2E Delay (s)     : {max_delay:.6f}")
    print(f"Minimum E2E Delay (s)     : {min_delay:.6f}\n")

    # ============================================================
    # Per Sender-Receiver Pair Metrics (Optional Display)
    # ============================================================
    pairwise_summary = df.groupby(["Sender", "Receiver"])["Delay"].agg(
        Packets="count",
        Avg_Delay="mean",
        Max_Delay="max",
        Min_Delay="min"
    ).reset_index()

    # print("----- Per Sender → Receiver Delay Summary -----")
    # print(pairwise_summary)


# ==============================================
# 🔚 FINAL SUMMARY ACROSS ALL CONFIGS
# ==============================================
print("\n==== FINAL E2E DELAY SUMMARY ACROSS ALL CONFIGS ====")
for (X, Y), avg, mx, mn in zip(config_info, avg_delay_list, max_delay_list, min_delay_list):
    print(f"config_{X}_{Y} → Avg: {avg:.6f}, Max: {mx:.6f}, Min: {mn:.6f}")

print("\n✅ All E2E delay metrics stored in:")
print("avg_delay_list, max_delay_list, min_delay_list")

"""# Channel Access Delay (CAD)

CAD is calculated by using the {veinsChannelAccessDelayInfo.csv} file.
"""

# ==========================================================
# ==========================================================
# ==========================================================
# ==========================================================
# ==========================================================
# ==========================================================
# ==========================================================
# ==========================================================
# ==========================================================


import pandas as pd
import os
import re
import glob

# ==============================================
# 0️⃣ FIND ALL CONFIGURATION FOLDERS (supports float X,Y)
# ==============================================
base_path = "/mnt/Work/Assignments/Wireless/Assignment 2/Task 1"  # <-- FIXED BASE PATH
config_folders = glob.glob(os.path.join(base_path, "config_*_*"))

# Arrays to store results across configurations
config_info = []              # Stores (X, Y)
global_avg_cad_list = []      # Global average CAD per config
global_max_cad_list = []      # Global max CAD per config
global_min_cad_list = []      # Global min CAD per config
global_median_cad_list = []   # Global median CAD per config
global_95th_cad_list = []     # Global 95th percentile CAD per config

# ==============================================
# LOOP THROUGH EACH CONFIGURATION
# ==============================================
for config_path in config_folders:

    # Extract float X and Y from folder name
    match = re.search(r"config_([0-9]*\.?[0-9]+)_([0-9]*\.?[0-9]+)", config_path)
    if not match:
        continue

    X_period = float(match.group(1))
    Y_period = float(match.group(2))
    config_info.append((X_period, Y_period))

    # Dynamic CSV path for this configuration
    cad_csv = f"{config_path}/veinsChannelAccessDelayInfo.csv"

    try:
        df_cad = pd.read_csv(cad_csv)
    except FileNotFoundError:
        print(f"⚠️ File not found in {config_path}, skipping...")
        continue

    # ---------------------------------------------
    # Normalize column names & rename
    # ---------------------------------------------
    df_cad.columns = df_cad.columns.str.strip().str.lower()
    df_cad = df_cad.rename(columns={
        "sending node": "sender",
        "channel access delay": "cad"
    })

    # ---------------------------------------------
    # Extract node name
    # ---------------------------------------------
    def extract_node_name(s):
        try:
            s = str(s)
            if "node[" in s:
                idx = s.rfind("node[")
                return s[idx:]
            return s
        except:
            return str(s)

    df_cad["sender"] = df_cad["sender"].apply(extract_node_name)

    # ---------------------------------------------
    # Convert CAD to numeric & drop NaNs
    # ---------------------------------------------
    df_cad["cad"] = pd.to_numeric(df_cad["cad"], errors="coerce")
    df_cad = df_cad.dropna(subset=["cad"])

    # ---------------------------------------------
    # Global CAD metrics
    # ---------------------------------------------
    global_avg_cad = df_cad["cad"].mean()
    global_max_cad = df_cad["cad"].max()
    global_min_cad = df_cad["cad"].min()
    global_median_cad = df_cad["cad"].median()            # 50th percentile
    global_95th_cad = df_cad["cad"].quantile(0.95)        # 95th percentile
    total_packets = len(df_cad)

    # Store global metrics in lists
    global_avg_cad_list.append(global_avg_cad)
    global_max_cad_list.append(global_max_cad)
    global_min_cad_list.append(global_min_cad)
    global_median_cad_list.append(global_median_cad)
    global_95th_cad_list.append(global_95th_cad)

    # ---------------------------------------------
    # Print per-config results (no full tables)
    # ---------------------------------------------
    print(f"\n===== CAD Metrics for config_{X_period}_{Y_period} =====")
    print(f"Total valid CAD records : {total_packets}")
    print(f"📌 Average CAD      : {global_avg_cad:.12f} seconds")
    print(f"✅ Minimum CAD      : {global_min_cad:.12f} seconds")
    print(f"🚨 Maximum CAD      : {global_max_cad:.12f} seconds")
    print(f"🔸 Median CAD (50%) : {global_median_cad:.12f} seconds")
    print(f"🔹 95th Percentile  : {global_95th_cad:.12f} seconds")

# ==============================================
# 🔚 FINAL SUMMARY ACROSS ALL CONFIGS
# ==============================================
print("\n==== FINAL CAD SUMMARY ACROSS ALL CONFIGS ====")
for (X, Y), avg, mx, mn, med, p95 in zip(
        config_info,
        global_avg_cad_list,
        global_max_cad_list,
        global_min_cad_list,
        global_median_cad_list,
        global_95th_cad_list):
    print(f"config_{X}_{Y} → "
          f"Avg: {avg:.12f}, "
          f"Min: {mn:.12f}, "
          f"Max: {mx:.12f}, "
          f"Median: {med:.12f}, "
          f"95th: {p95:.12f}")

print("\n✅ All CAD metrics stored in:")
print("global_avg_cad_list, global_max_cad_list, global_min_cad_list, global_median_cad_list, global_95th_cad_list")

"""# Density Calculation


"""
# ==========================================================
# ==========================================================
# ==========================================================
# ==========================================================
# ==========================================================
# ==========================================================
# ==========================================================
# ==========================================================
# ==========================================================




# ==============================================
# 📦 DENSITY CALCULATION USING EXISTING VARIABLES
# Requires: config_info (list of (X,Y))
# ==============================================

density_total_list = []

for (X, Y) in config_info:
    # Total Density Formula
    density_total = ((1/float(X) + 1/float(Y))) * 12

    density_total_list.append(density_total)

# ==============================================
# 📊 PRINT DENSITY RESULTS
# ==============================================
print("\n==== DENSITY SUMMARY ACROSS ALL CONFIGS ====")
for (X, Y), dTotal in zip(config_info, density_total_list):
    print(f"config_{X}_{Y} → Density: {dTotal:.4f}")

print("\n✅ densities collected in: density_total_list\n")

print("\n=== DENSITY RESULTS ===\n")
for value in density_total_list:
    print(f"{value:.5f}")

"""# =======================
# VISUAL ANALYSIS PORTION
# =======================

# SMR vs Density
"""

# ==========================================================
# ==========================================================
# ==========================================================
# ==========================================================
# ==========================================================
# ==========================================================
# ==========================================================
# ==========================================================
# ==========================================================


import matplotlib.pyplot as plt

# ==============================================
# 1️⃣ Paired sort: density and SMRavg
# ==============================================
# Convert to list of tuples
paired_list = list(zip(density_total_list, SMRavg_list))
# Sort by density (first element of each tuple)
paired_list.sort(key=lambda x: x[0])
# Unzip back to two lists
density_sorted, SMRavg_sorted = zip(*paired_list)

# ==============================================
# 2️⃣ PLOT SMRavg vs Density
# ==============================================
plt.figure(figsize=(8, 5))
plt.plot(density_sorted, SMRavg_sorted, marker='o', linestyle='-', color='b', label='SMRavg')

plt.title("Average SMR vs Traffic Density")
plt.xlabel("Density (vehicles/sec)")
plt.ylabel("Average SMR")
plt.grid(True, linestyle='--', alpha=0.6)
plt.legend()
plt.tight_layout()

# Save and show plot
plt.savefig('/mnt/Work/Assignments/Wireless/Assignment 2/Task 1/Results/SMR_vs_Density.png', dpi=300, bbox_inches='tight')
#

# ==============================================
# 1️⃣ Data (already computed)
# ==============================================
# Example lists (replace with your actual data)
# density_total_list = [10, 20, 30, 40, 50]
# SMRavg_list = [0.87, 0.83, 0.78, 0.72, 0.65]

# ==============================================
# 2️⃣ Define Classification Thresholds
# ==============================================
# You can adjust these thresholds later as needed
HIGH_THRESHOLD = 67.5   # Case A (High reliability)
MODERATE_THRESHOLD = 60  # Case B (Moderate reliability)
# Case C is anything below MODERATE_THRESHOLD

# ==============================================
# 3️⃣ Classify SMRavg
# ==============================================
classes = []
for smr in SMRavg_list:
    if smr >= HIGH_THRESHOLD:
        classes.append("High Reliability (Case A)")
    elif MODERATE_THRESHOLD <= smr < HIGH_THRESHOLD:
        classes.append("Moderate Reliability (Case B)")
    else:
        classes.append("Low Reliability (Case C)")

# ==============================================
# 4️⃣ Combine with density/configuration info
# ==============================================
classification_results = list(zip(density_total_list, SMRavg_list, classes))

# ==============================================
# 5️⃣ Display Results
# ==============================================
print("Density\tSMRavg\tClassification")
for density, smr, cls in classification_results:
    print(f"{density}\t{smr:.3f}\t{cls}")

# ==============================================
# 6️⃣ Optional: Separate lists per class
# ==============================================
high_reliability = [(d, s) for d, s, c in classification_results if c.startswith("High")]
moderate_reliability = [(d, s) for d, s, c in classification_results if c.startswith("Moderate")]
low_reliability = [(d, s) for d, s, c in classification_results if c.startswith("Low")]

print("\nHigh Reliability (Case A):", high_reliability)
print("Moderate Reliability (Case B):", moderate_reliability)
print("Low Reliability (Case C):", low_reliability)


print("\n✅ All classification lists stored in:")
print("high_reliability , moderate_reliability , low_reliability")

"""# NoM vs Density"""

# ==========================================================
# ==========================================================
# ==========================================================
# ==========================================================
# ==========================================================
# ==========================================================
# ==========================================================
# ==========================================================
# ==========================================================



import matplotlib.pyplot as plt
import numpy as np

# ==============================================
# 0️⃣ INPUT DATA (Already Available)
# ==============================================
# density_total_list
# mean_NoM_list, median_NoM_list, p95_NoM_list, max_NoM_list
# classification_results ([(density, SMRavg, class_label), ...])

# ==============================================
# 1️⃣ SORT DATA BY DENSITY (Paired Sorting)
# ==============================================
paired_data = list(zip(
    density_total_list,
    mean_NoM_list,
    median_NoM_list,
    p95_NoM_list,
    max_NoM_list
))
paired_data.sort(key=lambda x: x[0])  # sort by density

(density_sorted,
 mean_NoM_sorted,
 median_NoM_sorted,
 p95_NoM_sorted,
 max_NoM_sorted) = zip(*paired_data)

# ==============================================
# 2️⃣ IMPROVED RELIABILITY CLASSIFICATION
# ==============================================
high_reliability = [(d, s) for d, s, c in classification_results if c.startswith("High")]
moderate_reliability = [(d, s) for d, s, c in classification_results if c.startswith("Moderate")]
low_reliability = [(d, s) for d, s, c in classification_results if c.startswith("Low")]

# Helper to avoid empty cases
def extract_indices(case_list):
    return [density_sorted.index(d) for d, _ in case_list if d in density_sorted]

def filter_by_reliability(index_list):
    return {
        "density": [density_sorted[i] for i in index_list],
        "mean": [mean_NoM_sorted[i] for i in index_list],
        "median": [median_NoM_sorted[i] for i in index_list],
        "p95": [p95_NoM_sorted[i] for i in index_list],
        "max": [max_NoM_sorted[i] for i in index_list]
    }

case_A = filter_by_reliability(extract_indices(high_reliability))      # High
case_B = filter_by_reliability(extract_indices(moderate_reliability))  # Moderate
case_C = filter_by_reliability(extract_indices(low_reliability))       # Low

# In case empty lists, assign NaN
for case in [case_A, case_B, case_C]:
    for key in ["mean", "median", "p95", "max"]:
        if len(case[key]) == 0:
            case[key] = [np.nan]

# ==============================================
# 3️⃣ GROUPED BAR CHART (Mean, Median, P95, Max)
# ==============================================
labels = ['Case A (High)', 'Case B (Moderate)', 'Case C (Low)']

mean_values = [np.nanmean(case_A["mean"]), np.nanmean(case_B["mean"]), np.nanmean(case_C["mean"])]
median_values = [np.nanmean(case_A["median"]), np.nanmean(case_B["median"]), np.nanmean(case_C["median"])]
p95_values = [np.nanmean(case_A["p95"]), np.nanmean(case_B["p95"]), np.nanmean(case_C["p95"])]
max_values = [np.nanmean(case_A["max"]), np.nanmean(case_B["max"]), np.nanmean(case_C["max"])]

x = np.arange(len(labels))
width = 0.2

plt.figure(figsize=(10, 6))
plt.bar(x - 1.5*width, mean_values, width, label='Mean NoM')
plt.bar(x - 0.5*width, median_values, width, label='Median NoM')
plt.bar(x + 0.5*width, p95_values, width, label='95th Percentile NoM')
plt.bar(x + 1.5*width, max_values, width, label='Max NoM (Worst Case)')

plt.title('Summary NoM Metrics by Reliability Class')
plt.ylabel('NoM Value')
plt.xlabel('Reliability Class')
plt.xticks(x, labels)
plt.legend()
plt.grid(axis='y', linestyle='--', alpha=0.5)
plt.tight_layout()
plt.savefig('/mnt/Work/Assignments/Wireless/Assignment 2/Task 1/Results/NoM_Summary_by_Reliability_Class.png', dpi=300, bbox_inches='tight')
#

# ==============================================
# 4️⃣ MAX NoM Highlight (Worst-Case Marker)
# ==============================================
max_values = [
    np.nanmax(case_A["max"]),
    np.nanmax(case_B["max"]),
    np.nanmax(case_C["max"])
]

plt.figure(figsize=(8, 5))
plt.plot(labels, max_values, marker='o', linestyle='-', label='Max NoM (Worst Case)')
plt.title("Worst-Case NoM Across Reliability Classes")
plt.ylabel("Max NoM Value")
plt.grid(True, linestyle='--', alpha=0.5)
plt.legend()
plt.tight_layout()
plt.savefig('/mnt/Work/Assignments/Wireless/Assignment 2/Task 1/Results/NoM_Worst_Case_by_Reliability_Class.png', dpi=300, bbox_inches='tight')
#


# ==============================================
# 5️⃣ CDF PLOTS FOR EACH CASE (SEPARATE GRAPHS)
# ==============================================
def plot_cdf(data, label):
    clean_data = [x for x in data if not np.isnan(x)]
    if clean_data:
        sorted_data = np.sort(clean_data)
        y_vals = np.arange(1, len(sorted_data) + 1) / len(sorted_data)
        plt.plot(sorted_data, y_vals, label=label)

# ---- Case A (High Reliability) ----
plt.figure(figsize=(10, 6))
plot_cdf(case_A["mean"], "Case A (High)")
plt.title("CDF of NoM Values - Case A (High Reliability)")
plt.xlabel("NoM Value")
plt.ylabel("Cumulative Probability")
plt.grid(True, linestyle='--', alpha=0.5)
plt.legend()
plt.tight_layout()
plt.savefig('/mnt/Work/Assignments/Wireless/Assignment 2/Task 1/Results/NoM_CDF_Case_A_High_Reliability.png', dpi=300, bbox_inches='tight')
#

# ---- Case B (Moderate Reliability) ----
plt.figure(figsize=(10, 6))
plot_cdf(case_B["mean"], "Case B (Moderate)")
plt.title("CDF of NoM Values - Case B (Moderate Reliability)")
plt.xlabel("NoM Value")
plt.ylabel("Cumulative Probability")
plt.grid(True, linestyle='--', alpha=0.5)
plt.legend()
plt.tight_layout()
plt.savefig('/mnt/Work/Assignments/Wireless/Assignment 2/Task 1/Results/NoM_CDF_Case_B_Moderate_Reliability.png', dpi=300, bbox_inches='tight')
#

# ---- Case C (Low Reliability) ----
plt.figure(figsize=(10, 6))
plot_cdf(case_C["mean"], "Case C (Low)")
plt.title("CDF of NoM Values - Case C (Low Reliability)")
plt.xlabel("NoM Value")
plt.ylabel("Cumulative Probability")
plt.grid(True, linestyle='--', alpha=0.5)
plt.legend()
plt.tight_layout()
plt.savefig('/mnt/Work/Assignments/Wireless/Assignment 2/Task 1/Results/NoM_CDF_Case_C_Low_Reliability.png', dpi=300, bbox_inches='tight')
#


"""# E2E Delay vs Density"""


# ==========================================================
# ==========================================================
# ==========================================================
# ==========================================================
# ==========================================================
# ==========================================================
# ==========================================================
# ==========================================================
# ==========================================================




import matplotlib.pyplot as plt
import numpy as np

# ==============================================
# 0️⃣ INPUT DATA (Already Available & Index Aligned)
# ==============================================
# density_total_list
# avg_delay_list, max_delay_list, min_delay_list
# classification_results  ->  (density, smravg, class_label)

# ==============================================
# 1️⃣ SORT DATA BY DENSITY (Keep Delays Aligned)
# ==============================================
paired_data = list(zip(
    density_total_list,
    avg_delay_list,
    min_delay_list,
    max_delay_list
))
paired_data.sort(key=lambda x: x[0])  # Sort using density

(density_sorted,
 avg_delay_sorted,
 min_delay_sorted,
 max_delay_sorted) = zip(*paired_data)

# ==============================================
# 2️⃣ GROUP BY RELIABILITY CLASS (High / Moderate / Low)
# ==============================================
high_reliability = [(d, s) for d, s, c in classification_results if c.startswith("High")]
moderate_reliability = [(d, s) for d, s, c in classification_results if c.startswith("Moderate")]
low_reliability = [(d, s) for d, s, c in classification_results if c.startswith("Low")]

def extract_indices(case_list):
    return [density_sorted.index(d) for d, _ in case_list if d in density_sorted]

def filter_delays(index_list):
    return {
        "density": [density_sorted[i] for i in index_list],
        "avg": [avg_delay_sorted[i] for i in index_list],
        "min": [min_delay_sorted[i] for i in index_list],
        "max": [max_delay_sorted[i] for i in index_list]
    }

case_A = filter_delays(extract_indices(high_reliability))     # High
case_B = filter_delays(extract_indices(moderate_reliability)) # Moderate
case_C = filter_delays(extract_indices(low_reliability))      # Low

# ================= SAFE FUNCTION =================
def safe_mean(values):
    return np.mean(values) if len(values) > 0 else 0

# ==============================================
# 3️⃣ BAR CHARTS - Min / Avg / Max separately
# ==============================================
labels = ['Case A (High)', 'Case B (Moderate)', 'Case C (Low)']
x = np.arange(len(labels))
width = 0.5

# ---- Min Delay Bar Chart ----
min_values = [safe_mean(case_A["min"]), safe_mean(case_B["min"]), safe_mean(case_C["min"])]
plt.figure(figsize=(8,5))
plt.bar(x, min_values, width, color='skyblue')
plt.title('Mean Min E2E Delay by Reliability Class')
plt.ylabel('Delay (s)')
plt.xlabel('Reliability Class')
plt.xticks(x, labels)
plt.grid(axis='y', linestyle='--', alpha=0.5)
plt.tight_layout()
plt.savefig('/mnt/Work/Assignments/Wireless/Assignment 2/Task 1/Results/E2E_Min_Delay_by_Reliability_Class.png', dpi=300, bbox_inches='tight')
#

# ---- Avg Delay Bar Chart ----
avg_values = [safe_mean(case_A["avg"]), safe_mean(case_B["avg"]), safe_mean(case_C["avg"])]
plt.figure(figsize=(8,5))
plt.bar(x, avg_values, width, color='lightgreen')
plt.title('Mean Avg E2E Delay by Reliability Class')
plt.ylabel('Delay (s)')
plt.xlabel('Reliability Class')
plt.xticks(x, labels)
plt.grid(axis='y', linestyle='--', alpha=0.5)
plt.tight_layout()
plt.savefig('/mnt/Work/Assignments/Wireless/Assignment 2/Task 1/Results/E2E_Avg_Delay_by_Reliability_Class.png', dpi=300, bbox_inches='tight')
#

# ---- Max Delay Bar Chart ----
max_values = [safe_mean(case_A["max"]), safe_mean(case_B["max"]), safe_mean(case_C["max"])]
plt.figure(figsize=(8,5))
plt.bar(x, max_values, width, color='salmon')
plt.title('Mean Max E2E Delay by Reliability Class')
plt.ylabel('Delay (s)')
plt.xlabel('Reliability Class')
plt.xticks(x, labels)
plt.grid(axis='y', linestyle='--', alpha=0.5)
plt.tight_layout()
plt.savefig('/mnt/Work/Assignments/Wireless/Assignment 2/Task 1/Results/E2E_Max_Delay_by_Reliability_Class.png', dpi=300, bbox_inches='tight')
#

# ==============================================
# 4️⃣ DENSITY vs Delay Plots - Min / Avg / Max separately
# ==============================================
# ---- Min Delay vs Density ----
plt.figure(figsize=(8,5))
plt.plot(density_sorted, min_delay_sorted, marker='o', color='skyblue', label='Min Delay')
plt.title('Density vs Min E2E Delay')
plt.xlabel('Vehicle Density')
plt.ylabel('Delay (s)')
plt.grid(True, linestyle='--', alpha=0.5)
plt.legend()
plt.tight_layout()
plt.savefig('/mnt/Work/Assignments/Wireless/Assignment 2/Task 1/Results/Density_vs_Min_E2E_Delay.png', dpi=300, bbox_inches='tight')
#

# ---- Avg Delay vs Density ----
plt.figure(figsize=(8,5))
plt.plot(density_sorted, avg_delay_sorted, marker='o', color='lightgreen', label='Avg Delay')
plt.title('Density vs Avg E2E Delay')
plt.xlabel('Vehicle Density')
plt.ylabel('Delay (s)')
plt.grid(True, linestyle='--', alpha=0.5)
plt.legend()
plt.tight_layout()
plt.savefig('/mnt/Work/Assignments/Wireless/Assignment 2/Task 1/Results/Density_vs_Avg_E2E_Delay.png', dpi=300, bbox_inches='tight')
#

# ---- Max Delay vs Density ----
plt.figure(figsize=(8,5))
plt.plot(density_sorted, max_delay_sorted, marker='o', color='salmon', label='Max Delay')
plt.title('Density vs Max E2E Delay')
plt.xlabel('Vehicle Density')
plt.ylabel('Delay (s)')
plt.grid(True, linestyle='--', alpha=0.5)
plt.legend()
plt.tight_layout()
plt.savefig('/mnt/Work/Assignments/Wireless/Assignment 2/Task 1/Results/Density_vs_Max_E2E_Delay.png', dpi=300, bbox_inches='tight')
#


# ==============================================
# 5️⃣ CDF PLOTS FOR EACH CASE (Avg Delay - SEPARATE)
# ==============================================
def plot_cdf(data, label):
    if len(data) == 0:
        return
    sorted_data = np.sort(data)
    y_vals = np.arange(1, len(sorted_data) + 1) / len(sorted_data)
    plt.plot(sorted_data, y_vals, label=label)

# ---- Case A (High Reliability) ----
plt.figure(figsize=(10, 6))
plot_cdf(case_A["avg"], "Case A (High)")
plt.title("CDF of E2E Avg Delay - Case A (High Reliability)")
plt.xlabel("Avg Delay (s)")
plt.ylabel("Cumulative Probability")
plt.grid(True, linestyle='--', alpha=0.5)
plt.legend()
plt.tight_layout()
plt.savefig('/mnt/Work/Assignments/Wireless/Assignment 2/Task 1/Results/E2E_CDF_Case_A_High_Reliability.png', dpi=300, bbox_inches='tight')
#

# ---- Case B (Moderate Reliability) ----
plt.figure(figsize=(10, 6))
plot_cdf(case_B["avg"], "Case B (Moderate)")
plt.title("CDF of E2E Avg Delay - Case B (Moderate Reliability)")
plt.xlabel("Avg Delay (s)")
plt.ylabel("Cumulative Probability")
plt.grid(True, linestyle='--', alpha=0.5)
plt.legend()
plt.tight_layout()
plt.savefig('/mnt/Work/Assignments/Wireless/Assignment 2/Task 1/Results/E2E_CDF_Case_B_Moderate_Reliability.png', dpi=300, bbox_inches='tight')
#

# ---- Case C (Low Reliability) ----
plt.figure(figsize=(10, 6))
plot_cdf(case_C["avg"], "Case C (Low)")
plt.title("CDF of E2E Avg Delay - Case C (Low Reliability)")
plt.xlabel("Avg Delay (s)")
plt.ylabel("Cumulative Probability")
plt.grid(True, linestyle='--', alpha=0.5)
plt.legend()
plt.tight_layout()
plt.savefig('/mnt/Work/Assignments/Wireless/Assignment 2/Task 1/Results/E2E_CDF_Case_C_Low_Reliability.png', dpi=300, bbox_inches='tight')
#




"""# Channel Access Delay vs Density"""



# ==========================================================
# ==========================================================
# ==========================================================
# ==========================================================
# ==========================================================
# ==========================================================
# ==========================================================
# ==========================================================
# ==========================================================



import numpy as np
import matplotlib.pyplot as plt

# ==================================================
# 0️⃣ INPUT DATA (Already Available & Index Aligned)
# ==================================================
# density_total_list
# global_avg_cad_list, global_min_cad_list, global_max_cad_list
# global_median_cad_list, global_95th_cad_list
# classification_results -> (density, smravg, class_label)

# ==================================================
# 1️⃣ SORT DATA BY DENSITY (Keep CAD Metrics Aligned)
# ==================================================
paired_data_cad = list(zip(
    density_total_list,
    global_avg_cad_list,
    global_min_cad_list,
    global_max_cad_list,
    global_median_cad_list,
    global_95th_cad_list
))
paired_data_cad.sort(key=lambda x: x[0])  # Sort by density

(density_sorted,
 avg_cad_sorted,
 min_cad_sorted,
 max_cad_sorted,
 median_cad_sorted,
 p95_cad_sorted) = zip(*paired_data_cad)

# ==================================================
# 2️⃣ GROUP BY RELIABILITY CLASS (High / Moderate / Low)
# ==================================================
high_reliability = [(d, s) for d, s, c in classification_results if c.startswith("High")]
moderate_reliability = [(d, s) for d, s, c in classification_results if c.startswith("Moderate")]
low_reliability = [(d, s) for d, s, c in classification_results if c.startswith("Low")]

def extract_indices(case_list):
    return [density_sorted.index(d) for d, _ in case_list if d in density_sorted]

def filter_cad(index_list):
    return {
        "density": [density_sorted[i] for i in index_list],
        "min":    [min_cad_sorted[i] for i in index_list],
        "avg":    [avg_cad_sorted[i] for i in index_list],
        "median": [median_cad_sorted[i] for i in index_list],
        "p95":    [p95_cad_sorted[i] for i in index_list],
        "max":    [max_cad_sorted[i] for i in index_list]
    }

case_A = filter_cad(extract_indices(high_reliability))     # High
case_B = filter_cad(extract_indices(moderate_reliability)) # Moderate
case_C = filter_cad(extract_indices(low_reliability))      # Low

def safe_mean(values):
    return np.mean(values) if len(values) > 0 else 0

# ==================================================
# 3️⃣ BAR CHARTS - Mean CAD Comparison (Min/Avg/Median/95th/Max)
# ==================================================
labels = ['Case A (High)', 'Case B (Moderate)', 'Case C (Low)']
x = np.arange(len(labels))
width = 0.5

# ---- Average CAD Bar Chart ----
avg_values = [safe_mean(case_A["avg"]), safe_mean(case_B["avg"]), safe_mean(case_C["avg"])]
plt.figure(figsize=(8,5))
plt.bar(x, avg_values, width)
plt.title('Mean Avg CAD by Reliability Class')
plt.ylabel('CAD (s)')
plt.xlabel('Reliability Class')
plt.xticks(x, labels)
plt.grid(axis='y', linestyle='--', alpha=0.5)
plt.tight_layout()
plt.savefig('/mnt/Work/Assignments/Wireless/Assignment 2/Task 1/Results/CAD_Avg_by_Reliability_Class.png', dpi=300, bbox_inches='tight')
#

# ---- Median CAD Bar Chart ----
median_values = [safe_mean(case_A["median"]), safe_mean(case_B["median"]), safe_mean(case_C["median"])]
plt.figure(figsize=(8,5))
plt.bar(x, median_values, width)
plt.title('Mean Median CAD by Reliability Class')
plt.ylabel('CAD (s)')
plt.xlabel('Reliability Class')
plt.xticks(x, labels)
plt.grid(axis='y', linestyle='--', alpha=0.5)
plt.tight_layout()
plt.savefig('/mnt/Work/Assignments/Wireless/Assignment 2/Task 1/Results/CAD_Median_by_Reliability_Class.png', dpi=300, bbox_inches='tight')
#

# ---- 95th Percentile CAD Bar Chart ----
p95_values = [safe_mean(case_A["p95"]), safe_mean(case_B["p95"]), safe_mean(case_C["p95"])]
plt.figure(figsize=(8,5))
plt.bar(x, p95_values, width)
plt.title('Mean 95th Percentile CAD by Reliability Class')
plt.ylabel('CAD (s)')
plt.xlabel('Reliability Class')
plt.xticks(x, labels)
plt.grid(axis='y', linestyle='--', alpha=0.5)
plt.tight_layout()
plt.savefig('/mnt/Work/Assignments/Wireless/Assignment 2/Task 1/Results/CAD_95th_Percentile_by_Reliability_Class.png', dpi=300, bbox_inches='tight')
#

# ==================================================
# 4️⃣ DENSITY vs CAD Plots – Individual (No Loop)
# ==================================================

# ---- Min CAD vs Density ----
plt.figure(figsize=(8,5))
plt.plot(density_sorted, min_cad_sorted, marker='o', label='Min CAD')
plt.title('Density vs Min CAD')
plt.xlabel('Vehicle Density')
plt.ylabel('CAD (s)')
plt.grid(True, linestyle='--', alpha=0.5)
plt.legend()
plt.tight_layout()
plt.savefig('/mnt/Work/Assignments/Wireless/Assignment 2/Task 1/Results/Density_vs_Min_CAD.png', dpi=300, bbox_inches='tight')
#

# ---- Avg CAD vs Density ----
plt.figure(figsize=(8,5))
plt.plot(density_sorted, avg_cad_sorted, marker='o', label='Avg CAD')
plt.title('Density vs Avg CAD')
plt.xlabel('Vehicle Density')
plt.ylabel('CAD (s)')
plt.grid(True, linestyle='--', alpha=0.5)
plt.legend()
plt.tight_layout()
plt.savefig('/mnt/Work/Assignments/Wireless/Assignment 2/Task 1/Results/Density_vs_Avg_CAD.png', dpi=300, bbox_inches='tight')
#

# ---- Median CAD vs Density ----
plt.figure(figsize=(8,5))
plt.plot(density_sorted, median_cad_sorted, marker='o', label='Median CAD')
plt.title('Density vs Median CAD')
plt.xlabel('Vehicle Density')
plt.ylabel('CAD (s)')
plt.grid(True, linestyle='--', alpha=0.5)
plt.legend()
plt.tight_layout()
plt.savefig('/mnt/Work/Assignments/Wireless/Assignment 2/Task 1/Results/Density_vs_Median_CAD.png', dpi=300, bbox_inches='tight')
#

# ---- 95th Percentile CAD vs Density ----
plt.figure(figsize=(8,5))
plt.plot(density_sorted, p95_cad_sorted, marker='o', label='95th Percentile CAD')
plt.title('Density vs 95th Percentile CAD')
plt.xlabel('Vehicle Density')
plt.ylabel('CAD (s)')
plt.grid(True, linestyle='--', alpha=0.5)
plt.legend()
plt.tight_layout()
plt.savefig('/mnt/Work/Assignments/Wireless/Assignment 2/Task 1/Results/Density_vs_95th_Percentile_CAD.png', dpi=300, bbox_inches='tight')
#

# ---- Max CAD vs Density ----
plt.figure(figsize=(8,5))
plt.plot(density_sorted, max_cad_sorted, marker='o', label='Max CAD')
plt.title('Density vs Max CAD')
plt.xlabel('Vehicle Density')
plt.ylabel('CAD (s)')
plt.grid(True, linestyle='--', alpha=0.5)
plt.legend()
plt.tight_layout()
plt.savefig('/mnt/Work/Assignments/Wireless/Assignment 2/Task 1/Results/Density_vs_Max_CAD.png', dpi=300, bbox_inches='tight')
#


# ==================================================
# 5️⃣ CDF PLOTS FOR EACH CASE (Median CAD - SEPARATE)
# ==================================================
def plot_cdf(data, label):
    if len(data) == 0:
        return
    sorted_data = np.sort(data)
    y_vals = np.arange(1, len(sorted_data) + 1) / len(sorted_data)
    plt.plot(sorted_data, y_vals, label=label)

# ---- Case A (High Reliability) ----
plt.figure(figsize=(10, 6))
plot_cdf(case_A["median"], "Case A (High)")
plt.title("CDF of Median CAD - Case A (High Reliability)")
plt.xlabel("Median CAD (s)")
plt.ylabel("Cumulative Probability")
plt.grid(True, linestyle='--', alpha=0.5)
plt.legend()
plt.tight_layout()
plt.savefig('/mnt/Work/Assignments/Wireless/Assignment 2/Task 1/Results/CAD_CDF_Case_A_High_Reliability.png', dpi=300, bbox_inches='tight')
#

# ---- Case B (Moderate Reliability) ----
plt.figure(figsize=(10, 6))
plot_cdf(case_B["median"], "Case B (Moderate)")
plt.title("CDF of Median CAD - Case B (Moderate Reliability)")
plt.xlabel("Median CAD (s)")
plt.ylabel("Cumulative Probability")
plt.grid(True, linestyle='--', alpha=0.5)
plt.legend()
plt.tight_layout()
plt.savefig('/mnt/Work/Assignments/Wireless/Assignment 2/Task 1/Results/CAD_CDF_Case_B_Moderate_Reliability.png', dpi=300, bbox_inches='tight')
#

# ---- Case C (Low Reliability) ----
plt.figure(figsize=(10, 6))
plot_cdf(case_C["median"], "Case C (Low)")
plt.title("CDF of Median CAD - Case C (Low Reliability)")
plt.xlabel("Median CAD (s)")
plt.ylabel("Cumulative Probability")
plt.grid(True, linestyle='--', alpha=0.5)
plt.legend()
plt.tight_layout()
plt.savefig('/mnt/Work/Assignments/Wireless/Assignment 2/Task 1/Results/CAD_CDF_Case_C_Low_Reliability.png', dpi=300, bbox_inches='tight')
#

# ==============================================
# CLOSE OUTPUT FILE
# ==============================================
print("\n" + "=" * 80)
print("# Analysis Complete")
print(f"Results saved to: {output_file}")
print("=" * 80)

# Close the logger and restore stdout
sys.stdout = logger.terminal
logger.close()
print(f"\n✅ All output has been saved to: {output_file}")




