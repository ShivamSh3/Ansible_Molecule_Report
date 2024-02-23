#!/usr/bin/python
import re
import os
import json
from flask import Flask, render_template, jsonify

directory = "/root/log/"
pattern = re.compile(r"PLAY RECAP.*\n(.*)", re.MULTILINE)
app = Flask(__name__, template_folder='templates')
result = {}

def get_all_log_files(directory):
    return [os.path.join(root, file) for root, dirs, files in os.walk(directory) for file in files]

def check_playbook_failures(data, pattern):
    playbook_recap_match = pattern.findall(data)
    if playbook_recap_match:
        for match in playbook_recap_match:
            failed_match = re.search(r"failed=(\d+)", match)
            if failed_match and int(failed_match.group(1)) >= 1:
                return "FAIL"
    return "PASS"

def simplify_output(file_path):
    log_file_name = file_path.split('/')[-1]
    log_file_name_split = log_file_name.split('-')
    role_name, scenario_name = log_file_name_split[0], log_file_name_split[1]
    if 'TC-' in log_file_name:
        code = log_file_name_split[2]
        scenario_name += code
    scenario_name = scenario_name.replace('.log', '')
    return role_name, scenario_name

@app.route('/')
def index():
    global result
    return render_template('index.html', result=result)

if __name__ == '__main__':
    pass_result = 0
    fail_result = 0
    passed_role = set()
    failed_role = set()
    partial_role = set()
    file_list = get_all_log_files(directory)
    print('Total scenario: ', len(file_list))
    for file_path in file_list:
        with open(file_path, "r") as f:
            content = f.read()
            report = check_playbook_failures(content, pattern)
            role_name, scenario_name = simplify_output(file_path)
            result.setdefault(role_name, {})[scenario_name] = report
            if report == 'PASS':
                pass_result += 1
            else:
                fail_result += 1

    print(json.dumps(result, indent=4))
    print('Pass: ', pass_result)
    print('Fail: ', fail_result)
    print('Pass Percentage: ', round(pass_result / (pass_result + fail_result) * 100, 2),'%')

    app.run(port=5000)
