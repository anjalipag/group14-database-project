from django.shortcuts import render, redirect

# Create your views here.
from django.http import HttpResponse
from django.db import connection
from datetime import datetime
from django.urls import reverse
from django.contrib import messages
import requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

# chatGPT was used to understand how to use connection.cursor() and understand POST without model forms
def index(request):
    return HttpResponse("Hello, world. You're at the home index.")

def get_total_post_count(group_id):
    with connection.cursor() as c:
        c.execute("""SELECT COUNT(*) FROM RecommendationPost WHERE group_id = %s""", [group_id])
        count = c.fetchone()[0]
    return count

def group_feed(request, group_id):
    total_post_count = get_total_post_count(group_id)
    post_by_category ={}
    with connection.cursor() as cursor:
        #get admin id for later to check if someone has admin permissions
        cursor.execute("SELECT admin_id FROM Groups WHERE group_id = %s", [group_id])
        admin_id = cursor.fetchone()[0]


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
        WHERE rp.group_id = %s
        ORDER BY c.category_name, rp.time_stamp DESC""", [group_id])
        rows = cursor.fetchall()
        cursor.execute("SELECT group_name FROM Groups WHERE group_id = %s", [group_id])
        group_title = cursor.fetchone()[0]
        cursor.execute("SELECT group_description FROM Groups WHERE group_id = %s", [group_id])
        group_des = cursor.fetchone()[0]

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
            'posted_by_id': row[10],
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
        'group_title': group_title,
        'group_des': group_des,
        'total_posts': total_post_count,
        'category_posts': post_by_category,
        'category_names': category_names,
        'admin_id': admin_id,
        'user_id':request.session.get('user_id'),
    }

    return render(request, 'group_feed.html', context)

def serve_group_image(request, group_id):

    with connection.cursor() as c:
        c.execute("SELECT group_photo FROM groups WHERE group_id = %s", [group_id])
        row = c.fetchone()

    if row and row[0]:
        return HttpResponse(row[0], content_type='image/jpeg')  # or image/png
    else:
        # Fallback image
        from django.shortcuts import redirect
        return redirect("https://via.placeholder.com/400x200.png?text=No+Image")

def group_detail(request, recommendation_post_id, group_id = None):
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
        extra_info = get_extra_info(recommendation_post_id)
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
            'extra_info': extra_info
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
        'group_id': group_id
    }

    return render(request, 'group_detail.html', context)

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

def save_recc(request, recommendation_post_id, posted_by_id, group_id):
    if request.method == 'POST':
        user_saved_id = request.session.get('user_id')
        print("RECC ID", recommendation_post_id)
        date_saved = datetime.now()

        with connection.cursor() as cursor:
            cursor.execute("""
            SELECT * FROM SavedRecommendations WHERE user_saved_id = %s AND recommendation_id = %s""",
                           [user_saved_id, recommendation_post_id])
            rows = cursor.fetchall()
            number_of_rows = len(rows)

        if number_of_rows == 0:
            with connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO SavedRecommendations (date_saved, user_posted_id, user_saved_id, recommendation_id)
                    VALUES (%s, %s, %s, %s)
                """, [date_saved, posted_by_id, user_saved_id, recommendation_post_id])
    messages.success(request, "Successfully saved recommendation!")
    return redirect('group_feed', group_id=group_id)


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
        external_id = request.POST.get('external_api_id')


        # Get category_id from category_name
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT category_id FROM Category WHERE category_name = %s",
                [category_name]
            )
            row = cursor.fetchone()
            category_id = row[0]

        #checki if recommended item has already been recommended on before; if so, don't make another item
        with connection.cursor() as c:
            c.execute(
                """SELECT recommended_item_id FROM RecommendedItem WHERE category_id = %s AND external_id = %s""",[category_id, external_id]
            )
            existing_item = c.fetchone()


        # Insert into RecommendedItem
        if existing_item:
            recommended_item_id = existing_item[0]
        else:
            with connection.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO RecommendedItem (title, category_id, external_id) VALUES (%s, %s, %s) RETURNING recommended_item_id",
                    [title, category_id, external_id]
                )
                recommended_item_id= cursor.fetchone()[0]

                insert_into_category(category_name, external_id, recommended_item_id,title)


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

