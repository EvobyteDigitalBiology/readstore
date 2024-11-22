from rest_framework.permissions import BasePermission

class RSClientHasStaging(BasePermission):
    
    def has_permission(self, request, view):
        
        if hasattr(request.user, 'appuser'):
            if request.user.groups.filter(name='staging').exists():
                return True
            else:
                return False
        else:
            return False