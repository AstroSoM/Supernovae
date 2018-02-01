import numpy as np
import h5py
import astropy.units as u
import astropy.coordinates as coord
from astropy.io import ascii
from datetime import datetime

'''
Procedure:
----------
Collect RA, DEC, Date, etc. for all of the supernovae in chronological order.
Require RA, DEC, Date, toss out data without this information.
Require Date >= the year 1900.

Output:
-------
An HDF5 file of the filtered and organized supernovae data.

Resources:
----------
Supernovae Data --> https://sne.space/ (Guillochon et al. 2017, ApJ, 835, 64)

Notes:
------
Some bad data still need to be filtered out, like 200+ discovered in one day in the Galactic plane?!
The data entry with index i=31996 has a formatting issue, so I fix it in place.
'''
# Output HDF5 filename
fh5 = "/Users/salvesen/outreach/asom/supernovae/data/SNedata.h5"

# Do not include any supernova from 2018 onward
endyear = 2018

# Collect the raw supernovae data
# RA  : [ 00h:00m:00.0s,  24h:00m:00.0s]
# DEC : [-90d:00m:00.0s, +90d:00m:00.0s]
fcsv  = "/Users/salvesen/outreach/asom/supernovae/data/The_Open_Supernova_Catalog.csv"
table = ascii.read(fcsv, header_start=0, data_start=1)
name  = table['Name']
date  = table['Disc. Date']  # 'yyyy/mm/dd'
mmax  = table['mmax']  # Maximum apparent AB magnitude
host  = table['Host Name']
ra    = table['R.A.']  # [hour:arcmin:arcsec]
dec   = table['Dec.']  # [degree:arcmin:arcsec]
z     = table['z']     # Redshift
type  = table['Type']  # Classification (e.g., Ia, II)

# Fill in missing values with NaN's
name = name.filled(np.nan)
date = date.filled(np.nan)
mmax = mmax.filled(np.nan)
host = host.filled(np.nan)
ra   = ra.filled(np.nan)
dec  = dec.filled(np.nan)
z    = z.filled(np.nan)
type = type.filled(np.nan)

# Function to convert 'yyyy/mm/dd' string to yyyy.yy float
def fractionalyear(yyyymmdd):
    yyyymmdd = yyyymmdd.split('/')
    yyyy     = yyyymmdd[0].zfill(4)
    mm       = yyyymmdd[1]
    dd       = yyyymmdd[2]
    dateobj  = datetime.strptime(yyyy+'/'+mm+'/'+dd, '%Y/%m/%d')
    year_part   = dateobj - datetime(year=dateobj.year, month=1, day=1)
    year_length = datetime(year=dateobj.year+1, month=1, day=1) - datetime(year=dateobj.year, month=1, day=1)
    year_frac   = dateobj.year + (float(year_part.days) / float(year_length.days))
    return year_frac

# Loop through the supernovae and discard those without date information and/or RA/DEC information
Nlines = len(date)
igood  = []
for i in np.arange(Nlines):
    # We require adequate RA/DEC and date information
    thisdate = date[i].split(',')[0]
    datefmt  = thisdate.split('/')  # Expecting yyyy/mm/dd
    thisra   = ra[i].split(',')[0]
    thisdec  = dec[i].split(',')[0]
    if ((thisdate != 'nan') and (thisra != 'nan') and (thisdec != 'nan') and (len(datefmt) == 3)):# and (i != 28766)):  # <-- old formatting issue with i = 28766, but fine now
        # Do not include any supernovae beyond the specified year
        if (int(datefmt[0]) < endyear):
            # Append the supernova to the list of "good" ones
            igood.append(i)

# Keep only the good supernovae
name  = name[igood]
date  = date[igood]
mmax  = mmax[igood]
host  = host[igood]
ra    = ra[igood]
dec   = dec[igood]
z     = z[igood]
type  = type[igood]

# Loop through the supernovae with date info and sort chronologically
Nlines = len(date)
time   = np.zeros(Nlines)
for i in np.arange(Nlines):
    thisdate = date[i].split(',')[0]
    if (i == 37187): thisdate = '1948/05/28'  # <-- formatting issue with i = 37187
    print i, thisdate
    time[i] = fractionalyear(yyyymmdd=thisdate)

# Sort the supernovae data chronologically
isort = np.argsort(time)
time  = time[isort]
name  = name[isort]
date  = date[isort]
mmax  = mmax[isort]
host  = host[isort]
ra    = ra[isort]
dec   = dec[isort]
z     = z[isort]
type  = type[isort]

