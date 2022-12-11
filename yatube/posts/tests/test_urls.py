import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from posts.models import Group, Post

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
User = get_user_model()


class StaticURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='NameSurname')
        cls.user_dif = User.objects.create_user(username='Name1Surname1')
        cls.post = Post.objects.create(
            text='Тестовый пост',
            pub_date='2022-11-30 00:00:00',
            author=User.objects.get(username='NameSurname')
        )
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='1',
            description='Какая-то тестовая группа'
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_url_opening(self):
        """Все URL-адреса открываются"""
        pages_list = {
            reverse('posts:index'): 200,
            reverse(
                'posts:group_list',
                kwargs={'slug': self.group.slug}
            ): 200,
            reverse(
                'posts:profile',
                kwargs={'username': self.post.author}
            ): 200,
            reverse(
                'posts:post_detail',
                kwargs={'post_id': 1}
            ): 200,
            '/unexisting_page/': 404
        }
        for page, answer in pages_list.items():
            with self.subTest(page=page):
                response = self.guest_client.get(page)
                self.assertEqual(response.status_code, answer)

    def test_create(self):
        """Страница создания поста открывается только авторизованнюму"""
        response = self.guest_client.get('/create/', follow=True)
        self.assertRedirects(
            response,
            reverse(
                'users:login'
            ) + '?next=' + reverse(
                'posts:post_create'
            )
        )
        response = self.authorized_client.get('/create/')
        self.assertEqual(response.status_code, 200)

    def test_post_edit(self):
        """Редактирование поста доступно только автору"""
        response = self.guest_client.get('/posts/1/edit/', follow=True)
        self.assertRedirects(
            response, '/posts/1/')
        response = self.authorized_client.get('/posts/1/edit/')
        self.assertEqual(response.status_code, 200)
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user_dif)
        response = self.authorized_client.get('/posts/1/edit/', follow=True)
        self.assertRedirects(
            response, '/posts/1/')

    def test_urls_uses_correct_template(self):
        """Проверка правильного применения шаблонов на URL-адресе."""
        templates_url_names = {
            '/': 'posts/index.html',
            '/group/1/': 'posts/group_list.html',
            '/posts/1/': 'posts/post_detail.html',
            '/profile/NameSurname/': 'posts/profile.html',
            '/create/': 'posts/create_post.html',
            '/posts/1/edit/': 'posts/create_post.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)
