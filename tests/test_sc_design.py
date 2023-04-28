"""Compute prop mass fraction of MEV"""
import numpy as np

isp_xenon = 1800
isp_hydrazine = 230

dV_profile = [1600, 75, 300, 75, 300, 75, 300]
isp_profile = [isp_xenon, isp_hydrazine, isp_xenon, isp_hydrazine, isp_xenon, isp_hydrazine, isp_xenon]
payload_mass = [0, 0, 2450, 0, 2450, 0, 2450]

# Apply a 30% margin to delta-V profiles
dV_profile = [x * 1.3 for x in dV_profile]

prop_mass_xenon = 0
prop_mass_hydrazine = 0

# Initial launch mass of MEV
launch_mass = 2500
m_0 = launch_mass

# Iterate over mission profile
for i, dV in enumerate(dV_profile):
    # Get Isp and payload mass for burn
    isp = isp_profile[i]
    payload = payload_mass[i]
    # Compute mass frac for burn
    mass_frac = np.exp(-dV / isp / 9.81)
    m_f = (m_0 + payload) * mass_frac
    used_prop_mass = m_0 + payload - m_f
    m_0 -= used_prop_mass
    if isp == isp_xenon:
        prop_mass_xenon += used_prop_mass
    else:
        prop_mass_hydrazine += used_prop_mass

# Report results
print(f"Total Prop Mass Fraction = {1 - (m_0 / launch_mass)}")
print(f"Mass of Xenon Prop = {prop_mass_xenon}")
print(f"Mass of Hydrazine Prop = {prop_mass_hydrazine}")

m_0 = 6500
dV = 4000
isp = 330
m_f = m_0 * np.exp(-dV / isp / 9.81)
print(m_f)
