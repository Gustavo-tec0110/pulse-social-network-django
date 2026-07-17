from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from network.models import Comment, Follow, Like, Post


User = get_user_model()


class Command(BaseCommand):
    help = "Cria dados de demonstração para o ambiente local"

    def handle(self, *args, **options):
        people = [
            ("demo", "Demo", "Pulse", "Conta para conhecer o projeto."),
            ("ana.dev", "Ana", "Silva", "Python, APIs e café."),
            ("leo.design", "Leo", "Matos", "Design de produto e experiências digitais."),
        ]
        users = {}
        for username, first_name, last_name, bio in people:
            user, _ = User.objects.get_or_create(username=username)
            user.first_name = first_name
            user.last_name = last_name
            user.email = f"{username.replace('.', '')}@example.com"
            user.set_password("pulse-demo-2026")
            user.save()
            user.profile.bio = bio
            user.profile.save()
            users[username] = user

        Follow.objects.get_or_create(follower=users["demo"], following=users["ana.dev"])
        Follow.objects.get_or_create(follower=users["demo"], following=users["leo.design"])

        post_one, _ = Post.objects.get_or_create(
            author=users["ana.dev"],
            content="Acabei de publicar uma API com Django REST Framework. Simples, testada e pronta para crescer. ✨",
        )
        Post.objects.get_or_create(
            author=users["leo.design"],
            content="Uma boa interface não pede atenção: ela ajuda a pessoa a chegar onde precisa.",
        )
        Post.objects.get_or_create(
            author=users["demo"],
            content="Bem-vindo ao Pulse! Este é um ambiente de demonstração do projeto.",
        )
        Like.objects.get_or_create(user=users["demo"], post=post_one)
        Comment.objects.get_or_create(
            author=users["demo"], post=post_one, content="Ficou excelente!"
        )
        self.stdout.write(self.style.SUCCESS("Dados de demonstração criados."))
