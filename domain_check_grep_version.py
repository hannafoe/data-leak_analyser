#! python3.8.8

# install:
#! pip install filesplit

# coding=utf-8
import gc
import multiprocessing as mp
import os
import re
import sys
import time
import shutil
import subprocess

from fsplit.filesplit import Filesplit




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
      

def create_result_txtfile(domain):
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
        with open('results/'+domain,'w+') as f:
            f.write('')
    else:
        with open('results/'+domain+'.txt','w+') as f:
            f.write('')

def create_all_results_txtfiles(file_paths):
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
        create_result_txtfile(file_name)
    create_result_txtfile('other')
    create_result_txtfile('all_bund')

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


def check_emails_in_domain_txt(file,input_file):
    '''
    Check for each email if its domain is in this file, only used for when the output file should be a txt file.
    If an email has a domain from Domainlist, this is saved into results/ under the name of the Domainlist from where it is from

    Args:
        file (String): The file path of a Domainfile
        input_file (String): The file path of the input file (or the split input file, which contains the emails)
    
    Returns:
        void

    '''
    with open(file) as f:
        lines = f.readlines()
    lines = [line.strip() for line in lines]
    if '.txt' in file:
        file_name = 'results/'+file.split('/'+domains_folder_name+'/',1)[1]
    else:
        file_name = 'results/'+file.split('/'+domains_folder_name+'/',1)[1]+'.txt'
    print('Currently checking from domainlist : ',file_name[7:])
    for line in lines:
        if line.strip()=='':
            continue
        try:
            #look for each domain in emails
            #print(line)
            line = line.split('.')
            line = '\\.'.join(line)
            line_upper = line.upper()
            subprocess.check_output(
                #"grep -E '\\b[A-Za-z0-9._%+-]+@[A-Za-z0-9._%+-]*[\\.|]'" +line+'\|'+line_upper+ "'\\b' " + input_file + " | sort | uniq >> " + file_name,
                "grep --text -E '\\b@[A-Za-z0-9._%+-]*[\\.|]'" +line+'\|'+line_upper+ "'\\b' " + input_file + " | sort | uniq >> " + file_name,
                shell=True)
            #os.system("grep --text -E " + " '[A-Za-z0-9._%+-]+@[A-Za-z0-9._%+-]*[\\.|]" + line+ "' " + input_file + " > " +file_name + "s.txt")

        except subprocess.CalledProcessError as error:
            error_output("beim Pruefen der Top-Level-Domains", error, 1)

    print()
    print('All emails in domain file: ',file_name[7:])
    print()
    with open(file_name) as f:
        ls=f.readlines()
    print(ls)
    print()
    print('--------------------')
    print()

    return 


def find_email_domains_txt(input_file):
    '''
    Find all emails, where the domain is in Domainlist. 
    Write the email addresses to the specific txt file to which its domain belongs to in the results folder.
    i.e. info@vgem-betzenstein.bayern.de (and its additional information) should be written to bayern.txt in the subfolder Bundeslaender in the folder results.

    Args:
        input_file (String): The file path of the input file (or the split input file, which contains the emails)

    Returns:
        void

    '''

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
    print('Start of searching email domains. ')

    for i in range(len(file_paths)):
        check_emails_in_domain_txt(file_paths[i],input_file)
    
    end = time.time()
    diff = end-start
    hrs = diff//60//60
    diff-=hrs*60*60
    mins = diff//60
    diff-=mins*60
    sec = int(diff)
    print("The process has finished in ",hrs," hours ",mins," minutes ", sec,"seconds.")
    print('End of searching email domains. ')
    return



def clean_file(input_file):
    '''
    Clean the input file, such that a space always splits the words.

    Args:
        input_file (String): The file path of the input file (or the split input file, which contains the emails)

    Returns:
        void

    '''
    print()
    print('Cleaning file.')
    print()
    try:
        subprocess.run(['sed','-E','-i','s/,|:|\\n|;| |TAB/ /g',input_file])
    except:
        print('Error in changing file')
    
    return
    



######################################################################################
#Functions that handle different input files

