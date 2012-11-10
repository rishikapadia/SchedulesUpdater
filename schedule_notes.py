"""
Rishi Kapadia
11-9-12

Note: Run in Python version 2.7, NOT 3
"""

import mechanize, urllib, urllib2, cookielib
from _beautifulsoup import BeautifulSoup
from twilio.rest import TwilioRestClient
from datetime import datetime


TWILIO_PHONE_NUMBER = "(562) 352 - 0309"
TWILIO_ACCOUNT_SID = 'ACdd9b3407c0ff20c450ebe385bc09c71a'
TWILIO_AUTH_TOKEN = '0a1ffeb8651886b31fe61bcd1ee3d47f'
client = TwilioRestClient(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)


FROM_NUMBER = '+15623520309'     # Twilio phone number
TO_NUMBER = '+15622918691'     # Default TO_NUMBER

URLS = ["http://schedule.berkeley.edu/srchfall.html", "http://schedule.berkeley.edu/srchsprg.html", "http://schedule.berkeley.edu/srchsmr.html"]

admins = ('+15622918691')
authorized = ['+15622918691']
schedules = {'+15622918691': {}} # keys are phone numbers, values are dictionaries, of key msg_body and value class status

critical = False
previously_checked = datetime.now()



def find_nr(br, sec_number):
    # 
    return

def get_class_status(lines): # goes online, web crawling, scraping
    # open browser
    # navigate b/w fall/spring/summer, using lines[0]
        # if error, return "Sorry, that is not a valid semester entry."
    # set lines[1], lines[2] to appropriate forms / text fields
    # click submit
        # if error, return "Sorry, that is not a valid course entry."
    # search for section number, lines[3]
        # if error, return "Sorry, that is not a valid section number."
    # click on appropriate button
    # scrape for text pattern
        # if found, return status as a string. if critical, change to False
        # else if not found, change critical to True, return "Changes to server. Check site."
    # close browser
    return # msg_body + ':' + string

def check_schedules():
    # for each person in schedules
        # for each course/msg_body in person
            # status = get_class_status(lines)
            # if status is "Changes to server. Check site.": send msg and return
            # elif status different from schedules[person][msg_body]
                # change that class status
                # send text with new status
    return

def analyze_msg(msg):
    # split body.upper() by whitespace (msg_body)
    # error checking: index errors
    # if stop / stop all message, stop / stop all from that number
    # status = get_class_status(msg_body)
    # if status is "Changes to server. Check site.": send msg and return
    # if not one of the error messages,
        # append/update course to that person's dictionary: schedules[person][new_msg][status]= status
    return  # status message

def authorized(msg):
    # status_text = analyze_msg(msg)
    # send message: status_text
    return

def admin(msg):
    # split body.upper() by whitespace
    # error checking: index errors
    #if first word is "AUTHORIZE", then add second word(person) to list of authorized
        # schedules[lines[1]] = {}
        # send confirmation
    # if first word is "DEAUTHORIZE", then remove word from list, if possible. Send confirmation results. del schedules[lines[1]]
    # else: call authorized(msg)
    return

def main(right_now):
    # check all messages, from previously_checked to now
        # if admin: admin(msg)
        # if authorized: authorized(msg)
        # else send msg: "I'm sorry, you are not authorized to use this service."
    # check schedules for changes
    # change previously_checked to right_now
    return


while True:
    try:
        right_now = datetime.now()
        if critical and (right_now.second % 60 == 0):
            main(right_now)
        elif right_now.minute % 10 == 0:
            main(right_now)
    except Exception as e:
        client.sms.messages.create(to=TO_NUMBER, from_=FROM_NUMBER, body=e[:160])
        continue




#######################
"""
client.sms.messages.create(to=TO_NUMBER, from_=FROM_NUMBER, body="Hello World.")



for msg in client.sms.messages.iter(to=TWILIO_PHONE_NUMBER):
    if msg.from_ in authorized:
        continue
        
    votes[msg.body.strip().upper()] += 1
    voted.add(msg.from_)
"""

"""
http://wwwsearch.sourceforge.net/mechanize/
http://wwwsearch.sourceforge.net/mechanize/doc.html
http://stockrt.github.com/p/emulating-a-browser-in-python-with-mechanize/
http://stackoverflow.com/questions/2648738/html-javascript-automaticly-getting-link-from-submit-button-maybe-automating-wi

view-source:http://schedule.berkeley.edu/srchfall.html
"""

"""
br = mechanize.Browser()
br.set_cookiejar(cookielib.LWPCookieJar())
r = br.open('http://schedule.berkeley.edu/srchsprg.html')
br.select_form(nr=0)
br.form['p_dept'] = 'math'
br.form['p_course'] = '1b'
r = br.submit()
br.select_form(nr=find_nr(br, '203'))
r = br.submit()
text = br.response().read()[1900:].strip()
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

print msg.strip() + '.'
br.close()


# print br.response().read()    --> the html text

##################

def find_nr(br, sec_number):
    text = br.response().read()
    num_forms = len([f for f in br.forms()])
    form_to_submit = -1
    if text.count(sec_number) == 1:
        form_to_submit = text.count('submit', text.index(sec_number))
    else:
        for _ in range(text.count(sec_number)):
            i = text.index(sec_number)
            if text[i-1] != ':' or text[i-2] != ':':
                form_to_submit = text.count('submit', i)
        if form_to_submit == -1:
                return -1
    return num_forms - form_to_submit + 1    
"""
