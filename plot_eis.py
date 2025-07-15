import os
import re
import glob
from collections import defaultdict
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

def parse_filename(filepath):
    """
    Parses a filepath to extract the chemical, pH, condition, and a unique ID.
    
    This function is designed to handle the complex naming convention of the EIS files,
    including special cases like 'Cu' or multi-word chemical names.

    :param filepath: The full path to the data file.
    :return: A dictionary containing the parsed information, or None if parsing fails.
    """
    filename = os.path.basename(filepath)
    
    # Use regular expressions to robustly capture the different parts of the filename.
    pattern = re.compile(
        r"(\d+)_"                               # 1: Index number
        r"(.+?)\s"                              # 2: Chemical name (non-greedy)
        r"(?:(pH\s\d+)\s)?"                     # 3: Optional pH group
        r"(OCP|CAP|FAR)"                        # 4: Condition (OCP, CAP, or FAR)
        r"\s\((Nyquist|Bode|Nyquist and Bode)\)" # 5: Plot type
    )
    
    match = pattern.match(filename)
    
    if match:
        parts = match.groups()
        return {
            "id": f"{parts[0]}_{parts[1]} {parts[2]} {parts[3]}", # A unique ID for the experiment
            "chemical": parts[1].strip(),
            "ph": parts[2] if parts[2] else 'N/A',
            "condition": parts[3]
        }
        
    # Handle special cases like the Copper reference files which have a different format.
    if 'Cu' in filename:
        condition_match = re.search(r"(OCP|CAP|FAR)", filename)
        if condition_match:
            return {
                "id": f"Cu_{condition_match.group(1)}",
                "chemical": 'Cu',
                "ph": 'N/A', # No pH for Cu reference
                "condition": condition_match.group(1)
            }
            
    # Handle the 'KReO4 + Na2SO4' case
    if 'KReO4 + Na2SO4' in filename:
        condition_match = re.search(r"(OCP|CAP|FAR)", filename)
        if condition_match:
            return {
                "id": f"KReO4 + Na2SO4_{condition_match.group(1)}",
                "chemical": 'KReO4 + Na2SO4',
                "ph": 'N/A',
                "condition": condition_match.group(1)
            }
            
    return None

def group_files_by_experiment(data_dir):
    """
    Scans the data directory, groups files by experiment, handling split files.

    :param data_dir: The directory containing EIS files.
    :return: A dictionary grouping file lists by [ph][condition][chemical].
    """
    experiment_files = defaultdict(list)
    
    for filepath in glob.glob(os.path.join(data_dir, '*.txt')):
        parsed_info = parse_filename(filepath)
        if parsed_info:
            experiment_files[parsed_info['id']].append(filepath)

    grouped_plots = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    
    for file_list in experiment_files.values():
        parsed_info = parse_filename(file_list[0])
        if parsed_info:
            ph = parsed_info['ph']
            condition = parsed_info['condition']
            chemical = parsed_info['chemical']
            grouped_plots[ph][condition][chemical].extend(file_list)
            
    return grouped_plots

def load_eis_data(file_list):
    """
    Loads EIS data from one or two files (for split Nyquist/Bode).
    If two files are provided, it merges them into a single DataFrame.

    :param file_list: A list containing one or two filepaths for an experiment.
    :return: A single pandas DataFrame with all data, or None on error.
    """
    try:
        if len(file_list) == 1:
            return pd.read_csv(file_list[0], sep=';')
        elif len(file_list) == 2:
            df1 = pd.read_csv(file_list[0], sep=';')
            df2 = pd.read_csv(file_list[1], sep=';')
            # A simple way to merge is to combine the dataframes, assuming columns are unique
            # or one is a subset of the other.
            # A more complex merge would be needed if columns overlap with different data.
            # For now, let's assume one file has Nyquist and the other has Bode.
            if "Z' (Ω)" not in df2.columns: # df2 is likely Bode only
                merged_df = pd.merge(df1, df2, on="Frequency (Hz)", how="outer", suffixes=('', '_y'))
            else: # df1 is likely Bode only
                merged_df = pd.merge(df2, df1, on="Frequency (Hz)", how="outer", suffixes=('', '_y'))

            return merged_df.loc[:, ~merged_df.columns.str.endswith('_y')]
    except Exception as e:
        print(f"Error loading data from {file_list}: {e}")
        return None
    return None

