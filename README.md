# DiffCapAnalyzer [![Build Status](https://travis-ci.com/nicolet5/DiffCapAnalyzer.svg?branch=master)](https://travis-ci.com/nicolet5/DiffCapAnalyzer) ![Python status](https://img.shields.io/badge/python-3.6%20%7C%203.7%20%7C%203.8-blue)
## Package for Battery Cycling Data Visualization and Analysis
This package is intended to quantitatively analyze raw cycling data by identifying and parameterizing peaks found in the differential capacity plots. Differential capacity plots (dQ/dV) can be very powerful for uncovering battery performance characteristics, as the peaks that appear in these plots correspond to the various electrochemical events. However, because of the large amount of data gathered during cycing experiments, many researchers report subsets of cycles and purely qualitative conclusions. This package adds the ability to quantify this type of analysis by cleaning battery cycling datasets and obtaining peak locations, widths, amplitudes, and other descriptors for every charge/discharge cycle in the data. To this end, this tool develops individualized fitted models for each charge and discharge cycle in the data set, comprised of a gaussian baseline and pseudo-voigt distributions at each peak location. 

Additionally, there is a DASH based visualization app that can be used as the user interface. Users can upload raw cycling data, either collected via a MACCOR or an Arbin cycler. The app will then process the data and add a few files to the database: the raw data, the cleaned data, and the peak descriptors for every cycle. The app also allows users to scroll through cycles and better understand the differential capacity curves. Additionally, there is a section to evaluate the fit of the gaussian baseline, and tailor the peak finding process. The user can also download the peak descriptors using the "Download CSV" file button in the app. 

Additionally, some machine learning was done to classify between two different cathode chemistries, LiCoO2 and LiFePO4. Data sets for these chemistries were obtained from the CALCE website(https://web.calce.umd.edu/batteries/data.htm). Once this data was cleaned and labelled, a 20-80 test-train split was done and a support vector classifier was utilized, with a final test set accuracy of 77%. 

### How to Install
```
pip install diffcapanalyzer 
```
### Software Dependencies 
- Python3 
- For python packages see requirements.txt

## Organization of the project
```
|   app.py
|   LICENSE
|   README.md
|   requirements.txt
|   runTests
|   setup.py
|   __init__.py
|
+---data
|   +---ARBIN
|   |   |   README.md
|   |   |
|   |   +---CS2_33
|   |   |
|   |   \---K2_016
|   |
|   +---databases
|   |       dQdV.db
|   |       init_database.db
|   |
|   +---MACCOR
|   |       example_data.csv
|   |
|   \---ML_data
|           c_descriptors.xlsx
|           descriptors_without_heights.xlsx
|           final_descriptors.xlsx
|           k_descriptors.xlsx
|           svc_model.sav
|           svc_results.png
|
+---diffcapanalyzer
|       app_helper_functions.py
|       chachifuncs.py
|       databasefuncs.py
|       databasewrappers.py
|       descriptors.py
|       __init__.py
|
+---docs
|   |   Poster.pdf
|   |
|   +---images
|   |       diagram.png
|   |
|   \---paper
|       |   paper.md
|       |
|       \---images
|               cleaning_dqdv.png
|               fitting_dqdv.png
|
+---examples
|   |   ProcessData_PlotDescriptors_Examples.ipynb
|   |
|   \---ML
|           SVC_Model.ipynb
|
\---tests
    |   test_app_helper_functions.py
    |   test_chachifuncs.py
    |   test_databasefuncs.py
    |   test_databasewrappers.py
    |   test_descriptors.py
    |   __init__.py
    |
    \---test_data
            test_data.csv
            test_data_mac.csv
```

## Data Visualization
Make sure to install the following dash libraries
```
pip install dash==0.21.0  # The core dash backend
pip install dash-renderer==0.11.3  # The dash front-end
pip install dash-html-components==0.9.0  # HTML components
pip install dash-core-components==0.18.1  # Supercharged components
pip install plotly --upgrade  # Latest Plotly graphing library
```

To run the app run the following in terminal:
```
python app.py
```
Which should return
```
 * Running on http://someurl/ (Press CTRL+C to quit)
```
Type that URL in browser to launch


## Data Requirements
At the moment, the package can only process CSV files and relies on specific column headers for each type of file (Arbin vs. Maccor). Please reference the `data` directory for example files. The column headers for each data type must include and appear exactly as the following: 
* Arbin: 
    * Cycle_Index
    * Data_Point
    * Voltage(V)
    * Current(A)
    * Discharge_Capacity(Ah)
    * Charge_Capacity(Ah)
    * Step_Index
* MACCOR: 
    * Rec
    * Cycle C Step
    * TestTime
    * StepTime
    * Cap. [Ah]
    * Voltage [V]
    * Md
    * Current [A]
