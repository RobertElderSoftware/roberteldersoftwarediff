# This Python file uses the following encoding: utf-8
import subprocess
import random
import sys
import os
import platform
import codecs
import time

codecs.register(lambda name: codecs.lookup('utf-8') if name == 'cp65001' else None)

def is_probably_on_windows():
    p = platform.system().lower()
    if p.find("windows") != -1:
        return True
    elif p.find("cygwin") != -1:
        return True
    return False

random.seed(125)  #  For deterministic test result comparisons.

LINUX_PYTHON_EXECS = [u"python2", u"python3"]
LINUX_RES_DIFF_SCRIPT_LOCATION = u"roberteldersoftwarediff.py"

WINDOWS_PYTHON_EXECS = [u"C:\\Python27\\python.exe", u"C:\\Python361\\python.exe"]
WINDOWS_RES_DIFF_SCRIPT_LOCATION = u".\\roberteldersoftwarediff.py"

TEST_INPUT_FILES_LOCATION = u"tests"

input_files = []

for (dirpath, dirnames, filenames) in os.walk(TEST_INPUT_FILES_LOCATION):
    input_files.extend([dirpath + u"/" + f for f in filenames])

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
    u"utf_8_sig",
    #  Not really text encodings, but sure, why not?
    #  "idna",          Does not work with ignore errors
    u"palmos",
    #  "punycode",      Throws UnicodeDecodeError, but doesn't seem to use ignore error handler
    u"raw_unicode_escape",
    #  "rot_13",        It is not supported by str.encode() (which only produces bytes output)  
    #  See https://docs.python.org/3/library/codecs.html#text-transforms
    #  "undefined",     This one always triggers error by definition.
    u"unicode_escape",
    u"unicode_internal",
    #  "base64_codec",  Complains about always requiring strict errors.
    #  "bz2_codec",     Complains about always requiring strict errors.
    #  "hex_codec",     Complains about always requiring strict errors.
    #  "quopri_codec",  Complains about always requiring strict errors.
    #  "string_escape"  Not available in Python 3
    #  "uu_codec"       Complains about always requiring strict errors.
    #  "zlib_codec"     Complains about always requiring strict errors.
] + ([] if not is_probably_on_windows() else [
    u"mbcs"  #  Windows only
])

PYTHON_EXECS = LINUX_PYTHON_EXECS
RES_DIFF_SCRIPT_LOCATION = LINUX_RES_DIFF_SCRIPT_LOCATION

if is_probably_on_windows():
    PYTHON_EXECS = WINDOWS_PYTHON_EXECS
    RES_DIFF_SCRIPT_LOCATION = WINDOWS_RES_DIFF_SCRIPT_LOCATION

params = []

def get_random_nonquote_character():
    n = 34 #  Quote
    while n == 34:
        n = random.randint(32, 126) 

    return chr(n)

def get_random_delimiter():
    return "\"" + "".join([get_random_nonquote_character() for i in range(0, random.randint(0, 10))]) + "\""

def get_infile_param():
    return [input_files[random.randint(0,len(input_files)-1)]]

def get_random_encoding():
    return ENCODINGS[random.randint(0, len(ENCODINGS) -1)]

def get_output_encoding_param():
    return ["--output-encoding", get_random_encoding()]

def get_oldfile_encoding_param():
    return ["--oldfile-encoding", get_random_encoding()]

def get_newfile_encoding_param():
    return ["--newfile-encoding", get_random_encoding()]

def get_parameters_encoding_param():
    return ["--parameters-encoding", get_random_encoding()]

def get_delimiters_param():
    return ["--delimiters", get_random_delimiter()]

def get_push_delimiters_param():
    return ["--push-delimiters", get_random_delimiter()]

def get_pop_delimiters_param():
    return ["--pop-delimiters", get_random_delimiter()]

def get_cols_param():
    return ["--cols", str(random.randint(0,200))]

def get_lines_context_param():
    return ["--lines-context", str(random.randint(0,200))]

def get_enable_windows_terminal_colours_param():
    return ["--enable-windows-terminal-colours" ]

