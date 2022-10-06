import shutil
import tempfile

from django import forms
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache

from ..models import Post, Group, User


KEY_PAGE_OBJ = 'page_obj'
KEY_POST = 'post'
KEY_FORM = 'form'

INDEX_URL = 'posts:index'
GROUP_URL = 'posts:group_list'
PROFILE_URL = 'posts:profile'
POST_DETAIL_URL = 'posts:post_detail'
POST_CREATE_URL = 'posts:post_create'
POST_EDIT_URL = 'posts:post_edit'
FOLLOW_INDEX = 'posts:follow_index'

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
class PostViewsTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.author = User.objects.create_user(username='author')
        cls.user = User.objects.create_user(username='NoName')
        cls.follower = User.objects.create_user(username='follower')

        cls.group1 = Group.objects.create(
            title='Тестовый заголовок1',
            slug='test-slug1',
            description='Тестовое описание1'
        )

        cls.group2 = Group.objects.create(
            title='Тестовый заголовок2',
            slug='test-slug2',
            description='Тестовое описание2'
        )

        cls.groups_list = list(Group.objects.all())

        for i in range(1, 14):
            Post.objects.create(
                text=f'Текст номер {i}',
                author=cls.author,
                group=cls.group1
            )

        cls.posts_list = list(Post.objects.all())

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):

        cache.clear()

        self.test_client = Client()
        self.author_client = Client()
        self.follower_client = Client()

        self.test_client.force_login(PostViewsTests.author)

    def test_context_contains_key(self):
        """Словарь context содержит необходимый ключ"""

        group1 = PostViewsTests.groups_list[0].slug
        author_client = PostViewsTests.author.username
        post1 = PostViewsTests.posts_list[12].id

        urls_keys_list = [
            (
                reverse(INDEX_URL),
                KEY_PAGE_OBJ,
            ),
            (
                reverse(
                    GROUP_URL, args=[group1]
                ),
                KEY_PAGE_OBJ,
            ),
            (
                reverse(PROFILE_URL, args=[author_client]),
                KEY_PAGE_OBJ,
            ),
            (
                reverse(POST_DETAIL_URL, args=[post1]),
                KEY_POST,
            ),
            (
                reverse(POST_DETAIL_URL, args=[post1]),
                KEY_FORM,
            ),
            (
                reverse(POST_CREATE_URL),
                KEY_FORM,
            ),
            (
                reverse(POST_EDIT_URL, args=[post1]),
                KEY_FORM,
            ),
            (
                reverse(FOLLOW_INDEX),
                KEY_PAGE_OBJ,
            )
        ]

        for url, key in urls_keys_list:
            with self.subTest(url=url):

                response = self.test_client.get(url)

                self.assertIn(
                    key,
                    response.context.keys()
                )

    def test_correct_context(self):
        """Шаблоны index group_list profile
        сформированы с правильным контекстом."""

        group1 = PostViewsTests.groups_list[0].slug
        author_client = PostViewsTests.author.username

        post_list = Post.objects.all()

        amount_posts = 0
        paginate_by = 10

        address_list = [
            reverse(INDEX_URL),
            reverse(GROUP_URL, args=[group1]),
            reverse(PROFILE_URL, args=[author_client]),
        ]

        for address in address_list:

            for page in range(1, 3):

                post_page = post_list[amount_posts:amount_posts + paginate_by]

                response_page = self.test_client.get(
                    address,
                    {'page': page}
                )

                page = response_page.context.get(KEY_PAGE_OBJ).object_list

                for expected_post in post_page:
                    with self.subTest(expected_post=expected_post):
                        self.assertIn(expected_post, page)

                amount_posts += 10

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail для поста с pk=1
        сформирован с правильным контекстом."""

        post1 = PostViewsTests.posts_list[12].pk

        response = self.test_client.get(
            reverse(POST_DETAIL_URL, args=[post1])
        )

        post_object = response.context[KEY_POST]

        self.assertEqual(post_object, Post.objects.get(pk=1))

    def test_post_create_page_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""

        response = self.test_client.get(
            reverse(POST_CREATE_URL)
        )

        form_fields = [
            ('text', forms.fields.CharField),
            ('group', forms.fields.ChoiceField),
        ]

        for value, expected in form_fields:
            with self.subTest(value=value):
                form_field = response.context.get(KEY_FORM).fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_edit_page_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""

        post1 = Post.objects.latest('-pub_date')

        response = self.test_client.get(
            reverse(POST_EDIT_URL, args=[post1.pk])
        )

        form_fields = [
            ('text', forms.fields.CharField),
            ('group', forms.fields.ChoiceField),
        ]

        for value, expected in form_fields:
            with self.subTest(value=value):
                form_field = response.context.get(KEY_FORM).fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_correct_show_of_post(self):
        """Проверка: post13 отображается на главной странице, в group1,
        в профиле автора, post13 не отображается в group2,
        в профиле другого пользователя."""

        group1 = PostViewsTests.groups_list[0].slug
        group2 = PostViewsTests.groups_list[1].slug
        author_client = PostViewsTests.author.username
        user_client = PostViewsTests.user.username

        post13 = Post.objects.get(pk=13)

        response_value = [
            (reverse(INDEX_URL), True),
            (reverse(GROUP_URL, args=[group1]), True),
            (reverse(PROFILE_URL, args=[author_client]), True),
            (reverse(GROUP_URL, args=[group2]), False),
            (reverse(PROFILE_URL, args=[user_client]), False),
        ]

        for address, value in response_value:
            with self.subTest(address=address):
                response = self.test_client.get(address)
                page = response.context.get(KEY_PAGE_OBJ).object_list
                self.assertEqual(post13 in page, value)

    def test_page_contains_ten_records(self):
        """Проверка пагинатора index group_list profile"""

        group1 = PostViewsTests.groups_list[0].slug
        author_client = PostViewsTests.author.username

        posts_per_pages_total = [
            (1, 10),
            (2, 3)
        ]

        reverse_name = [
            reverse(INDEX_URL),
            reverse(GROUP_URL, args=[group1]),
            reverse(PROFILE_URL, args=[author_client]),
        ]

        for page, posts in posts_per_pages_total:
            for address in reverse_name:
                with self.subTest(address=address):
                    response = self.test_client.get(
                        address, {'page': page}
                    )
                    self.assertEqual(
                        len(
                            response.context[KEY_PAGE_OBJ]
                        ), posts
                    )

    def test_image_context_correct(self):
        """Context содержит изображение для страниц
        index  group_list  profile  post_detail"""

        small_gif = IMAGE_VALUE
        self.uploaded = SimpleUploadedFile(
            name=IMAGE_NAME,
            content=small_gif,
            content_type='image/gif'
        )

        uploaded = SimpleUploadedFile(
            name=IMAGE_NAME,
            content=small_gif,
            content_type='image/gif'
        )

        post_new = Post.objects.create(
            author=PostViewsTests.author,
            text='Тест редактирования',
            group=PostViewsTests.group1,
            image=uploaded,
        )

        url_value_list = [
            (
                self.test_client.get(
                    reverse(
                        POST_DETAIL_URL,
                        args=[post_new.id]
                    )
                ).context[KEY_POST].image, post_new.image
            ),
            (
                self.test_client.get(
                    reverse(INDEX_URL)
                ).context[KEY_PAGE_OBJ][0].image, post_new.image
            ),
            (
                self.test_client.get(
                    reverse(
                        GROUP_URL,
                        args=[PostViewsTests.group1.slug]
                    )
                ).context[KEY_PAGE_OBJ][0].image, post_new.image
            ),
            (
                self.test_client.get(
                    reverse(
                        PROFILE_URL,
                        args=[PostViewsTests.author.username]
                    )
                ).context[KEY_PAGE_OBJ][0].image, post_new.image
            )
        ]

        for expected, value in url_value_list:
            with self.subTest(expected=expected):
                self.assertEqual(expected, value)

    def test_correct_subscription_feed(self):
        """Новый пост автора отображается в ленте подписчика,
        но не отображается в ленте другого пользователя."""

        self.author_client.force_login(PostViewsTests.author)
        self.test_client.force_login(PostViewsTests.user)
        self.follower_client.force_login(PostViewsTests.follower)

        self.follower_client.post(
            reverse(
                'posts:profile_follow',
                args=[PostViewsTests.author.username]
            ),
        )

        post_new = Post.objects.create(
            author=PostViewsTests.author,
            text='Тест ленты',
        )

        response_page_follower = self.follower_client.get(
            reverse(FOLLOW_INDEX)
        )
        page_follower = response_page_follower.context.get(
            KEY_PAGE_OBJ
        ).object_list

        self.assertIn(post_new, page_follower)

        response_page_user = self.test_client.get(
            reverse(FOLLOW_INDEX)
        )
        page_user = response_page_user.context.get(
            KEY_PAGE_OBJ
        ).object_list

        self.assertNotIn(post_new, page_user)
