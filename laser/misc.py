import numpy as np
from scipy.interpolate import interp1d, interp2d

def get_moments(image):
    """
    Compute image centroid and statistical waist from the intensity distribution.
    
    Parameters:
    -----------
    image: 2D numpy array
    """
    # Build axes in pixels
    ny, nx = image.shape
    x, y = np.arange(nx), np.arange(ny)
    X, Y = np.meshgrid(x,y)
    # Zeroth moment
    c0 = np.sum(image)
    # First moments
    cx = np.sum(X*image)/c0
    cy = np.sum(Y*image)/c0
    # Second centered moments
    sx2 = np.sum((X-cx)**2*image)/c0
    sy2 = np.sum((Y-cy)**2*image)/c0
    return cx, cy, 2*np.sqrt(sx2), 2*np.sqrt(sy2)

def get_encircled_energy(image, center="centroid"):
    """
    Compute the encircled energy of an intensity distribution
    
    Parameters
    ----------
    image: 2D numpy array
        Intensity distribution
    
    center: {"centroid", "peak"} or tuple, optional
        Defines from which point is the encircled energy calculated.
    """
    # Get the center position
    if center == "centroid":
        cx, cy, _, _ = get_moments(image)
    elif center == "peak":
        cy, cx = np.unravel_index(np.argmax(image), image.shape)
    else:
        cx, cy = center[0], center[1]
    
    # build radius axis
    ny, nx = image.shape
    x, y = np.arange(nx), np.arange(ny)
    Xc, Yc = np.meshgrid(x-cx,y-cy)
    R, _ = cart2pol(Xc,Yc)
    
    # Sort the radius and get the index
    idx_sort = np.argsort(R, axis=None)
    rad_sort = R.ravel()[idx_sort]
    
    
    # Get the encircled energy
    en_circ = np.cumsum(image.ravel()[idx_sort])
    en_circ = np.insert(en_circ, 0, 0.0)/np.sum(image)
    rad_sort = np.insert(rad_sort, 0, 0.0)
    
    return rad_sort, en_circ

def get_fwhm(intensity, interpolation_factor=1, kind='cubic'):
    """
    Get the Full Width at Half Maximum of the 1D intensity distribution
    
    Parameters
    ----------
    intensity: 1D numpy array
        intensity distribution
    
    interpolation_factor: int, optional
        Interpolate the data for a more accurate calculation
    """
    position = np.arange(intensity.size)
    pos_i = np.linspace(np.min(position), np.max(position), interpolation_factor*position.size)
    inten_i = interp1d(position[:], intensity[:], kind=kind)
    idx = (inten_i(pos_i) >= np.max(inten_i(pos_i))*0.5).nonzero()[0]
    return pos_i[idx[-1] + 1] - pos_i[idx[0]]

def gauss2D(x, y, fwhmx, fwhmy, x0=0, y0=0, offset=0, order=1, int_FWHM=True):
    """
    Define a (super-)Gaussian 2D beam.

    Parameters
    ----------
    x: float 2D np.array
        Horizontal axis of the Gaussian

    y: float 2D np.array
        Vertical axis of the Gaussian

    fwhmx: float
        Horizontal Full Width at Half Maximum

    fwhmy: float
        Vertical Full Width at Half Maximum

    x0: float, optional
        Horizontal center position of the Gaussian

    y0: float, optional
        Vertical center position of the Gaussian

    offset: float, optional
        Amplitude offset of the Gaussian

    order: int, optional
        order of the super-Gaussian function.
        Defined as: exp( - ( x**2 + y**2 )**order )

    int_FWHM: boolean, optional
        If True, the FWHM is the FWHM of the square of the Gaussian (intensity).
        If False, it is the FWHM of the Gaussian directly (electric field).
    """
    coeff = 1.0
    if int_FWHM:
        coeff = 0.5
    return np.exp(-np.log(2) * coeff * ((2 * (x - x0) / fwhmx)**2 + (2 * (y - y0) / fwhmy)**2)**order) + offset

def gauss1D(x, fwhm, x0=0, offset=0, order=1, int_FWHM=True):
    """
    Define a (super-)Gaussian 1D beam. Identical to laser.misc.gauss2D but in 1D.

    Parameters
    ----------
    x: float 1D np.array
        Axis of the Gaussian

    fwhm: float
        Full Width at Half Maximum

    x0: float, optional
        Center position of the Gaussian

    offset: float, optional
        Amplitude offset of the Gaussian

    order: int, optional
        order of the super-Gaussian function.
        Defined as: exp( - ( x**2 )**order )

    int_FWHM: boolean, optional
        If True, the FWHM is the FWHM of the square of the Gaussian (intensity).
        If False, it is the FWHM of the Gaussian directly (electric field).
    """
    coeff = 1.0
    if int_FWHM:
        coeff = 0.5
    return np.exp(-np.log(2) * coeff * ((2 * (x - x0) / fwhm)**2)**order) + offset


