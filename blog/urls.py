from django.urls import path

from . import views

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('generate', views.GenerateBlogView.as_view(), name='generate_blog'),
    path('generate/local', views.GenerateLocalBlogView.as_view(), name='generate_local_blog'),
    path('output/index', views.GeneratedIndexView.as_view(), name='generated_index'),
    path('output/story', views.GeneratedStoryView.as_view(), name='generated_story'),
]
