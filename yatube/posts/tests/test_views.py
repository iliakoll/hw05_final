import shutil
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse
from django import forms


from posts.models import Post, Group, User, Follow


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='test_slug',
        )
        cls.small_img = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.jpg',
            content=cls.small_img,
            content_type='image/jpg'
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый текст',
            group=cls.group,
            image=cls.uploaded
        )
        cls.templates_page_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_list', kwargs={'slug': f'{cls.group.slug}'}
            ): 'posts/group_list.html',
            reverse(
                'posts:profile', kwargs={'username': f'{cls.author.username}'}
            ): 'posts/profile.html',
            reverse(
                'posts:post_detail', kwargs={'post_id': f'{cls.post.pk}'}
            ): 'posts/post_detail.html',
            reverse(
                'posts:post_edit', kwargs={'post_id': f'{cls.post.pk}'}
            ): 'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html',
        }

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()

        self.user = User.objects.create_user(username='HasNoName')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

        self.auth_client_author = Client()
        self.author_user = self.post.author
        self.auth_client_author.force_login(self.author_user)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        for reverse_name, template in self.templates_page_names.items():
            with self.subTest(template=template):
                response = self.auth_client_author.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def check_post(self, post):
        self.assertEqual(post.text, 'Тестовый текст')
        self.assertEqual(post.author, self.author)
        self.assertEqual(post.group.title, 'Тестовый заголовок')
        self.assertEqual(post.image, self.post.image)

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        context = response.context['page_obj'][0]
        self.check_post(context)

    def test_group_list_show_correct_context(self):
        """Шаблон group_list содержит context."""
        response = self.authorized_client.get(reverse(
            'posts:group_list',
            kwargs={'slug': f'{self.group.slug}'}
        ))
        context = response.context['page_obj'][0]
        self.check_post(context)

    def test_profile_page_show_correct_context(self):
        """Шаблон profile содержит context."""
        response = self.authorized_client.get(reverse(
            'posts:profile',
            kwargs={'username': f'{self.author.username}'}
        ))
        context = response.context['page_obj'][0]
        self.check_post(context)

    def test_post_detail_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.guest_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id})
        )
        post = response.context.get('post')
        self.check_post(post)

    def test_post_create_page_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_edit_page_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.auth_client_author.get(reverse(
            'posts:post_edit',
            kwargs={'post_id': f'{self.post.id}'}
        ))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def post_show_on_template(self):
        """Пост появляется на домашней странице, странице группы и профиля."""
        for view_name in self.view_name:
            with self.subTest(value=view_name):
                if (
                    view_name == self.VIEW_POST_DETAIL
                    or view_name == self.VIEW_POST_CREATE
                    or view_name == self.VIEW_POST_EDIT
                ):
                    continue
                response = self.authorized_client.get(view_name)
                self.assertTrue(
                    self.post in response.context['page_obj'].object_list
                )


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author_2 = User.objects.create_user(username='auth2')
        cls.group_2 = Group.objects.create(
            title='Тестовый заголовок 1',
            slug='test_slug_1',
        )
        for i in range(15):
            cls.post_15 = Post.objects.create(
                author=cls.author_2,
                text=f'Тестовый текст {i}',
                group=cls.group_2
            )
        cls.list_urls = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_list',
                kwargs={'slug': f'{cls.post_15.group.slug}'}
            ): 'posts/group_list.html',
            reverse(
                'posts:profile',
                kwargs={'username': f'{cls.post_15.author.username}'}
            ): 'posts/profile.html'
        }

    def setUp(self):
        self.user_1 = User.objects.create_user(username='HasNoName_2')
        self.authoriz_client = Client()
        self.authoriz_client.force_login(self.user_1)

    def test_first_page_contains_ten_records(self):
        """Количество постов на первой странице равно 10."""
        for test_url in self.list_urls.keys():
            response = self.authoriz_client.get(test_url)
            self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_page_contains_ten_records(self):
        """Количество постов на второй странице равно 5."""
        for test_url in self.list_urls.keys():
            response = self.authoriz_client.get(test_url + '?page=2')
            self.assertEqual(len(response.context['page_obj']), 5)


class CasheViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='test_slug',
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый текст',
            group=cls.group,
        )

    def setUp(self):
        self.guest_client = Client()

        self.user = User.objects.create_user(username='HasNoName')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_cache_index(self):
        """Проверяем, кэш главной страницы."""
        new_post = self.post
        response = self.authorized_client.get(
            reverse('posts:index')
        ).content
        new_post.delete()
        response_cache = self.authorized_client.get(
            reverse('posts:index')
        ).content
        self.assertEqual(response, response_cache)
        cache.clear()
        response_not_cache = self.authorized_client.get(
            reverse('posts:index')
        ).content
        self.assertNotEqual(response, response_not_cache)


class FollowTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='author')
        cls.user = User.objects.create_user(username='follower')
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый текст',
        )
        cls.follow = Follow.objects.create(
            user=cls.user,
            author=cls.author
        )

    def setUp(self):
        self.guest_client = Client()

        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

        self.author_user = Client()
        self.author_user.force_login(self.author)

    def test_subscription(self):
        """Проверка подписки."""
        response = self.authorized_client.post(reverse(
            'posts:profile_follow',
            args={self.author}
        ))
        self.assertRedirects(response, reverse(
            'posts:profile',
            args={self.author}
        ))
        self.assertEqual(Follow.objects.count(), 1)
        self.assertTrue(
            Follow.objects.filter(
                user=self.user,
                author=self.author
            ).exists()
        )

    def test_unsubscription(self):
        """Проверка отписки."""
        response = self.authorized_client.post(reverse(
            'posts:profile_unfollow',
            args={self.author}
        ))
        self.assertRedirects(response, reverse(
            'posts:profile',
            args={self.author}
        ))
        self.assertEqual(Follow.objects.count(), 0)
        self.assertFalse(
            Follow.objects.filter(
                user=self.user,
                author=self.author
            ).exists()
        )

    def test_post_for_follower(self):
        """Новый пост появляется в ленте у подписчика."""
        response = self.authorized_client.post(reverse(
            'posts:profile_follow',
            args={self.author}
        ))
        response = self.authorized_client.post(reverse('posts:follow_index'))
        self.assertTrue(self.post in response.context['page_obj'].object_list)

    def test_post_not_for_unfollower(self):
        """Новый пост НЕ появляется в ленте у НЕ подписчика."""
        response = self.authorized_client.post(reverse(
            'posts:profile_unfollow',
            args={self.author}
        ))
        response = self.authorized_client.post(reverse('posts:follow_index'))
        self.assertFalse(self.post in response.context['page_obj'].object_list)
