#!/usr/bin/python
import re
import os
import json
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from jinja2 import Environment, FileSystemLoader

# Read values from config file
with open('config.json', 'r') as f:
    config = json.load(f)

directory = os.path.dirname(os.path.abspath(__file__)) + '/log/'
templates_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
pattern = re.compile(r"PLAY RECAP.*\n(.*)", re.MULTILINE)
result = {}
total_test_cases = 0
passed_test_cases = 0
failed_test_cases = 0
pass_percentage = 0

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

def generate_html_output(result, passed_test_cases, failed_test_cases, pass_percentage):
    env = Environment(loader=FileSystemLoader(templates_dir))
    template = env.get_template('index.html')
    total_test_cases = passed_test_cases + failed_test_cases
    output = template.render(result=result, total_test_cases=total_test_cases, passed_test_cases=passed_test_cases, failed_test_cases=failed_test_cases, pass_percentage=pass_percentage)
    return output

def send_email(output_file_path, recipient_email):
    # Read values from config file
    # Set up the SMTP server
    print('Preparing email...')
    smtp_server = config['smtp_server']
    smtp_username = config['smtp_username']
    email_subject = r"%s %s: Molecule Execution Report" % (config["test_suite"], config["version"])

    # Create the email message
    msg = MIMEMultipart()
    msg['From'] = smtp_username
    msg['To'] = recipient_email
    msg['Subject'] = email_subject

    # Attach the output file
    with open(output_file_path, 'rb') as file:
        attachment = MIMEBase('application', 'octet-stream')
        attachment.set_payload(file.read())
        encoders.encode_base64(attachment)
        attachment.add_header('Content-Disposition', f'attachment; filename="{os.path.basename(output_file_path)}"')
        msg.attach(attachment)
        print("Attachments added")

    # Send the email
    with smtplib.SMTP(smtp_server) as server:
        server.sendmail(smtp_username, [recipient_email], msg.as_string())
        print("Email sent successfully!")

if __name__ == '__main__':
    passed_role = set()
    failed_role = set()
    partial_role = set()
    file_list = get_all_log_files(directory)
    total_test_cases = len(file_list)
    for file_path in file_list:
        with open(file_path, "r") as f:
            content = f.read()
            report = check_playbook_failures(content, pattern)
            role_name, scenario_name = simplify_output(file_path)
            result.setdefault(role_name, {})[scenario_name] = report
            if report == 'PASS':
                passed_test_cases += 1
            else:
                failed_test_cases += 1

    pass_percentage = round(passed_test_cases / (passed_test_cases + failed_test_cases) * 100, 2)
    html_output = generate_html_output(result, passed_test_cases, failed_test_cases, pass_percentage)
    with open('report.html', 'w') as f:
        print('Generating report...')
        f.write(html_output)
        print('Report generated successfully!')

    print('Summary of test results:')
    print('Total scenario: ', total_test_cases)
    print('Pass: ', passed_test_cases)
    print('Fail: ', failed_test_cases)
    print('Pass Percentage: ', pass_percentage,'%')
    recipient = config['recipient']
    send_email('report.html', recipient)
