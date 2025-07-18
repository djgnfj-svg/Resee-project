from django.contrib import admin
from .models import Category, Content


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'created_at')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Content)
class ContentAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'category', 'priority', 'created_at')
    list_filter = ('category', 'priority', 'created_at')
    search_fields = ('title', 'content')