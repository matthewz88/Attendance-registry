Python 3.13.7 (tags/v3.13.7:bcee1c3, Aug 14 2025, 14:15:11) [MSC v.1944 64 bit (AMD64)] on win32
Enter "help" below or click "Help" above for more information.
# ============================================================
# ATTENDWISE - SMART ATTENDANCE DASHBOARD
# VIBECRAFT HACKATHON - SRMIST TRICHY
#
# Generic / Dataset-Driven Version
# ============================================================

import csv
import math
import os
from datetime import datetime, timedelta

SEMESTER_START = datetime(2026, 8, 29)
SEMESTER_END = datetime(2026, 11, 29)

MIN_ATTENDANCE = 75
TARGET_ATTENDANCE = 90


# ============================================================
# BASIC ATTENDANCE CALCULATIONS
# ============================================================

def percentage(attended, conducted):
    if conducted <= 0:
        return 0.0
    return (attended / conducted) * 100


def classes_needed(attended, conducted, target):
    """
    Number of consecutive future classes that must be attended
    to reach target attendance.
    """

    target = target / 100

    if conducted == 0:
        return 0

    if attended / conducted >= target:
        return 0

    if target >= 1:
        return float("inf")

    x = (target * conducted - attended) / (1 - target)

    return max(0, math.ceil(x))


def safe_skips(attended, conducted, minimum=75):
    """
    Maximum number of consecutive classes that can be skipped
    while remaining >= minimum attendance.
    """

    if conducted == 0:
        return 0

    minimum = minimum / 100

    x = attended / minimum - conducted

    return max(0, math.floor(x))


def status(p):

    if p >= 90:
        return "EXCELLENT"

    elif p >= 80:
        return "SAFE"

    elif p >= 75:
        return "WARNING"

    else:
        return "DETENTION RISK"


# ============================================================
# GENERIC CSV COLUMN DETECTION
# ============================================================

def normalize(text):

    return (
        str(text)
        .strip()
        .lower()
        .replace("_", "")
        .replace(" ", "")
        .replace("-", "")
    )


def find_column(headers, possibilities):

    normalized_headers = {
        normalize(h): h for h in headers
    }

    for possible in possibilities:

        p = normalize(possible)

        if p in normalized_headers:
            return normalized_headers[p]

    return None


# ============================================================
# READ ANY SIMILAR CSV TIMETABLE
# ============================================================

def load_timetable(filename):

    timetable = []

    try:

        with open(
            filename,
            "r",
            encoding="utf-8-sig",
            newline=""
        ) as file:

            reader = csv.DictReader(file)

            headers = reader.fieldnames

            if not headers:
                print("CSV has no headers.")
                return []

            # Automatically detect common column names

            day_col = find_column(
                headers,
                [
                    "day",
                    "weekday",
                    "days"
                ]
            )

            subject_col = find_column(
                headers,
                [
                    "subject",
                    "subject name",
                    "course",
                    "course name",
                    "paper",
                    "module"
                ]
            )

            time_col = find_column(
                headers,
                [
                    "time",
                    "timing",
                    "period",
                    "slot",
                    "hour"
                ]
            )

            section_col = find_column(
                headers,
                [
                    "section",
                    "class",
                    "batch"
                ]
            )

            print("\nDetected columns:")

            print("Day     :", day_col)
            print("Subject :", subject_col)
            print("Time    :", time_col)
            print("Section :", section_col)

            if day_col is None or subject_col is None:

                print(
                    "\nCould not automatically detect "
                    "Day or Subject columns."
                )

                return []

            for row in reader:

                day = row.get(day_col, "").strip()
                subject = row.get(subject_col, "").strip()

                time = (
                    row.get(time_col, "").strip()
                    if time_col else ""
                )

                section = (
                    row.get(section_col, "").strip()
                    if section_col else ""
                )

                # Ignore empty rows

                if day and subject:

                    timetable.append(
                        {
                            "day": day,
                            "subject": subject,
                            "time": time,
                            "section": section
                        }
                    )

        return timetable

    except Exception as e:

        print("\nCould not load CSV:", e)

        return []


