import numpy as np
from scipy.interpolate import splrep, splev
from scipy.stats import norm
import pandas as pd
from scipy.optimize import curve_fit

###################### ORIGINAL CODE FROM:
# author='D. Severin Ryberg',
# url='https://github.com/FZJ-IEK3-VSA/windtools'
# Windtools, FZJ-IEK3-VSA

############ ADDED CUT-IN WIND SPEED OPTION ################

capFac = np.array([0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 11.0, 12.0, 13.0, 14.0, 15.0, 16.0, 17.0, 
          18.0, 19.0, 20.0, 21.0, 22.0, 23.0, 24.0, 25.0, 26.0, 27.0, 28.0, 29.0, 30.0, 31.0, 32.0, 33.0, 34.0, 35.0, 
          36.0, 37.0, 38.0, 39.0,  40.0, 41.0, 42.0, 43.0, 44.0, 45.0, 46.0, 47.0, 48.0, 49.0, 50.0, 51.0, 52.0, 53.0, 
          54.0, 55.0, 56.0, 57.0, 58.0,  59.0, 60.0, 61.0, 62.0, 63.0, 64.0, 65.0, 66.0, 67.0, 68.0, 69.0, 70.0, 71.0, 
          72.0, 73.0, 74.0, 75.0, 76.0, 77.0,  78.0, 79.0, 80.0, 81.0, 82.0, 83.0, 84.0, 85.0, 86.0, 87.0, 88.0, 89.0, 
          90.0, 91.0, 92.0, 93.0, 94.0, 95.0, 96.0,  97.0, 98.0, 99.0, 100.0,])

constA = np.array([-0.8691217362419719, -0.5846306874157908, -0.4199402034594731, -0.39102684258488274, 
          -0.3894573187489953, -0.4058020013186425, -0.40432027949816374, -0.39236913666698187, -0.3819249132228733, 
          -0.36330046354548506, -0.3435178362137303, -0.3178321425403834, -0.29117508148616195, -0.269508217230584, 
          -0.2532127879218888, -0.23716397286478894, -0.22262634723157404, -0.20608305884473196, -0.18294597412929683, 
          -0.1595198473797326, -0.1370173698072664, -0.11673980125939647, -0.10109357095443004, -0.08657611801800887, 
          -0.07475367908452243, -0.0632268060157558, -0.05125428172949209, -0.039703953493727594, -0.028335883786178517, 
          -0.01558658032251571, -0.0023729354603777156, 0.012792316480288236, 0.034139993622620955, 0.054711366860818865, 
          0.07301254668013582, 0.0898846001854323, 0.10482533277884826, 0.1150798118926572, 0.11964163861256258, 
          0.1242663158085397, 0.1294060065593988, 0.1352503099574173, 0.14152170196334551, 0.14683148290674713, 
          0.15136974087405913, 0.15579167325105514, 0.16027451616989363, 0.16455629622664028, 0.16836020011407535, 
          0.17250900734008895, 0.1765350074146051, 0.18057485786938174, 0.18426444139957254, 0.1885531927827845, 
          0.19215673631235866, 0.19482283957199606, 0.19705093291250078, 0.19823204136166156, 0.1986947366716821, 
          0.19857859581037052, 0.19826130240180936, 0.19787106118220874, 0.19697825851443274, 0.19541633763382596, 
          0.19326578494880048, 0.19090088568221777, 0.18833523184930082, 0.1856944901502562, 0.1823018438171243, 
          0.17902157722026388, 0.17583645944964005, 0.17433875596971168, 0.17282643301966263, 0.17183139919421217, 
          0.1712745290384288, 0.17100886657189338, 0.17155504072621522, 0.17181169091183046, 0.1717475206313266, 
          0.17205953689104467, 0.17203759637770671, 0.17135373589368072, 0.17038596526121402, 0.1696531890637046, 
          0.16777914643443562, 0.16631979884256623, 0.1650077001337763, 0.1638990474023653, 0.16392813072956272, 
          0.16592132918666147, 0.16818170112634986, 0.16826496645049946, 0.1685499709652857, 0.17168741672630294, 
          0.1785778934680895, 0.18353861618665934, 0.17884824961686804, 0.17285863610537955, 0.15069868246914123, 
          0.13128579344491695, 0.11012455979004396,])

