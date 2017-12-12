import urllib.request, urllib.parse, urllib.error,urllib.request,urllib.error,urllib.parse,re,datetime,sys,http.cookiejar
import json
from pyquery import PyQuery

from models import Tweet

def get_json_response(query, start, end, refresh_cursor, cookie_jar):
    """Constructs the URL for twitter search and get response from twitter
    """
    # Base URL
    url = "https://twitter.com/i/search/timeline?f=tweets&q=%s&src=typd&%smax_position=%s"

    # Language
    urlLang = 'lang=en&'

    # Date range
    urlGetData = " since:%s until:%s %s" % (start, end, query)

    url = url % (urllib.parse.quote(urlGetData), urlLang, refresh_cursor)
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookie_jar))

    headers = [
        ('Host', "twitter.com"),
        ('User-Agent', "Mozilla/5.0 (Windows NT 6.1; Win64; x64)"),
        ('Accept', "application/json, text/javascript, */*; q=0.01"),
        ('Accept-Language', "de,en-US;q=0.7,en;q=0.3"),
        ('X-Requested-With', "XMLHttpRequest"),
        ('Referer', url),
        ('Connection', "keep-alive")
    ]
    opener.addheaders = headers

    response = opener.open(url) 
    jsonResponse = response.read()

    return json.loads(jsonResponse.decode())


def parse_tweet(json_data):
    """Parse the raw output data we get from Twitter's search results
    """
    parsed_tweets = []

    if len(json_data['items_html'].strip()) == 0:
        return parsed_tweets

    tweets = PyQuery(json_data['items_html'])('div.js-stream-tweet')

    if len(tweets) == 0:
        return parsed_tweets

    for tweet in tweets:
        tweetPQ = PyQuery(tweet)

        username_tweet = tweetPQ("span.username b").text()
        txt = re.sub(r"\s+", " ", tweetPQ("p.js-tweet-text").text().replace('# ', '#').replace('@ ', '@'));
        retweets = int(tweetPQ("span.ProfileTweet-action--retweet span.ProfileTweet-actionCount").attr("data-tweet-stat-count").replace(",", ""));
        favorites = int(tweetPQ("span.ProfileTweet-action--favorite span.ProfileTweet-actionCount").attr("data-tweet-stat-count").replace(",", ""));
        dateSec = int(tweetPQ("small.time span.js-short-timestamp").attr("data-time"));
        id = tweetPQ.attr("data-tweet-id");
        permalink = tweetPQ.attr("data-permalink-path");
        user_id = int(tweetPQ("a.js-user-profile-link").attr("data-user-id"))

        geo = ''
        geoSpan = tweetPQ('span.Tweet-geo')
        if len(geoSpan) > 0:
            geo = geoSpan.attr('title')
        urls = []
        for link in tweetPQ("a"):
            try:
                urls.append((link.attrib["data-expanded-url"]))
            except KeyError:
                pass

        t = Tweet()
        t.username = username_tweet
        t.txt = txt
        t.date = datetime.datetime.fromtimestamp(dateSec)

        parsed_tweets.append(t)

    return parsed_tweets


def search_tweets(query, start, end):
    """Searchs twitter and return a list of Tweet objects
    """

    cookie_jar = http.cookiejar.CookieJar()

    all_tweets = []

    refresh_cursor = ''
    active = True
    counter = 0
    while active:
        json_data = get_json_response(query, start, end, refresh_cursor, cookie_jar)

        refresh_cursor = json_data['min_position']
        tweets = parse_tweet(json_data)

        all_tweets = all_tweets + tweets

        if len(tweets) == 0:
            active = False

        if counter % 100 == 0:
            print("number of tweets added: %d" % len(all_tweets))

        counter = counter + 1

    return all_tweets


query = "#bitcoin"

# Time frame
start_date = datetime.datetime.strptime("2017-01-01", '%Y-%m-%d')
date_list = [start_date + datetime.timedelta(days=x) for x in range(345)]
date_list = [d.strftime("%Y-%m-%d") for d in date_list]

search_results = {}

for i in range(len(date_list) - 1):
    print("Getting tweets for ", date_list[i])

    start_time = datetime.datetime.now()
    day_results = search_tweets("#bitcoin", start=date_list[i], end=date_list[i+1])
    end_time = datetime.datetime.now()

    with open("data/" + date_list[i] + ".csv", "w") as f:
        for t in day_results:
            f.write(t.date.strftime("%Y-%m-%d %H:%M:%S") + "|" + t.txt + "\n")

    print("Took ", end_time - start_time, " seconds")
    print("Number of results for this day: ", len(search_results))

