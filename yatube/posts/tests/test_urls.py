from django.test import TestCase, Client
from http import HTTPStatus

from posts.models import Post, Group, User


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='test_slug',
        )
        cls.post = Post.objects.create(
            author=User.objects.create_user(username='auth'),
            text='Тестовый текст',
            group=cls.group
        )
        cls.public_url_names = {
            '/': 'posts/index.html',
            '/group/test_slug/': 'posts/group_list.html',
            '/profile/auth/': 'posts/profile.html',
            f'/posts/{cls.post.pk}/': 'posts/post_detail.html',
        }
        cls.private_url_names = {
            f'/posts/{cls.post.pk}/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html',
            '/follow/': 'posts/follow.html',
        }

    def setUp(self):
        self.guest_client = Client()

        self.user = User.objects.create_user(username='HasNoName')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

        self.auth_client_author = Client()
        self.author_user = self.post.author
        self.auth_client_author.force_login(self.author_user)

    def test_public_url_status(self):
        """Публичные страницы доступны всем пользователям."""
        for address in self.public_url_names.keys():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_private_url_redirect_anonymous_on_admin_login(self):
        """Приватные страницы перенаправят анонимного пользователя
        на страницу логина.
        """
        for address in self.private_url_names.keys():
            with self.subTest(address=address):
                response = self.guest_client.get(address, follow=True)
                self.assertRedirects(response, f'/auth/login/?next={address}')

    def test_private_url_status(self):
        """Приватные страницы доступны авторизованным пользователям."""
        for address in self.private_url_names.keys():
            with self.subTest(address=address):
                response = self.auth_client_author.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_public_urls_uses_correct_template(self):
        """Публичный URL-адрес использует соответствующий шаблон."""
        for address, template in self.public_url_names.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_private_urls_uses_correct_template(self):
        """Приватный URL-адрес использует соответствующий шаблон."""
        for address, template in self.private_url_names.items():
            with self.subTest(address=address):
                response = self.auth_client_author.get(address)
                self.assertTemplateUsed(response, template)

    def test_edit_post_url_redirect_noauthor_on_post(self):
        """Страница /posts/post.id/edit/ перенаправит не
        автора поста на страницу поста.
        """
        response = self.authorized_client.get(
            f'/posts/{self.post.pk}/edit/',
            follow=True
        )
        self.assertRedirects(response, f'/posts/{self.post.pk}/')

    def test_status_404(self):
        """Ошибка 404 если страницы не существует."""
        response = self.auth_client_author.get('/unknown/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
