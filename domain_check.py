import gc
import multiprocessing as mp
import os
import re
import sys
import time
import warnings
import shutil
import subprocess

import numpy as np
import pandas as pd
from fsplit.filesplit import Filesplit
from pandas.core.common import SettingWithCopyWarning
from tqdm import tqdm

warnings.simplefilter(action="ignore", category=SettingWithCopyWarning)

#Regexes for some keywords, this can also be expanded to include more keywords
dict_regex ={}
dict_regex['email'] = "(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)"
dict_regex['ip'] = "^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])$"
dict_regex['url'] = "http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+"
dict_regex['phone_number'] = "\+(9[976]\d|8[987530]\d|6[987]\d|5[90]\d|42\d|3[875]\d|2[98654321]\d|9[8543210]|8[6421]|6[6543210]|5[87654321]|4[987654310]|3[9643210]|2[70]|7|1)\d{1,14}$"
dict_regex['password'] = "[A-Za-z\d@$!#%*?&\.\-\_]{2,50}$"



def is_something(regex,word):
    '''
    Check if a word satisfies a regex

    Args:
        regex (String): The regular expression with which the word is checked
        word  (String): The word which is checked

    Returns:
        boolean: True, if word matches the regex, else False
    '''
    if (re.fullmatch(regex,word)):
        return True
    else:
        return False

def get_paths(path,with_filenames):
    '''
    Get all files in a folder

    Args:
        path (String): the path of a directory
        with_filenames (boolean): True if file_names should be returned, else False
    
    Returns:
        file_paths (list): The list of file paths
        [file_names (list): The list of file names]

    '''
    file_paths = []
    if with_filenames==True:
        file_names =[]
        for root, dir, files in os.walk(path):
            for file in files:
                file_paths.append(os.path.join(root, file))
                file_names.append(file)
        return file_paths,file_names
    else:
        for root, dir, files in os.walk(path):
            for file in files:
                file_paths.append(os.path.join(root, file))
        return file_paths

def error_output(textmsg, errorcode, bol_programstop):
    """
    Create error messages
    Args:
        textmsg (String): String which is output
        errorcode (String): error code
        bol_programstop (boolean): True if program should be killed, False otherwise
    """
    print ("An error occured {}.".format(textmsg))
    if bol_programstop:
        print ("The program was killed.")
        print (errorcode)
        exit(1)

##Functions for text file output###############################        

def create_result_folder(domain):
    '''
    Create a txt file of a specific domain with relevant subfolders in the results folder
    The results folder will have the same structure as the Domainlist given to the program.

    Args:
        domain (String): A domain in the Domainlist

    Returns:
        void

    '''
    
    domain_lst = domain.split('/')
    for i in range(len(domain_lst)):
        dir_path=''
        for l in range(i):
            dir_path +=('/'+domain_lst[l])
        if not os.path.exists('results/'+dir_path):
            os.mkdir('results/'+dir_path)
    if '.txt' in domain:
        if not os.path.exists('results/'+domain[:4]):
            os.mkdir('results/'+domain[:-4])
    else:
        if not os.path.exists('results/'+domain):
            os.mkdir('results/'+domain)

def create_all_results_folders(file_paths):
    '''
    Create a txt file for each domain with in the results folder
    The results folder will have the same structure as the Domainlist given to the program.

    Args:
        file_paths (list)): All file_paths in Domainlisten

    Returns:
        void

    '''
    if not os.path.exists('results'):
        os.mkdir('results')
    for file in file_paths:
        file_name = file.split('/'+domains_folder_name+'/',1)[1]
        create_result_folder(file_name)
    with open('results/other.txt','w+') as f:
        f.write('')

