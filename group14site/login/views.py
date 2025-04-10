from django.shortcuts import render, redirect
from django.db import connection


def index(request):
    error_message = ""
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM Users WHERE username = %s AND password = %s", [username, password])
            user = cursor.fetchone()

        if user:
            user_id = user[0]
            request.session["user_id"] = user_id
            return redirect(f"/group/saved/")
        else:
            error_message = "Invalid username or password."

    return render(request, "login/index.html", {"error_message": error_message})