def plot_eis_data():
    """
    Main function to generate and save all EIS plots.
    """
    DATA_DIR = 'EIS/'
    ROWS = ['pH 1', 'pH 4', 'pH 6']
    COLS = ['OCP', 'CAP', 'FAR']
    
    unique_chemicals = sorted(['K2ReCl6', 'KReO4', 'NH4ReO4', 'Cu', 'KReO4 + Na2SO4'])
    colors = plt.cm.viridis(np.linspace(0, 1, len(unique_chemicals)))
    markers = ['o', 's', '^', 'D', 'v', 'p', '*', 'X']
    STYLE_MAP = {chem: {'color': colors[i], 'marker': markers[i % len(markers)], 'markersize': 5, 'linestyle': 'None'} for i, chem in enumerate(unique_chemicals)}
    DEFAULT_STYLE = {'color': 'grey', 'marker': 'x'}
    
    grouped_data = group_files_by_experiment(DATA_DIR)
    
    fig_nyquist, axes_nyquist = plt.subplots(3, 3, figsize=(15, 15))
    fig_bode1, axes_bode1 = plt.subplots(3, 3, figsize=(15, 15), sharex=True)
    fig_bode2, axes_bode2 = plt.subplots(3, 3, figsize=(15, 15), sharex=True, sharey=True)

    fig_nyquist.suptitle('Nyquist Plots', fontsize=20)
    fig_bode1.suptitle('Bode Plots (Magnitude)', fontsize=20)
    fig_bode2.suptitle('Bode Plots (Phase)', fontsize=20)

    for i, ph in enumerate(ROWS):
        for j, condition in enumerate(COLS):
            ax_n, ax_b1, ax_b2 = axes_nyquist[i, j], axes_bode1[i, j], axes_bode2[i, j]
            
            title = f'{ph}, {condition}'
            ax_n.set_title(title)
            ax_b1.set_title(title)
            ax_b2.set_title(title)
            
            experiments_to_plot = grouped_data[ph][condition]
            
            for chemical, file_list in sorted(experiments_to_plot.items()):
                df = load_eis_data(file_list)
                if df is not None:
                    style = STYLE_MAP.get(chemical, DEFAULT_STYLE)
                    
                    ax_n.plot(df["Z' (Ω)"], df["-Z'' (Ω)"], label=chemical, **style)
                    ax_b1.plot(df['Frequency (Hz)'], df['Z (Ω)'], label=chemical, **style)
                    ax_b2.plot(df['Frequency (Hz)'], df['-Phase (°)'], label=chemical, **style)

            # --- Formatting for each subplot ---
            # Nyquist
            ax_n.set_xlabel("Z' / Ω")
            ax_n.set_ylabel("-Z'' / Ω")
            ax_n.grid(True, linestyle=':')
            ax_n.legend()
            ax_n.set_aspect('equal', adjustable='box')
            # UPDATED: Set fixed axis limits for all Nyquist plots
            ax_n.set_xlim(0, 200)
            ax_n.set_ylim(0, 200)

            # Bode 1
            ax_b1.set_xscale('log')
            ax_b1.set_ylabel("|Z| / Ω")
            ax_b1.grid(True, which='both', linestyle=':')
            ax_b1.legend()
            
            # Bode 2
            ax_b2.set_xscale('log')
            ax_b2.set_ylabel("-Phase / °")
            ax_b2.grid(True, which='both', linestyle=':')
            ax_b2.legend()
    
    for j in range(3):
        axes_bode1[2, j].set_xlabel("Frequency / Hz")
        axes_bode2[2, j].set_xlabel("Frequency / Hz")

    fig_nyquist.tight_layout(rect=[0, 0.03, 1, 0.95])
    fig_bode1.tight_layout(rect=[0, 0.03, 1, 0.95])
    fig_bode2.tight_layout(rect=[0, 0.03, 1, 0.95])
    
    fig_nyquist.savefig('eis_nyquist_plots.tiff', dpi=600)
    fig_bode1.savefig('eis_bode1_plots.tiff', dpi=600)
    fig_bode2.savefig('eis_bode2_plots.tiff', dpi=600)
    
    print("EIS plots generated successfully.")

if __name__ == '__main__':
    plot_eis_data()
