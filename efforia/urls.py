from django.conf.urls import patterns,url,include

urlpatterns = patterns('efforia.views',    
    (r'^mosaic','mosaic'),
    (r'^config','config'),
    (r'^profile','profile'),
    (r'^basket','basket'),
    (r'^photo','photo'),
    (r'^appearance','appearance'),
    (r'^options','options'),
    (r'^place','place'),
    (r'^password','password'),
    (r'^integrations','integrations'),
    (r'^enter','authenticate'),
    (r'^leave','leave'),
    (r'^delete','delete'),
    (r'^userid','ids'),
    (r'^search','search'),
    (r'^explore','search'),
    (r'^known','explore'),
    (r'^activity','activity'),
    (r'^following','following'),
    (r'^follow','follow'),
    (r'^unfollow','unfollow'),
    (r'^twitter/post','twitter_post'),
    (r'^facebook/post','facebook_post'),
    (r'^facebook/eventcover','facebook_eventcover'),
    (r'^facebook/event','facebook_event'),
    (r'^participate','participate'),
    (r'^tutorial','tutorial'),
    (r'^pagseguro','pagseguro'),
    (r'^paypal','paypal'),
    (r'^pages','page'),
    (r'^pageview','pageview'),
    (r'^pageedit','pageedit'),
    (r'^discharge','discharge'),
    (r'^recharge','recharge'),
    (r'^balance','balance'),
    (r'^deadlines','deadlines'),
)
