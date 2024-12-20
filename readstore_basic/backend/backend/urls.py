# readstore-basic/backend/backend/urls.py

"""
URL configuration for backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from rest_framework import routers
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.views import TokenVerifyView

from app import views
from app import ext_views

router = routers.DefaultRouter()
router.register(r'user', views.UserViewSet, basename='User')
router.register(r'owner_group', views.OwnerGroupViewSet)
router.register(r'app_user', views.AppUserViewSet)
router.register(r'group', views.GroupViewSet)
router.register(r'fq_file', views.FqFileViewSet, basename='FqFile')
router.register(r'fq_dataset', views.FqDatasetViewSet, basename='FqDataset')
router.register(r'fq_attachment', views.FqAttachmentViewSet, basename='FqAttachment')
router.register(r'project', views.ProjectViewSet, basename='Project')
router.register(r'project_attachment', views.ProjectAttachmentViewSet, basename='ProjectAttachment')
router.register(r'license_key', views.LicenseKeyViewSet, basename='LicenseKey')
router.register(r'pro_data', views.ProDataViewSet, basename='ProData')

ext_router = routers.DefaultRouter()

# URL patterns for app backend
urlpatterns = [
    path('api_v1/', include(router.urls)),
    path('api_v1/get_user_groups/', views.GetUserGroupsView.as_view()),
    
    path('api_v1/transfer_owner/', views.TransferOwnerView.as_view()),
    
    path('api_v1/user/my_owner_group/', views.UserViewSet.as_view({'get': 'my_owner_group'})),
    path('api_v1/user/my_user/', views.UserViewSet.as_view({'get': 'my_user'})),
    path('api_v1/user/regenerate_token/', views.UserViewSet.as_view({'get': 'regenerate_token'})),
    path('api_v1/user/reset_password/', views.UserViewSet.as_view({'get': 'reset_password'})),

    path('api_v1/fq_file_upload_app/', views.FqFileUploadAppView.as_view()),
    path('api_v1/fq_queue/', views.FqQueueView.as_view()),

    path('api_v1/fq_file/staging/', views.FqFileViewSet.as_view({'get': 'staging'})),
    path('api_v1/fq_file/my_fq_file/', views.FqFileViewSet.as_view({'get': 'my_fq_file'})),
    
    path('api_v1/fq_dataset/collab/', views.FqDatasetViewSet.as_view({'get': 'collab'})),
    path('api_v1/fq_dataset/owner_group/', views.FqDatasetViewSet.as_view({'get': 'owner_group'})),
    path('api_v1/fq_dataset/my_fq_dataset/', views.FqDatasetViewSet.as_view({'get': 'my_fq_dataset'})),
    path('api_v1/fq_dataset/empty/', views.FqDatasetViewSet.as_view({'get': 'empty'})),
    
    path('api_v1/fq_attachment/owner_group/', views.FqAttachmentViewSet.as_view({'get': 'owner_group'})),
    path('api_v1/fq_attachment/collab/', views.FqAttachmentViewSet.as_view({'get': 'collab'})),
    path('api_v1/fq_attachment/fq_dataset/<pk>/', views.FqAttachmentViewSet.as_view({'get': 'fq_dataset'})),

    path('api_v1/project/collab/', views.ProjectViewSet.as_view({'get': 'collab'})),
    path('api_v1/project/owner_group/', views.ProjectViewSet.as_view({'get': 'owner_group'})),

    path('api_v1/project_attachment/owner_group/', views.ProjectAttachmentViewSet.as_view({'get': 'owner_group'})),
    path('api_v1/project_attachment/collab/', views.ProjectAttachmentViewSet.as_view({'get': 'collab'})),
    path('api_v1/project_attachment/project/<pk>/', views.ProjectAttachmentViewSet.as_view({'get': 'project'})),

    path('api_v1/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api_v1/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api_v1/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    
    path('api_v1/pro_data/valid/', views.ProDataViewSet.as_view({'get': 'valid'})),
    path('api_v1/pro_data/owner_group/', views.ProDataViewSet.as_view({'get': 'owner_group'})),
    path('api_v1/pro_data/fq_dataset/<pk>/', views.ProDataViewSet.as_view({'get': 'fq_dataset'})),
    path('api_v1/pro_data/validate_upload_path', views.ProDataViewSet.as_view({'get': 'validate_upload_path'})),
    
    path('admin/', admin.site.urls),
]

# URL patterns for external API
urlpatterns.extend([
    path('api_x_v1/', include(ext_router.urls)),
    path('api_x_v1/auth_token/', ext_views.TokenExt.as_view()),

    path('api_x_v1/project_attachment/', ext_views.ProjectAttachmentExt.as_view()),
    path('api_x_v1/project_attachment/<pk>/', ext_views.ProjectAttachmentExt.as_view()),
    
    path('api_x_v1/project/', ext_views.ProjectExt.as_view()),
    path('api_x_v1/project/<pk>/', ext_views.ProjectExt.as_view()),
    
    path('api_x_v1/fq_attachment/', ext_views.FqAttachmentExt.as_view()),
    path('api_x_v1/fq_attachment/<pk>/', ext_views.FqAttachmentExt.as_view()),
    
    path('api_x_v1/fq_file/', ext_views.FqFileExt.as_view()),
    path('api_x_v1/fq_file/<pk>/', ext_views.FqFileExt.as_view()),
    
    path('api_x_v1/fq_dataset/', ext_views.FqDatasetExt.as_view()),
    path('api_x_v1/fq_dataset/<pk>/', ext_views.FqDatasetExt.as_view()),
    
    path('api_x_v1/pro_data/', ext_views.ProDataExt.as_view()),
    path('api_x_v1/pro_data/<pk>/', ext_views.ProDataExt.as_view()),
    
    path('api_x_v1/fq_file_upload/', ext_views.FqFileUploadExt.as_view()),
])
