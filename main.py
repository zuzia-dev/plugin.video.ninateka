# -*- coding: utf-8 -*-

import sys
import re

PY3 = sys.version_info >= (3, 0, 0)

try:
    # For Python 3.0 and later
    from urllib.parse import urlencode, parse_qsl

    unicode = str

except ImportError:
    # Python 2
    from urlparse import parse_qsl

    from urllib import urlencode

import xbmcgui
import xbmcaddon
import xbmcplugin
import requests

base_url = sys.argv[0]
addon_handle = int(sys.argv[1])
params = dict(parse_qsl(sys.argv[2][1:]))

addon = xbmcaddon.Addon(id='plugin.video.ninateka')
PATH = addon.getAddonInfo('path')

RESOURCES = PATH + '/resources/'

ikona = RESOURCES + '../icon.png'
FANART = RESOURCES + '../fanart.jpg'

apiurl = 'https://admin.fina.gov.pl/umbraco/api/'

BASEURL = 'https://ninateka.pl'
TIMEOUT = 15
UA = 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:87.0) Gecko/20100101 Firefox/87.0'

hd = {
    'Host': 'admin.fina.gov.pl',
    'user-agent': UA,
    'accept': 'application/json, text/plain, */*',
    'accept-language': 'pl,en-US;q=0.7,en;q=0.3',
    'x-language': 'pl-pl',
    'origin': 'https://ninateka.pl',
    'dnt': '1',
    'referer': 'https://ninateka.pl/',
    'te': 'trailers',
}

sess = requests.Session()


def get_url(url, x_origin_url=None):
    if x_origin_url:
        hd.update({'x-origin-url': x_origin_url})
    response_content = sess.get(url, headers=hd, verify=False).json()
    return response_content


def encoded_dict(in_dict):
    try:
        # Python 2
        iter_dict = in_dict.iteritems
    except AttributeError:
        # Python 3
        iter_dict = in_dict.items
    out_dict = {}
    for k, v in iter_dict():
        if isinstance(v, unicode):
            v = v.encode('utf8')
        elif isinstance(v, str):

            v.decode('utf8')
        out_dict[k] = v
    return out_dict


def build_url(query):
    return base_url + '?' + urlencode(encoded_dict(query))


def add_item(url, name, image, folder, mode, infoLabels=False, isplay=True, itemcount=1, page=1):
    list_item = xbmcgui.ListItem(label=name)

    if folder:
        list_item.setProperty("IsPlayable", 'false')
    else:
        if isplay:
            list_item.setProperty("IsPlayable", 'true')
        else:
            list_item.setProperty("IsPlayable", 'false')

    if not infoLabels:
        infoLabels = {'title': name, 'plot': name}

    list_item.setInfo(type="video", infoLabels=infoLabels)
    list_item.setArt({'thumb': image, 'poster': image, 'banner': image, 'fanart': image})
    xbmcplugin.addDirectoryItem(
        handle=addon_handle,
        url=build_url({'mode': mode, 'url': url, 'page': page, 'opisb': infoLabels, 'image': image, 'title': name}),
        listitem=list_item,
        isFolder=folder)
    xbmcplugin.addSortMethod(addon_handle, sortMethod=xbmcplugin.SORT_METHOD_NONE, label2Mask="%R, %Y, %P")


def home():
    add_item('https://ninateka.pl/vod/dokument/', 'Dokument', '', True, "list_movies")
    add_item('https://ninateka.pl/vod/fabula/', 'Fabuła', '', True, "list_movies")
    add_item('https://ninateka.pl/vod/teatr/', 'Spektakl', '', True, "list_movies")
    add_item('https://ninateka.pl/vod/ksiazki-czytane/', 'Ksiązki', '', True, "list_movies")
    add_item('https://ninateka.pl/vod/rozmowy/', 'Rozmowa', '', True, "list_movies")
    add_item(apiurl + 'search?page=1&limit=48&__NodeTypeAlias.0=asset&search_tag.2=tag_1423&sort_field.5=Ascending|https://ninateka.pl/vod/', 'Dla dzieci', '', True, "list_subcategories")
    add_item(apiurl + 'search?page=1&limit=48&__NodeTypeAlias.0=asset&sort_field.5=Ascending|https://ninateka.pl/vod/', 'Wszystkie', '', True, "list_subcategories")
    add_item('https://ninateka.pl/vod/rozmowy/', 'Szukaj', '', True, "list_search")


def list_movies(xorigin):
    jsondata = get_url(apiurl + 'content', xorigin)
    ccs = jsondata.get('content', None).get('items', None)
    for cc in ccs:

        if cc.get('items', None):
            tytul = cc.get('header', None)
            id = re.findall('(\d+)', cc.get('headerUrl', None))[-1]
            urlk = apiurl + 'search?page=1&limit=48&__NodeTypeAlias.0=asset&__subCategory.2=' + str(
                id) + '&sort_field.5=Ascending|' + xorigin
            add_item(urlk, tytul, '', True, "list_subcategories")

    xbmcplugin.endOfDirectory(addon_handle)


