Three use cases of our proposed project: 
* 1. Input your own battery cycling data, select and visualize 
representative cycles to get nice plots.
Components: 
* GUI asking to load users cycling data, data type from a dropdown 
menu (text, excel). 
* read file into dataframe using pd.read_csv, pd.read_excel
* Check for empty cells and delete those rows 
* from raw data, create new column, calculate dq/dv for each point, put 
in the new column.
* Return to user number of cycles found, ask which representative cycles 
to display or 'all'
* plot dq/dv for selected cycle, show user 

  
* 2. Look for trends in your own battery cycling data (freedom for user 
to select what trends to look for).  
Components: plots, peak deconvolution and identification, number of 
peaks in a cycle, peak positions, peak widths, peak heights,  
* 3. Input battery cycling data and classify battery as a certain type, 
based off of peak descriptors.
Components: peak deconvolution and identification, number of peaks in a 
cycle, peak positions, peak widths, peak heights (all reused from use 
case #2), ML algorithm. 
