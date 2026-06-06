from django.core.management.base import BaseCommand
from users.models import Role, Menu, Action, RolePermission,User
from django.utils import timezone

class Command(BaseCommand):
    help = 'Seed initial data: roles, modules, actions, and role permissions'

    def handle(self, *args, **options):
        self.stdout.write('Seeding data...')
        admin_user = User.objects.get(pk=1)  # Assuming the first user is the admin who creates this seed data
        # ---------- Actions ----------
        actions_data = [
            {'name': 'View', 'code': 'view','created_by': admin_user,'created_at': timezone.now()},
            {'name': 'Add', 'code': 'add','created_by': admin_user,'created_at': timezone.now()},
            {'name': 'Update', 'code': 'update','created_by': admin_user,'created_at': timezone.now()},
            {'name': 'Delete', 'code': 'delete','created_by': admin_user,'created_at': timezone.now()},
            {'name': 'Export', 'code': 'export','created_by': admin_user,'created_at': timezone.now()},
            {'name': 'Import', 'code': 'import','created_by': admin_user,'created_at': timezone.now()},
            {'name': 'Approve', 'code': 'approve','created_by': admin_user,'created_at': timezone.now()},
            {'name': 'Reject', 'code': 'reject','created_by': admin_user,'created_at': timezone.now()},
            {'name': 'Publish', 'code': 'publish','created_by': admin_user,'created_at': timezone.now()},
            {'name': 'Unpublish', 'code': 'unpublish','created_by': admin_user,'created_at': timezone.now()},
        ]
        actions = {}
        for act in actions_data:
            obj, created = Action.objects.get_or_create(
                code=act['code'], 
                defaults={
                    'name': act['name'], 
                    'created_by': act['created_by'], 
                    'created_at': act['created_at']
                }
            )
            actions[act['code']] = obj
            if created:
                self.stdout.write(f'  Created action: {obj.name}')
            else:
                self.stdout.write(f'  Action already exists: {obj.name}')

        # ---------- Modules/Menus ----------
        modules_data = [
            {'name': 'Dashboard', 'code': 'dashboard', 'icon': 'file-text', 'order': 1,'created_by': admin_user,'created_at': timezone.now()},
            {'name': 'Posts', 'code': 'posts', 'icon': 'file-text', 'order': 2,'created_by': admin_user,'created_at': timezone.now()},
            {'name': 'Categories', 'code': 'categories', 'icon': 'folder', 'order': 3,'created_by': admin_user,'created_at': timezone.now()},
            {'name': 'Tags', 'code': 'tags', 'icon': 'tags', 'order': 4,'created_by': admin_user,'created_at': timezone.now()},
            {'name': 'Comments', 'code': 'comments', 'icon': 'comments', 'order': 5,'created_by': admin_user,'created_at': timezone.now()},
            {'name': 'Media Library', 'code': 'media', 'icon': 'image', 'order': 6,'created_by': admin_user,'created_at': timezone.now()},
            {'name': 'Users', 'code': 'users', 'icon': 'users', 'order': 7,'created_by': admin_user,'created_at': timezone.now()},
            {'name': 'Roles', 'code': 'roles', 'icon': 'shield', 'order': 8,'created_by': admin_user,'created_at': timezone.now()},
            {'name': 'Permissions', 'code': 'permissions', 'icon': 'shield', 'order': 9,'created_by': admin_user,'created_at': timezone.now()},
            {'name': 'Subscribers', 'code': 'subscribers', 'icon': 'mail', 'order': 10,'created_by': admin_user,'created_at': timezone.now()},
            {'name': 'Reports', 'code': 'reports', 'icon': 'bar-chart', 'order': 11,'created_by': admin_user,'created_at': timezone.now()},
            {'name': 'Site Settings', 'code': 'site_settings', 'icon': 'cog', 'order': 12,'created_by': admin_user,'created_at': timezone.now()},
            {'name': 'Audit Logs', 'code': 'audit_logs', 'icon': 'history', 'order': 13,'created_by': admin_user,'created_at': timezone.now()},
        ]
        modules = {}
        for mod in modules_data:
            obj, created = Menu.objects.get_or_create(
                code=mod['code'],
                defaults={
                    'name': mod['name'],
                    'icon': mod.get('icon'),
                    'order': mod.get('order', 0),
                    'created_by': mod['created_by'],
                    'created_at': mod['created_at']
                }
            )
            modules[mod['code']] = obj
            if created:
                self.stdout.write(f'  Created Menu/Module: {obj.name}')
            else:
                self.stdout.write(f'  Menu/Module already exists: {obj.name}')

        # ---------- Roles ----------
        roles_data = [
            {'name': 'Super Admin', 'code': 'super_admin','created_by': admin_user,'created_at': timezone.now()},
            {'name': 'Admin', 'code': 'admin','created_by': admin_user,'created_at': timezone.now()},
            {'name': 'Editor', 'code': 'editor','created_by': admin_user,'created_at': timezone.now()},
            {'name': 'Author', 'code': 'author','created_by': admin_user,'created_at': timezone.now()},
            {'name': 'Contributor', 'code': 'contributor','created_by': admin_user,'created_at': timezone.now()},
            {'name': 'Moderator', 'code': 'moderator','created_by': admin_user,'created_at': timezone.now()},
            {'name': 'Guest User', 'code': 'guest','created_by': admin_user,'created_at': timezone.now()},
            {'name': 'Subscriber', 'code': 'subscriber','created_by': admin_user,'created_at': timezone.now()},
        ]
        roles = {}
        for role in roles_data:
            obj, created = Role.objects.get_or_create(
                code=role['code'], 
                defaults={
                    'name': role['name'],
                    'created_by': role['created_by'],
                    'created_at': role['created_at']
                }
            )
            roles[role['code']] = obj
            if created:
                self.stdout.write(f'  Created role: {obj.name}')
            else:
                self.stdout.write(f'  Role already exists: {obj.name}')

        # ---------- Role Permissions ----------
        # Define mapping: role_code -> module_code -> list of action codes
        permissions_map = {
            # ==========================================
            # SUPER ADMIN
            # ==========================================
            'super_admin': {
                # all modules, all actions
                'dashboard': ['view'],
                'posts': ['view', 'add', 'update', 'delete', 'export', 'import', 'approve', 'reject', 'publish', 'unpublish'],
                'categories': ['view', 'add', 'update', 'delete', 'export', 'import'],
                'tags': ['view', 'add', 'update', 'delete', 'export', 'import'],
                'comments': ['view', 'add', 'update', 'delete', 'approve', 'reject'],
                'media': ['view', 'add', 'update', 'delete', 'export', 'import'],
                'users': ['view', 'add', 'update', 'delete', 'export', 'import'],
                'roles': ['view', 'add', 'update', 'delete'],
                'permissions': ['view', 'add', 'update', 'delete'],
                'subscribers': ['view', 'add', 'update', 'delete', 'export', 'import'],
                'reports': ['view', 'export'],
                'site_settings': ['view','add', 'update', 'delete'],
                'audit_logs': ['view', 'export'],
            },
            # ==========================================
            # ADMIN
            # ==========================================
            'admin': {
                'dashboard': ['view'],
                'posts': ['view', 'add', 'update', 'delete', 'approve', 'reject', 'publish', 'unpublish'],
                'categories': ['view', 'add', 'update', 'delete'],
                'tags': ['view', 'add', 'update', 'delete'],
                'comments': ['view', 'update', 'delete', 'approve', 'reject'],
                'media': ['view', 'add', 'update', 'delete'],
                'users': ['view', 'add', 'update'],
                'roles': ['view'],
                'permissions': ['view'],
                'subscribers': ['view', 'update', 'export'],
                'reports': ['view', 'export'],
                'site_settings': ['view','add', 'update', 'delete'],
                'audit_logs': ['view'],
            },
            # ==========================================
            # EDITOR
            # ==========================================
            'editor': {
                'dashboard': ['view'],
                'posts': ['view', 'add', 'update', 'approve', 'reject', 'publish', 'unpublish'],
                'categories': ['view', 'add', 'update'],
                'tags': ['view', 'add', 'update'],
                'comments': ['view', 'update', 'delete', 'approve', 'reject'],
                'media': ['view', 'add', 'update'],
                'subscribers': ['view'],
                'reports': ['view'],
            },

            # ==========================================
            # AUTHOR
            # ==========================================
            'author': {
                'dashboard': ['view'],
                'posts': ['view', 'add', 'update'],
                'categories': ['view'],
                'tags': ['view', 'add'],
                'comments': ['view', 'add', 'update', 'delete'],
                'media': ['view', 'add'],
            },

            # ==========================================
            # CONTRIBUTOR
            # ==========================================
            'contributor': {
                'dashboard': ['view'],
                'posts': ['view', 'add', 'update'],
                'categories': ['view'],
                'tags': ['view'],
                'media': ['view', 'add'],
            },

            # ==========================================
            # MODERATOR
            # ==========================================
            'moderator': {
                'dashboard': ['view'],
                'comments': ['view', 'update', 'delete', 'approve', 'reject'],
                'posts': ['view'],
                'users': ['view'],
            },
            # ==========================================
            # SUBSCRIBER
            # ==========================================
            'subscriber': {
                'dashboard': ['view'],
                'posts': ['view'],
                'categories': ['view'],
                'tags': ['view'],
                'comments': ['view', 'add'],
            },

            # ==========================================
            # GUEST USER
            # ==========================================
            'guest': {
                'posts': ['view'],
                'categories': ['view'],
                'tags': ['view'],
            },

        }

        for role_code, module_perms in permissions_map.items():
            role = roles[role_code]
            for module_code, action_codes in module_perms.items():
                module = modules[module_code]
                for action_code in action_codes:
                    action = actions[action_code]
                    obj, created = RolePermission.objects.get_or_create(
                        role=role,
                        menu=module,
                        action=action,
                        created_by=admin_user,
                        created_at=timezone.now()
                    )
                    if created:
                        self.stdout.write(f'  Perm: {role.name} | {module.name} | {action.name}')
                    # else skip

        self.stdout.write(self.style.SUCCESS('Seed data completed successfully!'))