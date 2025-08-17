from django.contrib import admin

from .models import AIEvaluation, AIQuestion, AIQuestionType, AIReviewSession


@admin.register(AIQuestionType)
class AIQuestionTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'display_name', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'display_name']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(AIQuestion)
class AIQuestionAdmin(admin.ModelAdmin):
    list_display = ['content', 'question_type', 'difficulty', 'is_active', 'created_at']
    list_filter = ['question_type', 'difficulty', 'is_active', 'created_at']
    search_fields = ['content__title', 'question_text', 'keywords']
    readonly_fields = ['created_at', 'updated_at']
    raw_id_fields = ['content']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('content', 'question_type', 'difficulty', 'is_active')
        }),
        ('Question Content', {
            'fields': ('question_text', 'correct_answer', 'options', 'explanation')
        }),
        ('Metadata', {
            'fields': ('keywords', 'ai_model_used', 'generation_prompt'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(AIEvaluation)
class AIEvaluationAdmin(admin.ModelAdmin):
    list_display = ['user', 'question_preview', 'ai_score', 'similarity_score', 'created_at']
    list_filter = ['ai_score', 'created_at', 'ai_model_used']
    search_fields = ['user__email', 'question__question_text', 'user_answer']
    readonly_fields = ['created_at']
    raw_id_fields = ['question', 'user']
    
    def question_preview(self, obj):
        return obj.question.question_text[:50] + "..." if len(obj.question.question_text) > 50 else obj.question.question_text
    question_preview.short_description = 'Question'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('question', 'user', 'created_at')
        }),
        ('Answer & Evaluation', {
            'fields': ('user_answer', 'ai_score', 'similarity_score', 'feedback')
        }),
        ('Technical Details', {
            'fields': ('evaluation_details', 'ai_model_used', 'processing_time_ms'),
            'classes': ('collapse',)
        }),
    )


@admin.register(AIReviewSession)
class AIReviewSessionAdmin(admin.ModelAdmin):
    list_display = ['user_email', 'content_title', 'session_type', 'questions_answered', 'average_score', 'created_at']
    list_filter = ['session_type', 'created_at']
    search_fields = ['review_history__user__email', 'review_history__content__title']
    readonly_fields = ['created_at', 'updated_at', 'completion_percentage']
    raw_id_fields = ['review_history']
    
    def user_email(self, obj):
        return obj.review_history.user.email
    user_email.short_description = 'User'
    
    def content_title(self, obj):
        return obj.review_history.content.title
    content_title.short_description = 'Content'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('review_history', 'session_type', 'created_at', 'updated_at')
        }),
        ('Session Stats', {
            'fields': ('questions_generated', 'questions_answered', 'completion_percentage', 'average_score')
        }),
        ('Performance Metrics', {
            'fields': ('session_duration_seconds', 'ai_processing_time_ms'),
            'classes': ('collapse',)
        }),
        ('Notes', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
    )
