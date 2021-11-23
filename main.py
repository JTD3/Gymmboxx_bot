import telebot
from telebot import types
import os
import requests
import schedule
import time
import logging
import threading
import schedule

TOKEN = os.environ.get('TOKEN')

#logger = telebot.logger	
#telebot.logger.setLevel(logging.DEBUG)
bot = telebot.TeleBot(TOKEN)



def getNamesAndCodeNames():
	z = requests.get('https://smartentry.org/status/api/metrics/gymmboxx')
	names,codeNames = [],[]
	for i in z.json()['outlets']: names.append(i['name']), codeNames.append(i['code'])
	return names,codeNames



def run_continuously(interval=1):
    """Continuously run, while executing pending jobs at each
    elapsed time interval.
    @return cease_continuous_run: threading. Event which can
    be set to cease continuous run. Please note that it is
    *intended behavior that run_continuously() does not run
    missed jobs*. For example, if you've registered a job that
    should run every minute and you set a continuous run
    interval of one hour then your job won't be run 60 times
    at each interval but only once.
    """
    cease_continuous_run = threading.Event()

    class ScheduleThread(threading.Thread):
        @classmethod
        def run(cls):
            while not cease_continuous_run.is_set():
                schedule.run_pending()
                time.sleep(interval)


    continuous_thread = ScheduleThread()
    continuous_thread.start()
    return cease_continuous_run




@bot.message_handler(commands=['gym'])
def getAllGymData(message):

	x = requests.get('https://smartentry.org/status/api/metrics/gymmboxx')
	response = ''
	for i in x.json()['outlets']:

		currentOccupancy = i['occupancy']
		maximumOccupancy =i['occupancy_limit']
		currentWaiting = i['queue_length']
		gymName = i['name']
		if currentOccupancy >= maximumOccupancy:
			response += f"*{gymName}*  \n"
			response += f"Current occupancy : {currentOccupancy} / {maximumOccupancy}\n"
			response += f"Gym is currently full \U0001F534 \n"
			response += f"There are currently  {currentWaiting} people waiting\n\n"
		else:
			response += f"*{gymName}*  \n"
			response += f"Current occupancy : {currentOccupancy} / {maximumOccupancy}\n"
			if round(float(100 * currentOccupancy/maximumOccupancy)) < 30:
				response += 'Occupancy: Low \U0001F7E2 \n\n '
			elif round(float(100 * currentOccupancy/maximumOccupancy)) >= 30 and round(float(100 * currentOccupancy/maximumOccupancy)) < 70:
				response += 'Occupancy: Medium \U0001F7E1\n\n'
			else:
				response += 'Occupancy: High \U0001F534\n\n'

	bot.send_message(message.chat.id,response ,parse_mode='Markdown')

@bot.message_handler(commands=['codenames'])
def getCodeNames(message):
	names,codeNames = getNamesAndCodeNames()
	response = ''
	for index, i in enumerate(names):
		response += f"*{i}* : {codeNames[index]}\n"

	bot.send_message(message.chat.id,response ,parse_mode='Markdown')	




def getGymData(message,gymLocation):

	z = requests.get('https://smartentry.org/status/api/metrics/gymmboxx')
	response = ''
	for i in z.json()['outlets']:
		if i['name'] == gymLocation:
			currentOccupancy = i['occupancy']
			maximumOccupancy = i['occupancy_limit']
			currentWaiting = i['queue_length']
			gymName = i['name']

			if currentOccupancy >= maximumOccupancy:
				response += f"*{gymName}*  \n"
				response += f"Current occupancy : {currentOccupancy} / {maximumOccupancy}\n"
				response += f"Gym is currently full \U0001F534 \n"
				response += f"There are currently  {currentWaiting} people waiting\n\n"
			else:
				response += f"*{gymName}*  \n"
				response += f"Current occupancy : {currentOccupancy} / {maximumOccupancy}\n"
				if round(float(100 * currentOccupancy/maximumOccupancy)) < 30:
					response += 'Occupancy: Low \U0001F7E2 \n\n '
				elif round(float(100 * currentOccupancy/maximumOccupancy)) >= 30 and round(float(100 * currentOccupancy/maximumOccupancy)) < 70:
					response += 'Occupancy: Medium \U0001F7E1\n\n'
				else:
					response += 'Occupancy: High \U0001F534\n\n'
	bot.send_message(message.chat.id, response, parse_mode='Markdown')



@bot.message_handler(commands=['notify'])
def notify(message):
	global stop_run_continuously
	names,codeNames = getNamesAndCodeNames()
	try:
		if len(message.text.split()) > 3:
			raise ValueError()
		location = message.text.split()[1]
		updateTimer = int(message.text.split()[2])

	except (IndexError, ValueError) as e:
		location = None
		updateTimer = None
	all_jobs = schedule.get_jobs(location)

	if not all_jobs:

		if location is not None and updateTimer is not None:	
		
			if location in codeNames:

				if int(updateTimer) >= 5 and int(updateTimer) <= 60:
					bot.send_message(message.chat.id, f"You will now receive updates every {updateTimer} minutes at Gymboxx {names[codeNames.index(location)]}\n To stop receiving messages type /stop")
					schedule.every(updateTimer).minutes.do(getGymData,message,names[codeNames.index(location)]).tag(location)
					stop_run_continuously = run_continuously()
			
				else:
					bot.send_message(message.chat.id, 'You can only receive updates every 5 to 60 minutes')

			else:
				bot.send_message(message.chat.id, f"{location} is not a valid Gymboxx location")
		else:

			bot.send_message(message.chat.id, "To use this command, type /notify followed by the gym's codename and the update duration in minutes. Type /codenames to get all of the gyms' codenames")
	else:

		bot.send_message(message.chat.id, 'Automated messages for this gymmboxx location already exists. Type /stop to stop all automated messages before starting a new one at the same gymmboxx location')

@bot.message_handler(commands=['stop'])
def stopNotifications(message):
	all_jobs = schedule.get_jobs()
	print(all_jobs)
	if all_jobs:
		bot.send_message(message.chat.id, 'Stopping all automated messages')
		schedule.clear()
		print(stop_run_continuously)
		stop_run_continuously.set()
	else:
		bot.send_message(message.chat.id, 'No automated messages has been set. To set automated messages type /notify')



	

if __name__ == "__main__":

	bot.polling(none_stop=True)
	