def handle_text_file(file,key,out_format):
    '''
    Analyse the input txt file and outputs a file in a specified format

    Args:
        file       (String): The file path from current directory
        key        (String): The key given by the user (standard:email) to sort by, i.e. most important information
        out_format (String): The user-specified output format (right now only .txt)
    
    Returns:
        void

    '''
    
    with open(file,encoding='UTF-8',errors="ignore") as f:
        print("File was opened successfully!")
        lines = f.readlines()##Read in parts for bigger files??
    #Now see what pattern the rows i.e. each line has
    #best case every line is the same as the first line, worst case every line is individually different
    clean_file(file)
    if out_format=='.txt':
        if key=='email':
            find_email_domains_txt(file)
            file_paths = get_paths(os.path.abspath(os.getcwd())+'/'+domains_folder_name,False)
            
            #Change permission settings
            try:
                subprocess.check_output('chmod +x results/all_bund.txt',shell=True)
            except subprocess.CalledProcessError as error:
                error_output("when changing results/all_bund.txt file permission settings",error,1)
            for i in range(len(file_paths)):
                if file_paths[i].endswith('.txt'):
                    result_file = 'results/'+file_paths[i].split('/'+domains_folder_name+'/',1)[1]
                else:
                    result_file = 'results/'+file_paths[i].split('/'+domains_folder_name+'/',1)[1]+'.txt'
                #Change permission settings
                try:
                    subprocess.check_output('chmod +x '+result_file,shell=True)
                except subprocess.CalledProcessError as error:
                    error_output("when changing file permission settings of a file in results folder",error,1)
                #Append the content of each domain file to all_bund file
                try:
                    subprocess.check_output('cat '+result_file+' >> results/all_bund.txt',shell=True)
                except subprocess.CalledProcessError as error:
                    error_output("when emails whose domains are in the Domainlist were appended to all_bund file",error,1)

            #save emails that are not in a Domainlist into the results/other.txt file
            #grep -Fvxf <lines-to-remove> <all-lines>
            try:
                subprocess.check_output('grep -Fxvf '+'results/all_bund.txt'+' '+file+' >> results/other.txt',shell=True)
            except subprocess.CalledProcessError as error:
                error_output("when emails whose domains are in the Domainlist were deleted from the input file",error,1)
        else:#Case when email is not the key
            print('The key is not the email address, hence the file will not be domain checked.')
            print('The sorted and cleaned version of the input file will be saved into results/other.txt')
            print()
            file_name=file.split('/')[-1].strip('.txt')
            split_files = get_paths(os.path.abspath(os.getcwd())+'/splitfiles/'+file_name,False)
            split_files = [val for val in split_files if not val.endswith("fs_manifest.csv")]
            try:
                subprocess.check_output('chmod +x results/other.txt',shell=True)
            except subprocess.CalledProcessError as error:
                error_output("when changing results/other.txt file permission settings",error,1)
            for split_file in split_files:
                try:
                    subprocess.check_output('chmod +x '+split_file,shell=True)
                except subprocess.CalledProcessError as error:
                    error_output("when changing file permission settings of a file in split_files",error,1)
                try:
                    subprocess.check_output('cat '+split_file+' >> results/other.txt',shell=True)
                except subprocess.CalledProcessError as error:
                    error_output("when emails whose domains are in the Domainlist were appended to all_bund file",error,1)



def handle_csv_file(file,key,out_format,in_format):
    '''
    Analyse the input csv/excel file and outputs a file in a specified format

    Args:
        file       (String): The file path from current directory
        key        (String): The key given by the user (standard:email) to sort by, i.e. most important information
        out_format (String): The user-specified output format (right now only .txt)
        in_format  (String): The input file's file format
    
    Returns:
        void

    '''

    if in_format=='.csv':
        txt_file = file.strip('.csv')+'.txt'
        try:
            subprocess.check_output('cat '+file+' | tr "," " " > '+txt_file,shell=True)
        except subprocess.CalledProcessError as error:
            error_output("when converting csv to txt", error, 1)
        if out_format=='.txt':
            handle_text_file(txt_file,key,out_format)
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
        if out_format=='.txt':
            handle_text_file(txt_file,key,out_format)

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

    if '/' not in folder:
        file_paths = get_paths(os.path.abspath(os.getcwd())+'/'+folder)
    else:
        file_paths = get_paths(folder,False)
    print(file_paths)
    for file in file_paths:
        if '/' not in folder:
            type_of_file(file.split(folder+'/',1)[1],key,out_format)
        else:
            type_of_file(file,key,out_format,True)
        gc.collect()

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
    if not os.path.exists('splitfiles/'):
        os.mkdir('splitfiles/')
    if not os.path.exists('splitfiles/'+file_name):
        os.mkdir('splitfiles/'+file_name)    
    fs = Filesplit()
    #Change split_size if there are memory issues!! 
    num = 200000000
    mb = num//1000000
    print('All input files will be split at ',mb,'megabytes.\n')
    fs.split(file=file, split_size=num, output_dir=os.path.abspath(os.getcwd())+'/splitfiles/'+file_name,newline=True)
    split_files = get_paths(os.path.abspath(os.getcwd())+'/splitfiles/'+file_name,False)
    split_files = [val for val in split_files if not val.endswith("fs_manifest.csv")]
    
    return split_files


