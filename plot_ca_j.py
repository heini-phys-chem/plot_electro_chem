import os
import re
from collections import defaultdict
import pandas as pd
import matplotlib.pyplot as plt

# --- IMPORTANT: Please set your electrode's surface area here ---
# The surface area of the working electrode in square centimetres (cm^2).
# This value is essential for calculating the current density correctly.
ELECTRODE_AREA_CM2 = 1.0

def generate_ca_subplots(directory_path: str, output_filename: str) -> None:
    """
    Scans a directory for chronoamperometry data, groups it by pH, and plots
    current density vs. time on a 3-panel subplot figure, with a reference
    curve on each panel. The final figure is saved to a file.

    Parameters
    ----------
    directory_path : str
        The path to the directory containing the .txt data files.
    output_filename : str
        The name of the file to save the plot to.

    Returns
    -------
    None
        Saves a matplotlib plot to the specified file.
    """
    # --- 1. Group files by pH value ---
    grouped_files = defaultdict(list)
    cu_ref_path = None
    try:
        all_files = sorted([f for f in os.listdir(directory_path) if f.endswith(".txt")])
    except FileNotFoundError:
        print(f"Error: The directory '{directory_path}' could not be found.")
        return

    for filename in all_files:
        if "Cu" in filename:
            cu_ref_path = os.path.join(directory_path, filename)
        elif "pH" in filename:
            match_ph = re.search(r'pH(\d+)', filename)
            if match_ph:
                ph_key = f"pH {match_ph.group(1)}"
                grouped_files[ph_key].append(os.path.join(directory_path, filename))

    # --- 2. Create subplots and define styles ---
    ph_keys = sorted(grouped_files.keys())
    fig, axes = plt.subplots(len(ph_keys), 1, figsize=(10, 15), sharex=True)
    fig.suptitle('Chronoamperometry Analysis: Current Density vs. Time', fontsize=16)

    markers = ['o', 's', '^', 'D', 'v']
    linestyles = ['-', '--', '-.', ':']

    # --- 3. Loop through each pH group and plot ---
    for i, ph_key in enumerate(ph_keys):
        ax = axes[i]
        plot_index = 0

        # First, plot the Copper reference on the current subplot
        if cu_ref_path:
            try:
                data_ref = pd.read_csv(cu_ref_path, sep='\t')
                if 'Time (s)' in data_ref.columns and 'WE(1).Current (A)' in data_ref.columns:
                    data_ref['Time (min)'] = (data_ref['Time (s)'] - data_ref['Time (s)'].iloc[0]) / 60
                    data_ref['j (mA/cm2)'] = (data_ref['WE(1).Current (A)'] * 1000) / ELECTRODE_AREA_CM2
                    ax.plot(data_ref['Time (min)'], data_ref['j (mA/cm2)'],
                            label='Cu Reference', color='grey', linestyle='--')
            except Exception as e:
                print(f"❌ Could not process reference file '{cu_ref_path}': {e}")

        # Now, plot all systems for the current pH
        for file_path in grouped_files[ph_key]:
            filename = os.path.basename(file_path)
            match_label = re.search(r'pH\d+_(.*)\.txt', filename)
            plot_label = match_label.group(1).strip() if match_label else filename

            try:
                data = pd.read_csv(file_path, sep='\t')
                if 'Time (s)' in data.columns and 'WE(1).Current (A)' in data.columns:
                    # Normalise time and calculate current density
                    data['Time (min)'] = (data['Time (s)'] - data['Time (s)'].iloc[0]) / 60
                    data['j (mA/cm2)'] = (data['WE(1).Current (A)'] * 1000) / ELECTRODE_AREA_CM2

                    # Select styles and plot
                    marker = markers[plot_index % len(markers)]
                    linestyle = linestyles[plot_index % len(linestyles)]
                    ax.plot(data['Time (min)'], data['j (mA/cm2)'], label=plot_label,
                            marker=marker, linestyle=linestyle, markevery=200, markersize=6)
                    plot_index += 1
                else:
                    print(f"⚠️  Warning: Could not find required columns in '{filename}'.")
            except Exception as e:
                print(f"❌ An error occurred while processing '{filename}': {e}")

        # --- 4. Configure each subplot ---
        ax.set_title(f'Analysis for {ph_key}')
        ax.set_ylabel('j / mA$\\cdot$cm$^{-2}$')
        ax.legend(title='System')
        ax.grid(True, linestyle='--', alpha=0.7)

    # --- 5. Final adjustments and save ---
    axes[-1].set_xlabel('Time (min)') # Add x-label only to the bottom plot
    plt.tight_layout(rect=[0, 0.03, 1, 0.95]) # Adjust layout to make room for suptitle

    try:
        fig.savefig(output_filename, dpi=600, bbox_inches='tight')
        print(f"✅ Plot successfully saved as '{output_filename}'")
    except Exception as e:
        print(f"❌ Error saving file: {e}")

# --- Main execution block ---
if __name__ == '__main__':
    data_directory = 'CAs/'
    generate_ca_subplots(data_directory, output_filename="ca_current_density_subplots.tiff")
