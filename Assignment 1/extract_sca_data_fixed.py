#!/usr/bin/env python3
"""
OMNeT++ .sca File Data Extraction Script - Fixed Version
========================================================

This script extracts performance metrics from OMNeT++ scalar result files (.sca)
for wireless network simulation analysis.

Usage:
    python extract_sca_data.py [path_to_task1_folder]

Output:
    - CSV file with extracted metrics for all configurations
    - Summary statistics and analysis
"""

import os
import re
import pandas as pd
import numpy as np
import argparse
from pathlib import Path


def parse_sca_file_advanced(filepath):
    """
    Advanced parsing of OMNeT++ .sca file with comprehensive metric extraction.
    
    Returns:
        Dictionary with all extracted metrics
    """
    metrics = {
        # Basic packet statistics
        'packets_sent_total': 0,
        'packets_received_total': 0,
        'packets_dropped_total': 0,
        'bytes_sent_total': 0,
        'bytes_received_total': 0,
        
        # Timing statistics
        'simulation_time': 0,
        'avg_end_to_end_delay': 0,
        'min_end_to_end_delay': 0,
        'max_end_to_end_delay': 0,
        'stddev_end_to_end_delay': 0,
        
        # MAC layer statistics
        'mac_queue_length_avg': 0,
        'mac_queue_length_max': 0,
        'collision_count_total': 0,
        'retry_count_total': 0,
        'channel_access_time_avg': 0,
        
        # Physical layer statistics
        'signal_power_avg': 0,
        'noise_power_avg': 0,
        'snir_avg': 0,
        'bit_error_rate_avg': 0,
        
        # Application layer statistics
        'throughput_bps': 0,
        'goodput_bps': 0,
        'packet_delivery_ratio': 0,
        
        # Host-specific breakdowns
        'host_metrics': {}
    }
    
    try:
        with open(filepath, 'r') as file:
            content = file.read()
        
        print(f"Processing {filepath}...")
        
        # Extract simulation time from parameters
        sim_time_match = re.search(r'param \*\*\.sim-time-limit\s+(\d+)s', content)
        if sim_time_match:
            metrics['simulation_time'] = int(sim_time_match.group(1))
        else:
            # Try alternative format
            sim_time_match = re.search(r'sim-time-limit = (\d+)s', content)
            if sim_time_match:
                metrics['simulation_time'] = int(sim_time_match.group(1))
            else:
                metrics['simulation_time'] = 40  # Default
        
        # Extract packets sent (from all wireless hosts' applications)
        packets_sent_matches = re.findall(r'scalar.*wirelessHost\[\d+\]\.app\[0\]\s+packetSent:count\s+(\d+)', content)
        metrics['packets_sent_total'] = sum([int(x) for x in packets_sent_matches])
        
        # Extract bytes sent (from applications)
        bytes_sent_matches = re.findall(r'scalar.*wirelessHost\[\d+\]\.app\[0\]\s+packetSent:sum\(packetBytes\)\s+(\d+)', content)
        metrics['bytes_sent_total'] = sum([int(x) for x in bytes_sent_matches])
        
        # Extract packets received (at sink application level)
        packets_received_matches = re.findall(r'scalar.*sinkNode\.app\[0\]\s+packetReceived:count\s+(\d+)', content)
        metrics['packets_received_total'] = sum([int(x) for x in packets_received_matches])
        
        # Extract bytes received (at sink app level)
        bytes_received_matches = re.findall(r'scalar.*sinkNode\.app\[0\]\s+packetReceived:sum\(packetBytes\)\s+(\d+)', content)
        metrics['bytes_received_total'] = sum([int(x) for x in bytes_received_matches])
        
        # Calculate basic performance metrics
        if metrics['packets_sent_total'] > 0:
            metrics['packet_delivery_ratio'] = (metrics['packets_received_total'] / metrics['packets_sent_total']) * 100
        
        if metrics['simulation_time'] > 0:
            metrics['throughput_bps'] = (metrics['bytes_received_total'] * 8) / metrics['simulation_time']
            metrics['goodput_bps'] = metrics['throughput_bps']  # Assuming all received data is useful
        
        # Extract end-to-end delay statistics (from histogram data)
        # Look for endToEndDelay histogram and extract the field mean value
        delay_pattern = r'statistic.*endToEndDelay:histogram\s+field count \d+\s+field mean ([0-9\.e\-\+\-nan]+)'
        delay_match = re.search(delay_pattern, content, re.MULTILINE)
        if delay_match:
            try:
                delay_str = delay_match.group(1)
                if delay_str not in ['-nan', 'nan', '-inf', 'inf']:
                    metrics['avg_end_to_end_delay'] = float(delay_str)
            except ValueError:
                metrics['avg_end_to_end_delay'] = 0
        
        # Alternative: look for individual field mean lines following endToEndDelay
        if metrics['avg_end_to_end_delay'] == 0:
            # Find the endToEndDelay histogram section and extract the mean
            delay_section_start = content.find('endToEndDelay:histogram')
            if delay_section_start > 0:
                delay_section = content[delay_section_start:delay_section_start+500]  # Look within next 500 chars
                field_mean_match = re.search(r'field mean ([0-9\.e\-\+]+)', delay_section)
                if field_mean_match:
                    try:
                        metrics['avg_end_to_end_delay'] = float(field_mean_match.group(1))
                    except ValueError:
                        pass
        
        # Extract MAC layer statistics (retry and collision data)
        retry_matches = re.findall(r'scalar.*\.mac\.dcf\.packetSentToPeerWithRetry:count\s+(\d+)', content)
        if retry_matches:
            metrics['retry_count_total'] = sum([int(x) for x in retry_matches])
        
        # Extract queue length statistics
        queue_matches = re.findall(r'scalar.*queueLength:timeavg\s+([0-9\.e\-\+]+)', content)
        if queue_matches:
            valid_values = []
            for x in queue_matches:
                try:
                    if x not in ['-nan', 'nan', '-inf', 'inf', '-']:
                        valid_values.append(float(x))
                except ValueError:
                    continue
            if valid_values:
                metrics['mac_queue_length_avg'] = np.mean(valid_values)
        
        # Print extraction summary
        print(f"  - Packets Sent: {metrics['packets_sent_total']}")
        print(f"  - Packets Received: {metrics['packets_received_total']}")
        print(f"  - PDR: {metrics['packet_delivery_ratio']:.2f}%")
        print(f"  - Throughput: {metrics['throughput_bps'] / 1_000_000:.2f} Mbps")
        print(f"  - Avg Delay: {metrics['avg_end_to_end_delay']:.6f}s")
        print(f"  - Simulation Time: {metrics['simulation_time']}s")
        
    except Exception as e:
        print(f"Error parsing {filepath}: {e}")
    
    return metrics


