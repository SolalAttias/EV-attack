#!/usr/bin/env python
import os.path

# Define a filename.

filename = "testcases/R1-12.47-2"
full_filename = filename + ".glm"
new_filename = filename + "_batt.glm"
if not os.path.isfile(full_filename):
    print('File does not exist.')
    quit()

# Open the file as f.
# The function readlines() reads the file.
with open(full_filename) as f:
    content = f.read().splitlines()

# We find all the lines in the file that correspond to residential houses
# and that also have a meter associated to it 
# (I will probably have to do something about the rest...)
# Also find the names of the houses and meters associated

houses = []
names = []
meter_names = []
phases = []
for i in range(len(content)):
    if "object triplex_node" in content[i]:
        is_house = False
        has_parent = False
        name = ""
        meter_name = ""
        for j in range(10):
            if "nominal_voltage 120" in content[i+j]:
                is_house = True
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



# We add the lines that go from the house to the meter and we add the meter

for index in range(len(houses)):
    stuff1 = """object triplex_line {
     	name tl_batt_""" + names[index] + """;
     	from """ + names[index] + """;
     	to batt_meter_""" + names[index] + """;
        """ + phases[index] + """
        length 10;
        configuration triplex_line_configuration:1;
    }"""
    stuff2 = """object triplex_meter {
         name batt_meter_""" + names[index] + """;
         """ + phases[index] + """
         nominal_voltage 120.00;
    }"""
    # Need to figure out if this is the right numbers for the inverter

    stuff3 = """object inverter {
        name batt_inv_""" + names[index] + """;
        generator_status ONLINE;
        inverter_type FOUR_QUADRANT;
        four_quadrant_control_mode LOAD_FOLLOWING;
    	parent batt_meter_""" + names[index] + """;
    	sense_object """ + meter_names[index] + """;
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
    }"""

    # We add batteries to all the houses

    stuff4 = """object battery {
    	name batt_""" + names[index] + """;
    	parent batt_inv_""" + names[index] + """;
        use_internal_battery_model TRUE;
        battery_type LI_ION;
        rated_power 3 kW;
        nominal_voltage 400;
        battery_capacity 50 kWh;
        round_trip_efficiency 0.81;
        state_of_charge 0.5;
        generator_mode SUPPLY_DRIVEN;
    }"""

    content.insert(houses[index]+4*index, stuff4)
    content.insert(houses[index]+4*index, stuff3)
    content.insert(houses[index]+4*index, stuff2)
    content.insert(houses[index]+4*index, stuff1)

f = open(new_filename, "w")
for s in content:
    f.write(s)
    f.write('\n')

f.close()