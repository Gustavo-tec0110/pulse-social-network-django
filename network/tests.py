from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Comment, Follow, Like, Post, Profile


User = get_user_model()


class SocialModelTests(TestCase):
    def test_profile_is_created_with_user(self):
        user = User.objects.create_user(username="ana", password="senha-segura")

        self.assertTrue(Profile.objects.filter(user=user).exists())

    def test_relationship_and_interactions_are_unique(self):
        ana = User.objects.create_user(username="ana")
        bia = User.objects.create_user(username="bia")
        post = Post.objects.create(author=bia, content="Primeira publicação")

        Follow.objects.get_or_create(follower=ana, following=bia)
        Follow.objects.get_or_create(follower=ana, following=bia)
        Like.objects.get_or_create(user=ana, post=post)
        Like.objects.get_or_create(user=ana, post=post)

        self.assertEqual(Follow.objects.count(), 1)
        self.assertEqual(Like.objects.count(), 1)


class SocialViewsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="gustavo", password="senha-segura", first_name="Gustavo"
        )
        self.followed = User.objects.create_user(username="ana", password="senha-segura")
        self.stranger = User.objects.create_user(username="bia", password="senha-segura")
        self.client.login(username="gustavo", password="senha-segura")

    def test_feed_contains_only_own_and_followed_posts(self):
        Follow.objects.create(follower=self.user, following=self.followed)
        own_post = Post.objects.create(author=self.user, content="Meu post")
        followed_post = Post.objects.create(author=self.followed, content="Post seguido")
        stranger_post = Post.objects.create(author=self.stranger, content="Post de fora")

        response = self.client.get(reverse("feed"))
        feed_posts = list(response.context["page_obj"].object_list)

        self.assertIn(own_post, feed_posts)
        self.assertIn(followed_post, feed_posts)
        self.assertNotIn(stranger_post, feed_posts)

    def test_user_can_create_post(self):
        response = self.client.post(reverse("create-post"), {"content": "Olá, Pulse!"})

        self.assertRedirects(response, reverse("feed"))
        self.assertTrue(Post.objects.filter(author=self.user, content="Olá, Pulse!").exists())

    def test_follow_button_toggles_relationship(self):
        url = reverse("toggle-follow", args=[self.followed.username])

        self.client.post(url)
        self.assertTrue(Follow.objects.filter(follower=self.user, following=self.followed).exists())

        self.client.post(url)
        self.assertFalse(Follow.objects.filter(follower=self.user, following=self.followed).exists())

    def test_like_button_toggles_like(self):
        post = Post.objects.create(author=self.followed, content="Conteúdo")
        url = reverse("toggle-like", args=[post.pk])

        self.client.post(url)
        self.assertTrue(Like.objects.filter(user=self.user, post=post).exists())

        self.client.post(url)
        self.assertFalse(Like.objects.filter(user=self.user, post=post).exists())

    def test_user_can_comment_on_post(self):
        post = Post.objects.create(author=self.followed, content="Conteúdo")

        response = self.client.post(
            reverse("add-comment", args=[post.pk]), {"content": "Ótima publicação!"}
        )

        self.assertRedirects(response, reverse("post-detail", args=[post.pk]))
        self.assertTrue(
            Comment.objects.filter(post=post, author=self.user, content="Ótima publicação!").exists()
        )

    def test_only_author_can_delete_post(self):
        post = Post.objects.create(author=self.followed, content="Conteúdo")

        response = self.client.post(reverse("delete-post", args=[post.pk]))

        self.assertEqual(response.status_code, 404)
        self.assertTrue(Post.objects.filter(pk=post.pk).exists())

    def test_profile_can_be_updated_without_changing_every_field(self):
        response = self.client.post(
            reverse("edit-profile"),
            {
                "first_name": "Gustavo",
                "last_name": "Lopes",
                "email": "gustavo@example.com",
                "bio": "Desenvolvedor Python",
                "location": "São Paulo",
                "website": "",
            },
        )

        self.assertRedirects(response, reverse("profile", args=[self.user.username]))
        self.user.refresh_from_db()
        self.assertEqual(self.user.profile.bio, "Desenvolvedor Python")


class PublicAccountTests(TestCase):
    def test_register_creates_authenticated_account(self):
        response = self.client.post(
            reverse("register"),
            {
                "username": "novo_usuario",
                "first_name": "Novo",
                "last_name": "Usuário",
                "email": "novo@example.com",
                "password1": "SenhaSegura2026!",
                "password2": "SenhaSegura2026!",
            },
        )

        self.assertRedirects(response, reverse("feed"))
        self.assertTrue(User.objects.filter(username="novo_usuario").exists())
        self.assertIn("_auth_user_id", self.client.session)


class SocialApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="gustavo", password="senha-segura")
        self.followed = User.objects.create_user(username="ana", password="senha-segura")
        self.stranger = User.objects.create_user(username="bia", password="senha-segura")
        self.client.force_authenticate(self.user)

    def test_authenticated_user_creates_post_with_own_author(self):
        response = self.client.post(reverse("api-post-list"), {"content": "Post pela API"})

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Post.objects.get().author, self.user)

    def test_api_feed_filters_unfollowed_users(self):
        Follow.objects.create(follower=self.user, following=self.followed)
        Post.objects.create(author=self.followed, content="Visível")
        Post.objects.create(author=self.stranger, content="Oculto")

        response = self.client.get(reverse("api-post-feed"))
        contents = [item["content"] for item in response.data["results"]]

        self.assertIn("Visível", contents)
        self.assertNotIn("Oculto", contents)

    def test_api_supports_follow_like_and_comment(self):
        post = Post.objects.create(author=self.followed, content="Conteúdo")

        follow_response = self.client.post(reverse("api-user-follow", args=["ana"]))
        like_response = self.client.post(reverse("api-post-like", args=[post.pk]))
        comment_response = self.client.post(
            reverse("api-post-comments", args=[post.pk]), {"content": "Comentário REST"}
        )

        self.assertEqual(follow_response.status_code, 200)
        self.assertEqual(like_response.status_code, 200)
        self.assertEqual(comment_response.status_code, 201)
        self.assertTrue(Follow.objects.filter(follower=self.user, following=self.followed).exists())
        self.assertTrue(Like.objects.filter(user=self.user, post=post).exists())
        self.assertTrue(Comment.objects.filter(author=self.user, post=post).exists())

    def test_public_api_registration_hashes_password(self):
        self.client.force_authenticate(user=None)

        response = self.client.post(
            reverse("api-register"),
            {
                "username": "api_user",
                "email": "api@example.com",
                "first_name": "API",
                "last_name": "User",
                "password": "SenhaSegura2026!",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.get(username="api_user").check_password("SenhaSegura2026!"))
