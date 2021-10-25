from discord.ext import commands
from flask import Flask, request, redirect
import json
import os
from pyshorteners import Shortener
from splitwise import Splitwise


class Authentication(commands.Cog):
    """ Handles all authentication functions and methods. """

    def __init__ (self, bot=commands.Bot, splitwise=Splitwise(os.environ.get('SPLITWISE_CONSUMER_KEY'), os.environ.get('SPLITWISE_CONSUMER_SECRET'))):
        self.bot = bot
        self.splitwise = splitwise

    def addAccessToken(self, id, token):
        """ Adds the authenticating user's Discord ID and Access Token to the access_tokens.json file. """

        with open('modules/authentication/access_tokens.json', 'r') as json_file:
            access_tokens = json.load(json_file)

        user_index = next((i for i, item in enumerate(access_tokens) if item['id'] == id), None)
        if user_index is None: 
            access_tokens.append({"id": id, "token": token})
        else: 
            access_tokens[user_index]['token'] = token
            
        with open('modules/authentication/access_tokens.json', 'w') as json_file:
            json.dump(access_tokens, json_file, indent=4, sort_keys=True)

    async def setUser(self, context, id):
        """ Sets the current user interacting with Billwise. """

        with open('modules/authentication/access_tokens.json', 'r') as json_file:
            access_tokens = json.load(json_file)

        user_index = next((i for i, item in enumerate(access_tokens) if item['id'] == id), None)          
        if user_index is None: 
            await context.send("You are not authenticated with Splitwise. Run the `authenticate` command to connect your Splitwise account with Billwise")
        else:
            self.splitwise = Splitwise(os.environ.get('SPLITWISE_CONSUMER_KEY'), os.environ.get('SPLITWISE_CONSUMER_SECRET'), oauth2_access_token={'access_token': access_tokens[user_index]['token'], 'token_type': 'bearer'})

    @commands.command(hidden=True)
    async def resetUser(self, context=commands.Context):
        """ 
        Resets the current user interacting with Billwise.

        Usage: `.resetuser`
        """

        if await self.setUser(context, context.message.author.id):
            currentUser = self.splitwise.getCurrentUser()
            await context.send(f"Welcome, {currentUser.getFirstName()} {currentUser.getLastName()} :partying_face:")

    @commands.command(hidden=True)
    async def removeUser(self, context=commands.Context):
        """
        Removes the current user. 

        Usage: `.removeUser`
        """

        with open('modules/authentication/access_tokens.json', 'r') as json_file:
            access_tokens = json.load(json_file)

        user_index = next((i for i, item in enumerate(access_tokens) if item['id'] == context.message.author.id), None)
        if user_index is None: 
            await context.send("You are not authenticated with Splitwise. Run the `authenticate` command to connect your Splitwise account with Billwise")
        else:
            access_tokens.pop(user_index)
            with open('modules/authentication/access_tokens.json', 'w') as json_file:
                json.dump(access_tokens, json_file, indent=4, sort_keys=True)
            await context.send("You have now been removed from Billwise. I'm sorry to see you go :frowning2:")

    @commands.command()
    async def authenticate(self, context=commands.Context):
        """
        Authenticates the current user's Splitwise account.

        Usage: `.authenticate`
        """

        url, state = self.splitwise.getOAuth2AuthorizeURL("http://localhost:5000/forward_auth_code")
        url_shortener = Shortener(api_key=os.environ.get('BITLY_ACCESS_TOKEN'))
        await context.send(f"Head over to this link to authorize your Splitwise account :point_right:  {url_shortener.bitly.short(url)}")
       
       #--------------------------------------------------------------------------------------------------#
       #                     Temporary Flask Web Server to serve as a RedirectURI                         # 
       #                     for the user after authorization and to retrieve the                         #
       #                     Authorization Code.                                                          #
       #--------------------------------------------------------------------------------------------------#
        app = Flask(__name__)

        @app.route("/")
        def home():
            return """
                    <!DOCTYPE html>
                    <html>
                    <head>
                    <style>
                    .container{
                        position: absolute; 
                        top: 50%;
                        left: 50%;
                        -moz-transform: translateX(-50%) translateY(-50%);
                        -webkit-transform: translateX(-50%) translateY(-50%);
                        transform: translateX(-50%) translateY(-50%);
                    }
                    </style>
                    </head>
                    <body>
                    <div class="container">
                    <span>This is a basic web server set up to receive Splitwise Access Tokens</span>
                    </div>
                    </body>
                    </html>
                """ 

        @app.route("/forward_auth_code")
        def forward_auth_code():
            global authorization_code, authorized_state
            authorization_code, authorized_state = request.args.get('code'), request.args.get('state')

            return redirect('shutdown', code=303)

        def shutdown_server():
            func = request.environ.get('werkzeug.server.shutdown')
            if func is None:
                raise RuntimeError('Not running with the Werkzeug Server')
            func()
        
        @app.route('/shutdown', methods=['GET'])
        def shutdown():
            shutdown_server()
            return """
            <!DOCTYPE html>
            <html>
            <head>
            <style>
            .container{
                position: absolute; 
                top: 50%;
                left: 50%;
                -moz-transform: translateX(-50%) translateY(-50%);
                -webkit-transform: translateX(-50%) translateY(-50%);
                transform: translateX(-50%) translateY(-50%);
            }
            </style>
            </head>
            <body>
            <div class="container">
            <span>Your Access Token will be routed into Discord. Thanks for authenticating!</span>
            </div>
            </body>
            </html>
            """ 

        app.run()        
        #--------------------------------------------------------------------------------------------------#

        if state == authorized_state:
            print("INFO: State matches Authorized State")
            access_token =  self.splitwise.getOAuth2AccessToken(authorization_code, "http://localhost:5000/forward_auth_code")
            self.addAccessToken(context.message.author.id, access_token['access_token'])
            await self.setUser(context, context.message.author.id)
            currentUser = self.splitwise.getCurrentUser()
            await context.send(f"Welcome, {currentUser.getFirstName()} {currentUser.getLastName()} :partying_face:")
        else:
            print("ERROR: State does not match Authorized State. Retry authentication.")
            await context.send("An error has occurred during authentication. Please try again using the `authenticate` command, or contact @jakeRyder#5664")


def setup(bot=commands.Bot):
    bot.add_cog(Authentication(bot))
