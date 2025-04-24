from django.shortcuts import render, redirect
from django.db import connection
from django.contrib.auth.hashers import check_password

#How to hash passwords Source Used: https://docs.djangoproject.com/en/5.2/topics/auth/passwords/

def index(request):
  error_message = ""
  if request.method == "POST":
      username = request.POST.get("username")
      password = request.POST.get("password")

      with connection.cursor() as cursor:
          cursor.execute("SELECT user_id, password FROM Users WHERE username = %s", [username])
          user = cursor.fetchone()

      if user and check_password(password, user[1]):
          user_id = user[0]
          request.session["user_id"] = user_id
          return redirect(f"/group/saved/")
      else:
          error_message = "Invalid username or password."

  return render(request, "login/index.html", {"error_message": error_message})


