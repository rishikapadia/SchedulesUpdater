SchedulesUpdater
================

Schedule Update Notifier



This code checks the updated UC Berkeley course enrollment site every minute, and notifies the user by text when a change is made to the status of one or more courses.
It enables users to manage their schedules separately from other users.


The file "schedule-2.py" is of my own creation. All other files are part of the imported "mechanize" or "twilio" libraries.




To run:
========
In the schedule-2.py file:
--------------------------
Change the fields marked with ****** to your 10 digit phone number or registered Twilio number, preceded by the number 1.
Fill in your Twilio Account SID and Authorization Token into the constant declarations.

In the data-2.py file:
----------------------
Include your phone number in the field provided, same as before.



Type into the terminal:
$ python schedule-2.py

