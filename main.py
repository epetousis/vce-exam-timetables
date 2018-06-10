from flask import Flask, Response, render_template, send_from_directory
from exam import Exam
from icalendar import Calendar, Event
from datetime import datetime
import dateutil.parser
from dateutil.tz import gettz
import csv
app = Flask(__name__)

exams = []
aus_tz = gettz('Australia/Melbourne')

def setup_client_exam_values(exams):
    exam_names = [exam.name for exam in exams]
    exam_values = {}
    for exam in exam_names:
        if "Examination" in exam:
            pieces = exam.split(" Examination")
            subject_name = pieces[0]
            exam_values[subject_name] = subject_name + "*"
        elif "GAT" in exam:
            continue
        else:
            exam_values[exam] = exam
    
    return exam_values

with open("exam_schedule.csv", "r") as file:
    reader = csv.reader(file)
    exams = [Exam(name, session, day) for name, session, day in reader]
    client_exam_values = setup_client_exam_values(exams)

def generate_calendar(exams):
    cal = Calendar()
    cal.add('prodid', '-//VCE//VCE Exam Schedule//')
    cal.add('version', '2.0')
    cal.add('X-WR-CALNAME', 'VCE Exam Schedule')

    for exam in exams:
        event = Event()
        event.add('summary', "{} Exam".format(exam.name))
        event.add('dtstart', dateutil.parser.parse(exam.start_date).replace(tzinfo=aus_tz))
        event.add('dtend', dateutil.parser.parse(exam.end_date).replace(tzinfo=aus_tz))
        event.add('dtstamp', datetime.today())
        cal.add_component(event)
    
    return cal

@app.route("/")
def index():
    return render_template("index.html", exams=client_exam_values)

@app.route("/css/<path:path>")
def send_css(path):
    return send_from_directory("css", path)

@app.route("/api/<subject_string>")
def api(subject_string):
    subjects = subject_string.split(",")
    # Append GAT
    subjects.append("General Achievement Test (GAT)")
    wildcard_subjects = [subject.strip("*") for subject in subjects if subject.endswith("*")]
    matched_exams = [exam for exam in exams if exam.name in subjects]
    matched_wildcard_exams = [exam for exam in exams if exam.name.startswith(tuple(wildcard_subjects))]
    matched_exams.extend(matched_wildcard_exams)
    return Response(generate_calendar(matched_exams).to_ical(), mimetype="text/calendar")
