"""
Rishi Kapadia
Schedule Update Notifier
CSUA Hackathon 11-9-12 to 11-10-12

Note: Run in Python version 2.7, NOT 3
"""

from mechanize import _mechanize
from mechanize import *
import urllib, urllib2, cookielib, time
from bs4 import BeautifulSoup
from mechanize._beautifulsoup import BeautifulSoup
from twilio.rest import TwilioRestClient
from datetime import datetime, timedelta
from email.utils import parsedate


TWILIO_PHONE_NUMBER = "*"
TWILIO_ACCOUNT_SID = '*'
TWILIO_AUTH_TOKEN = '*'
client = TwilioRestClient(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

FROM_NUMBER = '+*'     # Twilio phone number
TO_NUMBER = '+*'     # Default TO_NUMBER

urls = {'FALL': 'http://schedule.berkeley.edu/srchfall.html', 'SPRING': 'http://schedule.berkeley.edu/srchsprg.html', 'SUMMER': 'http://schedule.berkeley.edu/srchsmr.html'}
errors = ["Sorry, that is not a valid semester entry.", "Sorry, that is not a valid course entry.", "Sorry, that is not a valid section number.", "I'm sorry, you are not authorized to use this service.", "Telebears is down for an unscheduled maintenance.", "Section number returns too many results."]

ADMIN = '+*'
AUTHORIZED = ['+*']
schedules = {'+*': {}} # keys are phone numbers, values are dictionaries, of key msg_body(a list) and value class status

global critical
critical = False
previously_checked = datetime.now()


def read_from_file():
    f = open("data.py", "r")
    string = f.read()
    global schedules
    schedules = eval(string)
    f.close()


def write_to_file():
    # Write mode creates a new file or overwrites the existing content of the file. 
    # Write mode will _always_ destroy the existing contents of a file.
    try:
        # This will create a new file or **overwrite an existing file**.
        f = open("data.py", "w")
        if schedules != {'+15622918691': {}}:
            f.write(str(schedules)) # Write a string to a file
        f.close()
    except IOError:
        pass


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
    br = _mechanize.Browser()
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
    
    section = ' '+course[3]+' '
    if br.response().read().count(section) > 1:
        return errors[5]
    form_number = find_nr(br, section)
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


def check_schedule(course, person):
    global critical
    status = get_class_status(course)
    if status in errors:
        critical = True
        return
    elif status == schedules[person][course]:
        critical = False
    elif status != schedules[person][course]:
        schedules[person][course] = status
        b = course[1]+' '+course[2]+' '+course[3]+': '+status
        client.sms.messages.create(to=person, from_=FROM_NUMBER, body=b[:160])

def check_all():
    for person in schedules:
        for course in schedules[person]:
            check_schedule(course, person)

def check_admin():
    for course in schedules[ADMIN]:
        check_schedule(course, ADMIN)

def analyze_msg(msg):
    text_lines = tuple(str(msg.body).upper().split())
    if len(text_lines) < 1:
        return
    elif len(text_lines) == 1:
        return 'Invalid entry.'
    elif text_lines[0].upper() == 'STOP':
        if text_lines[1].upper() == 'ALL':
            schedules[msg.from_] = {}
            return 'Successfully stopped all courses.'
        elif len(text_lines) < 5:
            return 'Not enough arguments.'
        elif tuple(text_lines[1:5]) in schedules[msg.from_]:
            del schedules[msg.from_][tuple(text_lines[1:5])]
            return 'Successfully stopped: '+text_lines[1]+' '+text_lines[2]+' '+text_lines[3]+' '+text_lines[4]
        else:
            return 'Course not found: '+text_lines[1]+' '+text_lines[2]+' '+text_lines[3]+' '+text_lines[4]
    elif len(text_lines) < 4:
        return 'Not enough arguments.'
    status = get_class_status(text_lines)
    if status == 'Changes to server. Check site.':
        return 'Changes to server. Unable to add course at this moment.'
    elif status in errors:
        return status
    schedules[msg.from_][tuple(text_lines[:4])] = str(status)
    return text_lines[1]+' '+text_lines[2]+' '+text_lines[3]+': '+status


def authorized(msg):
    status_text = str(analyze_msg(msg))
    if status_text:
        client.sms.messages.create(to=msg.from_, from_=FROM_NUMBER, body=status_text[:160])

class UserError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)


