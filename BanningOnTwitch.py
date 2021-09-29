import time
import pyautogui
# install with 'pip install pyautogui'


import csv
bot_names = []
# bot_list.csv is the file that contains all of the names to be banned
# expects a format of one name per line
with open('bot_list_sep_28.csv', newline='' ) as csvfile:
    spamreader = csv.reader(csvfile,delimiter=' ')
    bot_names = [row[0].strip() for row in spamreader]

print('Starting countdown')
for i in range(10,0,-1):
    print(f"Writing text in {i} seconds")
    #time.sleep(1)
n = len(bot_names)
i = 0
for userToBan in bot_names:
    print(f"\r({i*100/n}%) banning user {userToBan}                      ",end = '\r')
    #pyautogui.write(f'/ban {userToBan}')
    #pyautogui.press('enter')
    #time.sleep(0.05)
    i +=1
