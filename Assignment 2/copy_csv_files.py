#!/usr/bin/env python3
"""
Script to copy all CSV files from config folders to a centralized location.
CSV files are renamed to include the config folder name for easy identification.
"""

import os
import shutil
from pathlib import Path


def copy_csv_files(base_path, output_folder_name="all_csv_files"):
    """
    Copy all CSV files from config_* folders to a new organized folder.
    
    Args:
        base_path: Path to the Task folder (e.g., "Task 1" or "Task 2")
        output_folder_name: Name of the output folder to create
    """
    base_path = Path(base_path)
    
    # Create output folder
    output_folder = base_path / output_folder_name
    output_folder.mkdir(exist_ok=True)
    
    print(f"Copying CSV files from: {base_path}")
    print(f"Output folder: {output_folder}")
    print("-" * 60)
    
    # Get all config folders
    config_folders = sorted([d for d in base_path.iterdir() 
                           if d.is_dir() and d.name.startswith("config_")])
    
    if not config_folders:
        print("No config folders found!")
        return
    
    total_copied = 0
    
    # Process each config folder
    for config_folder in config_folders:
        config_name = config_folder.name
        print(f"\nProcessing: {config_name}")
        
        # Find all CSV files in the config folder
        csv_files = list(config_folder.glob("*.csv"))
        
        if not csv_files:
            print(f"  No CSV files found in {config_name}")
            continue
        
        # Copy each CSV file with renamed format
        for csv_file in csv_files:
            # Create new filename: config_name + original_csv_name
            new_filename = f"{config_name}_{csv_file.name}"
            destination = output_folder / new_filename
            
            # Copy the file
            shutil.copy2(csv_file, destination)
            print(f"  ✓ Copied: {csv_file.name} -> {new_filename}")
            total_copied += 1
    
    print("\n" + "=" * 60)
    print(f"Summary: Copied {total_copied} CSV files to {output_folder.name}/")
    print("=" * 60)


def main():
    """Main function to process both Task folders."""
    script_dir = Path(__file__).parent
    
    # Process Task 1
    task1_path = script_dir / "Task 1"
    if task1_path.exists():
        print("\n" + "=" * 60)
        print("TASK 1")
        print("=" * 60)
        copy_csv_files(task1_path, "CSV_Files")
    else:
        print(f"Task 1 folder not found at: {task1_path}")
    
    # Process Task 2
    task2_path = script_dir / "Task 2"
    if task2_path.exists():
        print("\n\n" + "=" * 60)
        print("TASK 2")
        print("=" * 60)
        copy_csv_files(task2_path, "CSV_Files")
    else:
        print(f"Task 2 folder not found at: {task2_path}")
    
    print("\n\n✅ All done!")


if __name__ == "__main__":
    main()