# ============================================================
# MANUAL TIMETABLE MODE
# ============================================================

def manual_timetable():

    timetable = []

    print("\nMANUAL TIMETABLE ENTRY")
    print("----------------------")

    n = int(
        input(
            "How many timetable entries do you want to enter? "
        )
    )

    for i in range(n):

        print(f"\nEntry {i + 1}")

        day = input(
            "Day (Monday/Tuesday/etc): "
        ).strip()

        subject = input(
            "Subject: "
        ).strip()

        time = input(
            "Time/Period: "
        ).strip()

        section = input(
            "Section: "
        ).strip()

        timetable.append(
            {
                "day": day,
                "subject": subject,
                "time": time,
                "section": section
            }
        )

    return timetable


# ============================================================
# EXTRACT SUBJECTS AUTOMATICALLY
# ============================================================

def get_subjects(timetable):

    subjects = []

    for row in timetable:

        subject = row["subject"]

        if subject not in subjects:
            subjects.append(subject)

    return subjects


# ============================================================
# DAY CONVERSION
# ============================================================

DAY_MAP = {

    "monday": 0,
    "mon": 0,

    "tuesday": 1,
    "tue": 1,
    "tues": 1,

    "wednesday": 2,
    "wed": 2,

    "thursday": 3,
    "thu": 3,
    "thur": 3,

    "friday": 4,
    "fri": 4,

    "saturday": 5,
    "sat": 5,

    "sunday": 6,
    "sun": 6
}


def day_number(day):

    return DAY_MAP.get(
        day.strip().lower(),
        None
    )


# ============================================================
# COUNT REMAINING CLASSES FROM TIMETABLE
# ============================================================

def remaining_classes(
    subject,
    timetable,
    from_date
):

    count = 0

    current = from_date

    while current <= SEMESTER_END:

        weekday = current.weekday()

        for row in timetable:

            d = day_number(row["day"])

            if (
                d == weekday
                and row["subject"] == subject
            ):
                count += 1

        current += timedelta(days=1)

    return count


# ============================================================
# FIND UPCOMING CLASS DATES
# ============================================================

def upcoming_classes(
    subject,
    timetable,
    from_date,
    limit=5
):

    results = []

    current = from_date

    while (
        current <= SEMESTER_END
        and len(results) < limit
    ):

        weekday = current.weekday()

        for row in timetable:

            d = day_number(row["day"])

            if (
                d == weekday
                and row["subject"] == subject
            ):

                results.append(
                    {
                        "date":
                        current.strftime(
                            "%d %b %Y"
                        ),

                        "day":
                        current.strftime(
                            "%A"
                        ),

                        "time":
                        row["time"]
                    }
                )

        current += timedelta(days=1)

    return results


# ============================================================
# RECOVERY DATE
# ============================================================

def recovery_date(
    subject,
    timetable,
    from_date,
    classes_required
):

    if classes_required == 0:
        return "Target already achieved"

    upcoming = upcoming_classes(
        subject,
        timetable,
        from_date,
        classes_required
    )

    if len(upcoming) < classes_required:

        return "Not achievable before semester ends"

    return upcoming[-1]["date"]


# ============================================================
# CHECK WHETHER 90% IS POSSIBLE
# ============================================================

def target_possible(
    attended,
    conducted,
    remaining,
    target
):

    final_attended = attended + remaining
    final_total = conducted + remaining

    final_percentage = percentage(
        final_attended,
        final_total
    )

    return (
        final_percentage >= target,
        final_percentage
    )


# ============================================================
# SUBJECT ANALYSIS
# ============================================================

