from django.urls import path
from . import views
from . import file_upload_utility 

urlpatterns = [
    path('', views.homepage, name='homepage'),
    path('login/',views.login_view,name='login'),
    path('signup/',views.signup_view,name='signup'),
    path('logout/',views.logout_view,name='logout'),
    path('chatpage/<str:chat_id>',views.chatpage_view,name='chatpage'),
    path('profile/',views.profile_view,name='profile'),
    path('delete_account/',views.delete_account_view,name='delete_account'),
    path('password_reset/',views.password_reset_view,name='password_reset'),
    path('upload_docs/',file_upload_utility.upload_docs,name="upload_docs"),
    path('delete_doc/<str:id>',file_upload_utility.delete_doc,name="delete_doc"),
    path('delete_all_docs/',views.delete_all_docs_view,name="delete_all_docs"),
    path('new_chat/',views.new_chat_view,name="new_chat"),
    
]