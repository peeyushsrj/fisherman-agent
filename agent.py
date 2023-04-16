#!/usr/bin/python3
import sys
import os
from function_list import *
import function_list
import argparse
import inspect
import json
import csv
import re

csv_file = "inputs.csv"
# Function to calculate Levenshtein distance score
def list_functions():
    members = inspect.getmembers(function_list)
    functions = [m[0] for m in members if inspect.isfunction(m[1])]
    return functions

def update_csv(local_file, remote_url, id_field):
    try:
        # Read the contents of the local file into a dictionary
        local_data = {}
        with open(local_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                local_data[row[id_field]] = row

        # Read the contents of the remote file into a dictionary
        remote_data = {}
        response = requests.get(remote_url)
        reader = csv.DictReader(response.text.splitlines())
        for row in reader:
            remote_data[row[id_field]] = row

        # Update the local data with the remote data
        local_data.update(remote_data)

        # Write the combined data to the local file
        with open(local_file, 'w') as f:
            writer = csv.DictWriter(f, fieldnames=reader.fieldnames)
            writer.writeheader()
            for row in local_data.values():
                writer.writerow(row)
                
        print("Successfully updated local file from remote file.")
    except Exception as e:
        print(f"Error: {e}")

def is_valid_url(url):
    pattern = re.compile(r'^https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+')

    return bool(pattern.match(url))

def call_function(func_name: str, *args) -> any:
    try:
        return globals()[func_name](*args)
    except KeyError:
        print(f"Function '{func_name}' not found.")
        return None

def group_data_by_cmd(data):
    # Group the dictionary items based on the value in the "cmd" field
    grouped_data = {}
    for item in data:
        cmd = item["cmd"]
        if cmd in grouped_data:
            grouped_data[cmd].append(item)
        else:
            grouped_data[cmd] = [item]
    #return list(filter(None, grouped_data.keys()))
    return grouped_data

def check_function_in_data(user_input, data):
    found = False
    for item in data["data"]:
        if item["cmd"] == user_input:
            print("Match found for id:", user_input)
            #print(item)
            found = True
            break
    return found

def get_cmd_data():
    with open(csv_file, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    # Convert each row to a JSON object
    data = [json.loads(json.dumps(row)) for row in rows]

    return data

def post_function_data(idName, functionName, inputs):
    with open(csv_file, 'r') as f:
        reader = csv.reader(f)
        for row in reader:
            if row and row[0] == idName:
                print('Input already exists in file')
                return

    # Open the CSV file in append mode and write the new row
    with open(csv_file, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([idName, functionName, inputs])
    print('Inputs have been saved')


parser = argparse.ArgumentParser(description="Command line argument parser")
parser.add_argument('--auto', action='store_const', const=True, default=False, help='Enable or disable automode')
parser.add_argument('--importdefinition', help='URL of import definition csv', default=None)

args = parser.parse_args()
# flow mode is very lazy, avoiding 

if args.auto:
    auto_mode = True
else:
    auto_mode = False

print("-----")
print("automode", auto_mode)
print("-----")

if not os.path.isfile(csv_file):
    with open(csv_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['id', 'cmd', 'inputs', 'skip'])
    print('Inputs file initiated.')

if args.importdefinition is not None:
    print('Importing definition from:', args.importdefinition)
    if is_valid_url(args.importdefinition):
        update_csv(csv_file, args.importdefinition, 'id')
    else:
        print("Please pass validate csv url ")
        sys.exit()

print("Avaliable function list - \n")
for func_item in list_functions():
    print(func_item)

try:
    user_input= input("Enter a function call: ")
except KeyboardInterrupt as e:
    # Cache the exception
    print("Exited Manually!")
    sys.exit()

print("Function entered:", user_input)

if not auto_mode:
    try:
        user_choice = input("Is this correct? (y/N): ")
    except KeyboardInterrupt as e:
        print("Exited Manually!")
        sys.exit()
else:
    user_choice = "y"

# Check if the user wants to continue
if user_choice.lower() == "y":
    print("Loading inputs ...")
    data = get_cmd_data()
    grouped_data = group_data_by_cmd(data)

    # print inputs of given functions
    if user_input in grouped_data.keys():
        inp_values = list(set([d["id"] for d in grouped_data[user_input]]))
        for iter, func_item in enumerate(list(filter(None, inp_values))):
            print(func_item)

    print("custom input")

    try:
        # another function input
        user_input2= input("Enter a cmd: ")
    except KeyboardInterrupt as e:
        # Cache the exception
        print("Exited Manually!")
        sys.exit()

    print("CMD entered:", user_input2)
    if not auto_mode:
        try:
            user_choice = input("Is this correct? (y/N): ")
        except KeyboardInterrupt as e:
            print("Exited Manually!")
            sys.exit()
    else:
        user_choice = "y"

    if user_choice.lower() != "y":
        print("Exiting...Re-run again")
        sys.exit()

    if user_input2 == "custom input":
        print("custom input choosed")
        params = inspect.signature(globals()[user_input]).parameters
        print(params)
        args = []
        for param in params:
            while True:
                arg = input(f"Enter value for '{param}': ")
                if params[param].annotation is not inspect.Parameter.empty and not isinstance(arg, params[param].annotation):
                    print(f"Invalid input type. Expected type: {params[param].annotation}")
                else:
                    args.append(arg)
                    break
        result = call_function(user_input, *args)
        if result is not None:
            print("*****************")
            print(f"Result of {user_input}({', '.join(args)}) = {result}")
            
            user_choice = input("Do you want to store this input for future? (y/N): ")
            if user_choice.lower() == "y":
                user_input3= input("What name should we save it as ?: ")
                print("saving it as : ", user_input3)

                post_function_data(user_input3, user_input, args)
    else:
        for item in data:
            if item['id'] == user_input2:
                if item.get("skip"):
                    return_code = os.system(item["skip"])
                    if return_code == 0:
                        print("Condition already sastisfied!")
                        sys.exit()

                args = json.loads(item["inputs"].replace("'", "\""))
                #print(args)
                result = call_function(user_input, *args)
                if result is not None:
                    print("*****************")
                    print(f"Result of {user_input}({', '.join(args)}) = {result}")
else:
    print("Exiting...Re-run again")
    sys.exit()
