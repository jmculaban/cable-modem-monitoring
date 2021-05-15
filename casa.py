"""
NBCTI Check Modem Status
Version: v1.0
Date: 05/11/2021

For CASA System to connect using telnet
Set IP Address, USER, PASSWORD in .env file

Copyright © 2021 by Engr. John Michael Culaban
"""

import tkinter as tk
from tkinter import messagebox
from dotenv import load_dotenv
from dotenv import dotenv_values

import telnetlib
import getpass
import time

# to read all data available
# maximize window
import struct
from telnetlib import DO, DONT, IAC, WILL, WONT, NAWS, SB, SE

MAX_WINDOW_WIDTH = 65000  # Max Value: 65535
MAX_WINDOW_HEIGHT = 5000

config = dotenv_values(".env")

window = tk.Tk()

window.title("NBCTI Check Modem Status")

# Disable Maximize buttonwindow.resizable(0,0)

Host = config["IP"]
username = config["USER"]
password = config["PASSWORD"]

#################### Center window #########################
def center(toplevel):
	toplevel.update_idletasks()

	screen_width = toplevel.winfo_screenwidth()
	scree_height = toplevel.winfo_screenheight()

	size = tuple(int(_) for _ in toplevel.geometry().split('+')[0].split('x'))
	x = screen_width/2 - size[0]/2
	y = scree_height/2 - size[1]/2

	toplevel.geometry("+%d+%d" % (x, y))

#################### Resize to max #########################
def set_max_window_size(tsocket, command, option):
	if option == NAWS:
		width = struct.pack('H', MAX_WINDOW_WIDTH)
		height = struct.pack('H', MAX_WINDOW_HEIGHT)
		tsocket.send(IAC + WILL + NAWS)
		tsocket.send(IAC + SB + NAWS + width + height + IAC + SE)
	elif command in (DO, DONT):
		tsocket.send(IAC + WONT + option)
	elif command in (WILL, WONT):
		tsocket.send(IAC + DONT + option)

#################### Offline Status Function #########################
def offline_status(mac_address):
	# telnet login
	tn = telnetlib.Telnet(Host)
	tn.set_option_negotiation_callback(set_max_window_size)
	tn.read_until(b"CASA-C100G login: ")
	tn.write(username.encode("ascii") + b"\n") 
	tn.read_until(b"Password: ")
	tn.write(password.encode('ascii') + b"\n")

	# print("Successfully connected to CASA")
	time.sleep(0.5)

	tn.write(b"scm offline\n")
	time.sleep(0.5)
	offline_modems = tn.read_very_eager()
	offline_modems_arr = offline_modems.decode('utf-8').split()
	# print(offline_modems_arr)

	# Change mac address format
	mac_arr = mac_address.split(':')
	mac_dot = mac_arr[0] + mac_arr[1] + '.' + mac_arr[2] + mac_arr[3] + '.' + mac_arr[4] + mac_arr[5]

	mac_location = offline_modems_arr.index(mac_dot)

	if mac_location > -1:
		mac_offline_status = offline_modems_arr[mac_location + 4]
		mac_offline_date = offline_modems_arr[mac_location + 5]

		# adjust time
		date_time = mac_offline_date.split(',') 
		date_time = date_time[1].split(':')
		adjust_time = int(date_time[0]) - 1
		mac_offline_date = mac_offline_date.replace(date_time[0], str(adjust_time)) 

		last_active_lbl_value.set("Last Active:")
		last_active_value.set(mac_offline_date)
		last_status_lbl_value.set("Last Status:")
		last_status_value.set(mac_offline_status)

	else:
		last_active_lbl_value.set("")
		last_active_value.set("")
		last_status_lbl_value.set("")
		last_status_value.set("")

		messagebox.showinfo("NBCTI CASA", "No modem found.")

	ch_zero.set('-')
	rx_zero.set('-')
	snr_zero.set('-')

	ch_one.set('-')
	rx_one.set('-')
	snr_one.set('-')

	ch_two.set('-')
	rx_two.set('-')
	snr_two.set('-')

	ch_three.set('-')
	rx_three.set('-')
	snr_three.set('-')

	# End connection
	tn.write(b"exit\n")
	time.sleep(0.4)

