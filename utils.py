"""
Utility functions.
"""
from modules import Course, CourseTime


def normalize_list(probability_list: list[float]) -> list[float]:
    """
    Normalize a list of probability.
    """
    total = sum(probability_list)
    normalized_list = [prob / total for prob in probability_list]
    return normalized_list


def decided_courses_cmp(a: tuple[CourseTime, Course], b: tuple[CourseTime, Course]) -> int:
    """
    Compare two courses' time. If a > b, return 1, else if a < b, return -1, else return 0.
    :param a:.
    :param b:
    :return: 1, -1 or 0
    """
    time_a: CourseTime = a[0]
    time_b: CourseTime = b[0]
    if time_a > time_b:
        return 1
    elif time_a < time_b:
        return -1
    else:
        return 0


def dict_to_tuple_list(dict_: dict):
    """_summary_
    Convert a dict to a list of tuples.
    :param dict_: The dict to be converted.
    :return: A list of tuples.
    """
    return [(k, v) for k, v in dict_.items()]
