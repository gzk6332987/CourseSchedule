"""
这是一个Python脚本，主要用于处理课程表的生成和调度。它使用了yaml库来读取设置文件，并使用自定义的data_processing和modules模块来处理数据和生成课程表。

全局变量
SETTING_FILE: 设置文件的名称。
COURSE_TABLE: 课程表对象，初始化为None。
COURSE_HOURS: 课程时间的字典。
ALL_CLASSES: 所有班级的字典，键为班级名，值为班级对象。
ALL_TEACHERS: 所有教师的字典，键为教师名，值为教师对象。
ALL_COURSES: 所有课程的字典，键为课程名，值为课程对象。
course_name_list: 课程名列表。
course_probability: 课程概率的字典。
course_schedule_depth: 课程表深度。

函数
load(): 加载设置文件，并初始化全局变量。

主程序
在主程序中，首先调用load()函数加载设置文件。然后，根据课程时间加载课程，并生成课程表。最后，打印出调度后的班级。
"""
import yaml
from functools import cmp_to_key

import data_processing
import modules
import utils
import export

SETTING_FILE = "settings.yaml"
COURSE_TABLE: modules.CourseTable = None  # Initialize to None
COURSE_HOURS = {}

ALL_CLASSES: dict[str, modules.Class] = {}
ALL_TEACHERS: dict[str, modules.Teacher] = {}
ALL_COURSES = {}
course_name_list = []
course_probability = {}
course_schedule_depth = -1


advance_decision_courses: list[tuple[modules.CourseTime, modules.Course]] = []


