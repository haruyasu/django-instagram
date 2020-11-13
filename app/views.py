from django.views.generic import View
from django.shortcuts import render
import requests
import json
import datetime
from django.utils.timezone import localtime
from django.conf import settings
from .models import Insight, Post
import math


# Instagram Graph API認証情報
def get_credentials():
    credentials = dict()
    credentials['access_token'] = settings.ACCESS_TOKEN
    credentials['instagram_account_id'] = settings.INSTAGRAM_ACCOUNT_ID
    credentials['graph_domain'] = 'https://graph.facebook.com/'
    credentials['graph_version'] = 'v8.0'
    credentials['endpoint_base'] = credentials['graph_domain'] + credentials['graph_version'] + '/'
    credentials['ig_username'] = 'hathle'
    return credentials


# Instagram Graph APIコール
def call_api(url, endpoint_params):
    # API送信
    data = requests.get(url, endpoint_params)
    response = dict()
    # API送信結果をjson形式で保存
    response['json_data'] = json.loads(data.content)
    return response

# ユーザーアカウント情報取得
def get_account_info(params):
    # エンドポイント
    # https://graph.facebook.com/{graph-api-version}/{ig-user-id}?fields={fields}&access_token={access-token}

    endpoint_params = dict()
    # ユーザ名、プロフィール画像、フォロワー数、フォロー数、投稿数、メディア情報取得
    endpoint_params['fields'] = 'business_discovery.username(' + params['ig_username'] + '){\
        username,profile_picture_url,follows_count,followers_count,media_count,\
        media.limit(10){comments_count,like_count,caption,media_url,permalink,timestamp}}'
    endpoint_params['access_token'] = params['access_token']
    url = params['endpoint_base'] + params['instagram_account_id']
    return call_api(url, endpoint_params)


# 特定メディアIDのインサイト取得
def get_media_insights(params):
    # エンドポイント
    # https://graph.facebook.com/{graph-api-version}/{ig-media-id}/insights?metric={metric}&access_token={access-token}

    endpoint_params = dict()
    # エンゲージメント、インプレッション、リーチ、保存情報取得
    endpoint_params['metric'] = 'engagement,impressions,reach,saved'
    endpoint_params['access_token'] = params['access_token']
    url = params['endpoint_base'] + params['media_id'] + '/insights'
    return call_api(url, endpoint_params)


# ハッシュタグ検索
def get_hashtag_id(params):
    # エンドポイント
    # https://graph.facebook.com/{graph-api-version}/ig_hashtag_search?user_id={user-id}&q={hashtag-name}&fields={fields}&access_token={access-token}

	endpoint_params = dict()
	endpoint_params['user_id'] = params['instagram_account_id']
    # 指定ハッシュタグ
	endpoint_params['q'] = params['hashtag_name']
	endpoint_params['fields'] = 'id,name'
	endpoint_params['access_token'] = params['access_token']
	url = params['endpoint_base'] + 'ig_hashtag_search'
	return call_api(url, endpoint_params)


def get_hashtag_media(params):
    # エンドポイント 評価順
    # https://graph.facebook.com/{graph-api-version}/{ig-hashtag-id}/top_media?user_id={user-id}&fields={fields}

	endpoint_params = dict()
	endpoint_params['user_id'] = params['instagram_account_id']
	endpoint_params['fields'] = 'id,media_type,media_url,children{media_url},permalink,caption,like_count,comments_count,timestamp'
	endpoint_params['access_token'] = params['access_token']
	url = params['endpoint_base'] + params['hashtag_id'] + '/top_media'
	return call_api(url, endpoint_params)


