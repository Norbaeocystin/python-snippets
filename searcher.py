#!python3
'''
date: July 2018

Small script to search inside .py files for specific word, 
for example you have lots of scripts in folder and you want look on examples where you used requests
than you simply use get_search() function where path is path to folder which you wants search and search in this case will be "requests"
'''
import os
from sys import stdout

SEARCH = 'import re'
PATH = '/home/oktogen/Desktop/'
FILES = 'py, ipynb, csv, txt, tsv'

class Searcher:
    '''
    Class to search in files
    '''
    
    def __init__(self, search_term = SEARCH, path = PATH, files = FILES):
        self.folders = [item[0] for item in os.walk(path)]
        self.search_term = search_term
        self.files = files
        
    def get_files(self, folder_path):
        '''
        return list of files from folder
        '''
        files = [ item for item in os.listdir(folder_path) if item.split('.')[-1] in self.files]
        if files:
            return [os.path.join(folder_path, item) for item in files]
        
    def scan_folders(self):
        '''
        return list of files from folders
        '''
        files = []
        for item in self.folders:
            files_found = self.get_files(item)
            if files_found:
                files.extend(files_found)
        return files
    
    def search(self):
        '''
        return list of files where is search in text
        '''
        files = self.scan_folders()
        result  = []
        stdout.write( '[' )
        tenth = len(files)//10
        for item in files:
            with open(item, encoding = 'utf8', errors = 'ignore') as f:
                txt = f.read()
                if self.search_term in txt:
                    result.append(item)
            if files.index(item) % tenth == 0:
                stdout.write('#')
        stdout.write('#]')
        return result
