""" Create Spacecraft objects to capture industry design solutions """
from adr_toolbox.architecture import Architecture
from adr_toolbox.spacecraft import Spacecraft, Shuttle, Mothership, Picker
from adr_toolbox.util import load_data, save_data

# Load in the debris space environment scored and clustered
space_env = load_data("top_50_w_unc_clustered")

# Build SpaceLogistics Mission Extension Vehicle
MEV = Shuttle("MEV", 2500, 0.34, 360e-3, 1800, 3, 1,
            6378+400, 65, 0, 300, 10*24*60*60, 75, 2)

# Build SpaceLogistics Mission Robotic Vehicle and Mission Extension Pod
MEP1 = Spacecraft("MEP1", 400, 0.5, 180e-3, 1800, 1, -1)
MEP2 = Spacecraft("MEP2", 400, 0.5, 180e-3, 1800, 1, -1)
MEP3 = Spacecraft("MEP3", 400, 0.5, 180e-3, 1800, 1, -1)
modules = [MEP1, MEP2, MEP3]
MRV = Mothership("MRV", 1800, 0.6, 360e-3, 1800, 4, 2,
                6378+400, 65, 120, 550, 10*24*60*60, 75, 0, modules)

# Build Maxar SSL-1300 OSAM-1
OSAM1 = Shuttle("OSAM-1", 6500, 0.35, 264, 330, 1, 0,
                6378+400, 65, 240, 300, 10*24*60*60, 75, 2)

# Build ClearSpace ClearSpace-1
CLEARSPACE1 = Picker("ClearSpace-1", 500, 0.35, 22, 230, 1, 0,
                6378+400, 65, 0, 10*24*60*60, 75)
CLEARSPACE2 = Picker("ClearSpace-2", 500, 0.35, 22, 230, 1, 0,
                6378+400, 65, 120, 10*24*60*60, 75)
CLEARSPACE3 = Picker("ClearSpace-3", 500, 0.35, 22, 230, 1, 0,
                6378+400, 65, 240, 10*24*60*60, 75)

# Build Astroscale ELSA-M
ELSAM1 = Shuttle("ELSA-M1", 500, 0.35, 100e-3, 1400, 1, 1,
                6378+550, 65, 0, 300, 10*24*60*60, 75, 2)
ELSAM2 = Shuttle("ELSA-M2", 500, 0.35, 100e-3, 1400, 1, 1,
                6378+550, 65, 120, 300, 10*24*60*60, 75, 2)

# Create Architectures for different conservatisms
for gamma in [0, 1, 2]:
    architecture = Architecture(
        2024, 6, space_env,
        [MEV, MRV, OSAM1, CLEARSPACE1, CLEARSPACE2, CLEARSPACE3, ELSAM1, ELSAM2],
        2720, 200000, [1, 0, 0], 8, gamma, 10
    )
    # Optimize the architecture
    architecture.solve_architecture()
    # Save output data
    save_data(architecture, f"commercial_architecture_top_50_debris_{gamma}gamma_V2")
    print(f"Gamma={gamma} Done")