def extract_config_parameters(ini_filepath):
    """
    Extract configuration parameters from omnetpp.ini file.
    """
    params = {
        'message_length': 100,  # Default
        'send_interval': 1.0,   # Default
        'cw_min': 15,          # Default
        'cw_max': 1023,        # Default
        'retry_limit': 7       # Default
    }
    
    try:
        with open(ini_filepath, 'r') as file:
            content = file.read()
        
        # Extract message length (look for the configured value with comment)
        msg_length_match = re.search(r'messageLength = (\d+)B\s*# Configure it', content)
        if msg_length_match:
            params['message_length'] = int(msg_length_match.group(1))
        
        # Extract send interval (look for configured value with comment)
        send_interval_match = re.search(r'sendInterval = ([\d\.]+)s\s*# Configure it', content)
        if send_interval_match:
            params['send_interval'] = float(send_interval_match.group(1))
        
        # Extract contention window parameters
        cw_min_match = re.search(r'cwMin = (\d+)', content)
        if cw_min_match:
            params['cw_min'] = int(cw_min_match.group(1))
        
        cw_max_match = re.search(r'cwMax = (\d+)', content)
        if cw_max_match:
            params['cw_max'] = int(cw_max_match.group(1))
            
        # Extract retry limit
        retry_match = re.search(r'shortRetryLimit = (\d+)', content)
        if retry_match:
            params['retry_limit'] = int(retry_match.group(1))
            
    except Exception as e:
        print(f"Error parsing {ini_filepath}: {e}")
    
    return params


