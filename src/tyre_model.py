# Example tyre model for F1 tyre simulation. Linear analogy.abs
import math

class SimpleTyreModel:
    def __init__(self, lateral_stiffness=10000, longitudinal_stiffness=10000, peak_slip_angle=0.5):
        self.lateral_stiffness = lateral_stiffness
        self.longitudinal_stiffness = longitudinal_stiffness
        self.peak_slip_angle = peak_slip_angle
        
    def calculate_longitudinal_force(self, slip_ratio):
        # Simple linear model (Force = Stiffness * Slip)
        return self.longitudinal_stiffness * slip_ratio

    def magic_formula_lateral_force(self, mu_s, mu_k, alpha_peak, alpha_zero, C, v):
        """
        Calculate the lateral force using the Magic Formula.
        
        Parameters:
        - mu_s: Static friction peak
        - mu_k: Kinematic friction
        - alpha_peak: Peak slip angle at which mu_s is reached (in radians)
        - alpha_zero: Zero slip angle (in radians)
        - C: Curvature factor (a coefficient that accounts for the geometry of the track)
        - v: Speed of the vehicle (in m/s)
        
        Returns:
        - F_lateral: Lateral force (in Newtons)
        """

        # Convert angles to radians if they are not already
        alpha_peak = math.radians(alpha_peak)
        alpha_zero = math.radians(alpha_zero)

        # Calculate the slip angle
        beta = math.atan2(C * v, mu_s * 9.81) - alpha_zero

        # Calculate the lateral force using the Magic Formula
        if beta <= alpha_peak:
            F_lateral = (mu_k + mu_s * math.tan(beta)) * 9.81 * 0.75 * C * v ** 2
        else:
            F_lateral = mu_k * 9.81 * 0.75 * C * v ** 2

        return F_lateral
