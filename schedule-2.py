"""
Rishi Kapadia
Schedule Update Notifier
CSUA Hackathon 11-9-12 to 11-10-12

Note: Run in Python version 2.7, NOT 3
"""

from mechanize import _mechanize
from mechanize import *
import urllib, urllib2, os, cookielib, time
from bs4 import BeautifulSoup
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
abbrev = {"FALL":"FA", "SPRING":"SP", "SUMMER":"SU"}
errors = ["Sorry, that is not a valid semester entry.", "Sorry, that is not a valid course entry.", "Sorry, that is not a valid section number.", "I'm sorry, you are not authorized to use this service.", "Telebears is down for an unscheduled maintenance.", "Section number returns too many results."]

ADMIN = '+*'
AUTHORIZED = ['+*']
schedules = {'+*': {}} # keys are phone numbers, values are dictionaries, of key msg_body(a list) and value class status

global critical
critical = False
previously_checked = datetime.now()

saved_so_far = {}

def read_from_file():
    f = open("data-2.py", "r")
    string = f.read()
    global schedules
    schedules = eval(string)
    f.close()


def write_to_file():
    # Write mode creates a new file or overwrites the existing content of the file. 
    # Write mode will _always_ destroy the existing contents of a file.
    try:
        # This will create a new file or **overwrite an existing file**.
        f = open("data-2.py", "w")
    	f.write(str(schedules)) # Write a string to a file
        f.close()
    except IOError:
        pass


#######


TEMPLATE_URL = "http://osoc.berkeley.edu/OSOC/osoc?y=0&p_term={0}&p_deptname={1}&p_course={2}"
MAPPINGS = {"DIS":"Discussion Section","LAB":"Lab"} 

def gen_url(department,course,semester="SP"):
   department = ' '.join(department.split()).replace(" ","+") #strips extra spaces, replaces spaces with + 
   return TEMPLATE_URL.format(semester,department,course) 

def return_live_course_size(ccn): 
      try: 
         url = "https://telebears.berkeley.edu/enrollment-osoc/osc"
         values = {'_InField2':str(ccn),'_InField3':'13B4'}
         data = urllib.urlencode(values) 
         req = urllib2.Request(url,data) 
         response = urllib2.urlopen(req)  
         html = response.read()
         soup = BeautifulSoup(html) 
         results = soup.find('blockquote').find('div').text.encode('utf-8').strip().split("\n")
         courseSizeInfo = results[0].split() 
         waitListSizeInfo = results[2].split()  
         return {'class size':courseSizeInfo[-1],'current size':courseSizeInfo[0],'waitlist limit':waitListSizeInfo[-1],'waitlist size':waitListSizeInfo[0]} 
      except AttributeError:
         print "Scraping Error"

def scrape_course_info(url):
    html = urllib2.urlopen(url).read() 
    soup = BeautifulSoup(html) 
    output_dict = {} 
    search_results = soup.find_all('table')[1:-1] 
    for each in search_results:
        class_details = each.text.encode('utf-8').strip().replace("\xc2\xa0","").split("\n")
        result_dict = {}
        for field in class_details:
            if field.split(":")[1]:
                result_dict[field.split(":")[0].lower()] = field.split(":")[1].lower().strip()
        result_dict['enrollment info'] = return_live_course_size(int(result_dict['course control number']))
        output_dict[result_dict["course"]] = result_dict 
    return output_dict


#######


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

    msg = "Course not found."
    class_name = course[0] + " " + course[1] + " " +course[2]
    if class_name in saved_so_far:
		section = saved_so_far[class_name]
    else:
        section = scrape_course_info(gen_url(course[1], course[2], abbrev[course[0].upper()]))
        saved_so_far[class_name] = section
    
    for class_name in section:
		if course[3] in class_name:
			s = section[class_name]['enrollment info']
			if s['waitlist size'] == '.' and s['waitlist limit'] == '.':
				return "enrolled: {0}/{1}, No waitlist".format(s['current size'], s['class size'])
			return "enrolled: {0}/{1}, waitlisted: {2}/{3}".format(s['current size'], s['class size'], s['waitlist size'], s['waitlist limit'])
    return msg
    


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
            read_from_file()
            right_now = datetime.now()
            if right_now.second % 60 == 0:
                check_admin()
                time.sleep(1)
                if right_now.minute % 10 == 0:
                    main(right_now)
                global saved_so_far
                saved_so_far = {}
            write_to_file()
        except urllib2.URLError as e:
            pass
        #except Exception as e:
        #    client.sms.messages.create(to=TO_NUMBER, from_=FROM_NUMBER, body='ERROR: '+str(e[:160]))
        #    break


def run2():
    while True:
        import urllib, urllib2, os, cookielib, time
        from bs4 import BeautifulSoup
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
