from bs4 import BeautifulSoup
from exam import Exam
from datetime import datetime, date
import pytz
import csv

# If a line in the table contains these keywords, it's actually an exam instruction.
non_exam_keywords = ["commences with a", "is preceded by"]

def fstrip(string):
    return " ".join([line.strip() for line in string.splitlines()])

def parse_exams(s):
    exams = []

    for day_element in s.find_all("tr"):
        for session_element in day_element.find_all("td"):
            for exam_element in session_element.find_all("p")[1::]:
                # Ignore any links that may be in the table.
                if exam_element.a:
                    continue

                day = fstrip(day_element.th.text)
                session_times = session_element.p.text.strip().split(" – ")
                exam_name = fstrip(exam_element.text)

                exploded_exam_name = exam_name.split(",")
                if len(exam_name.split(",")) >= 3:
                    # Some VCE subjects have commas. This has two or more commas,
                    # therefore this is a language exam.
                    language_exams = [parse_exam(day, session_times, fstrip(name)) for name in exploded_exam_name]
                    exams.extend(language_exams)
                else:
                    exam = parse_exam(day, session_times, exam_name)
                    if exam:
                        exams.append(exam)

    return exams

def parse_exam(day, session_times, exam_name):
    # If a line in the table contains the forbidden keywords, it's actually an exam instruction.
    # Also, if a day contains " to " (with spaces so we don't reject October dates), it is a
    # date range, meaning no exams are scheduled (it's just VCAA telling people to look at their
    # advice slips). Don't attempt parsing if any of these conditions apply.
    if " to " in day or any(keyword in exam_name for keyword in non_exam_keywords):
        return None

    current_year = datetime.today().year

    start_time = datetime.strptime(session_times[0], "%I.%M%p")
    end_time = datetime.strptime(session_times[1], "%I.%M%p")

    start_date = datetime.strptime(day, "%A %d %B")
    start_date = start_date.replace(year=current_year, hour=start_time.hour, minute=start_time.minute)
    end_date = datetime.strptime(day, "%A %d %B")
    end_date = end_date.replace(year=current_year, hour=end_time.hour, minute=end_time.minute)
    # Uses format of Friday 2 November, 2.00pm – 3.45pm

    # Localise
    locale = pytz.timezone("Australia/Melbourne")
    start_date = locale.localize(start_date)
    end_date = locale.localize(end_date)

    exam = Exam(exam_name, start_date, end_date)
    return exam

def write_exam_timetable(exams):
    with open("exam_schedule.csv", "w") as csv_file:
        writer = csv.writer(csv_file)
        for exam in exams:
            writer.writerow([exam.name, exam.start_date.isoformat(), exam.end_date.isoformat()])

s = BeautifulSoup(open("exam_timetable.html"), "html.parser")
exam_timetables = s.find_all("table", { "class" : "examtimetable" })
exam_days = [parse_exams(exam_day.tbody) for exam_day in exam_timetables]
exams = [exam for day in exam_days for exam in day]

print("There are {} exams this year.".format(len(exams)))

write_exam_timetable(exams)