def check_emails_in_domain_txt(file,dict_key):
    '''
    Check for each email if its domain is in this file, only used for when the output file should be a txt file

    Args:
        file   (String): The file path from current directory
        dict_key (dict): A dictionary with the list of all emails in the input data file(s) as keys 
                         and the list of all information about each data point (i.e. [email, password, ...]) as values.
    
    Returns:
        new_lst (list): List of all emails that were found in the Domainlist

    '''
    emails=list(dict_key.keys())
    lst=[]
    with open(file) as f:
        file_name = file.split('/'+domains_folder_name+'/',1)[1]
        lines = f.readlines()
        for i in range(len(lines)):
            line=lines[i].strip()
            if not line:
                continue
            lst.extend([[email,line] for email in emails if line in email])
            
    new_lst=[[email[0],email[1]] for email in lst if ((('@'+email[1]) in email[0]) or (('.'+email[1]) in email[0]))]
    lst=[email[0] for email in new_lst]
    print()
    print('All emails in domain file: ',file_name)
    print(lst)
    print('------------------------------------')
    print()
    infos = [', '.join(list(filter(None,dict_key[email]))) for email in lst]
    if '.txt' in file_name:
        for i in range(len(lst)):
            try:
                with open('results/'+file_name[:-4]+'/'+lst[i].split('@')[1],'a') as f:
                    f.write(infos[i]+'\n')
            except:
                with open('results/'+file_name[:-4]+'/'+lst[i].split('@')[1],'w+') as f:
                    f.write('\n'.join(infos)+'\n')
    else:
        for i in range(len(lst)):
            try:
                with open('results/'+file_name+'/'+lst[i].split('@')[1],'a') as f:
                    f.write(infos[i]+'\n')
            except:
                with open('results/'+file_name+'/'+lst[i].split('@')[1],'w+') as f:
                    f.write('\n'.join(infos)+'\n')
    return lst


result_list = []
def log_result(result):
    '''
    Append the return values of check_emails_in_domain_[txt|other](args) to result_list.
    (Comment regarding multi-processing: result_list is modified only by the main process, not the pool workers.)

    Args:
        result (list): List of all emails that were found in the Domainlist by check_emails_in_domain_[txt|other]
    
    '''
    result_list.append(result)

def find_email_domains_txt(dict_key,mult_files):
    '''
    Find all emails, where the domain is in Domainlist. 
    Write the email addresses to the specific txt file to which its domain belongs to in the results folder.
    i.e. info@vgem-betzenstein.bayern.de (and its additional information) should be written to bayern.txt in the subfolder Bundeslaender in the folder results.

    Args:
        dict_key (dict): A dictionary with the list of all emails in the input data file(s) as keys 
                         and the list of all information about each data point (i.e. [email, password, ...]) as values.
        mult_files (boolean): Signals whether the input was a folder or a single file
    Returns:
        void
    '''
    #reset global result_list
    global result_list
    result_list=[]

    emails=list(dict_key.keys())
    infos=list(dict_key.values())
    start = time.time()
    #Create results directory
    dirName = 'results'
    try:
        os.mkdir(dirName)
    except FileExistsError:
        pass
    #find all text files with domain names
    file_paths = get_paths(os.path.abspath(os.getcwd())+'/'+domains_folder_name,False)

    #classify each email address
    print()
    print('************************************************')
    print('Start of multiprocessing to find email domains. ')
    num_workers = mp.cpu_count()
    print('Number of parallel cores used for multiprocessing: ',num_workers)
    print('The progressbar shows how many domain files have been processed.')
    print()
    pool = mp.Pool(num_workers)
    jobs=[pool.apply_async(check_emails_in_domain_txt,args=(file_paths[i],dict_key),callback = log_result) for i in range(len(file_paths))]
    pool.close()
    result_list_tqdm=[]
    for job in tqdm(jobs):
        result_list_tqdm.append(job.get())
    
    pool.join()
    bundes_domain_list = [item for sublist in result_list for item in sublist]
    end = time.time()

    diff = end-start
    hrs = diff//60//60
    diff-=hrs*60*60
    mins = diff//60
    diff-=mins*60
    sec = int(diff)
    print("The process has finished in ",hrs," hours ",mins," minutes ", sec,"seconds.")
    print('End of multiprocessing to find email domains. ')
    print('************************************************')
    print()
    #all unclassified email addresses are put into 'other.txt'
    with open('results/other.txt','a') as f:
        for i in range(len(emails)):
            if emails[i] not in bundes_domain_list:
                f.write(', '.join(list(filter(None,infos[i])))+'\n')

