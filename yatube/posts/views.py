from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_page

from .forms import PostForm, CommentForm
from .models import Post, Group, User, Follow
from .utils import get_page


@cache_page(20, key_prefix='index_page')
def index(request):

    page_obj = get_page(Post.objects.all(), request)

    context = {
        'page_obj': page_obj,
    }

    return render(request, 'posts/index.html', context)


def group_posts(request, slug):

    group = get_object_or_404(Group, slug=slug)

    posts = group.posts.all()

    page_obj = get_page(posts, request)

    context = {
        'group': group,
        'page_obj': page_obj,
    }

    return render(request, 'posts/group_list.html', context)


def profile(request, username):

    author = get_object_or_404(User, username=username)

    posts_list = author.posts.all()
    posts_count = posts_list.count()

    page_obj = get_page(posts_list, request)

    print(author)
    print(1)
    print(request.user)

    following = True

    if request.user.is_authenticated:
        if Follow.objects.filter(
            user=request.user, author=author
        ).exists():
            following = True
        else:
            following = False

    context = {
        'author': author,
        'page_obj': page_obj,
        'username': username,
        'posts_count': posts_count,
        'following': following
    }

    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):

    post = Post.objects.get(pk=post_id)

    username = post.author.get_username()
    author = get_object_or_404(User, username=username)

    posts_list = author.posts.all()
    posts_count = posts_list.count()

    form = CommentForm(request.POST or None)
    comments = post.comments.all()

    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.save()
        return redirect('posts:post_detail', post_id=post_id)

    context = {
        'posts_count': posts_count,
        'post': post,
        'form': form,
        'comments': comments,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
    )

    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:profile', request.user.username)

    context = {
        'form': form,
        'is_edit': True
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)

    if post.author != request.user:
        return redirect('posts:post_detail', post.pk)

    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )

    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post.pk)

    context = {
        'form': form,
        'post': post,
        'is_edit': False
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)

    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):

    following_list = Follow.objects.filter(user=request.user)
    following_username = []

    for obj in following_list:
        following_username.append(obj.author)

    posts_list = Post.objects.filter(author__in=following_username)

    page_obj = get_page(posts_list, request)

    for post in page_obj:
        print(post)

    context = {
        'page_obj': page_obj,
    }

    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):

    follow_author = get_object_or_404(User, username=username)

    if request.user != follow_author:
        Follow.objects.get_or_create(user=request.user, author=follow_author)

    return redirect("posts:profile", username=username)


@login_required
def profile_unfollow(request, username):

    unfollow_author = get_object_or_404(User, username=username)

    Follow.objects.filter(user=request.user, author=unfollow_author).delete()

    return redirect("posts:profile", username=username)