def get_disable_windows_terminal_colours_param():
    return ["--disable-windows-terminal-colours" ]

def get_enable_ansi_param():
    return ["--enable-ansi" ]

def get_disable_ansi_param():
    return ["--disable-ansi" ]

def get_verbose_param():
    return ["--verbose" ]

def get_infinite_context_param():
    return ["--infinite-context" ]

def get_max_line_length_param():
    return ["--max-line-length", str(random.randint(0,200))]

def get_oldfile_message_param():
    return ["--oldfile-message", get_random_delimiter()]

def get_newfile_message_param():
    return ["--newfile-message", get_random_delimiter()]

def get_disable_header_param():
    return ["--disable-header"]

def get_enable_mark_param():
    return ["--enable-mark"]

def get_disable_line_numbers_param():
    return ["--disable-line-numbers"]

def get_disable_colours_param():
    return ["--disable-colours"]

def get_include_delimiters_param():
    return ["--include-delimiters"]

def get_show_byte_offsets_param():
    return ["--show-byte-offsets"]

def get_outfile_param():
    return ["--outfile", "tmp_outfile_test" if is_probably_on_windows() else "/tmp/tmp_outfile_test"]

def get_random_params():
    params = []
    #  Two mandatory input files.
    params += get_infile_param()
    params += get_infile_param()

    if random.randint(0, 1) == 0:
        params += get_output_encoding_param()

    if random.randint(0, 1) == 0:
        params += get_oldfile_encoding_param()

    if random.randint(0, 1) == 0:
        params += get_newfile_encoding_param()

    if random.randint(0, 1) == 0:
        params += get_parameters_encoding_param()

    if random.randint(0, 1) == 0:
        params += get_delimiters_param()

    if random.randint(0, 1) == 0:
        params += get_push_delimiters_param()

    if random.randint(0, 1) == 0:
        params += get_pop_delimiters_param()

    if random.randint(0, 1) == 0:
        params += get_cols_param()

    if random.randint(0, 1) == 0:
        params += get_enable_windows_terminal_colours_param()

    if random.randint(0, 1) == 0:
        params += get_disable_windows_terminal_colours_param()

    if random.randint(0, 1) == 0:
        params += get_enable_ansi_param()

    if random.randint(0, 1) == 0:
        params += get_disable_ansi_param()

    if random.randint(0, 1) == 0:
        params += get_verbose_param()

    if random.randint(0, 1) == 0:
        params += get_infinite_context_param()

    if random.randint(0, 1) == 0:
        params += get_lines_context_param()

    if random.randint(0, 1) == 0:
        params += get_max_line_length_param()

    if random.randint(0, 1) == 0:
        params += get_oldfile_message_param()

    if random.randint(0, 1) == 0:
        params += get_newfile_message_param()

    if random.randint(0, 1) == 0:
        params += get_newfile_message_param()

    if random.randint(0, 1) == 0:
        params += get_disable_header_param()

    if random.randint(0, 1) == 0:
        params += get_enable_mark_param()

    if random.randint(0, 1) == 0:
        params += get_disable_line_numbers_param()

    if random.randint(0, 1) == 0:
        params += get_outfile_param()

    return params

