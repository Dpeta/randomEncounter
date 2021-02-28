import os, time

# Restarts the bot automatically for if it crashes.

os.system("python3 --version")
while(True):
        try:
                os.system("python3 client.py")
        except:
                pass
        print("Waiting 5 seconds until restart...")
        time.sleep(5)
input("Finish :3")
