"""
Created on Mon Jul 22 14:
@author: Gong Zhe Kai
"""

import copy

WEEKDAYS = [i for i in range(1, 12 + 1)]
MAP = [[None for j in range(1005)] for i in range(1005)]


class Course:
    """_summary_
    Course class.
    """

    def __init__(self, name, mode: int, prohibit: list[int] | list = None):
        self.name = name
        # 基础科目配置(其中mode=0为必修,mode=1为物理或历史,mode=2为选课,mode=3为副科, mode=4是走班(对于理科mode=1, 见classes))
        # mode=5 是特殊课程(such as 升旗), 需要手动安排课程(如单周一第一节 100% 为升旗)
        self.mode = mode
        if prohibit is not None:
            self.prohibit = prohibit
        self.teachers = []

        self.daily_max_courses: int = -1

        # elective_course var
        self.elective_relation_classes: list[Course] = []

    def add_teacher(self, teacher):
        self.teachers.append(teacher)

    def set_elective_course(self, relation_classes: list):
        # judge if the mode accord with elective courses
        if self.mode != 4:
            raise ValueError(
                f"Elective course must set 'mode' to 4! Now {self.name} mode is {self.mode}!"
            )

        if not self.elective_relation_classes:
            self.elective_relation_classes = relation_classes
        else:
            for relation_class in relation_classes:
                self.elective_relation_classes.append(relation_class)

    def __hash__(self):
        return hash(hash(self.name) + hash(self.mode))

    def __str__(self):
        return f"<Course name={self.name}>"

    def __repr__(self):
        return self.__str__()


class CourseTable(object):
    def __init__(self, course_depth: int, course_probability: dict):
        self.courses: list[Course] = []
        self.probability = []
        self.course_depth = course_depth
        self.course_probability = course_probability

        # private var
        self._now_course_num: int = 1

    def append_course(self):
        # self.courses.append(course)
        self.probability.append(self.course_probability.get(self._now_course_num))
        self._now_course_num += 1


class CourseTime(object):
    """
    用于记录课程的具体时间
    """

    def __init__(
        self,
        day: int,
        course_time: int,
        week_days: list = None,
        max_courses: int = None,
    ):
        if week_days is None:
            week_days = WEEKDAYS
        if max_courses is not None:
            max_courses = COURSE_TABLE.course_depth

        self.week_days = week_days
        self.max_courses = max_courses

        self.day = day
        self.course_time = course_time

    def __eq__(self, other) -> bool:
        if isinstance(other, CourseTime):
            return self.day == other.day and self.course_time == other.course_time
        else:
            raise TypeError(f"Unexpected type {type(other)}")

    def __le__(self, other) -> bool:
        if isinstance(other, CourseTime):
            day = self.day * 1e5
            course_time = self.course_time

            other_day = other.day * 1e5
            other_course_time = other.course_time

            all_time = day + course_time
            other_all_time = other_day + other_course_time

            return all_time <= other_all_time
        else:
            raise TypeError(f"Unexpected type {type(other)}.")

    def __gt__(self, other) -> bool:
        if isinstance(other, CourseTime):
            return not (self.__eq__(other) or self.__le__(other))
        else:
            raise TypeError(f"Unexpected type {type(other)}")

    def __str__(self):
        return f"<CourseTime day={self.day} course_time={self.course_time}>"

    def __repr__(self):
        return self.__str__()

    def __hash__(self):
        return hash((self.day, self.course_time))


class Teacher(object):
    def __init__(self, name):
        self.name = name
        self.courses = []
        self.unwilling = []

        self.busy_courses: dict[CourseTime, Course] = {}

    def add_unwilling(self, course_num: int | list[int]):
        if isinstance(course_num, int):
            self.unwilling.append(course_num)
        elif isinstance(course_num, list):
            for course in course_num:
                self.unwilling.append(course)
        else:
            raise TypeError(f"Unexpected type {type(course_num)}")

    def add_course(self, course: Course):
        self.courses.append(course)

    def cheek_busy_courses(self, current_time: CourseTime) -> bool:
        """
        cheek func `add_busy_courses()` the added courses conflict to current_time
        :param current_time: The course time to be checked for
        :return: Return True if the course is conflict with `current_time`
        """
        for course_time, _ in self.busy_courses.items():
            if course_time == current_time:
                return True
        return False

    def add_busy_course(self, course: Course, time: CourseTime):
        # cheek if arg 'time' already present in 'self.busy_courses'
        if self.cheek_busy_courses(time):
            raise ValueError("The argument: time is already in self.busy_courses!")
        # self.busy_courses.append((course, time))
        self.busy_courses[time] = course

    def __str__(self):
        return f"<teacher={self.name} courses={self.courses}>"


