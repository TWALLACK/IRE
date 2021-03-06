# Compiles a list of speakers and events for IRE 2016


#Import modules
import urllib2
from lxml import html
from bs4 import BeautifulSoup
import re
import sys 
import time
import os

#Declare empty sets
url_list = []
unique_event_list = []
speakers_nodupes = []
speakers_with_events = []

# retrieves current directory
outpath = os.getcwd()
print outpath

# Creates files 

outfilename = "/IRE2016_events.txt"
outfile = open(outpath+outfilename, 'w')
outfile.write("Event|Day|Date|Time|Location|Speakers|Moderator|ModeratorOrg|URL\n")
outfile.close()

outfilename = "/IRE2016_speakers.txt"
outfile = open(outpath+outfilename, 'w')
outfile.write("Name|Twitter|Bio|Event|Day|Date|Time\n")
outfile.close()

outfilename = "/IRE2016_speakers_nodupes.txt"
outfile = open(outpath+outfilename, 'w')
outfile.write("Name|Twitter|Bio\n")
outfile.close()

#Opens and reads IRE 2016 conference page
url = "http://www.ire.org/conferences/ire-2016/speakers/"
page = html.fromstring(urllib2.urlopen(url).read())

#Creates a list of links to all the conference sessions
for internal_link in page.xpath("//a"):
    full_link= internal_link.get("href")
    if full_link[0:27] == "/events-and-training/event/": #excludes non-confernce links
        if full_link not in url_list:  #makes sure you don't grab same link twice
           url_list.append("http://www.ire.org"+full_link)

# Grabs information from each page in url_list
for url in url_list:
    time.sleep(5)  #pauses five seconds between pages
    content = urllib2.urlopen(url).read()
    soup = BeautifulSoup(content)

    #Pulls out the data in the main section of each panel page, including title
    MainSection = soup.findAll("h1", { "class" : "heading1" },text=True)
    title = MainSection[0].text
    title = title.encode('utf-8')
    title = title.strip()

    # Get information in list for each panel page
    info_list = soup.find("section", class_="main-content").findAll('li')
    
    # Get speaker information 
    speakers = info_list[1].get_text()
    speakers = speakers.encode('utf-8')
    # Eliminates commas before 2nd, Jr. Sr, III & IV
    speakers = re.sub(r",[\W]{0,4}Jr.", r" Jr.", speakers)
    speakers = re.sub(r",[\W]{0,4}Sr.", r" Sr.", speakers)
    speakers = re.sub(r",[\W]{0,4}2nd", r" 2nd", speakers)
    speakers = re.sub(r",[\W]{0,4}III", r" III", speakers)
    speakers = re.sub(r",[\W]{0,4}IV", r" IV", speakers)
    speakers = speakers.strip()
 
    #Gets timing and splits into day, date and time 
    timing = info_list[2].get_text()
    timing= timing.encode('utf-8')
    timing = timing[11:].split(",")
    day = timing[0]
    timing = timing[1].split(" at ")
    date = timing[0].strip()
    time_of_day = timing[1]
     
    #Gets location information
    location = info_list[3].get_text()
    location= location.encode('utf-8')
    location = location[10:]

    #Shows whether audio file is availasble  
    Audio = info_list[4].get_text()
    Audio= Audio.encode('utf-8')
    Audio = Audio[12:]

    #Assembles list of speakers (and filters out blanks) 
    speaker_list = [] 
    speaker_list_initial = speakers[9:].split(',')
    for person in speaker_list_initial:
        if person.strip()<>"": 
           speaker_list.append(person)

    #Looks for moderator
    moderator_name = "No moderator listed"
    moderator_org = ""
    for ptag in soup.findAll('p'):
       match = re.search(r'\*Moderated',ptag.text[1:11])
       if match: 
          moderator=ptag.text[15:]
          moderator=moderator.encode('utf-8')
          moderator = moderator.split(",")
          moderator_name = moderator[0].strip()
          mod_length = len(moderator)
          if mod_length>1:
             moderator_org = moderator[1].strip()
          else:
            moderator_org = "" 

    #Make list of classes here
    if url not in unique_event_list:
       unique_event_list.append(url)
       event_row = title + "|" + day + "|" + date + "|" + time_of_day + "|" + location + "|" + speakers[9:]  + "|" + moderator_name + "|" + moderator_org + "|" + url 
       print event_row
       outfilename = "/IRE2016_events.txt"
       outfile = open(outpath+outfilename, 'a')
       outfile.write(event_row +"\n")
       outfile.close()

    #Find speaker bios
    #This section was a bit complicated
    #Bios sometimes took up multiple lines. And IRE used two different sets of HTML
    #tags to introduce each one.
    
    #Initializes variables in this section
    a=0
    bios=[]
    
    #Locates bio section by finding speakers tag, and then grabbing 2nd element after    
    speakers_tag = soup.find("h2", text="Speakers")
    for speaker in speakers_tag.next_elements:
       if a<3:
         next = speaker.encode('utf-8')
         if a==2: 
            bio = next[5:-6]
            bio = re.sub(r"\|", r"!", bio) # Gets rid of existing pipes
            bio = re.sub(r"<div>", r"<p>", bio)
            bio = re.sub(r"</div>", r"</p>", bio)
            bio_new = re.sub(r"<p>None</p>", r"|<p>No bio</p>", bio)
            bio_new = re.sub(r"</p>\n<p></p><p>", r"|</p><p></p><p>", bio_new)
            bio_new = re.sub(r"\xc2\xa0", r" ", bio_new)
            chars_to_remove = ['<p>', '</p>']
            bio_new.translate(None, ''.join(chars_to_remove))
            bio_new = re.sub(r"<p>", r"", bio_new)
            bio_new = re.sub(r"</p>", r"", bio_new)
            bio_new = re.sub(r"\n", r"", bio_new)
            bio_list_initial = bio_new.split("|")
            bio_list = []
            for bio in bio_list_initial:
               if bio<>"": 
                  bio_list.append(bio)

            #scans bios for Twitter handles and puts them in new list
            twitter_list = []
            for current_bio in bio_list:
                twitter_username = re.search(r'@([A-Za-z0-9_]+)',current_bio)
                if twitter_username:
                   twitter_list.append(twitter_username.group())
                else: 
                   twitter_list.append("")
       a+=1
    #Puts together list for each speaker
    #print "test"
    speaker_row =""
    for number in range(len(speaker_list)):
      speaker_row =  speaker_list[number].strip() + "|" + twitter_list[number].strip() + "|" + bio_list[number].strip()
      
      
      #Builds two lists of speakers:
      #speakers_nodupes has an unduplicated list of speakers
      if speaker_row not in speakers_nodupes:
         speakers_nodupes.append(speaker_row)
      #speakers_with_events lists a speaker with each panel or class they are in
      #but speakers with multiple events will appear in multiple rows
      speaker_row_extra = speaker_row + "|" + title + "|" + day + "|"+ date + "|"+ time_of_day + "|" + url
      if speaker_row_extra not in speakers_with_events:
         speakers_with_events.append(speaker_row_extra)


#pour info into speakers_nodupes
for row in speakers_nodupes:
  outfilename = "/IRE2016_speakers_nodupes.txt"
  outfile = open(outpath+outfilename, 'a')
  outfile.write(row+"\n")
  outfile.close()

#pour info into speakers_with_events
for row in speakers_with_events:
  outfilename = "/IRE2016_speakers.txt"
  outfile = open(outpath+outfilename, 'a')
  outfile.write(row+"\n")
  outfile.close()
