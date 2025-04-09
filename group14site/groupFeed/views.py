from django.shortcuts import render, redirect

# Create your views here.
from django.http import HttpResponse
from django.db import connection
from datetime import datetime

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

    context = {
        'group_id': group_id,
        'category_posts': post_by_category,
    }

    return render(request, 'group_feed.html', context)

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
        comment = request.POST.get("comment_text")
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO Comment (comment_text, time_posted, user_id, recommendation_post_id)
                VALUES (%s, %s, %s, %s)
                """,
                [comment, now, 1, recommendation_post_id]  # Replace user_id=1 when merge
            )

    return redirect('group_detail', recommendation_post_id=recommendation_post_id)