#################### Button Function #########################
def check_status():
	mac = mac_input.get().strip()
	
	if mac == '':
		messagebox.showinfo("NBCTI CASA", "Please provid MAC Address")
		return

	# telnet login
	tn = telnetlib.Telnet(Host)
	tn.read_until(b"CASA-C100G login: ")
	tn.write(username.encode("ascii") + b"\n") 
	tn.read_until(b"Password: ")
	tn.write(password.encode('ascii') + b"\n")

	# print("Successfully connected to CASA")
	time.sleep(0.5)

	# Write command 'scm <mac address>' to telnet
	tn.write(b"scm " + mac.encode("ascii") + b"\n")
	time.sleep(0.4)
	status_out = tn.read_very_eager()
	status_arr = status_out.decode('utf-8').split()

	# Get modem status (online, offline or no data)
	try:
		mac_status.set(status_arr[26])
	except:
		messagebox.showinfo("NBCTI CASA", "No modem found.")
		return

	# check modem if online
	if status_arr[26].find("online") < 0:
		# messagebox.showinfo("NBCTI CASA", "Modem offline")
		if status_arr[26] == "offline":
			# End connection
			tn.write(b"exit\n")
			time.sleep(0.4)
			offline_status(mac)
			return
	
	last_status_lbl_value.set("")
	last_status_value.set("")
	last_active_lbl_value.set("")
	last_active_value.set("")

	status_arr = []

	# Write command 'scm <mac address> phy' to telnet
	tn.write(b"scm " + mac.encode("ascii") + b" phy\n")
	time.sleep(0.4)
	status_out = tn.read_very_eager()
	status_arr = status_out.decode('utf-8').split()

	# End connection
	tn.write(b"exit\n")
	time.sleep(0.4)

	# Extract data (US channel, Rx power and SNR)
	try:
		ch_zero.set(status_arr[25])
		rx_zero.set(status_arr[29])
		snr_zero.set(status_arr[30])
	except:
		ch_zero.set('-')
		rx_zero.set('-')
		snr_zero.set('-')

	try:
		ch_one.set(status_arr[37])
		rx_one.set(status_arr[41])
		snr_one.set(status_arr[42])
	except:
		ch_one.set('-')
		rx_one.set('-')
		snr_one.set('-')

	try:
		ch_two.set(status_arr[49])
		rx_two.set(status_arr[53])
		snr_two.set(status_arr[54])
	except:
		ch_two.set('-')
		rx_two.set('-')
		snr_two.set('-')

	try:
		ch_three.set(status_arr[61])
		rx_three.set(status_arr[65])
		snr_three.set(status_arr[66])
	except:
		ch_three.set('-')
		rx_three.set('-')
		snr_three.set('-')

#################### Button Function End #########################

input_frame = tk.Frame(window)
input_frame.grid(row=0, column=0)

input_lbl = tk.Label(
	input_frame,
	font=("Helvetica", 10),
	text="Enter Mac Address: "
)
input_lbl.grid(row=0, column=0, padx=3, pady=5)

# .get() to delete value
# .delete() to delete value
# .insert() to insert value
mac_input = tk.Entry(
	input_frame,
	font=("Helvetica", 10),
	width=38
)
mac_input.grid(row=0, column=1, padx=3, pady=5)

# activity_btn = tk.Button(
# 	btn_frame,
# 	text="Check Activity",
# 	width=15,
# 	justify="right"
# )
# activity_btn.grid(row=0, column=1, padx=5, pady=5)

status_btn = tk.Button(
	input_frame,
	font=("Helvetica", 10),
	text="Check Status",
	width=15,
	command=check_status
)
status_btn.grid(row=1, column=1, padx=5, pady=5)

# status_frame = tk.Frame(window)
# status_frame.grid(row=2, column=0)

data_frame = tk.Frame(window)
data_frame.grid(row=1, column=0)

#################### MAC Status #########################
mac_status_lbl = tk.Label(
	data_frame,
	font=("Helvetica", 10),
	text="MAC Status: ",
)
mac_status_lbl.grid(row=0, column=0, padx=8, pady=2)

#################### MAC Status Data #########################
mac_status = tk.StringVar()
mac_status_data = tk.Label(
	data_frame,
	font=("Helvetica", 10),
	textvariable=mac_status,
)
mac_status_data.grid(row=1, column=0, padx=5, pady=3)
mac_status.set("-")

#################### Title for Data #########################
ch_title = tk.Label(
	data_frame,
	font=("Helvetica", 10),
	text="Channel",
)
ch_title.grid(row=0, column=1, padx=8, pady=2)

rx_title = tk.Label(
	data_frame,
	font=("Helvetica", 10),
	text="Rx (dB)",
)
rx_title.grid(row=0, column=2, padx=8, pady=2)

snr_title = tk.Label(
	data_frame,
	font=("Helvetica", 10),
	text="SNR (dB)",
)
snr_title.grid(row=0, column=3, padx=8, pady=2)

