# Descriptor Function Developments

### Introduction

The purpose of this notebook is to discuss the principles behind the descriptor generating functions used to analyze battery data. It explains the inputs and outputs from the overall package as well as the components that make up the function.

### Installation guidelines

These functions require the following pip installs

```
pip install lmfit
pip install numpy
pip install pandas
pip install peakutils
pip install scipy
```
### Import statements

```
import descriptors
```

## Data Generation

Before this package can be used, the following script is used to extract clean separated cycle data from the raw battery data. This can be done using the following code from the `chachifuncs` package.

```
import chachifuncs
chachifuncs.get_all_data(base_folder, raw_data_folder)
```
Where `base_folder` is the path to the folder used for data management and `raw_data_folder` is the folder in `base_folder` that contains the raw battery data. This extracts, cleans, and categorizes raw battery data. It will generate a folder named `Clean_Separated_Cycles`. The path to this folder must be used to run the main function described below.

## Running Main Function

This function generates an excel sheet of descriptors from a folder containing clean cycle data. The python call for this function can be written as follows:

```
import descriptors
descriptors.ML_generate('import_filepath')
```

`import_filepath` must be the directory that contains cleaned cycle ata. The results of the descriptor generation are outputted to an excel spreadsheet titled 'describe.xlsx' in the current directory.

# Components

## Fitting Class

This class contains the function that peform the actual fitting. The process of fitting is represented by the following diagram.

![Images/fittingFlowChart.jpg](Images/fittingFlowChart.jpg)

This process is carried out by the `lmfit` package.

### LMfit

lmfit is an open-source fitting platform based on `scipy.optimize.leastsq`. It uses a Levenberg-Marquart algorithm with numerically-calculated derivatives from MINPACK's lmdif function. For our use case. We needed to fit a mixture of Pseudo-Voight distributions with a 4th degree polynomial background. The Pseudo-Voight distribution has the following form:

Each function is fit with a linear combination of Pseudo-Voight distributions and a 4th order polynomial background. The error of this fit is quantified using Reduced Chi Squared, Akaike information criterion (AIC), and Bayesian infromation criterion (BIC) parameters. More information regarding the model and the descriptors parameters can be found in Descriptor_Examples.ipynb.

### Overall Code Use

The overall fit can be obtained using the following:
```
import descriptors

descriptors.fitters.descriptor_func(V_series, dQdV_series, cd, 5, 'battery name')
```

In this function, `V_series` and `dQdV_series` are the pandas series objects for the $x$ and $f(x)$ inputs to the fit. They are generated and used in the function `process.imp_one_cycle`.

`cd` is either 'c' for charge or 'd' for discharge, `5` is the cycle number, and `bat` will contain the battery name. the output of this fuction will be a dictionary containing the descriptors described above.

## Process Class

These functions execute the lmfit peak fitting function and properly organize the pandas dataframe of descriptors. This pandas dataframe has the following form.

'names'| 'ch_0'| '...'| 'ch_18'| 'ch_AIC'| 'ch_BIC'| 'ch_red_chi'| 'dc_0'| '...'|'dc_18'| 'dc_AIC'| 'dc_BIC'| 'dc_red_chi'
--|--|--|--|--|--|--|--|--|--|--|--|--
 | | | | | | | | | | | | 
 
 Each row of the dataframe is an individual cycle. Briefly, each battery cycle is run to develop a dataframe of either charge or discharge data. These dataframes are iteratively conocated vertically and the name of each battery is inserted into the dataset. This process is repeated for the discharge cycles and the charge/discharge dataframes are conocated along the column axis.

### Descriptor Keys

the 'ch_'/'dc_' prefix is for the charge/discharge descriptors and will be used in this table as 'pref':

DataFrame Entry | Descriptors
------|------
pref_0 to pref_3 | polynomial coefficient in order of degree
pref_4, 7, 10, ... | peak location (V)
pref_5, 8, 11, ... | peak height (dQ/dV)
pref_6, 9, 12, ... | peak $\sigma$

### Process class work flow

This call graph was generated on a set of two batteries with 16 cycles total. It shows the structure of the `descriptors` package when `ML_generate` is called.

![Images/filter_none_overall.png](Images/filter_none_overall.png)

This figure was generated using the package pycallgraph. It can be found at the following GitHub repository: https://github.com/gak/pycallgraph/#python-call-graph

It is installable with the following lines in a python terminal:
```
pip install pycallgraph
pip install graphviz
```