from django.shortcuts import render, redirect
from django.db import connection
from groupFeed import views
def user_recommendations(request):
    user_id = request.session.get('user_id')

    if not user_id:
        return HttpResponse("You must be logged in to see your recommendations.")

    with connection.cursor() as cursor:
        cursor.execute("SELECT username FROM Users WHERE user_id = %s", [user_id])
        user_row = cursor.fetchone()
    if user_row:
        username = user_row[0]
    else:
        username = "Unknown User"

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT
                rp.recommendation_post_id,
                rp.description,
                rp.up_vote_count,
                rp.down_vote_count,
                rp.overall_rating,
                rp.extra_info,
                rp.time_stamp,
                ri.title,
                g.group_name,
                c.category_name
            FROM RecommendationPost rp
            JOIN RecommendedItem ri ON rp.recommended_item_id = ri.recommended_item_id
            JOIN Groups g ON rp.group_id = g.group_id
            JOIN Category c ON ri.category_id = c.category_id
            WHERE rp.user_id = %s
            ORDER BY rp.time_stamp DESC
        """, [user_id])
        rows = cursor.fetchall()
    user_posts = []
    for row in rows:
        extra_info = get_extra_info(row[0])
        post_data = {
            'post_id': row[0],
            'description': row[1],
            'up_vote_count': row[2],
            'down_vote_count': row[3],
            'overall_rating': row[4],
            'extra_info': extra_info,
            'time_stamp': row[6],
            'title': row[7],
            'group_name': row[8],
            'category_name': row[9]
        }
        user_posts.append(post_data)

    context = {
        'user_posts': user_posts,
        'username': username,
    }
    return render(request, 'user_recommendations.html', context)

def delete_my_post(request, recommendation_post_id):
    print(recommendation_post_id)
    with connection.cursor() as c:
        c.execute("""DELETE FROM RecommendationPost WHERE recommendation_post_id = %s""", [recommendation_post_id])
    return redirect('user_recommendations')

def get_extra_info(recommendation_post_id):
    with connection.cursor() as c:
        #first find category (as category determines the extra info type)
        c.execute("""SELECT c.category_name, ri.recommended_item_id FROM RecommendationPost rp JOIN RecommendedItem ri ON rp.recommended_item_id = ri.recommended_item_id JOIN Category c ON ri.category_id = c.category_id WHERE rp.recommendation_post_id = %s""", [recommendation_post_id])

        row = c.fetchone()

        if not row:
            return {}

        category_name, recommendation_item_id = row

        #need to get data from appropriate table (based on rec id and category)
        if category_name == "Movies":
            c.execute("""SELECT director, duration, rated, plot FROM Movie WHERE recommended_item_id = %s""", [recommendation_item_id])
            result = c.fetchone()
            if result:
                return {'Director': result[0], 'Duration': result[1], 'Rated': result[2], 'Plot': result[3]}
        elif category_name == "TV Shows":
            c.execute("""SELECT director, season_count, rated, plot FROM TVShow WHERE recommended_item_id = %s""",
                      [recommendation_item_id])
            result = c.fetchone()
            if result:
                return {'Director': result[0], 'Season Count': result[1], 'Rated': result[2], 'Plot': result[3]}
        elif category_name == "Music":
            c.execute("""SELECT artist, duration, album FROM Song WHERE recommended_item_id = %s""",
                      [recommendation_item_id])
            result = c.fetchone()
            if result:
                return {'Artist': result[0], 'Duration': result[1], 'Album': result[2]}
        elif category_name == "Books":
            c.execute("""SELECT author, year_published FROM Book WHERE recommended_item_id = %s""",
                      [recommendation_item_id])
            result = c.fetchone()
            if result:
                return {'Author': result[0], 'Year Published': result[1]}
    return {}
def comment_detail(request, recommendation_post_id):
    user_id = request.session.get('user_id')
    with connection.cursor() as cursor:
        cursor.execute("SELECT username FROM Users WHERE user_id = %s", [user_id])
        user_row = cursor.fetchone()
    if user_row:
        username = user_row[0]
    else:
        username = "Unknown User"

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT
                c.category_name,
                rp.recommendation_post_id,
                rp.description,
                rp.up_vote_count,
                rp.down_vote_count,
                rp.overall_rating,
                rp.extra_info,
                rp.time_stamp,
                ri.title,
                u.username,
                rp.user_id
            FROM RecommendationPost rp
            JOIN RecommendedItem ri ON rp.recommended_item_id = ri.recommended_item_id
            JOIN Category c ON ri.category_id = c.category_id
            JOIN Users u ON rp.user_id = u.user_id
            WHERE rp.recommendation_post_id = %s
            """, [recommendation_post_id])
        row = cursor.fetchone()
        post_data = {
            'post_id': row[1],
            'description': row[2],
            'up_vote_count': row[3],
            'down_vote_count': row[4],
            'overall_rating': row[5],
            'extra_info': row[6],
            'time_stamp': row[7],
            'title': row[8],
            'posted_by': row[9],
            'category_name': row[0],
            'posted_by_id': row[10],
        }

        all_comments =[]
        cursor.execute("""
                    SELECT
                        c.comment_id,
                        c.comment_text,
                        c.time_posted,
                        u.username
                    FROM Comment c 
                    JOIN Users u ON c.user_id = u.user_id
                    WHERE c.recommendation_post_id = %s
                    """, [recommendation_post_id])
        rows = cursor.fetchall()
        for row in rows:
            comment_data = {
                'comment_id' : row[0],
                'comment_text': row[1],
                'time_posted': row[2],
                'posted_by': row[3]
            }
            all_comments.append(comment_data)

    # print("all_comments", all_comments)
    #Get admin ID for delete admin perms
        cursor.execute("SELECT group_id FROM RecommendationPost WHERE recommendation_post_id = %s", [recommendation_post_id])
        group_id = cursor.fetchone()[0]
        cursor.execute("SELECT admin_id FROM Groups WHERE group_id = %s", [group_id])
        admin_id = cursor.fetchone()[0]

    context = {
        'recommendation_post_id': recommendation_post_id,
        'post': post_data,
        'comments_for_post': all_comments,
        'admin_id': admin_id,
        'user_id':request.session.get('user_id'),
        'username': username,
    }

    return render(request, 'user_reccs_comments.html', context)