def type_of_file(file,key,out_format):
    '''
    Analyse the given input data's format

    Args:
        file       (String): The file path of the input file
        key        (String): The key given by the user (standard:email) to sort by, i.e. most important information
        out_format (String): The user-specified output format
    
    Returns:
        void

    '''
    if file.lower().endswith('.txt'):
        print()
        print('The input file you want analysed has been recognised as a text format.')
        print('Processing will now continue.\n')
        print()
        #Split file so that there is no memory error
        split_files = split_file(file,'.txt')
        print('These are the split files that will now be processed separately: ')
        print(split_files)
        print()
        for f in split_files: #for every splitted file check domains
            print('Now handling: ',f)
            print()
            handle_text_file(f,key,out_format)
        shutil.rmtree('splitfiles/'+file.split('/')[-1].strip('.txt'), ignore_errors=True) #remove all split files after
        return

    elif file.lower().endswith('.csv'):
        print()
        print('The input file you want analysed has been recognised as a csv format.')
        print('Processing will now continue.\n')
        #Split file so that there is no memory error
        split_files = split_file(file,'.csv')
        print('These are the split files that will now be processed separately: ')
        print(split_files)
        print()
        for f in split_files: #for every splitted file check domains
            print('Now handling: ',f)
            print()
            handle_csv_file(f,key,out_format,'.csv')
        shutil.rmtree('splitfiles/'+file.split('/')[-1].strip('.csv'), ignore_errors=True)
        
    elif file.lower().endswith('.xlsx'):
        print()
        print('The input file you want analysed has been recognised as a xlsx format.')
        print('Processing will now continue.\n')
        print()
        #Split file so that there is no memory error
        split_files = split_file(file,'.xlsx')
        print('These are the split files that will now be processed separately: ')
        print(split_files)
        print()
        for f in split_files: #for every splitted file check domains
            print('Now handling: ',f)
            handle_csv_file(f,key,out_format,'.xlsx')
        shutil.rmtree('splitfiles/'+file.split('/')[-1].strip('.xlsx'), ignore_errors=True)
    elif os.path.isdir(file):  
        print("The input given is a folder.")  
        handle_folder(file,key,out_format)
        print()
    else:
        print("Sorry, the file format is not supported by the script.")



def main():
    '''
    This is the main function, from here the input file will be analysed and sorted and output in the specified format
    The current version only outputs in txt format.
    '''
    gc.enable()

    #variables
    key='email'
    out_format = '.txt'    
    args_lst = [arg for arg in sys.argv]
    #Assuming the 0th argument is the python file remove that from args_lst
    args_lst.pop(0)
    global domains_folder_name
    domains_folder_name = args_lst[-1]
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

    print('The following file[s]/folder[s] were given as input: ')
    print(args_lst)
    print()
    print('The following was selected (if nothing was given as the 1st or 2nd argument then the program standard was selected):')
    print('key: ',key)
    print('output format: ',out_format,'\n')

    if out_format=='.txt':
        file_paths=get_paths(os.path.abspath(os.getcwd())+'/'+domains_folder_name,False)
        create_all_results_txtfiles(file_paths)
    elif out_format=='.csv':
        if os.path.isfile('results.csv'):
            os.remove('results.csv')
    for f in args_lst:
        #Check what type of file the input file is for each file in args_lst and whether the file-type is valid i.e. handled in this program
        type_of_file(f,key,out_format)

    #The program has almost finished
    #In this part the results file is sorted and only the unique key+password(or other info) are left in the results file
    if out_format=='.txt':
        file_paths.append(os.path.abspath(os.getcwd()+'/'+domains_folder_name+'/all_bund'))
        for domain_file in file_paths:
            if domain_file.endswith('.txt'):
                result_file = 'results/'+domain_file.split('/'+domains_folder_name+'/',1)[1]
            else:
                result_file = 'results/'+domain_file.split('/'+domains_folder_name+'/',1)[1]+'.txt'
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
            subprocess.check_output('rm '+temp_file,shell=True)

        except subprocess.CalledProcessError as error:
            error_output("when selecting unique emails", error, 1)

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








