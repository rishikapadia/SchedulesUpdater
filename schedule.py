"""
Rishi Kapadia
Schedule Update Notifier
Hackathon 11-9-12 to 11-10-12

Note: Run in Python version 2.7, NOT 3
"""

import mechanize, urllib, urllib2, cookielib, time
from _beautifulsoup import BeautifulSoup
from twilio.rest import TwilioRestClient
from datetime import datetime


TWILIO_PHONE_NUMBER = "(562) 352 - 0309"
TWILIO_ACCOUNT_SID = 'ACdd9b3407c0ff20c450ebe385bc09c71a'
TWILIO_AUTH_TOKEN = '0a1ffeb8651886b31fe61bcd1ee3d47f'
client = TwilioRestClient(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

FROM_NUMBER = '+15623520309'     # Twilio phone number
TO_NUMBER = '+15622918691'     # Default TO_NUMBER

urls = {'FALL': 'http://schedule.berkeley.edu/srchfall.html', 'SPRING': 'http://schedule.berkeley.edu/srchsprg.html', 'SUMMER': 'http://schedule.berkeley.edu/srchsmr.html'}
errors = ["Sorry, that is not a valid semester entry.", "Sorry, that is not a valid course entry.", "Sorry, that is not a valid section number.", "I'm sorry, you are not authorized to use this service.", "Telebears is down for an unscheduled maintenance."]

ADMIN = '+15622918691'
AUTHORIZED = ['+15622918691']
schedules = {'+15622918691': {}} # keys are phone numbers, values are dictionaries, of key msg_body(a list) and value class status

global critical
critical = False
previously_checked = datetime.now()




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
            if text[i-1] != ':' or text[i-2] != ':':
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
    return msg


def check_schedules():
    for person in schedules:
        for course in schedules[person]:
            global critical
            status = get_class_status(course)
            if status == 'Changes to server. Check site.':
                critical = True
                client.sms.messages.create(to=person, from_=FROM_NUMBER, body=status)
            elif status == errors[4]:
                return
            elif status == schedules[person][course]:
                critical = False
            elif status != schedules[person][course]:
                schedules[person][course] = status
                client.sms.messages.create(to=person, from_=FROM_NUMBER, body=course[1]+' '+course[2]+' '+course[3]+': '+status)


def analyze_msg(msg):
    text_lines = msg.body.split()
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
    schedules[msg.from_][text_lines[0:4]] = tuple(status)
    return status


def authorized(msg):
    status_text = analyze_msg(msg)
    if status_text:
        client.sms.messages.create(to=msg.from_, from_=FROM_NUMBER, body=status_text)


def admin(msg):
    text_lines = msg.body.split()
    if len(text_lines) < 1:
        return
    elif len(text_lines) == 1:
        if text_lines[0].lower() == 'clear' or text_lines[0].lower() == 'reset':
            global schedules
            schedules = {'+15622918691': {}}
    elif text_lines[0].upper() == 'AUTHORIZE':
        schedules[text_lines[1]] == {}
        AUTHORIZED.append(text_lines[1])
        client.sms.messages.create(to=msg.from_, from_=FROM_NUMBER, body='You are now authorized!')
        client.sms.messages.create(to=ADMIN, from_=FROM_NUMBER, body=msg.from_ + ' is now authorized.')
    elif text_lines[0].upper() == 'DEAUTHORIZE':
        if text_lines[1] in AUTHORIZED:
            AUTHORIZED.remove(text_lines[1])
            del schedules[text_lines[1]]
            client.sms.messages.create(to=ADMIN, from_=FROM_NUMBER, body=text_lines[1]+' is now deauthorized.')
        else:
            client.sms.messages.create(to=ADMIN, from_=FROM_NUMBER, body=text_lines[1]+' was not found.')
    authorized(msg)


def change_datetime(datetime):
    return datetime.strftime('%Y %m %d %H:%M:%S')


def change_unicode(date_sent):
    t = str(date_sent)[5:25]
    return t[-13:-9]+' '+str(time.strptime(t[3:6], '%b').tm_mon)+' '+t[:2]+' '+t[-8:]


def main(right_now):
    for msg in client.sms.messages.iter(to=TWILIO_PHONE_NUMBER):
        global previously_checked
        if change_unicode(msg.date_sent) >= change_datetime(previously_checked):
            if msg.from_ == ADMIN:
                admin(msg)
            elif msg.from_ in AUTHORIZED:
                authorized(msg)
            else:
                client.sms.messages.create(to=msg.from_, from_=FROM_NUMBER, body=errors[3])
                b = msg.from_ + ' tried to use this service.'
                client.sms.messages.create(to=ADMIN, from_=FROM_NUMBER, body=b)
    check_schedules()
    previously_checked = right_now


while True:
    try:
        right_now = datetime.now()
        if critical and (right_now.second % 60 == 0):
            main(right_now)
            time.sleep(1)
        elif right_now.minute % 10 == 0:
            main(right_now)
            time.sleep(60)
    except Exception as e:
        client.sms.messages.create(to=TO_NUMBER, from_=FROM_NUMBER, body=e[:160])
        continue
