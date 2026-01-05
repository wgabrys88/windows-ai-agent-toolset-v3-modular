import os
from pathlib import Path

# ============================================
# CONFIGURATION - Edit this list as needed
# ============================================
files_to_combine = [
    "agent.py",
    "main.py",
    "winapi.py",
    "scenarios.json",
    # Add more files here as needed
]

output_file = "all_combined.txt"  # Changed to .txt since it's mixed types

# ============================================
# Script
# ============================================
def combine_files():
    with open(output_file, 'w', encoding='utf-8') as outfile:
        for filename in files_to_combine:
            if os.path.exists(filename):
                print(f"Adding: {filename}")
                
                # Write separator
                outfile.write(f"\n{'='*70}\n")
                outfile.write(f"# FILE: {filename}\n")
                outfile.write(f"{'='*70}\n\n")
                
                # Write file content
                with open(filename, 'r', encoding='utf-8') as infile:
                    outfile.write(infile.read())
                
                outfile.write("\n\n")
            else:
                print(f"Warning: {filename} not found, skipping...")
    
    print(f"\n✓ Combined {len(files_to_combine)} files into '{output_file}'")

if __name__ == "__main__":
    combine_files()
