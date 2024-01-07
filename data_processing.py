"""
Data processing module
"""
import random

import utils
from modules import (
    Teacher,
    CourseTime,
    Course,
    JudgeRationality,
    Class,
    WEEKDAYS,
)


# Initialize list p
def init_p(
    probability: list[float], courses: list[Course], depth: int
) -> (list[float], list[float]):
    """
    Initialize list p
    :param probability:
    :return: probability, courses
    """
    # The first day init p list
    if depth == 1:
        this_course_probability = probability[depth]
        p_0, p_1, p_2, p_3, p_4 = (
            this_course_probability[0],
            this_course_probability[1],
            this_course_probability[2],
            this_course_probability[3],
            this_course_probability[4],
        )
        p = []

        for course in courses:
            if course.mode == 0:
                p.append(p_0)
            elif course.mode == 1:
                p.append(p_1)
            elif course.mode == 2:
                p.append(p_2)
            elif course.mode == 3:
                p.append(p_3)
            elif course.mode == 4:
                p.append(0)
            elif course.mode == 5:
                # mode=5 is special course
                p.append(0)
            else:
                raise ValueError(
                    f"Unexpected mode {course.mode}. "
                    f"其中mode=0为必修,mode=1为物理或历史,mode=2为选课,mode=3为副科, "
                    f"mode=4是走班(对于理科mode=1, 见classes)"
                )

        if len(p) != len(courses):
            raise ValueError(
                f"Unexpected length len(p)={len(courses)}, len(courses)={len(courses)}. "
            )

    # The other day init p list
    else:
        this_course_probability = probability[depth]
        p_0, p_1, p_2, p_3, p_4 = (
            this_course_probability[0],
            this_course_probability[1],
            this_course_probability[2],
            this_course_probability[3],
            this_course_probability[4],
        )
        p = []

        for course in courses:
            if course.mode == 0:
                p.append(p_0)
            elif course.mode == 1:
                p.append(p_1)
            elif course.mode == 2:
                p.append(p_2)
            elif course.mode == 3:
                p.append(p_3)
            elif course.mode == 4:
                p.append(0)
            elif course.mode == 5:
                # mode=5 is special course
                p.append(0)
            else:
                raise ValueError(
                    f"Unexpected mode {course.mode}. "
                    f"其中mode=0为必修,mode=1为物理或历史,mode=2为选课,mode=3为副科, "
                    f"mode=4是走班(对于理科mode=1, 见classes)"
                )

        if len(p) != len(courses):
            raise ValueError(
                f"Unexpected length len(p)={len(courses)}, len(courses)={len(courses)}. "
            )

    # Return
    return p, courses


