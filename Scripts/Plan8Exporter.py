import json
import ntpath
# import requests
import reapy
import os
import os.path as path
import math
import shutil
from shutil import copyfile


# reapy.configure_reaper()

isDev = True
project = reapy.Project()

project.select_all_items()

tracks = project.tracks

items = project.items

markers = project.markers
regions = project.regions

config_items = []

config_tracks = []

groups = {}

RPR_ClearConsole()


def timeToBeat(time):
  timeSignature = 4
  quarterTime = (60 / project.bpm)
  quarters = time / quarterTime
  quarters = float(round(quarters, 4))

  measures = math.floor(quarters / timeSignature)
  sixteenths = (quarters % 1) * 4
  
  normalized = (sixteenths - 0) / (16 - 0)
  quarters = math.floor(quarters) % timeSignature

  sixteenthString = str(sixteenths)
  
  if len(sixteenthString) > 3:
    first = round(float(sixteenthString),3)
    sixteenths = float(first)
  
  progress = [measures, quarters, sixteenths]
    
  return ':'.join(str(x) for x in progress) 
  

def convert_time(pos):

    formatted = RPR_format_timestr_pos(pos, '', 512, 2)
    time_obj = RPR_format_timestr(pos, "", 512)
    
   

    return {
        'seconds': time_obj[0],
        #'time':  time_obj[1],
        #'formatted': formatted[1],
        'beats': timeToBeat(pos)#formatted[1].replace(".", ":"),
    }

def create_item_dict(item,groupGuide, idx = 0):
  take = item.active_take
  # if idx > 0 :
  #   rendername = os.path.splitext(take.name)[0] + '-00' + str(idx) + '.wav'
     
  # else:
  rendername = os.path.splitext(take.name)[0]
  pos = item.get_info_value('D_POSITION')
  guidePos = groupGuide.get_info_value('D_POSITION')
  source = RPR_GetMediaItemTake_Source(take.id)
  sourceArray = RPR_GetMediaSourceFileName(source, "", 512)
  infile = sourceArray[1]
  return {
    #'takeName': formatName(take.name),
    'name': formatName(rendername),
    'format': getFormatFromName(ntpath.basename(infile)),
    #'track': item.track.name,
    'startFromGroup': convert_time(pos - guidePos),
    'endFromGroup': convert_time((pos+item.length) - guidePos),
    #'start': convert_time(pos),
    #'end': convert_time(pos+item.length),
    'duration': convert_time(item.length),
    #'sourcePath': infile,
    'baseName': ntpath.basename(infile),
    
  } 
 
  return true



def msg(m, prefix=""):
    if isDev:
        RPR_ShowConsoleMsg(prefix + str(m) + "\n")

def getFormatFromName(name):
  formatString = ''
  if '.' in name:
    formatString = name.split('.')[1]
  return formatString

# remove some words from name
def formatName(name):
  wordsToRemove = ["_group_"]
  cleanedName = name
  for i in range(len(wordsToRemove)):
    if wordsToRemove[i] in name:
      cleanedName = name.split(wordsToRemove[i])[1]
  #remove format
  if '.' in cleanedName:
      cleanedName = name.split('.')[0]
  return cleanedName

for track in tracks:
    parent = track.parent_track

    # do not include group track in tracks
    if '_group_' not in track.name:
      config_tracks.append(track.name)

    if parent:
      if not parent.items:
        reapy.show_message_box("All _group_ tracks need a guide", "Hm")
        break
      else:
        groupGuide = parent.items[0]
      if '_group_' in parent.name:
        if formatName(parent.name) not in groups:         
          groupDict = create_item_dict(groupGuide,groupGuide)
          groups[formatName(parent.name)] = {
            'guide': groupDict, 
            'tracks': [],
            #'allItems': []
          }

        if '_group_' not in track.name:
          # don't included muted tracks
          if track.is_muted: continue
          takes = []
          if len(track.items) == 1:
            takes.append(create_item_dict(track.items[0], groupGuide, 0))
            #groups[formatName(parent.name)]['allItems'].append(create_item_dict(track.items[0], groupGuide,0))
          else:
          
            for idx,trackitem in enumerate(track.items, start=1):
              itemMuted = trackitem.get_info_value('B_MUTE')
              # don't included muted items
              if itemMuted:
                continue
              takes.append(create_item_dict(trackitem, groupGuide, idx))
              #groups[formatName(parent.name)]['allItems'].append(create_item_dict(trackitem, groupGuide, idx))

          groups[formatName(parent.name)]['tracks'].append({
            'track_name': track.name,
            'items': takes
          })
          
          

nameOut = ''

regionenums = RPR_EnumProjectMarkers(0, 0, 0, 0, nameOut, 0)

outputFolder = 'reaperExport/'
config_file = {
    'bpm': project.bpm,
    'tracks': config_tracks,
    'groups': groups,
    'audioPath' : outputFolder
}

project_root = os.path.abspath(os.path.join(project.path, os.pardir))
file_name = project_root + '/plan8.json'


with open(file_name, 'w', encoding='utf-8') as f:
    json.dump(config_file, f, ensure_ascii=False, indent=4)
    
devroot = os.path.abspath(path.join(project_root ,".."))

dst = devroot + '/static/plan8.json'
copyfile(file_name,dst )

source_dir = project_root + '/Bounce/'

file_names = os.listdir(source_dir)

target_dir = devroot + '/static/' + outputFolder

fileCount = -1
    
for file_name in file_names:
  fileCount += 1
  try:
    shutil.copy(os.path.join(source_dir, file_name), target_dir)
  except IOError as io_err:
    os.makedirs(os.path.dirname(target_dir))
    shutil.copy(os.path.join(source_dir, file_name), target_dir)
   



if isDev == False:
    reapy.show_message_box("All done", "Plan Exporter, moved " + str(fileCount) + " files to static directory")
