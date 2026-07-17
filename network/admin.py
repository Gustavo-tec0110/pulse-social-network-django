from django.contrib import admin

from .models import Comment, Follow, Like, Post, Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "location", "created_at")
    search_fields = ("user__username", "user__first_name", "user__last_name")


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ("author", "short_content", "created_at")
    list_filter = ("created_at",)
    search_fields = ("content", "author__username")

    @admin.display(description="Conteúdo")
    def short_content(self, obj):
        return obj.content[:60]


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ("follower", "following", "created_at")
    search_fields = ("follower__username", "following__username")


@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ("user", "post", "created_at")


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("author", "post", "created_at")
    search_fields = ("content", "author__username")