class IndexView(View):
    def get(self, request, *args, **kwargs):
        # Instagram Graph API認証情報取得
        params = get_credentials()
        # アカウント情報取得
        account_response = get_account_info(params)
        business_discovery = account_response['json_data']['business_discovery']
        account_data = {
            'profile_picture_url': business_discovery['profile_picture_url'],
            'username': business_discovery['username'],
            'followers_count': business_discovery['followers_count'],
            'follows_count': business_discovery['follows_count'],
            'media_count': business_discovery['media_count'],
        }

        # 本日の日付
        today = datetime.date.today()
        # Insightデーターベースに保存
        obj, created = Insight.objects.update_or_create(
            label=today,
            defaults={
                'follower': business_discovery['followers_count'],
                'follows': business_discovery['follows_count'],
            }
        )

        # Insightデーターベースからデータを取得
        # order_byで昇順に並び替え
        media_insight_data = Insight.objects.all().order_by("label")
        follower_data = []
        follows_data = []
        ff_data = []
        label_data = []
        for data in media_insight_data:
            # フォロワー数
            follower_data.append(data.follower)
            # フォロー数
            follows_data.append(data.follows)
            # フォロー数、フォロワー数比率(小数点2桁)
            ff = math.floor((data.follower / data.follows) * 100) / 100
            ff_data.append(ff)
            # ラベル
            label_data.append(data.label)

        # アカウント情報から投稿情報を取得
        like = 0
        comments = 0
        count = 1
        post_timestamp = ''
        for data in business_discovery['media']['data']:
            # 投稿日取得
            timestamp = localtime(datetime.datetime.strptime(data['timestamp'], '%Y-%m-%dT%H:%M:%S%z')).strftime('%Y-%m-%d')
            # 同じ日に複数の投稿がある場合、各データを足していく
            if post_timestamp == timestamp:
                like += data['like_count']
                comments += data['comments_count']
                count += 1
            else:
                like = data['like_count']
                comments = data['comments_count']
                post_timestamp = timestamp

            # 投稿データベースに保存
            obj, created = Post.objects.update_or_create(
                label=timestamp,
                defaults={
                    'like': like,
                    'comments': comments,
                    'count': count,
                }
            )

        # Postデーターベースからデータを取得
        # order_byで昇順に並び替え
        post_data = Post.objects.all().order_by("label")
        like_data = []
        comments_data = []
        count_data = []
        post_label_data = []
        for data in post_data:
            # いいね数
            like_data.append(data.like)
            # コメント数
            comments_data.append(data.comments)
            # 投稿数
            count_data.append(data.count)
            # ラベル
            post_label_data.append(data.label)

        # アカウントのインサイトデータ
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

        # 最新の投稿情報を取得
        latest_media_data = business_discovery['media']['data'][0]
        params['media_id'] = latest_media_data['id']
        media_response = get_media_insights(params)
        media_data = media_response['json_data']['data']

        # メディアのインサイトデータ
        insight_media_data = {
            'caption': latest_media_data['caption'],
            'media_url': latest_media_data['media_url'],
            'permalink': latest_media_data['permalink'],
            'timestamp': localtime(datetime.datetime.strptime(latest_media_data['timestamp'], '%Y-%m-%dT%H:%M:%S%z')).strftime('%Y/%m/%d %H:%M'),
            'like_count': latest_media_data['like_count'],
            'comments_count': latest_media_data['comments_count'],
            'engagement': media_data[0]['values'][0]['value'],
            'impression': media_data[1]['values'][0]['value'],
            'reach': media_data[2]['values'][0]['value'],
            'save': media_data[3]['values'][0]['value'],
        }

        return render(request, 'app/index.html', {
            'today': today.strftime('%Y-%m-%d'),
            'account_data': account_data,
            'insight_data': json.dumps(insight_data),
            'insight_media_data': insight_media_data,
        })

class HashtagView(View):
    def get(self, request, *args, **kwargs):
        # Instagram Graph API認証情報取得
        params = get_credentials()

        # ハッシュタグ設定
        params['hashtag_name'] = 'デイトラ'

        # ハッシュタグID取得
        hashtag_id_respinse = get_hashtag_id(params)

        # ハッシュタグID設定
        params['hashtag_id'] = hashtag_id_respinse['json_data']['data'][0]['id'];

        # ハッシュタグ検索
        hashtag_media_response = get_hashtag_media(params)


        print(hashtag_media_response)


        return render(request, 'app/hashtag.html', {

        })
