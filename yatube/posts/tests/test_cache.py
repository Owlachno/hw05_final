from django.urls import reverse
from django.core.cache import cache
from django.test import TestCase, Client

from ..models import Post, User


class CacheTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.author = User.objects.create_user(username='NoName')
        cls.INDEX = reverse('posts:index')

    def setUp(self):
        cache.clear()

        self.test_client = Client()

    def test_index_cache(self):
        """Тестирование кэширования страницы index."""

        post = Post.objects.create(
            text='Тест кэша.',
            author=CacheTests.author
        )

        response_before_delete = self.test_client.get(CacheTests.INDEX)

        Post.objects.filter(id=post.id).delete()

        response_after_delete = self.test_client.get(CacheTests.INDEX)

        self.assertEqual(
            response_before_delete.content,
            response_after_delete.content
        )
