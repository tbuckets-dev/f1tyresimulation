import tyre_model

# Create an instance of the tyre model
tyre = tyre_model.SimpleTyreModel()

# Magic Formula Longitudinal Force Test
mu_s = 1.4 # Static friction peak
mu_k = 1.7 # Kinematic friction
SR = 0.75 # Slip Ratio
V0 = 50 # Reference speed (in m/s)

# Magic Formula Lateral Force Test
mu_s = 1.4 # Static friction peak
mu_k = 1.7 # Kinematic friction
alpha_peak = 5 # Peak slip angle at which mu_s is reached (in radians)
alpha_zero = 2 # Zero slip angle (in radians)
C = 100 # Curvature factor (a coefficient that accounts for the geometry of the track)
v = 50 # Speed of the vehicle (in m/s)

lateral_force = tyre.magic_formula_lateral_force(mu_s, mu_k, alpha_peak, alpha_zero, C, v)
longitudinal_force = tyre.magic_formula_longitudinal_force(mu_s, mu_k, SR, V0)

print(f"Lateral Force: {lateral_force} N")
print(f"Longitudinal Force: {longitudinal_force} N")
