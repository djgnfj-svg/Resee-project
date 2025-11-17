from django.contrib import admin

from .models import WeeklyTest, WeeklyTestAnswer, WeeklyTestQuestion


@admin.register(WeeklyTest)
class WeeklyTestAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'start_date', 'end_date',
                    'status', 'total_questions', 'score_percentage', 'created_at']
    list_filter = ['status', 'created_at', 'start_date']
    search_fields = ['title', 'user__email']
    readonly_fields = ['total_questions', 'correct_answers', 'score_percentage', 'created_at', 'updated_at']
    ordering = ['-created_at']


class WeeklyTestQuestionInline(admin.TabularInline):
    model = WeeklyTestQuestion
    extra = 0
    readonly_fields = ['created_at']


@admin.register(WeeklyTestQuestion)
class WeeklyTestQuestionAdmin(admin.ModelAdmin):
    list_display = ['question_text_short', 'weekly_test', 'question_type', 'order', 'points']
    list_filter = ['question_type', 'weekly_test__status']
    search_fields = ['question_text', 'weekly_test__title']
    ordering = ['weekly_test', 'order']

    def question_text_short(self, obj):
        return obj.question_text[:50] + '...' if len(obj.question_text) > 50 else obj.question_text
    question_text_short.short_description = '문제'


@admin.register(WeeklyTestAnswer)
class WeeklyTestAnswerAdmin(admin.ModelAdmin):
    list_display = ['user', 'question_short', 'is_correct', 'points_earned', 'answered_at']
    list_filter = ['is_correct', 'question__question_type', 'answered_at']
    search_fields = ['user__email', 'question__question_text']
    readonly_fields = ['answered_at']
    ordering = ['-answered_at']

    def question_short(self, obj):
        return obj.question.question_text[:30] + '...' if len(obj.question.question_text) > 30 else obj.question.question_text
    question_short.short_description = '문제'
