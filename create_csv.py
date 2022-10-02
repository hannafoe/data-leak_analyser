
import pandas as pd
import numpy as np
import subprocess

def main():
    #df = pd.DataFrame(np.array([['kar.lei@freenet.de','Lusdek'],['fischerog@web.de','kalk2020'],['ruediger_hoffmann@yahoo.de','Isswsdis'],['erika_mesquita_bichsel@freenet.de','eM272719']]),columns = ['email', 'password'])
    #df.to_csv('example.csv',index=False)

    file = 'beispiel_leak2.txt'
    csv_file = file.strip('.txt')+'.csv'
    try:
        subprocess.check_output('cat '+file+' | tr -s ":" "," > '+csv_file,shell=True)
    except subprocess.CalledProcessError as error:
        print('error')
if __name__ == "__main__":
    main()

