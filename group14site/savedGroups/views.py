from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.db import connection

def my_groups(request):
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
            AND g.admin_id != %s
        """, [user_id, user_id])
        cols = [col[0] for col in c.description]
        return [dict(zip(cols, row)) for row in c.fetchall()]

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

def get_groups_created(user_id):
    with connection.cursor() as c:
        c.execute("""
            SELECT 
            g.group_id,
            g.group_name,
            g.group_photo,
            g.admin_id AS admin_username,
            (
                SELECT COUNT(*) 
                FROM GroupsMembers gm 
                WHERE gm.group_id = g.group_id 
                  AND gm.invitation_status = 'Pending'
            ) AS num_pending
        FROM groups g
        JOIN users u ON g.admin_id = u.user_id
        WHERE g.admin_id = %s
        """, [user_id])
        cols = [col[0] for col in c.description]
        return [dict(zip(cols, row)) for row in c.fetchall()]

def admin_view(request, group_id):
    if request.method == 'POST':
        uid_to_remove = int(request.POST.get('user_id'))
        with connection.cursor() as c:
            c.execute("""DELETE FROM GroupsMembers WHERE group_id = %s AND user_id = %s""", [group_id, uid_to_remove])
        return redirect('admin_view', group_id=group_id)

    group_members = get_group_members(group_id,request.session.get('user_id'))
    group_name = get_group_name(group_id)
    return render(request, 'admin_view.html', {'group_id': group_id, 'group_name': group_name, 'group_members': group_members})

def get_group_members(group_id, current_user):
    with connection.cursor() as c:
        c.execute("""
               SELECT * FROM groupsmembers gm JOIN users u ON gm.user_id = u.user_id WHERE gm.group_id = %s AND gm.invitation_status = 'Accepted'
           AND u.user_id != %s""", [group_id, current_user])
        cols = [col[0] for col in c.description]
        return [dict(zip(cols, row)) for row in c.fetchall()]

def get_group_name(group_id):
    with connection.cursor() as c:
        c.execute("""
               SELECT group_name FROM groups WHERE groups.group_id = %s
           """, [group_id])
        row = c.fetchone()
        return row[0]

def manage_requests(request, group_id):
    if request.method == 'POST':
        action = request.POST.get("action")
        uid = request.POST.get("user_id")

        with connection.cursor() as c:
            if action == "accept":
                c.execute("""
                UPDATE GroupsMembers SET invitation_status = 'Accepted' WHERE group_id = %s AND user_id = %s""", [group_id, uid])
            elif action == "reject":
                c.execute("""DELETE FROM GroupsMembers WHERE group_id = %s AND user_id = %s AND invitation_status = 'Pending'""", [group_id, uid])
        return redirect("manage_requests", group_id = group_id)

    #If not trying to mod requests, just default and show pending requests
    with connection.cursor() as c:
        c.execute("""SELECT u.user_id, u.username FROM groupsmembers gm JOIN users u on gm.user_id = u.user_id WHERE gm.group_id=%s AND gm.invitation_status = 'Pending'""", [group_id])

        pending_requests = c.fetchall()
    return render(request, 'manage_requests.html', {"group_id": group_id, "pending_requests": pending_requests,})
