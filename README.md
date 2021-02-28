## Random Encounters
A simple bot for irc servers meant to be used with Pesterchum to serve the same functionality as the original randomEncounter bot using python3's socket module.

Credit to the original author of the bot, though I'm not entirely certain as to who that is. (Hydrothermal?)

Configure the variables at the top of "client.py" and execute it, or run "run.py" if you'd like to have it automatically restart in the case of unexpected crashes.
People are random encountered by *default*. It has to be explicitly disabled by the user, in which case their handle is removed from the list. (and saved to do_not_random_encounter.txt)

### Software requirements
 - Python 3 (Ideally, 3.6 or higher.)
 - OpenSSL

### Required Python modules
 - os
 - sys
 - time
 - socket
 - random
 - ssl

### Disclaimer
This bot *may* be exceptionally shoddy.
