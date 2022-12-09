import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        post = PostModelTest.post
        expected_object_name = post.text[:15]
        self.assertEqual(expected_object_name, str(post))
        group = PostModelTest.group
        expected_object_name = group.title
        self.assertEqual(expected_object_name, str(group))

    def test_models_have_correct_verbose_name(self):
        """Проверяем, что у моделей корректное verbose_name"""
        verbose_names = {
            'text': 'Текст поста',
            'pub_date': 'Дата публикации',
            'group': 'Группа',
            'author': 'Автор'
        }
        for vn, name in verbose_names.items():
            with self.subTest(vn=vn):
                response = self.post._meta.get_field(vn).verbose_name
                self.assertEqual(response, name)

    def test_models_have_correct_help_text(self):
        """Проверяем, что у моделей корректный help_text"""
        help_text = {
            'text': 'Введите текст поста',
            'group': 'Группа, в которой размещен пост'
        }
        for ht, text in help_text.items():
            with self.subTest(ht=ht):
                response = self.post._meta.get_field(ht).help_text
                self.assertEqual(response, text)
