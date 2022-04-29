import shutil
import tempfile

from django.test import Client, TestCase, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.conf import settings

from posts.forms import PostForm, CommentForm
from posts.models import Post, Group, User, Comment


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='test_slug',
        )
        cls.form = PostForm()
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
            image=cls.uploaded,
        )
        cls.URL_COMMENT = reverse(
            'posts:add_comment',
            kwargs={'post_id': f'{cls.post.id}'}
        )

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

    def test_valid_form_create_post(self):
        """Валидная форма создает запись в Post."""
        posts_count = Post.objects.count()
        form_data_post = {
            'text': self.post.text,
            'group': self.group.id,
            'image': self.post.image,

        }
        response = self.authorized_client.post(
            reverse('posts:post_create'), data=form_data_post, follow=True)
        self.assertRedirects(response, reverse('posts:profile',
                             kwargs={'username': self.user.username}))
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                group=self.group.id,
                text=self.post.text,
                image=self.post.image
            ).exists()
        )

    def test_edit_post(self):
        """Проверка формы редактирования поста"""
        post_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый текст новый',
            'group': self.group.id,
        }
        response = self.auth_client_author.post(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': f'{self.post.id}'}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse(
                'posts:post_detail',
                kwargs={'post_id': f'{self.post.id}'}
            ))
        self.assertEqual(Post.objects.count(), post_count)
        self.assertTrue(
            Post.objects.filter(
                text='Тестовый текст новый',
                group=self.group.id,
            ).exists())
        self.assertFalse(
            Post.objects.filter(
                text='Тестовый текст',
                group=self.group.id,
            ).exists())

    def test_comment_post_for_authorized_client(self):
        """Проверка добавления коммента только авторизованным пользователем."""
        form = CommentForm(data={
            'text': 'Тестовый коммент',
        })
        self.assertTrue(form.is_valid())
        comment_count = Comment.objects.count()
        response = self.guest_client.post(
            self.URL_COMMENT,
            data=form.data,
            follow=True
        )
        self.assertEqual(Comment.objects.count(), comment_count)
        response = self.authorized_client.post(
            self.URL_COMMENT,
            data=form.data,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse(
                'posts:post_detail',
                kwargs={'post_id': f'{self.post.id}'}
            ))
        self.assertEqual(Comment.objects.count(), comment_count + 1)
        self.assertEqual(self.post.comments.last().text, form.data['text'])
