import numpy as np
import h5py
from PIL import Image

'''
Procedure:
----------
For the Milky Way panorama, retreive the RGB values of the pixels interior to the Hammer projection ellipse.

Output:
-------
HDF5 file containing the information needed to plot the Milky Way panorama on a Hammer projection
(Grids of longitudes, latitudes, RGB values, along with a color tuple)

Resources:
----------
Milky Way Hammer-Aitoff projection --> http://www.milkywaysky.com/licenses.html (Mellinger 2009, PASP 121, 1180)

Notes:
------
I can't figure out how to plot RBG colors on a Hammer projection plot (went with grayscale instead)
https://stackoverflow.com/questions/22222733/how-to-plot-an-irregular-spaced-rgb-image-using-python-and-basemap
https://stackoverflow.com/questions/29232439/plotting-an-irregularly-spaced-rgb-image-in-python/29232957
'''

# Input JPG filename
fjpg = "/Users/salvesen/outreach/asom/supernovae/data/mwpan2_Aitoff_2000x1000.jpg"

# Output HDF5 filename
fout = "/Users/salvesen/outreach/asom/supernovae/data/milkyway.h5"

# Read in the JPG file (will get RGB values from this)
im = Image.open(fjpg)
rgb_im = im.convert('RGB')

# Hammer projection --- see Wikipedia page for equations: https://en.wikipedia.org/wiki/Hammer_projection
xmin = -2.0 * np.sqrt(2.0)  # Min x-value
xmax = 2.0 * np.sqrt(2.0)   # Max x-value
ymin = -1.0 * np.sqrt(2.0)  # Min y-value
ymax = 1.0 * np.sqrt(2.0)   # Max y-value
Nx = im.size[0]
Ny = im.size[1]
x  = np.linspace(xmin, xmax, Nx)
y  = np.linspace(ymin, ymax, Ny)
lon_grid = np.zeros([Nx, Ny])  # [lonmin, lonmax] = [-180, +180] degrees
lat_grid = np.zeros([Nx, Ny])  # [latmin, latmax] = [-90, + 90] degrees
rgb_grid = np.zeros([Nx, Ny, 3])

# Loop through the pixel in the JPG image
for i in np.arange(Nx):
    for j in np.arange(Ny):
    
        # Check that we are inside the ellipse, get the longitude/latitude
        if ((0.125*x[i]**2 + 0.5*y[j]**2) < 1.0):
            z = np.sqrt(1.0 - (0.25 * x[i])**2 - (0.5 * y[j])**2)
            lon_grid[i,j] = 2.0 * np.arctan(z * x[i] / (2.0 * (2.0 * z**2 - 1.0)))
            lat_grid[i,j] = np.arcsin(z * y[j])
            r, g, b = rgb_im.getpixel((i,j))
            rgb_grid[i,j,:] = [r/255.0, g/255.0, b/255.0]
        
        # Set values to NaN if outside the ellipse
        else:
            lon_grid[i,j]   = np.nan
            lat_grid[i,j]   = np.nan
            rgb_grid[i,j,:] = np.nan

# Flatten the RGB grid for plotting with pcolormesh
colorTuple = tuple(np.array([rgb_grid[:,:,0].flatten(), rgb_grid[:,:,1].flatten(), rgb_grid[:,:,2].flatten()]).transpose().tolist())

# Output colorTuple to an HDF5 file
f = h5py.File(fout, 'w')
f.create_dataset('lon_grid',   data=lon_grid)
f.create_dataset('lat_grid',   data=lat_grid)
f.create_dataset('rgb_grid',   data=rgb_grid)
f.create_dataset('colorTuple', data=colorTuple)
f.close()
