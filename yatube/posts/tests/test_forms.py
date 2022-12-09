import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from posts.forms import PostForm
from posts.models import Comment, Follow, Group, Post

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
User = get_user_model()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='NameSurname')
        cls.user_dif = User.objects.create_user(username='Name1Surname1')
        cls.follower = User.objects.create_user(username='Follower')
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
            content_type='image/gif'
        )
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_group',
            description='Какая-то тестовая группа'
        )
        cls.post = Post.objects.create(
            text='Тестовый пост',
            author=User.objects.get(username='NameSurname'),
            group=cls.group
        )
        cls.post_follower = Post.objects.create(
            text='Тестовый пост подписчика',
            author=User.objects.get(username='Follower'),
        )
        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_follower = Client()
        self.authorized_follower.force_login(self.follower)
        self.authorized_dif = Client()
        self.authorized_dif.force_login(self.user_dif)

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        posts_count = Post.objects.all().count()
        form_data = {
            'author': self.user,
            'text': 'Тестовый пост 2',
            'group': self.group.pk,
            'image': self.uploaded,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse('posts:profile', kwargs={'username': self.post.author})
        )
        self.assertEqual(Post.objects.all().count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                author=form_data['author'],
                text=form_data['text'],
                group=self.group.pk,
                image='posts/small.gif'
            ).exists()
        )

    def test_edit_post(self):
        """Валидная форма изменяет запись в Post."""
        posts_count = Post.objects.all().count()
        form_data = {
            'text': 'Тестовый улучшенный пост',
            'group': self.post.group.pk
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse('posts:post_detail', kwargs={'post_id': self.post.id})
        )
        self.assertEqual(Post.objects.all().count(), posts_count)
        changed_post = Post.objects.get(id=self.post.id)
        self.assertEqual(changed_post.text, form_data.get('text'))

    def test_create_post_unautorized(self):
        """Если пользователь не авторизован, запись Post не создается."""
        posts_count = Post.objects.all().count()
        form_data = {
            'author': 'Name1Surname1',
            'text': 'Тестовый пост',
            'group': self.post.group.pk
        }
        response = self.guest_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse('posts:index')
        )
        self.assertEqual(Post.objects.all().count(), posts_count)

    def test_comment_post_autorized(self):
        """Коментарий создается только у авторизованного пользователя."""
        comments_count_authorized = Comment.objects.all().count()
        form_data_authorized = {
            'text': 'Тестовый комментарий',
        }
        response = self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=form_data_authorized,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse('posts:post_detail', kwargs={'post_id': self.post.id})
        )
        self.assertEqual(
            Comment.objects.count(),
            comments_count_authorized + 1
        )
        self.assertTrue(
            Comment.objects.filter(
                text=form_data_authorized['text'],
            ).exists()
        )
        comments_count_guest = Comment.objects.all().count()
        form_data_guest = {
            'text': 'Тестовый комментарий 2',
        }
        response = self.guest_client.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': self.post.id}
            ),
            data=form_data_guest,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse('users:login')
        )
        self.assertEqual(
            Comment.objects.all().count(),
            comments_count_guest,
        )
        self.assertFalse(
            Comment.objects.filter(
                text=form_data_guest['text'],
            ).exists()
        )

    def test_follow_autorized(self):
        """Подписаться может только авторизованный пользователь."""
        follow_count = Follow.objects.count()
        self.authorized_follower.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': self.user.username}
            )
        )
        follow = Follow.objects.last()
        self.assertEqual(Follow.objects.count(), follow_count + 1)
        self.assertEqual(follow.author, self.post.author)
        self.assertEqual(follow.user, self.follower)
        self.authorized_follower.get(
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': follow.author}
            )
        )
        self.assertEqual(Follow.objects.count(), follow_count)

    def test_following_posts(self):
        """Новая запись пользователя появляется в ленте тех,
        кто на него подписан."""
        self.authorized_follower.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': self.user.username}
            )
        )
        self.authorized_dif.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': self.follower.username}
            )
        )
        post_form_data = {
            'text': 'Тест подписок',
        }
        self.authorized_client.post(
            reverse('posts:post_create'),
            data=post_form_data,
            follow=True
        )
        response_0 = self.authorized_follower.get(
            reverse('posts:follow_index')
        )
        first_object = response_0.context['page_obj'][0]
        post_text_0 = first_object.text
        self.assertEqual(post_text_0, post_form_data['text'])
        response_1 = self.authorized_dif.get(
            reverse('posts:follow_index')
        )
        second_object = response_1.context['page_obj'][0]
        post_text_1 = second_object.text
        self.assertNotEqual(post_text_0, post_text_1)
