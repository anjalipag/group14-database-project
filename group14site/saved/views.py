from django.shortcuts import render,redirect
from django.db import connection

def index(request):
   saved_recs = get_saved_recs(request)
   context = {
      'saved_recs': saved_recs,
   }
   return render(request, 'saved_recs.html', context)

#NOTE: right now I cannot filter saved recs to a specific user id because I can't login and save user id state
def get_saved_recs(request):
   user_id = request.session.get('user_id')
   with connection.cursor() as c:
      c.execute("SELECT * FROM savedrecommendations JOIN users ON user_posted_id = user_id NATURAL JOIN recommendationpost NATURAL JOIN recommendeditem NATURAL JOIN groups WHERE user_saved_id = %s", [user_id])
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

##MODIFY LATER: change to user id (not hardcoded)

def delete_rec(request, rec_id):
    print("rec_id", rec_id)
    user_id = request.session.get('user_id')
    with connection.cursor() as c:
        c.execute("""
        DELETE FROM SavedRecommendations WHERE user_saved_id = %s AND saved_recommendation_id = %s
        """, [user_id, rec_id])

    saved_recs = get_saved_recs(request)
    context = {
        'saved_recs': saved_recs,
    }
    return render(request, 'saved_recs.html', context)
def handle_upvote(request, rec_id):
    user_id = request.session.get('user_id')
    with connection.cursor() as c:
        #This is to see how the user has/has not voted
        c.execute("""SELECT vote_type FROM voting WHERE user_id = %s AND recommendation_post = %s""", [user_id, rec_id])
        row = c.fetchone()

        #If the user has never voted, they can add a vote
        if row is None:
            c.execute("""INSERT INTO voting(user_id,recommendation_post, vote_type) VALUES(%s, %s, 'Upvoted')""", [user_id, rec_id])
            c.execute("""UPDATE RecommendationPost SET up_vote_count = up_vote_count + 1 WHERE recommendation_post_id = %s""", [rec_id])

        #If they've downvoted before, change their vote
        elif row[0] == 'Downvoted':
            c.execute("""UPDATE voting SET vote_type = 'Upvoted' WHERE user_id = %s AND recommendation_post = %s""", [user_id, rec_id])

            c.execute("""UPDATE RecommendationPost SET up_vote_count = up_vote_count + 1, down_vote_count = down_vote_count - 1 WHERE recommendation_post_id = %s""", [rec_id])

        elif row[0] == 'Upvoted':
            #Shouldn't be able to upvote again
            pass

    #Reload page
    return redirect('saved_rec_details', rec_id=rec_id)

def handle_downvote(request, rec_id):
    user_id = request.session.get('user_id')
    with connection.cursor() as c:
        # This is to see how the user has/has not voted
        c.execute("""SELECT vote_type FROM voting WHERE user_id = %s AND recommendation_post = %s""",
                  [user_id, rec_id])
        row = c.fetchone()

        # If the user has never voted, they can add a vote
        if row is None:
            c.execute("""INSERT INTO voting(user_id,recommendation_post, vote_type) VALUES(%s, %s, 'Downvoted')""",
                      [user_id, rec_id])
            c.execute(
                """UPDATE RecommendationPost SET down_vote_count = down_vote_count + 1 WHERE recommendation_post_id = %s""",
                [rec_id])

        # If they've upvoted before, change their vote
        elif row[0] == 'Upvoted':
            c.execute("""UPDATE voting SET vote_type = 'Downvoted' WHERE user_id = %s AND recommendation_post = %s""",
                      [user_id, rec_id])

            c.execute(
                """UPDATE RecommendationPost SET down_vote_count = down_vote_count + 1, up_vote_count = up_vote_count - 1 WHERE recommendation_post_id = %s""",
                [rec_id])

        elif row[0] == 'Downvoted':
            # Shouldn't be able to downvote again
            pass

    # Reload page
    return redirect('saved_rec_details', rec_id=rec_id)