#################### Channel 0 Data #########################
ch_zero = tk.StringVar()
ch_zero_data = tk.Label(
	data_frame,
	font=("Helvetica", 10),
	textvariable=ch_zero,
)
ch_zero_data.grid(row=1, column=1, padx=3, pady=3)
ch_zero.set("-")

# Rx Power Data
rx_zero = tk.StringVar()
rx_zero_data = tk.Label(
	data_frame,
	font=("Helvetica", 10),
	textvariable=rx_zero,
)
rx_zero_data.grid(row=1, column=2, padx=3, pady=3)
rx_zero.set("-")

# SNR Data
snr_zero = tk.StringVar()
snr_zero_data = tk.Label(
	data_frame,
	font=("Helvetica", 10),
	textvariable=snr_zero,
)
snr_zero_data.grid(row=1, column=3, padx=3, pady=3)
snr_zero.set("-")

#################### Channel 1 Data #########################
ch_one = tk.StringVar()
ch_one_data = tk.Label(
	data_frame,
	font=("Helvetica", 10),
	textvariable=ch_one,
)
ch_one_data.grid(row=2, column=1, padx=3, pady=3)
ch_one.set("-")

# Rx Power Data
rx_one = tk.StringVar()
rx_one_data = tk.Label(
	data_frame,
	font=("Helvetica", 10),
	textvariable=rx_one,
)
rx_one_data.grid(row=2, column=2, padx=3, pady=3)
rx_one.set("-")

# SNR Data
snr_one = tk.StringVar()
snr_one_data = tk.Label(
	data_frame,
	font=("Helvetica", 10),
	textvariable=snr_one,
)
snr_one_data.grid(row=2, column=3, padx=3, pady=3)
snr_one.set("-")

#################### Channel 2 Data #########################
ch_two = tk.StringVar()
ch_two_data = tk.Label(
	data_frame,
	font=("Helvetica", 10),
	textvariable=ch_two,
)
ch_two_data.grid(row=3, column=1, padx=3, pady=3)
ch_two.set("-")

# Rx Power Data
rx_two = tk.StringVar()
rx_two_data = tk.Label(
	data_frame,
	font=("Helvetica", 10),
	textvariable=rx_two,
)
rx_two_data.grid(row=3, column=2, padx=3, pady=3)
rx_two.set("-")

# SNR Data
snr_two = tk.StringVar()
snr_two_data = tk.Label(
	data_frame,
	font=("Helvetica", 10),
	textvariable=snr_two,
)
snr_two_data.grid(row=3, column=3, padx=3, pady=3)
snr_two.set("-")

#################### Channel 3 Data #########################
ch_three = tk.StringVar()
ch_three_data = tk.Label(
	data_frame,
	font=("Helvetica", 10),
	textvariable=ch_three,
)
ch_three_data.grid(row=4, column=1, padx=3, pady=3)
ch_three.set("-")

# Rx Power Data
rx_three = tk.StringVar()
rx_three_data = tk.Label(
	data_frame,
	font=("Helvetica", 10),
	textvariable=rx_three,
)
rx_three_data.grid(row=4, column=2, padx=3, pady=3)
rx_three.set("-")

# SNR Data
snr_three = tk.StringVar()
snr_three_data = tk.Label(
	data_frame,
	font=("Helvetica", 10),
	textvariable=snr_three,
)
snr_three_data.grid(row=4, column=3, padx=3, pady=3)
snr_three.set("-")

#################### Offline Status Data #########################
offline_frame = tk.Frame(window)
offline_frame.grid(row=2, column=0)

# Last active
last_active_lbl_value = tk.StringVar()
last_active_lbl = tk.Label(
	offline_frame,
	font=("Helvetica", 10),
	textvariable=last_active_lbl_value,
)
last_active_lbl.grid(row=0, column=0, padx=1, pady=1)
last_active_lbl_value.set("")

last_active_value = tk.StringVar()
last_active = tk.Label(
	offline_frame,
	font=("Helvetica", 10),
	textvariable=last_active_value,
)
last_active.grid(row=0, column=1, padx=1, pady=1)
last_active_value.set("")

# Last status
last_status_lbl_value = tk.StringVar()
last_status_lbl = tk.Label(
	offline_frame,
	font=("Helvetica", 10),
	textvariable=last_status_lbl_value,
)
last_status_lbl.grid(row=1, column=0, padx=1, pady=1)
last_status_lbl_value.set("")

last_status_value = tk.StringVar()
last_status = tk.Label(
	offline_frame,
	font=("Helvetica", 10),
	textvariable=last_status_value,
)
last_status.grid(row=1, column=1, padx=1, pady=1)
last_status_value.set("")

center(window)
window.iconbitmap('logo.ico')
window.mainloop()