##Functions for csv/excel file output###############################   
def check_emails_in_domain_other(file,df,dict_key,file_name):
    '''
    Check for each email if its domain is in this file, only used for when the output file should be a csv/excel file

    Args:
        file (String): The file path from current directory
        df (pandas.Dataframe): Pandas dataframe object with len(lines)) rows containing all the information from the input data 
                               and following columns: ['email', 'password','ip','url','phone_number','else','domain']
        dict_key (dict): A dictionary with the key as key and the index in the dataframe as value (generated by get_words_with_label)
        file_name (String): The name of the file
    
    Returns:
        lst (list): List of all emails that were found in the Domainlist

    '''
    emails = df['email'].to_list()
    lst = []
    with open(file) as f:
        lines = f.readlines()
    for line in lines:
        line = line.strip()
        if not line:
            continue
        lst.extend([[email,line,dict_key[email],file_name] for email in emails if line in email])
    new_lst=[[email[0],email[2],email[3]] for email in lst if ((('@'+email[1]) in email[0]) or (('.'+email[1]) in email[0]))]
    lst = [(email[1],email[2])for email in new_lst]
    
    print()
    print('All emails in domain file: ',file_name)
    print()
    print([email[0] for email in new_lst])
    print()
    print('--------------------')
    print()
    return lst

def append_df_to_excel(file_names,df,results_file_xlsx):
    '''
    Append the contents of a dataframe to an excel file

    Args:
        file_names (list): All the file names that are in the Domainlist
        df (pandas.Dataframe): Pandas dataframe object with len(lines)) rows containing all the information from the input data 
                               and following columns: ['email', 'password','ip','url','phone_number','else','domain']
        results_file_xlsx (String): The path (including the name) of the excel file to append the contents of the df to
    
    Returns:
        void

    '''
    xlsx = pd.ExcelFile(results_file_xlsx)
    df_dict={}
    for sheet_name in xlsx.sheet_names:
        df_dict[sheet_name]=pd.read_excel(xlsx,sheet_name,index_col=0)
    with pd.ExcelWriter(results_file_xlsx) as writer:  
        for file in file_names:
            try:
                concat_df = pd.concat([df_dict[file],df[df['domain']==file]])
                concat_df.to_excel(writer,sheet_name=file)
            except:
                pass
        concat_df = pd.concat([df_dict['other'],df[df['domain']=='other']])
        concat_df.to_excel(writer,sheet_name='other')    


def find_email_domains_other(df,dict_key,mult_files,results_file_xlsx,out_format):
    '''
    Find all emails, where the domain is in Domainlist. 
    Write the email addresses to the specific sheet in the results.[xlsx|csv] to which its domain belongs to.
    i.e. info@vgem-betzenstein.bayern.de (and its additional information) should be written to the sheet bayer in the results.[xlsx|csv] file.

    Args:
        df (pandas.Dataframe): Pandas dataframe object with len(lines)) rows containing all the information from the input data 
                               and following columns: ['email', 'password','ip','url','phone_number','else','domain']
        dict_key (dict): A dictionary with the key as key and the index in the dataframe as value (generated by get_words_with_label)
        mult_files (boolean): Signals whether the input was a folder or a single file
        results_file_xlsx (String): The path (including the name) of the excel file to append or write the contents of the df to
        out_format (String): The user-specified output format
    
    Returns:
        void
    '''
    start = time.time()
    print('Start of multiprocessing to find email domains. ')
    #find all text files with domain names
    #file_paths, file_names = get_paths(os.path.abspath(os.getcwd())+'/Domainchecker-master-Domainlisten',True)
    file_paths, file_names = get_paths(os.path.abspath(os.getcwd())+'/'+domains_folder_name,True)
    #classify each email address
    num_workers = mp.cpu_count()
    print()
    print('Number of parallel cores: ',num_workers)
    pool = mp.Pool(num_workers)
    for i in range(len(file_paths)):
        pool.apply_async(check_emails_in_domain_other,args=(file_paths[i],df,dict_key,file_names[i]),callback = log_result)
    pool.close()
    pool.join()
    #bundes_domain_list := dict of all emails that are in the domain list with the value domain name
    bundes_domain_list = [item for sublist in result_list for item in sublist]
    for element in bundes_domain_list:
        df.loc[element[0],'domain'] = element[1]
    #write results to excel file
    if out_format=='.xlsx':
        if ((mult_files==False) or (not os.path.isfile(results_file_xlsx))):
            with pd.ExcelWriter(results_file_xlsx) as writer:  
                for file in file_names:
                    try:
                        df[df['domain']==file].to_excel(writer,sheet_name=file)
                    except:
                        pass
                try:
                    df[df['domain']=='other'].to_excel(writer,sheet_name='other')
                except:
                    pass
        else:
            append_df_to_excel(file_names,df,results_file_xlsx)
    else: #out_format=='.csv'
        if ((mult_files==False) or (not os.path.isfile(results_file_xlsx))):
            df.to_csv('results.csv',header='column_names')
        else:
            df.to_csv('results.csv',mode='a', header=False)
    end = time.time()
    print("The process has finished in ",end-start, "seconds.")
    print('End of multiprocessing to find email domains. ')
    print()
            
