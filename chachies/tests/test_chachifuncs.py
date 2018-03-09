import chachifuncs as ccf
import pandas as pd

def test_load_sep_cycles():
    """ tests loading seperate cycles """
    try: 
        ccf.get_data('test.xsls')
    except (AssertionError):
        pass
    else:
        pass

def test_sep_cycles():
    """ tests function to seperate cycles """
    #dataframe = pd.read_excel('test.xsls',1) #test should raise an error
    dataframe = [1,2,3] #test should pass if test generates an AssertionError 
    try: 
        ccf.sep_cycles(dataframe)
    except (AssertionError):
        pass
    else:
        raise Exception ("Exception not handled by Asserts")

def test_save_sep_cycles_xsls():
    """tests function that saves seperate cycles"""
    dataframe = pd.read_excel('test.xsls',1)
    cycle_dict = [dataframe,1,2] #should raise AssertionError
    try: 
        ccf.save_sep_cycles_xlsx(cycle_dict, 'battery1', 'seperate_cycles/') 
    except (AssertionError):
        pass
    else: 
        raise Exception ("Exception not handled by Asserts")


