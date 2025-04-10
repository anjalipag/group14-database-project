from django.shortcuts import render
from django.db import connection

def browse_groups(request):
    #username= 'test1'
    #username =  request.session.get('user_id')

    #user_id = get_user_id_by_username(username)
    user_id = request.session.get('user_id')
    groups = get_groups_not_joined_by_user(user_id)

    return render(request, 'browse_groups.html', {'groups': groups})

def get_user_id_by_username(username):
    with connection.cursor() as c:
        c.execute("SELECT user_id FROM users WHERE username = %s", [username])
        row = c.fetchone()
    return row[0] if row else None

def get_groups_not_joined_by_user(user_id):
    with connection.cursor() as c:
        c.execute("""
            SELECT g.group_id, g.group_name, g.group_description AS group_description, g.group_photo AS group_photo_url,
                   u.username AS admin_username
            FROM groups g
            JOIN users u ON g.admin_id = u.user_id
            WHERE g.group_id NOT IN (
                SELECT group_id FROM groupsmembers WHERE user_id = %s
                )
        """, [user_id])
        cols = [col[0] for col in c.description]
        groups = [dict(zip(cols, row)) for row in c.fetchall()]
    return groups
