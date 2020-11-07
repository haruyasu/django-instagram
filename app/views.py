from django.views.generic import View
from django.shortcuts import render, redirect
import requests
import json
import datetime
from django.utils.timezone import localtime
from django.conf import settings
from .models import Insight, Post
import math


def getCreds():
    creds = dict()
    creds['access_token'] = settings.ACCESS_TOKEN
    creds['instagram_account_id'] = settings.INSTAGRAM_ACCOUNT_ID
    creds['graph_domain'] = 'https://graph.facebook.com/'
    creds['graph_version'] = 'v8.0'
    creds['endpoint_base'] = creds['graph_domain'] + creds['graph_version'] + '/'
    creds['ig_username'] = 'hathle'
    return creds


def makeApiCall(url, endpoint_params):
    data = requests.get(url, endpoint_params)
    response = dict()
    response['url'] = url
    response['endpoint_params'] = endpoint_params
    response['endpoint_params_clean'] = json.dumps(endpoint_params, indent=4)
    response['json_data'] = json.loads(data.content)
    response['json_data_clean'] = json.dumps(response['json_data'], indent=4)
    return response


def getAccountInfo(params):
    endpointParams = dict()
    endpointParams['fields'] = 'business_discovery.username(' + params['ig_username'] + '){\
        username,website,name,ig_id,id,profile_picture_url,biography,follows_count,followers_count,\
        media_count,media{comments_count,like_count,caption,media_type,media_url,permalink,timestamp}}'
    endpointParams['access_token'] = params['access_token']
    url = params['endpoint_base'] + params['instagram_account_id']
    return makeApiCall(url, endpointParams)


def getUserInsights(params, period):
    endpointParams = dict()
    if period == 'day':
        endpointParams['metric'] = 'follower_count, profile_views'
    elif period == 'week':
        endpointParams['metric'] = 'impressions, reach'
    endpointParams['period'] = period
    endpointParams['access_token'] = params['access_token']
    url = params['endpoint_base'] + params['instagram_account_id'] + '/insights'
    return makeApiCall(url, endpointParams)


def getUserMedia(params):
    endpointParams = dict()
    endpointParams['fields'] = 'id,caption,media_type,media_url,permalink,thumbnail_url,timestamp,username,like_count,comments_count'
    endpointParams['access_token'] = params['access_token']
    url = params['endpoint_base'] + params['instagram_account_id'] + '/media'
    return makeApiCall(url, endpointParams)


def getMediaInsights(params):
    endpointParams = dict()
    endpointParams['metric'] = params['metric']
    endpointParams['access_token'] = params['access_token']
    url = params['endpoint_base'] + params['latest_media_id'] + '/insights'
    return makeApiCall(url, endpointParams)


def getHashtagInfo(params):
    endpointParams = dict()
    endpointParams['user_id'] = params['instagram_account_id']
    endpointParams['q'] = params['hashtag_name']
    endpointParams['fields'] = 'id,name'
    endpointParams['access_token'] = params['access_token']
    url = params['endpoint_base'] + 'ig_hashtag_search'
    return makeApiCall(url, endpointParams)


def getHashtagMedia(params):
    endpointParams = dict()
    endpointParams['user_id'] = params['instagram_account_id']
    endpointParams['fields'] = 'id,children,caption,name,comment_count,like_count,media_type,media_url,permalink'
    endpointParams['access_token'] = params['access_token']
    url = params['endpoint_base'] + params['hashtag_id'] + '/' + params['type']
    return makeApiCall(url, endpointParams)


class IndexView(View):
    def get(self, request, *args, **kwargs):
        params = getCreds()
        account_response = getAccountInfo(params)
        account_data = account_response['json_data']['business_discovery']
        profile_picture_url = account_data['profile_picture_url']
        username = account_data['username']
        followers_count = account_data['followers_count']
        follows_count = account_data['follows_count']
        media_count = account_data['media_count']
        media_data =  account_data['media']['data']

        today = datetime.date.today()
        obj, created = Insight.objects.update_or_create(
            label=today,
            defaults={
                'follower': followers_count,
                'follows': follows_count,
            }
        )

        like = 0
        comments = 0
        count = 1
        post_timestamp = ''
        for i in range(10):
            timestamp = localtime(datetime.datetime.strptime(media_data[i]['timestamp'], '%Y-%m-%dT%H:%M:%S%z'))
            timestamp = timestamp.strftime('%Y-%m-%d')
            if post_timestamp == timestamp:
                like += media_data[i]['like_count']
                comments += media_data[i]['comments_count']
                count += 1
            else:
                like = media_data[i]['like_count']
                comments = media_data[i]['comments_count']
                post_timestamp = timestamp

            obj, created = Post.objects.update_or_create(
                label=timestamp,
                defaults={
                    'like': like,
                    'comments': comments,
                    'count': count,
                }
            )

        latest_media_data = account_data['media']['data'][0]
        caption = latest_media_data['caption']
        media_type = latest_media_data['media_type']
        media_url = latest_media_data['media_url']
        permalink = latest_media_data['permalink']
        timestamp = localtime(datetime.datetime.strptime(latest_media_data['timestamp'], '%Y-%m-%dT%H:%M:%S%z'))
        timestamp = timestamp.strftime('%Y/%m/%d %H:%M')
        like_count = latest_media_data['like_count']
        comments_count = latest_media_data['comments_count']

        params['latest_media_id'] = latest_media_data['id']
        params['metric'] = 'engagement,impressions,reach,saved'
        media_response = getMediaInsights(params)
        media_data = []
        for media in media_response['json_data']['data']:
            media_data.append(media['values'][0]['value'])

        media_insight_data = Insight.objects.all().order_by("label")
        follower_data = []
        follows_data = []
        ff_data = []
        label_data = []
        for data in media_insight_data:
            follower_data.append(data.follower)
            follows_data.append(data.follows)
            ff = math.floor((data.follower / data.follows) * 100) / 100
            ff_data.append(ff)
            label_data.append(data.label)

        post_data = Post.objects.all().order_by("label")
        like_data = []
        comments_data = []
        count_data = []
        post_label_data = []
        for data in post_data:
            like_data.append(data.like)
            comments_data.append(data.comments)
            count_data.append(data.count)
            post_label_data.append(data.label)

        insight_data = {
            'follower_data': follower_data,
            'follows_data': follows_data,
            'ff_data': ff_data,
            'label_data': label_data,
            'like_data': like_data,
            'comments_data': comments_data,
            'count_data': count_data,
            'post_label_data': post_label_data,
        }

        return render(request, 'app/index.html', {
            'today': today.strftime('%Y-%m-%d'),
            'profile_picture_url': profile_picture_url,
            'username': username,
            'followers_count': followers_count,
            'follows_count': follows_count,
            'media_count': media_count,
            'caption': caption,
            'media_url': media_url,
            'permalink': permalink,
            'timestamp': timestamp,
            'like_count': like_count,
            'comments_count': comments_count,
            'eng': media_data[0],
            'imp': media_data[1],
            'reach': media_data[2],
            'save': media_data[3],
            'insight_data': json.dumps(insight_data)
        })

