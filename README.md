# Skripte zur Analyse von Data-Leaks

## Dokumentation
Die Skripte untersuchen die Input-Datei nach einer Email Addresse. Wenn es eine gibt dann wird das Programm suchen ob die Email Adresse in der Domain-Liste vorhanden ist, welche im gleichen Ordner wie das Skript liegt. Anschließend, wird das Programm im gewünschten output Format das Ergebnis der Analyse liefern. 

Das Projekt umfasst das folgende Skript, welches zur Bearbeitung von veröffentlichten Datendumps genutzt werden soll:
- domain_check.py
- domain_check_grep_version.py

<br>Das Skript *domain_check.py* durchsucht den Datenleak nach den Domains in dem Ordner Domainlisten (bitte kreeieren Sie so einen Ordner mit möglichen Subordnern und Textdateien, die in jeder Zeile eine neue Domain aufführen) und sortiert Email-Adressen in Text-Dateien nach Domainlisten. Diese Version ist dann schnell, wenn mindestens so viele Domainlisten untersucht werden wie verfügbare Cores im Computer, da multiprocessing benutzt wird. Das Skript *domain_check_grep.py* ist eine Version, die die Bash-Funktion grep benutzt und damit den Prozess beschleunigt.

### Domainchecker (domain_check.py)
Das Skript benötigt nur die Top-Level-Domains der jeweiligen Mailanbieter und sucht automatisch auch nach Sub-domain Einträgen in der input Datei.
Die Listprüfung geht von keinem bestimmten Datensatzstil aus. Die Wörter in einer Zeile werden von einander getrennt und die E-mail Adresse wird immer an die erste Position sortiert.

Im Falle der Auswahl .txt als Outputformat, wird es für jede Domäne eine Textdatei geben und die Textdateien sind in Ordnern so angeordnet, dass die Ordnerhierarchie der Domainliste widerspiegelt ist. Falls es eine Email Adresse mehrmals gibt, wird nur das letzte Ereignis gespeichert. Falls keine E-mail Adresse vorhanden ist, trennt das Programm alle Wörter voneinander (reinigt die Input-Datei) und sortiert sie in die Datei results/other.txt.

Im Falle der Auswahl .xlsx als Outputformat, wird es nur eine Excel Datei geben. Die Daten sind sortiert in die jeweiligen Domainlisten durch verschiedene Sheets in der Excel Datei. Bei der Excel-Datei werden die Datenpunkte gelabelt als password, email, ip, url, phone_number oder else. Falls es eine Email Adresse mehrmals gibt, werden die unterschiedlichen Passwörter zum Beispiel mit einem Komma getrennt in die gleiche Zelle gespeichert. Hinweis: Meherere Excel Dateien werden hergestellt bei großen Dateien.

Im Falle der Auswahl .csv als Outputformat, wird es eine CSV Datei geben mit Labels. Eines der Labels ist die Domain zu der die Email Adresse gehört. 

Empfohlen ist die Outputdatei als Textdatei zu erhalten, da dies eine viel schnellere Laufzeit hat, da alle Wörter außer der Email-Addresse nicht gelabelt werden. Das Programm nutzt multiprocessing indem mehrere Domainlisten gleichzeitig mit den Email-Adressen aus der Input-Datei gegengeprüft werden. Wenn der Computer also 8 freie CPU-Kerne hat und 8 Domainlisten zum gegenprüfen benutzt werden sollen, werden diese parallel geprüft. Die Laufzeit ist deshalb nicht optimal wenn immer nur eine Domainliste als Input gegeben wird. Außerdem ist die Laufzeit stark abhängig von den verfügbaren CPU-Kernen.


#### Anwendung
<br><br>
>**Hinweis**
><br>
>Das Skript verwendet Python v3!
><br>
>Die folgenden Pakete sollten vor das Skript benutzt wird installiert werden:
>```bash
>pip install pandas
>pip install numpy
>pip install filesplit
>pip install tqdm
>easy_install xlsx2csv (nur notwending wenn Eingabe Datei eine CSV Datei ist.)
>```

```bash
python domain_check.py [email|ip|url|...] [.txt|.xlsx|.csv] email_leak1[.txt|.csv|.xlsx] email_leak2[.txt|.csv|.xlsx] Domainlisten
python domain_check.py [email|ip|url|...] [.txt|.xlsx|.csv] email_leak_folder Domainlisten

Beispiel:
python domain_check.py beispiel_file.txt meine_domainlisten
python domain_check_grep_version.py .xlsx beispiel_folder meine_domainlisten
python domain_check_grep_version.py .csv USB/media/beispiel_file.txt meine_domainlisten
```

```bash
usage: domain_check.py [<gewünschter key>] [<output Dateiformat>] <input Dateien> <Ordner von Domainlisten>

positional arguments:
  <input Dateien>     Alle Dateien, die analysiert werden sollen entweder mit Endung .txt, .csv oder .xlsx, oder Ordner mit diesen Dateien.
  <Ordner von Domainlisten> Ein Ordner mit allen Domainlisten, dieser soll im gleichen Ordner wie das Skript sein.

optional arguments:
  <gewünschter key>   Der gewünschte Key ist standardmäßig die Email Addresse. Falls aber keine Email Adressen vorhanden sind, soll ein anderer Key ausgewählt werden, 
                      wonach die Datei verarbeitet werden soll. Die zulässigen keys sind: password, email, ip, url, phone_number, else.
  <output Dateiformat> Das Outputformat der sortierten Email Addressen. Hier ist [.txt|.csv|.xlsx] zulässig. Hinweis: .txt ist die schnellste Version.
```




