#!/usr/bin/env python

import spidev
import time
import os
import datetime
import glob
from time import strftime
from datetime import datetime
import RPi.GPIO as GPIO
import MySQLdb

GPIO.setmode(GPIO.BCM)

spi = spidev.SpiDev()
spi.open(0,0)
DEBUG = 1

adc_flex = 0
adc_force_1 = 1
adc_force_2 = 2

last_flex = 0       
last_force1 = 0
last_force2 = 0

flex_tolerance = 1       # prevent jitter
force_tolerance = 1
flex_scale = 10.24
force_scale = 10.24

flex_array = [0, 0 , 0 , 0 , 0 , 0 , 0 , 0 , 0 , 0]
force1_array = [0, 0 , 0 , 0 , 0 , 0 , 0 , 0 , 0 , 0]
force2_array = [0, 0 , 0 , 0 , 0 , 0 , 0 , 0 , 0 , 0]

force1_read = 0
force2_read = 0
flex_read = 0		

force1_in = 0
force2_in = 0
flex_in = 0

force1_mean = 0
force2_mean = 0 
flex_mean = 0	

force1_level = 0
force2_level = 0
flex_level = 0

flex_idx = 0
force1_idx = 0
force2_idx = 0

flex_trigger = 0

force_threshold = 800
flex_threshold = 500

motor_pin = 18
led_green = 23
led_red = 24

GPIO.setup(motor_pin, GPIO.OUT)
GPIO.setup(led_green, GPIO.OUT)
GPIO.setup(led_red, GPIO.OUT)

  # ADC Value
  # (approx)     Volts
  #    0          0.00
  #   78          0.25
  #  155          0.50
  #  233          0.75
  #  310          1.00
  #  465          1.50
  #  775          2.50
  # 1023          3.30

# read SPI data from MCP3008 chip, 8 possible adc's (0 thru 7)
def readadc(adcnum):
        if ((adcnum > 7) or (adcnum < 0)):
                return -1
	r = spi.xfer2([1,(8+adcnum)<<4,0])
	adcout = ((r[1]&3) << 8) + r[2]
	return adcout

def readForce1(int):
			global last_force1 
			global force1_in
			
			force1_read = abs(readadc(adc_force_1) - force1_level)	
			force1_adjust = abs(force1_read - last_force1)

			if ( force1_adjust > force_tolerance ):
				 force1_in = force1_read 
				 # print "-----------------------------------------"
				 # print "Force Reading 1: ", force1_in, (time.strftime("%Y-%m-%d ") + time.strftime("%H:%M:%S"))
				 last_force1 = force1_read
				 # print "-----------------------------------------"
			return force1_in

def readForce2(int):
			global last_force2 
			global force2_in
			
			force2_read = abs(readadc(adc_force_2) - force2_level)
			force2_adjust = abs(force2_read - last_force2)

			if ( force2_adjust > force_tolerance ):
				 force2_in = force2_read 
				 # print "-----------------------------------------"
				 # print "Force Reading 2: ", force2_in, (time.strftime("%Y-%m-%d ") + time.strftime("%H:%M:%S"))
				 last_force2 = force2_read
				 # print "-----------------------------------------"
			return force2_in	
			
def readFlex(int):
			global last_flex  
			global flex_in
			
			flex_read = abs(readadc(adc_flex) - flex_level)
			flex_adjust = abs(flex_read - last_flex)
			
			if ( flex_adjust > flex_tolerance ):
				 flex_in = flex_read 
				 # print "-----------------------------------------" 
				 # print "Flex Reading: ", flex_in, (time.strftime("%Y-%m-%d ") + time.strftime("%H:%M:%S"))
				 # last_flex = flex_in	
				 # print "-----------------------------------------"
			return flex_in

def force1Mean(int):
		global force1_mean
		
		for i in range (0,9):
			force1_mean = force1_mean + force1_array[i] 
			
		force1_mean = force1_mean / 10
		return force1_mean

def force2Mean(int):
		global force2_mean
		
		for j in range (0,9):
			force2_mean = force2_mean + force2_array[j] 
			
		force2_mean = force2_mean / 10
		return force2_mean
	
def flexMean(int):
		global flex_mean

		for k in range(0,9):
			flex_mean = flex_mean + flex_array[k]
			
		flex_mean = flex_mean / 10
		return flex_mean
	
force1_level = readadc(adc_force_1)
force2_level = readadc(adc_force_2)
flex_level = readadc(adc_flex)

db = MySQLdb.connect(host="localhost", user="root", passwd="ee30322016", db="posture_database")
cur = db.cursor()

while True:
	try:	
		
		time.sleep(1) 
		print "-----------------------------------------"
		print (time.strftime("%Y-%m-%d ") + time.strftime("%H:%M:%S"))
		
		force1_array[force1_idx] = readForce1( force1_read )
		if( force1_idx == 9):
			force1_idx = 0
		else:
			force1_idx = force1_idx + 1
			
		force1_mean = force1Mean(force1_mean)
		print "-----------------------------------------"
		print "Force1 Array: ", (force1_array)
		print "Force1 mean: ", force1_mean		
		print "-----------------------------------------"
		
		sql=("""INSERT INTO FlexLog (DateTime, LeftForce) VALUES (%s, %s)""", (datetimeWrite, force1_mean))
		try:
			print "writing to database"
			cur.execute(*sql)
			db.commit()
			print "write complete"
		except:
			db.rollback()
			print "failed to write"
		cur.close()
		db.close()
		
		force2_array[force1_idx] = readForce2( force2_read )
		if( force2_idx == 9):
			 force2_idx = 0
		else:
			force2_idx = force2_idx + 1
		force2_mean = force2Mean(force2_mean)
		print "-----------------------------------------"
		print "Force2 Array: ", (force2_array)
		print "Force2 mean: ", force2_mean
		print "-----------------------------------------"	
		
		sql=("""INSERT INTO FRLog (DateTime, RightForce) VALUES (%s, %s)""", (datetimeWrite, force2_mean))
		try:
			print "writing to database"
			cur.execute(*sql)
			db.commit()
			print "write complete"
		except:
			db.rollback()
			print "failed to write"
		cur.close()
		db.close()

		flex_trigger = (flex_trigger + 1) % 2 #alternate between 1 and 0 to trigger at half the frequency
		
		if ( flex_trigger == 0):
			flex_array[flex_idx] = readFlex( flex_read ) 
			if (flex_idx == 9):
				flex_idx = 0
			else :
				flex_idx = flex_idx + 1
			
			flex_mean = flexMean(flex_mean)
			print "-----------------------------------------"
			print "Flex Array: ", (flex_array)
			print "Flex mean: ", flex_mean
			print "-----------------------------------------"
			sql=("""INSERT INTO FlexLog (DateTime, Flex) VALUES (%s, %s)""", (datetimeWrite, flex_mean))
			try:
				print "writing to database"
				cur.execute(*sql)
				db.commit()
				print "write complete"
			except:
				db.rollback()
				print "failed to write"
			cur.close()
			db.close()
	
		if( ((force1_mean + force2_mean) / 2 > force_threshold) or (flex_mean > flex_threshold)) :
			GPIO.output(motor_pin,1)
			GPIO.output(led_green, 0)
			GPIO.output(led_red, 1)			
		else:
			GPIO.output(motor_pin, 0)
			GPIO.output(led_green, 1)
			GPIO.output(led_red, 0)
			

	except KeyboardInterrupt:
		exit()
	
GPIO.cleanup()
