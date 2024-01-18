## Qualtrics-Data-Editor

This script uses the Qualtrics API to batch edits embedded data variables in a Qualtrics survey database. The project takes in a csv file that contains a list of all of the responses that you want to edit, as well as all the data that you want to change. It then converts the data uploaded into an API payload and sends the request to Qualtrics. You must have a Qualtrics developer API key to run. The script will alert you if any of the requests fail and will output errors as needed. 
