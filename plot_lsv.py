import os
import glob
import pandas as pd
import matplotlib.pyplot as plt

# --- Please set your electrode area here ---
# The surface area of the working electrode in square centimeters (cm^2).
ELECTRODE_AREA_CM2 = 1.0

def plot_lsv_data():
    """
    This script loads Linear Sweep Voltammetry (LSV) data from a specified
    directory, processes it, and generates a multi-panel plot with custom
    styling based on the pH value.
    """
    data_directory = 'LSV/'
    chemicals = ['K2ReCl6', 'KReO4', 'NH4ReO4']

    # --- Custom Styling Definitions ---
    # Define a map where each pH value has a unique color, marker, and linestyle.
    style_map = {
        'pH 1': {'color': 'red',   'marker': 'o', 'linestyle': '-', 'markersize': 4},
        'pH 4': {'color': 'blue',  'marker': 's', 'linestyle': '--', 'markersize': 4},
        'pH 6': {'color': 'green', 'marker': '^', 'linestyle': ':', 'markersize': 4}
    }
    # A default style for any unexpected pH values
    default_style = {'color': 'black', 'marker': 'x', 'linestyle': '-.'}


    # --- Plotting Setup ---
    fig, axes = plt.subplots(1, 3, figsize=(18, 6), sharey=True)
    cu_ref_path = os.path.join(data_directory, 'LSV_Reference Cu')

    # --- Main Plotting Loop ---
    for ax, chemical in zip(axes, chemicals):
        # Plot the Copper reference
        if os.path.exists(cu_ref_path):
            df_ref = pd.read_csv(cu_ref_path, delimiter='\t', header=0)
            current_density_ref = (df_ref['WE(1).Current (A)'] * 1000) / ELECTRODE_AREA_CM2
            ax.plot(
                df_ref['Potential applied (V)'],
                current_density_ref,
                label='Reference Cu',
                linestyle='--',
                color='gray'
            )

        # Find and plot the data for the current chemical
        search_pattern = os.path.join(data_directory, f'LSV_pH*_{chemical}*')
        file_paths = sorted(glob.glob(search_pattern))

        # Plot each pH file with its defined style
        for file_path in file_paths:
            filename = os.path.basename(file_path)
            try:
                ph_value = filename.split('_')[1]
            except IndexError:
                ph_value = "Unknown pH"
            
            # Get the style from the map based on the pH value
            style = style_map.get(ph_value, default_style)

            df_chem = pd.read_csv(file_path, delimiter='\t', header=0)
            current_density_chem = (df_chem['WE(1).Current (A)'] * 1000) / ELECTRODE_AREA_CM2
            
            # Use the style dictionary to set color, marker, etc.
            ax.plot(
                df_chem['Potential applied (V)'],
                current_density_chem,
                label=ph_value,
                **style
            )

        # --- Subplot Formatting ---
        ax.set_title(chemical, fontsize=14)
        ax.set_xlabel('E / V vs Ag/AgCl (sat KCl)', fontsize=12)
        ax.grid(True, linestyle=':', alpha=0.6)
        ax.legend(title="Sample")

    axes[0].set_ylabel('j / mA$\\cdot$cm$^{-2}$', fontsize=12)
    plt.tight_layout()
    output_filename = 'lsv_comparison_plot.tiff'
    plt.savefig(output_filename, dpi=600)
    print(f"Plot saved successfully as '{output_filename}'")

if __name__ == '__main__':
    plot_lsv_data()
