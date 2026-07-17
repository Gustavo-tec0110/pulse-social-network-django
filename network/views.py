from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import connection
from django.db.models import Count, Q
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .forms import (
    CommentForm,
    PostForm,
    ProfileUpdateForm,
    RegisterForm,
    UserUpdateForm,
)
from .models import Follow, Like, Post


User = get_user_model()


def home(request):
    return redirect("feed" if request.user.is_authenticated else "login")


def health_check(request):
    try:
        connection.ensure_connection()
    except Exception:
        return JsonResponse({"status": "unhealthy", "database": "unavailable"}, status=503)
    return JsonResponse({"status": "healthy", "database": "connected"})


def register(request):
    if request.user.is_authenticated:
        return redirect("feed")

    form = RegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, "Sua conta foi criada. Bem-vindo ao Pulse!")
        return redirect("feed")
    return render(request, "registration/register.html", {"form": form})


def _posts_queryset():
    return (
        Post.objects.select_related("author", "author__profile")
        .prefetch_related("likes", "comments")
        .annotate(like_count=Count("likes", distinct=True), comment_count=Count("comments", distinct=True))
        .order_by("-created_at")
    )


@login_required
def feed(request):
    followed_ids = Follow.objects.filter(follower=request.user).values_list(
        "following_id", flat=True
    )
    posts = _posts_queryset().filter(Q(author=request.user) | Q(author_id__in=followed_ids))
    paginator = Paginator(posts, 10)
    page_obj = paginator.get_page(request.GET.get("page"))
    liked_post_ids = set(
        Like.objects.filter(user=request.user, post__in=page_obj.object_list).values_list(
            "post_id", flat=True
        )
    )
    return render(
        request,
        "network/feed.html",
        {
            "page_obj": page_obj,
            "post_form": PostForm(),
            "liked_post_ids": liked_post_ids,
            "page_title": "Seu feed",
        },
    )


@login_required
def explore(request):
    query = request.GET.get("q", "").strip()
    posts = _posts_queryset()
    people = User.objects.select_related("profile").exclude(pk=request.user.pk)
    if query:
        posts = posts.filter(
            Q(content__icontains=query)
            | Q(author__username__icontains=query)
            | Q(author__first_name__icontains=query)
        )
        people = people.filter(
            Q(username__icontains=query)
            | Q(first_name__icontains=query)
            | Q(last_name__icontains=query)
        )
    else:
        people = people[:6]

    paginator = Paginator(posts, 10)
    page_obj = paginator.get_page(request.GET.get("page"))
    liked_post_ids = set(
        Like.objects.filter(user=request.user, post__in=page_obj.object_list).values_list(
            "post_id", flat=True
        )
    )
    return render(
        request,
        "network/explore.html",
        {
            "page_obj": page_obj,
            "people": people,
            "query": query,
            "liked_post_ids": liked_post_ids,
        },
    )


@login_required
@require_POST
def create_post(request):
    form = PostForm(request.POST, request.FILES)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        messages.success(request, "Publicação criada.")
    else:
        messages.error(request, "Revise o texto ou a imagem da publicação.")
    return redirect("feed")


@login_required
def post_detail(request, post_id):
    post = get_object_or_404(_posts_queryset(), pk=post_id)
    liked = Like.objects.filter(user=request.user, post=post).exists()
    return render(
        request,
        "network/post_detail.html",
        {"post": post, "liked_post_ids": {post.pk} if liked else set(), "comment_form": CommentForm()},
    )


def _safe_next_url(request, fallback):
    next_url = request.POST.get("next")
    if next_url and url_has_allowed_host_and_scheme(
        next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    ):
        return next_url
    return fallback


@login_required
@require_POST
def toggle_like(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    like, created = Like.objects.get_or_create(user=request.user, post=post)
    if not created:
        like.delete()
    return redirect(_safe_next_url(request, reverse("post-detail", args=[post.pk])))


@login_required
@require_POST
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
        messages.success(request, "Comentário publicado.")
    else:
        messages.error(request, "O comentário não pôde ser publicado.")
    return redirect("post-detail", post_id=post.pk)


@login_required
def profile_detail(request, username):
    profile_user = get_object_or_404(User.objects.select_related("profile"), username=username)
    posts = _posts_queryset().filter(author=profile_user)
    page_obj = Paginator(posts, 10).get_page(request.GET.get("page"))
    liked_post_ids = set(
        Like.objects.filter(user=request.user, post__in=page_obj.object_list).values_list(
            "post_id", flat=True
        )
    )
    return render(
        request,
        "network/profile.html",
        {
            "profile_user": profile_user,
            "page_obj": page_obj,
            "liked_post_ids": liked_post_ids,
            "followers_count": profile_user.follower_links.count(),
            "following_count": profile_user.following_links.count(),
            "is_following": Follow.objects.filter(
                follower=request.user, following=profile_user
            ).exists(),
        },
    )


@login_required
@require_POST
def toggle_follow(request, username):
    target = get_object_or_404(User, username=username)
    if target == request.user:
        raise Http404
    relationship, created = Follow.objects.get_or_create(
        follower=request.user, following=target
    )
    if not created:
        relationship.delete()
    return redirect("profile", username=target.username)


@login_required
def edit_profile(request):
    user_form = UserUpdateForm(request.POST or None, instance=request.user)
    profile_form = ProfileUpdateForm(
        request.POST or None, request.FILES or None, instance=request.user.profile
    )
    if request.method == "POST" and user_form.is_valid() and profile_form.is_valid():
        user_form.save()
        profile_form.save()
        messages.success(request, "Perfil atualizado com sucesso.")
        return redirect("profile", username=request.user.username)
    return render(
        request,
        "network/edit_profile.html",
        {"user_form": user_form, "profile_form": profile_form},
    )


@login_required
@require_POST
def delete_post(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if post.author != request.user:
        raise Http404
    post.delete()
    messages.success(request, "Publicação excluída.")
    return redirect("profile", username=request.user.username)