def extract_all_configurations(task1_path="Task1/Wireless"):
    """
    Extract data from all configuration directories.
    """
    configs = ['conf1', 'conf2', 'conf3', 'conf4', 'conf5', 'conf6']
    all_results = {}
    
    print("="*80)
    print("OMNeT++ .sca DATA EXTRACTION - FIXED VERSION")
    print("="*80)
    
    for conf in configs:
        print(f"\nProcessing {conf}...")
        print("-" * 30)
        
        conf_path = Path(task1_path) / conf
        sca_path = conf_path / 'results' / 'Configurable_WiredAndWirelessHosts-#0.sca'
        ini_path = conf_path / 'omnetpp.ini'
        
        result = {'config': conf}
        
        # Extract configuration parameters
        if ini_path.exists():
            try:
                params = extract_config_parameters(ini_path)
                result.update(params)
                
                # Calculate theoretical load
                if 'message_length' in result and 'send_interval' in result:
                    packet_bits = result['message_length'] * 8
                    load_per_host_bps = packet_bits / result['send_interval']
                    # Count number of wireless hosts (typically 10 in these simulations)
                    num_hosts = 10  # Based on the grep results showing wirelessHost[0] through [9]
                    result['theoretical_load_mbps'] = (load_per_host_bps * num_hosts) / 1_000_000
                
                print(f"  - Message Length: {result.get('message_length', 'N/A')} bytes")
                print(f"  - Send Interval: {result.get('send_interval', 'N/A')} sec")
                print(f"  - Theoretical Load: {result.get('theoretical_load_mbps', 'N/A'):.2f} Mbps")
                
            except Exception as e:
                print(f"  - Error reading omnetpp.ini: {e}")
        
        # Extract metrics from .sca file
        if sca_path.exists():
            sca_metrics = parse_sca_file_advanced(sca_path)
            result.update(sca_metrics)
        else:
            print(f"  - Warning: {sca_path} not found")
        
        all_results[conf] = result
    
    return all_results


def save_results_to_csv(results, output_file="task1_extracted_data_fixed.csv"):
    """
    Save extraction results to CSV file.
    """
    # Prepare data for DataFrame
    rows = []
    for conf, data in results.items():
        # Create base row with main metrics
        row = {k: v for k, v in data.items() if k != 'host_metrics'}
        rows.append(row)
    
    df = pd.DataFrame(rows)
    
    # Sort by configuration
    df['config_num'] = df['config'].str.extract('(\d+)').astype(int)
    df = df.sort_values('config_num').drop('config_num', axis=1)
    
    # Save to CSV
    df.to_csv(output_file, index=False)
    print(f"\nResults saved to: {output_file}")
    
    # Display summary
    print("\n" + "="*80)
    print("EXTRACTION SUMMARY - FIXED VERSION")
    print("="*80)
    
    if 'theoretical_load_mbps' in df.columns and 'throughput_bps' in df.columns:
        df['achieved_throughput_mbps'] = df['throughput_bps'] / 1_000_000
        df['efficiency_percent'] = (df['achieved_throughput_mbps'] / df['theoretical_load_mbps'] * 100).fillna(0)
        
        summary_cols = ['config', 'theoretical_load_mbps', 'achieved_throughput_mbps', 
                       'packet_delivery_ratio', 'avg_end_to_end_delay', 'efficiency_percent',
                       'packets_sent_total', 'packets_received_total']
        
        available_cols = [col for col in summary_cols if col in df.columns]
        print(df[available_cols].round(3))
    else:
        print(df.round(3))
    
    return df


def main():
    parser = argparse.ArgumentParser(description='Extract data from OMNeT++ .sca files')
    parser.add_argument('task1_path', nargs='?', default='Task1/Wireless',
                       help='Path to Task1 folder containing configuration directories')
    parser.add_argument('-o', '--output', default='task1_extracted_data_fixed.csv',
                       help='Output CSV filename')
    
    args = parser.parse_args()
    
    # Check if path exists
    if not os.path.exists(args.task1_path):
        print(f"Error: Path '{args.task1_path}' does not exist!")
        print("Please ensure you're running from the correct directory.")
        return 1
    
    # Extract data
    results = extract_all_configurations(args.task1_path)
    
    # Save results
    df = save_results_to_csv(results, args.output)
    
    print(f"\nExtraction completed successfully!")
    print(f"Processed {len(results)} configurations")
    print(f"Output saved to: {args.output}")
    
    return 0


if __name__ == '__main__':
    exit(main())