# Only keep the first entries of the data
# ...(may want to average all entries or something like that in the future)...
for i in np.arange(Nlines):
    #time[i] = time[i].split(',')[0]  <-- cannot split floats
    name[i] = name[i].split(',')[0]
    date[i] = date[i].split(',')[0]
    #mmax[i] = mmax[i].split(',')[0]  <-- cannot split floats
    host[i] = host[i].split(',')[0]
    ra[i]   = ra[i].split(',')[0]
    dec[i]  = dec[i].split(',')[0]
    z[i]    = z[i].split(',')[0]
    type[i] = type[i].split(',')[0]

# Fill in NaN apparent magnitudes with the mean value
mmax_mean = np.nanmean(mmax)  # Mean apparent AB magnitude
mmax_min  = np.nanmin(mmax)   # Brightest apparent AB magnitude
mmax_max  = np.nanmax(mmax)   # Dimmest apparent AB magnitude
for i in np.arange(Nlines):
    if (np.isnan(mmax[i])):
        mmax[i] = mmax_mean
    #if (mmax[i] < 6.5):  # Magnitude 6.5 is just visible to the human eye
    #    print "This SN was visible by eye: ", name[i]

# Toss out the 12 supernovae prior to 1900
ikeep = []
for i in np.arange(Nlines):
    # This is a hack because datetime does not like pre-1900 dates
    thisyear = int(date[i].split('/')[0])
    if (thisyear >= 1900):
        thisdate = datetime.strptime(date[i], '%Y/%m/%d')
        ikeep.append(i)
time  = time[ikeep]
name  = name[ikeep]
date  = date[ikeep]
mmax  = mmax[ikeep]
host  = host[ikeep]
ra    = ra[ikeep]
dec   = dec[ikeep]
z     = z[ikeep]
type  = type[ikeep]

# New number of lines in the dataset after truncating dates < 1900
Nlines = len(date)

# THIS NEXT BIT TAKES UP THE MOST AMOUNT OF COMPUTING TIME
# Collect the RA/DEC for each supernova in units of [degrees]
# RA  : [  0.0d, 360.0d]
# DEC : [-90.0d, +90.0d]
ra_list = []
dec_list = []
l_list = []
b_list = []
for i in np.arange(Nlines):
    radec = coord.SkyCoord(ra[i], dec[i], unit=(u.hour, u.deg), frame='icrs')
    ra_list.append(radec.ra.deg)    # [degrees]
    dec_list.append(radec.dec.deg)  # [degrees]
    # Galactic coordinates (l,b)
    lonlat = radec.transform_to('galactic')
    l_list.append(lonlat.l.deg)  # [degrees]
    b_list.append(lonlat.b.deg)  # [degrees]

# Convert RA/DEC from [degrees] to angular coordinates [degrees:arcmin:arcsec]
# RA  : [  0d:00m:00.0s, +360d:00m:00.0s]
# DEC : [-90d:00m:00.0s,  +90d:00m:00.0s]
ra_list  = coord.Angle(ra_list * u.degree)
dec_list = coord.Angle(dec_list * u.degree)
l_list   = coord.Angle(l_list * u.degree)
b_list   = coord.Angle(b_list * u.degree)

# Bound RA/DEC to conform to our plotting coordinate range [degrees:arcmin:arcsec]
# RA  : [-180d:00m:00.0s, +180d:00m:00.0s]
# DEC : [ -90d:00m:00.0s,  +90d:00m:00.0s]
ra_list  = ra_list.wrap_at(180.0 * u.degree)
dec_list = dec_list.wrap_at(90.0 * u.degree)
l_list   = l_list.wrap_at(180.0 * u.degree)
b_list   = b_list.wrap_at(90.0 * u.degree)

# Convert RA/DEC to radians
ra_list = ra_list.radian
dec_list = dec_list.radian
l_list   = l_list.radian
b_list   = b_list.radian

# Write out the results to an HDF5 file
f = h5py.File(fh5, 'w')
f.create_dataset('time', data=time)  # yyyy.yy
f.create_dataset('name', data=name)
f.create_dataset('date', data=date)  # 'yyyy/mm/dd'
f.create_dataset('mmax', data=mmax)
f.create_dataset('host', data=host)
f.create_dataset('ra',   data=ra_list)   # [-180d:00m:00.0s, +180d:00m:00.0s]
f.create_dataset('dec',  data=dec_list)  # [ -90d:00m:00.0s,  +90d:00m:00.0s]
f.create_dataset('l',    data=l_list)    # [-180d:00m:00.0s, +180d:00m:00.0s]
f.create_dataset('b',    data=b_list)    # [ -90d:00m:00.0s,  +90d:00m:00.0s]
f.create_dataset('z',    data=z)
f.create_dataset('type', data=type)
f.close()

