#!/usr/bin/env python3
#Jellyfin - https://jellyfin.org/
#JellyPoster - https://www.mattsshack.com/JellyPoster/
#Release Version 0.0.2
#  Update Uses API & username only (no password or authentication required).
#  Update Code Opimizations. I am sure there is still a lot more to do... :)
#  Add    Experimental CEC Control 
#  Add    Live TV Channel (Only show logo of channel being played)
#  Add    Top Text Idle / PLaying Options
#  Add    Bottom Text Idle / PLaying Options

#Install Python Dependencies
#CEC TV Control
#sudo apt-get install libcec-dev
#sudo pip3 install cec

#Note
#I currently run the JellyPoster Service on my main server and view it via a web broswer installed on a serprate Raspberry Pi connected to a display.
#You should be able to run the JellyPoster Service and web broswer on a single Raspberry Pi / Computer.

#Credits
#666Warlock666 - Version that uses API & username only (no password or authentication required).

###################### START CONFIGURATION ######################
#Jellyfin Server Configuration
jellyfin_url = "http://192.168.1.10:8096"              #Jellyfin Server URL with Port. Example: "http://192.168.1.10:8096" Default Port 8096
jellyfin_username = "[USERNAME]"                       #Jellyfin Server Username
jellyfin_api_key = "[API Key]"                         #Jellyfin Server API Key

#Jellyfin Client Configuration
jellyfin_client_ip = "[CLIENT IP]"                    #The JellyPoster display will updated when this IP Address is seen playing content (Example: Your Roku, Firestick, Nvidia Shield, etc.). 

#JellyPoster Configuration
#CEC TV Controls (Experimental)
#This only works if you Raspberry Pi / Computer is connected to the TV via HDMI and the TV has CEC is enabled. Not all TV will be compatabile. 
jellyposter_cec = "False"                              #True = Enabled / False = Disabled (Default)
jellyposter_cec_schedule_enable = "False"              #True = Enabled / False = disabled (Default)
jellyposter_cec_schedule_start_time = "08:00"          #Start time for CEC Schedule. 24 hour clock time.
jellyposter_cec_schedule_end_time = "23:00"            #End time for CEC Schedule. 24 hour clock time.

#Web Server Configuration
jellyposter_host = "[JELLYPOSTER SERVER IP]"           #IP Address of the machine running JellyPoster Service
jellyposter_port = 4242                                #Port you want JellyPoster to listen on. Default 4242
jellyposter_refresh = "20"                             #How ofter to refresh and change for diaplsy changes. Default 20

#Top Text Idle
jellyposter_top_text_idle = "Coming Soon"
jellyposter_top_text_idle_font = "Arial"
jellyposter_top_text_idle_font_size = "70px"
jellyposter_top_text_idle_font_color = "#FFFF00"
jellyposter_top_text_idle_font_backgroundcolor = "#000000"

#Top Text Playing
jellyposter_top_text_playing = "Now Playing"
jellyposter_top_text_playing_font = "Arial"
jellyposter_top_text_playing_font_size = "65px"
jellyposter_top_text_playing_font_color = "#FFFF00"
jellyposter_top_text_playing_font_backgroundcolor = "#000000"

#Bottom Text Idle
jellyposter_bottom_text_idle = "www.mattsshack.com"  # You will want to change this :)
jellyposter_bottom_text_idle_font = "Arial"
jellyposter_bottom_text_idle_font_size = "70px"
jellyposter_bottom_text_idle_font_color = "#FFFFFF"
jellyposter_bottom_text_idle_font_backgroundcolor = "#000000"

#Bottom Text Playing
jellyposter_bottom_text_playing_font = "Arial"
jellyposter_bottom_text_playing_font_size = "25px"
jellyposter_bottom_text_playing_font_color = "#FFFFFF"
jellyposter_bottom_text_playing_font_backgroundcolor = "#000000"
####################### END CONFIGURATION #######################

#Imports
import requests, json, os, sys, time, cec
from urllib.parse import urlparse
from http.server import HTTPServer, BaseHTTPRequestHandler

#get userId
def get_userid():
    response = requests.get(f'{jellyfin_url}/Users?api_key={jellyfin_api_key}')
    print(response.status_code)
    for userid in response.json():
        if userid.get('Name') == jellyfin_username:
            jellyfin_userid= userid.get('Id')
            return(jellyfin_userid)

