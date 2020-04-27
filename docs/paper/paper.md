
---
title: 'DiffCapAnalyzer: A Python Package for Quantitative Analysis of Total Differential Capacity Data'
tags:
  - Python
  - differential capacity
  - dQ/dV
  - cycling data
authors:
  - name: Nicole L. Thompson
    orcid: 0000-0003-3411-7373
    affiliation: 1
  - name: Sarah Alamdari
    affiliation: 1
  - name: Theodore A. Cohen
    affiliation: "1, 2, 3"
  - name: Grant A. Williamson
    affiliation: 3
  - name: Vincent C. Holmberg
    affiliation: 1
  - name: David A. C. Beck
    affiliation: 1

affiliations:
 - name: Dept. of Chemical Engineering, University of Washington
   index: 1
 - name: Dept. of Molecular Engineering, University of Washington
   index: 2
 - name: Dept. of Material Science and Engineering, University of Washington
   index: 3
date: 26 April 2020
bibliography: paper.bib
---

## Summary 
In order to study long-term degradation and charge storage mechanisms in batteries, researchers often cycle these electrochemical cells for hundreds or even thousands of charge and discharge cycles. The raw data produced during cycling can be interpreted via a variety of techniques that each highlight specific aspects of how the battery is functioning.  Differential capacity (dQ/dV) analysis, one such technique, results in plots of the differential capacity – the charge introduced into the battery during a small change in voltage – _vs._ the voltage. Electrochemical reactions result in significant charge introduced into the cell across a small voltage window. In the differential capacity plot, this behavior results in a peak for each electrochemical reaction. Therefore, differential capacity plots are particularly useful for highlighting the various electrochemical events occurring within the cell, specific to each cycle [1-6]. In turn, these peaks carry important characteristics of the electrochemical reaction. For example, the location of the peak indicates at what voltage the reaction occurs, and the area of the peak is linked to the amount of charge exchanged in the reaction. 

Traditionally, when using differential capacity plots, researchers have drawn conclusions based on an arbitrarily chosen subset of cycles and reported mainly qualitative claims on how peaks shift during cycling, due to the difficulties in analyzing the full amount of data produced in the differential capacity plots. Additionally, although it is known that peak shapes and areas correlate to important electrochemical events, only a few papers report using peak deconvolution as a method to interpret dQ/dV plots [2, 3]. Further, there does not exist any standardized method for peak deconvolution of differential capacity plots. 
The presented software aims to address the drawbacks associated with differential capacity analysis by processing cycling data in a chemistry agnostic manner. This is done by calculating differential capacity from the given raw cycling data using Equation 1, cleaning and smoothing the dQ/dV plots, and performing automatic peak locating and deconvolution for every cycle within the dataset. 

$$(dQ/dV)_i=(Q_i-Q_{(i-1)})/(V_i-V_{(i-1)})$$        (1)

In differential capacity curves without any cleaning or smoothing, there  is significant noise and large step-wise changes present. This is a common problem when the denominator of Equation 1 approaches zero [7]. Therefore, in order to accurately identify peaks, the data was cleaned by removing points such that the voltage difference between datapoints was at least 0.001 V. Subsequently, the curve was smoothed using a Savitzky-Golay filter, which is a moving polynomial of specified order fit over a specified number of data points. At the current state of the software, the polynomial order of the Savitzky-Golay filter is set at 3 with a window length of 9 data points, as these seemed the best parameters on the data tested to preserve important features while removing noise. This cleaning process is summarized in Figure 1. 

![Figure 1: Cleaning process on example dQdV](images/cleaning_dqdv.png)

Once the data is clean, the software automatically finds peaks in the dQ/dV curves utilizing the PeakUtils Python package [8], returning the peak heights and the peak locations, as shown by an example cycle in Figure 2a.  These peak heights and locations are then used to inform the model build, which is individualized to each cycle contained in the dataset. The model consists of Pseudo-Voigt distributions positioned at the identified peak locations and a baseline gaussian distribution that captures the area that is not part of the Psuedo-Voigt distributions. The Pseudo-Voigt distribution described by Equations 2 and 3 is simply the linear combination of a Gaussian and a Lorentzian and is often used in fitting experimental spectral data due to it being a highly generalizable function able to fit a large variety of peak shapes [9].

$$f_v(x,A,\mu,\sigma,\alpha)=\frac{(1−\alpha)A}{\sigma_g \sqrt{2 \pi}}\exp{[−{(x− \mu)}^2/2 {\sigma_g}^2]}+\frac{\alpha A}{\pi}[\frac{\sigma}{{(x-\mu)}^2 + \sigma^2}]$$        (2)


