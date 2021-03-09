import reapy

isDev = True

project = reapy.Project()

RPR_ClearConsole()

def msg(m, prefix=""):
    if isDev:
        RPR_ShowConsoleMsg(prefix + str(m) + "\n")

selectedItems = project.selected_items
if len(selectedItems) == 0:
    msg('No item selected')

split_points = []
track = selectedItems[0].track

for item in selectedItems:
    take = item.active_take
    for note in take.notes:
        point = {'start':note.start, 'pitch':note.pitch}
        split_points.append(point)
    item.update()

    for point in reversed(split_points):
        msg(point)
        item.split(point['start'])

    track_items = track.items

    for track_item in track_items:
        for point in split_points: 
            if point['start'] == track_item.position:
                RPR_GetSetMediaItemTakeInfo_String(track_item.active_take.id , "P_NAME", track_item.active_take.name + '_' + str(point['pitch']), True)

    
