import binascii
import csv
import struct

import xml.etree.ElementTree as ET


def truncate_titleid(titleid: str):
    """
    Truncates the titleid
    :param titleid: the original TitleID
    :return: The truncated TitleID
    """
    return titleid[-8:].upper()


def parse_xml():
    """
    Parses
    :return: Returns a ga
    """
    # create element tree object
    tree = ET.parse('3dsreleases.xml')

    # get root element
    root = tree.getroot()

    gamesitems = []

    # iterate news items
    for item in root.findall('./'):
        games = {}

        for child in item:
            if child.tag == 'titleid':
                games["titleid"] = truncate_titleid(child.text)
            if child.tag == 'name':
                games["name"] = child.text
            if child.tag == 'region':
                games["region"] = child.text
            if child.tag in ('titleid', 'name', 'platform', 'region'):
                games["platform"] = "3DS"
        if games:
            gamesitems.append(games)
    with open('System.csv', mode='r') as f:
        csvFile = csv.reader(f)

        for lines in csvFile:
            games = {"name": lines[7], "titleid": truncate_titleid(lines[1]), "region": "", "platform": "System"}
            gamesitems.append(games)
    with open('DSi.csv', mode='r', encoding='utf-8') as f:
        csvFile = csv.reader(f)

        for lines in csvFile:
            games = {"name": lines[3], "titleid": truncate_titleid(lines[1]), "region": "", "platform": "DSi"}
            gamesitems.append(games)
    with open('eShop.csv', mode='r', encoding='utf-8') as f:
        csvFile = csv.reader(f)

        for lines in csvFile:
            if not any(dictionary['titleid'] == lines[1] for dictionary in gamesitems):
                games = {"name": lines[0], "titleid": truncate_titleid(lines[1]), "region": lines[5], "platform": "3DS"}
                gamesitems.append(games)
    with open('Manual.csv', mode='r', encoding='utf-8') as f:
        csvFile = csv.reader(f)

        for lines in csvFile:
            if not any(dictionary['titleid'] == lines[1] for dictionary in gamesitems):
                games = {"name": lines[1], "titleid": lines[0].upper(), "region": "", "platform": lines[2]}
                gamesitems.append(games)
    return gamesitems


releases = parse_xml('3dsreleases.xml')


def match_name(titleid: str):
    name = ""
    for release in releases:
        if release["titleid"].upper() == titleid.upper():
            if release["region"] == "USA":
                return release["name"]
            name = release["name"]
    return name


def match_platform(titleid: str):
    for release in releases:
        truncated_titleid = release["titleid"][-8:]
        if truncated_titleid == titleid.upper():
            return release["platform"]
    return ""


games = [["Truncated TitleID", "Name", "Time", "Times Played"]]
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
        print(entry)
        if entry:
            games.append(entry)
with open('3ds.csv', 'w', newline='') as f:
    write = csv.writer(f)
    write.writerows(games)