#JellyPoster HTTP Server
class JellyPosterHTTP(BaseHTTPRequestHandler):
    def do_GET(self):

        #CEC Check
        if jellyposter_cec == "True":
            check_CEC()

        http_path = self.path
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()

        if http_path == "/":
            #Check for Playing
            jellyfin_client_match = check_PLAYING()
            if jellyfin_client_match == "true":
                jellyposter_top, jellyposter_middle, jellyposter_bottom = get_PLAYING()

                self.wfile.write(bytes(f"<html style='height: 100%; overflow: hidden;'>", "utf-8"))
                self.wfile.write(bytes(f"   <head><title>JellyPoster</title><meta http-equiv='refresh' content='{jellyposter_refresh}'></head>", "utf-8"))
                self.wfile.write(bytes(f"   <body style='background-color: black; color: white; font-size: large; font-family: Arial, Helvetica, sans-serif;'>", "utf-8"))
                self.wfile.write(bytes(f"      <div id='wrapper' style='height: 100%; display: flex; flex-direction: column;'>", "utf-8"))
                self.wfile.write(bytes(f"         <top style='height: 10%; display: flex; justify-content: center; align-items: center; background-color: {jellyposter_top_text_playing_font_backgroundcolor}; color: {jellyposter_top_text_playing_font_color}; font-size: {jellyposter_top_text_playing_font_size}; font-family: {jellyposter_top_text_playing_font}'> {jellyposter_top} </top>", "utf-8"))
                self.wfile.write(bytes(f"         <middle style='height: 80%; background-position: 50% 50%; background-size: contain; background-repeat: no-repeat;'> <img style='height: 100%; width: 100%; object-fit: contain' src='{jellyposter_middle}'></middle>", "utf-8"))
                self.wfile.write(bytes(f"         <bottom style='height: 10%; display: flex; justify-content: center; align-items: center; background-color: {jellyposter_bottom_text_playing_font_backgroundcolor}; color: {jellyposter_bottom_text_playing_font_color}; font-size: {jellyposter_bottom_text_playing_font_size}; font-family: {jellyposter_bottom_text_playing_font}'> {jellyposter_bottom} </bottom>", "utf-8"))
                self.wfile.write(bytes(f"      </div>", "utf-8"))
                self.wfile.write(bytes(f"   </body>", "utf-8"))
                self.wfile.write(bytes(f"</html>", "utf-8"))

            else:
                jellyposter_top, jellyposter_middle, jellyposter_bottom = get_RANDOM()

                self.wfile.write(bytes(f"<html style='height: 100%; overflow: hidden;'>", "utf-8"))
                self.wfile.write(bytes(f"   <head><title>JellyPoster</title><meta http-equiv='refresh' content='{jellyposter_refresh}'></head>", "utf-8"))
                self.wfile.write(bytes(f"   <body style='background-color: black; color: white; font-size: large; font-family: Arial, Helvetica, sans-serif;'>", "utf-8"))
                self.wfile.write(bytes(f"      <div id='wrapper' style='height: 100%; display: flex; flex-direction: column;'>", "utf-8"))
                self.wfile.write(bytes(f"         <top style='height: 10%; display: flex; justify-content: center; align-items: center; background-color: {jellyposter_top_text_idle_font_backgroundcolor}; color: {jellyposter_top_text_idle_font_color}; font-size: {jellyposter_top_text_idle_font_size}; font-family: {jellyposter_top_text_idle_font}'> {jellyposter_top} </top>", "utf-8"))
                self.wfile.write(bytes(f"         <middle style='height: 80%; background-position: 50% 50%; background-size: contain; background-repeat: no-repeat;'> <img style='height: 100%; width: 100%; object-fit: contain' src='{jellyposter_middle}'></middle>", "utf-8"))
                self.wfile.write(bytes(f"         <bottom style='height: 10%; display: flex; justify-content: center; align-items: center; background-color: {jellyposter_bottom_text_idle_font_backgroundcolor}; color: {jellyposter_bottom_text_idle_font_color}; font-size: {jellyposter_bottom_text_idle_font_size}; font-family: {jellyposter_bottom_text_idle_font}'> {jellyposter_bottom} </bottom>", "utf-8"))
                self.wfile.write(bytes(f"      </div>", "utf-8"))
                self.wfile.write(bytes(f"   </body>", "utf-8"))
                self.wfile.write(bytes(f"</html>", "utf-8"))

#Check if Client is Playing
def check_PLAYING():
    jellyfin_client_match = "false"

    playing_devices = requests.get(f'{jellyfin_url}/Sessions?ActiveWithinSeconds=90&api_key={jellyfin_api_key}')
    for playing_device in playing_devices.json():
        if playing_device.get('NowPlayingItem'):

            #Check Remote IP for match with Client IP
            print(playing_device.get('RemoteEndPoint'))
            if (playing_device.get('RemoteEndPoint') == jellyfin_client_ip):
                jellyfin_client_match = "true"

    return jellyfin_client_match