def cart2pol(x, y):
    """Convert cartesian to polar coordinates"""
    return np.abs(x + 1j * y), np.angle(x + 1j * y)


def pol2cart(r, theta):
    """Convert polar to cartesian coodinates"""
    return np.real(r * np.exp(1j * theta)), np.imag(r * np.exp(1j * theta))


def array_trim(ar):
    """Trim zeros of 2D map"""
    ar_trim = ar.copy()
    ar_trim = ar_trim[:, ar_trim.any(axis=0)]  # trim columns
    ar_trim = ar_trim[ar_trim.any(axis=1), :]  # trim rows
    return ar_trim


def vect(N):
    """Return a centered array between -0.5 and 0.5"""
    return np.linspace(0, N, num=N) / N - 0.5


def norm(a):
    """Normalise an array by it's maximum value"""
    return a / np.max(np.abs(a))


def text_progress_bar(iteration, num_iteration, max_char = 50):
    """Display a progress bar with the print function"""
    num_bar = int(np.floor(iteration/num_iteration*max_char)+1)
    num_dot = max_char-num_bar-1    
    return print('|'*(num_bar) + '.'*(num_dot) + ' %.1f %%'%((iteration+1)/num_iteration*100), end='\r')

def waist_from_nf(radius, angle, wavelength):
    """
    Calculate the Gaussian beam waist parameters from a near field radius and divergence
    """    
    w0 = radius * np.sqrt( ( 1 - np.sqrt( 1 - ( 2*wavelength / ( radius * np.pi * np.tan(angle) ) )**2 ) ) / 2 )
    zr = w0**2*np.pi/wavelength
    z0 = -radius / np.tan(angle)
    return w0, zr, z0

def rolling_window(a, window):
    """
    Reshape an array to calculate rolling statistics
    """
    shape = a.shape[:-1] + (a.shape[-1] - window + 1, window)
    strides = a.strides + (a.strides[-1],)
    return np.lib.stride_tricks.as_strided(a, shape=shape, strides=strides)

def rolling_mean(a, window):
    """
    Compute the rolling mean
    """
    return np.nanmean(rolling_window(a, window), axis=-1)

def rolling_std(a, window):
    """
    Compute the rolling standard deviation
    """
    return np.nanstd(rolling_window(a, window), axis=-1)

def moving_average(a, window):
    """
    Very fast moving average
    """
    ret = np.cumsum(a, dtype=float)
    ret[window:] = ret[window:] - ret[:-window]
    return ret[window - 1:] / window

def add_noise(image, density=None, amplitude=1, kind='quintic', seed=None):
    """
    Add noise to a 2D numpy array. If "density" is specified, the noise is interpolated to have smooth variations.
    
    Parameters
    ----------
    image: 2D numpy.array
        Image on which the noise should be added
    
    density: int, 2-tuple, optional
        Noise density. if equal to the image size, equivalent to "None"
    
    amplitude: float, optional
        Amplitude of the noise. If "1", image is modulated by +- 100%
    
    kind: {'linear', 'cubic', 'quintic'}
        Type of 2D-interpolation. 'linear' can be used but it is pretty ugly.
    
    seed: int, optional
        Seed for random number generation        
    """
    ny, nx = image.shape
    if density is None:
        density = (nx,ny)
    try:
        dx = density[0]
        dy = density[1]
    except TypeError:
        dx = density
        dy = density
    np.random.seed(seed)
    noise_raw = np.random.rand(int(dy), int(dx))
    x_raw = np.arange(int(dx))
    y_raw = np.arange(int(dy))
    noisefunc = interp2d(x_raw,y_raw,noise_raw, kind=kind)
    x = np.linspace(np.min(x_raw), np.max(x_raw), nx)
    y = np.linspace(np.min(y_raw), np.max(y_raw), ny)
    noise = noisefunc(x,y)
    noise = (noise-np.min(noise))/np.ptp(noise)*2-1
    
    image_noise = image*(1+amplitude*noise)/(1+amplitude)
    image_noise *= np.sum(image)/np.sum(image_noise)
    return image_noise
