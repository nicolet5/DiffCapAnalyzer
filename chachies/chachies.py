import glob
import os
import pandas as pd
import pickle
from sklearn import linear_model
from sklearn import preprocessing
from sklearn import svm
from sklearn.model_selection import train_test_split
from sklearn.feature_selection import VarianceThreshold


#import data
k_list = [f for f in glob.glob('data/K_descriptors/*.xlsx')]
c_list = [f for f in glob.glob('data/C_descriptors/*.xlsx')]

c_data = pd.DataFrame()
for each in c_list:
    df = pd.read_excel(each)
    c_data = c_data.append(df,ignore_index=True)
k_data = pd.DataFrame()
for each in k_list:
    df = pd.read_excel(each)
    k_data = k_data.append(df,ignore_index=True)
data = c_data.append(k_data)
data = data.T.drop_duplicates().T


#reset index and provide 0 1 classifiers
data = data.reset_index(drop = True)

for i in range(len(data)):
    if data.loc[i, ('names')].startswith('CS2_33'):
        data.loc[i, ('label')] = 'LiCoO2'
        data.loc[i, ('lasso')] = 0
    else:
        data.loc[i,('label')] = 'LiFePO4'
        data.loc[i, ('lasso')] = 1

#split data
train,test = train_test_split(data, test_size=0.2, random_state=1010)


#choose data
train_y = train['lasso'] #what are we predicting
test_y = test['lasso']

train_x = train[['ch_5','ch_7','dc_5']] #from LASSO
test_x = test[['ch_5','ch_7','dc_5']]

train_x_scaled  = preprocessing.normalize(train_x, norm='l1')
test_x_scaled  = preprocessing.normalize(test_x, norm='l1')

lin_svc = svm.LinearSVC().fit(train_x, train_y)
trainpred=lin_svc.predict(train_x_scaled) #predict train data 
testpred=lin_svc.predict(test_x_scaled)


filename = 'svc_model.sav'
pickle.dump(lin_svc, open(filename, 'wb'))


#load model from disk 
loaded_model = pickle.load(open(filename, 'rb'))
result = loaded_model.score(test_x, test_y)
print (result)



