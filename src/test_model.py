import tyre_model

# Create an instance of the tyre model
tyre = tyre_model.SimpleTyreModel()

# Test the model
slip_angle = 0.3
slip_ratio = 0.2

# Magic Formula Lateral Force Test
mu_s = 0.8
mu_k = 0.6
alpha_peak = 45
alpha_zero = 10
C = 100
v = 30

lateral_force = tyre.magic_formula_lateral_force(mu_s, mu_k, alpha_peak, alpha_zero, C, v)
longitudinal_force = tyre.calculate_longitudinal_force(slip_ratio)

print(f"Lateral Force: {lateral_force} N")
print(f"Longitudinal Force: {longitudinal_force}")
