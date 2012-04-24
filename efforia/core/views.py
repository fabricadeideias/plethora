#!/usr/bin/python
# -*- coding: utf-8 -*-
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from models import UserProfile
from forms import RegisterForm,PasswordForm,ProfileForm
from handlers import BaseHandler
from tornado.web import HTTPError
import tornado.web
import tornado.auth
import urllib,urllib2,ast,datetime,os,stat,mimetypes,email.utils,time
import simplejson as json

class FileHandler(tornado.web.StaticFileHandler,BaseHandler):
    def get(self,path,include_body=True):
        if os.path.sep != "/":
            path = path.replace("/", os.path.sep)
        abspath = os.path.abspath(os.path.join(self.root, path))
        if not (abspath + os.path.sep).startswith(self.root):
            raise HTTPError(403, "%s is not in root static directory", path)
        if os.path.isdir(abspath) and self.default_filename is not None:
            if not self.request.path.endswith("/"):
                self.redirect(self.request.path + "/")
                return
            abspath = os.path.join(abspath, self.default_filename)
        if not os.path.exists(abspath):
            self.render(self.templates()+"404.html")
            #raise HTTPError(404)
        if not os.path.isfile(abspath):
            pass
            #self.render(self.templates()+"404.html")
            #raise HTTPError(403, "%s is not a file", path)

        stat_result = os.stat(abspath)
        modified = datetime.datetime.fromtimestamp(stat_result[stat.ST_MTIME])

        self.set_header("Last-Modified", modified)
        if "v" in self.request.arguments:
            self.set_header("Expires", datetime.datetime.utcnow() + \
                                       datetime.timedelta(days=365*10))
            self.set_header("Cache-Control", "max-age=" + str(86400*365*10))
        else:
            self.set_header("Cache-Control", "public")
        mime_type, encoding = mimetypes.guess_type(abspath)
        if mime_type:
            self.set_header("Content-Type", mime_type)

        self.set_extra_headers(path)
        ims_value = self.request.headers.get("If-Modified-Since")
        if ims_value is not None:
            date_tuple = email.utils.parsedate(ims_value)
            if_since = datetime.datetime.fromtimestamp(time.mktime(date_tuple))
            if if_since >= modified:
                self.set_status(304)
                return

        if not include_body:
            return
        file = open(abspath, "rb")
        try:
            self.write(file.read())
        finally:
            file.close()

class LoginHandler(BaseHandler):    
    def get(self):
        form = AuthenticationForm()
        if self.get_argument("error",None): form.fields['username'].errors = self.get_argument("error")
        form.fields["username"].label = "Nome"
        form.fields["password"].label = "Senha"
        self.render(self.templates()+"login.html", next=self.get_argument("next","/"), form=form)
    def post(self):
        username = self.get_argument("username", "")
        password = self.get_argument("password", "")
        auth = self.authenticate(username,password) # DB lookup here
        if auth is not None:
            self.set_current_user(username)
            self.redirect(self.get_argument("next", "/"))
        else:
            error_msg = u"?error=" + tornado.escape.url_escape("Login incorrect.")
            self.redirect(u"/login" + error_msg)
    def set_current_user(self, user):
        if user:
            self.set_cookie("user",tornado.escape.json_encode(user))
        else:
            self.clear_cookie("user")

class LogoutHandler(BaseHandler):
    def get(self):
        self.clear_cookie("user")
        self.clear_cookie("google_token")
        self.clear_cookie("twitter_token")
        self.clear_cookie("facebook_token")
        self.redirect(u"/")

