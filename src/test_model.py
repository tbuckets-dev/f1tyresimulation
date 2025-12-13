import tyre_model

# Create an instance of the tyre model
tyre = tyre_model.SimpleTyreModel()

# Test the model
slip_angle = 0.3
slip_ratio = 0.2

lateral_force = tyre.calculate_lateral_force(slip_angle)
longitudinal_force = tyre.calculate_longitudinal_force(slip_ratio)

print(f"Lateral Force: {lateral_force}")
print(f"Longitudinal Force: {longitudinal_force}")
