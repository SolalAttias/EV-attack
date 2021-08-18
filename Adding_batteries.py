#!/usr/bin/env python
import os
import random
import subprocess
import time
import math

#random.seed(42)

RUN = False

households_with_EVs = 0.4
EVs_with_V2G = 0.2

BATTERY = """      use_internal_battery_model TRUE;
	battery_type LI_ION;
	rated_power 200 kW;
	nominal_voltage 350;
	battery_capacity 50 kWh;
	round_trip_efficiency 0.81;
	state_of_charge 0.5;
	generator_mode SUPPLY_DRIVEN;
"""


INVERTER_SLOW = """     four_quadrant_control_mode LOAD_FOLLOWING;
     rated_power 3000.0;		//Per phase rating
     inverter_efficiency .95;
	charge_on_threshold 1.5 kW;
	charge_off_threshold 1.7 kW;
	discharge_off_threshold 2 kW;
	discharge_on_threshold 3 kW;
	max_discharge_rate 3 kW;
	max_charge_rate 3 kW;
	charge_lockout_time 1;
	discharge_lockout_time 1;
"""

INVERTER_FAST = """     four_quadrant_control_mode LOAD_FOLLOWING;
     rated_power 22000.0;		//Per phase rating
     inverter_efficiency .95;
	charge_on_threshold 1.5 kW;
	charge_off_threshold 1.7 kW;
	discharge_off_threshold 2 kW;
	discharge_on_threshold 3 kW;
	max_discharge_rate 22 kW;
	max_charge_rate 22 kW;
	charge_lockout_time 1;
	discharge_lockout_time 1;
"""

HACKED_INVERTER_FAST = """     four_quadrant_control_mode CONSTANT_PQ;
     rated_power 22 kVA;
     inverter_efficiency 0.9;
     V_base 120;
     charge_lockout_time 1;
     discharge_lockout_time 1;
     P_Out 22000;
     Q_Out 0;
     """

HACKED_INVERTER_SLOW = """     four_quadrant_control_mode CONSTANT_PQ;
     rated_power 3 kVA;
     inverter_efficiency 0.9;
     V_base 120;
     charge_lockout_time 1;
     discharge_lockout_time 1;
     P_Out 3000;
     Q_Out 0;
     """

n = 20
HACKED_REACTIVE_INVERTER_FAST = """     four_quadrant_control_mode CONSTANT_PQ;
     rated_power 22 kVA;
     inverter_efficiency 0.9;
     charge_lockout_time 1;
     discharge_lockout_time 1;
     P_Out """ + str(22000 * math.sin(3 * math.pi/n)) + """;
     Q_Out """ + str(22000 * math.cos(3 * math.pi/n)) + """;
     """

HACKED_REACTIVE_INVERTER_SLOW = """     four_quadrant_control_mode CONSTANT_PQ;
     rated_power 3 kVA;
     inverter_efficiency 0.9;
     charge_lockout_time 1;
     discharge_lockout_time 1;
     P_Out """ + str(3000 * math.sin(3 * math.pi/n)) + """;
     Q_Out """ + str(3000 * math.cos(3 * math.pi/n)) + """;
     """