class Schedule:
    """
    A class for schedule courses.
    """

    def __init__(self, all_courses, all_teachers, all_classes, course_table):
        self.ALL_COURSES = all_courses
        self.ALL_TEACHERS: dict[str, Teacher] = all_teachers  # busy state save in it!
        self.ALL_CLASSES: dict[str, Class] = all_classes
        self.COURSE_TABLE = course_table

        self.decided_courses: list[tuple[CourseTime, Course]] = []
        self.now_decided_courses: list[tuple[CourseTime, Course]] = []

        self.decay_factor: float = 0.985

    def _decay(self, probability_list: list[float]) -> list[float]:
        new_probability_list: list[float] = []
        for p in probability_list:
            new_probability_list.append(p * self.decay_factor)
        new_probability_list = utils.normalize_list(new_probability_list)
        return new_probability_list

    def _choose_from_courses(
        self,
        courses_,
        course_probability_,
        current_class,
        current_course_num,
        time: CourseTime,
    ):
        """
        :return: In sequence is the: chosen course, courses (the rest of the courses),
            course_probability, teacher,
        the probability list before set to zero
        """
        courses = courses_.copy()
        course_probability = course_probability_.copy()

        elements_with_index = list(enumerate(zip(courses, course_probability)))
        weights = [item[1][1] for item in elements_with_index]
        try:
            index, (chosen_course, _) = random.choices(
                elements_with_index, weights=weights, k=1
            )[0]
            chosen_course: Course

        except ValueError as e:
            print("weights", weights)
            print("courses", courses)
            raise ValueError("Total of weights must be greater than zero. \n" + str(e))

        teacher = current_class.teachers.get(chosen_course.name)

        # judge rationality
        judge_rationality = JudgeRationality(
            chosen_course,
            current_course_num,
            teacher,
            time,
            current_class,
            all_classes=self.ALL_CLASSES,
        )
        (judge_output, whether_set_to_zero) = judge_rationality()

        if judge_output:
            courses.pop(index)
            course_probability.pop(index)
            course_probability_.pop(index)
            return (
                chosen_course,
                courses,
                course_probability,
                teacher,
                course_probability_,
            )
        else:
            if whether_set_to_zero:
                course_probability[index] = 0
            return None, courses, course_probability, teacher, course_probability_

    def advance_schedule(
        self,
        advance_schedule: list[tuple[CourseTime, Course]],
        target_classes: list[Class] = None,
    ):
        """
        Decide on some courses in advance.
        TODO: 'target_classes' not yet enabled.
        """
        # If 'target_classes' is None, then set it to all classes.
        if target_classes is None:
            target_classes = []
            for _, each_class_obj in self.ALL_CLASSES.items():
                target_classes.append(each_class_obj)

        # For each advanced scheduled courses.
        for course_time, course in advance_schedule:
            # For each class, add advanced scheduled courses to the target classes.
            for each_class_obj in target_classes:
                each_class_obj.add_decided_course([(course_time, course)])
                
        # Set teacher busy state.
        for course_time, course in advance_schedule:
            for each_class_obj in target_classes:
                target_teacher: Teacher = each_class_obj.teachers.get(course.name)

                # XXX Beater cheek it!!
                if not target_teacher.cheek_busy_courses(course_time):
                    target_teacher.add_busy_course(course, course_time)

    def _schedule_elective_classes(
        self, target_classes: list[Class], elective_course: list[Course]
    ):
        """
        Special course (such as 走1, 走2)
        :param target_classes: The class to for schedule
        :param elective_course: 特殊课程列表
        :return:
        """
        # 走班课抽取
        # random choose course time
        chosen_time: list[CourseTime] = []
        # cyclic each course (index)
        # cyclic each course (index)
        for index, _ in enumerate(elective_course):
            while True:  # 添加这个循环
                course_obj: Course = elective_course[index]
                while True:
                    random_time = CourseTime(
                        random.randint(1, len(WEEKDAYS)),
                        random.randint(1, self.COURSE_TABLE.course_depth),
                    )
                    if random_time in chosen_time:
                        continue
                    else:
                        break

                for each_class in self.ALL_CLASSES:
                    each_class: str
                    each_class_obj: Class = self.ALL_CLASSES[each_class]
                    if each_class_obj in target_classes:
                        each_class_obj: Class

                        # Prepare arguments
                        teacher = each_class_obj.teachers[course_obj.name]

                        judge_rationality = JudgeRationality(
                            course_obj,
                            random_time.course_time,
                            teacher,
                            random_time,
                            each_class_obj,
                            all_classes=self.ALL_CLASSES,
                        )
                        whether_rationality, whether_set_to_zero = judge_rationality()

                        if not whether_rationality:  # 如果判断结果不合理
                            break  # 跳出当前循环，重新选择课程

                        # ...
                        each_class_obj.add_decided_course([(random_time, course_obj)])

                else:  # 如果所有的班级都合理，就跳出循环，继续执行后面的代码
                    break

            # set the elective course
            chosen_time.append(random_time)

    def __call__(self, target_classes: list[Class], courses_: list) -> list[Class]:
        """
        Schedule a course list for given classes
        :param target_classes:
        :param courses_:
        :return:
        """

        depth = self.COURSE_TABLE.course_depth
        probability = self.COURSE_TABLE.course_probability

        p = None
        # This list is used to save the p before set to zero.
        # When this day is end, then set the real p list to this list.
        p_before_set_to_zero: list = []

        # schedule elective course secondly.
        # - find elective course and class
        elective_courses: list[Course] = []
        for index, course in enumerate(courses_):
            if course.mode == 4:
                elective_courses.append(course)
        # - schedule elective course
        self._schedule_elective_classes(target_classes, elective_courses)

        # foreach classes
        for target_class in target_classes:
            # 'courses' need to play role in every 'target_class' foreach 'target_classes'
            courses = courses_.copy()

            # First init p list.
            if not p:
                # p, courses = init_p(probability, courses, depth)

                # Init p list on the first day of the week. (is if not p)
                p, courses = init_p(probability, courses, 1)

                # remove zero p courses
                while 0 in p:
                    for index, _ in enumerate(p):
                        if p[index] == 0:
                            p.pop(index)
                            courses.pop(index)
                            break

            # foreach work days
            vscode_stop = False
            for day in WEEKDAYS:
                for each_course_time in range(1, depth + 1):
                    # Init p list if each_course != 1
                    if each_course_time != 1:
                        p, courses = init_p(probability, courses, each_course_time)

                    if vscode_stop:
                        if not p or not courses:
                            print("所有课程均已拍完, 但一大周没有结束, 请检查课时是否符合!")
                            print("now day", day, "\n", "now course", each_course_time)
                            print("weekdays", WEEKDAYS)
                            quit(0)
                    current_time = CourseTime(day, each_course_time)

                    choose_course = None
                    choose_teacher: Teacher = None

                    # Whether skip this time
                    whether_skip_this_time = False

                    while choose_course is None:
                        # TODO Judge whether the time had been scheduled.                        
                        # Init JudgeRationality object.
                        judge_rationality = JudgeRationality(
                            None,
                            current_time.course_time,
                            None,
                            current_time,
                            target_class,
                            self.ALL_CLASSES,
                        )
                        if judge_rationality.judge_class_busy_time():
                            # If the class is busy, then skip this time.
                            whether_skip_this_time = True
                            break

                        # Choose normal course follow the p list.
                        (
                            choose_course,
                            courses,
                            p,
                            choose_teacher,
                            p_before_set_to_zero,
                        ) = self._choose_from_courses(
                            courses, p, target_class, each_course_time, current_time
                        )
                    
                    # If this time is skipped, then continue this for loop.
                    if whether_skip_this_time:
                        continue

                    # set teacher in busy state this time('current_time')
                    self.ALL_TEACHERS.get(choose_teacher.name).add_busy_course(
                        self.ALL_COURSES.get(choose_teacher.courses[0]), current_time
                    )

                    self.now_decided_courses.append((current_time, choose_course))

                    # decay the p. In order to promote the low probability course.
                    p = self._decay(p)

                    # p_before_set_to_zero = self._decay(p_before_set_to_zero)
                    for index, _ in enumerate(p):
                        if p[index] != 0:
                            p_before_set_to_zero[index] = p[index]

                    # Add to self.ALL_CLASSES
                    now_classes_obj: Class = self.ALL_CLASSES[
                        str(target_class.class_num)
                    ]
                    now_classes_obj.add_decided_course([(current_time, choose_course)])

                # add 'decided_courses' to target_class member
                target_class.add_decided_course(self.decided_courses)
                # clear self.decided_courses
                self.now_decided_courses = []
                # reset p
                p = p_before_set_to_zero

        # Add to self.decided_courses
        for course_time, course in self.now_decided_courses:
            course: Course

            # Judge error. (If this course_time already in self.decided_courses.)
            for d_course_time, d_course in self.decided_courses:
                if d_course_time == course_time:
                    raise ValueError(f"Unexpected course time {course_time}.")

            self.decided_courses.append((course_time, course))

        return self.ALL_CLASSES
