#!/usr/bin/env python3
"""YouTube playlist helper — list items or reorder a playlist via the Data API v3.

Uses the dedicated YouTube OAuth token at ~/.hermes/gws/youtube_token.json
(youtube.force-ssl scope; separate from the Gmail/Drive token).

Usage:
  yt_playlist.py list PLAYLIST_ID            # show items with positions
  yt_playlist.py reorder PLAYLIST_ID NEW_ORDER   # NEW_ORDER = comma list of videoIds
  yt_playlist.py move PLAYLIST_ID VIDEO_ID NEW_POSITION

Reorder strategy: the API has no atomic reorder. Moving items one at a time
shifts positions, so this moves items from the BACK of the target order to the
front (reverse iteration), which avoids position drift. Each reorder costs ~50
quota units per moved item (10k default daily quota).
"""
import json
import sys
import time
import requests
from pathlib import Path

GWS_DIR = Path('/home/user/.hermes/gws')
API = 'https://www.googleapis.com/youtube/v3'


def get_access_token():
    creds = json.load(open(GWS_DIR / 'youtube_token.json'))
    resp = requests.post('https://oauth2.googleapis.com/token', data={
        'client_id': creds['client_id'],
        'client_secret': creds['client_secret'],
        'refresh_token': creds['refresh_token'],
        'grant_type': 'refresh_token',
    })
    if resp.status_code != 200:
        print('REFRESH ERROR:', resp.json())
        sys.exit(1)
    return resp.json()['access_token']


def list_items(playlist_id, token):
    items = []
    page_token = None
    while True:
        params = {
            'part': 'snippet,contentDetails,status',
            'playlistId': playlist_id,
            'maxResults': 50,
        }
        if page_token:
            params['pageToken'] = page_token
        r = requests.get(f'{API}/playlistItems', params=params,
                         headers={'Authorization': f'Bearer {token}'})
        if r.status_code != 200:
            print('API ERROR:', r.status_code, r.text[:500])
            sys.exit(1)
        data = r.json()
        for it in data.get('items', []):
            items.append({
                'playlistItemId': it['id'],
                'videoId': it['snippet']['resourceId']['videoId'],
                'title': it['snippet']['title'][:80],
                'position': it['snippet']['position'],
            })
        page_token = data.get('nextPageToken')
        if not page_token:
            break
    return items


def reorder(playlist_id, new_video_order, token):
    """Move playlist items to match new_video_order (list of videoIds)."""
    items = list_items(playlist_id, token)
    by_video = {it['videoId']: it for it in items}

    # sanity: same set of videos
    current = {it['videoId'] for it in items}
    requested = set(new_video_order)
    if current != requested:
        missing = current - requested
        extra = requested - current
        print(f'ERROR: order must contain exactly the same videos. '
              f'missing from order: {missing or "none"}, unknown in order: {extra or "none"}')
        sys.exit(1)

    # Move from the end of the desired order toward the front: process in
    # reverse so earlier moves don't disturb later targets.
    moves = 0
    for target_pos in range(len(new_video_order) - 1, -1, -1):
        video_id = new_video_order[target_pos]
        item = by_video[video_id]
        if item['position'] == target_pos:
            continue
        payload = {
            'id': item['playlistItemId'],
            'snippet': {
                'playlistId': playlist_id,
                'position': target_pos,
                'resourceId': {'kind': 'youtube#video', 'videoId': video_id},
            },
        }
        r = requests.put(f'{API}/playlistItems', params={'part': 'snippet'},
                         json=payload,
                         headers={'Authorization': f'Bearer {token}',
                                  'Content-Type': 'application/json'})
        if r.status_code != 200:
            print(f'MOVE ERROR at {video_id}: {r.status_code} {r.text[:300]}')
            sys.exit(1)
        moves += 1
        time.sleep(0.3)  # be gentle with quota/rate limits

    print(f'Done: {moves} moves applied to playlist {playlist_id}')


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    action = sys.argv[1]
    playlist_id = sys.argv[2]
    token = get_access_token()

    if action == 'list':
        items = list_items(playlist_id, token)
        print(f'{len(items)} items in playlist {playlist_id}:')
        for it in items:
            print(f"  {it['position']:>3} | {it['videoId']} | {it['title']}")
    elif action == 'reorder':
        order = [v.strip() for v in sys.argv[3].split(',') if v.strip()]
        reorder(playlist_id, order, token)
    elif action == 'move':
        video_id = sys.argv[3]
        new_pos = int(sys.argv[4])
        items = list_items(playlist_id, token)
        by_video = {it['videoId']: it for it in items}
        if video_id not in by_video:
            print(f'ERROR: {video_id} not in playlist')
            sys.exit(1)
        new_order = [it['videoId'] for it in items]
        new_order.remove(video_id)
        new_order.insert(new_pos, video_id)
        reorder(playlist_id, new_order, token)
    else:
        print(__doc__)
        sys.exit(1)


if __name__ == '__main__':
    main()