##################################################################################
##Two functions that handle input from txt files as lines##
def get_words_without_label(lines,key):
    '''
    Find the key in each line of the file. If a key occurs multiple times then only the last occurence is taken into account.
    Does not label the other information given in each data point, but puts each word into a list of all words in the line.

    Args:
        lines (list): The list of Strings from the txt file, each line is a String
        key (String): The key given by the user (standard:email) to sort by, i.e. most important information

    Returns:
        dict_key (dict): A dictionary with the key as key and the whole data point as a list (i.e. [email,password,...]) as value

    '''
    dict_key = {}
    index=0
    for line in lines:
        lst = re.split(';|,|\n|:| |\t',line)
        words = list(filter(None,[word.strip() for word in lst]))
        email_exists = False
        for i in range(len(words)):
            word=words[i]
            if is_something(dict_regex[key],word):
                email_exists=True
                if i!=0:
                    words[0],words[i] = words[i], words[0]
                dict_key[word]=words
                continue
            if censor_password==True:
                if is_something(dict_regex['password'],word):
                    words[i] = word[:3]+'****'
        if ((email_exists==False) and (index==0)):
            input_var=input("No email was found in the first line if you want to continue with email as key enter Y otherwise enter n: ")
            if input_var=='Y':
                continue
            input_var = input("Choose a different key from: [password, ip, url, phone_number, else] and input the chosen word in the same spelling here: ")
            print ("you entered " + input_var)
            get_words_without_label(lines,input_var)
        #Note those without a key (email address) as in the other lines won't be considered
        index+=1  
    return dict_key

def label(df,index,key,dict_key,word,words,i,multiple_occur,keep_index,email_exists,recur):
    '''
    Label the information in each line of the input file.

    Args:
        df (pandas.Dataframe): Pandas dataframe object with len(lines)) rows containing all the information from the input data 
                               and following columns: ['email', 'password','ip','url','phone_number','else','domain']
        index (int): position of the email address in the dataframe
        key (String): The key given by the user (standard:email) to sort by, i.e. most important information
        dict_key (dict): A dictionary with the key as key and the whole data point as a list (i.e. [email,password,...]) as value
        word (String): One information that is being labeled, this could be an email address, password etc.
        words (String): All other words (infos) that were given in the same line in the input file
        i (int): word position in words
        multiple_occur (boolean): True if an email is already in the dataframe, else False
        keep_index (int): row position in the dataframe, from where all rows below are still empty
        email_exists (boolean): True if email exists in the line, else False
        recur (int): an integer to check if an infinite recursion loop has been started

    Returns:
        multiple_occur (boolean): True if an email is already in the dataframe, else False
        keep_index (int): row position in the dataframe, from where all rows below are still empty
        index (int): position of the email address in the dataframe
        email_exists (boolean): True if email exists in the line, else False

    '''

    if recur>=2:
        print('Label: ',index,key,words,word)
        if df.loc[index,'password']=='':
            df.loc[index,'password'] = word
        else:
            df.loc[index,'password'] = df.loc[index,'password']+', '+word
        print(df.loc[index])
        return multiple_occur,keep_index,index,email_exists
    if (is_something(dict_regex[key],word) and recur<2 and email_exists==False):
        if word in dict_key.keys():
            email_exists=True
            df.loc[index] = ['','','','','','','other']
            multiple_occur=True
            keep_index=index
            index=dict_key[word]
            for w in words[:i]:
                label(df,index,key,dict_key,w,words,i,multiple_occur,keep_index,email_exists,recur+1)
        else:
            email_exists=True
            dict_key[word]=index
            df.loc[index,key] = word 
    elif is_something(dict_regex['ip'],word):
        if df.loc[index,'ip']=='':
            df.loc[index,'ip'] = word
        else:
            df.loc[index,'ip'] = df.loc[index,'ip']+', '+word

    elif is_something(dict_regex['url'],word):
        if df.loc[index,'url']=='':
            df.loc[index,'url'] = word
        else:
            df.loc[index,'url'] = df.loc[index,'url']+', '+word

    elif is_something(dict_regex['phone_number'],word):
        if df.loc[index,'phone_number']=='':
            df.loc[index,'phone_number'] = word
        else:
            df.loc[index,'phone_number'] = df.loc[index,'url']+', '+word

    elif is_something(dict_regex['password'],word):
        if censor_password==True:
            if df.loc[index,'password']=='':
                df.loc[index,'password'] = word[:3]+'****'
            else:
                df.loc[index,'password'] = (df.loc[index,'password']+', '+word[:3]+'****')
        else:
            if df.loc[index,'password']=='':
                df.loc[index,'password'] = word
            else:
                df.loc[index,'password'] = (df.loc[index,'password']+', '+word)

    else:
        if df.loc[index,'else']=='':
            df.loc[index,'else'] = word
        else:
            df.loc[index,'else'] = (df.loc[index,'url']+', '+word)
    return multiple_occur,keep_index,index,email_exists