def admin(msg):
    text_lines = msg.body.split()
    if len(text_lines) < 1:
        return
    elif len(text_lines) == 1:
        if text_lines[0].lower() == 'clear' or text_lines[0].lower() == 'reset':
            global schedules
            schedules = {'+15622918691': {}}
    elif text_lines[0].upper() == 'EXIT':
        raise UserError("User-prompted exception successful.")
    elif text_lines[0].upper() == 'AUTHORIZE':
        schedules[text_lines[1]] == {}
        AUTHORIZED.append(text_lines[1])
        client.sms.messages.create(to=msg.from_, from_=FROM_NUMBER, body='You are now authorized!')
        b = str(msg.from_) + ' is now authorized.'
        client.sms.messages.create(to=ADMIN, from_=FROM_NUMBER, body=b[:160])
    elif text_lines[0].upper() == 'DEAUTHORIZE':
        if text_lines[1] in AUTHORIZED:
            AUTHORIZED.remove(text_lines[1])
            del schedules[text_lines[1]]
            b = str(text_lines[1])+' is now deauthorized.'
            client.sms.messages.create(to=ADMIN, from_=FROM_NUMBER, body=b[:160])
        else:
            b = str(text_lines[1])+' was not found.'
            client.sms.messages.create(to=ADMIN, from_=FROM_NUMBER, body=b[:160])
    else:
        authorized(msg)


def change_datetime(dt):
    return dt #+ timedelta(hours=8)  # GMT-8 to UTC #


def change_unicode(date_sent):   # UTC
    t = parsedate(date_sent)
    return datetime(t[0], t[1], t[2], t[3], t[4], t[5], 999999)


def main(right_now):
    global previously_checked
    for msg in client.sms.messages.iter(to=TWILIO_PHONE_NUMBER):
        if change_unicode(msg.date_sent) >= change_datetime(previously_checked):
            if msg.from_ == ADMIN:
                admin(msg)
            elif msg.from_ in AUTHORIZED:
                authorized(msg)
            else:
                client.sms.messages.create(to=msg.from_, from_=FROM_NUMBER, body=errors[3])
                b = str(msg.from_) + ' tried to use this service.'
                client.sms.messages.create(to=ADMIN, from_=FROM_NUMBER, body=b)
    check_all()
    previously_checked = right_now


"""
try:
    right_now = datetime.now()
    check_admin()
    if right_now.minute % 10 == 0:
        main(right_now)
except urllib2.URLError as e:
    pass
except Exception as e:
    client.sms.messages.create(to=TO_NUMBER, from_=FROM_NUMBER, body='ERROR: '+str(e[:160]))
    break
"""



def run():
    while True:
        try:
            right_now = datetime.now()
            if right_now.second % 60 == 0:
                read_from_file()
                check_admin()
                time.sleep(1)
                if right_now.minute % 10 == 0:
                    main(right_now)
                write_to_file()
        except urllib2.URLError as e:
            pass
        #except Exception as e:
        #    client.sms.messages.create(to=TO_NUMBER, from_=FROM_NUMBER, body='ERROR: '+str(e[:160]))
        #    break


def run2():
    while True:
        #import mechanize, urllib, urllib2, cookielib, time
        #from _beautifulsoup import BeautifulSoup
        from twilio.rest import TwilioRestClient
        from datetime import datetime, timedelta
        from email.utils import parsedate

        global client
        client = TwilioRestClient(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

        try:
            run()
        except UserError as e:
            break
        client.sms.messages.create(to=TO_NUMBER, from_=FROM_NUMBER, body="Run Restarted: "+ str(datetime.now()))

run2()
