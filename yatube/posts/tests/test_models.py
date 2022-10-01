from django.test import TestCase

from ..models import Post, Group, User


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

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""

        value_title_text = [
            (PostModelTest.post, PostModelTest.post.text[:15]),
            (PostModelTest.group, PostModelTest.group.title)
        ]

        for value, expected_value in value_title_text:
            with self.subTest(value=value):
                self.assertEqual(str(value), str(expected_value))

    def test_models_have_correct_verbose_name(self):
        """verbose_name в полях совпадает с ожидаемым."""

        post = PostModelTest.post

        field_verboses_name_post = {
            'text': 'Текст поста',
            'pub_date': 'Дата публикации',
            'author': 'Автор',
            'group': 'Группа',
        }

        for field, expected_value in field_verboses_name_post.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).verbose_name, expected_value
                )

    def test_models_have_correct_help_text(self):
        """help_text в полях совпадает с ожидаемым."""

        post = PostModelTest.post

        field_help_text_post = {
            'text': 'Введите текст поста',
            'group': 'Группа, к которой будет относиться пост',
        }

        for field, expected_value in field_help_text_post.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).help_text, expected_value
                )
