from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Choice, Course, Enrollment, Lesson, Question, Submission


class ExamFlowTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.user = User.objects.create_user("learner1", password="pass-12345", first_name="Lea")
        cls.other = User.objects.create_user("learner2", password="pass-12345")

        cls.course = Course.objects.create(name="Test course", description="d", pub_date=date.today())
        lesson = Lesson.objects.create(course=cls.course, title="L1", content="c", order=1)

        cls.q1 = Question.objects.create(lesson=lesson, question_text="Single?", grade=50)
        cls.q1_ok = Choice.objects.create(question=cls.q1, choice_text="yes", is_correct=True)
        cls.q1_bad = Choice.objects.create(question=cls.q1, choice_text="no", is_correct=False)

        cls.q2 = Question.objects.create(lesson=lesson, question_text="Multi?", grade=50)
        cls.q2_a = Choice.objects.create(question=cls.q2, choice_text="a", is_correct=True)
        cls.q2_b = Choice.objects.create(question=cls.q2, choice_text="b", is_correct=True)
        cls.q2_c = Choice.objects.create(question=cls.q2, choice_text="c", is_correct=False)

        cls.enrollment = Enrollment.objects.create(user=cls.user, course=cls.course)

    # ---- model grading ---------------------------------------------------
    def test_is_get_score_requires_exact_set(self):
        self.assertTrue(self.q2.is_get_score([self.q2_a.id, self.q2_b.id]))
        self.assertFalse(self.q2.is_get_score([self.q2_a.id]))                   # missed one
        self.assertFalse(self.q2.is_get_score([self.q2_a.id, self.q2_b.id, self.q2_c.id]))  # extra wrong
        self.assertFalse(self.q2.is_get_score([]))

    # ---- submit ----------------------------------------------------------
    def _submit(self, choice_ids):
        self.client.login(username="learner1", password="pass-12345")
        return self.client.post(reverse("onlinecourse:submit", args=(self.course.id,)), {"choice": choice_ids})

    def test_submit_creates_submission_and_redirects(self):
        response = self._submit([self.q1_ok.id, self.q2_a.id, self.q2_b.id])
        submission = Submission.objects.get()
        self.assertRedirects(
            response,
            reverse("onlinecourse:exam_result", args=(self.course.id, submission.id)),
        )
        self.assertEqual(submission.choices.count(), 3)

    def test_submit_requires_post_login_and_enrollment(self):
        url = reverse("onlinecourse:submit", args=(self.course.id,))
        self.assertEqual(self.client.post(url).status_code, 302)  # anonymous -> login
        self.client.login(username="learner1", password="pass-12345")
        self.assertEqual(self.client.get(url).status_code, 405)   # GET not allowed
        self.client.login(username="learner2", password="pass-12345")
        self.client.post(url, {"choice": [self.q1_ok.id]})
        self.assertEqual(Submission.objects.count(), 0)           # not enrolled

    # ---- result ----------------------------------------------------------
    def test_passing_result_shows_congratulations(self):
        response = self._submit([self.q1_ok.id, self.q2_a.id, self.q2_b.id], )
        response = self.client.get(response.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Congratulations")
        self.assertContains(response, "100/100")
        self.assertTrue(response.context["passed"])

    def test_failing_result_shows_retake(self):
        response = self._submit([self.q1_bad.id])
        response = self.client.get(response.url)
        self.assertNotContains(response, "Congratulations")
        self.assertContains(response, "Retake the exam")
        self.assertEqual(response.context["grade"], 0)

    def test_result_is_private_to_the_learner(self):
        submission = Submission.objects.create(enrollment=self.enrollment)
        url = reverse("onlinecourse:exam_result", args=(self.course.id, submission.id))
        self.client.login(username="learner2", password="pass-12345")
        self.assertEqual(self.client.get(url).status_code, 404)

    # ---- pages -----------------------------------------------------------
    def test_course_detail_lists_lessons_and_exam_for_enrolled_user(self):
        self.client.login(username="learner1", password="pass-12345")
        response = self.client.get(reverse("onlinecourse:course_details", args=(self.course.id,)))
        self.assertContains(response, "Test course")
        self.assertContains(response, "L1")
        self.assertContains(response, "Submit answers")

    def test_enroll_increments_total_once(self):
        self.client.login(username="learner2", password="pass-12345")
        url = reverse("onlinecourse:enroll", args=(self.course.id,))
        self.client.post(url)
        self.client.post(url)
        self.course.refresh_from_db()
        self.assertEqual(self.course.total_enrollment, 1)
