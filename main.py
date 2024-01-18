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
from selenium.common import WebDriverException

from db import get_criteria_from_db, add_alert_to_db, alert_exists

load_dotenv()  # Load variables from the .env file

# Selenium settings
options = webdriver.ChromeOptions()
options.add_argument('--headless')
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--no-sandbox")
driver = webdriver.Chrome(options=options)

# Get environment variables
host = os.getenv("HOST")
port = int(os.getenv("PORT"))
sender_email = os.getenv("SENDER_EMAIL")
sender_password = os.getenv("SENDER_PASSWORD")
recipient_email = os.getenv("RECIPIENT_EMAIL")

# Global variables
new_url = ''


def send_email(subject, body):
    # Create a MIMEText object to represent the email body
    message = MIMEMultipart()
    message['From'] = sender_email
    message['To'] = recipient_email
    message['Subject'] = subject
    message.attach(MIMEText(body, 'plain'))

    # Connect to the SMTP server
    with smtplib.SMTP(host, port) as server:
        server.starttls()
        server.login(sender_email, sender_password)

        # Send the email
        server.sendmail(sender_email, recipient_email, message.as_string())
    print('done')


def get_cached_html():
    with open('output.html', 'r', encoding='utf-8') as file:
        html = file.read()
    return html


def get_html(url):
    global new_url
    html = ''
    try:
        driver.get(url)

        # Allow time for JavaScript to execute (adjust sleep time if needed)
        print('Executing javascript...')
        time.sleep(5)

        # Get the HTML content after JavaScript execution
        html = driver.page_source

        # Get the current URL
        new_url = driver.current_url

        # Save HTML content to a file
        with open('output.html', 'w', encoding='utf-8') as file:
            file.write(html)
    except WebDriverException as e:
        print(e)
    finally:
        driver.quit()

    return html


def scrape(html, criteria):
    # Parse the HTML content using BeautifulSoup
    soup = BeautifulSoup(html, 'html.parser')
    timeslots = soup.find_all('a', class_='timeslot')

    subject = ''
    body = ''
    for timeslot in timeslots:
        timeslot_time_str = timeslot.find('div', class_='timeslot-time').get_text()

        # Convert timeslot time string to datetime object
        timeslot_time = datetime.strptime(timeslot_time_str, '%I:%M %p')

        # Check if timeslot time is within the specified range
        if criteria[2] <= timeslot_time <= criteria[3]:
            timeslot_resource = timeslot.find('div', class_='timeslot-resource').get_text()

            # Check if an alert has already been sent for this slot
            date = criteria[1]
            duration = criteria[4]
            if alert_exists(date, timeslot_time, timeslot_resource, duration):
                print('Alert already sent for this slot. Skipping email.')
                continue
            else:
                add_alert_to_db(date, timeslot_time, timeslot_resource, duration)

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


if __name__ == '__main__':
    url = os.getenv("URL")
    criteria = get_criteria_from_db()[0]
    date = criteria[1]
    start_time = criteria[2]
    end_time = criteria[3]
    duration = criteria[4]

    # Update the URL with the criteria
    url += f'&date={date.strftime("%Y-%m-%d")}'
    url += f'&duration={duration}'

    # Print the criteria
    print(f'Date: {date}')
    print(f'Start Time: {start_time.strftime("%I:%M %p")}')
    print(f'End Time: {end_time.strftime("%I:%M %p")}')
    print(f'Duration: {duration}')
    print(f'URL: {url}')
    print('.' * 50)

    app_env = os.getenv("APP_ENV")
    if app_env == 'production':
        html = get_html(url)
    else:
        html = get_cached_html()

    if url == new_url:
        scrape(html, criteria)
    else:
        print('No slots available. The page has been redirected.')
