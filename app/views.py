from django.views.generic import View
from django.shortcuts import render
import requests
import json
import datetime
from django.utils.timezone import localtime
from django.conf import settings
from .models import Insight
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
        response = getMediaInsights(params)
        insight_data = []
        for insight in response['json_data']['data']:
            insight_data.append(insight['values'][0]['value'])

        account_insight_data = Insight.objects.all().order_by("created")
        follower_data = []
        follows_data = []
        ff_data = []
        date_data = []
        for data in account_insight_data:
            follower_data.append(data.follower)
            follows_data.append(data.follower)
            ff = math.floor((data.follower / data.follower) * 100) / 100
            ff_data.append(ff)
            date_data.append(data.created)

        print(follower_count_data)

        return render(request, 'app/index.html', {
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
            'eng': insight_data[0],
            'imp': insight_data[1],
            'reach': insight_data[2],
            'save': insight_data[3],
        })

# class IndexView(View):
#     def get_insight_data(self, data):
#         insight_val = []
#         insight_time = []
#         for insight in data['values']:
#             insight_val.append(insight['value'])
#             end_time = localtime(datetime.datetime.strptime(insight['end_time'], '%Y-%m-%dT%H:%M:%S%z'))
#             insight_time.append(end_time.strftime('%Y/%m/%d'))
#         insight_data = {
#             'val': insight_val,
#             'time': insight_time
#         }
#         return insight_data

#     def get(self, request, *args, **kwargs):
#         params = getCreds()
#         account_response = getAccountInfo(params)
#         account_data = account_response['json_data']['business_discovery']

#         user_insight_response_day = getUserInsights(params, 'day')
#         follower_count_data = self.get_insight_data(user_insight_response_day['json_data']['data'][0])
#         profile_views_data = self.get_insight_data(user_insight_response_day['json_data']['data'][1])

#         user_insight_response_week = getUserInsights(params, 'week')
#         impressions_data = self.get_insight_data(user_insight_response_week['json_data']['data'][0])
#         reach_data = self.get_insight_data(user_insight_response_week['json_data']['data'][1])

#         return render(request, 'app/index.html', {
#             'account_data': account_data,
#             'follower_count_data': json.dumps(follower_count_data),
#             'profile_views_data': json.dumps(profile_views_data),
#             'impressions_data': json.dumps(impressions_data),
#             'reach_data': json.dumps(reach_data),
#         })


class InsightView(View):
    def get(self, request, *args, **kwargs):
        params = getCreds()
        response = getUserMedia(params)
        latest_data = response['json_data']['data'][0]
        print(latest_data)
        id = latest_data['id']
        caption = latest_data['caption']
        media_type = latest_data['media_type']
        media_url = latest_data['media_url']
        permalink = latest_data['permalink']
        timestamp = localtime(datetime.datetime.strptime(latest_data['timestamp'], '%Y-%m-%dT%H:%M:%S%z'))
        timestamp = timestamp.strftime('%Y/%m/%d %H:%M')
        username = latest_data['username']
        like_count = latest_data['like_count']
        comments_count = latest_data['comments_count']

        params['latest_media_id'] = id
        if 'VIDEO' == latest_data['media_type']:
            params['metric'] = 'engagement,impressions,reach,saved,video_views'
        else:
            params['metric'] = 'engagement,impressions,reach,saved'
        response = getMediaInsights(params)

        insight_data = []
        for insight in response['json_data']['data']:
            insight_data.append(insight['values'][0]['value'])

        return render(request, 'app/insight.html', {
            'id': id,
            'caption': caption,
            'media_type': media_type,
            'media_url': media_url,
            'permalink': permalink,
            'timestamp': timestamp,
            'username': username,
            'like_count': like_count,
            'comments_count': comments_count,
            'eng': insight_data[0],
            'imp': insight_data[1],
            'reach': insight_data[2],
            'save': insight_data[3],
        })


class HashView(View):
    def get(self, request, *args, **kwargs):
        return render(request, 'app/hash.html')
