import numpy as np
import datetime

'''
Procedure:
----------
Bin supernovae data by day (or month) increments.

Notes:
------
Use groupNdays() for production, while groupmonth() was used in the initial/testing phases.
These routines may be a bit sloppy, but they get the job done.
'''

#====================================================================================================
# Group dates by number of days (fractional days are acceptable)
def groupNdays(date, date0, datef, Ndays):
    '''
    Inputs:
    -------
    date  - List of ordered dates in "yyyy/mm/dd" string format
    date0 - Starting date in format of a datetime.datetime() object
    datef - Ending date in format of a datetime.datetime() object
    Ndays - Bin size for grouping the data (can be a non-integer)
    
    Outputs:
    --------
    datebins, iNdays - Date bins (edges), Indices of input date array within each bin
    '''
    # Initializations
    Ndates   = len(date)
    datemin  = date0
    datebins = []  # Output date bins
    iNdays   = []  # Output date indices belonging to each bin
    j = 0
    
    # Determine the number of bins
    Nbins = int((datef - date0).days / float(Ndays))

    # Initial date in the dataset
    datenow = datetime.datetime.strptime(date[0], '%Y/%m/%d')

    # Loop through each date bin, collect the relevant supernovae
    for i in np.arange(Nbins):

        # Append datemin to the bins list
        datebins.append(datemin)

        # Bounding end date for the current bin
        datemax = datemin + datetime.timedelta(days=Ndays)

        # Initialize the list for this date bin
        thisbin = []

        # Collect the supernovae belonging to the current date bin
        while ((datenow >= datemin) and (datenow < datemax) and (j < Ndates)):
            
            # Add the SN to this date bin
            thisbin.append(j)
            
            # Move on to the next supernova
            j = j + 1
            if (j < Ndates):
                datenow = datetime.datetime.strptime(date[j], '%Y/%m/%d')
    
        # Add thisbin to the master list
        iNdays.append(thisbin)

        # datemax becomes the new datemin
        datemin = datemax

    # Append the final datemax to the bins list
    datebins.append(datemax)

    # We now have the supernova in a list of lists grouped by Ndays
    # ...e.g., iNdays = [[0,1,2,3],[4,5],[6,7,8,9]]...
    return datebins, iNdays


#====================================================================================================
# Group dates by month
def groupmonth(date, y0, m0, d0):
    '''
    Inputs:
    -------
    date - List of ordered dates in "yyyy/mm/dd" format
    y0   - Starting year (e.g., 1900)
    m0   - Starting month (e.g., 1)
    d0   - Starting day (e.g., 1)
    
    Outputs:
    --------
    bins, imonths - Date bins (edges), Indices of input date array within each bin

    Notes:
    ------
    Something not right! len(datebins) should be 1 greater than len(imonths)
    Just reqrite this routine to work the same way as groupNdays...
    '''
    # Initializations
    Ndates = len(date)
    y0   = int(y0)
    m0   = int(m0)
    yold = y0
    mold = m0
    datebins = []  # Output date bins
    imonths  = []  # Output date indices belonging to each bin
    j = 0

    # Determine the number of bins
    date0 = datetime.date(year=y0, month=m0, day=1)
    ymdf  = date[-1].split('/')  # "yyyy/mm/dd"
    datef = datetime.date(year=int(ymdf[0]), month=int(ymdf[1]), day=int(ymdf[2]))
    Nbins = ((datef.year-1) - (date0.year+1))*12 + (12-m0+1) + (int(ymdf[1])+1)
    #year  = y0
    #month = m0
    yold = y0
    mold = m0
    dold = d0
    
    # Initial date in the dataset
    ymdnow  = date[0].split('/')  # "yyyy/mm/dd"
    ynow    = int(ymdnow[0])
    mnow    = int(ymdnow[1])
    dnow    = int(ymdnow[2])
    datenow = datetime.date(year=ynow, month=mnow, day=dnow)

    # Loop through each date bin, collect the relevant supernovae
    for i in np.arange(Nbins):

        # Bounding dates for the current bin
        datemin = datetime.date(year=yold, month=mold, day=dold)
        year  = yold
        month = mold + 1
        if (month > 12):
            month = 1
            year  = yold + 1
        datemax = datetime.date(year=year, month=month, day=dold)
        
        # Append datemin to the bins list
        datebins.append(datemin)

        # Initialize the list for this date bin
        thisbin = []

        # Collect the supernovae belonging to the current date bin
        while ((datenow >= datemin) and (datenow < datemax) and (j < Ndates)):
            
            # Add the SN to this date bin
            thisbin.append(j)
            
            # Move on to the next supernova
            j = j + 1
            if (j < Ndates):
                ymdnow  = date[j].split('/')  # "yyyy/mm/dd"
                ynow    = int(ymdnow[0])
                mnow    = int(ymdnow[1])
                dnow    = int(ymdnow[2])
                datenow = datetime.date(year=ynow, month=mnow, day=dnow)
    
        # Add thisbin to the master list
        imonths.append(thisbin)

        # Update yol, mold, dold so that datemax will become the new datemin
        yold = int(datemax.year)
        mold = int(datemax.month)
        dold = int(datemax.day)
    
    # Append the final datemax to the bins list
    datebins.append(datemax)
    
    # We now have the supernova in a list of lists grouped by months
    # ...e.g., imonths = [[0,1,2,3],[4,5],[6,7,8,9]]...
    return datebins, imonths

