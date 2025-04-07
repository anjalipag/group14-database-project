# from django.db import models
# from groupFeed.models import RecommendationPost
#
# class Savedrecommendations(models.Model):
#     saved_recommendation_id = models.AutoField(primary_key=True)  # The composite primary key (saved_recommendation_id, user_saved_id) found, that is not supported. The first column is selected.
#     date_saved = models.DateTimeField()
#     user_posted = models.ForeignKey('Users', models.DO_NOTHING)
#     user_saved = models.ForeignKey('Users', models.DO_NOTHING, related_name='savedrecommendations_user_saved_set')
#     recommendation = models.ForeignKey(RecommendationPost, models.DO_NOTHING)
#
#     class Meta:
#         managed = False
#         db_table = 'savedrecommendations'
#         unique_together = (('saved_recommendation_id', 'user_saved'),)