def insert_into_category(category_name, external_id, recommended_item_id, title):
    with connection.cursor() as cursor:
        if category_name == "Movies":
            movie_tbl_data = search_omdb_by_id_for_extra_info(external_id, "Movies")

            cursor.execute(
                """INSERT INTO Movie (director, duration, recommended_item_id, rated, plot) VALUES (%s, %s, %s, %s, %s)""",
                [movie_tbl_data['director'], movie_tbl_data['duration'], recommended_item_id, movie_tbl_data['rated'], movie_tbl_data['plot']]
            )
        if category_name == "TV Shows":
            tv_show_data = search_omdb_by_id_for_extra_info(external_id, "TV Shows")

            cursor.execute(
                """INSERT INTO TVShow (director, season_count, recommended_item_id, rated, plot) VALUES (%s, %s, %s, %s, %s)""",
                [tv_show_data['director'], tv_show_data['season_count'], recommended_item_id,  tv_show_data['rated'], tv_show_data['plot']]
            )
        if category_name == "Music":
            music_tbl_data = search_deezer_by_id_for_extra_info(title,external_id)
            #need to cast to type interval for our DB type check
            duration_secs = music_tbl_data['duration']
            mins = duration_secs // 60
            seconds = duration_secs % 60
            cursor.execute( """INSERT INTO Song (artist, duration, recommended_item_id, album) VALUES (%s, %s, %s, %s)""",
                [music_tbl_data['artist'],f"{mins} minutes {seconds} seconds", recommended_item_id, music_tbl_data['album']])

        if category_name == "Books":
            books_tbl_data = search_openlibrary_by_id_for_extra_info(title, external_id)
            cursor.execute("""INSERT INTO Book (author, year_published, recommended_item_id) VALUES (%s, %s, %s)""",
                           [books_tbl_data['author'], books_tbl_data['year_published'], recommended_item_id])


