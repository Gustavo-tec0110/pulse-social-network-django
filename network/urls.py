from django.urls import path

from . import views


urlpatterns = [
    path("cadastro/", views.register, name="register"),
    path("feed/", views.feed, name="feed"),
    path("explorar/", views.explore, name="explore"),
    path("publicar/", views.create_post, name="create-post"),
    path("post/<int:post_id>/", views.post_detail, name="post-detail"),
    path("post/<int:post_id>/curtir/", views.toggle_like, name="toggle-like"),
    path("post/<int:post_id>/comentar/", views.add_comment, name="add-comment"),
    path("post/<int:post_id>/excluir/", views.delete_post, name="delete-post"),
    path("perfil/editar/", views.edit_profile, name="edit-profile"),
    path("perfil/<str:username>/", views.profile_detail, name="profile"),
    path("perfil/<str:username>/seguir/", views.toggle_follow, name="toggle-follow"),
]
