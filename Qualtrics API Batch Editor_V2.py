import pandas as pd
import requests
import json
from tkinter import filedialog
import tkinter as tk
import time


domain = "iad1"

#Get filepath for datafile
def contained_askopenfilename(**kwargs) -> str:
  root = tk.Tk()
  root.filepath = filedialog.askopenfilename(**kwargs)
  filepath = root.filepath
  root.destroy()
  return filepath

#Saveas filepath
def contianed_asksaveasfilename(**kwargs) -> str:
  root = tk.Tk()
  root.filepath = filedialog.asksaveasfilename(**kwargs)
  filepath = root.filepath
  root.destroy()
  return filepath

#Opens filepath selected by user, opens the csv as a dataframe. If the words "ImportId" 
# are in the 3rd row, it will mark the file as a Qualtrics Export and ask if you want to
#  get rid of these rows
def retrieve_dataframe(filepath:str) -> pd.DataFrame:
    try:
        with open(filepath, 'r', encoding= 'utf-8') as data_file:
            df = pd.read_csv(data_file)
    except UnicodeDecodeError as E:
        with open(filepath, 'r', encoding='utf-8-sig') as data_file:
            df = pd.read_csv(data_file)

    file_check = str(df.iloc[1,0])
    if '{"ImportId"' in file_check:
        user_input = "0"
        while user_input.upper() != "Y" and user_input.upper() != "N":
            user_input = input("""It appears that you have selected a raw data file. Would you like rows 2 and 3 to be ignored?
    Enter Y | N : """).strip()
        if user_input.upper() == "Y":
            df = df.drop([0,1])
    return df

#Takes in a dictionary of the results of the responses from the requests,
#  gives the user options if they want to export the results as a JSON
def output_results(log:dict) -> None:
    try:
        n_successes = len(log["Successes"])
        n_failures = len(log["Failures"])
        write_log = input(f"There were {n_successes} successful requests and {n_failures} failed requests.  Would you like to write these to a JSON file for followup? Y/N: ").upper()
        while write_log.upper() != "Y" and write_log.upper() != "N":
            write_log = input(f"There were {n_successes} successful requests and {n_failures} failed requests.  Would you like to write these to a JSON file for followup? Y/N: ").upper()
    except:
        write_log = input('Would you like to print the error log for your request? Y/N: ')
        while write_log.upper() != "Y" and write_log.upper() != "N":
            write_log = input('Would you like to print an error log of your request? Y/N: ')
    if write_log.upper() == "Y":
        try:
            save_filename = contianed_asksaveasfilename(initialdir="/", title="Save JSON log", defaultextension=".json", filetypes=[("json files","*.json")])
            with open(save_filename, 'w', encoding='utf-8') as save_file:
                json.dump(log, save_file)
        except Exception as E:
            print("Error writing log as JSON. Attempting to write as text file...")
            try:
                with open(save_filename.replace(".json",".txt"), 'w') as save_file:
                    save_file.write(str(log))
            except Exception as E:
                print("Error writing log as text file. Printing log.")
                print(str(log))

#Takes in a dataframe and outputs a list of the Response IDs that are in the selected csv file
def retrieve_response_ids(dataframe:pd.DataFrame) -> list:
    try:
        all_ids = list(dataframe["ResponseId"])
        valid_ids = [id for id in all_ids if 'R_' in id]
        return valid_ids
    except KeyError:
        print("""*******Error: Column 'ResponseId' not found******* 
Please assure the file you selected has a column with this column header. Exiting program.""")
        quit()

#Takes in the dataframe, current response ID, boolean of if all varables should be updated, 
# and list of specified headers if not all_vars. Outputs a dictionary of embedded data for the request
def create_embedded_data(dataframe:pd.DataFrame, all_vars:bool, specified_headers:list):
    response_list = []
    if all_vars:
        headers = list(dataframe)
        for row in dataframe.values:
            data_dict = {}
            data_dict["responseId"] = ''
            data_dict['embeddedData'] = {}
            data_dict['resetRecordedDate'] = False
            for header in headers:
                if header == 'ResponseId':
                    response_id = str(row[headers.index(header)])
                    data_dict['responseId'] = response_id
                    continue
                value = str(row[headers.index(header)])
                if value != 'nan' and value != ' ':
                    try:
                        data_dict['embeddedData'][header] = value
                        # value = float(value)
                        # if int(value) == value:
                        #     data_dict['embeddedData'][header] = int(value)
                        # else:
                        #     data_dict['embeddedData'][header] = value
                    except:
                        data_dict['embeddedData'][header] = value
            response_list.append(data_dict)
    else:
        headers_i = list(dataframe)
        for row in dataframe.values:
            data_dict["responseId"] = ''
            data_dict['embeddedData'] = {}
            for header in specified_headers:
                if header == 'ResponseId':
                    response_id = str(row[headers.index(header)])
                    data_dict['responseId'] = response_id
                    continue
                try:
                    value = str(row[headers_i.index(header)])
                    if value != 'nan':
                        try:
                            value = float(value)
                            if int(value) == value:
                                data_dict['embeddedData'][header] = int(value)
                            else:
                                data_dict['embeddedData'][header] = value
                        except:
                            data_dict['embeddedData'][header] = value
                except KeyError:
                    print(f"""An error has occurred for trying to update the entered variable '{header}'.
    Please check the variable names and try running again.""")
                    quit()
            response_list.append(data_dict)
    return response_list

