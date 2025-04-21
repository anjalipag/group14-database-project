from django.shortcuts import render
from django.db import connection

def my_groups(request):
    # user_id = request.GET.get('user_id')
    user_id = request.session.get('user_id')
    groups = get_groups_joined_by_user(user_id)
    groups_created = get_groups_created(user_id)
    return render(request, 'my_groups.html', {'groups': groups, 'groups_created': groups_created})

def get_groups_joined_by_user(user_id):
    with connection.cursor() as c:
        c.execute("""
            SELECT g.group_id, g.group_name, g.group_photo,
                   u.username AS admin_username
            FROM groups g
            JOIN users u ON g.admin_id = u.user_id
            WHERE g.group_id IN (
                SELECT group_id FROM groupsmembers WHERE user_id = %s
            )
        """, [user_id])
        cols = [col[0] for col in c.description]
        return [dict(zip(cols, row)) for row in c.fetchall()]

def get_groups_created(user_id):
    with connection.cursor() as c:
        c.execute("""
            SELECT g.group_id, g.group_name, g.group_photo,
                   g.admin_id AS admin_username
            FROM groups g
            JOIN users u ON g.admin_id = u.user_id
            WHERE g.admin_id = %s
        """, [user_id])
        cols = [col[0] for col in c.description]
        return [dict(zip(cols, row)) for row in c.fetchall()]