def save_recc_det(request, recommendation_post_id, posted_by_id):
    if request.method == 'POST':
        user_saved_id = request.session.get('user_id')
        print("RECC ID", recommendation_post_id)
        date_saved = datetime.now()


        with connection.cursor() as cursor:
            cursor.execute("""
            SELECT * FROM SavedRecommendations WHERE user_saved_id = %s AND recommendation_id = %s""", [user_saved_id, recommendation_post_id])
            rows = cursor.fetchall()
            number_of_rows = len(rows)

        if number_of_rows == 0:
            with connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO SavedRecommendations (date_saved, user_posted_id, user_saved_id, recommendation_id)
                    VALUES (%s, %s, %s, %s)
                """, [date_saved, posted_by_id, user_saved_id, recommendation_post_id])

    messages.success(request, "Successfully saved recommendation!")
    return redirect('group_detail', recommendation_post_id=recommendation_post_id)



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
    uid = request.session.get('user_id')
    with connection.cursor() as c:
        #This is to see how the user has/has not voted
        c.execute("""SELECT vote_type FROM voting WHERE user_id = %s AND recommendation_post = %s""", [uid, recommendation_post_id])
        row = c.fetchone()

        #If the user has never voted, they can add a vote
        if row is None:
            c.execute("""INSERT INTO voting(user_id,recommendation_post, vote_type) VALUES(%s, %s, 'Upvoted')""", [uid, recommendation_post_id])
            c.execute("""UPDATE RecommendationPost SET up_vote_count = up_vote_count + 1 WHERE recommendation_post_id = %s""", [recommendation_post_id])

        #If they've downvoted before, change their vote
        elif row[0] == 'Downvoted':
            c.execute("""UPDATE voting SET vote_type = 'Upvoted' WHERE user_id = %s AND recommendation_post = %s""", [uid, recommendation_post_id])

            c.execute("""UPDATE RecommendationPost SET up_vote_count = up_vote_count + 1, down_vote_count = down_vote_count - 1 WHERE recommendation_post_id = %s""", [recommendation_post_id])

        elif row[0] == 'Upvoted':
            #Shouldn't be able to upvote again
            pass

    #Reload page
    return redirect('group_detail', recommendation_post_id=recommendation_post_id)

def handle_downvote(request, recommendation_post_id):
    uid = request.session.get('user_id')
    with connection.cursor() as c:
        # This is to see how the user has/has not voted
        c.execute("""SELECT vote_type FROM voting WHERE user_id = %s AND recommendation_post = %s""",
                  [uid, recommendation_post_id])
        row = c.fetchone()

        # If the user has never voted, they can add a vote
        if row is None:
            c.execute("""INSERT INTO voting(user_id,recommendation_post, vote_type) VALUES(%s, %s, 'Downvoted')""",
                      [uid, recommendation_post_id])
            c.execute(
                """UPDATE RecommendationPost SET down_vote_count = down_vote_count + 1 WHERE recommendation_post_id = %s""",
                [recommendation_post_id])

        # If they've upvoted before, change their vote
        elif row[0] == 'Upvoted':
            c.execute("""UPDATE voting SET vote_type = 'Downvoted' WHERE user_id = %s AND recommendation_post = %s""",
                      [uid, recommendation_post_id])

            c.execute(
                """UPDATE RecommendationPost SET down_vote_count = down_vote_count + 1, up_vote_count = up_vote_count - 1 WHERE recommendation_post_id = %s""",
                [recommendation_post_id])

        elif row[0] == 'Downvoted':
            # Shouldn't be able to downvote again
            pass

    # Reload page
    return redirect('group_detail', recommendation_post_id=recommendation_post_id)

def delete_post(request, post_id):
    if request.method == "POST":
        uid = request.session.get("user_id")
        with connection.cursor() as c:
            c.execute("""SELECT g.group_id, g.admin_id FROM Groups g JOIN RecommendationPost rp ON g.group_id = rp.group_id
            WHERE rp.recommendation_post_id = %s""", [post_id])
            result = c.fetchone()

            #make sure the user is the admin of the group
            if result:
                group_id, admin_id = result
                if uid == admin_id:
                    c.execute("DELETE FROM RecommendationPost WHERE recommendation_post_id = %s", [post_id])
                return redirect('group_feed', group_id=group_id)

    return redirect('/')

    return redirect('group_feed.html', recommendation_post_id=recommendation_post_id)

def admin_delete_comment(request, comment_id, post_id):
        user_id = request.session.get("user_id")

        with connection.cursor() as c:
            c.execute("""SELECT rp.group_id FROM Comment c JOIN RecommendationPost rp ON c.recommendation_post_id = rp.recommendation_post_id WHERE c.comment_id = %s""", [comment_id])
            row=c.fetchone()
            if not row:
                return redirect('group_detail', recommendation_post_id = post_id)
            group_id = row[0]

            c.execute("SELECT admin_id FROM Groups WHERE group_id = %s", [group_id])
            admin_id = c.fetchone()[0]

            #confirm can only delete if current user is the admin
            if user_id == admin_id:
                c.execute("DELETE FROM Comment WHERE comment_id = %s", [comment_id])

        return redirect('group_detail', recommendation_post_id=post_id)


@csrf_exempt
def search_deezer(request):
    if request.method == 'GET':
        query = request.GET.get('query', '')
        if not query:
            return JsonResponse({'error': 'Missing query'}, status=400)

        response = requests.get(f'https://api.deezer.com/search?q={query}')
        data = response.json()

        tracks = []
        for item in data.get('data', []):
            tracks.append({
                'title': item['title'],
                'artist': item['artist']['name'],
                'album': item['album']['title'],
                'preview_url': item['preview'],
                'deezer_url': item['link'],
                'api_id': item['id']
            })

        return JsonResponse({'tracks': tracks})
    return JsonResponse({'error': 'Only GET allowed'}, status=405)

@csrf_exempt
def search_deezer_by_id_for_extra_info(title,external_id):
    response = requests.get(f'https://api.deezer.com/search?q={title}')

    if response.status_code != 200:
        return JsonResponse({'error': f'Error: {response.status_code}'}), response.status_code

    data = response.json()
    result = {}
    for item in data.get('data', []):
        if str(item['id']) == str(external_id):
            result = {'title': item['title'],
                      'artist': item['artist']['name'],
                      'duration': item['duration'],
                        'album': item['album']['title']}

    return result


@csrf_exempt
def search_openlibrary(request):
    if request.method == 'GET':
        query = request.GET.get('query', '')
        if not query:
            return JsonResponse({'error': 'Missing query'}, status=400)

        response = requests.get(f'https://openlibrary.org/search.json?q={query}')
        data = response.json()

        books = []
        for doc in data.get('docs', [])[:10]:  # Limit to 10 results
            books.append({
                'title': doc.get('title'),
                'author': ', '.join(doc.get('author_name', [])),
                'cover_url': f"http://covers.openlibrary.org/b/id/{doc['cover_i']}-M.jpg" if 'cover_i' in doc else None,
                'openlibrary_url': f"https://openlibrary.org{doc['key']}",
                'author_key': doc.get('author_key', [None])[0],
            })

        return JsonResponse({'books': books})
    return JsonResponse({'error': 'Only GET allowed'}, status=405)

@csrf_exempt
def search_openlibrary_by_id_for_extra_info(title,external_id):
    response = requests.get(f'https://openlibrary.org/search.json?q={title}')


    if response.status_code != 200:
        return JsonResponse({'error': f'Error: {response.status_code}'}), response.status_code

    data = response.json()
    result = {}

    for doc in data.get('docs', [])[:10]:  # Limit to 10 results
        if external_id in doc.get('author_key', []):
            author = ', '.join(doc.get('author_name', [])),
            if ',' in author:
                author = author.split(',')[0].strip()
            else:
                author = ', '.join(doc.get('author_name', [])),
            result = {
                'title': doc.get('title'),
                'author': author,
                'year_published': doc.get('first_publish_year')
            }


    return result



@csrf_exempt
def search_omdb_movies(request):
    if request.method == 'GET':
        query = request.GET.get('query', '')
        if not query:
            return JsonResponse({'error': 'Missing query'}, status=400)


        response = requests.get(f'https://www.omdbapi.com/?apikey={settings.OMDB_KEY}&s={query}')
        data = response.json()

        if data.get('Response') == 'False':
            return JsonResponse({'error': data.get('Error', 'Movie not found')}, status = 404)

        movies = []
        for movie in data.get('Search', [])[:10]:
            if movie.get("Type") == "movie":
                movies.append({
                    'title': movie.get('Title'),
                    'year': movie.get('Year', []),
                     'imdbID' : movie.get('imdbID'),
                })

        return JsonResponse({'movies': movies})
    return JsonResponse({'error': 'Only GET allowed'}, status=405)

def search_omdb_shows(request):
    if request.method == 'GET':
        query = request.GET.get('query', '')
        if not query:
            return JsonResponse({'error': 'Missing query'}, status=400)

        response = requests.get(f'https://www.omdbapi.com/?apikey={settings.OMDB_KEY}&s={query}')
        data = response.json()

        if data.get('Response') == 'False':
            return JsonResponse({'error': data.get('Error', 'Show not found')}, status=404)

        shows = []
        for show in data.get('Search', [])[:10]:  # Limit to 10 results
            if show.get('Type') == "series":
                shows.append({
                    'title': show.get('Title'),
                    'year': show.get('Year', []),
                    'imdbID' : show.get('imdbID'),
                })

        return JsonResponse({'shows': shows})
    return JsonResponse({'error': 'Only GET allowed'}, status=405)

def search_omdb_by_id_for_extra_info(imdbid, category):
    response = requests.get(f'https://www.omdbapi.com/?apikey={settings.OMDB_KEY}&i={imdbid}')
    data = response.json()
    result = {}

    if data.get('Response') == 'False':
        return JsonResponse({'error': data.get('Error', 'Nothing found')}, status=404)

    if(category == "Movies"):
        #Need to do this so we don't have multiple values in column (goes against normal forms)
        director = data.get('Director')
        if ',' in director:
            director = director.split(',')[0].strip()
        else:
            director = data.get('Director')
        result = {'title': data.get('Title'),
                  'director': director,
                'duration': data.get('Runtime'),
                  'rated': data.get('Rated'),
                  'plot': data.get('Plot'),
                  }

    if(category == "TV Shows"):
        # Need to do this so we don't have multiple values in column (goes against normal forms)
        if ',' in data.get('Director'):
            director = director.split(',')[0].strip()
        else:
            director = data.get('Director')
        result = {'title': data.get('Title'),
                'director': director,
                'season_count': data.get('totalSeasons'),
                  'rated': data.get('Rated'),
                  'plot': data.get('Plot')
                  }


    return result




