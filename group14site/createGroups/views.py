from django.shortcuts import render
from django.db import connection

# Create your views here.
from django.http import HttpResponse


def index(request):
    # return HttpResponse("Hello, world. You're at the create groups index.")
    return render(request, 'createGroups.html')

# NEEDS TO TAKE IN USERS ADMIN ID
def create_group(request):
    if request.method == 'POST':
        group_name = request.POST['group_name']
        group_description = request.POST['group_description']
        #idk this might not work rn
        #group_photo = request.FILES.get('group_photo')
    else:
        return

    with connection.cursor() as c:
        c.execute("""INSERT INTO groups (admin_id, group_name, group_description) VALUES (1, %s, %s)""", [group_name, group_description])

    return HttpResponse("success!")





