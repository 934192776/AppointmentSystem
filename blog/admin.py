from django.contrib import admin
from .models import Category, Post, Comment

# 注册Category
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'created_at')  # 在列表页显示这些字段
    search_fields = ('name',)  # 添加搜索功能

# 注册Post
@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'author', 'category', 'created_at')
    list_filter = ('author', 'category', 'created_at')  # 添加筛选功能
    search_fields = ('title', 'content')

# 注册Comment
@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('id', 'post', 'author', 'content', 'created_at')
    list_filter = ('created_at',)