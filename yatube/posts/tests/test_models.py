from django.test import TestCase

from posts.models import Group, Post, User


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='k' * 20,
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        post = PostModelTest.post
        object_names = post.text[:15]
        self.assertEqual(object_names, str(post))

    def test_group_str(self):
        """В поле __str__  объекта task записано значение поля group.title."""
        group = PostModelTest.group
        object_name_group = group.title
        self.assertEqual(object_name_group, str(group))
