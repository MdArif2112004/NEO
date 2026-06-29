@echo off
cd /d C:\Users\moham\neo_core

:: Delay for system stability
timeout /t 5 /nobreak >nul

:: Run everything completely silently in the background using pythonw
start "" pythonw telegram_router.py
start "" pythonw voice.py
start "" pythonw notification_server.py

:: Launch the Discord Bounty Spider (freelance gig scanner)
start "" pythonw -c "from neo.tools.discord_spider import execute_spider; execute_spider()"

:: Launch the Reddit Bounty Tracker
start "" pythonw reddit_bounty_tracker.py
timeout /t 5

:: Run the UI silently (the Notch will appear, but no terminal window)
start "" pythonw notch.py