class Class(object):
    def __init__(self, class_num, course_mode: int):
        self.class_num = class_num
        self.course_mode = course_mode  # 0为文科, 1为理科
        self.courses = []
        self.teachers: dict[Course, Teacher] = {}

        # course schedule variables
        self.decided_courses: dict[CourseTime, Course] = {}

    def add_course(self, course):
        self.courses.append(course)

    def add_teacher(self, teacher: Teacher, the_main_course: Course = 0) -> None:
        """
        Bind the teacher to the class.
        :param teacher:
        :param the_main_course: If the teacher's course more than 1, it's required.
        :return:
        """
        global ALL_COURSES
        # Get the teacher's main course
        teacher_course = teacher.courses[0] if len(teacher.courses) == 1 else None

        if teacher_course is None:
            main_course_name = the_main_course.name
            if main_course_name not in ALL_COURSES:
                raise ValueError(
                    f"Course '{main_course_name}' must be present in ALL_COURSES!"
                )

            teacher_course = teacher.courses[ALL_COURSES[main_course_name]]

        # Set the teacher for the course
        self.teachers[teacher_course] = teacher

    def add_decided_course(
        self, decided_course: list[tuple[CourseTime, Course]],
        whether_check: bool = True
    ) -> None:
        """
        Adds a decided course to the schedule.

        Args:
            decided_course (list[tuple[CourseTime, Course]]): A list of tuples containing the course time and course.

        Raises:
            ValueError: If the decided course is empty.

        Returns:
            None
        """
        # TODO Remove this block is right?
        # if decided_course == []:
        #     raise ValueError("The decided course had not been sat!")
        for course_time, course in decided_course:
            if whether_check and self.decided_courses.get(course_time, False):
                raise ValueError(
                    f"The course time {course_time} had been decided!"
                )
            self.decided_courses[course_time] = course

    def __str__(self) -> str:
        return f"<Class num={self.class_num}>"

    def __eq__(self, other) -> bool:
        if isinstance(other, Class):
            other: Class
            return self.class_num == other.class_num


# COPY VARIABLES
ALL_COURSES: dict = {}
ALL_TEACHERS: dict = {}
ALL_CLASSES: dict = {}

COURSE_TABLE: CourseTable = None


def initialize(
    all_courses: dict, all_teachers: dict, all_classes: dict, course_table: CourseTable
):
    global ALL_COURSES, ALL_TEACHERS, ALL_CLASSES, COURSE_TABLE
    ALL_COURSES = all_courses.copy()
    ALL_TEACHERS = all_teachers.copy()
    ALL_CLASSES = all_classes.copy()
    COURSE_TABLE = copy.copy(course_table)


class JudgeRationality:
    def __init__(
        self,
        current_course: Course,
        current_course_num: int,
        teacher: Teacher,
        time: CourseTime,
        current_class: Class,

        # self arguments
        all_classes: dict[str, Class],
    ):
        self.current_course = current_course
        self.current_course_num = current_course_num
        self.teacher = teacher
        self.time = time
        self.current_class = current_class

        self.all_classes = all_classes

    def __call__(self, *args, **kwargs) -> (bool, bool):
        if not self.judge_unwilling():
            return False, False
        if self.judge_teacher_busy_time():
            return False, False
        if self.judge_daily_max_courses():
            return False, True
        return True, False

    def judge_unwilling(self) -> bool:
        """
        判断教师是否不愿意教授当前课程。

        Returns:
            bool: 如果教师不愿意教授当前课程，则返回False；否则返回True。
        """
        unwilling_period = self.teacher.unwilling
        if self.current_course_num in unwilling_period:
            return False
        return True

    def judge_class_busy_time(self):
        """
        Judge class busy course.
        Return True if this course time exists in the Class object's decided_courses,
        else False.
        """
        all_classes = self.all_classes.copy()
        this_class = all_classes[self.current_class.class_num]
        decided_courses = this_class.decided_courses
        for course_time, _ in decided_courses.items():
            if course_time == self.time:
                return True
        return False

    def judge_teacher_busy_time(self):
        """
        Judge teacher busy course.

        For example,
            A teacher is busy on Monday's second course. Then compare self.time
            to each teacher.decided_courses.
            If there is no difference, then return True.
        :return:
        """
        whether_teacher_busy = self.teacher.cheek_busy_courses(self.time)
        if whether_teacher_busy:
            return True
        else:
            return False

    def judge_daily_max_courses(self):
        """
        Judge the daily max courses.
        Returning False if the course's daily max courses is not reached, else True.
        That's all, thank you.
        """
        # Prepare some necessary variables
        cur_course = self.current_course
        decided_courses = self.current_class.decided_courses
        this_day_courses = []
        num: int = 0

        # Foreach the decided courses to find this day's courses
        for course_time, course in decided_courses.items():
            if course_time.day == self.time.day:
                this_day_courses.append(course)

        # Foreach this day's courses to find the current course
        for course in this_day_courses:
            if course == cur_course:
                num += 1

        # Judge the num whether greater than the daily max courses
        if num > cur_course.daily_max_courses:
            return True
        else:
            return False
