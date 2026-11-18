import logging

from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import F
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views import generic
from django.views.decorators.http import require_POST

from .models import Choice, Course, Enrollment, Question, Submission

logger = logging.getLogger(__name__)

# Minimum percentage needed to pass the exam.
PASS_MARK = 80


def check_if_enrolled(user, course):
    if user is not None and user.is_authenticated:
        return Enrollment.objects.filter(user=user, course=course).exists()
    return False


# --------------------------------------------------------------------------- #
# Authentication
# --------------------------------------------------------------------------- #
def registration_request(request):
    context = {}
    if request.method == "GET":
        return render(request, "onlinecourse/user_registration_bootstrap.html", context)

    User = get_user_model()
    username = request.POST.get("username", "").strip()
    password = request.POST.get("password", "")
    first_name = request.POST.get("first_name", "").strip()
    last_name = request.POST.get("last_name", "").strip()

    if not username or not password:
        context["message"] = "Username and password are required."
        return render(request, "onlinecourse/user_registration_bootstrap.html", context)
    if User.objects.filter(username=username).exists():
        context["message"] = "User already exists."
        return render(request, "onlinecourse/user_registration_bootstrap.html", context)

    user = User.objects.create_user(
        username=username,
        first_name=first_name,
        last_name=last_name,
        password=password,
    )
    login(request, user)
    return redirect("onlinecourse:index")


def login_request(request):
    context = {}
    if request.method == "POST":
        user = authenticate(
            request,
            username=request.POST.get("username", ""),
            password=request.POST.get("password", ""),
        )
        if user is not None:
            login(request, user)
            return redirect(request.POST.get("next") or "onlinecourse:index")
        context["message"] = "Invalid username or password."
    context["next"] = request.GET.get("next", "")
    return render(request, "onlinecourse/user_login_bootstrap.html", context)


def logout_request(request):
    logout(request)
    return redirect("onlinecourse:index")


# --------------------------------------------------------------------------- #
# Course list / detail / enroll
# --------------------------------------------------------------------------- #
class CourseListView(generic.ListView):
    template_name = "onlinecourse/course_list_bootstrap.html"
    context_object_name = "course_list"

    def get_queryset(self):
        courses = list(Course.objects.order_by("-total_enrollment", "name")[:10])
        user = self.request.user
        if user.is_authenticated:
            enrolled_ids = set(
                Enrollment.objects.filter(user=user).values_list("course_id", flat=True)
            )
            for course in courses:
                course.is_enrolled = course.id in enrolled_ids
        return courses


class CourseDetailView(generic.DetailView):
    model = Course
    template_name = "onlinecourse/course_details_bootstrap.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        course = self.object
        course.is_enrolled = check_if_enrolled(self.request.user, course)
        context["lessons"] = course.lesson_set.all()
        context["questions"] = (
            Question.objects.filter(lesson__course=course)
            .select_related("lesson")
            .prefetch_related("choice_set")
            .order_by("lesson__order", "lesson__id", "id")
        )
        return context


@login_required
@require_POST
def enroll(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    _, created = Enrollment.objects.get_or_create(
        user=request.user, course=course, defaults={"mode": Enrollment.HONOR}
    )
    if created:
        Course.objects.filter(pk=course.pk).update(total_enrollment=F("total_enrollment") + 1)
    return HttpResponseRedirect(reverse("onlinecourse:course_details", args=(course.id,)))


# --------------------------------------------------------------------------- #
# Exam: submit + result
# --------------------------------------------------------------------------- #
def extract_answers(request):
    """Return the list of choice ids ticked on the exam form."""
    submitted_answers = []
    for value in request.POST.getlist("choice"):
        try:
            submitted_answers.append(int(value))
        except (TypeError, ValueError):
            logger.warning("Ignoring invalid choice value %r", value)
    return submitted_answers


@login_required
@require_POST
def submit(request, course_id):
    """
    Save the learner's answers as a Submission for their Enrollment, then
    redirect to the result page.
    """
    course = get_object_or_404(Course, pk=course_id)
    enrollment = Enrollment.objects.filter(user=request.user, course=course).first()
    if enrollment is None:
        # Only enrolled learners can take the exam.
        return HttpResponseRedirect(reverse("onlinecourse:course_details", args=(course.id,)))

    submission = Submission.objects.create(enrollment=enrollment)
    chosen = Choice.objects.filter(
        pk__in=extract_answers(request), question__lesson__course=course
    )
    submission.choices.set(chosen)
    return HttpResponseRedirect(
        reverse("onlinecourse:exam_result", args=(course.id, submission.id))
    )


@login_required
def show_exam_result(request, course_id, submission_id):
    """Grade a submission and show the score with a per-question breakdown."""
    course = get_object_or_404(Course, pk=course_id)
    submission = get_object_or_404(
        Submission,
        pk=submission_id,
        enrollment__course=course,
        enrollment__user=request.user,
    )
    selected_ids = set(submission.choices.values_list("id", flat=True))

    questions = (
        Question.objects.filter(lesson__course=course)
        .prefetch_related("choice_set")
        .order_by("lesson__order", "lesson__id", "id")
    )

    total_possible = 0
    total_score = 0
    results = []
    for question in questions:
        got_it = question.is_get_score(selected_ids)
        total_possible += question.grade
        if got_it:
            total_score += question.grade
        results.append(
            {
                "question": question,
                "is_correct": got_it,
                "choices": [
                    {
                        "text": choice.choice_text,
                        "selected": choice.id in selected_ids,
                        "is_correct": choice.is_correct,
                    }
                    for choice in question.choice_set.all()
                ],
            }
        )

    grade = round(total_score / total_possible * 100) if total_possible else 0
    context = {
        "course": course,
        "submission": submission,
        "results": results,
        "score": total_score,
        "total": total_possible,
        "grade": grade,
        "pass_mark": PASS_MARK,
        "passed": grade >= PASS_MARK,
    }
    return render(request, "onlinecourse/exam_result_bootstrap.html", context)
