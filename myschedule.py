"""
Rishi Kapadia
Schedule Update Notifier
Hackathon 11-9-12 to 11-10-12

Note: Run in Python version 2.7, NOT 3
"""

import mechanize, urllib, urllib2, cookielib, time
from _beautifulsoup import BeautifulSoup
from twilio.rest import TwilioRestClient
from datetime import datetime, timedelta
from email.utils import parsedate


TWILIO_PHONE_NUMBER = "(562) 352 - 0309"
TWILIO_ACCOUNT_SID = 'ACdd9b3407c0ff20c450ebe385bc09c71a'
TWILIO_AUTH_TOKEN = '0a1ffeb8651886b31fe61bcd1ee3d47f'
client = TwilioRestClient(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

FROM_NUMBER = '+15623520309'     # Twilio phone number
TO_NUMBER = '+15622918691'     # Default TO_NUMBER

urls = {'FALL': 'http://schedule.berkeley.edu/srchfall.html', 'SPRING': 'http://schedule.berkeley.edu/srchsprg.html', 'SUMMER': 'http://schedule.berkeley.edu/srchsmr.html'}
errors = ["Sorry, that is not a valid semester entry.", "Sorry, that is not a valid course entry.", "Sorry, that is not a valid section number.", "I'm sorry, you are not authorized to use this service.", "Telebears is down for an unscheduled maintenance."]

schedules = {('spring', 'physics', '7a', '107'): '', ('spring', 'physics', '7a', '108'): '', ('spring', 'math', '1b', '203'): '', ('spring', 'math', '1b', '201 '): '', ('spring', 'math', '1b', '202'): ''}




def find_nr(br, sec_number):
    text = br.response().read()
    num_forms = len([f for f in br.forms()])
    form_to_submit = -1
    if text.count(sec_number) < 1:
        return -1
    elif text.count(sec_number) == 1:
        form_to_submit = text.count('submit', text.index(sec_number))
    elif text.count(sec_number) > 1:
        for _ in range(text.count(sec_number)):
            i = text.index(sec_number)
            if text[i-1] != ':' and text[i-2] != ':':
                form_to_submit = text.count('submit', i)
        if form_to_submit == -1:
                return -1
    return num_forms - form_to_submit + 1


def get_class_status(course):
    br = mechanize.Browser()
    br.set_cookiejar(cookielib.LWPCookieJar())
    if course[0].upper() not in urls:
        return errors[0]
    r = br.open(urls[course[0].upper()])
    
    br.select_form(nr=0)
    br.form['p_dept'] = course[1]
    br.form['p_course'] = course[2]
    r = br.submit()
    if br.response().read()[2411:2413] == 'No':
        return errors[1]
    
    form_number = find_nr(br, course[3])
    if form_number == -1:
        return errors[2]
    br.select_form(nr=form_number)
    r = br.submit()
    text = br.response().read()[1900:].strip()
    if text == '':
        return errors[4]
    i = -1
    for _ in range(3):
        i = text.index('\n', i + 1)
    text = text[:i]
    fil = filter(lambda x: x!='' and x!='.', text.split('  '))
    msg = ''
    for f in fil:
        msg += f
        if msg[-1] == '\n':
            msg = msg[:-1] + ' '
    while msg.count('  '):
        msg = msg.replace('  ', ' ')
    msg = msg.strip() + '.'
    
    br.close()
    return str(msg)


def check_schedules():
    for course in schedules:
        status = get_class_status(course)
        if status == schedules[course]:
            pass
        elif status != schedules[course]:
            if status in errors:
                pass
            else:
                schedules[course] = status
                b = course[1]+' '+course[2]+' '+course[3]+': '+status
                client.sms.messages.create(to='+15622918691', from_=FROM_NUMBER, body=b[:160])


while True:
    try:
        right_now = datetime.now()
        if (right_now.second % 60 == 0):
            check_schedules()
            time.sleep(1)
    except URLError as e:
        pass
    except Exception as e:
        b = 'ERROR: '+str(e)
        client.sms.messages.create(to='+15622918691', from_=FROM_NUMBER, body=b[:160])