def get_special_case_params():
    #  The windows and unix specific tests should be tested on both unix and Windows to detect crashes.
    special_cases = [
        [u"noexist", u"noexist"],
        [u"tests/ascii/ex1", u"noexist"],
        [u"noexist", u"tests/ascii/ex1"],
        [u"tests/ascii/ex1", u"tests/ascii/ex1", "--outfile", "/dev/null"],
        [u"tests/ascii/ex1", u"tests/ascii/ex2"],
        [u"tests/utf_8/ex3", u"tests/utf_8/ex4"],
        [u"tests/utf_8/ex3", u"tests/utf_8/ex4", u"--oldfile-encoding", u"\"utf-8\"", u"--newfile-encoding", u"\"utf-8\""],
        [u"tests/utf_8/ex3", u"tests/utf_8/ex4", u"--oldfile-encoding", u"\"utf-8\"", u"--newfile-encoding", u"\"utf-8\"", u"--output-encoding", u"\"utf-8\""],
        [u"tests/ascii/ex5", u"tests/ascii/ex6"],
        [u"tests/ascii/ex7", u"tests/ascii/ex8"],
        [u"tests/ascii/a.json", u"tests/ascii/b.json"],
        [u"tests/ascii/a.json", u"tests/ascii/b.json", u"--push-delimiters", u"\"{\"", u"\"[\"", u"--pop-delimiters", u"\"}\"", u"\"]\"", u"--include-delimiters"],
        [u"tests/utf_8/fancy1", u"tests/utf_8/fancy2", u"--delimiters", u"日本国", u"--include-delimiters", u"--parameters-encoding", u"\"utf-8\"", u"--output-encoding", u"\"utf-8\"", u"--newfile-encoding", u"\"utf-8\"", u"--oldfile-encoding", u"\"utf-8\""],
        [u"tests/utf_8/fancy1", u"tests/utf_8/fancy2", u"--delimiters", u"\"\\u65e5\\u672c\\u56fd\"", u"--include-delimiters", u"--parameters-encoding", u"\"utf-8\"", u"--output-encoding", u"\"utf-8\"", u"--newfile-encoding", u"\"utf-8\"", u"--oldfile-encoding", u"\"utf-8\""],
        [u"tests/utf_8/this-is-encoded-in-utf-8", u"tests/utf_16/this-is-encoded-in-utf-16", u"--output-encoding", u"\"utf-8\"", u"--newfile-encoding", u"\"utf-16\"", u"--oldfile-encoding", u"\"utf-8\"", u"--enable-mark"],
        [u"tests/ascii/a.html", u"tests/ascii/b.html", u"-m", u"html"]
    ]
    return special_cases[random.randint(0, len(special_cases)-1)]

current_visual_param_number = 0

