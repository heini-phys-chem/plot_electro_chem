import os
import re
import pandas as pd
import matplotlib

# Use a non-interactive backend for saving files.
matplotlib.use('Agg')

import matplotlib.pyplot as plt

def generate_styled_plot(directory_path: str, output_filename: str) -> None:
    """
    Scans a directory for all .txt data files, normalises the start time, and plots
    all data on a single graph with unique markers and line styles for each system.
    The final figure is saved to a file.

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
    # --- 1. Create a single plot and define styles ---
    fig, ax = plt.subplots(figsize=(12, 8))

    # Define lists of styles to cycle through for better readability.
    markers = ['o', 's', '^', 'D', 'v', 'p', '*', '<', '>', 'X']
    linestyles = ['-', '--', '-.', ':']

    try:
        all_files = sorted([f for f in os.listdir(directory_path) if f.endswith(".txt")])
    except FileNotFoundError:
        print(f"Error: The directory '{directory_path}' could not be found.")
        return

    plot_index = 0 # Initialise a counter for cycling through styles.

    # --- 2. Loop through all files, process, and plot ---
    for filename in all_files:
        plot_label = None

        if "pH" in filename:
            match_ph = re.search(r'pH(\d+)', filename)
            match_label = re.search(r'pH\d+_(.*)\.txt', filename)
            if match_ph and match_label:
                ph = match_ph.group(1)
                base_label = match_label.group(1).strip()
                plot_label = f"{base_label} (pH {ph})"
        elif "Cu" in filename:
            plot_label = "Cu"
        
        if not plot_label:
            print(f"ℹ️  Skipping unrecognised file: {filename}")
            continue

        file_path = os.path.join(directory_path, filename)
        try:
            data = pd.read_csv(file_path, sep='\t')
            
            time_col_s = 'Time (s)'
            charge_col = 'WE(1).Charge (C)'

            if time_col_s in data.columns and charge_col in data.columns:
                # Normalise time to start at 0.
                initial_time = data[time_col_s].iloc[0]
                data[time_col_s] = data[time_col_s] - initial_time

                # Convert time to minutes.
                data['Time (min)'] = data[time_col_s] / 60
                
                # --- Select unique styles for the current plot ---
                marker = markers[plot_index % len(markers)]
                linestyle = linestyles[plot_index % len(linestyles)]

                # Plot with specified styles. `markevery` prevents the plot from being too crowded.
                ax.plot(data['Time (min)'], data[charge_col], label=plot_label,
                        marker=marker, linestyle=linestyle, markevery=150, markersize=7)
                
                plot_index += 1 # Increment index for the next file's style.
            else:
                print(f"⚠️  Warning: Could not find required columns in '{filename}'.")

        except Exception as e:
            print(f"❌ An error occurred while processing '{filename}': {e}")

    # --- 3. Configure the final plot ---
    ax.set_title('Combined Chronoamperometry Analysis (Time Normalised)')
    ax.set_xlabel('Time (min)')
    ax.set_ylabel('Charge ($C$)')
    ax.legend(title='System', fontsize='small', ncol=2) # Using 2 columns for the legend.
    ax.grid(True, linestyle='--', alpha=0.7)

    # --- 4. Save the figure ---
    try:
        fig.savefig(output_filename, dpi=600, bbox_inches='tight')
        print(f"✅ Plot successfully saved as '{output_filename}'")
    except Exception as e:
        print(f"❌ Error saving file: {e}")

# --- Main execution block ---
if __name__ == '__main__':
    data_directory = 'CAs/'
    generate_styled_plot(data_directory, output_filename="ca_final_styled.tiff")
