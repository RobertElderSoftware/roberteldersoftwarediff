import os
import sys
import codecs

#  Must be run with python 3 in order to work

ENCODINGS = [
    u"ascii",
    u"big5",
    u"big5hkscs",
    u"cp037",
    u"cp424",
    u"cp437",
    u"cp500",
    u"cp720",
    u"cp737",
    u"cp775",
    u"cp850",
    u"cp852",
    u"cp855",
    u"cp856",
    u"cp857",
    u"cp858",
    u"cp860",
    u"cp861",
    u"cp862",
    u"cp863",
    u"cp864",
    u"cp865",
    u"cp866",
    u"cp869",
    u"cp874",
    u"cp875",
    u"cp932",
    u"cp949",
    u"cp950",
    u"cp1006",
    u"cp1026",
    u"cp1140",
    u"cp1250",
    u"cp1251",
    u"cp1252",
    u"cp1253",
    u"cp1254",
    u"cp1255",
    u"cp1256",
    u"cp1257",
    u"cp1258",
    u"euc_jp",
    u"euc_jis_2004",
    u"euc_jisx0213",
    u"euc_kr",
    u"gb2312",
    u"gbk",
    u"gb18030",
    u"hz",
    u"iso2022_jp",
    u"iso2022_jp_1",
    u"iso2022_jp_2",
    u"iso2022_jp_2004",
    u"iso2022_jp_3",
    u"iso2022_jp_ext",
    u"iso2022_kr",
    u"latin_1",
    u"iso8859_2",
    u"iso8859_3",
    u"iso8859_4",
    u"iso8859_5",
    u"iso8859_6",
    u"iso8859_7",
    u"iso8859_8",
    u"iso8859_9",
    u"iso8859_10",
    u"iso8859_13",
    u"iso8859_14",
    u"iso8859_15",
    u"iso8859_16",
    u"johab",
    u"koi8_r",
    u"koi8_u",
    u"mac_cyrillic",
    u"mac_greek",
    u"mac_iceland",
    u"mac_latin2",
    u"mac_roman",
    u"mac_turkish",
    u"ptcp154",
    u"shift_jis",
    u"shift_jis_2004",
    u"shift_jisx0213",
    u"utf_32",
    u"utf_32_be",
    u"utf_32_le",
    u"utf_16",
    u"utf_16_be",
    u"utf_16_le",
    u"utf_7",
    u"utf_8",
    u"utf_8_sig"
]

def get_code_points(e):
    rtn = u""
    for i in range (0, 255):
        try:
            c = bytes([i]).decode(e)
            rtn += c
        except:
            pass  #  Error, ignore this character
    return rtn

for e in ENCODINGS:
    msg = u"This file is encoded in " + e + "\r\nHere are there first 255 code points in this encoding:\r\n"
    print(msg)
    d = e
    if not os.path.exists(e):
        os.makedirs(e)
    filename = d + "/" + e
    f = codecs.open(filename, "w", encoding=e)
    points = get_code_points(e)
    try:
        f.write(msg + points)
    except:
        print("Encoding error writing to " + filename)
    f.close()
