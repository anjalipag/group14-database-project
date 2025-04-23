from django.shortcuts import render, redirect
from django.db import connection
from django.contrib import messages
import psycopg2

# Create your views here.
from django.http import HttpResponse

def index(request):
    return render(request, 'createGroups.html')

def create_group(request):
    if request.method == 'POST':
        group_name = request.POST['group_name']
        group_description = request.POST['group_description']
        user_id = request.session.get('user_id')
        #idk this might not work rn
        group_photo = request.FILES.get('group_photo')
        print(group_photo)
        photo_data = group_photo.read() if group_photo else None
        print(photo_data)
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