def batch_edit(domain:str, api_token:str, survey_id:str, dataframe:pd.DataFrame) -> dict:
    user_input = "0"
    while user_input != "1" and user_input != "2":
        user_input = input("""Would you like to update:
    (1) All variables in the csv file
    (2) Only specified variables from csv file
        Enter 1 | 2 : """).strip()
        if user_input == "1":
            all_vars = True
            specified_headers = []
            print("Please note your file should only include variables you intend to edit.")
            print("Attempting to edit pre-existing values with the same value seems to be the source of unintended type conversions in Qualtrics.")
            ex_script = input("Press 'Enter' to continue, or 'Q' to exit script.")
            if ex_script.upper() == "Q":
                quit()
            print()
        else:
            all_vars = False
            user_input2 = input("""Enter the list of variables you wish to edit, seprarated by a comma (e.g. Prog_site, MFLast, PEARID...)
        Enter: """).split(',')
            specified_headers = [x.strip() for x in user_input2]
    
    #Makes request
    headers=list(dataframe)
    url = f"https://{domain}.qualtrics.com/API/v3/surveys/{survey_id}/update-responses"
    headers = {
        "X-API-TOKEN": api_token,
        "Content-Type": "application/json"
    }
    payload = {
        "updates": [],
        "ignoreMissingResponses": False
    }
    embedded_data = create_embedded_data(dataframe, all_vars, specified_headers)
    payload["updates"] = embedded_data
    
    with open('payload.json', 'w') as o:
        json.dump(payload,o)

    try:
        response = requests.request("POST", url, json=payload, headers=headers)

        response_text = json.loads(response.text)
        progress_id = response_text["result"]["progressId"]
        progress_url = f"https://{domain}.qualtrics.com/API/v3/surveys/{survey_id}/update-responses/{progress_id}"

        response_status = 'inProgress'
        error_log = {}
        while(response_status == 'inProgress'):
            progress_response = requests.request("GET", url= progress_url, headers=headers)
            status_text = json.loads(progress_response.text)
            progress_id = status_text["result"]['progressId']
            response_status = status_text["result"]["status"]
            n_errors = status_text['result']['errorCount']
            error_list = list(status_text['result']['errors'])
            n_warnings = status_text['result']['warningCount']
            warning_list = list(status_text['result']['warnings'])
            error_log = {'error count': n_errors, 'errors': error_list, 'warning count': n_warnings, 'warnings': warning_list}
            print(f"Batch Edit Progress: {response_status}         ", end='\r')
            time.sleep(2)
    
        if response_status == 'complete':
            print(f'*** SUCCESS: You have successfully updated {len(embedded_data)} responses ***')
        elif response_status == 'queued':
            print(f'*** QUEUED: Your request has been queued. Your progressId is: {progress_id} ***')
        elif response_status == 'failed':
            print(f'*** FAILED: Your response failed with {n_errors} error. Responses have not been updated. ***')
    except Exception:
        print('Error occured making request. Exiting script.')
        quit()
    return error_log

def create_embedded_data_manual(response_id:str) -> dict:
    print(f"Editting variables for response with ResponseId: {response_id}")
    data = {}
    user_input = input("""Enter the list of variables you wish to edit, seprarated by a comma (e.g. Prog_site, MFLast, PEARID...)
        Enter: """).split(',')
    variables = [x.strip() for x in user_input]
    for v in variables:
        value = input(f"Please enter the desired value for the variable {v}: ")
        var_type = input("""Is this a: (1) string | (2) int | (3) float | (4) boolean
        Enter: """).strip()
        if var_type == "1":
            value = str(value)
        elif var_type == "2":
            value = int(value)
        elif var_type == "3":
            value = float(value)
        elif var_type == "4":
            value = bool(value)
        data[v] = value
    return data

def manual_edit(domain:str, api_token:str, survey_id:str, resp_ids:list):
    successes_and_failures = {"Successes": [], "Failures": []}
    for response_id in resp_ids:
        url = f"https://{domain}.qualtrics.com/API/v3/responses/{response_id}"
        headers = {
            "X-API-TOKEN": api_token,
            "Content-Type": "application/json"
        }
        embedded_data = create_embedded_data_manual(response_id)
        data = {
        "surveyId": survey_id, 
        "resetRecordedDate": False,
        "embeddedData": embedded_data
        }
        try:
            response = requests.put(url=url, headers=headers, json=data)
            if response.status_code == 200:
                successes_and_failures["Successes"].append({f"{response_id}":response.json()})
            else:
                successes_and_failures["Failures"].append({f"{response_id}":response.json()})
        except Exception as E:
            successes_and_failures["Failures"].append({f"{response_id}": str(E)})
    return successes_and_failures

def console_app():
    data_filepath = contained_askopenfilename(initialdir="/", title="Select CSV Data File", filetypes=[("csv files","*.csv")])

    api_token = input("Please enter your Qualtrics API Token: ").strip()
    survey_id = input("Please enter the Survey ID you want to make edits to (e.g. SV_2bGzOsMJpF5lVVs): ").strip()

    df = retrieve_dataframe(data_filepath)
    response_id_list = retrieve_response_ids(df)

    user_response = input("""Which kind of edit would you like to make:
    (1) Batch Edit: Assign reponses from columns in csv file
    (2) Manual Edit: Assign each response unique value
        Enter 1 | 2 : """).strip()
    if user_response == "1":
        log = batch_edit(domain, api_token, survey_id, df)
    elif user_response == "2":
        log = manual_edit(domain, api_token, survey_id, response_id_list)
    else:
        print("Invalid reponse. Exiting without making edits.")
        quit()

    output_results(log)


console_app()