constB = np.array([0.30864428729945903, 0.298395231937226, 0.28855482910643393, 0.29670835655698713, 
         0.30694659174340955, 0.3186606646987472, 0.3262109237633102, 0.3309590104414416, 0.3353076855262877, 
         0.3377929657612922, 0.33963490414680153, 0.33994744034478136, 0.3397628567355643, 0.3400709179760609, 
         0.34104589967775417, 0.34182215842728025, 0.342677119769971, 0.3430452815466755, 0.34212097609298914, 
         0.3409467860008212, 0.3397912532745987, 0.33891784784556933, 0.33873460341449246, 0.3386213565615072, 
         0.33886827438947414, 0.3390797757839704, 0.3391432173371577, 0.33922232252559076, 0.33926121476773186, 
         0.33900163826510576, 0.33859625081614964, 0.33780110674821306, 0.33589696154420867, 0.33409700749274673, 
         0.33264489345560033, 0.33139670650839426, 0.3304333161479266, 0.33022289054218695, 0.33093232690690216, 
         0.3315942385260518, 0.33213539920570395, 0.3325279563119545, 0.3328180841186797, 0.33324903030112274, 
         0.3337880560119182, 0.3343176761761118, 0.33481440494506853, 0.33532147113139826, 0.3358949127330813, 
         0.3363941497376186, 0.3369001413399903, 0.3373854094451347, 0.33791086689131156, 0.33830763653262885, 
         0.3388061917885345, 0.33945446631863424, 0.3401692545183817, 0.3410558652808998, 0.3420604313985917, 
         0.3431598218970714, 0.34428530273814234, 0.34541702411566705, 0.34662664250084896, 0.34794309830105724, 
         0.3493553281647887, 0.3507948657524085, 0.3522646588773047, 0.3537436504328669, 0.35535160917143216, 
         0.3569385284006994, 0.35850750514375196, 0.35978319892006216, 0.3610620326969219, 0.3622481306704468, 
         0.3633573244159112, 0.3644204304211945, 0.36534953287098765, 0.3663298056163852, 0.36736857090133734, 
         0.36834900739477233, 0.36940125738628526, 0.370576568712213, 0.3718120905892753, 0.3730195804206644, 
         0.3744312805803984, 0.37580157824845994, 0.37720392901934174, 0.3786249969503181, 0.37989766263735397, 
         0.38086578501576873, 0.3818189748119938, 0.38319957281022093, 0.38462943240495706, 0.38567391597445144, 
         0.38618181662154005, 0.38720768445078335, 0.3902082649368858, 0.39378413492769676, 0.4008966514755601, 
         0.4087302008778277, 0.4212662545480378,])

# Define the normalized exponential function
def exponential_cf(ws, k):
    return (1 - np.exp(-k * (ws - 3))) / (1 - np.exp(-k * (15.5 - 3)))

# Function to generate the curve
def generate_exponential_curve(data_points, start_ws=3, end_ws=15.5, step=0.25):
    # Separate the data into wind speeds and capacity factors
    wind_speeds, cf_values = zip(*data_points)

    # Fit the exponential function to the provided data
    popt, _ = curve_fit(exponential_cf, wind_speeds, cf_values)
    k_fitted = popt[0]  # Extract the fitted k value

    # Generate wind speeds in the desired range and increments
    ws_range = np.arange(start_ws, end_ws + step, step)
    cf_curve = exponential_cf(ws_range, k_fitted)

    # Create pairs of (ws, cf) for each increment
    ws_cf_pairs = list(zip(ws_range, cf_curve))

    return ws_cf_pairs

