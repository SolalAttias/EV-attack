import csv
import os
from math import sqrt
import subprocess



def find_power_in_A_real(filename):
	with open(filename) as csv_file:
		csv_reader = csv.reader(csv_file)
		# Find the power_in_A.real which is always column 5 row 10
		a = 0
		for row in csv_reader:
			if a == 9:
				power_in_A_real = row[4]
			a+=1
	return power_in_A_real

def find_all_powers_in_A_real(datafolder):
	reg_outputs = [f for f in os.listdir(datafolder) 
		if os.path.isfile(os.path.join(datafolder,f)) and f[-4:] == ".csv" and "reg" in f]
	reg_outputs.sort()

	with open('datapowerinA.csv', 'w', newline='') as csv_file:
		csv_writer = csv.writer(csv_file)
		for f in reg_outputs:
			csv_writer.writerow([f,find_power_in_A_real(os.path.join(datafolder,f))])
			
#datafolder = "data/scenario1"
#find_all_powers_in_A_real(datafolder)

def overvoltage(filename_volts,filename_nominal):
	# Returns the list of nodes that have overvoltages, and by how much
	with open(filename_nominal)	as csv_file_nominal:
		csv_reader_nominal = csv.reader(csv_file_nominal)
		nominal_voltages = []
		# Find the nominal voltages, which are in row 10
		a = 0	
		for row in csv_reader_nominal:
			if a == 9:
				nominal_voltages = row[1:]
			a += 1
		for i in range(len(nominal_voltages)):
			nominal_voltages[i] = int(nominal_voltages[i])
	with open(filename_volts) as csv_file_volts:
			csv_reader_volts = csv.reader(csv_file_volts)
			a = 0
			for row in csv_reader_volts:
				if a >= 9:
					if a == 9:
						row_length = len(row)
						is_overvoltaged = [False]*(row_length-1)
						overvoltages = [0]*(row_length-1)
					for i in range(row_length-1):
						voltage_A_str = row[i+1]
						voltage_A_complex = complex(voltage_A_str)
						absolute_voltage = abs(voltage_A_complex)
						# Sometimes we need sqrt(3) here to convert from three phase power flow
						if absolute_voltage < 0.1:
							is_overvoltaged[i] = -1
						#elif absolute_voltage > 1.1*nominal_voltages[i]:

						# We test a 5% limit
						elif absolute_voltage > 1.05*nominal_voltages[i]:
							is_overvoltaged[i] = True
						if absolute_voltage > overvoltages[i]:
							overvoltages[i] = absolute_voltage
				a+=1
	return is_overvoltaged,overvoltages

def undervoltage(filename_volts,filename_nominal):
	# Returns the list of nodes that have undervoltages, and by how much
	with open(filename_nominal)	as csv_file_nominal:
		csv_reader_nominal = csv.reader(csv_file_nominal)
		nominal_voltages = []
		# Find the nominal voltages, which are in row 10
		a = 0	
		for row in csv_reader_nominal:
			if a == 9:
				nominal_voltages = row[1:]
			a += 1
		for i in range(len(nominal_voltages)):
			nominal_voltages[i] = int(nominal_voltages[i])
	with open(filename_volts) as csv_file_volts:
			csv_reader_volts = csv.reader(csv_file_volts)
			a = 0
			for row in csv_reader_volts:
				if a >= 9:
					if a == 9:
						row_length = len(row)
						is_undervoltaged = [False]*(row_length-1)
						undervoltages = [10000]*(row_length-1)
					for i in range(row_length-1):
						voltage_A_str = row[i+1]
						voltage_A_complex = complex(voltage_A_str)
						absolute_voltage = abs(voltage_A_complex)
						# Sometimes we need sqrt(3) here to convert from three phase power flow
						if absolute_voltage < 0.1:
							is_undervoltaged[i] = -1
						#elif absolute_voltage > 1.1*nominal_voltages[i]:

						# We test a 5% limit
						elif absolute_voltage < 0.95*nominal_voltages[i]:
							is_undervoltaged[i] = True
						if absolute_voltage < undervoltages[i]:
							undervoltages[i] = absolute_voltage
				a+=1
	return is_undervoltaged,undervoltages

