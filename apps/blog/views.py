from django.shortcuts import render, redirect, get_object_or_404
from django.views import View

from django.views.generic import TemplateView
from django.views.generic.list import ListView

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import logout, login, authenticate
from django.contrib import messages

from django.core.paginator import Paginator

from .forms import RegisterForm, LoginForm, PostUpdateForm, PostCreateForm
from .models import Post

import datetime


class CustomHtmxMixin:
    def dispatch(self, request, *args, **kwargs):
        # import pdb; pdb.set_trace()
        self.template_htmx = self.template_name
        if not self.request.META.get("HTTP_HX_REQUEST"):
            self.template_name = "blog/include_blog.html"
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        kwargs["template_htmx"] = self.template_htmx
        return super().get_context_data(**kwargs)


class RegisterPageView(CustomHtmxMixin, View):
    template_name = "blog/register.html"

    def get(self, request):
        return render(request, "blog/register.html", {"form": RegisterForm()})

    def post(self, request):

        form = RegisterForm(request.POST, request.FILES)

        if form.is_valid():
            form.save()
            messages.success(request, "User succesfully registered")
            return redirect("login")
        else:
            messages.warning(request, "Error registered!")
            return render(request, "blog/register.html", {"form": form})


class LoginPageView(CustomHtmxMixin, View):
    template_name = "blog/login.html"

    def get(self, request):
        return render(request, "blog/login.html", {"form": LoginForm()})

    def post(self, request):
        form = LoginForm(request.POST)

        if form.is_valid():
            username = form.cleaned_data.get("username")
            password = form.cleaned_data.get("password")
            user = authenticate(username=username, password=password)

            if user is not None:
                login(request, user)
                messages.info(request, f"You are logged in as { username }")
                return redirect("home")

            else:
                messages.error(request, "Invalid username or password.")
                return redirect("login")

        return render(request, "blog/login.html", {"form": form})


class LogoutView(CustomHtmxMixin, View):
    template_name = "blog/logout.html"

    def get(self, request):
        return render(request, "blog/logout.html")

    def post(self, request):
        logout(request)
        return redirect("home")


class HomePageView(CustomHtmxMixin, TemplateView):
    template_name = "blog/home.html"

    def get(self, request):
        if request.user.is_authenticated:
            posts = Post.objects.exclude(author=request.user)
        else:
            posts = Post.objects.all()

        posts = posts.filter(is_active=True).order_by("id")

        page = request.GET.get("page", 1)
        size = request.GET.get("size", 4)

        paginator = Paginator(posts.order_by("id"), size)
        page_obj = paginator.page(page)

        return render(
            request,
            "blog/home.html",
            {
                "page_obj": page_obj,
            },
        )


class AboutPageView(CustomHtmxMixin, TemplateView):
    template_name = "blog/about.html"


class PostDetailPageView(CustomHtmxMixin, View):
    template_name = "blog/post_detail.html"

    def get(self, request, slug):
        post = get_object_or_404(Post, slug=slug)
        return render(request, "blog/post_detail.html", {"post": post})


class UserProfilePageView(CustomHtmxMixin, LoginRequiredMixin, View):
    template_name = "blog/user_posts.html"

    def get(self, request):
        posts = Post.objects.filter(author=request.user)
        return render(
            request,
            "blog/user_posts.html",
            {
                "posts": posts,
            },
        )


class PostFormPageView(CustomHtmxMixin, LoginRequiredMixin, TemplateView):
    template_name = "blog/post_form.html"

    def get(self, request):
        return render(request, "blog/post_form.html", {"form": PostCreateForm()})

    def post(self, request):
        form = PostCreateForm(request.POST)

        if form.is_valid():

            post = Post.objects.create(
                title=form.cleaned_data.get("title"),
                content=form.cleaned_data.get("content"),
                is_active=form.cleaned_data.get("is_active"),
                author=request.user,
                publisher_at=datetime.datetime.now().strftime("%Y-%m-%d"),
            )
            post.save()

            messages.success(request, "Post succesfully created")
            return redirect("home")
        messages.warning(
            request,
            "There is a mistake in your post ! or your post is not filled to the depth.",
        )
        return render(request, "blog/post_form.html", {"form": form})


class UserPostPageView(CustomHtmxMixin, ListView):
    model = Post
    template_name = "blog/user_posts.html"
    context_object_name = "posts"


class PostUpdateView(CustomHtmxMixin, LoginRequiredMixin, View):
    template_name = "blog/post_update.html"

    def get(self, request, slug):
        post = get_object_or_404(Post, slug=slug)
        form = PostUpdateForm(instance=post)
        return render(request, "blog/post_update.html", {"form": form, "post": post})

    def post(self, request, slug):
        post = get_object_or_404(Post, slug=slug)
        form = PostUpdateForm(request.POST, instance=post)
        if form.is_valid():
            messages.success(request, "Post succsessfully updated")
            form.save()
            return redirect("profile")

        messages.error(request, "You`r post is not valid !")
        return render(request, "blog/post_update.html", {"form": form})


class PostDeleteView(CustomHtmxMixin, LoginRequiredMixin, View):
    template_name = "blog/post_confirm_delete.html"

    def get(self, request, slug):
        post = get_object_or_404(Post, slug=slug)
        return render(request, "blog/post_confirm_delete.html", {"post": post})

    def post(self, request, slug):
        post = get_object_or_404(Post, slug=slug)
        messages.success(request, "post successfully deleted")
        post.delete()
        return redirect("profile")
