import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def load_data(file_path):
    """Load data from a CSV file."""
    return pd.read_csv(file_path)

def calculate_statistics(data, metric):
    """Calculate mean, median, 95th percentile, and maximum for a given metric."""
    mean = data[metric].mean()
    median = data[metric].median()
    percentile_95 = np.percentile(data[metric], 95)
    maximum = data[metric].max()
    return mean, median, percentile_95, maximum

def plot_cdf(data, metric, label):
    """Plot the CDF for a given metric."""
    sorted_data = np.sort(data[metric])
    cdf = np.arange(1, len(sorted_data) + 1) / len(sorted_data)
    plt.plot(sorted_data, cdf, label=label)

def analyze_density_impact(data, metric):
    """Analyze how performance changes with increasing density."""
    grouped = data.groupby('Density')[metric].mean()
    return grouped

def identify_saturation(data, metrics):
    """Identify network saturation indicators."""
    saturation = {}
    for metric in metrics:
        sudden_drop = data[metric].diff().min()
        significant_spike = data[metric].diff().max()
        saturation[metric] = {
            'Sudden Drop': sudden_drop,
            'Significant Spike': significant_spike
        }
    return saturation

def main():
    # File paths for urban and freeway scenarios
    urban_file = 'Task 1/CSV_Files/urban_metrics.csv'
    freeway_file = 'Task 2/CSV_Files/freeway_metrics.csv'

    # Load data
    urban_data = load_data(urban_file)
    freeway_data = load_data(freeway_file)

    metrics = ['SMR', 'NoM', 'E2E Delay', 'CAD']

    # Statistical Comparison
    print("Statistical Comparison:")
    for metric in metrics:
        urban_stats = calculate_statistics(urban_data, metric)
        freeway_stats = calculate_statistics(freeway_data, metric)
        print(f"{metric} - Urban: {urban_stats}, Freeway: {freeway_stats}")

    # Distribution Comparison
    plt.figure(figsize=(10, 6))
    for metric in metrics:
        plot_cdf(urban_data, metric, f"Urban {metric}")
        plot_cdf(freeway_data, metric, f"Freeway {metric}")
    plt.xlabel('Value')
    plt.ylabel('CDF')
    plt.title('CDF Comparison')
    plt.legend()
    plt.grid()
    plt.savefig('cdf_comparison.png')

    # Density Impact
    print("Density Impact:")
    for metric in metrics:
        urban_density_impact = analyze_density_impact(urban_data, metric)
        freeway_density_impact = analyze_density_impact(freeway_data, metric)
        print(f"{metric} - Urban: {urban_density_impact}, Freeway: {freeway_density_impact}")

    # Saturation Indicators
    print("Saturation Indicators:")
    urban_saturation = identify_saturation(urban_data, metrics)
    freeway_saturation = identify_saturation(freeway_data, metrics)
    print(f"Urban: {urban_saturation}, Freeway: {freeway_saturation}")

if __name__ == "__main__":
    main()