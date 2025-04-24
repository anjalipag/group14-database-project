# from django.db import models
#
# # Create your models here.
# class Groups(models.Model):
#     group_id = models.AutoField(primary_key=True)
#     group_name = models.CharField(max_length=100)
#     group_photo = models.BinaryField(blank=True, null=True)
#     group_description = models.TextField(blank=True, null=True)
#     admin = models.ForeignKey('Users', models.DO_NOTHING)
#
#     class Meta:
#         managed = False
#         db_table = 'groups'
#
# class RecommendationPost(models.Model):
#     recommendation_post_id = models.AutoField(primary_key=True)
#     user = models.ForeignKey('Users', models.DO_NOTHING)
#     group = models.ForeignKey(Groups, models.DO_NOTHING)
#     recommended_item = models.ForeignKey('Recommendeditem', models.DO_NOTHING)
#     description = models.TextField()
#     up_vote_count = models.IntegerField()
#     down_vote_count = models.IntegerField()
#     overall_rating = models.IntegerField()

#     time_stamp = models.DateTimeField()
#
#     class Meta:
#         managed = False
#         db_table = 'recommendationpost'