def add_batteries(content,INVERTER,BATTERY,households_with_EVs, EVs_with_V2G,prefix,hacked = False,is_load = False):
	# We find all the lines in the file that correspond to residential houses
	# and that also have a meter associated to it 
	# (I will probably have to do something about the rest...)
	# Also find the names of the houses and meters associated
	content = content.copy()

	houses = []
	names = []
	meter_names = []
	phases = []

	# We only use metered houses for simplicity's sake, but here we count all houses
	all_houses_nb = 0 



	for i in range(len(content)):
		if "object triplex_node" in content[i]:
			is_house = False
			has_parent = False
			name = ""
			meter_name = ""
			for j in range(10):
				if "nominal_voltage 120" in content[i+j]:
					is_house = True
					# houses have 120 voltage
				if "name" in content[i+j]:
					name = content[i+j][10:-2]
					# This is fragile : the string "     name " is 10 long
				if "parent" in content[i+j]:
					has_parent = True
					meter_name = content[i+j][12:-2]
					# This is fragile : the string "     parent " is 12 long
				if "phases" in content[i+j]:
					phase = content[i+j]
				if is_house and has_parent:
					houses.append(i)
					meter_names.append(meter_name)
					names.append(name)
					phases.append(phase)
					break
			if is_house: 
				all_houses_nb += 1
		if 'file "' in content[i]:
			content[i] = content[i][0:11] + prefix + content[i][11:]
			# This is fragile : the string '    file "' is 10 long


	metered_houses_nb = len(houses)
	expected_EVs_added = households_with_EVs*EVs_with_V2G*all_houses_nb
	if expected_EVs_added < 1:
		print(filename,"No EVs")
		return 0

	# We add the lines that go from the house to the meter and we add the meter
	try:
		if households_with_EVs*EVs_with_V2G*all_houses_nb/metered_houses_nb > 1:
			print(filename,"Not enough metered houses")
	except:
		if metered_houses_nb == 0:
			print(filename, "no metered houses... Uh-oh")
		return 0

	lines_added = 0

	for index in range(metered_houses_nb):
		if random.random() < households_with_EVs*all_houses_nb/metered_houses_nb:
			if random.random() < EVs_with_V2G: 
				# We add a triplex line that goes from the house to the new EV meter
				batt_line = "object triplex_line {" + '\n'
				batt_line += "     name tl_batt_" + names[index] + ";" + '\n'
				batt_line += "     from " + names[index] + ";" + '\n'
				batt_line += "     to batt_meter_" + names[index] + ";" + '\n'
				batt_line += phases[index] + '\n'
				batt_line += "     length 10;" + '\n'
				batt_line += "     configuration triplex_line_configuration:1;" + '\n' "}" + '\n'

				# We add a meter for the inverter and battery
				batt_meter = "object triplex_meter {" + '\n'
				batt_meter += "     name batt_meter_" + names[index] + ";"  + '\n'
				batt_meter += phases[index] + '\n'
				batt_meter += "     nominal_voltage 120.00;" + '\n' + "}" + '\n'

				# We add an inverter for the battery
				batt_inverter = "object inverter {" + '\n'
				batt_inverter += "     name batt_inv_" + names[index] + ";" + '\n'
				batt_inverter += "     generator_status ONLINE;" + '\n'
				batt_inverter += "     inverter_type FOUR_QUADRANT;" + '\n'
				batt_inverter += "     parent batt_meter_" + names[index] + ";" + '\n'
				batt_inverter += "     sense_object " + meter_names[index] + ";" + '\n'
				batt_inverter += INVERTER + '\n'
				batt_inverter += "}" + '\n'

				# We add a battery, that represents our EV
				batt_EV = "object battery {" + '\n' "     name batt_" + names[index] + ";" + '\n'
				batt_EV += "     parent batt_inv_" + names[index] + ";" + '\n'
				batt_EV += BATTERY + '\n'
				batt_EV += "}" +'\n'

				content.insert(houses[index]+lines_added, batt_EV)
				content.insert(houses[index]+lines_added, batt_inverter)
				content.insert(houses[index]+lines_added, batt_meter)
				content.insert(houses[index]+lines_added, batt_line)
				lines_added += 4
			elif is_load:
				content.insert(houses[index]+lines_added, load)
				lines_added += 1
	return content





def add_loads(content):
	return 0
"""
files = [os.path.join("testcases/",f) for f in os.listdir("testcases/") if os.path.isfile(os.path.join("testcases/",f)) and f[-4:] == ".glm" and f[:2] != '._' and f[-8:-4] !="batt"]

files.sort()"""
"""
for filename in files:
	full_filename = filename
	new_filename = filename[:-4] + "_batt.glm"
	if not os.path.isfile(full_filename):
		print(full_filename, 'File does not exist.')
		quit()

	with open(full_filename) as f:
		content = f.read().splitlines()

	new_content = add_batteries(content)
	if new_content == 0:
		continue


	#print(filename,int(expected_EVs_added),EVs_added)
	f = open(new_filename, "w")
	for s in new_content:
		f.write(s)
		f.write('\n')

	f.close()

all_files = [os.path.join("testcases/",f) for f in os.listdir("testcases/") if os.path.isfile(os.path.join("testcases/",f)) and f[-4:] == ".glm" and f[:2] != '._']
"""
if RUN:
	t1 = time.time()
	for f in all_files:
		subprocess.run(["/usr/local/bin/gridlabd",f])
	t2 = time.time()
	print(t2-t1)


