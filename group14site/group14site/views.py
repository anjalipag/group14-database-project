from django.shortcuts import render, redirect
from django.db import connection


def index(request):
    error_message = ""
    success_message = ""

    if request.method == "POST":
        if "signup" in request.POST:
            username = request.POST.get("username")
            password = request.POST.get("password")

            # Check if username already exists
            with connection.cursor() as cursor:
                cursor.execute("SELECT user_id FROM Users WHERE username = %s", [username])
                existing_user = cursor.fetchone()

            if existing_user:
                error_message = "Username already exists."
            else:
                with connection.cursor() as cursor:
                    cursor.execute("INSERT INTO Users (username, password) VALUES (%s, %s)", [username, password])
                success_message = "User created successfully. You can now log in."

    return render(request, "group14site/index.html", {"error_message": error_message, "success_message": success_message})
