# Django Online Course App

A Django app (`onlinecourse`) where learners can browse courses, enroll, read lessons and take
a graded exam. Includes the models, admin site, Bootstrap templates, views and URLs for the
exam flow (`submit` and `show_exam_result`).

## Features
- Models: `Instructor`, `Learner`, `Course`, `Lesson`, `Enrollment`, `Question`, `Choice`, `Submission`
- Admin site with inline editing (`QuestionInline`, `ChoiceInline`, `QuestionAdmin`, `LessonAdmin`, `CourseAdmin`)
- Course list and course detail pages (course name + all lessons) styled with Bootstrap 5
- Exam: tick answers, submit, get a score and a per-question breakdown (pass mark: 80)
- User registration, login and logout

## Quick start
```bash
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt

python manage.py migrate
python manage.py seed_demo        # demo course, 3 lessons, 5 questions (100 points)
python manage.py createsuperuser  # for the admin site
python manage.py runserver
```
Open http://127.0.0.1:8000/ (course list) and http://127.0.0.1:8000/admin/ (admin site).

## Try the exam
1. Go to `/onlinecourse/registration/` and create a learner account.
2. Open **Introduction to Python**, click **Enroll in this course**.
3. Tick the answers under **Exam** and click **Submit answers**.
4. The result page shows the score and the exam results. Scoring 80 or more shows **Congratulations**.

Scoring rule: a question earns its points only when the ticked answers are exactly the correct
set (every correct answer ticked, no wrong ones). Edit questions and choices in the admin site.

## Project layout
```
manage.py
myproject/                  project settings and root urls
onlinecourse/
  models.py                 Question, Choice, Submission and the rest
  admin.py                  inlines + ModelAdmin classes
  views.py                  submit, show_exam_result, extract_answers, ...
  urls.py                   paths incl. submit and exam_result
  templates/onlinecourse/
    course_details_bootstrap.html
    course_list_bootstrap.html
    exam_result_bootstrap.html
    user_login_bootstrap.html / user_registration_bootstrap.html
  management/commands/seed_demo.py
  tests.py
```

## Tests
```bash
python manage.py test
```

## Configuration
Development defaults work out of the box. For a real deployment set `DJANGO_SECRET_KEY`,
`DJANGO_DEBUG=False` and `DJANGO_ALLOWED_HOSTS` as environment variables.
