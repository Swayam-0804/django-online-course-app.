from django.contrib import admin

from .models import Choice, Course, Instructor, Learner, Lesson, Question, Submission


class LessonInline(admin.StackedInline):
    model = Lesson
    extra = 5


class QuestionInline(admin.StackedInline):
    model = Question
    extra = 2


class ChoiceInline(admin.StackedInline):
    model = Choice
    extra = 4


class QuestionAdmin(admin.ModelAdmin):
    inlines = [ChoiceInline]
    list_display = ["question_text", "lesson", "grade"]


class LessonAdmin(admin.ModelAdmin):
    inlines = [QuestionInline]
    list_display = ["title", "course", "order"]


class CourseAdmin(admin.ModelAdmin):
    inlines = [LessonInline]
    list_display = ["name", "pub_date", "total_enrollment"]
    list_filter = ["pub_date"]
    search_fields = ["name", "description"]


admin.site.register(Course, CourseAdmin)
admin.site.register(Lesson, LessonAdmin)
admin.site.register(Instructor)
admin.site.register(Learner)
admin.site.register(Question, QuestionAdmin)
admin.site.register(Choice)
admin.site.register(Submission)