def read_file(filename):
	full_filename = filename
	if not os.path.isfile(full_filename):
		print(full_filename, 'File does not exist.')
		quit()

	with open(full_filename) as f:
		content = f.read().splitlines()
	return content



def find_power_factor(filename,n):
	for alpha in range(n+1):
		new_filename = "optimal_PF/scenario3_GFC_alpha_" + str(alpha) + "_" + filename


		new_content = add_batteries(content.copy(),HACKED_INVERTER_SLOW,str(alpha)+"batt_",hacked = True)
		if new_content == 0:
			print("what")


		#print(filename,int(expected_EVs_added),EVs_added)
		f = open(new_filename, "w")
		for s in new_content:
			f.write(s)
			f.write('\n')

		f.close()


filename = "R3-12.47-3_fixed.glm"
folder = "testcases/scenario3/"
content = read_file(filename)


prefix = "data/scenario3/"

new_content = add_batteries(content,INVERTER_SLOW,BATTERY,0.4, 0.2,prefix+"2035",hacked = False,is_load = False)
if new_content == 0:
	print("what")

new_filename = folder + "scenario3_2035" + filename
f = open(new_filename, "w")
for s in new_content:
	f.write(s)
	f.write('\n')

f.close()

new_content = add_batteries(content,INVERTER_FAST,BATTERY,0.4, 0.2,prefix+"GFC",hacked = False,is_load = False)
if new_content == 0:
	print("what")

new_filename = folder+"scenario3_GFC" + filename
f = open(new_filename, "w")
for s in new_content:
	f.write(s)
	f.write('\n')

f.close()

new_content = add_batteries(content,INVERTER_SLOW,BATTERY,0.8, 0.4,prefix+"HP",hacked = False,is_load = False)
if new_content == 0:
	print("what")

new_filename = folder+"scenario3_HP" + filename
f = open(new_filename, "w")
for s in new_content:
	f.write(s)
	f.write('\n')

f.close()

new_content = add_batteries(content,HACKED_INVERTER_SLOW,BATTERY,0.4, 0.2,prefix+"hacked_2035",hacked = False,is_load = False)
if new_content == 0:
	print("what")

new_filename = folder + "scenario3_hacked_2035" + filename
f = open(new_filename, "w")
for s in new_content:
	f.write(s)
	f.write('\n')

f.close()

new_content = add_batteries(content,HACKED_INVERTER_FAST,BATTERY,0.4, 0.2,prefix+"hacked_GFC",hacked = False,is_load = False)
if new_content == 0:
	print("what")

new_filename = folder + "scenario3_hacked_GFC" + filename
f = open(new_filename, "w")
for s in new_content:
	f.write(s)
	f.write('\n')

f.close()

new_content = add_batteries(content,HACKED_INVERTER_SLOW,BATTERY,0.8, 0.4,prefix+"hacked_HP",hacked = False,is_load = False)
if new_content == 0:
	print("what")

new_filename = folder + "scenario3_hacked_HP" + filename
f = open(new_filename, "w")
for s in new_content:
	f.write(s)
	f.write('\n')

f.close()

new_content = add_batteries(content,HACKED_REACTIVE_INVERTER_SLOW,BATTERY,0.4, 0.2,prefix+"hacked_reactive_2035",hacked = False,is_load = False)
if new_content == 0:
	print("what")

new_filename = folder + "scenario3_hacked_reactive_2035" + filename
f = open(new_filename, "w")
for s in new_content:
	f.write(s)
	f.write('\n')

f.close()

new_content = add_batteries(content,HACKED_REACTIVE_INVERTER_FAST,BATTERY,0.4, 0.2,prefix+"hacked_reactive_GFC",hacked = False,is_load = False)
if new_content == 0:
	print("what")

new_filename = folder + "scenario3_hacked_reactive_GFC" + filename
f = open(new_filename, "w")
for s in new_content:
	f.write(s)
	f.write('\n')

f.close()

new_content = add_batteries(content,HACKED_REACTIVE_INVERTER_SLOW,BATTERY,0.8, 0.4,prefix+"hacked_reactive_HP",hacked = False,is_load = False)
if new_content == 0:
	print("what")

new_filename = folder + "scenario3_hacked_reactive_HP" + filename
f = open(new_filename, "w")
for s in new_content:
	f.write(s)
	f.write('\n')

f.close()
