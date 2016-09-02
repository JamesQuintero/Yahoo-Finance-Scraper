#Scraper to get stock price and option data from yahoo finance

import urllib.request           #script for URL request handling
import urllib.parse             #script for URL handling
import html.parser              #script for HTML handling
import os.path                  #script for directory/file handling
import csv                      #script for CSV file handling
import time                     #scripting timing handling
import datetime                   #data and time handling
from datetime import date
import random


class Yahoo:

	opener = None
	user_agents=[]
	timezone=4

	def __init__(self):
		self.user_agents.append("Mozilla/5.0 (X10; Ubuntu; Linux x86_64; rv:25.0)")
		self.user_agents.append("Mozilla/5.0 (Windows NT 6.0; WOW64; rv:12.0)")
		self.user_agents.append("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2227.1 Safari/537")
		self.user_agents.append("Mozilla/5.0 (Windows NT 6.1) AppleWebKit/540 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/540")
		self.user_agents.append("Mozilla/5.0 (Windows; U; Windows NT 5.2; it; rv:1.8.1.11) Gecko/20071327 Firefox/2.0.0.10")
		self.user_agents.append("Opera/9.3 (Windows NT 5.1; U; en)")

		self.opener=urllib.request.build_opener(urllib.request.HTTPRedirectHandler(),urllib.request.HTTPHandler(debuglevel=0))

	#gets current stock price
	def currentPrice(self, stock_symbol):
		try:
			data=self.httpRequest("http://finance.yahoo.com/q?s="+str(stock_symbol).upper())
			h=html.parser.HTMLParser()
			data=h.unescape(data)
			
			temp_data=data.split('id="yfs_l84_'+str(stock_symbol).lower()+'">')
			temp_data=temp_data[1]
			temp_data=temp_data.split("<")
			temp_data=temp_data[0]
			temp_data=temp_data.strip()
			return float(temp_data)

		except Exception as error:
			print("Error occcured when getting "+str(stock_smbol.upper())+"'s current price: "+str(error))
			return 0

	#downloads 1 days worth of 1min intraday history. 1 day is max on yahoo finance
	def downloadMinIntradayHistory(self, stock_symbol):

		try:
			data=self.httpRequest("http://chartapi.finance.yahoo.com/instrument/1.0/"+str(stock_symbol)+"/chartdata;type=quote;range=1d/csv")
		except urllib.request.HTTPError as error:
			print("Error when downloading intraday history "+str(stock_symbol)+": "+str(error))
			return []

		data=data.split("\n")

		#if price data was received
		if len(data)>20:

			#removes beginning information
			for x in range(0, 20):
				data.pop(0)

			new_list=[]
			for x in range(0, len(data)):
				data[x]=data[x].split(",")

				#can have "TIMEZONE_OFFSET=-300" in row. If it doesn't have it in row,
				#1421764499,107.5850,107.9483,107.0600,107.8800,3135600
				if len(data[x])!=1:
					temp={}
					temp['date']=data[x][0]
					temp['open']=data[x][4]
					temp['high']=data[x][2]
					temp['low']=data[x][3]
					temp['close']=data[x][1]
					temp['volume']=data[x][5]
					new_list.append(temp)

			return new_list
		else:
			return []

	#gets option data like call/put price, strike, etc. for stock_symbol 
	#date format example: 1416614400
	def downloadOptionData(self, stock_symbol, date):

		try:
			data=self.httpRequest("http://finance.yahoo.com/q/op?s="+str(stock_symbol)+"&date="+str(date))
			h=html.parser.HTMLParser()
			data=h.unescape(data)

			data=data.split(',"options"')
			#includes option data and the rest of the HTML page
			data=data[5]

			temp_data=data.split("_options")
			data=temp_data[0]

			#removes :{"calls":[ from beginning and " from end
			data=data[11:len(data)-2]

			temp_data=data.split('"puts":')
			calls=temp_data[0]
			puts=temp_data[1]


			to_return={}
			to_return['call']=self.extractOptionData(calls)
			to_return['put']=self.extractOptionData(puts)

			return to_return
		except Exception as error:
			print("Error: "+str(error))
			to_return={}
			to_return['call']=[]
			to_return['put']=[]
			return to_return

		

	#actually extracts option data from scraped content
	def extractOptionData(self, data):
		data=data.split("},{")

		for x in range(0, len(data)):
			data[x]=data[x].replace("{", "")
			data[x]=data[x].replace("}", "")
			data[x]=data[x].replace("[", "")
			data[x]=data[x].replace("]", "")
			data[x]=data[x].replace('"', "")
			data[x]=data[x].split(",")

			for y in range(0, len(data[x])):
				data[x][y]=data[x][y].split(":")

		# X  | Y | data[x][y]
		# 30 | 0 | ['contractSymbol', 'AAPL141122C00106000']
		# 30 | 1 | ['currency', 'USD']
		# 30 | 2 | ['volume', '778']
		# 30 | 3 | ['openInterest', '8591']
		# 30 | 4 | ['contractSize', 'REGULAR']
		# 30 | 5 | ['expiration', '1416614400']
		# 30 | 6 | ['lastTradeDate', '1415998724']
		# 30 | 7 | ['inTheMoney', 'true']
		# 30 | 8 | ['percentChangeRaw', '18.668596']
		# 30 | 9 | ['impliedVolatilityRaw', '0.335944140625']
		# 30 | 10 | ['impliedVolatility', '33.59']
		# 30 | 11 | ['strike', '106.00']
		# 30 | 12 | ['lastPrice', '8.20']
		# 30 | 13 | ['change', '1.29']
		# 30 | 14 | ['percentChange', '+18.67']
		# 30 | 15 | ['bid', '8.10']
		# 30 | 16 | ['ask', '8.30']
		
		new_data=[]
		for x in range(0, len(data)):

			temp_list={}
			for y in range(0, len(data[x])):
				if data[x][y][0]!="":
					item=data[x][y][0]

					if item=="strike":
						temp_list['strike']=data[x][y][2]
					elif item=="lastPrice":
						temp_list['price']=data[x][y][2]
					elif item=="bid":
						temp_list['bid']=data[x][y][2]
					elif item=="ask":
						temp_list['ask']=data[x][y][2]
					elif item=="openInterest":
						temp_list['open_int']=data[x][y][2]
					elif item=="volume":
						temp_list['volume']=data[x][y][2]
					elif item=="impliedVolatility":
						temp_list['IV']=data[x][y][2]
						
			new_data.append(temp_list)

		return new_data


	#gets available option contract expiration dates
	def getExpirationDates(self, stock_symbol):

		try:
			data=self.httpRequest("http://finance.yahoo.com/q/op?s="+str(stock_symbol))
			h=html.parser.HTMLParser()
			data=h.unescape(data)
		except Exception as error:
			print("Error when retrieving option contract exp dates ("+stock_symbol.upper()+"): "+str(error))
			return []



		date_ids=[]
		date_strings=[]
		try:
			date_splits=data.split('<option data-selectbox-link="/q/op?s='+str(stock_symbol)+'&date=')
			date_splits.pop(0)


			for x in range(0, len(date_splits)):
				temp_data=date_splits[x].split('"')

				#gets date_ids
				date_id=temp_data[0]
				date_id=date_id.strip()
				date_ids.append(date_id)

				#gets actual date
				date=temp_data[3]
				temp_date=date.split("</option>")
				#>November 22, 2014
				date=temp_date[0]
				#November 22, 2014
				date=date.replace(">", "")
				date=date.strip()
				#[0]=November
				#[1]=22,
				#[2]=2014
				date=date.split(" ")
				#[1]=22
				date[1]=date[1].replace(",", "")
				#[0]=11
				temp_strings={}
				temp_strings['january']=1
				temp_strings['february']=2
				temp_strings['march']=3
				temp_strings['april']=4
				temp_strings['may']=5
				temp_strings['june']=6
				temp_strings['july']=7
				temp_strings['august']=8
				temp_strings['september']=9
				temp_strings['october']=10
				temp_strings['november']=11
				temp_strings['december']=12
				date[0]=temp_strings[date[0].lower()]
				#['month']=11
				#['day']=22
				#['year']=2014
				temp_date={}
				temp_date['month']=int(date[0])
				temp_date['day']=int(date[1])
				temp_date['year']=int(date[2])
				date_strings.append(temp_date)
				
			
		except Exception as error:
			print("String handling error (yahoo.py get_expiration_dates()): "+str(error))


		to_return={}
		to_return['date_ids']=date_ids
		to_return['dates']=date_strings
		return to_return



	#gets high,low,open,close from a yahoo provided start date to prev_date
	#prev_date
	#[0]=month
	#[1]=day
	#[2]=year
	def prevPrice(self, stock_symbol, prev_date):
		try:
			data=self.httpRequest("http://real-chart.finance.yahoo.com/table.csv?s="+str(stock_symbol)+"&g=d&a="+str(prev_date['month']-1)+"&b="+str(prev_date['day'])+"&c="+str(prev_date['year'])+"&ignore=.csv")
			h=html.parser.HTMLParser()
			data=h.unescape(data)

			#joins data into list format
			new_list=[]
			index=0
			new_str=""
			while index<len(data):
				if data[index]!="\n":
					new_str+=data[index]
				else:
					new_list.append(new_str)
					new_str=""
				index+=1
			data=new_list

			#removes column titles
			data.pop(0)

			data.reverse()

			for x in range(0, len(data)):
				data[x]=data[x].split(",")

				unadj_open=float(data[x][1])
				unadj_high=float(data[x][2])
				unadj_low=float(data[x][3])
				unadj_close=float(data[x][4])

				#if volume is 0
				if int(data[x][5])==0:
					if x!=0:
						adj_open=float(data[x-1]['open'])
						adj_high=float(data[x-1]['high'])
						adj_low=float(data[x-1]['low'])
						adj_close=float(data[x-1]['close'])
				else:

					#for some reason, yahoo's adjusted close is just slightly off from the regular close, so don't get adjusted close if diff is less than 5%
					if abs(float(data[x][6])-float(data[x][4]))/float(data[x][4])*100<5:
						adj_close=float(data[x][4])
					else:
						adj_close=float(data[x][6])

					#gets split ratio
					ratio=unadj_close/adj_close

					#adjusts open, high, and low to match new prices after the stock split
					adj_open=self.convertNumber(unadj_open/ratio)
					adj_high=self.convertNumber(unadj_high/ratio)
					adj_low=self.convertNumber(unadj_low/ratio)

				date=data[x][0].split("-")
				date=str(date[1])+"/"+str(date[2])+"/"+str(date[0])

				temp_list={}
				temp_list['date']=date
				temp_list['open']=adj_open
				temp_list['high']=adj_high
				temp_list['low']=adj_low
				temp_list['close']=adj_close
				temp_list['volume']=data[x][5]
				temp_list['adj_close']=float(data[x][6])
				data[x]=temp_list

			data.pop(0)
			return data


		except Exception as error:
			print("URL error (yahoo.py donwload_modified_history()): "+str(error)+" | "+str(stock_symbol))
			return []


	#retrieves split adjusted interday price history. 
	#timeframe is in years, EX: "10y", "1y"
	def downloadAdjustedInterdayHistory(self, stock_symbol, timeframe):
		try:
			cur_date=self.currentDate()

			if "y" not in timeframe:
				raise ValueError
			else:
				timeframe=int(timeframe.replace("y", ""))

			response = self.opener.open("http://real-chart.finance.yahoo.com/table.csv?s="+str(stock_symbol)+"&g=d&a="+str(cur_date['month']-1)+"&b="+str(cur_date['day'])+"&c="+str(cur_date['year']-timeframe)+"&ignore=.csv", timeout=30)
			
			data=response.read()
			data=data.decode('UTF-8')
			h=html.parser.HTMLParser()
			data=h.unescape(data)

			#joins data into list format
			new_list=[]
			index=0
			new_str=""
			while index<len(data):
				if data[index]!="\n":
					new_str+=data[index]
				else:
					new_list.append(new_str)
					new_str=""
				index+=1
			data=new_list

			#removes column titles
			data.pop(0)

			data.reverse()

			for x in range(0, len(data)):
				data[x]=data[x].split(",")

				unadj_open=float(data[x][1])
				unadj_high=float(data[x][2])
				unadj_low=float(data[x][3])
				unadj_close=float(data[x][4])

				#if volume is 0
				if int(data[x][5])==0:
					if x!=0:
						adj_open=float(data[x-1]['open'])
						adj_high=float(data[x-1]['high'])
						adj_low=float(data[x-1]['low'])
						adj_close=float(data[x-1]['close'])
				else:

					#for some reason, yahoo's adjusted close is just slightly off from the regular close, so don't get adjusted close if diff is less than 5%
					if abs(float(data[x][6])-float(data[x][4]))/float(data[x][4])*100<5:
						adj_close=float(data[x][4])
					else:
						adj_close=float(data[x][6])

					#gets split ratio
					ratio=unadj_close/adj_close

					#adjusts open, high, and low 
					adj_open=self.convertNumber(unadj_open/ratio)
					adj_high=self.convertNumber(unadj_high/ratio)
					adj_low=self.convertNumber(unadj_low/ratio)

				date=data[x][0].split("-")
				date=str(date[1])+"/"+str(date[2])+"/"+str(date[0])

				temp_list={}
				temp_list['date']=date
				temp_list['open']=adj_open
				temp_list['high']=adj_high
				temp_list['low']=adj_low
				temp_list['close']=adj_close
				temp_list['volume']=data[x][5]
				temp_list['adj_close']=float(data[x][6])
				data[x]=temp_list

			

			return data


		except Exception as error:
			print("URL error (yahoo.py donwload_modified_history()): "+str(error)+" | "+str(stock_symbol)+" "+str(timeframe))
			return []

	#retrieves non-split adjusted interday price history. 
	#timeframe is in years, EX: "10y", "1y"
	def downloadUnadjustedInterdayHistory(self, stock_symbol, timeframe):
		try:
			cur_date=self.currentDate()

			if "y" not in timeframe:
				raise ValueError
			else:
				timeframe=int(timeframe.replace("y", ""))

			data=self.httpRequest("http://real-chart.finance.yahoo.com/table.csv?s="+str(stock_symbol)+"&g=d&a="+str(cur_date['month']-1)+"&b="+str(cur_date['day'])+"&c="+str(cur_date['year']-timeframe)+"&ignore=.csv")
			h=html.parser.HTMLParser()
			data=h.unescape(data)

			#joins data into list format
			new_list=[]
			index=0
			new_str=""
			while index<len(data):
				if data[index]!="\n":
					new_str+=data[index]
				else:
					new_list.append(new_str)
					new_str=""
				index+=1
			data=new_list

			#removes column titles
			data.pop(0)

			for x in range(0, len(data)):
				data[x]=data[x].split(",")

				unadj_open=float(data[x][1])
				unadj_high=float(data[x][2])
				unadj_low=float(data[x][3])
				unadj_close=float(data[x][4])

				date=data[x][0].split("-")
				date=str(date[1])+"/"+str(date[2])+"/"+str(date[0])

				temp_list={}
				temp_list['date']=date
				temp_list['open']=unadj_open
				temp_list['high']=unadj_high
				temp_list['low']=unadj_low
				temp_list['close']=unadj_close
				temp_list['adj_close']=float(data[x][6])
				temp_list['volume']=data[x][5]
				data[x]=temp_list

			data.reverse()

			return data


		except Exception as error:
			print("URL error (yahoo.py donwload_unmodified_history()): "+str(error)+" | "+str(stock_symbol)+" "+str(timeframe))
			return []

	#returns current date in format: {"year": 2016, "month": 1, "day": 15}
	def currentDate(self):
		curDate=str(datetime.datetime.utcnow() + datetime.timedelta(hours=-self.timezone))
		date=curDate.split(' ')
		#2013-12-15
		curDate=date[0]

		cur_date=curDate.split("-")

		to_return={}
		to_return['year']=int(cur_date[0])
		to_return['month']=int(cur_date[1])
		to_return['day']=int(cur_date[2])
		return to_return

	#returns request results from url
	def httpRequest(self, url):
		#sets random user agent
		self.opener.addheaders=[('User-agent', random.choice(self.user_agents))]

		response = self.opener.open(url, timeout=30)
		data=response.read()
		data=data.decode('UTF-8', errors='ignore')
		return data


	def convertNumber(self, number):
		return int(number*100)/100
		


if __name__=="__main__":
	yahoo=Yahoo()

	symbol="AAPL"
	price=yahoo.currentPrice(symbol)
	print(symbol+" current price: "+str(price))