def load():
    """_summary_
    A function to load the setting file and initialize the global variables.
    """
    global COURSE_TABLE, ALL_CLASSES, ALL_TEACHERS, COURSE_HOURS, course_schedule_depth

    # Write something.

    with open(SETTING_FILE, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

        course_info = data.get("courses")
        course_schedule_: dict = data.get("course_schedule")
        course_schedule_depth = len(course_schedule_)

        # Load course names and probabilities
        for course_name in course_info:
            course_name_list.append(course_name)

        for course in course_schedule_:
            for course_num, course_details in course.items():
                course_probability[course_num] = course_details.get("probability")

        # Load classes, teachers, and courses
        cls = data.get("classes")
        tea = data.get("teachers")
        cou = data.get("courses")
        elective_cou = data.get("elective_courses")

        # general courses
        for j in cou:
            for k, v in j.items():
                max_daily_courses = v.get("max_daily_courses")
                if max_daily_courses < 0:
                    raise ValueError(
                        "The max_daily_courses must be greater than or equal to 0!"
                    )
                cou_ = modules.Course(k, v.get("mode"), v.get("prohibit"))
                cou_.daily_max_courses = max_daily_courses
                ALL_COURSES[k] = cou_

        # elective courses
        elective_courses_relations_dict: dict[str, list[tuple[int, str]]] = {}
        for j in elective_cou:
            for k, v in j.items():
                max_daily_courses = v.get("max_daily_courses")
                relation_classes_num = v.get("relation_classes")
                teacher_name = v.get("teacher_name")
                for num in relation_classes_num:
                    if elective_courses_relations_dict.get(k, False):
                        elective_courses_relations_dict[k].append((num, teacher_name))
                    else:
                        elective_courses_relations_dict[k] = [(num, teacher_name)]

                if max_daily_courses < 0:
                    raise ValueError(
                        "The max_daily_courses must be greater or equal to 0!"
                    )
                cou_ = modules.Course(k, 4, v.get("prohibit"))
                cou_.daily_max_courses = max_daily_courses
                ALL_COURSES[k] = cou_

        for j in tea:
            tea_ = modules.Teacher(teacher_name := j.get("name"))
            unwilling = j.get("unwilling", None)
            if unwilling:
                tea_.add_unwilling(unwilling)
            tea_.courses.append(j.get("course")[0])
            ALL_TEACHERS[teacher_name] = tea_

        for j in cls:
            for k, v in j.items():
                _class_course_dict_str_to_str = v.get("teachers")  # course: name

            # Data preprocessing
            class_course_dict: dict[modules.Course, modules.Teacher] = {}
            if _class_course_dict_str_to_str is None:
                raise ValueError(
                    "You must fill the class course info in 'settings.yaml'"
                )
            for (
                _class_course_name,
                _class_teacher_name,
            ) in _class_course_dict_str_to_str.items():
                cur_course = ALL_COURSES[_class_course_name]
                cur_teacher = ALL_TEACHERS[_class_teacher_name]
                class_course_dict[cur_course] = cur_teacher

            cls_ = modules.Class(str(k), v.get("mode"))
            cls_.add_course(class_course_dict)
            for _course, _teacher in class_course_dict.items():
                cls_.add_teacher(_teacher, _course)
            ALL_CLASSES[cls_.class_num] = cls_

        # transform 'elective_courses_relations_dict' dict value into class obj
        elective_courses_relations: dict[modules.Course, list[modules.Class]] = {}
        for course_name, infos in elective_courses_relations_dict.items():
            for cur_class, teacher_name in infos:
                class_obj = ALL_CLASSES[str(cur_class)]
                course_obj_ = ALL_COURSES[course_name]
                class_obj.add_teacher(ALL_TEACHERS.get(teacher_name))
                if elective_courses_relations_dict.get(ALL_COURSES[course_name], False):
                    elective_courses_relations[course_obj_].append(class_obj)
                else:
                    elective_courses_relations[course_obj_] = [class_obj]

        # Load to course table
        COURSE_HOURS = data.get("course_hours")

        # Load 'advance_decision' courses
        # Then delete them from 'COURSE_HOURS'
        advance_decision_courses_from_data = data.get("advance_decision")
        # advance_decision_courses
        for course_info_dict in advance_decision_courses_from_data:
            course_info_dict: dict
            for key, value in course_info_dict.items():
                course_name = key
                target_class_str_list = value.get("target_class")
                target_class_obj_list: list[modules.Class] = []
                for target_class_str in target_class_str_list:
                    target_class_obj_list.append(ALL_CLASSES[str(target_class_str)])
                time_info = value.get("time")
                time_day = time_info.get("day")
                time_course = time_info.get("course_time")
                # Transform time_day and time_course into CourseTime obj
                time_obj = modules.CourseTime(time_day, time_course)
                # Add to advance_decision_courses
                advance_decision_courses.append(
                    (time_obj, ALL_COURSES.get(course_name))
                )
                # Minus the number from COURSE_HOURS. (Include arts and science class type)
                for course_type in COURSE_HOURS:
                    for course_name_dict in COURSE_HOURS[course_type]:
                        if course_name_dict.get(course_name, False):
                            course_name_dict[course_name] -= 1
                            if course_name_dict[course_name] < 0:
                                raise ValueError(
                                    f"The course '{course_name}' is not enough!\n"
                                    "You had better check the 'advance_decision' in 'settings.yaml'"
                                )

        COURSE_TABLE = modules.CourseTable(course_schedule_depth, course_probability)
        for j in range(1, COURSE_TABLE.course_depth + 1):
            COURSE_TABLE.append_course()
        modules.initialize(ALL_COURSES, ALL_TEACHERS, ALL_CLASSES, COURSE_TABLE)


if __name__ == "__main__":
    load()
    courses_list = []

    # Load courses based on course hours
    subjects = COURSE_HOURS.get("文科")
    for subject in subjects:
        for subject_name, course_hours in subject.items():
            course_obj = ALL_COURSES.get(subject_name)
            if course_obj is None:
                raise ValueError(f"Course '{subject_name}' not found in ALL_COURSES!")
            for _ in range(course_hours):
                courses_list.append(course_obj)

    # course schedule beginning
    course_schedule = data_processing.Schedule(
        ALL_COURSES, ALL_TEACHERS, ALL_CLASSES, COURSE_TABLE
    )

    # Replace the 'class_list' to each from 'ALL_CLASSES'
    classes_list: list[modules.Class] = []
    for class_obj in ALL_CLASSES.values():
        classes_list.append(class_obj)

    # TODO: Schedule advanced decision courses.
    course_schedule.advance_schedule(advance_decision_courses)

    # Schedule.
    after_schedule_classes = course_schedule(classes_list, courses_list)

    # Transform dict to list
    after_schedule_classes = utils.dict_to_tuple_list(after_schedule_classes)
    after_schedule_classes: list[tuple[modules.CourseTime, modules.Class]]

    # Sort the list by time.
    for _, class_obj in after_schedule_classes:
        class_obj: modules.Class
        # transform decided_courses dict to list
        class_obj.decided_courses = utils.dict_to_tuple_list(class_obj.decided_courses)

        class_obj.decided_courses.sort(key=cmp_to_key(utils.decided_courses_cmp))

    # output
    for class_num, class_obj in after_schedule_classes:
        decided_courses: dict[
            modules.CourseTime, modules.Course
        ] = class_obj.decided_courses
        print(class_num)
        for time, course in decided_courses:
            print(f"{time}: {course.name}")
        print("=" * 25)

    # Export to csv file.
    export.export_data(after_schedule_classes, "CourseScheduleOutput.csv")
