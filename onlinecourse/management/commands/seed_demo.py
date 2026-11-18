"""Create a demo course with lessons and a 5-question exam (100 points)."""
from datetime import date

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from onlinecourse.models import Choice, Course, Instructor, Lesson, Question

COURSE_NAME = "Introduction to Python"

# (lesson title, lesson content, [(question, grade, [(choice, is_correct), ...]), ...])
DEMO = [
    (
        "Getting started with Python",
        "Python is a readable, general purpose language.\n"
        "You run code with the interpreter and print output with print().",
        [
            (
                "Which function prints text to the screen in Python?",
                20,
                [("print()", True), ("echo()", False), ("console.log()", False), ("printf()", False)],
            ),
            (
                "Which of these are built-in Python data types? (select all that apply)",
                20,
                [("list", True), ("dict", True), ("tuple", True), ("pointer", False)],
            ),
        ],
    ),
    (
        "Control flow",
        "Use if/elif/else for decisions and for/while for loops.\n"
        "range(n) yields the integers 0 up to n - 1.",
        [
            (
                "What does list(range(3)) produce?",
                20,
                [("[0, 1, 2]", True), ("[1, 2, 3]", False), ("[0, 1, 2, 3]", False), ("[3]", False)],
            ),
            (
                "Which keyword starts a loop that runs while a condition is true?",
                20,
                [("while", True), ("repeat", False), ("loop", False), ("until", False)],
            ),
        ],
    ),
    (
        "Functions",
        "Define reusable blocks of code with the def keyword.\n"
        "Functions can take parameters and return values.",
        [
            (
                "Which keyword defines a function?",
                20,
                [("def", True), ("func", False), ("function", False), ("lambda only", False)],
            ),
        ],
    ),
]


class Command(BaseCommand):
    help = "Create a demo course (idempotent) so the exam flow can be tried straight away."

    @transaction.atomic
    def handle(self, *args, **options):
        if Course.objects.filter(name=COURSE_NAME).exists():
            self.stdout.write(self.style.WARNING(f'"{COURSE_NAME}" already exists - nothing to do.'))
            return

        User = get_user_model()
        teacher, _ = User.objects.get_or_create(
            username="instructor1",
            defaults={"first_name": "Ada", "last_name": "Lovelace"},
        )
        if teacher.has_usable_password():
            teacher.set_unusable_password()  # profile only, nobody logs in as this user
            teacher.save()
        instructor, _ = Instructor.objects.get_or_create(user=teacher)

        course = Course.objects.create(
            name=COURSE_NAME,
            description="A short beginner course covering Python basics, control flow and functions.",
            pub_date=date.today(),
        )
        course.instructors.add(instructor)

        for order, (title, content, questions) in enumerate(DEMO, start=1):
            lesson = Lesson.objects.create(course=course, title=title, content=content, order=order)
            for text, grade, choices in questions:
                question = Question.objects.create(lesson=lesson, question_text=text, grade=grade)
                for choice_text, is_correct in choices:
                    Choice.objects.create(question=question, choice_text=choice_text, is_correct=is_correct)

        self.stdout.write(self.style.SUCCESS(f'Created demo course "{COURSE_NAME}" (id={course.pk}).'))