class GoogleOAuth2Mixin():
    def authorize_redirect(self,client_id,redirect_uri,scope):
        oauth2_url = "https://accounts.google.com/o/oauth2/auth?"
        redirect_uri = redirect_uri; client_id = client_id; scope = scope
        oauth2_url = "%sclient_id=%s&redirect_uri=%s&scope=%s&response_type=code&access_type=offline" % (oauth2_url,client_id,redirect_uri,scope)
        self.redirect(oauth2_url)
    def get_authenticated_user(self,redirect_uri,client_id,client_secret,code):
        data = urllib.urlencode({
      		'code': 	 code,
    		'client_id': 	 client_id,
    		'client_secret': client_secret,
    		'redirect_uri':  redirect_uri,
    		'grant_type':    'authorization_code'
    	})
        return self.google_request('https://accounts.google.com/o/oauth2/token',data)
    def google_request(self,url,data):
        request = urllib2.Request(url=url,data=data)
        request_open = urllib2.urlopen(request)
        response = request_open.read()
        request_open.close()
        return response

class TwitterHandler(tornado.web.RequestHandler,
                     tornado.auth.TwitterMixin):
    @tornado.web.asynchronous
    def get(self):
        if self.get_argument("oauth_token", None):
            self.get_authenticated_user(self.async_callback(self._on_auth))
            return
        self.authenticate_redirect()

    def _on_auth(self, user):
        if not user:
            raise tornado.web.HTTPError(500, "Twitter auth failed")
        access_token = user["access_token"]
        data = urllib.urlencode({ 'twitter_token': access_token })
        self.redirect("register?%s" % data)
        self.finish()
        
class GoogleHandler(tornado.web.RequestHandler,
		    GoogleOAuth2Mixin):
    def get(self):
        if self.get_argument("code",False):
            token = self.get_authenticated_user(
				redirect_uri="http://efforia.herokuapp.com/google",
				client_id="416575314846.apps.googleusercontent.com",
				client_secret="4O7-8yKLovNcwWfN5fzA2ptD",
				code=self.get_argument("code"))
            self.redirect("register?google_token=%s" % json.loads(token)['access_token'])
        self.authorize_redirect("416575314846.apps.googleusercontent.com",
                                "http://efforia.herokuapp.com/google",
                                "https://gdata.youtube.com+https://www.googleapis.com/auth/userinfo.profile")

class FacebookHandler(tornado.web.RequestHandler,
		      tornado.auth.FacebookGraphMixin):
    @tornado.web.asynchronous
    def get(self):
        if self.get_argument("code", False):
            self.get_authenticated_user(
				redirect_uri='http://efforia.herokuapp.com/facebook',
				client_id=self.settings["facebook_api_key"],
				client_secret=self.settings["facebook_secret"],
				code=self.get_argument("code"),
				callback=self.async_callback(self._on_login))
            return
        self.authorize_redirect(redirect_uri='http://efforia.herokuapp.com/facebook',
                              		client_id=self.settings["facebook_api_key"],
		                        extra_params={"scope": "publish_stream,read_stream,user_birthday,user_events,create_event"})
    def _on_login(self, user):
        self.redirect("register?facebook_token=%s" % user['access_token'])

