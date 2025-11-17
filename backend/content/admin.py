from django.contrib import admin

from .models import Category, Content


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'created_at')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Content)
class ContentAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'category', 'review_mode',
                    'is_ai_validated', 'ai_validation_score', 'created_at')
    list_filter = ('category', 'review_mode', 'is_ai_validated', 'created_at')
    search_fields = ('title', 'content')
    readonly_fields = ('ai_validation_score', 'ai_validation_result', 'ai_validated_at', 'created_at', 'updated_at')
