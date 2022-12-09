from django.shortcuts import get_object_or_404, redirect, render

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post, User
from .utils import pagination


def index(request):
    post_list = Post.objects.all()
    title = 'Последние обновления на сайте'
    page_obj = pagination(request, post_list)
    context = {
        'title': title,
        'text': 'Последние обновления на сайте',
        'page_obj': page_obj,
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = Post.objects.filter(group__slug=slug)
    page_obj = pagination(request, post_list)
    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    user = request.user
    author = get_object_or_404(User, username=username)
    title = f'Профайл пользователя {author}'
    posts = Post.objects.filter(author=author)
    posts_num = posts.count()
    page_obj = pagination(request, posts)
    
    context = {
        'author': author,
        'posts_num': posts_num,
        'page_obj': page_obj,
        'posts': posts,
        'title': title,
    }
    if user.is_authenticated:
        following = Follow.objects.filter(
            user=user,
            author=author
        ).exists()
        context['following'] = following
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    title = f'Пост {post.text[:30]}'
    posts_num = Post.objects.filter(author=post.author).count()
    form = CommentForm(request.POST or None)
    comments = post.comments.all()
    context = {
        'title': title,
        'form': form,
        'posts_num': posts_num,
        'post': post,
        'comments': comments,
    }
    return render(request, 'posts/post_detail.html', context)


def post_create(request):
    user = request.user
    if user.is_authenticated:
        if request.method == 'POST':
            form = PostForm(
                request.POST or None,
                files=request.FILES or None
            )
            if form.is_valid():
                v_form = form.save(commit=False)
                v_form.author = user
                v_form.save()
                return redirect(f'/profile/{user.username}/')
        form = PostForm()
        context = {
            'form': form,
            'is_edit': False,
        }
        return render(request, 'posts/create_post.html', context)
    return redirect('/')


def post_edit(request, post_id):
    user = request.user
    post = get_object_or_404(Post, pk=post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if post.author != user:
        return redirect('posts:post_detail', post_id)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            return redirect('posts:post_detail', post_id)
    context = {
        'form': form,
        'is_edit': True,
    }
    return render(request, 'posts/create_post.html', context)


def add_comment(request, post_id):
    user = request.user
    post = get_object_or_404(Post, pk=post_id) 
    if user.is_authenticated:
        form = CommentForm(request.POST or None)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.author = request.user
            comment.post = post
            comment.save()
            return redirect('posts:post_detail', post_id)
    return redirect('users:login')


def follow_index(request):
    user = request.user
    if user.is_authenticated:
        author = Post.objects.filter(author__following__user=user)
        title = 'Ваши подписки'
        page_obj = pagination(request, author) 
        context = {
            'page_obj': page_obj,
            'title': title,
        }
        return render(request, 'posts/follow.html', context)
    return redirect('users:login')


def profile_follow(request, username):
    user = request.user
    author = get_object_or_404(User, username=username)
    if user.is_authenticated:
        if author != user:
            Follow.objects.get_or_create(user=user, author=author)
            return redirect('posts:profile', username=author)
        return redirect('posts:profile', username=author)
    return redirect('users:login')
        

def profile_unfollow(request, username):
    user = request.user
    author = get_object_or_404(User, username=username)
    if user.is_authenticated:
        Follow.objects.filter(user=user, author=author).delete()
        return redirect('posts:profile', username=username)
    return redirect('users:login')