def analyse_subject(
    subject,
    attended,
    conducted,
    timetable,
    today
):

    current = percentage(
        attended,
        conducted
    )

    need75 = classes_needed(
        attended,
        conducted,
        75
    )

    need90 = classes_needed(
        attended,
        conducted,
        90
    )

    skips = safe_skips(
        attended,
        conducted,
        75
    )

    remaining = remaining_classes(
        subject,
        timetable,
        today
    )

    print("\n")
    print("=" * 60)
    print(subject.upper())
    print("=" * 60)

    print(
        f"Current attendance : "
        f"{current:.2f}%"
    )

    print(
        f"Status             : "
        f"{status(current)}"
    )

    print(
        f"Classes remaining  : "
        f"{remaining}"
    )

    # -----------------------------
    # 75% analysis
    # -----------------------------

    if current < 75:

        print("\n*** DETENTION ALERT ***")

        print(
            f"Attend next {need75} "
            f"{subject} class(es)"
        )

        date = recovery_date(
            subject,
            timetable,
            today,
            need75
        )

        print(
            "Expected recovery date:",
            date
        )

    else:

        print(
            f"\nSafe skips before "
            f"falling below 75%: "
            f"{skips}"
        )

    # -----------------------------
    # 90% analysis
    # -----------------------------

    possible, maximum = target_possible(
        attended,
        conducted,
        remaining,
        90
    )

    if current >= 90:

        print(
            "90% Target: "
            "Already achieved!"
        )

    elif possible:

        print(
            f"Classes needed for "
            f"90%: {need90}"
        )

    else:

        print(
            "\n90% target cannot be "
            "reached before semester end."
        )

        print(
            f"Maximum possible attendance "
            f"if every remaining class is "
            f"attended: {maximum:.2f}%"
        )

    # -----------------------------
    # NEXT CLASS
    # -----------------------------

    upcoming = upcoming_classes(
        subject,
        timetable,
        today,
        3
    )

    print("\nNext Classes:")

    if upcoming:

        for c in upcoming:

            print(
                c["date"],
                "-",
                c["day"],
                "-",
                c["time"]
            )

    else:

        print(
            "No remaining classes found."
        )

    # -----------------------------
    # SKIP PREDICTION
    # -----------------------------

    skip_percentage = percentage(
        attended,
        conducted + 1
    )

    print(
        f"\nIf next class is skipped: "
        f"{skip_percentage:.2f}%"
    )

    if skip_percentage < 75:

        print(
            "AI RECOMMENDATION: "
            "DO NOT SKIP!"
        )

        print(
            "Skipping the next class "
            "will put you in detention risk."
        )

    elif skip_percentage < 80:

        print(
            "AI RECOMMENDATION: "
            "Better to attend."
        )

    else:

        print(
            "AI RECOMMENDATION: "
            "Skipping one class will still "
            "keep you above 75%."
        )


# ============================================================
# SAMPLE DATA
#
# This lets your program work even if the online compiler
# does not support file uploads.
# ============================================================

def sample_timetable():

    return [

        {
            "day": "Monday",
            "subject": "Mathematics",
            "time": "09:00",
            "section": "A"
        },

        {
            "day": "Monday",
            "subject": "Python",
            "time": "11:00",
            "section": "A"
        },

        {
            "day": "Tuesday",
            "subject": "Physics",
            "time": "10:00",
            "section": "A"
        },

        {
            "day": "Wednesday",
            "subject": "Mathematics",
            "time": "09:00",
            "section": "A"
        },

        {
            "day": "Wednesday",
            "subject": "Python",
            "time": "11:00",
            "section": "A"
        },

        {
            "day": "Thursday",
            "subject": "Physics",
            "time": "10:00",
            "section": "A"
        },

        {
            "day": "Friday",
            "subject": "Mathematics",
            "time": "09:00",
            "section": "A"
        },

        {
            "day": "Friday",
            "subject": "Python",
            "time": "11:00",
            "section": "A"
        }
    ]


# ============================================================
# MAIN PROGRAM
# ============================================================

print(
    """
============================================================

                    ATTENDWISE

             SMART ATTENDANCE PLANNER

       VIBECRAFT - AI TOOL HACKATHON

============================================================

Semester:
29 August 2026 - 29 November 2026

AttendWise doesn't just tell students
their attendance.

It tells them WHAT TO DO NEXT.

============================================================
"""
)


# ============================================================
# CHOOSE DATA SOURCE
# ============================================================

print("Choose timetable source:\n")

