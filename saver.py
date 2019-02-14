'''
Short function using Pandas to export data from MongoDB to excel
'''
import pandas as pd
from pymongo import MongoClient

#connection to MongoDB
client = MongoClient('mongodb://localhost')


def export_to_excel(name, collection, database):
    '''
    save collection from MongoDB as .xlsx file, name of file is argument of function 
    '''
    data = list(client[database][collection].find({},{'_id':0}))
    df =  pd.DataFrame(data)
    #writer = pd.ExcelWriter('{}.xlsx'.format(name), engine='xlsxwriter')
    df.to_excel(writer, sheet_name='Sheet1')
    #writer.save()
