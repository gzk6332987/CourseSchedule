#!/Users/bmyy/dev/CourseSchedule/venv/bin/python
"""
Export data to csv file.
"""

import pandas as pd
from modules import Course, CourseTime, Teacher, Class


def export_data(data, filename):
    """
    Export data to csv file.
    """
    print("Target filename:", filename)

    # Open csv file.
    df = pd.read_csv(filename, encoding="gbk")

    # Foreach class
    for cur_class_num, cur_class_obj in data:
        cur_class_num: str
        cur_class_obj: Class

        decided_courses: tuple[CourseTime, Course] = cur_class_obj.decided_courses
        now_row = 0

        # Set column type.
        df[cur_class_num] = df[cur_class_num].astype(str)

        # Foreach course.
        for cur_course_time, cur_course in decided_courses:
            cur_course_time: CourseTime
            cur_course: Course

            # Set value.
            df.loc[now_row, cur_class_num] = cur_course.name
            now_row += 1

    # Save.
    df.to_csv(filename, index=False, encoding="gbk")


