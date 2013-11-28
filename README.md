trello-hipchat
==============

We use Trello as online task board for iterative software development
and HipChat as visualisation tool for our development flow. For that
we need to see in the chat when tasks in Trello move. Trello-hipchat
does that by using the Trello Webhooks API and the HipChat Python
bindings.

The webhooks API requires a callback URL that gets POST request, if the
state of a Trello model changes. For that reason, trello-hipchat is a
(very, very, very) simple web application.

We run it on Heroku, so we don't have to bother with hardware or systems
administration. But you can of course run it yourself on wsgi-enabled
servers or via a reverse proxy setup.

## Installation

This describes how to get trello up an running on Heroku.

First you need to create trello-hipchat.cfg. It needs a bunch of
configuration parameters and is not very user friendly to get them. See
below for some tips.

Assuming you bootstrapped yourself as heroku user (create a heroku account, download the toolbelt, ...) do the following:

    $ git clone https://github.com/einvalentin/trello-hipchat.git
    $ cd trello-hipchat
    $ update trello-hipchat.cfg
    $ heroku login
    $ heroku create
    $ git push heroku master
    $ heroku logs
    $ heroku open

Now if you login to Trello and move some tasks, you should get messages
in your chat room.

## Configuration

The following configuration data is necessary to get this up an running:

### HipChat
* *hipchat_token*: An API token for HipChat (notification scope). You get it over at your [hipchat page](https://www.hipchat.com/admin/api). This is a ~31 character long hex string.
* *hipchat_room*: The room id of your development room. Select your room at [the rooms list on hipchat](https://uqbatedevs.hipchat.com/admin/rooms) and find the value of 'api id'. This is a short number (~6 digits)

### Trello:
* *key*: The application key to access your trello board. Get it [at your trello page](https://trello.com/1/appKey/generate). It is a 32 character hex string. See [trello docs](https://trello.com/docs/gettingstarted/#application-key) for more info.

* *secret*: The application secret is used for hmac signing of requests. You can also grab yours [at the trello page](https://trello.com/1/appKey/generate). It is called secret and is 64 bytes long. See [trello docs](https://trello.com/docs/gettingstarted/webhooks.html#triggering-webhooks) for the exact security mechanism (HMAC-SHA1)

* *token*: You need to allow trello to access your board. I did bother implementing oauth, so authenticate manually and paste the token into the app :-) Get it at [https://trello.com/1/authorize?key=*app\_key*&name=HipChat+Integration&expiration=never&response_type=token](https://trello.com/1/authorize?key=ExchangeThisForYourAppKey&name=HipChat+Integration&expiration=never&response_type=token) into your browser (replace app_key in the URL) and click "Allow". Also see [trello docs](https://trello.com/docs/api/token/) for more info.

* *board_id*: The ID of the task board that you use as a development board. We assume you have 3 lists on that board: TODO, IN_PROGRESS, DONE. We need the ids of the lists, so you can actually call them whatever. Getting the board id is a little bit messy. There is probably an easier way but I just experimented with the API and curl. Since our board belongs to an organisation, I used the organisation API to list its boards and then found the right one manually.
* *list_todo*: The list id of the list that means 'TODO' in your environment (32 byte hex string).
* *list_in_progress*: The list id of the list that means 'IN PROGRESS' in your environment.
* *list_done*: You probably get it by now...

Please contact me or do a pull request, if you know a simpler way to get boardIds, listIds, ...

### Other
* *callback_url*: This is the url that trello should call back, when your board is updated. Basically your heroku URL with "/board\_modified" appended (i.e. 'https://uqbatehipchattrello.herokuapp.com/board\_modified')


#### Play manually with the Trello API:
See [the Trello API documentation](https://trello.com/docs/api/index.html) for more info.

    # List boards of an organisation - find the ID of the right board:
    curl -i  "https://trello.com/1/organizations/uqbatedevs/boards?key=*trello_key*&token=*trello_token*"


    # List all lists of the board to find the ids of the todo in_progress or done lists:
    curl -i "https://trello.com/1/boards/*boardid*/lists?key=*trello_key*&token=*trello_token*"
