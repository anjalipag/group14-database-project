from django.shortcuts import render, redirect
from django.db import connection
from django.contrib import messages
import psycopg2

# Create your views here.
from django.http import HttpResponse

def index(request):
    user_id = request.session.get('user_id')

    with connection.cursor() as cursor:
        cursor.execute("SELECT username FROM Users WHERE user_id = %s", [user_id])
        user_row = cursor.fetchone()
    if user_row:
        username = user_row[0]
    else:
        username = "Unknown User"
    return render(request, 'createGroups.html', { 'username': username})

def create_group(request):
    if request.method == 'POST':
        group_name = request.POST['group_name']
        group_description = request.POST['group_description']
        user_id = request.session.get('user_id')
        #idk this might not work rn
        group_photo = request.FILES.get('group_photo')
        photo_data = group_photo.read() if group_photo else None
    else:
        return

    with connection.cursor() as c:
        c.execute("""
            INSERT INTO groups (admin_id, group_name, group_description, group_photo)
            VALUES (%s, %s, %s, %s)
            RETURNING group_id
        """, [user_id, group_name, group_description, psycopg2.Binary(photo_data)])
        group_id = c.fetchone()[0]
        c.execute(""" INSERT INTO GroupsMembers (group_id, user_id, invitation_status)
                        VALUES (%s, %s, 'Accepted')""",[group_id, user_id])

    messages.success(request, "Successfully created group: " + group_name + "!")
    return redirect(index)





