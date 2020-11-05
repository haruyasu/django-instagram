from django.views.generic import View
from django.shortcuts import render
import requests
import json
import datetime
from django.utils.timezone import localtime
from django.conf import settings

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
    endpointParams['fields'] = 'business_discovery.username(' + params['ig_username'] + '){username,website,name,ig_id,id,profile_picture_url,biography,follows_count,followers_count,media_count}'
    endpointParams['access_token'] = params['access_token']
    url = params['endpoint_base'] + params['instagram_account_id']
    return makeApiCall(url, endpointParams)


def getUserInsights(params):
    endpointParams = dict()
    endpointParams['metric'] = 'follower_count,impressions,profile_views,reach'
    endpointParams['period'] = 'day'
    endpointParams['access_token'] = params['access_token']
    url = params['endpoint_base'] + params['instagram_account_id'] + '/insights'
    return makeApiCall(url, endpointParams)


def getUserMedia(params):
    endpointParams = dict()
    endpointParams['fields'] = 'id,caption,media_type,media_url,permalink,thumbnail_url,timestamp,username'
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
        user_insight_response = getUserInsights(params)
        follower_count_data = user_insight_response['json_data']['data'][0]

        follower_val = []
        follower_time = []
        for follower in follower_count_data['values']:
            follower_val.append(follower['value'])
            end_time = localtime(datetime.datetime.strptime(follower['end_time'], '%Y-%m-%dT%H:%M:%S%z'))
            follower_time.append(end_time.strftime('%Y/%m/%d'))
        print(follower_val)
        print(follower_time)

        impressions_data = user_insight_response['json_data']['data'][1]
        profile_views_data = user_insight_response['json_data']['data'][2]
        reach_data = user_insight_response['json_data']['data'][3]

        return render(request, 'app/index.html', {
            'account_data': account_data,
            'follower_val': follower_val,
            'follower_time': follower_time,
            'impressions_data': impressions_data,
            'profile_views_data': profile_views_data,
            'reach_data': reach_data,
        })


class InsightView(View):
    def get(self, request, *args, **kwargs):
        params = getCreds()
        response = getUserMedia(params)
        latest_data = response['json_data']['data'][0]
        id = latest_data['id']
        caption = latest_data['caption']
        media_type = latest_data['media_type']
        media_url = latest_data['media_url']
        permalink = latest_data['permalink']
        timestamp = localtime(datetime.datetime.strptime(latest_data['timestamp'], '%Y-%m-%dT%H:%M:%S%z'))
        timestamp = timestamp.strftime('%Y/%m/%d %H:%M')
        username = latest_data['username']

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
            'eng': insight_data[0],
            'imp': insight_data[1],
            'reach': insight_data[2],
            'save': insight_data[3],
        })


class HashView(View):
    def get(self, request, *args, **kwargs):
        return render(request, 'app/hash.html')