print("1. Load CSV dataset")
print("2. Enter timetable manually")
print("3. Use demo dataset")

choice = input(
    "\nEnter 1, 2 or 3: "
)


if choice == "1":

    filename = input(
        "Enter CSV filename: "
    )

    timetable = load_timetable(
        filename
    )

    if not timetable:

        print(
            "\nDataset could not be read."
        )

        print(
            "Switching to demo dataset."
        )

        timetable = sample_timetable()


elif choice == "2":

    timetable = manual_timetable()


else:

    timetable = sample_timetable()


# ============================================================
# SHOW DATASET INFORMATION
# ============================================================

subjects = get_subjects(
    timetable
)

print("\n")
print("=" * 60)
print("DATASET LOADED")
print("=" * 60)

print(
    "Timetable entries:",
    len(timetable)
)

print(
    "Subjects detected:",
    len(subjects)
)

for subject in subjects:
    print("-", subject)


# ============================================================
# STUDENT DETAILS
# ============================================================

student = input(
    "\nStudent Name: "
)

section = input(
    "Section: "
)


# Use today's date, but allow demo date

date_input = input(
    "\nEnter today's date "
    "(DD-MM-YYYY) "
    "or press Enter for 28-09-2026: "
)

if date_input.strip() == "":

    today = datetime(
        2026,
        9,
        28
    )

else:

    try:

        today = datetime.strptime(
            date_input,
            "%d-%m-%Y"
        )

    except:

        today = datetime(
            2026,
            9,
            28
        )


# ============================================================
# ATTENDANCE INPUT
# ============================================================

attendance_data = {}


for subject in subjects:

    print("\n")
    print(
        "Enter attendance for:",
        subject
    )

    conducted = int(
        input(
            "Classes conducted: "
        )
    )

    attended = int(
        input(
            "Classes attended: "
        )
    )

    if attended > conducted:

        print(
            "Attended cannot exceed "
            "conducted."
        )

        attended = conducted

    attendance_data[subject] = {

        "attended": attended,

        "conducted": conducted
    }


# ============================================================
# SMART DASHBOARD
# ============================================================

print("\n\n")

print(
    "=" * 60
)

print(
    "              SMART ATTENDANCE DASHBOARD"
)

print(
    "=" * 60
)

print(
    "Student:",
    student
)

print(
    "Section:",
    section
)

print(
    "Date:",
    today.strftime(
        "%d %B %Y"
    )
)


total_attended = 0
total_conducted = 0


for subject in subjects:

    data = attendance_data[
        subject
    ]

    analyse_subject(

        subject,

        data["attended"],

        data["conducted"],

        timetable,

        today
    )

    total_attended += data[
        "attended"
    ]

    total_conducted += data[
        "conducted"
    ]


# ============================================================
# OVERALL ANALYSIS
# ============================================================

overall = percentage(
    total_attended,
    total_conducted
)


print("\n\n")

print(
    "=" * 60
)

print(
    "                 OVERALL ANALYSIS"
)

print(
    "=" * 60
)

print(
    f"Overall Attendance: "
    f"{overall:.2f}%"
)

print(
    "Status:",
    status(overall)
)


if overall < 75:

    required = classes_needed(
        total_attended,
        total_conducted,
        75
    )

    print(
        "\nURGENT:"
    )

    print(
        f"Attend approximately "
        f"{required} consecutive classes "
        f"to recover above 75%."
    )


elif overall < 80:

    print(
        "\nWARNING:"
    )

    print(
        "You are close to the "
        "detention threshold."
    )


elif overall < 90:

    print(
        "\nSAFE:"
    )

    print(
        "Your attendance is currently safe."
    )


else:

    print(
        "\nEXCELLENT:"
    )

    print(
        "You are maintaining "
        "excellent attendance."
    )


print(
    """
============================================================

...                     ATTENDWISE
... 
... Traditional portals answer:
... 
...        "What is my attendance?"
... 
... AttendWise answers:
... 
...        "What should I do next?"
... 
... PLAN  |  PREDICT  |  PREVENT DETENTION
... 
... ============================================================
... """
