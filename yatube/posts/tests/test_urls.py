from http import HTTPStatus

from django.urls import reverse
from django.test import TestCase, Client
from django.core.cache import cache

from ..models import Post, Group, User


INDEX_URL = 'posts:index'
GROUP_URL = 'posts:group_list'
PROFILE_URL = 'posts:profile'
POST_DETAIL_URL = 'posts:post_detail'
POST_CREATE_URL = 'posts:post_create'
POST_EDIT_URL = 'posts:post_edit'
FOLLOW_INDEX = 'posts:follow_index'


class PostURLTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.author = User.objects.create_user(username='author')
        cls.user = User.objects.create_user(username='NoName')

        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='test-slug',
            description='Тестовое описание',
        )

        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.author,
            group=cls.group
        )

        cls.public_urls_temp_list = [
            (
                reverse(INDEX_URL),
                'posts/index.html',
            ),
            (
                reverse(GROUP_URL, args=[cls.group.slug]),
                'posts/group_list.html',
            ),
            (
                reverse(PROFILE_URL, args=[cls.author.username]),
                'posts/profile.html',
            ),
            (
                reverse(POST_DETAIL_URL, args=[cls.post.id]),
                'posts/post_detail.html',
            )
        ]

        cls.private_urls_temp_list = [
            (
                reverse(POST_CREATE_URL),
                'posts/create_post.html',
            ),
            (
                reverse(POST_EDIT_URL, args=[cls.post.id]),
                'posts/create_post.html',
            ),
            (
                reverse(FOLLOW_INDEX),
                'posts/follow.html',
            )
        ]

    def setUp(self):
        cache.clear()

        self.test_client = Client()
        self.author_client = Client()
        self.user_client = Client()

        self.author_client.force_login(self.author)
        self.user_client.force_login(self.user)

    def test_url_exists_at_desired_location(self):
        """Страницы по адресам /  /group/<slug>/  /profile/<username>/
        /posts/<post_id>/ доступны любому пользователю.

        URL-адрес использует соответствующий
        шаблон для публичных страниц."""

        for url, template in PostURLTests.public_urls_temp_list:
            with self.subTest(url=url):
                response = self.test_client.get(url)

                self.assertTemplateUsed(
                    response,
                    template
                )

                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_url_exists_at_desired_location_authorized(self):
        """Страница /posts/<post_id>/edit/ доступна только автору.
        Страница /create/ доступна только авторизованному пользователю.

        URL-адрес использует соответствующий
        шаблон для приватных страниц."""

        for url, template in PostURLTests.private_urls_temp_list:
            with self.subTest(url=url):
                response = self.author_client.get(url)

                self.assertTemplateUsed(
                    response,
                    template
                )

                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_unexistings_page_error(self):
        """Запрос к несуществующей странице
        возвращает ошибку любому пользователю."""

        response = self.test_client.get(
            '/does-not-exist/'
        )

        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_create_url_redirect_anonymous_on_admin_login(self):
        """Страница по адресу /create/ перенаправляет
        анонимного пользователя на страницу логина."""

        response = self.test_client.get(
            reverse(POST_CREATE_URL)
        )

        self.assertRedirects(
            response, '/auth/login/?next=/create/'
        )

    def test_post_edit_url_redirect_not_author_on_detail(self):
        """Страница по адресу /'posts/<int:post_id>/edit/ перенаправляет
        не автора поста на страницу подробной информации о посте"""

        response = self.user_client.get(
            reverse(POST_EDIT_URL, args=[PostURLTests.post.id]),
            follow=True
        )

        self.assertRedirects(
            response,
            reverse(POST_DETAIL_URL, args=[PostURLTests.post.id])
        )
