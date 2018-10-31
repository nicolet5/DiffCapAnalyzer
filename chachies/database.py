"""
Database related functions.
"""

import os

import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

DATABASE_URL_PREFIX = 'sqlite:///'
DATABASE_PATH = 'test.db'
DATABASE_URL = DATABASE_URL_PREFIX + DATABASE_PATH

SEED_DATA_FILE = 'data/CS2_33_8_17_10.xlsx'
SEED_DATA_SHEET_NAME = 1
SEED_DATA_NAMES = ['example1', 'example2', 'example3']
SEED_DATA_META = {"exp_class" : "Cycling",
                  "ref_authors" : "Wei He, Nicholas Williard, Michael "
                                  "Osterman, Michael Pecht",
                  "ref_title" : "Prognostics of lithium-ion batteries based "
                                "on Dempster–Shafer theory and the Bayesian "
                                "Monte Carlo method.",
                  "ref_journal" : "Journal of Power Sources",
                  "ref_year" : 2011,
                  "ref_doi" : "https://doi.org/10.1016/j.jpowsour.2011.08.040"}

engine = create_engine(DATABASE_URL, convert_unicode=True)
db_session = scoped_session(sessionmaker(autocommit=False,
                                         autoflush=False,
                                         bind=engine))
Base = declarative_base()
Base.query = db_session.query_property()

def init_db():
    Base.metadata.create_all(bind=engine)

    from models import MasterTable
    for dataset in SEED_DATA_NAMES:
        if not engine.dialect.has_table(engine, dataset):
            print("table {} does not exist yet- adding it now".format(dataset))
            filename = os.path.join(os.path.dirname(__file__), SEED_DATA_FILE)
            ex_df = pd.read_excel(filename, SEED_DATA_SHEET_NAME)
            con = engine.connect()
            ex_df.to_sql(dataset, con, if_exists="replace")
            con.close()
            # insert a new entry of meta data in the master table
            new_entry = MasterTable(dataset=dataset,
                                    exp_class=SEED_DATA_META["exp_class"],
                                    ref_authors=SEED_DATA_META["ref_authors"],
                                    ref_doi=SEED_DATA_META["ref_doi"],
                                    ref_title=SEED_DATA_META["ref_title"],
                                    ref_journal=SEED_DATA_META["ref_journal"],
                                    ref_year=SEED_DATA_META["ref_year"])
            db_session.add(new_entry)
            db_session.commit()
            print("table {} has been added".format(dataset))
        else:
            print("table {} already exists, skipping".format(dataset))