def get_words_with_label(lines,key,df):
    '''
    Find the key in each line of the file. If a key occurs multiple times then all information is stored in one row seperated with ', '
    Also labels the other information given in each data point and puts each word into a list of all words in the line.

    Args:
        lines (list): The list of Strings from the txt file, each line is a String
        key (String): The key given by the user (standard:email) to sort by, i.e. most important information
        df (pandas.Dataframe): Pandas dataframe object with len(lines)) rows and following columns: ['email', 'password','ip','url','phone_number','else','domain']

    Returns:
        dict_key (dict): A dictionary with the key as key and the index in the dataframe as value
        df (pandas.Dataframe): The same Pandas dataframe object as in the input, but now the cells are filled with given information in the lines
        
    '''
    dict_key = {}
    index=0
    keep_index=0
    for line in lines:
        lst = re.split(';|,|\n|:| |\t',line)
        words =[word.strip() for word in lst]
        words = list(filter(None,words))
        multiple_occur=False
        email_exists=False
        for i in range(len(words)):
            word=words[i]
            multiple_occur,keep_index,index,email_exists=label(df,index,key,dict_key,word,words,i,multiple_occur,keep_index,email_exists,0)
        if ((email_exists==False) and (index==0)):
            input_var=input("No email was found in the first line if you want to continue with email as key enter Y otherwise enter n: ")
            if input_var=='Y':
                continue
            input_var = input("Choose a different key from: [password, ip, url, phone_number, else] and input the chosen word in the same spelling here: ")
            print ("you entered " + input_var)
            get_words_with_label(lines,input_var,df)
        elif email_exists==False:#Those without a key (email address) as in the other lines won't be considered
            df.loc[index] = ['','','','','','','other']
            continue
        if multiple_occur==False:
            index+=1
        else:
            index=keep_index
    df = df[df[key] != '']
    df.dropna(subset=[key],inplace=True) ###Check if this is needed
    return dict_key,df

######################################################################################
#Functions that handle different input files

