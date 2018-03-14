import chachifuncs as ccf
from descriptors import process 
from descriptors import fitters
import glob
import os
import pandas as pd
import pickle
from sklearn import linear_model
from sklearn import preprocessing
from sklearn import svm
from sklearn.model_selection import train_test_split
from sklearn.feature_selection import VarianceThreshold

# Import data
k_list = [f for f in glob.glob('data/K_descriptors/*.xlsx')]
c_list = [f for f in glob.glob('data/C_descriptors/*.xlsx')]

c_data = pd.DataFrame()
for each in c_list:
    df = pd.read_excel(each)
    c_data = c_data.append(df, ignore_index=True)
k_data = pd.DataFrame()
for each in k_list:
    df = pd.read_excel(each)
    k_data = k_data.append(df, ignore_index=True)
data = c_data.append(k_data)
data = data.T.drop_duplicates().T


# reset index and provide 0 1 classifiers
data = data.reset_index(drop=True)

for i in range(len(data)):
    if data.loc[i, ('names')].startswith('CS2_33'):
        data.loc[i, ('label')] = 'LiCoO2'
        data.loc[i, ('lasso')] = 0
    else:
        data.loc[i, ('label')] = 'LiFePO4'
        data.loc[i, ('lasso')] = 1

# split data
train, test = train_test_split(data, test_size=0.2, random_state=1010)


# choose data
train_y = train['lasso']  # what are we predicting
test_y = test['lasso']

train_x = train[['ch_5', 'ch_7', 'dc_5']]  # from LASSO
test_x = test[['ch_5', 'ch_7', 'dc_5']]

train_x_scaled = preprocessing.normalize(train_x, norm='l1')
test_x_scaled = preprocessing.normalize(test_x, norm='l1')

lin_svc = svm.LinearSVC().fit(train_x, train_y)
trainpred = lin_svc.predict(train_x_scaled)  # predict train data
testpred = lin_svc.predict(test_x_scaled)


filename = 'svc_model.sav'
pickle.dump(lin_svc, open(filename, 'wb'))


# load model from disk
class chachies:
    
    def clean(rootdir, path_to_raw_data_folder):
        '''Gets all raw data from the rootdir (ie 'data/') and specified folder
        (path_to_raw_data_folder), i.e. 'Source_Data' (which is within rootdir),
        and then:
        1. separates it into raw cycles and puts them in a folder
        (data/Separated_Cycles/)
        2. cleans those separated cycles and puts them in a folder
        (data/Clean_Separated_Cycles/)
        3. recombines the cleaned, separated cycles and saves those
        data sets in a folder (data/Clean_Whole_Sets/). These folders
        do not have to have existed previously.'''
        assert os.path.exists(rootdir) == 1
        if not os.path.exists(rootdir):
            print('The specified rootdir does not exist.')
        if not os.path.exists(rootdir+'Separated_Cycles/'):
            os.makedirs(rootdir+'Separated_Cycles/')
        if not os.path.exists(rootdir+'Clean_Separated_Cycles/'):
            os.makedirs(rootdir + 'Clean_Separated_Cycles/')
        if not os.path.exists(rootdir + 'Clean_Whole_Sets/'):
            os.makedirs(rootdir + 'Clean_Whole_Sets/')
        ccf.load_sep_cycles(rootdir + path_to_raw_data_folder, rootdir + 'Separated_Cycles/')
        ccf.get_clean_cycles(rootdir + 'Separated_Cycles/',rootdir + 'Clean_Separated_Cycles/')
        ccf.get_clean_sets(rootdir + 'Clean_Separated_Cycles/', rootdir+'Clean_Whole_Sets/')
        return

    def get_descriptors(import_filepath):
        """Generates a dataframe containing charge and discharge
        descriptors/error parameters. Also writes descriptors to an
        excel spreadsheet 'describe.xlsx' import_filepath = filepath
        containing cleaned separated cycles"""

        # checks that the file exists
        assert os.path.exists(import_filepath), 'The file does not exist'

        # check that the whatever is passed to ML_generate is a string
        assert isinstance(import_filepath, str), 'The input should be a string'

        # creates dataframe of descriptors for the charge/discharge
        # cycles of all batteries
        df_ch = process.df_generate(import_filepath, 'c')
        df_dc = process.df_generate(import_filepath, 'd')
        # concats charge and discharge cycles
        df_final = pd.concat([df_ch, df_dc], axis=1)
        #drops any duplicate rows
        df_final = df_final.T.drop_duplicates().T
        # saves data to an excel file
        writer = pd.ExcelWriter('describe.xlsx')
        df_final.to_excel(writer, 'Sheet1')
        writer.save()
        return df_final
    
    
    def classify(filename, test_x, test_y):
        """ Calls the pickled model and runs it on some set of data
        filename = svc_model.sav 
        test_x = contain 3 descriptors (first peak amplitude in charge cycle, first peak
        amplitude in discharge cycle, second peak location in charge cycle)
        test_y = battery type (or predicted battery type) """
        loaded_model = pickle.load(open(filename, 'rb'))
        predict = loaded_model.predict(test_x,test_y)
        result = loaded_model.score(test_x, test_y)
    print(result)
