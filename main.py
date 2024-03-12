import binascii
import csv
import struct

import xml.etree.ElementTree as ET


def truncate_titleid(titleid: str):
    """
    Truncates the titleid
    :param titleid: the original titleid
    :return: The truncated titleid
    """
    return titleid[-8:].upper()


def parse_data():
    """
    Parses the 3dsreleases.xml, DSi.csv, and eShop.csv
    :return: Returns a games dictionary with internal dictionaries with keys as the region
    """
    tree = ET.parse('3dsreleases.xml')
    root = tree.getroot()

    games = {}

    for item in root.findall('./'):
        # Goes through the XML
        game_details = {'platform': '3DS'}
        title_id = ''
        region = ''
        for child in item:
            if child.tag == 'titleid':
                title_id = truncate_titleid(child.text)
            if child.tag == 'name':
                game_details["name"] = child.text
            if child.tag == 'region':
                region = child.text
        if title_id:
            if title_id in games:
                games[title_id][region] = game_details
            else:
                games[title_id] = {region: game_details}
    with open('System.csv', mode='r') as f:
        csv_file = csv.reader(f)
        for lines in csv_file:
            title_id = truncate_titleid(lines[1])
            if title_id in games:
                games[title_id][''] = {"name": lines[7], "platform": "3DS System"}
            else:
                games[title_id] = {'': {"name": lines[7], "platform": "3DS System"}}

    with open('DSi.csv', mode='r', encoding='utf-8') as f:
        csv_file = csv.reader(f)
        for lines in csv_file:
            title_id = truncate_titleid(lines[1])
            if title_id in games:
                games[title_id][''] = {"name": lines[3], "platform": "DSi", "region": lines[4]}
            else:
                games[title_id] = {'': {"name": lines[3], "platform": "DSi", "region": lines[4]}}
    with open('eShop.csv', mode='r', encoding='utf-8') as f:
        csv_file = csv.reader(f)
        for lines in csv_file:
            title_id = truncate_titleid(lines[1])
            if lines[5] == 'Japan':
                lines[5] = 'JPN'
            if lines[5] == 'Europe/Australia':
                lines[5] = 'EUR'
            if lines[5] == 'China':
                lines[5] = 'CHN'
            if lines[5] == 'Korea':
                lines[5] = 'KOR'
            if title_id not in games:
                games[title_id] = {'': {"name": lines[0], "platform": "3DS", "region": lines[5]}}
            elif lines[5] not in games[title_id]:
                games[title_id][lines[5]] = {"name": lines[0], "platform": "3DS", "region": lines[5]}
    # with open('Manual.csv', mode='r', encoding='utf-8') as f:
    #     csvFile = csv.reader(f)
    #
    #     for lines in csvFile:
    #         if not any(dictionary['titleid'] == lines[1] for dictionary in gamesitems):
    #             game = {"name": lines[1], "titleid": lines[0].upper(), "region": "", "platform": lines[2]}
    #             gamesitems.append(game)
    return games


releases = parse_data()


#
def match_name(titleid: str, region_priority=("USA", "EUR", "JPN", "KOR")):
    titleid = titleid.upper()
    if releases.get(titleid):
        for region in region_priority:
            if region in releases[titleid]:
                return releases[titleid][region]["name"]
        return next(iter(releases[titleid.upper()].values()))['name']
    return "Unknown"


def match_platform(titleid: str):
    print(titleid.upper())
    if titleid.upper() in releases:
        return next(iter(releases[titleid.upper()].values()))['platform']
    return "Unknown"

games_csv = [["Truncated TitleID", "Name", "Time", "Times Played"]]
with open('pld.dat', 'rb') as f:
    file = f.read()
    file = file[0x000C3510:]
    string_nospace = ""
    for b in file:
        w = "{0:0{1}x}".format(b, 2)
        string_nospace += w
    file = file[:int(string_nospace.find("00ffcf0b") / 2)]
    file_bitarray = bytearray(file)
    split_bitarray = [file_bitarray[i:i + 24] for i in range(0, len(file_bitarray), 24)]
    for array in split_bitarray:
        reversed_array = array[0:4]
        time_played = int.from_bytes(array[8:12], byteorder='little', signed=False)
        times_opened = struct.unpack('H', array[12:14])[0]
        # Reverses in next line
        reversed_array.reverse()
        titleid = ''.join(["{0:0{1}x}".format(x, 2) for x in reversed_array])
        entry = [titleid, match_name(titleid), match_platform(titleid), time_played, times_opened]
        if entry:
            games_csv.append(entry)
with open('3ds.csv', 'w', newline='') as f:
    write = csv.writer(f)
    write.writerows(games_csv)
