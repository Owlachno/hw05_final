from http import HTTPStatus
from django.urls import reverse
from django.test import TestCase, Client
from django.core.cache import cache

from ..models import Post, Group, User


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

        cls.public_urls_templates = {
            'posts:index': {
                'url': reverse('posts:index'),
                'template': 'posts/index.html'
            },
            'posts:group_list': {
                'url': reverse('posts:group_list', args=[cls.group.slug]),
                'template': 'posts/group_list.html'
            },
            'posts:profile': {
                'url': reverse('posts:profile', args=[cls.author.username]),
                'template': 'posts/profile.html'
            },
            'posts:post_detail': {
                'url': reverse('posts:post_detail', args=[cls.post.id]),
                'template': 'posts/post_detail.html'
            },
        }

        cls.private_urls_templates = {
            'posts:post_create': {
                'url': reverse('posts:post_create'),
                'template': 'posts/create_post.html'
            },
            'posts:post_edit': {
                'url': reverse('posts:post_edit', args=[cls.post.id]),
                'template': 'posts/create_post.html'
            }
        }

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

        for name in PostURLTests.public_urls_templates:
            with self.subTest(name=name):

                response = self.test_client.get(
                    PostURLTests.public_urls_templates[name]['url']
                )

                self.assertTemplateUsed(
                    response,
                    PostURLTests.public_urls_templates[name]['template']
                )

                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_url_exists_at_desired_location_authorized(self):
        """Страница /posts/<post_id>/edit/ доступна только автору.
        Страница /create/ доступна только авторизованному пользователю.

        URL-адрес использует соответствующий
        шаблон для приватных страниц."""

        for name in PostURLTests.private_urls_templates:
            with self.subTest(name=name):

                response = self.author_client.get(
                    PostURLTests.private_urls_templates[name]['url']
                )

                response_template = self.author_client.get(
                    PostURLTests.private_urls_templates[name]['url']
                )

                self.assertTemplateUsed(
                    response_template,
                    PostURLTests.private_urls_templates[name]['template']
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
            PostURLTests.private_urls_templates['posts:post_create']['url'],
            follow=True
        )

        self.assertRedirects(
            response, '/auth/login/?next=/create/'
        )

    def test_post_edit_url_redirect_not_author_on_detail(self):
        """Страница по адресу /'posts/<int:post_id>/edit/ перенаправляет
        не автора поста на страницу подробной информации о посте"""

        response = self.user_client.get(
            PostURLTests.private_urls_templates['posts:post_edit']['url'],
            follow=True
        )

        self.assertRedirects(
            response,
            PostURLTests.public_urls_templates['posts:post_detail']['url']
        )
