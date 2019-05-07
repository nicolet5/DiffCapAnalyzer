Use Cases:
 
1. Input your own battery cycling data, clean and smooth data in 
a standardized manner.
*Components*: 
- Dash App asking to load users cycling data, data type from a dropdown 
menu (Arbin, MACCOR). 
- Read file into dataframe using pd.read_csv, pd.read_excel
- Check for empty cells and delete those rows. Also delete/consolidate 
rows with repeat voltages for when dq/dv is calculated (dV /= 0). 
- From raw data, create new column, calculate dQ/dV for each point, put 
in the new column.
- Plot smoothed, clean data and raw data, and allow user to explore cycles. 
  
2. Look for trends in your own battery cycling data (freedom for user 
to select what trends to look for).  
*Components*:
- Dash App to plot data from a particular dataset
- Provide user with option to plot key descriptors vs. cycle # descriptor 
examples:
	- number of peaks in a cycle
	- peak positions
	- peak widths
	- peak heights, exc.
- Also provide users with a way to visually inspect the model fit for cycles.

3. Input battery cycling data and classify battery as a certain type, 
based off of peak descriptors (applicable for LiFePO4 and LiCoO2 cathodes). 
*Components*: 
- Load in Battery Cycling Data
 - Separate cycles 
 - For each cycle, do a model fit of peaks and calculate:
	- peak positions 
	- peak widths
	- peak heights 
	- number of peaks
 - Separate Data 
	- Test (20%)
	- Train (80%)
 - Train ML model (SVM)  
 - Validate model with Test Data 
 - Error Analysis 
 
Potential Use Case Extensions: 

1. Be able to upload your own data and generate publication-worthy 
plots through the app. Give users the ability to select which 
cycles will be on the plot, color scheme, etc. 

2. Expand abilities to deal with data which is not from an 
Arbin or a MACCOR cycler. One way to deal with this is to 
have user input for which columns to use to calculate dQ/dV.  

3. Report model fit error back to user as a goodness-of-fit measure. 