class SyntheticPowerCurve( object ):
    """The Synthetic Wind Turbine Power Curve Generator produces turbine power curves as as function of a turbine's specific capacity

    Initialization Parameters:
    --------------------------
    specificCapacity : numeric
        The specific capacity of the wind turbine in W/m2
         * Can be found from the nameplat capacity divided by the swept area
         * If 'specificCapacity' is provided, 'capacity' and 'rotordiam' will be ignored

    capacity : numeric
        The capacity of the wind turbine in kW
         * If 'capacity' is provided, 'rotordiam' mst also be given

    rotordiam : numeric
        The rotor diameter of the wind turbine in m
         * If 'rotordiam' is provided, 'capacity' mst also be given

    cutout : numeric
        The cut out wind speed of the wind turbine in m/s
    
    """

    def __init__(s, specificCapacity=None, capacity=None, rotordiam=None, cutin=5, cutout=25, input_points=None, wind_speed=None, capacity_factor=None):
        if wind_speed is not None and capacity_factor is not None:
            # If wind_speed and capacity_factor arrays are provided, use them directly
            s.wind_speed = np.array(wind_speed)
            s.capacity_factor = np.array(capacity_factor)
            return
        
        if cutout is None: 
            cutout=25
        if cutin is None: 
            cutin=5

        # Generate wind speed array with 1 m/s bins
        s.wind_speed = list(np.arange(0, cutin, 1))  # Wind speeds from 0 up to (but not including) cut-in
        s.capacity_factor = [0] * len(s.wind_speed)  # Capacity factor is 0 below cut-in speed

        # calculate specific capacity if capacity and rotor diameter are provided
        if specificCapacity is None:
            specificCapacity = capacity*1000/(np.pi*rotordiam**2/4)

        specificCapacity = int(specificCapacity)

        # Use the provided input data to generate wind speeds and capacity factors
        if input_points:
            ws_cf_curve = generate_exponential_curve(input_points)
            # Unpack wind speeds and capacity factors from the generated curve
            ws_fitted, cf_fitted = zip(*ws_cf_curve)

            # Extend wind_speed and capacity_factor arrays with the generated values
            s.wind_speed.extend(ws_fitted)
            s.capacity_factor.extend(cf_fitted)
        else:
            # Generate wind speeds and capacity factors based on the specific capacity
            s.wind_speed.extend(np.exp(constA + constB*np.log(specificCapacity)))
            s.capacity_factor.extend(capFac/100)

        # Generate wind speeds from cut-in to cut-out
        ratedWS = np.arange(s.wind_speed[-1], cutout, 0.25)
        s.wind_speed.extend(ratedWS.tolist())
        s.capacity_factor.extend([1]*len(ratedWS))

        # Convert wind_speed and capacity_factor arrays to numpy arrays
        s.wind_speed = np.array(s.wind_speed)
        s.capacity_factor = np.array(s.capacity_factor)

    def __str__(s):
        out = ""
        for ws,cf in zip(s.ws, s.cf):
            out += "%6.2f - %4.2f\n"%(ws,cf)
        return out

    def plot(s, ax=None, doFormatting=True, **kwargs):
        """Plot the power curve

        Parameters:
        -----------
        ax : matplotlib.Axis ; optional
            The axis to plot on

        doFormatting : bool
            Whether or not plot formatting should be applied 

        **kwargs
            All other arguments are passed on to matplotlib.plot()
        """
        if ax is None:
            import matplotlib.pyplot as plt
            plt.figure(figsize=(7,3))
            ax = plt.subplot(111)

        color=kwargs.pop('color', (0,91/255,130/255))
        linewidth = kwargs.pop('linewidth', 3)
        h = ax.plot(s.wind_speed,s.capacity_factor, color=color, linewidth=linewidth, **kwargs)

        if doFormatting:
            ax.tick_params(labelsize=12)
            ax.set_xlabel("wind speed [m/s]",fontsize=13)
            ax.set_ylabel("capacity output",fontsize=13)
            ax.grid()
            # Set x-ticks at uniform intervals (e.g., every 5 m/s)
            max_ws = int(s.wind_speed.max())
            ax.set_xticks(range(0, max_ws + 1, 5))

        return h

    def _repr_svg_(s): 
        #return str(s)
        import matplotlib.pyplot as plt
        from io import BytesIO

        s.plot()

        f = BytesIO()
        plt.savefig(f, format="svg", dpi=100, bbox_inches='tight')
        plt.close()
        f.seek(0)
        return f.read().decode('ascii')
    
    def convolute_by_gaussian(self, scaling=0.06, base=0.1, extend_beyond_cut_out=True, _min_speed=0.01, _max_speed=40, _steps=4000):
        """
        Convolutes a turbine power curve by a normal distribution function with wind-speed-dependent standard deviation.

        Parameters
        ----------
        scaling : float, optional
            scaling factor, by default 0.06

        base : float, optional
            base value, by default 0.1

        extend_beyond_cut_out : bool, optional
            extend the estimation beyond the turbine's cut out wind speed, by default True

        _min_speed : float, optional
            minimum wind speed value in m/s to be considered, by default 0.01

        _max_speed : int, optional
            maximum wind speed value in m/s to be considered, by default 40

        _steps : int, optional
            number of steps in between the wind speed range, by default 4000

        Returns
        -------
        PowerCurve
            The resulting convoluted power curve

        Notes
        ------
        The wind-speed-dependent standard deviation is computed with: std = wind_speed * scaling + base

        """
        # Initialize wind_speed axis
        ws = np.linspace(_min_speed, _max_speed, _steps)
        dws = ws[1] - ws[0]

        # check if we have enough resolution
        tmp = (scaling * 5 + base) / dws
        if tmp < 1.0:  # manually checked threshold
            if tmp < 0.25:  # manually checked threshold
                raise IndexError("Insufficient number of 'steps'")
            else:
                print("WARNING: 'steps' may not be high enough to properly compute the convoluted power curve. Check results or use a higher number of steps")

        # Initialize vanilla power curve
        selfInterp = splrep(ws, np.interp(ws, self.wind_speed, self.capacity_factor))

        cf = np.zeros(_steps)
        sel = ws < self.wind_speed.max()
        cf[sel] = splev(ws[sel], selfInterp)

        cf[ws < self.wind_speed.min()] = 0  # set all wind_speed less than cut-in speed to 0
        cf[ws > self.wind_speed.max()] = 0  # set all wind_speed greater than cut-out speed to 0 (just in case)
        cf[cf < 0] = 0  # force a floor of 0

        # Begin convolution
        convolutedCF = np.zeros(_steps)
        for i, ws_ in enumerate(ws):
            convolutedCF[i] = (norm.pdf(ws, loc=ws_, scale=scaling * ws_ + base) * cf).sum() * dws

        # Correct cutoff, maybe
        if not extend_beyond_cut_out:
            convolutedCF[ws > self.wind_speed[-1]] = 0

        # Done!
        ws = ws[::40]
        convolutedCF = convolutedCF[::40]
        return SyntheticPowerCurve(wind_speed=ws, capacity_factor=convolutedCF)
    
    def simulate(self, wind_speed):
        """
        Applies the power curve to the given wind speeds.
        """
        powerCurveInterp = splrep(self.wind_speed, self.capacity_factor)
        output = splev(wind_speed, powerCurveInterp)

        if isinstance(wind_speed, pd.DataFrame):
            output = pd.DataFrame(output, index=wind_speed.index, columns=wind_speed.columns)
        return output  # Fixed typo here