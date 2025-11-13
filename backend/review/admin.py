from django.contrib import admin

from .models import ReviewHistory, ReviewSchedule


@admin.register(ReviewSchedule)
class ReviewScheduleAdmin(admin.ModelAdmin):
    list_display = ('content', 'user', 'next_review_date', 'interval_index', 'is_active')
    list_filter = ('is_active', 'interval_index', 'next_review_date')
    search_fields = ('content__title', 'user__username')


@admin.register(ReviewHistory)
class ReviewHistoryAdmin(admin.ModelAdmin):
    list_display = ('content', 'user', 'review_date', 'result', 'time_spent')
    list_filter = ('result', 'review_date')
    search_fields = ('content__title', 'user__username')