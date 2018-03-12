import numpy as np
import pandas as pd
import math as mt
import knn

def test_KNNeighbor():
    #sets up test case
    K = 1
    col1 = 'rWC'
    col2 = 'rCh'
    ed = pd.read_csv("https://raw.githubusercontent.com/UWDIRECT/UWDIRECT.github.io/master/Wi18_content/DSMCER/atomsradii.csv")
    td = pd.read_csv("https://raw.githubusercontent.com/UWDIRECT/UWDIRECT.github.io/master/Wi18_content/DSMCER/testing.csv")
    
    cl = knn.KNNeighbor(ed, td, K, col1, col2)
    
    #verifies function output
    assert isinstance(cl, list), 'Function output should be a list'
    
    #verifies that the list has the proper number of entries
    assert len(td.index) == len(cl), "function didn't generate the right number of classes"
    
    #verifies that the classes determined by the algorithm match the Type set from the training set
    for i in cl: 
        assert ed['Type'].isin([i]).tolist(), 'classes found by the KNN are not inside the Type of the training set'
    
    return

def test_euc():
    #sets test case for euclidean distance calculator
    ed = pd.read_csv("https://raw.githubusercontent.com/UWDIRECT/UWDIRECT.github.io/master/Wi18_content/DSMCER/atomsradii.csv")
    
    er1 = ed.loc[[2]]
    er2 = ed.loc[[3]]
    dist = knn.euc(er1, er2, 'rWC', 'rCh')
    #print(dist)
    
    #assert 1, make sure output is a number
    assert isinstance(dist, float), "result isn't a number"
    
    #assert to make sure that the number is greater or equal to zero
    assert dist >= 0, "distance should be greater than or equal to 0"
    
    #verify that the test case gave the correct result
    assert mt.isclose(dist, 0.1303, abs_tol=10e-5), "Test Case didn't work"
    
    return

def test_sor():
    ed = pd.read_csv("https://raw.githubusercontent.com/UWDIRECT/UWDIRECT.github.io/master/Wi18_content/DSMCER/atomsradii.csv")
    td = pd.read_csv("https://raw.githubusercontent.com/UWDIRECT/UWDIRECT.github.io/master/Wi18_content/DSMCER/testing.csv")
    
    #generates test case
    er1 = td.loc[[2]]
    dfSort = knn.sor(ed, er1, 'rWC', 'rCh')
    
    #test that the output of the function is a pandas dataframe
    assert isinstance(dfSort, pd.DataFrame), "result needs to be a dataframe"
    
    #ensure that the number of euclidean distances matches the size of the training set
    assert len(dfSort.index) == len(ed.index), "incorrect number of elements in the dataframe"
    
    #ensures that the first entry is the smallest item in the dataset
    assert dfSort.loc[0, 'distance'] == dfSort['distance'].min(), "your first value should be the lowest"
        
    return

def test_classDet():
    #loads a test case into the unit test
    ed = pd.read_csv("https://raw.githubusercontent.com/UWDIRECT/UWDIRECT.github.io/master/Wi18_content/DSMCER/atomsradii.csv")
    td = pd.read_csv("https://raw.githubusercontent.com/UWDIRECT/UWDIRECT.github.io/master/Wi18_content/DSMCER/testing.csv")

    er1 = td.loc[[2]]
    dfSort = knn.sor(ed, er1, 'rWC', 'rCh')
    K = 9
    lsClass = knn.classDet(dfSort, ed, K)

    #assert that the output from the function must be a string
    assert isinstance(lsClass, str), 'Class name should be a string'
    
    #assert that the class output is from the classes in the training set
    assert ed['Type'].isin([lsClass]).tolist(), 'the class is not in your training set'
    
    return

def test_kHelp():
    ed = pd.read_csv("https://raw.githubusercontent.com/UWDIRECT/UWDIRECT.github.io/master/Wi18_content/DSMCER/atomsradii.csv")
    td = pd.read_csv("https://raw.githubusercontent.com/UWDIRECT/UWDIRECT.github.io/master/Wi18_content/DSMCER/testing.csv")

    #sets up the k list test case
    Klist = [1, 3, 5, 7, 9]
    kDict = knn.kHelp(ed, td, 'rWC', 'rCh', Klist)
    
    #verifies that the output is a dictionary
    assert isinstance(kDict, dict), "output is not a dictionary"
    
    #verifies that the number of elements in the dictionary is the same as the length of the K vector
    assert len(kDict.keys()) == len(td.index), "not enought K values in the dictionary"
    
    #verifies that each fraction is between 0 and 1
    for vals in kDict.values():
        assert vals >= 0, "Percentages should be larger than 0"
        assert vals <= 1, "Percentages should be less than 1"
    
    return