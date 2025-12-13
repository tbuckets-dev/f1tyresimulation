# Example tyre model for F1 tyre simulation. Linear analogy.abs

class SimpleTyreModel:
    def __init__(self, lateral_stiffness=10000, longitudinal_stiffness=10000, peak_slip_angle=0.5):
        self.lateral_stiffness = lateral_stiffness
        self.longitudinal_stiffness = longitudinal_stiffness
        self.peak_slip_angle = peak_slip_angle
        
    def calculate_lateral_force(self, slip_angle):
        # Simple linear model (Force = Stiffness * Slip)
        return self.lateral_stiffness * slip_angle * (1 - abs(slip_angle/self.peak_slip_angle))

    def calculate_longitudinal_force(self, slip_ratio):
        # Simple linear model (Force = Stiffness * Slip)
        return self.longitudinal_stiffness * slip_ratio