def list_subcategories(url, pg):
    urlk, xorigin = url.split('|')
    urlk = re.sub('page=\d+\&', 'page=%d&' % int(pg), urlk)

    jsondata = get_url(urlk, xorigin)

    records = jsondata.get('records', None)
    if records:
        items = len(records)
        for rc in records:
            if rc.get("type", None) == "Article":
                continue
            opis = rc.get('description', None)
            tytul = rc.get('title', None)
            try:
                img = rc.get('image', None).get('url', None)
            except:
                img = ikona
            xorigin = rc.get('url', None)
            xorigin = BASEURL + xorigin if xorigin.startswith('/vod') else xorigin
            durat = rc.get('duration', None)  # *60
            durat = durat * 60 if durat else ''
            year = rc.get('subtitle', None)

            year = re.findall('(\d+)', year)[-1] if year else ''

            infoL = {'plot': opis, 'title': tytul, 'duration': durat, 'year': year}
            urlk = apiurl + 'content|' + xorigin
            add_item(name=tytul, url=urlk, mode='play_item', image=img, folder=False, isplay=True, infoLabels=infoL, itemcount=items)

        if int(pg) < jsondata.get('pageCount', None):
            add_item(url, 'Nast. strona', '', True, "list_subcategories", page=int(pg) + 1)
        xbmcplugin.setContent(addon_handle, 'videos')
        xbmcplugin.endOfDirectory(addon_handle)


def play_item(url):
    urlk, xorigin = url.split('|')

    jsondata = get_url(urlk, xorigin)
    atdId = jsondata.get('content', None).get('atdId', None)

    if atdId:

        urlk = apiurl + 'products/' + str(atdId) + '?platform=BROWSER'
        jsondata2 = get_url(urlk, None)

        tp = 'MOVIE'
        if jsondata2.get('video', None):
            tp = 'MOVIE'
        elif jsondata2.get('videoSlt', None):
            tp = 'MOVIE_SLT'

        if jsondata.get('content', None).get('recordType', None) == 'audio':
            urlk = apiurl + 'products/' + str(atdId) + '/audios/playlist?platform=BROWSER&videoType=' + tp
        else:

            urlk = apiurl + 'products/' + str(atdId) + '/videos/playlist?platform=BROWSER&videoType=' + tp
        jsondata = get_url(urlk, None)
        mpdurl = jsondata.get('sources', None).get('DASH', None)[0].get('src', None)
        mpdurl = 'https:' + mpdurl if mpdurl.startswith('//') else mpdurl
        licurl = jsondata.get('drm', None).get('WIDEVINE', None).get('src', None)

        hea = '&'.join(['%s=%s' % (name, value) for (name, value) in hd.items()])
        license_url = licurl + '|' + hea + '|R{SSM}|'

        import inputstreamhelper

        PROTOCOL = 'mpd'
        DRM = 'com.widevine.alpha'

        is_helper = inputstreamhelper.Helper(PROTOCOL, drm=DRM)
        if is_helper.check_inputstream():

            play_item = xbmcgui.ListItem(path=mpdurl)
            if PY3:
                play_item.setProperty('inputstream', is_helper.inputstream_addon)
            else:
                play_item.setProperty('inputstreamaddon', is_helper.inputstream_addon)

            play_item.setProperty('inputstream.adaptive.license_type', DRM)
            play_item.setProperty('inputstream.adaptive.license_key', license_url)
            play_item.setProperty('inputstream.adaptive.manifest_type', PROTOCOL)

            play_item.setMimeType('application/dash+xml')
            play_item.setProperty('inputstream.adaptive.manifest_update_parameter', 'full')
            play_item.setContentLookup(False)
            xbmcplugin.setResolvedUrl(addon_handle, True, listitem=play_item)


mode = params.get('mode', None)
fname = params.get('foldername', None)
ex_link = params.get('url', None)
page = params.get('page', '')


def router(paramstring):
    params = dict(parse_qsl(paramstring))

    if params:
        mode = params.get('mode', None)
        if mode == 'list_movies':
            list_movies(ex_link)
        elif mode == 'play_item':
            play_item(ex_link)

        elif mode == "list_subcategories":
            list_subcategories(ex_link, page)

        elif mode == "list_search":
            query = xbmcgui.Dialog().input(u'Szukaj...', type=xbmcgui.INPUT_ALPHANUM)
            if query:
                query = query.replace(' ', '+')

                urlk = apiurl + 'search?page=1&limit=48&searchPhrase.3=%s&sort_field.5=Ascending|https://ninateka.pl/vod/' % (str(query))
                list_subcategories(urlk, 1)
    else:
        home()
        xbmcplugin.endOfDirectory(addon_handle)


if __name__ == '__main__':
    router(sys.argv[2][1:])