$$\sigma_g = \sigma/\sqrt{2 \ln{2}}$$        (3)


Once the model is generated, an optimized fit is found by allowing all parameters to vary except the center position of the Pseudo-Voigt peaks, which is assigned via the previously identified peak locations. Figure 2b presents an example of an initial model fit and the model fit once optimized specifically for that charge cycle.

![Figure 2: Fitting process on example dQdV](images/fitting_dqdv.png)

Further example model fits can be found on GitHub [10]. From this model, peak areas, widths, and shapes can be extracted and examined to give further insight into the electrochemical processes occurring.  The software also utilizes an SQLite database backend to store raw data, cleaned data, model parameters, and peak descriptors for each cycle. In addition to the data processing abilities of the software, a Dash-based web application has been developed where users can upload their own raw data to be processed and visualize the resulting dQ/dV plots and peak descriptors. Users can also evaluate the model fit, alter the threshold for peak detection, and update the model and descriptors in the database. From this application users can also download the cycle descriptors data as a CSV file for their own uses. Further instructions and descriptions of the software functionality can be found on GitHub [10].

Currently, an ongoing research project involves using the tool with a variety of different electrode chemistries to demonstrate the power of this type of quantitative analysis of differential capacity plots. This paper will include electrochemical interpretations of the data generated by the tool and showcases further applicability. This includes using the gathered peak descriptors to train and test a machine learning algorithm which can classify between different battery chemistries.
  
### References: 
[1]	Marzocca, L. M., & Atwater, T. B. (n.d.). Differential Capacity-Based Modeling for In-Use Battery Diagnostics, Prognostics, and Quality Assurance, 4.
[2]	Torai, S., Nakagomi, M., Yoshitake, S., Yamaguchi, S., & Oyama, N. (2016). State-of-health estimation of LiFePO4/graphite batteries based on a model using differential capacity. _J. Power Sources_, 306, 62–69. https://doi.org/10.1016/j.jpowsour.2015.11.070
[3]	Aihara, Y., Ito, S., Omoda, R., Yamada, T., Fujiki, S., Watanabe, T., Park, Y., Doo, S. (2016). The Electrochemical Characteristics and Applicability of an Amorphous Sulfide-Based Solid Ion Conductor for the Next-Generation Solid-State Lithium Secondary Batteries. _Frontiers in Energy Research_, 4. https://doi.org/10.3389/fenrg.2016.00018
[4]	Christophersen, J. P., & Shaw, S. R. (2010). Using radial basis functions to approximate battery differential capacity and differential voltage. _J. Power Sources_, 195(4), 1225–1234. https://doi.org/10.1016/j.jpowsour.2009.08.094
[5]	Christophersen, J. P., Bloom, I., Thomas, E. V., Gering, K. L., Henriksen, G. L., , V. S., & Howell, D. (2006). _Advanced Technology Development Program for Lithium-Ion Batteries: Gen 2 Performance Evaluation Final Report_ (No. INL/EXT-05-00913, 911596). https://doi.org/10.2172/911596
[6]	Weng, C., Cui, Y., Sun, J., & Peng, H. (2013). On-board state of health monitoring of lithium-ion batteries using incremental capacity analysis with support vector regression. _J. Power Sources_, 235, 36–44. https://doi.org/10.1016/j.jpowsour.2013.02.012
[7]	Bloom, I., Jansen, A. N., Abraham, D. P., Knuth, J., Jones, S. A., Battaglia, V. S., & Henriksen, G. L. (2005). Differential voltage analyses of high-power, lithium-ion cells. _J. Power Sources_, 139(1–2), 295–303. https://doi.org/10.1016/j.jpowsour.2004.07.021
[8]	PeakUtils — PeakUtils 1.3.0 documentation. (n.d.). Retrieved December 4, 2018, from https://peakutils.readthedocs.io/en/latest/
[9]	Wertheim, G. K., Butler, M. A., West, K. W., & Buchanan, D. N. E. (1974). Determination of the Gaussian and Lorentzian content of experimental line shapes. _Rev. Sci. Instrum._, 45(11), 1369–1371. https://doi.org/10.1063/1.1686503
[10] Thompson, N. (2018). DiffCapAnalyzer. GitHub Repository. https://github.com/nicolet5/DiffCapAnalyzer


