##### SINCE THERE WAS A PROBLEM ON THE CLUSTER INSTALLATION OF RESKIT
##### SOME CORE FUNCTIONS HAD TO BE USED DIRECTLY AND ARE THEREFORE COPIED HERE
import numpy as np
from scipy.stats import weibull_min

def apply_logarithmic_profile_projection(measured_wind_speed, measured_height, target_height, roughness, displacement=0, stability=0):

    return measured_wind_speed * (np.log((target_height - displacement) / roughness) + stability) / (np.log((measured_height - displacement) / roughness) + stability)

def calculate_weibull_params(wind_speed_data):
    """
    Fits a Weibull distribution to wind speed data and returns the shape and scale parameters.

    Parameters
    ----------
    wind_speed_data : array-like
        Wind speed data for which Weibull parameters are to be calculated.

    Returns
    -------
    shape : float
        Weibull shape parameter (k).
    scale : float
        Weibull scale parameter (λ).
    """
    wind_speed_data = wind_speed_data[np.isfinite(wind_speed_data)]
    shape, loc, scale = weibull_min.fit(wind_speed_data, floc=0)  # Setting location to zero
    return shape, scale