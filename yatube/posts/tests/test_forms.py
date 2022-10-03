import shutil
import tempfile

from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile

from ..models import Post, User, Comment, Follow


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

IMAGE_VALUE = (
    b'\x47\x49\x46\x38\x39\x61\x02\x00'
    b'\x01\x00\x80\x00\x00\x00\x00\x00'
    b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
    b'\x00\x00\x00\x2C\x00\x00\x00\x00'
    b'\x02\x00\x01\x00\x00\x02\x02\x0C'
    b'\x0A\x00\x3B'
)

IMAGE_NAME = 'small.gif'


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.author = User.objects.create_user(username='author')
        cls.user1 = User.objects.create_user(username='noname1')

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.test_client = Client()
        self.test_user1 = Client()

        self.test_client.force_login(self.author)
        self.test_user1.force_login(self.user1)

        self.posts_count = Post.objects.count()

        small_gif = IMAGE_VALUE

        self.uploaded = SimpleUploadedFile(
            name=IMAGE_NAME,
            content=small_gif,
            content_type='image/gif'
        )

    def test_create_post(self):
        """Валидная форма создает запись в Post."""

        form_data = {
            'text': 'Тест формы',
            'image': self.uploaded,
        }

        response = self.test_client.post(reverse(
            'posts:post_create'),
            data=form_data,
            follow=True
        )

        latest_post = Post.objects.latest('pub_date')

        self.assertRedirects(
            response, reverse(
                'posts:profile', args=[PostCreateFormTest.author.username]
            )
        )

        self.assertEqual(Post.objects.count(), self.posts_count + 1)

        self.assertTrue(
            Post.objects.filter(
                text=form_data['text'],
                image='posts/small.gif',
                pub_date=latest_post.pub_date,
                author=PostCreateFormTest.author,
                group=None
            ).exists()
        )

    def test_post_edit(self):
        """Валидная форма редактирует пост."""

        post = Post.objects.create(
            text='Тестовый текст',
            author=PostCreateFormTest.author,
            image=self.uploaded,
        )

        posts_count = Post.objects.count()

        small_edit_gif = IMAGE_VALUE
        uploaded = SimpleUploadedFile(
            name=IMAGE_NAME,
            content=small_edit_gif,
            content_type='image/gif'
        )

        form_data = {
            'text': 'Тест редактирования',
            'image': uploaded,
        }

        response = self.test_client.post(reverse(
            'posts:post_edit', args=[post.id]),
            data=form_data,
            follow=True
        )

        self.assertRedirects(
            response, reverse(
                'posts:post_detail', args=[post.id]
            )
        )

        self.assertEqual(
            post.id, response.context['post'].id
        )

        self.assertTrue(
            Post.objects.filter(
                pk=response.context['post'].id
            ).exists()
        )

        self.assertEqual(Post.objects.count(), posts_count)

    def test_create_post_anonymous(self):
        """Анонимный пользователь не может создать пост."""

        self.test_client.logout()

        Post.objects.create(
            text='Тестовый текст',
            author=PostCreateFormTest.author,
        )

        posts_count = Post.objects.count()

        form_data = {
            'text': 'Тест анонима',
        }

        self.test_client.post(reverse(
            'posts:post_create'),
            data=form_data,
            follow=True
        )

        latest_post = Post.objects.latest('pub_date')

        self.assertNotEqual(latest_post.text, form_data['text'])

        self.assertEqual(Post.objects.count(), posts_count)

    def test_add_comment(self):
        """Валидная форма создает комментарий."""

        post_new = Post.objects.create(
            author=PostCreateFormTest.author,
            text='Тестовый текст',
        )

        comment_count = Comment.objects.count()

        form_data = {
            'text': 'Тестовый комментарий'
        }

        response = self.test_client.post(
            reverse('posts:add_comment', args=[post_new.id]),
            data=form_data,
            follow=True
        )

        self.assertRedirects(
            response,
            reverse('posts:post_detail', args=[post_new.id])
        )

        self.assertEqual(Comment.objects.count(), comment_count + 1)

        latest_comment = Comment.objects.latest('created')

        self.assertEqual(
            latest_comment, Comment.objects.get(text=form_data['text'])
        )

    def test_add_comment_anonymous(self):
        """Анонимный пользователь не может создать комментарий."""

        self.test_client.logout()

        post_new = Post.objects.create(
            author=PostCreateFormTest.author,
            text='Тестовый текст',
        )

        comment_count = Comment.objects.count()

        form_data = {
            'text': 'Тестовый комментарий'
        }

        self.test_client.post(
            reverse('posts:add_comment', args=[post_new.id]),
            data=form_data,
            follow=True
        )

        self.assertEqual(Comment.objects.count(), comment_count)

    def test_add_subscriptions(self):
        """Валидная форма создает подписку и отписку. """

        self.test_user1.post(
            reverse(
                'posts:profile_follow',
                args=[PostCreateFormTest.author.username]
            ),
        )
        self.assertTrue(
            Follow.objects.filter(
                user=PostCreateFormTest.user1,
                author=PostCreateFormTest.author,
            ).exists
        )

        self.test_user1.post(
            reverse(
                'posts:profile_unfollow',
                args=[PostCreateFormTest.author.username]
            ),
        )

        self.assertTrue(
            Follow.objects.filter(
                user=PostCreateFormTest.user1,
                author=PostCreateFormTest.author,
            ).exists
        )
