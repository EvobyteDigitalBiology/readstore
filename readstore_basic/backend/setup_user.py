#!/usr/bin/env python3

"""

Script setup_user.py creates database permissions, user groups,
and service users.

Test datasets can be added as well to django DB

"""

import os
import django
from typing import List
from itertools import chain
import string



assert os.getenv("DJANGO_SETTINGS_MODULE"), "DJANGO_SETTINGS_MODULE not set"

django.setup()

from django.contrib.auth.models import Group
from django.contrib.auth.models import User
from django.contrib.auth.models import Permission
from django.contrib.auth.hashers import make_password

from app.models import AppUser
from app.models import OwnerGroup
from app.models import Project


def validate_charset(query_str: str):
    
    allowed = string.digits + string.ascii_lowercase + string.ascii_uppercase + '_-.@'
    allowed = set(allowed)
    
    return set(query_str) <= allowed

# Permission Management

class ViewPermissions:
    """Define view permissions for a model view.
    
        Collect permissions for a model view.
        Provide methods to get different types of permissions.
        
        Attributes:
            model_view (str): The model view name
            add_permission (Permission): The add permission
            change_permission (Permission): The change permission
            delete_permission (Permission): The delete permission
            view_permission (Permission): The view permission
        
        Methods:
            get_permissions(codename): Get a permission by codename
            get_add_permission(): Get the add permission
            get_change_permission(): Get the change permission
            get_delete_permission(): Get the delete permission
            get_view_permission(): Get the view permission
            get_rw_permissions(): Get the add, change, and view permissions
    """
    
    def __init__(self, model_view: str) -> None:
        self.model_view = model_view
        model_view_format = model_view.replace('_', '').lower()
        
        self.add_permission = self.get_permissions(f'add_{model_view}')
        self.change_permission = self.get_permissions(f'change_{model_view}')
        self.delete_permission = self.get_permissions(f'delete_{model_view}')
        self.view_permission = self.get_permissions(f'view_{model_view}')        
        
    def get_permissions(self, codename) -> Permission:
        """Get a permission by codename."""
        return (Permission
                .objects
                .get(codename=codename))

    def get_add_permission(self) -> Permission:
        """Get add permission for view."""
        return self.add_permission
    
    def get_change_permission(self) -> Permission:
        """Get change permission for view."""
        return self.change_permission
    
    def get_delete_permission(self) -> Permission:
        """Get delete permission for view."""
        return self.delete_permission
    
    def get_view_permission(self) -> Permission:
        """Get view permission for view."""
        return self.view_permission
    
    def get_rw_permissions(self) -> List[Permission]:
        """Get rw permission for view."""
        return [self.get_add_permission(),
                self.get_change_permission(),
                self.get_view_permission()]
    
    def get_full_permissions(self) -> List[Permission]:
        """Get all permissions for view."""
        return [self.get_add_permission(),
                self.get_change_permission(),
                self.get_delete_permission(),
                self.get_view_permission()]
    
class ViewPermissionManager():
    """Manager for multiple view permissions.

        Collect view permissions for multiple model views.
        
        Attributes:
            view_permissions (List[ViewPermissions]): List of view permissions
        
        Methods:
            get_view_permissions(): Get all view permissions
            get_rw_permissions(): Get all add, change, and view permissions
    """
    
    def __init__(self, view_permissions: List[ViewPermissions]) -> None:
        self.view_permissions = view_permissions
    
    def get_view_permissions(self) -> List[Permission]:
        """Get all view permissions."""
        return [view_permission.get_view_permission() for \
            view_permission in self.view_permissions] 
    
    def get_rw_permissions(self) -> List[Permission]:
        """Get all rw (add, change, view) permissions."""
        permissions = [view_permission.get_rw_permissions() for \
            view_permission in self.view_permissions]
        permissions = list(chain(*permissions))
        return permissions
    
    def get_full_permissions(self) -> List[Permission]:
        """Get all permissions."""
        permissions = [view_permission.get_full_permissions() for \
            view_permission in self.view_permissions]
        permissions = list(chain(*permissions))
        return permissions
    
def create_admin_user(name: str, password: str):
    if User.objects.filter(username=name).exists():
        return False
    else:
        admin = User.objects.create(username=name,
                                    password=make_password(password),
                                    is_staff=True)
                
        admin.groups.set([admin_group])
        admin.save()
        return True


if __name__ == '__main__':

    print("Setup permissions....")
    
    # Example
    user_permissions = ViewPermissions('user')
    app_user_permissions = ViewPermissions('appuser')
    owner_group_permissions = ViewPermissions('ownergroup')
    group_permissions = ViewPermissions('group')
    fq_file_permissions = ViewPermissions('fqfile')
    fq_dataset_permissions = ViewPermissions('fqdataset')
    fq_attachment_permissions = ViewPermissions('fqattachment')
    project_permissions = ViewPermissions('project')
    project_attachment_permissions = ViewPermissions('projectattachment')
    license_key_permissions = ViewPermissions('licensekey')

    view_permissions_manager = ViewPermissionManager([user_permissions,
                                                    app_user_permissions,
                                                    owner_group_permissions,
                                                    group_permissions,
                                                    fq_file_permissions,
                                                    project_permissions,
                                                    project_attachment_permissions,
                                                    fq_dataset_permissions,
                                                    fq_attachment_permissions,
                                                    license_key_permissions])

    print("Setup user groups....")

    admin_group, created = Group.objects.get_or_create(name='admin')
    admin_group.permissions.set(view_permissions_manager.get_full_permissions())

    appuser_group, created = Group.objects.get_or_create(name='appuser')
    appuser_group.permissions.set(view_permissions_manager.get_view_permissions() + \
                                    project_permissions.get_full_permissions() + \
                                    project_attachment_permissions.get_full_permissions() + \
                                    user_permissions.get_full_permissions() + \
                                    fq_dataset_permissions.get_full_permissions() + \
                                    fq_attachment_permissions.get_full_permissions() + \
                                    fq_file_permissions.get_full_permissions())

    staging_group, created = Group.objects.get_or_create(name='staging')
    staging_group.permissions.set(fq_file_permissions.get_full_permissions())


    # Create admin user
    print("Setup admin user....")

    if User.objects.filter(username='admin').exists():
        print("Admin user already exists.")
        admin = User.objects.get(username='admin')
    else:
        print('\n')

        print('Set ReadStore ADMIN Account')
        
        admin = User.objects.create(username='admin',
                                    password=make_password('readstore'),
                                    is_staff=True)
                
        admin.groups.set([admin_group])
        admin.save()
        print("Admin user created.")

    # Create default owner group
    print("Setup default owner group....")
    if not OwnerGroup.objects.filter(name='default').exists():
        OwnerGroup.objects.create(name='default', owner=admin)
        print("Default owner group created.")