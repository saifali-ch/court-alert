#! /usr/bin/env python3

import os
import smtplib
import time
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from bs4 import BeautifulSoup
from dotenv import load_dotenv
from selenium import webdriver

from db import get_criteria, add_alert, alert_exists

load_dotenv()  # Load variables from the .env file

# Selenium settings
options = webdriver.ChromeOptions()
options.add_argument('--headless')
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--no-sandbox")
driver = webdriver.Chrome(options=options)

# Get environment variables
__DEV__ = os.getenv("APP_ENV") == 'local'
host = os.getenv("HOST")
port = int(os.getenv("PORT"))
sender_email = os.getenv("SENDER_EMAIL")
sender_password = os.getenv("SENDER_PASSWORD")
recipient_email = os.getenv("RECIPIENT_EMAIL")


def send_email(subject, body):
    # Create a MIMEText object to represent the email body
    message = MIMEMultipart()
    message['From'] = sender_email
    message['To'] = recipient_email
    message['Subject'] = subject
    message.attach(MIMEText(body, 'plain'))

    if __DEV__:  # Use MailHog for local environment
        with smtplib.SMTP('localhost', 1025) as server:
            server.sendmail(sender_email, recipient_email, message.as_string())
    else:
        with smtplib.SMTP(host, port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, recipient_email, message.as_string())


def get_filename_from_url(url):
    filename = url.replace('https://', '').replace('http://', '').replace('/', '_').replace(':', '_') + '.html'
    return filename


def get_cached_html(url):
    global new_url
    new_url = url

    filename = get_filename_from_url(url)
    file_path = os.path.join('cache', filename)
    with open(file_path, 'r', encoding='utf-8') as file:
        html = file.read()
    return html


def get_html(url):
    global new_url
    driver.get(url)

    # Allow time for JavaScript to execute (adjust sleep time if needed)
    print('Executing javascript...')
    time.sleep(7)
    html = driver.page_source
    new_url = driver.current_url

    if not os.path.exists('cache'):
        os.makedirs('cache')

    filename = get_filename_from_url(url)
    file_path = os.path.join('cache', filename)
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(html)

    return html


def scrape(html, criteria):
    # Parse the HTML content using BeautifulSoup
    soup = BeautifulSoup(html, 'html.parser')
    timeslots = soup.find_all('a', class_='timeslot')

    if not timeslots:
        print('No timeslots detected.')
        return

    subject = ''
    body = ''
    for timeslot in timeslots:
        timeslot_time_str = timeslot.find('div', class_='timeslot-time').get_text()

        # Convert timeslot time string to datetime object
        timeslot_time = datetime.strptime(timeslot_time_str, '%I:%M %p')

        # Check if timeslot time is within the specified range for the current criteria
        if criteria[2] <= timeslot_time <= criteria[3]:
            timeslot_resource = timeslot.find('div', class_='timeslot-resource').get_text()

            # Check if an alert has already been sent for this slot and criteria
            if alert_exists(timeslot_time, timeslot_resource, criteria_id=criteria[0]):
                print('Alert already sent for this slot and criteria. Skipping email.')
                continue
            else:
                add_alert(timeslot_time, timeslot_resource, criteria_id=criteria[0])

            # Update the email subject
            date_str = criteria[1].strftime('%m/%d')
            time_str = timeslot_time.strftime('%I:%M %p')
            subject = f"Available Time: {date_str} at {time_str}"

            # Update the email body to add a line for each slot
            body += f"{timeslot_resource} is available on {date_str} at {timeslot_time.strftime('%I:%M %p')}\n"

    body += '\n' + url
    if subject and body:
        print(subject)
        print(body)
        send_email(subject, body)


# Global variables
new_url = ''
base_url = os.getenv("URL")

if __name__ == '__main__':
    app_env = os.getenv("APP_ENV")

    criteria_list = get_criteria(active=True)

    for criteria in criteria_list:
        url = f"{base_url}&date={criteria[1].strftime('%Y-%m-%d')}&duration={criteria[4]}"

        # Print the criteria for the current entry
        print(f'URL: {url}')
        print(f'Start Time: {criteria[2].strftime("%I:%M %p")}')
        print(f'End Time: {criteria[3].strftime("%I:%M %p")}')

        if __DEV__:
            html = get_cached_html(url)
        else:
            try:
                html = get_html(url)
            except Exception as e:
                print(e)
                continue

        if url == new_url:
            scrape(html, criteria)
        else:
            print('No slots available. The page has been redirected.')
        print('.' * 100)
    driver.quit()
    print('Processing complete.')
