from django.shortcuts import render, redirect

# Create your views here.
from django.http import HttpResponse
from django.db import connection
from datetime import datetime

# chatGPT was used to understand how to use connection.cursor() and understand POST without model forms
def index(request):
    return HttpResponse("Hello, world. You're at the home index.")

def group_feed(request, group_id):
    post_by_category ={}
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
            u.username
        FROM RecommendationPost rp
        JOIN RecommendedItem ri ON rp.recommended_item_id = ri.recommended_item_id
        JOIN Category c ON ri.category_id = c.category_id
        JOIN Users u ON rp.user_id = u.user_id
        WHERE rp.group_id = %s
        ORDER BY c.category_name, rp.time_stamp DESC""", [group_id])
        rows = cursor.fetchall()

    for row in rows:
        category_name = row[0]
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
        }

        # https://stackoverflow.com/questions/35918831/dict-setdefault-appends-one-extra-default-item-into-the-value-list
        post_by_category.setdefault(category_name, []).append(post_data)

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT c.category_name FROM Category c
            """
        )
        category_names = cursor.fetchall()

    context = {
        'group_id': group_id,
        'category_posts': post_by_category,
        'category_names': category_names,
    }



    return render(request, 'group_feed.html', context)

from django.shortcuts import redirect
from django.db import connection
from datetime import datetime

def add_recommendation(request, group_id):
    if request.method == "POST":
        user_id = request.session.get('user_id')
        category_name = request.POST.get('category_name')
        title = request.POST.get('title')
        description = request.POST.get('description')
        overall_rating = request.POST.get('overall_rating')
        extra_info = request.POST.get('extra_info')
        time_stamp = datetime.now()
        up_vote_count = 0
        down_vote_count = 0

        # Get category_id from category_name
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT category_id FROM Category WHERE category_name = %s",
                [category_name]
            )
            row = cursor.fetchone()
            category_id = row[0]

        # Insert into RecommendedItem
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO RecommendedItem (title, category_id) VALUES (%s, %s) RETURNING recommended_item_id",
                [title, category_id]
            )
            recommended_item_id= cursor.fetchone()[0]

        # Insert into RecommendationPost
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO RecommendationPost
                (user_id, group_id, recommended_item_id, description, up_vote_count, down_vote_count, overall_rating, extra_info, time_stamp)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                [user_id, group_id, recommended_item_id, description, up_vote_count, down_vote_count, overall_rating, extra_info, time_stamp]
            )

    return redirect('group_feed', group_id=group_id)

def group_detail(request, recommendation_post_id):
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
                u.username
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
            'category_name': row[0]
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
                'comment_text': row[1],
                'time_posted': row[2],
                'posted_by': row[3]
            }
            all_comments.append(comment_data)

    print("all_comments", all_comments)
    context = {
        'recommendation_post_id': recommendation_post_id,
        'post': post_data,
        'comments_for_post': all_comments,
    }

    return render(request, 'group_detail.html', context)

def add_comment(request, recommendation_post_id):
    if request.method == "POST":
        user_id = request.session.get('user_id')
        comment = request.POST.get("comment_text")
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO Comment (comment_text, time_posted, user_id, recommendation_post_id)
                VALUES (%s, %s, %s, %s)
                """,
                [comment, now, user_id, recommendation_post_id]  # Replace user_id=1 when merge
            )

    return redirect('group_detail', recommendation_post_id=recommendation_post_id)

##MODIFY LATER: change to user id (not hardcoded)
def handle_upvote(request, recommendation_post_id):
    with connection.cursor() as c:
        #This is to see how the user has/has not voted
        c.execute("""SELECT vote_type FROM voting WHERE user_id = %s AND recommendation_post = %s""", [1, recommendation_post_id])
        row = c.fetchone()

        #If the user has never voted, they can add a vote
        if row is None:
            c.execute("""INSERT INTO voting(user_id,recommendation_post, vote_type) VALUES(%s, %s, 'Upvoted')""", [1, recommendation_post_id])
            c.execute("""UPDATE RecommendationPost SET up_vote_count = up_vote_count + 1 WHERE recommendation_post_id = %s""", [recommendation_post_id])

        #If they've downvoted before, change their vote
        elif row[0] == 'Downvoted':
            c.execute("""UPDATE voting SET vote_type = 'Upvoted' WHERE user_id = %s AND recommendation_post = %s""", [1, recommendation_post_id])

            c.execute("""UPDATE RecommendationPost SET up_vote_count = up_vote_count + 1, down_vote_count = down_vote_count - 1 WHERE recommendation_post_id = %s""", [recommendation_post_id])

        elif row[0] == 'Upvoted':
            #Shouldn't be able to upvote again
            pass

    #Reload page
    return redirect('group_detail', recommendation_post_id=recommendation_post_id)

def handle_downvote(request, recommendation_post_id):
    with connection.cursor() as c:
        # This is to see how the user has/has not voted
        c.execute("""SELECT vote_type FROM voting WHERE user_id = %s AND recommendation_post = %s""",
                  [1, recommendation_post_id])
        row = c.fetchone()

        # If the user has never voted, they can add a vote
        if row is None:
            c.execute("""INSERT INTO voting(user_id,recommendation_post, vote_type) VALUES(%s, %s, 'Downvoted')""",
                      [1, recommendation_post_id])
            c.execute(
                """UPDATE RecommendationPost SET down_vote_count = down_vote_count + 1 WHERE recommendation_post_id = %s""",
                [recommendation_post_id])

        # If they've upvoted before, change their vote
        elif row[0] == 'Upvoted':
            c.execute("""UPDATE voting SET vote_type = 'Downvoted' WHERE user_id = %s AND recommendation_post = %s""",
                      [1, recommendation_post_id])

            c.execute(
                """UPDATE RecommendationPost SET down_vote_count = down_vote_count + 1, up_vote_count = up_vote_count - 1 WHERE recommendation_post_id = %s""",
                [recommendation_post_id])

        elif row[0] == 'Downvoted':
            # Shouldn't be able to downvote again
            pass

    # Reload page
    return redirect('group_detail', recommendation_post_id=recommendation_post_id)