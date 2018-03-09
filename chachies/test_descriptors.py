import descriptors

charge_descript, discharge_descript, name_dat = descriptors.imp_all('data/Clean_Separated_Cycles')
descriptors.pd_create(charge_descript, discharge_descript, name_dat)