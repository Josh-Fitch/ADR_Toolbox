""" Create Spacecraft objects to capture industry design solutions """
from adr_toolbox.architecture import Architecture
from adr_toolbox.spacecraft import Spacecraft, Shuttle, Mothership, Picker
from adr_toolbox.util import load_data, save_data

# Load in the debris space environment scored and clustered
space_env = load_data("top_50_w_unc_clustered")

# Build SpaceLogistics Mission Extension Vehicle
MEV = Shuttle("MEV", 500, 0.4, 100e-3, 1400, 1, 1,
            6378+550, 65, 320, 300, 10*24*60*60, 75, 2)

# Build SpaceLogistics Mission Robotic Vehicle and Mission Extension Pod
MEP1 = Spacecraft("MEP1", 200, 0.6, 100e-3, 1400, 1, -1)
MEP2 = Spacecraft("MEP2", 200, 0.6, 100e-3, 1400, 1, -1)
MEP3 = Spacecraft("MEP3", 200, 0.6, 100e-3, 1400, 1, -1)
modules = [MEP1, MEP2, MEP3]
MEP = Mothership("MRV", 2000, 0.5, 250, 330, 1, 1,
                6378+550, 65, 150, 550, 10*24*60*60, 75, 1, modules)

# Build Maxar SSL-1300
OSAM1 = Shuttle("OSAM-1", 500, 0.4, 100e-3, 1400, 1, 1,
                6378+550, 65, 320, 300, 10*24*60*60, 75, 2)

# Build ClearSpace ClearSpace-1
CLEARSPACE1 = Picker("ClearSpace-1", 500, 0.4, 100e-3, 1400, 1, 1,
                6378+550, 65, 320, 10*24*60*60, 75)

# Build Astroscale ELSA-M
ELSAM = Shuttle("ELSA-M", 500, 0.4, 100e-3, 1400, 1, 1,
                    6378+550, 65, 320, 300, 10*24*60*60, 75, 2)

# Create Architecture
architecture = Architecture(space_env, [MEV, MEP, OSAM1, CLEARSPACE1, ELSAM])

# Optimize the architecture
architecture.solve_architecture()

# Save output data
save_data(architecture, "commercial_architecture_top_50_debris")