def get_visual_test_params(enc):
    #  Tests where a human should check the output to see if it looks ok.
    all_cases = {
        "utf-8": [
            [u"tests/bytes-00-to-FF", u"tests/bytes-00-to-FF", u"--oldfile-encoding", u"latin_1", u"--newfile-encoding", u"latin_1", u"--output-encoding", u"utf-8", u"--infinite-context", u"--delimiters", u"\\n"],
            [u"tests/bytes-00-to-FF", u"tests/bytes-00-to-FF", u"--oldfile-encoding", u"iso8859_2", u"--newfile-encoding", u"iso8859_2", u"--output-encoding", u"utf-8", u"--infinite-context", u"--delimiters", u"\\n"],
            [u"tests/bytes-00-to-FF", u"tests/bytes-00-to-FF", u"--oldfile-encoding", u"iso8859_3", u"--newfile-encoding", u"iso8859_3", u"--output-encoding", u"utf-8", u"--infinite-context", u"--delimiters", u"\\n"],
            [u"tests/ascii/a.json", u"tests/ascii/b.json"],
            [u"tests/utf_8/delimit2", u"tests/utf_8/delimit1", u"--delimiters", u"\\u65e5\\u672c\\u56fd", u"--include-delimiters", u"--parameters-encoding", u"utf-8", u"--output-encoding", u"\"utf-8\"", u"--newfile-encoding", u"\"utf-8\"", u"--oldfile-encoding", u"\"utf-8\""],
            [u"tests/utf_8/shrug", u"tests/utf_16/shrug", u"--output-encoding", u"utf-8", u"--newfile-encoding", u"utf-16", u"--oldfile-encoding", u"utf-8", u"--delimiters", u"\\n"],
            [u"tests/big5hkscs/big5hkscs-test-big5hkscs", u"tests/utf_8/utf-8-test-big5hkscs", u"--oldfile-encoding", u"big5hkscs", u"--newfile-encoding", u"utf-8", u"--output-encoding", u"utf-8", u"--infinite-context", u"--delimiters", u"\\n"],
            [u"tests/gb2312/gb2312-test-gb2312", u"tests/utf_16/utf-16-test-gb2312", u"--oldfile-encoding", u"gb2312", u"--newfile-encoding", u"utf-16", u"--output-encoding", u"utf-8", u"--infinite-context", u"--delimiters", u"\\n"],
            [u"tests/cp866/cp866-test-cp866", u"tests/utf_32/utf-32-test-cp866", u"--oldfile-encoding", u"cp866", u"--newfile-encoding", u"utf-32", u"--output-encoding", u"utf-8", u"--infinite-context", u"--delimiters", u"\\n"],
            [u"tests/utf_8/utf-8-hebrew-test-2", u"tests/utf_8/utf-8-hebrew-test-1", u"--oldfile-encoding", u"utf-8", u"--newfile-encoding", u"utf-8", u"--output-encoding", u"utf-8", u"--infinite-context", u"--delimiters", u"\\n"],
            [u"tests/utf_8/utf-8-test-sanskrit-2", u"tests/utf_8/utf-8-test-sanskrit-1", u"--oldfile-encoding", u"utf-8", u"--newfile-encoding", u"utf-8", u"--output-encoding", u"utf-8", u"--infinite-context", u"--delimiters", u"\\n"]
        ],
        "big5hkscs": [
            [u"tests/big5hkscs/big5hkscs-test-big5hkscs", u"tests/utf_8/utf-8-test-big5hkscs", u"--oldfile-encoding", u"big5hkscs", u"--newfile-encoding", u"utf-8", u"--output-encoding", u"big5hkscs", u"--infinite-context", u"--delimiters", u"\\n"],
            [u"tests/big5hkscs/big5hkscs-test-big5hkscs", u"tests/utf_32/utf-32-test-big5hkscs", u"--oldfile-encoding", u"big5hkscs", u"--newfile-encoding", u"utf-32", u"--output-encoding", u"big5hkscs", u"--infinite-context", u"--delimiters", u"\\n"]
        ],
        "gb2312": [
            [u"tests/gb2312/gb2312-test-gb2312", u"tests/utf_16/utf-16-test-gb2312", u"--oldfile-encoding", u"gb2312", u"--newfile-encoding", u"utf-16", u"--output-encoding", u"gb2312", u"--infinite-context", u"--delimiters", u"\\n"]
        ],
        "cp866": [
            [u"tests/cp866/cp866-test-cp866", u"tests/utf_32/utf-32-test-cp866", u"--oldfile-encoding", u"cp866", u"--newfile-encoding", u"utf-32", u"--output-encoding", u"cp866", u"--infinite-context", u"--delimiters", u"\\n"]
        ]
    }
    global current_visual_param_number
    rtn = all_cases[enc][current_visual_param_number] if current_visual_param_number < len(all_cases[enc]) else None
    current_visual_param_number += 1
    return rtn;

def get_random_test_params():
    if random.randint(0, 1) == 0:
        return get_random_params()
    else:
        return get_special_case_params()

visual_mode = False
visual_test_encoding = "abcdef"
if len(sys.argv) > 1:
    visual_test_encoding = sys.argv[1]
    visual_mode = True

if visual_mode:
    print(u"Running tests in visual mode.  Expecting a human to watch results to see if they look fine.")

while True:
    python_exec = PYTHON_EXECS[random.randint(0,len(PYTHON_EXECS)-1)]
    params = []
    if visual_mode:
        p = get_visual_test_params(visual_test_encoding)
        if p is None:
            break
        params = [python_exec, RES_DIFF_SCRIPT_LOCATION] + p
    else:
        params = [python_exec, RES_DIFF_SCRIPT_LOCATION] + get_random_test_params()

    try:
        print(u"Begin test.  CMD is : " + (u" ".join(params)))
    except:
        print(u"Begin test.  CMD as bytes: " + str([bytearray(b, "utf-8") for b in params]))

    sys.stdout.flush()
    if visual_mode:
        time.sleep(1)
    rtn = subprocess.call(params)
    sys.stdout.flush()
    if visual_mode:
        time.sleep(1)
    if rtn > 0:
        #  Stop and make the error obvious.
        #  If the error is not in the list of known error codes.
        if not rtn in [100, 101, 102, 103, 104]:
            print(u"Saw unexpected return code: " + str(rtn))
            exit()
    print(u"Pass")
    sys.stdout.flush()
