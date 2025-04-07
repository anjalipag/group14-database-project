from django.shortcuts import render
from django.db import connection

def index(request):
   saved_recs = get_saved_recs()
   context = {
      'saved_recs': saved_recs,
   }
   return render(request, 'saved_recs.html', context)

def see_recommendation_details(request, rec_id):
   details = get_rec_details(rec_id)
   comments = get_comments(rec_id)
   return render(request, 'saved_rec_details.html', {'rec': details, 'comments': comments})

#NOTE: right now I cannot filter saved recs to a specific user id because I can't login and save user id state
def get_saved_recs():
   with connection.cursor() as c:
      c.execute("SELECT * FROM savedrecommendations JOIN users ON user_posted_id = user_id NATURAL JOIN recommendationpost NATURAL JOIN recommendeditem NATURAL JOIN groups")
      cols = [col[0] for col in c.description]
      saved_recs =  [dict(zip(cols, row)) for row in c.fetchall()]
   return saved_recs

def query_db(query, rec_id):
   with connection.cursor() as c:
      c.execute(query, [rec_id])
      cols = [col[0] for col in c.description]
      row = c.fetchone()
   return dict(zip(cols,row)) if row else None

def get_rec_details(rec_id):
   with connection.cursor() as c:
      c.execute("SELECT * FROM savedrecommendations JOIN users ON user_posted_id = user_id NATURAL JOIN recommendationpost NATURAL JOIN recommendeditem NATURAL JOIN groups WHERE recommendation_id = %s", [rec_id])
      cols = [col[0] for col in c.description]
      row = c.fetchone()
   return dict(zip(cols, row)) if row else None

def get_comments(rec_id):
   with connection.cursor() as c:
      c.execute("SELECT * FROM comment JOIN users ON comment.user_id = users.user_id WHERE recommendation_post_id = %s",[rec_id])
      cols = [col[0] for col in c.description]
      comments =  [dict(zip(cols, row)) for row in c.fetchall()]
   return comments
