Three use cases of our proposed project: 
* 1. Input your own battery cycling data, select and visualize 
representative cycles to get nice plots.
Components: plots, smoothing function, cleaning data functions  
* 2. Look for trends in your own battery cycling data (freedom for user 
to select what trends to look for).  
Components: plots, peak deconvolution and identification, number of 
peaks in a cycle, peak positions, peak widths, peak heights,  
* 3. Input battery cycling data and classify battery as a certain type, 
based off of peak descriptors.  
### Components: 
- Load in Battery Cycling Data
 - Separate cycles 
 - For each cycle calculate; 
	- deconvolute 
	- positions 
	- width 
	- heights 
	- count 
 - Seperate Data 
	- Test 
	- Train 
 - Train ML model (SVM)  
 - Validate model with Test Data 
 - Error Analysis 
 