def find_optimal_alpha(n):
	for alpha in range(n):
		f = "optimal_PF/scenario3_alpha_" + str(alpha) + "_" + "R3-12.47-3_fixed.glm"
		subprocess.run(["/usr/local/bin/gridlabd",f])
		filename_volts = "alpha_" + str(alpha) + "_batt_" + "node_volts_A_fixed.csv"
		filename_nominal = "alpha_" + str(alpha) + "_batt_" + "node_nominal_volts_fixed.csv"
		overvoltages,_ = overvoltage(filename_volts,filename_nominal)
		S = 0
		nb_nodes = 0
		for b in overvoltages:
			if b == True:
				S += 1
				nb_nodes += 1
			elif b == False:
				nb_nodes += 1
		print(S,nb_nodes,S/nb_nodes)


#find_optimal_alpha(20)


def read_scenario3(folder,nominal_filename,volts_filename,prefixes):
	hacked = [0]*len(prefixes)
	total_nb_nodes = 0
	proportion = [0]*len(prefixes)
	failures = [0]*len(prefixes)

	for i in range(60):
		subprocess.run(["/usr/bin/python3","Adding_batteries.py"])
		for j in range(len(prefixes)):
			f = "testcases/scenario3/" + "scenario3_" + prefixes[j] + "R3-12.47-3_fixed.glm" 
			subprocess.run(["/usr/local/bin/gridlabd",f])
			full_nominal_filename = folder + prefixes[j] + nominal_filename
			full_volts_filename = folder + prefixes[j] + volts_filename
			is_overvoltaged,overvoltages = overvoltage(full_volts_filename,full_nominal_filename)
			nb_nodes = 0
			nb_nodes_overvoltaged = 0
			for b in is_overvoltaged:
				if b == False:
					nb_nodes += 1
				elif b == True:
					nb_nodes += 1
					nb_nodes_overvoltaged += 1
			hacked[j] += nb_nodes_overvoltaged
			if nb_nodes_overvoltaged > 0:
				failures[j] += 1
			total_nb_nodes += nb_nodes
			proportion[j] = (proportion[j]*i + nb_nodes_overvoltaged/nb_nodes)/(i+1)
			print(proportion[j])
			with open('stats.txt', 'a') as stats:
				stats.write(str(prefixes[j]) + " " + str(nb_nodes_overvoltaged/nb_nodes) + '\n')
			print(nb_nodes_overvoltaged/nb_nodes)
		with open('stats2.txt', 'a') as stats2:
			stats2.write(str(proportion) + '\n')
		with open('stats3.txt', 'a') as stats3:
			stats3.write(str(failures) + '\n')





def read_scenario2(folder,nominal_filename,volts_filename,prefixes):
	hacked = [0]*len(prefixes)
	total_nb_nodes = 0
	proportion = [0]*len(prefixes)
	failures = [0]*len(prefixes)

	for i in range(60):
		subprocess.run(["/usr/bin/python3","Adding_batteries.py"])
		for j in range(len(prefixes)):
			f = "testcases/scenario2/" + "scenario2_" + prefixes[j] + "R3-12.47-3_fixed.glm" 
			subprocess.run(["/usr/local/bin/gridlabd",f])
			full_nominal_filename = folder + prefixes[j] + nominal_filename
			full_volts_filename = folder + prefixes[j] + volts_filename
			is_undervoltaged,undervoltages = undervoltage(full_volts_filename,full_nominal_filename)
			nb_nodes = 0
			nb_nodes_undervoltaged = 0
			for b in is_undervoltaged:
				if b == False:
					nb_nodes += 1
				elif b == True:
					nb_nodes += 1
					nb_nodes_undervoltaged += 1
			hacked[j] += nb_nodes_undervoltaged
			if nb_nodes_undervoltaged > 0:
				failures[j] += 1
			total_nb_nodes += nb_nodes
			proportion[j] = (proportion[j]*i + nb_nodes_undervoltaged/nb_nodes)/(i+1)
			print(proportion[j])
			with open('stats.txt', 'a') as stats:
				stats.write(str(prefixes[j]) + " " + str(nb_nodes_undervoltaged/nb_nodes) + '\n')
			print(nb_nodes_undervoltaged/nb_nodes)
		with open('stats2.txt', 'a') as stats2:
			stats2.write(str(proportion) + '\n')
		with open('stats3.txt', 'a') as stats3:
			stats3.write(str(failures) + '\n')

#folder = "data/scenario2/"
#nominal_filename = "node_nominal_volts_fixed.csv"
#volts_filename = "node_volts_A_fixed.csv"
#prefixes = ["2035_","HP_","GFC_"]