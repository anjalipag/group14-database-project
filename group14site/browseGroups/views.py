from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.db import connection

def browse_groups(request):
    user_id = request.session.get('user_id')
    groups = get_groups_not_joined_by_user(user_id)
    with connection.cursor() as cursor:
        cursor.execute("SELECT group_name, total_posts, total_users FROM MostPopularGroups")

        popular_groups = cursor.fetchall()

    return render(request, 'browse_groups.html', {'groups': groups, "popular_groups": popular_groups})

def send_join_request(request, group_id):
    if request.method == 'POST':
        user_id = request.session.get('user_id')
    with connection.cursor() as cursor:
        cursor.execute("""
        INSERT INTO GroupsMembers(group_id, user_id, invitation_status)
        VALUES (%s, %s, 'Pending')""",
                       [group_id, user_id])
    return redirect('browse_groups')

def get_user_id_by_username(username):
    with connection.cursor() as c:
        c.execute("SELECT user_id FROM users WHERE username = %s", [username])
        row = c.fetchone()
    return row[0] if row else None

def serve_group_image(request, group_id):

    with connection.cursor() as c:
        c.execute("SELECT group_photo FROM groups WHERE group_id = %s", [group_id])
        row = c.fetchone()

    if row and row[0]:
        return HttpResponse(row[0], content_type='image/jpeg')  # or image/png
    else:
        # Fallback image
        from django.shortcuts import redirect
        return redirect("https://via.placeholder.com/400x200.png?text=No+Image")

def get_groups_not_joined_by_user(user_id):
    with connection.cursor() as c:
        c.execute("""
            SELECT 
                g.group_id, 
                g.group_name, 
                g.group_description AS group_description, 
                g.group_photo AS group_photo,
                u.username AS admin_username,
                CASE 
                    WHEN gm.invitation_status = 'Pending' THEN 1
                    ELSE 0
                END AS status
            FROM groups g
            JOIN users u ON g.admin_id = u.user_id
            LEFT JOIN groupsmembers gm 
                ON g.group_id = gm.group_id AND gm.user_id = %s
            WHERE g.group_id NOT IN (
                SELECT group_id 
                FROM groupsmembers 
                WHERE user_id = %s AND invitation_status = 'Accepted'
            ) AND g.admin_id != %s
        """, [user_id, user_id, user_id])
        cols = [col[0] for col in c.description]
        groups = [dict(zip(cols, row)) for row in c.fetchall()]
    return groups
