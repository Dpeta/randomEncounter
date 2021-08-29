from irc import *
import os, sys, time
import random

## IRC Config
server = "127.0.0.1" # The IP/Hostname to connect to.
server_hostname = "irc.pesterchum.xyz" # The server's hostname.
#server = "havoc.ddns.net"
#server_hostname = "irc.havoc.ddns.net"
port = 3333
botnick = "randomEncounter"
logging_enabled = False
mood_on_join_enabled = False
insecure_mode = False # For if the hostname can't be verified for SSL/TLS.
                      # Havoc needs True

## Irrelevant variables
bot_hostname = "randomEncounter"
bot_servername = "randomEncounter"
bot_realname = "randomEncounter"
nickserv_username = "randomEncounter"

## Don't edit the variables past this point.
setup_finished = False
do_not_random_encounter_afk = []

## Checks if files are missing and asks to generate them if they are.
if (os.path.exists("./password.txt") == False):
    print("password.txt not found.")
    f = open("password.txt", "w")
    f.write(input("Please input nickserv password.\n"))
    f.close()
if (os.path.exists("./do_not_random_encounter.txt") == False):
    print("do_not_random_encounter.txt not found.")
    f = open("do_not_random_encounter.txt", "w")
    f.write("")
    f.close()

## Load variables
try:
    f = open("password.txt", "r")
    nickserv_password = f.read()
    f.close()
except:
    print("Failed to load nickserv password.")
    nickserv_password = ""

try:
    f = open("do_not_random_encounter.txt", "r")
    DN_RE_string = f.read().strip()
    do_not_random_encounter = DN_RE_string.split(" ")
    f.close()
except:
    print("Failed to load list of people who have random encounter disabled.")
    do_not_random_encounter = []
    
print("do_not_random_encounter = " + str(do_not_random_encounter))

## IRC
irc = IRC(server_hostname, insecure_mode)
irc.connect(server, port, botnick, server_hostname, bot_hostname, bot_servername, bot_realname)

while True:
    try:
        if (int(time.time())%1800) == 0:
            print("Autosave do_not_random_encounter: " + str(do_not_random_encounter))
            DN_RE_string = ""
            for x in range(len(do_not_random_encounter)):
                DN_RE_string += do_not_random_encounter[x]
                DN_RE_string += " "
            DN_RE_string = DN_RE_string.strip()
            
            f = open("do_not_random_encounter.txt", "w")
            f.write(DN_RE_string)
            f.close()
        
        text = irc.get_response()
            
        if (text!=None):
            print(text)
            if ((("End of /MOTD" in text)|("MOTD File is missing" in text)) & (setup_finished==False)):
                print("End of /MOTD found")
                if (irc.post_connect_setup(botnick, nickserv_username, nickserv_password)==0):
                    setup_finished = True
                print("setup_finished = " + str(setup_finished))

            # RE check
            textSplit = text.split(":")
            if (len(textSplit) > 1):
                if (len(textSplit) > 2):
                    if (mood_on_join_enabled==True):
                        # Give mood
                        # Because of the bot's modes, we can't actually check for GETMOOD,
                        # so, I decided to have it respond when people join.
                        # Of course, setting a mood isn't actually neccisarry for anything,
                        # so disabling it might actually be better for people with low bandwith :(
                        if (("JOIN" in textSplit[1])&("#pesterchum" in textSplit[2])):
                            irc.send("PRIVMSG #pesterchum MOOD >7" + "\n")
                    if (("PRIVMSG randomEncounter" in textSplit[1])&("COLOR >" not in textSplit[2])&("PESTERCHUM" not in textSplit[2])):
                        irc.send("PRIVMSG #pesterchum MOOD >7" + "\n")
                        nick = textSplit[1].split('!')
                        print("PRIVMSG from " + nick[0])
                        irc.send("PRIVMSG "+ nick[0] +" (This is an automated message) " + "\n")
                        irc.send("PRIVMSG "+ nick[0] +" Random user: " + \
                                 irc.randomEncounter(botnick, nick[0], do_not_random_encounter, do_not_random_encounter_afk, True, logging_enabled, server_hostname) +\
                                 "\n")
                    
                if ("NOTICE randomEncounter" in textSplit[1]):
                    print("NOTICE randomEncounter")
                    
                    commandChar = ((textSplit[2].replace('\n',"")).replace(' ',"")).replace('\r',"")
                    
                    # Get requester's nick
                    nick = textSplit[1].split('!')

                    print("Request " + commandChar + " from " + nick[0])
                    
                    # Random encounter
                    if (commandChar=='!'):
                        irc.randomEncounter(botnick, nick[0], do_not_random_encounter, do_not_random_encounter_afk, False, logging_enabled, server_hostname)

                    # Turn random encounters on and off.
                    if (commandChar=='+'):
                        irc.send("NOTICE " + nick[0] + " +=k" + "\n")
                        if nick[0] in do_not_random_encounter:
                            do_not_random_encounter.remove(nick[0])
                        print(do_not_random_encounter)
                    if (commandChar=='-'):
                        irc.send("NOTICE " + nick[0] + " -=k" + "\n")
                        do_not_random_encounter.append(nick[0])
                        print(do_not_random_encounter)

                    # Exclude afk users.
                    if (commandChar=='~'):# Become idle
                        irc.send("NOTICE " + nick[0] + " ~=k" + "\n")
                        do_not_random_encounter_afk.append(nick[0])
                        print(do_not_random_encounter_afk)
                    if (commandChar=='*'): # Stop being idle
                        irc.send("NOTICE " + nick[0] + " *=k" + "\n")
                        if nick[0] in do_not_random_encounter_afk:
                            do_not_random_encounter_afk.remove(nick[0])

                    # I have no clue what this does LOL
                    if (commandChar=='?'):
                        irc.send("NOTICE " + nick[0] + " ?=y" + "\n")
        else:
            time.sleep(1)
    except KeyboardInterrupt:
        if (irc.disconnect(do_not_random_encounter) == 0):
            print("Exiting gracefully.")
            sys.exit(0)
        else:
            print("Something went wrong :')")
            input()

