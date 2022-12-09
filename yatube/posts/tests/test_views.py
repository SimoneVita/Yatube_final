import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse
from posts.models import Group, Post

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
User = get_user_model()


class ViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='NameSurname')
        cls.user_dif = User.objects.create_user(username='Name1Surname1')
        cls.small_gif = (
             b'\x47\x49\x46\x38\x39\x61\x02\x00'
             b'\x01\x00\x80\x00\x00\x00\x00\x00'
             b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
             b'\x00\x00\x00\x2C\x00\x00\x00\x00'
             b'\x02\x00\x01\x00\x00\x02\x02\x0C'
             b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif',
        )
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_group',
            description='Какая-то тестовая группа',
        )
        cls.group_extra = Group.objects.create(
            title='Неправильная группа',
            slug='test_group_extra',
            description='Какая-то тестовая, но неправильная группа',
        )
        cls.post_extra = Post.objects.create(
            text='Неправильный тестовый пост',
            pub_date='2022-11-30 00:00:00',
            author=User.objects.get(username='Name1Surname1'),
            group=cls.group_extra,
        )
        cls.post = Post.objects.create(
            text='Тестовый пост',
            pub_date='2022-11-30 00:00:00',
            author=User.objects.get(username='NameSurname'),
            group=cls.group,
            image=cls.uploaded,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_page_use_correct_template(self):
        """URL-адреса используют корректный шаблон"""
        templates_pages = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_list',
                kwargs={'slug': self.group.slug}
            ): 'posts/group_list.html',
            reverse(
                'posts:profile',
                kwargs={'username': self.post.author}
            ): 'posts/profile.html',
            reverse(
                'posts:post_detail',
                kwargs={'post_id': 1}
            ): 'posts/post_detail.html',
            reverse(
                'posts:post_edit',
                kwargs={'post_id': 2}
            ): 'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html',
        }
        for rvs, template in templates_pages.items():
            with self.subTest(rvs=rvs):
                response = self.authorized_client.get(rvs)
                self.assertTemplateUsed(response, template)

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом, кэш работает"""
        response = self.authorized_client.get(reverse('posts:index'))
        first_object = response.context['page_obj'][0]
        post_text_0 = first_object.text
        post_pub_date_0 = first_object.pub_date
        post_author_0 = first_object.author
        post_image_0 = first_object.image
        self.assertEqual(post_text_0, self.post.text)
        self.assertEqual(post_pub_date_0, self.post.pub_date)
        self.assertEqual(post_author_0, self.post.author)
        self.assertEqual(post_image_0, self.post.image)
        cache.clear()
        post_new_extra = Post.objects.create(
            text='Тестовый пост 2',
            author=User.objects.get(username='NameSurname')
        )
        response_cache_1 = self.guest_client.get(reverse('posts:index'))
        response_cont_1 = response_cache_1.content
        Post.objects.filter(id=post_new_extra.id).delete()
        response_cache_2 = self.guest_client.get(reverse('posts:index')) 
        response_cont_2 = response_cache_2.content
        self.assertEqual(response_cont_1, response_cont_2)
        cache.clear()
        response_cache_3 = self.guest_client.get(reverse('posts:index')) 
        response_cont_3 = response_cache_3.content
        self.assertNotEqual(response_cont_1, response_cont_3)

    def test_group_posts_page_show_correct_context(self):
        """Шаблон group_posts сформирован с правильным контекстом."""
        response = self.authorized_client.get('/group/test_group/')
        first_object = response.context['group']
        post_object = response.context['page_obj'][0]
        group_name_0 = first_object.title
        group_slug_0 = first_object.slug
        group_description_0 = first_object.description
        group_image_0 = post_object.image
        self.assertEqual(group_name_0, self.group.title)
        self.assertEqual(group_slug_0, self.group.slug)
        self.assertEqual(group_description_0, self.group.description)
        self.assertEqual(group_image_0, self.post.image)

    def test_profile_page_show_correct_context(self):
        """Шаблон profile_page сформирован с правильным контекстом."""
        response = self.authorized_client.get('/profile/NameSurname/')
        first_object = response.context['page_obj'][0]
        profile_author_0 = first_object.author
        post_pub_date_0 = first_object.pub_date
        profile_num_posts_0 = response.context['posts_num']
        profile_image_0 = first_object.image
        self.assertEqual(profile_author_0, self.post.author)
        self.assertEqual(post_pub_date_0, self.post.pub_date)
        self.assertEqual(profile_num_posts_0, 1)
        self.assertEqual(profile_image_0, self.post.image)

    def test_post_detail_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get('/posts/2/')
        post_object = response.context['post']
        posts_num_0 = response.context['posts_num']
        posts_text_0 = response.context['post']
        post_image_0 = post_object.image
        self.assertEqual(posts_num_0, 1)
        self.assertEqual(f'{posts_text_0}', self.post.text)
        self.assertEqual(post_image_0, self.post.image)

    def test_post_create_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_post_edit_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.authorized_client.get('/posts/2/edit/')
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_post_is_on_index_group_and_profile(self):
        """Пост отображается на главной странице, в группе и в профайле"""
        actions = {
            reverse('posts:index'): self.post.author,
            reverse('posts:index'): self.post.text,
            reverse(
                'posts:group_list',
                kwargs={'slug': self.group.slug}
            ): self.post.author,
            reverse(
                'posts:group_list',
                kwargs={'slug': self.group.slug}
            ): self.post.text,
            reverse(
                'posts:profile',
                kwargs={'username': self.post.author}
            ): self.post.author,
            reverse(
                'posts:profile',
                kwargs={'username': self.post.author}
            ): self.post.text,
        }
        for rvs, info in actions.items():
            with self.subTest(rvs=rvs):
                response = self.authorized_client.get(rvs)
                first_object = response.context['page_obj'][0]
                author_0 = first_object.author
                text_0 = first_object.text
                if info == 'Тестовый пост':
                    self.assertEqual(text_0, info)
                else:
                    self.assertEqual(author_0, info)

    def test_post_is_not_in_incorrect_group(self):
        """Пост не попал в группу, для которой не был предназначен"""
        actions = {
            reverse(
                'posts:group_list',
                kwargs={'slug': self.group_extra.slug}
            ): self.post.author,
            reverse(
                'posts:group_list',
                kwargs={'slug': self.group_extra.slug}
            ): self.post.text,
        }
        for rvs, info in actions.items():
            with self.subTest(rvs=rvs):
                response = self.authorized_client.get(rvs)
                first_object = response.context['page_obj'][0]
                author_0 = first_object.author
                text_0 = first_object.text
                if info == 'Тестовый пост':
                    self.assertNotEqual(text_0, info)
                else:
                    self.assertNotEqual(author_0, info)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='NameSurname')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_group',
            description='Какая-то тестовая группа'
        )
        cls.post_1 = Post.objects.create(
            text='Тестовый пост',
            author=User.objects.get(username='NameSurname'),
            group=cls.group
        )
        cls.post_2 = Post.objects.create(
            text='Тестовый пост',
            author=User.objects.get(username='NameSurname'),
            group=cls.group
        )
        cls.post_3 = Post.objects.create(
            text='Тестовый пост',
            author=User.objects.get(username='NameSurname'),
            group=cls.group
        )
        cls.post_4 = Post.objects.create(
            text='Тестовый пост',
            author=User.objects.get(username='NameSurname'),
            group=cls.group
        )
        cls.post_5 = Post.objects.create(
            text='Тестовый пост',
            author=User.objects.get(username='NameSurname'),
            group=cls.group
        )
        cls.post_6 = Post.objects.create(
            text='Тестовый пост',
            author=User.objects.get(username='NameSurname'),
            group=cls.group
        )
        cls.post_7 = Post.objects.create(
            text='Тестовый пост',
            author=User.objects.get(username='NameSurname'),
            group=cls.group
        )
        cls.post_8 = Post.objects.create(
            text='Тестовый пост',
            author=User.objects.get(username='NameSurname'),
            group=cls.group
        )
        cls.post_9 = Post.objects.create(
            text='Тестовый пост',
            author=User.objects.get(username='NameSurname'),
            group=cls.group
        )
        cls.post_10 = Post.objects.create(
            text='Тестовый пост',
            author=User.objects.get(username='NameSurname'),
            group=cls.group
        )
        cls.post_11 = Post.objects.create(
            text='Тестовый пост',
            author=User.objects.get(username='NameSurname'),
            group=cls.group
        )
        cls.post_12 = Post.objects.create(
            text='Тестовый пост',
            author=User.objects.get(username='NameSurname'),
            group=cls.group
        )
        cls.post_13 = Post.objects.create(
            text='Тестовый пост',
            author=User.objects.get(username='NameSurname'),
            group=cls.group
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_paginator_first_pagepage(self):
        """Паджинация работает!"""
        paginated_pages = {
            reverse('posts:index'): 10,
            reverse('posts:index') + '?page=2': 3,
            reverse('posts:group_list', kwargs={'slug': self.group.slug}): 10,
            reverse(
                'posts:group_list', kwargs={'slug': self.group.slug}
            ) + '?page=2': 3,
            reverse('posts:profile', kwargs={'username': self.user}): 10,
            reverse(
                'posts:profile',
                kwargs={'username': self.user}
            ) + '?page=2': 3,
        }
        for rvs, posts_num in paginated_pages.items():
            with self.subTest(rvs=rvs):
                response = self.guest_client.get(rvs)
                self.assertEqual(len(response.context['page_obj']), posts_num)