def handle_text_file(file,key,out_format,mult_files):
    '''
    Analyse the input txt file and outputs a file in a specified format

    Args:
        file       (String): The file path from current directory
        key        (String): The key given by the user (standard:email) to sort by, i.e. most important information
        out_format (String): The user-specified output format
        mult_files (boolean): Signals whether the input was a folder or a single file
    
    Returns:
        void

    '''
    
    ###LATER CHANGE SO THAT KEY CAN BE SOMETHING ELSE+CREATE SOMETHING FOR LINES THAT DON'T HAVE AN EMAIL ADDRESS, like list
    with open(file,encoding='UTF-8',errors="ignore") as f:
        print("File was opened successfully!")
        lines = f.readlines()
    #Now see what pattern the rows i.e. each line has
    #best case every line is the same as the first line, worst case every line is individually different
    if out_format=='.txt':
        dict_key = get_words_without_label(lines,key)
        if key=='email':
            find_email_domains_txt(dict_key,mult_files)
        elif (mult_files==True and (os.path.isfile('results/other.txt'))):
            infos=list(dict_key.values())
            with open('results/other.txt','a') as f:
                for i in range(len(infos)):
                    f.write(', '.join(list(filter(None,infos[i])))+'\n')
        else:
            infos=list(dict_key.values())
            with open('results/other.txt','w+') as f:
                for i in range(len(infos)):
                    f.write(', '.join(infos[i])+'\n')
    elif out_format=='.xlsx': 
        #Create name of results xlsx file and make sure to delete any file with the same name in the directory
        file_name = file.split('/')[-1].strip('.txt')
        results_file_xlsx = 'result_'+file_name+'.xlsx'
        if os.path.isfile(results_file_xlsx):
            os.remove(results_file_xlsx)
        print(results_file_xlsx)
        df = pd.DataFrame(np.array([['','','','','','','other']]*len(lines)),columns = ['email', 'password','ip','url','phone_number','else','domain'])
        dict_key,df = get_words_with_label(lines,key,df)
        if key=='email':
            find_email_domains_other(df,dict_key,True,results_file_xlsx,out_format)
        elif (mult_files==True and (os.path.isfile(results_file_xlsx))):
            append_df_to_excel(['other'],df,results_file_xlsx)
        else:
            with pd.ExcelWriter(results_file_xlsx) as writer:  
                df.to_excel(writer,sheet_name='other')
    else: #out_format=='csv'
        print()
        df = pd.DataFrame(np.array([['','','','','','','other']]*len(lines)),columns = ['email', 'password','ip','url','phone_number','else','domain'])
        dict_key,df = get_words_with_label(lines,key,df)
        if key=='email':
            find_email_domains_other(df,dict_key,True,'results.csv',out_format)
        if ((mult_files==False) or (not os.path.isfile('results.csv'))):
            df.to_csv('results.csv',header='column_names')
        else:
            df.to_csv('results.csv',mode='a', header=False)

def check_if_email(df):
    '''
    Check if there exists an email address in the dataframe

    Args:
        df (pandas.Dataframe): Pandas dataframe object with len(lines)) rows and following columns: ['email', 'password','ip','url','phone_number','else','domain']
    
    Returns:
        col(String): The name of the column with emails
          or
        None

    '''
    
    for col in df.columns:
        print(col)
        if re.match("[Ee]{1}[-]{0,1}mail",col):
            return col
    for col in df.columns:
        print(col)
        if is_something(dict_regex['email'],col):
            return col
    return None

def handle_csv_file(file,key,out_format,in_format,mult_files):
    '''
    Analyse the input csv/excel file and outputs a file in a specified format

    Args:
        file       (String): The file path from current directory
        key        (String): The key given by the user (standard:email) to sort by, i.e. most important information
        out_format (String): The user-specified output format
        in_format  (String): The input file's file format
        mult_files (boolean): Signals whether the input was a folder or a single file
    
    Returns:
        void

    '''
    
    if in_format=='.csv':
        txt_file = file.strip('.csv')+'.txt'
        try:
            subprocess.check_output('cat '+file+' | tr "," " " > '+txt_file,shell=True)
        except subprocess.CalledProcessError as error:
            error_output("when converting csv to txt", error, 1)
        #Delete first line
        try:
            subprocess.check_output('sed -i "1d" '+txt_file,shell=True)
        except subprocess.CalledProcessError as error:
            error_output("when deleting first line in newly created text file", error, 1)
        handle_text_file(txt_file,key,out_format,mult_files)
    else: #in_format == '.xlsx'
        csv_file = file.strip('.xlsx')+'.csv'
        txt_file = file.strip('.xlsx')+'.txt'
        try:
            #if xlsx2csv is not downloaded, please download this!!
            subprocess.check_output('xlsx2csv '+file+' --all > '+csv_file,shell=True)
        except subprocess.CalledProcessError as error:
            error_output("when converting csv to txt", error, 1)
        try:
            subprocess.check_output('cat '+csv_file+' | tr "," " " > '+txt_file,shell=True)
        except subprocess.CalledProcessError as error:
            error_output("when converting csv to txt", error, 1)
        #Delete first line
        try:
            subprocess.check_output('sed -i "1d" '+txt_file,shell=True)
        except subprocess.CalledProcessError as error:
            error_output("when deleting first line in newly created text file", error, 1)
        
        handle_text_file(txt_file,key,out_format,mult_files)

    return

