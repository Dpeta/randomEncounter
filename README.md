## Random Encounters
A simple bot for Pesterchum servers to serve the same functionality as the original randomEncounter bot using python3's socket module. (Which I believe was maintained by Hydrothermal?)
Configure the variables at the top of "client.py" and execute it, or run "run.py" if you'd like to have it automatically restart in the case of unexpected crashes.
People are random encountered by *default*. It has to be explicitly disabled by the user, in which case their handle is removed from the list. (and saved to do_not_random_encounter.txt)
### Software requirements
 - Python 3 (Ideally, 3.6 or higher.)
 - OpenSSL
### Required python modules
 - os
 - sys
 - time
 - socket
 - random
 - ssl
