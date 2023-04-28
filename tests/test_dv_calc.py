import numpy as np
from astropy import units as u
from poliastro.bodies import Earth

# Set up some useful astrodynamic constants
MU_E = Earth.k.to_value(u.km**3 / u.s**2)
R_E = Earth.R_mean.to_value(u.km)

def calc_low(a_0, a_f, inc_0, inc_f, mass, isp, thrust):
    """
    Calculate delta-V, prop mass, and time of flight for low-thrust transfer
    
    Ref 1: Edelbaum, T. N. “Propulsion Requirements for Controllable Satellites”, 1961
    Ref 2: Kéchichian, J. A. “Reformulation of Edelbaum's Low-Thrust Transfer Problem
            Using Optimal Control Theory”, 1997
    """
    # Orbital velocities
    v_1 = np.sqrt(MU_E / a_0)
    v_2 = np.sqrt(MU_E / a_f)
    # Law of Cosines minimum dV
    delta_v = np.sqrt(v_1**2 + v_2**2 - \
        2*v_1*v_2*np.cos(np.deg2rad(np.abs(inc_0 - inc_f))*np.pi/2))
    # Compute prop mass from ideal rocket equation
    prop_mass = mass * (1 - np.exp(-delta_v * 1000 / isp / 9.81))
    # Calculate time of flight based on thrust and average mass
    tof = delta_v * 1000 / thrust * (mass - 0.5 * prop_mass)

    return delta_v, prop_mass, tof


def calc_imp(a_0, a_f, inc_0, inc_f, mass, isp):
    """
    Calculate delta-V, prop mass, and time of flight for impulsive transfer
    lower-velocity burn includes inc change
    """
    # Orbital velocities
    v_a_1 = np.sqrt(MU_E / a_0)
    v_a_2 = np.sqrt(2 * MU_E / a_0 - 2 * MU_E / (a_0 + a_f))
    v_b_1 = np.sqrt(2 * MU_E / a_f - 2 * MU_E / (a_0 + a_f))
    v_b_2 = np.sqrt(MU_E / a_f)
    # Check if transfer is increasing or decreasing altitude
    if a_f > a_0:
        # If altitude increasing, do inc change in second burn
        dv_1 = np.abs(v_a_1 - v_a_2)
        dv_2 = np.sqrt(v_b_1**2 + v_b_2**2 - \
            2*v_b_1*v_b_2*np.cos(np.deg2rad(np.abs(inc_0-inc_f))))
    else:
        dv_1 = np.sqrt(v_a_1**2 + v_a_2**2 - \
            2*v_a_1*v_a_2*np.cos(np.deg2rad(np.abs(inc_0-inc_f))))
        dv_2 = np.abs(v_b_1 - v_b_2)
    delta_v = dv_1 + dv_2
    # Compute prop mass from ideal rocket equation
    prop_mass = mass * (1 - np.exp(-delta_v * 1000 / isp / 9.81))
    # Assume Hohmann, or half of transfer orbit period
    tof = np.pi * np.sqrt(((a_0 + a_f) / 2)**3 / MU_E)

    return delta_v, prop_mass, tof


if __name__ == "__main__":
    a0 = 6378 + 800
    af = 6378 + 400
    inc0 = 65
    incf = 67
    mass = 10000
    isp1 = 330
    isp2 = 1800
    thrust = 0.36
    dv, prop_mass, tof = calc_imp(a0, af, inc0, incf, mass, isp1)
    print(dv)
    print(prop_mass)
    print(tof)
    dv, prop_mass, tof = calc_low(a0, af, inc0, incf, mass, isp2, thrust)
    print(dv)
    print(prop_mass)
    print(tof)