def handle_folder(folder,key,out_format):
    '''
    Get all files in the folder and handle each separately.

    Args:
        folder     (String): The folder path from current directory
        key        (String): The key given by the user (standard:email) to sort by, i.e. most important information
        out_format (String): The user-specified output format (right now only .txt)
    
    Returns:
        void

    '''

    #find all text files with domain names
    if '/' not in folder:
        file_paths = get_paths(os.path.abspath(os.getcwd())+'/'+folder,False)
    else:
        file_paths = get_paths(folder,False)
    print(file_paths)
    for file in file_paths:
        if '/' not in folder:
            type_of_file(file.split(folder+'/',1)[1],key,out_format,True)
        else:
            type_of_file(file,key,out_format,True)

def split_file(file,ending):
    '''
    Split a large file into a few smaller files, so that there are no memory errors

    Args:
        file    (String): The file path of the input file
        ending  (String): The input file ending
    
    Returns:
        void

    '''

    file_name=file.split('/')[-1].strip(ending)
    print(file_name)
    if not os.path.exists('splitfiles/'):
        os.mkdir('splitfiles/')
    if not os.path.exists('splitfiles/'+file_name):
        os.mkdir('splitfiles/'+file_name)    
    fs = Filesplit()
    #Change split_size if there are memory issues!! 
    num = 50000000
    mb = num//1000000
    print('All input files will be split at ',mb,' megabytes.\n')
    fs.split(file=file, split_size=num, output_dir=os.path.abspath(os.getcwd())+'/splitfiles/'+file_name,newline=True)
    split_files = get_paths(os.path.abspath(os.getcwd())+'/splitfiles/'+file_name,False)
    split_files = [val for val in split_files if not val.endswith("fs_manifest.csv")]
    
    return split_files

def type_of_file(file,key,out_format,mult_files):
    '''
    Analyse the given input data's format

    Args:
        file       (String): The file path from current directory
        key        (String): The key given by the user (standard:email) to sort by, i.e. most important information
        out_format (String): The user-specified output format
        mult_files (boolean): Signals whether the input was a folder or a single file
    
    Returns:
        void

    '''
    print()
    if file.lower().endswith('.txt'):
        print('The input file you want analysed has been recognised as a text format.')
        print('Processing will now continue.\n')
        #Split file so that there is no memory error into chunks of 30 MB#
        split_files = split_file(file,'.txt')
        print('These are the split files that will now be processed separately: ')
        print(split_files)
        print()
        if len(split_files)>1:
            mult_files=True
        for f in split_files: #for every splitted file check domains
            print('Now handling: ',f)
            print()
            handle_text_file(f,key,out_format,mult_files)
        shutil.rmtree('splitfiles/'+file.split('/')[-1].strip('.txt'), ignore_errors=True) #remove all split files after
        return

    elif file.lower().endswith('.csv'):
        print('The input file you want analysed has been recognised as a csv format.')
        print('Processing will now continue.\n')
        #Split file so that there is no memory error into chunks of 30 MB#
        split_files = split_file(file,'.csv')
        print('These are the split files that will now be processed separately: ')
        print(split_files)
        if len(split_files)>1:
            mult_files=True
        for f in split_files: #for every splitted file check domains
            print('Now handling: ',f)
            print()
            handle_csv_file(file,key,out_format,'.csv',mult_files)
        shutil.rmtree('splitfiles/'+file.split('/')[-1].strip('.csv'), ignore_errors=True)
        
    elif file.lower().endswith('.xlsx'):
        print('The input file you want analysed has been recognised as a xlsx format.')
        print('Processing will now continue.\n')
        #Split file so that there is no memory error into chunks of 30 MB#
        split_files = split_file(file,'.xlsx')
        print('These are the split files that will now be processed separately: ')
        print(split_files)
        if len(split_files)>1:
            mult_files=True
        for f in split_files: #for every splitted file check domains
            print('Now handling: ',f)
            print()
            handle_csv_file(file,key,out_format,'.xlsx',mult_files)
        shutil.rmtree('splitfiles/'+file.split('/')[-1].strip('.xlsx'), ignore_errors=True)
    elif os.path.isdir(file):  
        print("The input given is a folder.")  
        handle_folder(file,key,out_format)
    else:
        print("Sorry, the file format is not supported by the script.")
    #later add other cases


