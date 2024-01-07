import matplotlib.pyplot as plt
from modules import CourseTime, Course, Teacher, Class


# def plot_class(target_class: Class, data: list[tuple[CourseTime, Course]]):
#     """
#     Draw a picture of the class follow the data.
#     """
#     result_day = []
#     # Process data.
#     for piece in data:
#         course_time, course = piece
#         day = course_time.day
#         if day not in result_day:
#             result_day.append(day)