#JellyPoster Get Jellyfin Current Playing Devices
def get_PLAYING():
    playing_devices = requests.get(f'{jellyfin_url}/Sessions?ActiveWithinSeconds=90&api_key={jellyfin_api_key}')
    for playing_device in playing_devices.json():
        #print(playing_device) #Used for Debugging
        if playing_device.get('NowPlayingItem'):

            #Check Remote IP for match with Client IP
            if (playing_device.get('RemoteEndPoint') == jellyfin_client_ip):
                jellyfin_playback_type = playing_device['NowPlayingItem']['Type']

                #Episode Display
                if (jellyfin_playback_type == 'Episode'):
                    print('Client Playing a TV Episode')

                    #Setup Variable
                    jellyfin_episode_name = playing_device['NowPlayingItem']['SeriesName']
                    jellyfin_episode_id = playing_device['NowPlayingItem']['SeriesId']
                    jellyfin_episode_overview = playing_device['NowPlayingItem']['Overview']

                    jellyfin_playback_poster = (f'{jellyfin_url}/items/{jellyfin_episode_id}/Images/Primary')

                    jellyposter_top = jellyposter_top_text_playing
                    jellyposter_middle = jellyfin_playback_poster
                    jellyposter_bottom =  jellyfin_episode_name + " - " + jellyfin_episode_overview

                    return jellyposter_top, jellyposter_middle, jellyposter_bottom;

                #Movie Display
                if (jellyfin_playback_type == 'Movie'):
                    print('Client Playing a Movie')

                    #Setup Variable
                    jellyfin_movie_id = playing_device['NowPlayingItem']['Id']
                    jellyfin_movie_name = playing_device['NowPlayingItem']['Name']
                    jellyfin_movie_overview = playing_device['NowPlayingItem']['Overview']

                    jellyfin_playback_poster = (f'{jellyfin_url}/items/{jellyfin_movie_id}/Images/Primary')

                    jellyposter_top = jellyposter_top_text_playing
                    jellyposter_middle = jellyfin_playback_poster
                    jellyposter_bottom =  jellyfin_movie_name + " - " + jellyfin_movie_overview
                    return jellyposter_top, jellyposter_middle, jellyposter_bottom;d

                #TV Channel Display
                if (jellyfin_playback_type == 'TvChannel'):
                    print('Client Playing a Live TV')

                    #Setup Variable
                    jellyfin_channel_id = playing_device['NowPlayingItem']['Id']
                    jellyfin_channel_name = playing_device['NowPlayingItem']['Name']
                    jellyfin_channel_number = playing_device['NowPlayingItem']['ChannelNumber']
                    jellyfin_channel_program_title = playing_device['NowPlayingItem']['CurrentProgram']['EpisodeTitle']

                    jellyfin_playback_poster = (f'{jellyfin_url}/items/{jellyfin_channel_id}/Images/Primary')

                    jellyposter_top = jellyposter_top_text_playing
                    jellyposter_middle = jellyfin_playback_poster
                    jellyposter_bottom =  jellyfin_channel_name + " - " + jellyfin_channel_program_title
                    return jellyposter_top, jellyposter_middle, jellyposter_bottom;

#JellyPoster Get Random Poster if not playing
def get_RANDOM():
    get_random_movie_poster = requests.get(f'{jellyfin_url}/Items?Userid={jellyfin_userid}&limit=1&Recursive=true&IncludeItemTypes=Movie&IsPlayed=False&sortBy=Random&api_key={jellyfin_api_key}')
    random_movie_poster = get_random_movie_poster.json()

    #Setup Variable
    jellyfin_movie_id = random_movie_poster['Items'][0]['Id']
    jellyfin_playback_poster = (f'{jellyfin_url}/items/{jellyfin_movie_id}/Images/Primary')

    jellyposter_top = jellyposter_top_text_idle
    jellyposter_middle = jellyfin_playback_poster
    jellyposter_bottom =  jellyposter_bottom_text_idle
    return jellyposter_top, jellyposter_middle, jellyposter_bottom

#JellyPoster CEC TV Controls
def check_CEC():
    tv_status = tv.is_on()

    if jellyposter_cec_schedule_enable == "True":
        current_time = (time.strftime("%H:%M"))

        if (current_time > jellyposter_cec_schedule_start_time and current_time < jellyposter_cec_schedule_end_time and tv_status == False):
            print("Turning On TV.")
            tv.power_on()

        if (current_time < jellyposter_cec_schedule_start_time and current_time > jellyposter_cec_schedule_end_time and tv_status == True):
            print("Turning Off TV.")
            tv.power_off()

#JellyPoster Jellyfin Auth
jellyfin_userid = get_userid()

#JellyPoster CEC Init
if jellyposter_cec == "True":
    cec.init()
    tv = cec.Device(cec.CECDEVICE_TV)
    print("JellyPoster CEC Enabled.")

#Start JellyPoster HTTP Server
jellyposter_server = HTTPServer((jellyposter_host, jellyposter_port), JellyPosterHTTP)
print("JellyPoster Server is Running...")
jellyposter_server.serve_forever()
jellyposter_server.server_close()
print("JellyPoster Server is Stopped.")