def main():
    '''This is the main function, from here the input file will be analysed and sorted and output in the specified format'''
    gc.enable()
    #variables!!
    key='email'
    out_format = '.txt'    
    args_lst = [arg for arg in sys.argv]
    #Assuming the 0th argument is 'test.py' remove that from args_lst
    args_lst.pop(0)
    global domains_folder_name
    domains_folder_name = args_lst[-1]
    if '.' in domains_folder_name:
        print('Make sure that the last argument given is a folder with Domain lists.')
        input_val = input('If you want to proceed enter Y else enter n, then the program will terminate. ')
        if input_val=='Y':
            pass
        else:
            print()
            print('The program has been terminated because the last input was not a Domain list folder.')
            return
    args_lst.pop(-1)
    #if first input is a key, then key=input, else key='email'
    #if first or second input is an outputformat, then outputformat=input, else outputformat='.txt'
    if re.match(r'password|email|ip|url|phone_number|else',args_lst[0]):
        key=args_lst[0]
        args_lst.pop(0)
        if re.match(r'.txt|.csv|.xlsx', args_lst[0]):
            out_format = args_lst[0]
            args_lst.pop(0)
    elif re.match(r'.txt|.csv|.xlsx', args_lst[0]):
        out_format = args_lst[0]
        args_lst.pop(0)
    print()
    print('The following file[s]/folder[s] were given as input: ')
    print(args_lst)
    print()
    print('The following was selected (if nothing was given as the 1st or 2nd argument then the program standard was selected):')
    print('key: ',key)
    print('output format: ',out_format,'\n')
    if os.path.exists('results/'):
        try:
            subprocess.check_output('rm -r '+'results',shell=True)
        except subprocess.CalledProcessError as error:
            error_output("when removing directory 'results'", error, 1)
    if out_format=='.txt':
        file_paths=get_paths(os.path.abspath(os.getcwd())+'/'+domains_folder_name,False)
        create_all_results_folders(file_paths)
    elif out_format=='.csv':
        if os.path.isfile('results.csv'):
            os.remove('results.csv')

    #ask user if the password should be censored
    print()
    input_user = input('Should the password be censored? Enter Y if yes, else enter n: ')
    global censor_password
    if input_user=='Y':
        censor_password = True
    else:
        censor_password = False

    for f in args_lst:
        #Check what type of file and if file-type is valid i.e. handled in this program
        type_of_file(f,key,out_format,False)
    
    #The program has almost finished
    #In this part the results file is sorted and only the unique key+password(or other info) are left in the results file
    if out_format=='.txt':
        file_paths=get_paths(os.path.abspath(os.getcwd())+'/results',False)
        for result_file in file_paths:
            temp_file = 'results/temp.txt'
            try:
                subprocess.check_output('sort -u '+result_file+' > '+temp_file,shell=True)

            except subprocess.CalledProcessError as error:
                error_output("when selecting unique emails", error, 1)
            try:
                subprocess.check_output('cp '+temp_file+' '+result_file,shell=True)

            except subprocess.CalledProcessError as error:
                error_output("when selecting unique emails", error, 1)
    try:
        subprocess.check_output('rm '+'results/temp.txt',shell=True)

    except subprocess.CalledProcessError as error:
        error_output("when removing directory 'splitfiles'", error, 1)

    try:
        subprocess.check_output('rm -r '+'splitfiles',shell=True)

    except subprocess.CalledProcessError as error:
        error_output("when removing directory 'splitfiles'", error, 1)

if __name__ == "__main__":
    start = time.time()
    main()
    end = time.time()
    diff = end-start
    hrs = diff//3600
    diff-=(hrs*3600)
    mins = diff//60
    diff-=(mins*60)
    sec = int(diff)
    print("The process has finished in ",hrs," hours ",mins," minutes ", sec,"seconds.")