class RegisterHandler(BaseHandler,tornado.auth.TwitterMixin,tornado.auth.FacebookGraphMixin):
    @tornado.web.asynchronous
    def get(self):
        self.google_token = ""
        self.twitter_token = ""
        self.facebook_token = ""
        if self.get_argument("twitter_token",None):
            t = ast.literal_eval(urllib.unquote_plus(str(self.get_argument("twitter_token"))))
            self.twitter_token = "%s;%s" % (t['secret'],t['key'])
            self.twitter_request("/account/verify_credentials",access_token=t,callback=self.async_callback(self._on_response))
        elif self.get_argument("google_token",None):
            self.google_token = urllib.unquote_plus(self.get_argument("google_token"))
            url="https://www.googleapis.com/oauth2/v1/userinfo"
            request = urllib2.Request(url=url)
            request_open = urllib2.urlopen(request)
            response = request_open.read()
            request_open.close()
            self._on_response(response)
        elif self.get_argument("facebook_token",None): 
            self.facebook_token = urllib.unquote_plus(self.get_argument("facebook_token"))
            fields = ['id','first_name','last_name','link','birthday','picture']
            self.facebook_request("/me",access_token=self.facebook_token,callback=self.async_callback(self._on_response),fields=fields)
        else:
            self._on_response("") 
    def _on_response(self, response):
        if response is not "":
            dat = ast.literal_eval(str(response))
            if 'id_str' in dat:
                try: lastname = dat['name'].split()[1]
                except IndexError: lastname = ""
                data = {
                    'username':   dat['id_str'],
                    'first_name': dat['name'].split()[0],
                    'last_name':  lastname,
                    'email':      '@'+dat['screen_name'],
                    'password':   '3ff0r14',
                    'age':        13
                }
                form = RegisterForm(data=data)
                if len(User.objects.filter(username=data['username'])) < 1: self.create_user(form)
                self.login_user(data['username'],data['password'])
            elif 'id' in dat:
                age = 2012-int(dat['birthday'].split('/')[-1:][0])
                data = {
                        'username':   dat['id'],
                        'first_name': dat['first_name'],
                        'last_name':  dat['last_name'],
                        'email':      dat['link'],
                        'password':   '3ff0r14',
                        'age': age        
                }
                form = RegisterForm(data=data)
                if len(User.objects.filter(username=data['username'])) < 1: self.create_user(form)
                self.login_user(data['username'],data['password'])
        else:
            form = RegisterForm()
            return self.render(self.templates()+"register.html",form=form)
    @tornado.web.asynchronous
    def post(self):
        data = {
		    'username':self.request.arguments['username'][0],
		    'email':self.request.arguments['email'][0],
		    'password':self.request.arguments['password'][0],
		    'last_name':self.request.arguments['last_name'][0],
		    'first_name':self.request.arguments['first_name'][0],
		    'age':self.request.arguments['age'][0],
		}
        form = RegisterForm(data=data)
        if len(User.objects.filter(username=self.request.arguments['username'][0])) < 1: self.create_user(form)
        username = self.request.arguments['username'][0]
        password = self.request.arguments['password'][0]
        self.login_user(username,password)
    def create_user(self,form):
        user = User.objects.create_user(form.data['username'],
                                        form.data['email'],
                                        form.data['password'])
        user.last_name = form.data['last_name']
        user.first_name = form.data['first_name']
        user.save()
        try:
            profile = UserProfile(user=user,age=form.data['age'],
                                  twitter_token=self.twitter_token,
                                  facebook_token=self.facebook_token,
                                  google_token=self.google_token)
        except AttributeError:
            profile = UserProfile(user=user,age=form.data['age'],
                                  twitter_token="",facebook_token="",google_token="")
        profile.save()
    def login_user(self,username,password):
        auth = self.authenticate(username,password)
        if auth is not None:
            self.set_cookie("user",tornado.escape.json_encode(username))
            self.redirect("/")
        else:
            error_msg = u"?error=" + tornado.escape.url_escape("Falha no login")
            self.redirect(u"/login" + error_msg)
            
class ConfigHandler(BaseHandler):
    def get(self):
        self.render(self.templates()+'configuration.html')

class ProfileHandler(BaseHandler):
    def get(self):
        user = self.current_user()
        profile = ProfileForm()
        profile.fields['username'].initial = user.username
        profile.fields['email'].initial = user.email
        profile.fields['first_name'].initial = user.first_name
        profile.fields['last_name'].initial = user.last_name
        self.render(self.templates()+'profile.html',profile=profile)
        
class PasswordHandler(BaseHandler):
    def get(self):
        password = PasswordForm(user=self.current_user())
        password.fields['old_password'].label = 'Senha antiga'
        password.fields['new_password1'].label = 'Nova senha'
        password.fields['new_password2'].label = 'Confirmação de senha' 
        self.render(self.templates()+'password.html',password=password)