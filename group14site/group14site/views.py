from django.shortcuts import render
from django.db import connection
from django.contrib.auth.hashers import make_password


def index(request):
    if 'user_id' in request.session:
        del request.session['user_id']
    error_message = ""
    success_message = ""
    popular_groups = []

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        hashed_password = make_password(password)

        with connection.cursor() as cursor:
            cursor.execute("SELECT user_id FROM Users WHERE username = %s", [username])
            existing_user = cursor.fetchone()

        if existing_user:
            error_message = "Username already exists."
        else:
            with connection.cursor() as cursor:
                cursor.execute("INSERT INTO Users (username, password) VALUES (%s, %s)", [username, hashed_password])
            success_message = "User created successfully. You can now log in."

    return render(request, "group14site/index.html", {"error_message": error_message, "success_message": success_message})
