#!/usr/bin/python

#  Copyright 2017 Robert Elder Software Inc.
#  
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#  
#      http://www.apache.org/licenses/LICENSE-2.0
#  
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

import os
import time
import sys
import argparse
import codecs
import unicodedata
import platform
import subprocess
import signal
import traceback
import ctypes

codecs.register(lambda name: codecs.lookup('utf-8') if name == 'cp65001' else None)

MISSING_BYTE_ORDER_MARKER_EXIT_CODE = 100
TERMINAL_WIDTH_ERROR_EXIT_CODE = 101
COMMON_PREFIX_ERROR_EXIT_CODE = 102
FILE_OPEN_FAIL_ERROR_EXIT_CODE = 103
INVALID_MAX_LINE_LENGTH_ERROR_EXIT_CODE = 104

UNIX_INSERTION_COLOUR = 42
UNIX_DELETION_COLOUR = 41
UNIX_CHANGE_COLOUR = 44
UNIX_CORRECT_COLOUR = 32
UNIX_INCORRECT_COLOUR = 31

INSERTION_COLOUR = 1
DELETION_COLOUR = 2
CHANGE_COLOUR = 3
CORRECT_COLOUR = 4
INCORRECT_COLOUR = 5

GLOBAL_RUN_PARAMS = None  #  For use in signal handler.

def make_unix_terminal_interface(rp):
    class UnixTerminalInterface(object):
        def __init__(self, rp):
            self.semi = e_encode(u";", rp.output_encoding, "internal")
            self.esc = e_encode(u"\033", rp.output_encoding, "internal")
            self.m = e_encode(u"m", rp.output_encoding, "internal")
            self.open_sq = e_encode(u"[", rp.output_encoding, "internal")
            self.zero = e_encode(u"0", rp.output_encoding, "internal")
            self.rp = rp

            self.terminal_width = None
            try:
                p = subprocess.Popen(["stty", "size"], stdout=subprocess.PIPE)
                out, err = p.communicate()
                if p.returncode == 0:
                    self.terminal_width = int((out.split()[1]))
            except:
                pass

            self.num_colours_supported = None
            try:
                p = subprocess.Popen(["tput", "colors"], stdout=subprocess.PIPE)
                out, err = p.communicate()
                if p.returncode == 0:
                    self.num_colours_supported = int(out)
            except:
                pass

        def unix_colour_lookup(self, c):
            if c == INSERTION_COLOUR:
                return UNIX_INSERTION_COLOUR
            elif c == DELETION_COLOUR:
                return UNIX_DELETION_COLOUR
            elif c == CHANGE_COLOUR:
                return UNIX_CHANGE_COLOUR
            elif c == CORRECT_COLOUR:
                return UNIX_CORRECT_COLOUR
            elif c == INCORRECT_COLOUR:
                return UNIX_INCORRECT_COLOUR
            else:
                raise Exception("Unknown unix colour." + str(c))

        def set_terminal_colours(self, colours):
            colours_encoded_strings = [as_byte_string(str(self.unix_colour_lookup(k)), self.rp.output_encoding, "internal") for k in colours]
            colours_with_semi = self.semi.join(colours_encoded_strings)
            output_bytes(self.esc + self.open_sq + colours_with_semi + self.m, self.rp)

        def reset_terminal_colours(self):
            output_bytes(self.esc + self.open_sq + self.zero + self.m, self.rp)

        def as_unicode(self):
            rtn = u""
            #  Used for debugging
            rtn += u"terminal_width: " + py23_str(self.terminal_width, self.rp.output_encoding, "internal") + self.rp.output_newline
            rtn += u"num_colours_supported: " + py23_str(self.num_colours_supported, self.rp.output_encoding, "internal") + self.rp.output_newline
            return rtn

        def output_test(self):
            nl = self.rp.output_newline
            output_bytes(e_encode(u"Begin Unix Terminal Interface Test" + nl, self.rp.output_encoding, "internal"), self.rp)
            colours = [INSERTION_COLOUR, DELETION_COLOUR, CHANGE_COLOUR, CORRECT_COLOUR, INCORRECT_COLOUR]
            colours_n = [u"INSERTION_COLOUR", u"DELETION_COLOUR", u"CHANGE_COLOUR", u"CORRECT_COLOUR", u"INCORRECT_COLOUR"]
            for i in range(0,len(colours)):
                #  Flush any previous output
                sys.stdout.flush()
                self.set_terminal_colours([colours[i]])
                output_bytes(e_encode(u"This text should be coloured with " + colours_n[i], self.rp.output_encoding, "internal"), self.rp)
                sys.stdout.flush()
                self.reset_terminal_colours()
                output_bytes(e_encode(nl, self.rp.output_encoding, "internal"), self.rp)
            out_c = u"U"
            str_width = py23_str(self.terminal_width, self.rp.output_encoding, "internal")
            output_bytes(e_encode(u"The next line should exactly fill the terminal width with " + str_width + u" '" + out_c + u"' characters:" + nl, self.rp.output_encoding, "internal"), self.rp)
            if self.terminal_width is not None and self.terminal_width > 0:
                for i in range(0, self.terminal_width):
                    output_bytes(e_encode(out_c, self.rp.output_encoding, "internal"), self.rp)

    return UnixTerminalInterface(rp)

def make_windows_terminal_interface(rp):
    try:
        from ctypes import windll, wintypes
        try:
            class COORD(ctypes.Structure):
                _fields_ = [
                    ("x", ctypes.c_short),
                    ("y", ctypes.c_short)
                ]
            
            class RECT(ctypes.Structure):
                _fields_ = [
                    ("left", ctypes.c_short),
                    ("top", ctypes.c_short),
                    ("right", ctypes.c_short),
                    ("bottom", ctypes.c_short)
                ]
            
            class CSBI(ctypes.Structure):
                _fields_ = [
                    ("dwSize", COORD),
                    ("dwCursorPosition", COORD),
                    ("wAttributes", ctypes.c_ushort),
                    ("srWindow", RECT),
                    ("dwMaximumWindowSize", COORD)
                ]
            
            class WindowsTerminalInterface(object):
                def __init__(self, rp):
                    self.rp = rp
                    self.WINDOWS_INSERTION_COLOUR = 0x0020
                    self.WINDOWS_DELETION_COLOUR = 0x0040
                    self.WINDOWS_CHANGE_COLOUR = 0x0010
                    self.WINDOWS_CORRECT_COLOUR = 0x0002
                    self.WINDOWS_INCORRECT_COLOUR = 0x0004
                    self.original_colour_mask = 0xFFFFFF0F  #  Erase background colour, and keep current font colour.
                    #  Define the foreign function interfaces (required in Python 3)
                    windll.Kernel32.GetStdHandle.restype = ctypes.c_ulong
                    windll.kernel32.GetStdHandle.argtypes = [ctypes.c_ulong]
                    windll.kernel32.GetConsoleScreenBufferInfo.restype = ctypes.c_ulong
                    windll.kernel32.GetConsoleScreenBufferInfo.argtypes = [wintypes.HANDLE, ctypes.POINTER(CSBI)]
                    windll.kernel32.SetConsoleTextAttribute.restype = ctypes.c_ulong
                    windll.kernel32.SetConsoleTextAttribute.argtypes = [wintypes.HANDLE, ctypes.c_ushort]
                    windll.kernel32.GetLastError.restype = ctypes.c_ulong
                    #  Setup stream handles
                    self.STD_INPUT_HANDLE_NUMBER = ctypes.c_ulong(0xfffffff6) # -10
                    self.STD_OUTPUT_HANDLE_NUMBER = ctypes.c_ulong(0xfffffff5) # -11
                    self.STD_ERROR_HANDLE_NUMBER = ctypes.c_ulong(0xfffffff4) # -12
                    self.STD_INPUT_HANDLE = windll.kernel32.GetStdHandle(self.STD_INPUT_HANDLE_NUMBER)
                    self.STD_OUTPUT_HANDLE = windll.kernel32.GetStdHandle(self.STD_OUTPUT_HANDLE_NUMBER)
                    self.STD_ERROR_HANDLE = windll.kernel32.GetStdHandle(self.STD_ERROR_HANDLE_NUMBER)
                    self.csbi = CSBI()
                    self.GetConsoleScreenBufferInfo_result_code = windll.kernel32.GetConsoleScreenBufferInfo(self.STD_OUTPUT_HANDLE, self.csbi)
                    if self.GetConsoleScreenBufferInfo_result_code > 0:
                        #  Save this so we can reset it later
                        self.csbi_wAttributes_original = self.csbi.wAttributes
                        self.terminal_width = int(self.csbi.dwSize.x)
                        self.GetConsoleScreenBufferInfo_last_error = None
                    else:
                        self.csbi_wAttributes_original = None
                        self.terminal_width = None
                        self.GetConsoleScreenBufferInfo_last_error = windll.kernel32.GetLastError()
            
                def windows_colour_lookup(self, c):
                    if c == INSERTION_COLOUR:
                        return self.WINDOWS_INSERTION_COLOUR
                    elif c == DELETION_COLOUR:
                        return self.WINDOWS_DELETION_COLOUR
                    elif c == CHANGE_COLOUR:
                        return self.WINDOWS_CHANGE_COLOUR
                    elif c == CORRECT_COLOUR:
                        return self.WINDOWS_CORRECT_COLOUR
                    elif c == INCORRECT_COLOUR:
                        return self.WINDOWS_INCORRECT_COLOUR
                    else:
                        raise Exception("Unknown windows colour." + str(c))
            
                def set_terminal_colours(self, colours):
                    new_colour = self.csbi_wAttributes_original & self.original_colour_mask
                    for c in colours:
                        new_colour = new_colour | self.windows_colour_lookup(c)
                    windll.kernel32.SetConsoleTextAttribute(self.STD_OUTPUT_HANDLE, ctypes.c_ushort(new_colour))
            
                def reset_terminal_colours(self):
                    windll.kernel32.SetConsoleTextAttribute(self.STD_OUTPUT_HANDLE, ctypes.c_ushort(self.csbi_wAttributes_original))
            
                def as_unicode(self):
                    nl = self.rp.output_newline
                    rtn = u""
                    #  Used for debugging
                    rtn += u"STD_INPUT_HANDLE_NUMBER: " + py23_str(self.STD_INPUT_HANDLE_NUMBER, self.rp.output_encoding, "internal") + nl
                    rtn += u"STD_OUTPUT_HANDLE_NUMBER: " + py23_str(self.STD_OUTPUT_HANDLE_NUMBER, self.rp.output_encoding, "internal") + nl
                    rtn += u"STD_ERROR_HANDLE_NUMBER: " + py23_str(self.STD_ERROR_HANDLE_NUMBER, self.rp.output_encoding, "internal") + nl
                    rtn += u"STD_INPUT_HANDLE: " + py23_str(self.STD_INPUT_HANDLE, self.rp.output_encoding, "internal") + nl
                    rtn += u"STD_OUTPUT_HANDLE: " + py23_str(self.STD_OUTPUT_HANDLE, self.rp.output_encoding, "internal") + nl
                    rtn += u"STD_ERROR_HANDLE: " + py23_str(self.STD_ERROR_HANDLE, self.rp.output_encoding, "internal") + nl
                    rtn += u"original_colour_mask: " + py23_str(self.original_colour_mask, self.rp.output_encoding, "internal") + nl
                    rtn += u"GetConsoleScreenBufferInfo_result_code (0 means error): " + py23_str(self.GetConsoleScreenBufferInfo_result_code, self.rp.output_encoding, "internal") + nl
                    rtn += u"GetConsoleScreenBufferInfo_last_error: " + py23_str(self.GetConsoleScreenBufferInfo_last_error, self.rp.output_encoding, "internal") + nl
                    rtn += u"csbi_wAttributes_original: " + py23_str(self.csbi_wAttributes_original, self.rp.output_encoding, "internal") + nl
                    rtn += u"terminal_width: " + py23_str(self.terminal_width, self.rp.output_encoding, "internal") + nl
                    return rtn
            
                def output_test(self):
                    nl = self.rp.output_newline
                    output_bytes(e_encode(u"Begin Windows Terminal Interface Test" + nl, self.rp.output_encoding, "internal"), self.rp)
                    colours = [INSERTION_COLOUR, DELETION_COLOUR, CHANGE_COLOUR, CORRECT_COLOUR, INCORRECT_COLOUR]
                    colours_n = [u"INSERTION_COLOUR", u"DELETION_COLOUR", u"CHANGE_COLOUR", u"CORRECT_COLOUR", u"INCORRECT_COLOUR"]
                    if self.csbi_wAttributes_original:
                        for i in range(0,len(colours)):
                            sys.stdout.flush()
                            self.set_terminal_colours([colours[i]])
                            output_bytes(e_encode(u"This text should be coloured with " + colours_n[i], self.rp.output_encoding, "internal"), self.rp)
                            sys.stdout.flush()
                            self.reset_terminal_colours()
                            output_bytes(e_encode(self.rp.output_newline, self.rp.output_encoding, "internal"), self.rp)
                        out_c = u"W"
                        str_width = py23_str(self.terminal_width, self.rp.output_encoding, "internal")
                        output_bytes(e_encode(u"The next line should exactly fill the terminal width with " + str_width + u" '" + out_c + u"' characters:" + self.rp.output_newline, self.rp.output_encoding, "internal"), self.rp)
                        if self.terminal_width is not None and self.terminal_width > 0:
                            for i in range(0, self.terminal_width):
                                output_bytes(e_encode(out_c, self.rp.output_encoding, "internal"), self.rp)
                    else:
                        output_bytes(e_encode(u"csbi_wAttributes_original not set:  Skipping output test." + nl, self.rp.output_encoding, "internal"), self.rp)
            
            return WindowsTerminalInterface(rp)
        except Exception as e:
            traceback.print_exc()  #  If import worked, but there was a problem, we want to know about it.
    except:
        return None #  Don't worry about the windows interface if import fails



try:  #  Only works on unix
    signal.signal(signal.SIGPIPE,signal.SIG_DFL) #  Don't throw exceptions when piping.
except:
    pass

def do_graceful_exit(rp, exit_code):
    if rp and hasattr(rp, "use_windows_terminal_colours") and rp.use_windows_terminal_colours:
        try:
            rp.windows_terminal_interface.reset_terminal_colours()
        except:
            pass

    if rp and hasattr(rp, "use_ansi") and rp.use_ansi:
        try:
            rp.unix_terminal_interface.reset_terminal_colours()
        except:
            pass

    if rp and hasattr(rp, "outfile_f") and rp.outfile_f is not None:
        try:
            #  Close the output file
            if rp.outfile_f is not None:
                rp.outfile_f.close()
        except:
            pass
    sys.exit(exit_code)

def on_sigint_handler(signal, frame):
    global GLOBAL_RUN_PARAMS
    do_graceful_exit(GLOBAL_RUN_PARAMS, 0)
    
signal.signal(signal.SIGINT, on_sigint_handler)


disable_implicit_encoding = True  #  Used to help catch implicit encoding in python2
default_encoding = sys.getdefaultencoding()

if disable_implicit_encoding:
    try:
        reload(sys)
        sys.setdefaultencoding("undefined")
    except:
        pass

def diff(e, f, i=0, j=0):
  #  Documented at http://blog.robertelder.org/diff-algorithm/
  N,M,L,Z = len(e),len(f),len(e)+len(f),2*min(len(e),len(f))+2
  if N > 0 and M > 0:
    w,g,p = N-M,[0]*Z,[0]*Z
    for h in range(0, (L//2+(L%2!=0))+1):
      for r in range(0, 2):
        c,d,o,m = (g,p,1,1) if r==0 else (p,g,0,-1)
        for k in range(-(h-2*max(0,h-M)), h-2*max(0,h-N)+1, 2):
          a = c[(k+1)%Z] if (k==-h or k!=h and c[(k-1)%Z]<c[(k+1)%Z]) else c[(k-1)%Z]+1
          b = a-k
          s,t = a,b
          while a<N and b<M and e[(1-o)*N+m*a+(o-1)]==f[(1-o)*M+m*b+(o-1)]:
            a,b = a+1,b+1
          c[k%Z],z=a,-(k-w)
          if L%2==o and z>=-(h-o) and z<=h-o and c[k%Z]+d[z%Z] >= N:
            D,x,y,u,v = (2*h-1,s,t,a,b) if o==1 else (2*h,N-a,M-b,N-s,M-t)
            if D > 1 or (x != u and y != v):
              return diff(e[0:x],f[0:y],i,j)+diff(e[u:N],f[v:M],i+u,j+v)
            elif M > N:
              return diff([],f[N:M],i+N,j+N)
            elif M < N:
              return diff(e[M:N],[],i+M,j+M)
            else:
              return []
  elif N > 0: #  Modify the return statements below if you want a different edit script format
    return [{"operation": "delete", "position_old": i+n} for n in range(0,N)]
  else:
    return [{"operation": "insert", "position_old": i,"position_new":j+n} for n in range(0,M)]


err_source = None
err_counts = None

def initialize_error_counts_object(oldfile_encoding, oldfile_as_binary, newfile_encoding, newfile_as_binary, output_encoding, parameters_encoding):
    global err_counts
    err_counts = {
        "parameters": {
            "src" : u"Command line parameters",
            "dst" : parameters_encoding,
            "count" : 0
        },
        "oldfile": {
            "src" : u"binary oldfile" if oldfile_as_binary else oldfile_encoding,
            "dst" : output_encoding,
            "count" : 0
        },
        "newfile": {
            "src" : u"binary newfile" if newfile_as_binary else newfile_encoding,
            "dst" : output_encoding,
            "count" : 0
        },
        "internal": {
            "src" : u"internal constants",
            "dst" : output_encoding,
            "count" : 0
        }
    }

def ignore_errors(e):
    err_counts[err_source]["count"] += 1
    return (u"", e.end)  #  Skip this character

def e_encode(s, enc, err):
    global err_source
    err_source = err  #  So we can properly attribute where the error came from.
    return codecs.encode(s, enc, "ignore")

def e_decode(s, enc, err):
    global err_source
    err_source = err  #  So we can properly attribute where the error came from.
    return codecs.decode(s, enc, "ignore")

codecs.register_error("ignore", ignore_errors)

def group_unicode_characters(s):
    #  This function groups together unicode 'characters' that are
    #  really one unicode 'character'.  This is done specifically to
    #  consider cases where multiple surrogate characters that are split
    #  in certain versions/configurations of python.

    #  For example,
    #  len([c for c in u"\U0001D517"]) == 1 in Python 2.7.12 on Linux
    #  len([c for c in u"\U0001D517"]) == 2 in Python 2.7.13 on Windows
    #  len([c for c in u"\U0001D517"]) == 1 in Python 3.6.1 on Windows
    rtn = []
    i = 0
    while i < len(s):
        #  Check for surrogate pairs
        if ord(s[i]) >= 0xD800 and ord(s[i]) <= 0xDBFF and (i + 1) < len(s) and ord(s[i + 1]) >= 0xDC00 and ord(s[i + 1]) <= 0xDFFF:
            rtn.append([s[i], s[i+1]])
            i += 1
        else:
            rtn.append([s[i]])
        i += 1
    return rtn

def encode_unicode_characters(chrs, enc, src):
    #  Expects chrs to be an array of arrays where each innner
    #  array contains either one or two unicode character code points.
    #  An inner array will contain two unicode code points in some
    #  cases for surrogate pairs.
    #  Join any possible surrogate pairs before they are encoded.
    return [e_encode(u"".join(parts), enc, src) for parts in chrs]

def is_unicode_instance(s):
    #  Works in Python 2 and 3
    rtn = False
    try:
        if type(s) == unicode:
            rtn = True
    finally:
        return rtn

#  Normalization functions for Python 2/3 compatability
def string_as_int_array(a, enc, err):
    #  Turn a string or byte array into an array of ordinal numbers that identify the bytes.
    return [py23_ord(b) for b in as_byte_string(a, enc, err)]

def int_array_as_byte_string(a):
    #  Turn an array of ordinal numbers that identify the bytes into a byte string or bytes.
    assert(type(a) == list)
    for b in a:
        assert(type(b) == int)
    return bytes(bytearray(a))

def py23_str(o, enc, err):
    #  Turns anything (such as an int) into a unicode string.
    return e_decode(as_byte_string(str(o), enc, err), enc, err) 

def as_byte_string(s, enc, err):
    #  Make sure we know we're dealing with a byte string
    if is_unicode_instance(s):  #  Python 2 unicode
        return e_encode(s, enc, err)
    else:
        if type(s) == bytes and type(s) == str:  #  Python 2 str
            return s
        elif type(s) == bytes and not type(s) == str:  #  Python 3 bytes
            return s
        elif not type(s) == bytes and type(s) == str:  #  Python 3 str
            return e_encode(s, enc, err)  # Python3 bytes, or python2 str
        else:
            assert(0)

def py23_ord(c):
    #  Return the ordinal number that corresponds to a given byte.
    if type(c) is int:
        return c
    else:
        #  Unicode, or python 3 str
        return ord(c)

def portable_escape(s, enc, err):
    #  Escapes unicode and control characters in python 2 and 3
    return e_encode(e_decode(s, enc, err), "unicode-escape", err)

def de_double_slashes(int_array):
    #  Takes a list of integers representing each byte value of the string
    #  then removes any instance of double slashes.
    #  Returns a binary string.
    new_array = []
    last_c = None
    for c in int_array:
        if last_c == 92 and c == 92:
            pass #  Ignore this extra slash
        else:
            new_array.append(c)
        last_c = c
    return int_array_as_byte_string(new_array)

def evaluate_escape_sequences(s, enc, err):
    #  This function will return a byte string where all
    #  embedded unicode or hex escape sequences have been evaluated.
    #  The reason for using this function and not 'unicode-escape' directly
    #  is because 'unicode-escape' does not work when there are already
    #  unicode characters in the string.
    double_escaped_unicode = portable_escape(s, enc, err)
    bytes_as_ints = string_as_int_array(double_escaped_unicode, enc, err)
    return e_decode(de_double_slashes(bytes_as_ints), "unicode-escape", err)

def get_parts_for_change_region(edit_script, i, ins, dels):
    parts = []
    #  This is the size of the 'changed' region.
    square_size = min(len(ins), len(dels))
    #  These are the inserts and deletes that have been paired up
    for n in range(0, square_size):
        parts.append({"operation": "change", "position_old": edit_script[dels[n]]["position_old"] ,"position_new": edit_script[ins[n]]["position_new"]})
    #  These are the leftover inserts, that must be pushed 'square_size' units to the right.
    for n in range(square_size, len(ins)):
        m = edit_script[ins[n]]
        #  Adjust the insertion positions so the offsets make sense in the simplified path.
        shift_right = square_size - (m["position_old"] - edit_script[i]["position_old"])
        p = {"operation": "insert", "position_old": m["position_old"] + shift_right, "position_new": m["position_new"]}
        parts.append(p)

    #  These are the leftover deletes.
    for n in range(square_size, len(dels)):
        m = edit_script[dels[n]]
        parts.append(m)

    return parts


def simplify_edit_script(edit_script):
    #  If we find a contiguous path composed of inserts and deletes, make them into 'changes' so they
    #  can produce more visually pleasing diffs.
    new_edit_script = []
    m = len(edit_script)
    i = 0
    while i < m:
        others = []
        ins = []
        dels = []
        last_indx = edit_script[i]["position_old"]
        #  Follow the path of inserts and deletes
        while i + len(ins) + len(dels) < m:
            indx = i + len(ins) + len(dels)
            edit = edit_script[indx]
            if edit["operation"] == "insert" and edit["position_old"] == last_indx:
                last_indx = edit["position_old"]
                ins.append(indx)
            elif edit["operation"] == "delete" and edit["position_old"] == last_indx:
                last_indx = edit["position_old"] + 1
                dels.append(indx)
            else:
                if edit["operation"] == "insert" or edit["operation"] == "delete":
                    pass #  Non-contiguous insert or delete.
                else:  #  The current edit is something other than delete or insert, just add it...
                    others.append(indx)
                break
        if len(ins) > 0 and len(dels) > 0:
            #  Do simplify
            new_edit_script.extend(get_parts_for_change_region(edit_script, i, ins, dels))
        else:
            #  Add the lone sequence of deletes or inserts
            for r in range(0, len(dels)):
                new_edit_script.append(edit_script[dels[r]])
            for r in range(0, len(ins)):
                new_edit_script.append(edit_script[ins[r]])
        for r in range(0, len(others)):
            new_edit_script.append(edit_script[others[r]])
        i += len(ins) + len(dels) + len(others)
    return new_edit_script


def is_probably_on_windows():
    p = platform.system().lower()
    if p.find("windows") != -1:
        return True
    elif p.find("cygwin") != -1:
        return True
    return False

def read_char(in_fileobj, file_encoding, rp, file_source, as_binary):
    c = None
    try:
        c = in_fileobj.read(1)
    except UnicodeError as e:
        src = e_decode(as_byte_string(file_source, rp.output_encoding, "internal"), rp.output_encoding, "internal")
        msg = e_decode(as_byte_string(str(e), rp.output_encoding, "internal"), rp.output_encoding, "internal")
        output_bytes(e_encode(u"Fatal unicode error from " + src + u": " + msg + rp.output_newline, rp.output_encoding, "internal"), rp)
        do_graceful_exit(rp, MISSING_BYTE_ORDER_MARKER_EXIT_CODE)

    if as_binary:
        more_chars = c != b""
    else:
        more_chars = c != u""
        #  Get the bytes instead of characters
        c = e_encode(c, file_encoding, file_source)

    if not rp.pretty_output:  #  Try to convert it to the output format right away
        c = e_encode(e_decode(c, file_encoding, file_source), rp.output_encoding, file_source)

    return more_chars, c

def do_file_open_fail_error(f, e, rp):
    fname = e_decode(as_byte_string(f, rp.output_encoding, "internal"), rp.output_encoding, "internal")
    msg = e_decode(as_byte_string(str(e), rp.output_encoding, "internal"), rp.output_encoding, "internal")
    output_bytes(e_encode(u"Failed to open file " + fname + u": " + msg + rp.output_newline, rp.output_encoding, "internal"), rp)
    do_graceful_exit(rp, FILE_OPEN_FAIL_ERROR_EXIT_CODE)

def read_file_as_list(infile, rp, file_encoding, file_source, as_binary):
    indentation_levels = []
    byte_offsets = []
    rtn = []
    in_fileobj = None
    current_level = 0
    current_byte_offset = 0

    global err_source
    err_source = file_source

    if as_binary:
        try:
            in_fileobj = open(infile, "rb")
        except Exception as e:
            do_file_open_fail_error(infile, e, rp)
    else:
        try:
            in_fileobj = codecs.open(infile, "r", encoding=file_encoding, errors="ignore")
        except Exception as e:
            do_file_open_fail_error(infile, e, rp)
    line = b''
    try:
        num_reads = 1
        more_chars, c = read_char(in_fileobj, file_encoding, rp, file_source, as_binary)
        #  Note u"".encode("utf-16") == b"\xff\xfe", so be careful on loop termination.
        while more_chars:
            line = line + c
            for d in rp.delimiters:
                position = line.find(d["delimiter"])
                if position != -1:
                    if position > 0:  #  Avoid adding empty lines
                        rtn.append(line[0:position])
                        byte_offsets.append(current_byte_offset)
                        current_byte_offset += len(bytearray(line[0:position]))
                        indentation_levels.append(current_level)
                    level_before = current_level
                    current_level += d["level_adjust"]
                    if current_level < 0:
                        current_level = 0
                    if rp.include_delimiters:
                        rtn.append(line[position:]) #  Only if you want to include delimiters.
                        indentation_levels.append(min(current_level, level_before))
                        byte_offsets.append(current_byte_offset)
                        current_byte_offset += len(bytearray(line[position:]))
                    line = b''
            #  For cutting long lines into multiple lines
            if rp.cut_lines:
                if num_reads == rp.max_line_length:
                    num_reads = 0
                    rtn.append(line)
                    indentation_levels.append(current_level)
                    byte_offsets.append(current_byte_offset)
                    current_byte_offset += len(bytearray(line))
                    line = b''
            more_chars, c = read_char(in_fileobj, file_encoding, rp, file_source, as_binary)
            num_reads += 1
        if len(line) > 0:
            rtn.append(line)
            indentation_levels.append(current_level)
            byte_offsets.append(current_byte_offset)
            current_byte_offset += len(bytearray(line))
    finally:
        in_fileobj.close()
        #  Add an extra entry so we know how long the entire thing is.
        byte_offsets.append(current_byte_offset)
    return rtn, byte_offsets, indentation_levels


def get_terminal_width(rp, unix_terminal_interface, windows_terminal_interface):
    if unix_terminal_interface is not None:
        if unix_terminal_interface.terminal_width is not None:
            if unix_terminal_interface.terminal_width > 0:
                return unix_terminal_interface.terminal_width

    if windows_terminal_interface is not None:
        if windows_terminal_interface.terminal_width is not None:
            if windows_terminal_interface.terminal_width > 0:
                return windows_terminal_interface.terminal_width

    #  Give up and assume 80 wide
    msg = u"WARNING:  Unable to determine terminal width so defaulting to 80.  You can specify with --cols flag." + rp.output_newline
    b = e_encode(msg, rp.output_encoding, "internal") 
    output_bytes(b, rp)
    default_width = 80
    return default_width

def validate_delimiters(delimiters, rp):
    for i in range(0, len(delimiters)):
        for j in range(0, len(delimiters)):
            if i != j:
                if delimiters[i]["delimiter"].find(delimiters[j]["delimiter"]) == 0:
                    d1 = e_decode(delimiters[i]["delimiter"], rp.parameters_encoding, "parameters")
                    d2 = e_decode(delimiters[j]["delimiter"], rp.parameters_encoding, "parameters")
                    d1 = e_encode(d1, "unicode-escape", "internal")
                    d2 = e_encode(d2, "unicode-escape", "internal")
                    d1 = e_decode(d1, "utf-8", "internal")
                    d2 = e_decode(d2, "utf-8", "internal")
                    msg = u"ERROR:  The delimiter '" + d2 + u"' is a prefix of the delimiter '" + d1 + u"'.  This would cause the delimiter '" + d1 + u"' to never be matched." + rp.output_newline
                    b = e_encode(msg, rp.output_encoding, "internal") 
                    output_bytes(b, rp)
                    do_graceful_exit(rp, COMMON_PREFIX_ERROR_EXIT_CODE)
        

class RunParameters(object):
    def __init__(self, args):
        self.one_indent = u"  "
        self.input_newline = u"\r\n" if is_probably_on_windows() else u"\n"
        self.output_newline = self.input_newline  #  Default to platform.  Will be everwitten later.
        self.uses_change = False
        self.uses_deletion = False
        self.uses_insertion = False

        self.oldfile = args.oldfile
        self.newfile = args.newfile

        self.terminal_width = None

        #  Global encoding flag:
        if args.e is not None:
            args.parameters_encoding = args.e
            args.oldfile_encoding = args.e
            args.newfile_encoding = args.e
            args.output_encoding = args.e

        #  For minified files
        if args.m is not None:
            args.include_delimiters = True
            if args.m == "json" or args.m == "js" or args.m == "css":
                args.push_delimiters = [u"(", u"{", u"["]
                args.pop_delimiters = [u")", u"}", u"]"]
            if args.m == "html":
                args.push_delimiters = [u"(", u"{", u"[", u"<"]
                args.pop_delimiters = [u")", u"}", u"]", u">"]

        #  View hex mode
        if args.x is not None:
            args.delimiters = []
            args.show_byte_offsets = True
            args.max_line_length = args.x

        #  First, get the encodings so we know how to decode/encode everything else
        self.parameters_encoding = sys.getdefaultencoding() if disable_implicit_encoding is False else default_encoding
        if args.parameters_encoding is not None:
            self.parameters_encoding = args.parameters_encoding  # byte str in Python 2, unicode str in python 3

        self.pretty_output = True
        self.output_encoding = sys.getdefaultencoding() if disable_implicit_encoding is False else default_encoding
        if args.output_encoding is not None:
            self.pretty_output = False
            self.output_encoding = args.output_encoding

        self.oldfile_encoding = "ascii"
        self.oldfile_as_binary = True
        if args.oldfile_encoding is not None:
            self.oldfile_as_binary = False
            self.oldfile_encoding = args.oldfile_encoding

        self.newfile_encoding = "ascii"
        self.newfile_as_binary = True
        if args.newfile_encoding is not None:
            self.newfile_as_binary = False
            self.newfile_encoding = args.newfile_encoding

        self.outfile = None
        self.outfile_f = None
        if args.outfile is not None:
            self.outfile = args.outfile
            try:
                self.outfile_f = open(self.outfile, "wb")
            except Exception as e:
                do_file_open_fail_error(self.outfile, e, self)

        #  The unix terminal interface needs to be initialized after the output encoding is known because it will output ANSI escape sequences.
        self.unix_terminal_interface = make_unix_terminal_interface(self)
        self.windows_terminal_interface = make_windows_terminal_interface(self)


        initialize_error_counts_object(self.oldfile_encoding, self.oldfile_as_binary, self.newfile_encoding, self.newfile_as_binary, self.output_encoding, self.parameters_encoding)
        #  Change the newline if it was specified by the user.
        if args.newline is not None:
            d = args.newline
            param_as_unicode = e_decode(d, self.parameters_encoding, "parameters") if (type(d) == bytes and type(d) == str) else d
            bs = as_byte_string(param_as_unicode, self.parameters_encoding, "parameters")
            ed = as_byte_string(evaluate_escape_sequences(bs, self.parameters_encoding, "parameters"), self.parameters_encoding, "parameters")
            self.output_newline = e_decode(ed, self.parameters_encoding, "parameters")

        self.delimiters = []
        if args.delimiters is not None:
            for d in args.delimiters:
                param_as_unicode = e_decode(d, self.parameters_encoding, "parameters") if (type(d) == bytes and type(d) == str) else d
                bs = as_byte_string(param_as_unicode, self.parameters_encoding, "parameters")
                ed = as_byte_string(evaluate_escape_sequences(bs, self.parameters_encoding, "parameters"), self.parameters_encoding, "parameters")
                self.delimiters.append({"delimiter": ed, "level_adjust": 0})
        else:
            bs = as_byte_string(self.input_newline, self.output_encoding, "internal")
            self.delimiters.append({"delimiter": bs, "level_adjust": 0})

        if args.push_delimiters is not None:
            for d in args.push_delimiters:
                param_as_unicode = e_decode(d, self.parameters_encoding, "parameters") if (type(d) == bytes and type(d) == str) else d
                bs = as_byte_string(param_as_unicode, self.parameters_encoding, "parameters")
                ed = as_byte_string(evaluate_escape_sequences(bs, self.parameters_encoding, "parameters"), self.parameters_encoding, "parameters")
                self.delimiters.append({"delimiter": ed, "level_adjust": 1})

        if args.pop_delimiters is not None:
            for d in args.pop_delimiters:
                param_as_unicode = e_decode(d, self.parameters_encoding, "parameters") if (type(d) == bytes and type(d) == str) else d
                bs = as_byte_string(param_as_unicode, self.parameters_encoding, "parameters")
                ed = as_byte_string(evaluate_escape_sequences(bs, self.parameters_encoding, "parameters"), self.parameters_encoding, "parameters")
                self.delimiters.append({"delimiter": ed, "level_adjust": -1})

        validate_delimiters(self.delimiters, self)

        if args.cols is not None:
            self.terminal_width = args.cols
        else:
            self.terminal_width = get_terminal_width(self, self.unix_terminal_interface, self.windows_terminal_interface)

        if args.lines_context is not None:
            self.lines_context = args.lines_context
        else:
            self.lines_context = 2

        if args.max_line_length is not None:
            self.cut_lines = True
            self.max_line_length = args.max_line_length
            if not (self.max_line_length > 0):
                do_max_line_length_error(self)
        else:
            self.cut_lines = False

        self.infinite_context = False
        if args.infinite_context is not None and args.infinite_context == True:
            self.infinite_context = True

        decoded_oldfile_message = e_decode(args.oldfile_message, self.parameters_encoding, "parameters") if (type(args.oldfile_message) == bytes and type(args.oldfile_message) == str) else args.oldfile_message
        if decoded_oldfile_message is None:
            self.oldfile_message = self.oldfile
        else:
            self.oldfile_message = decoded_oldfile_message

        decoded_newfile_message = e_decode(args.newfile_message, self.parameters_encoding, "parameters") if (type(args.newfile_message) == bytes and type(args.newfile_message) == str) else args.newfile_message
        if decoded_newfile_message is None:
            self.newfile_message = self.newfile
        else:
            self.newfile_message = decoded_newfile_message

        self.enable_line_numbers = True
        if args.disable_line_numbers is not None and args.disable_line_numbers == True:
            self.enable_line_numbers = False

        self.disable_colours = False
        if args.disable_colours is not None and args.disable_colours == True:
            self.disable_colours = True

        self.include_delimiters = False
        if args.include_delimiters is not None and args.include_delimiters == True:
            self.include_delimiters = True

        self.show_byte_offsets = False
        if args.show_byte_offsets is not None and args.show_byte_offsets == True:
            self.show_byte_offsets = True

        self.enable_header = True
        if args.disable_header is not None and args.disable_header == True:
            self.enable_header = False

        self.enable_mark = False
        if args.enable_mark is not None and args.enable_mark == True:
            self.enable_mark = True

        #  Default print method comes from things we detect in terminal.
        self.use_ansi = False
        if self.unix_terminal_interface is not None:
            if self.unix_terminal_interface.num_colours_supported is not None:
                if self.unix_terminal_interface.num_colours_supported > 0:
                    self.use_ansi = True

        self.use_windows_terminal_colours = False
        if self.windows_terminal_interface is not None:
            if self.windows_terminal_interface.csbi_wAttributes_original is not None:
                self.use_windows_terminal_colours = True

        if args.enable_ansi is not None and args.enable_ansi == True:
            self.use_ansi = True

        if args.disable_ansi is not None and args.disable_ansi == True:
            self.use_ansi = False

        if args.enable_windows_terminal_colours is not None and args.enable_windows_terminal_colours == True:
            self.use_windows_terminal_colours = True

        if args.disable_windows_terminal_colours is not None and args.disable_windows_terminal_colours == True:
            self.use_windows_terminal_colours = False

        #  If we chop up the file, then line numbers don't make sense anymore.
        if self.include_delimiters or (args.pop_delimiters is not None and len(args.pop_delimiters)) or (args.pop_delimiters is not None and len(args.pop_delimiters)) or (self.cut_lines):
            self.show_byte_offsets = True


        if self.disable_colours:
            self.use_windows_terminal_colours = False
            self.use_ansi = False

        if args.verbose is not None and args.verbose == True:
            if self.windows_terminal_interface:
                self.windows_terminal_interface.output_test()
                output_bytes(e_encode(self.windows_terminal_interface.as_unicode(), self.output_encoding, "internal"), self)
            else:
                output_bytes(e_encode(u"Windows terminal interface is None" + self.output_newline, self.output_encoding, "internal"), self)

            if self.unix_terminal_interface:
                self.unix_terminal_interface.output_test()
                output_bytes(e_encode(self.unix_terminal_interface.as_unicode(), self.output_encoding, "internal"), self)
            else:
                output_bytes(e_encode(u"Unix terminal interface is None" + self.output_newline, self.output_encoding, "internal"), self)

            #  Dump all of the various params:
            output_bytes(e_encode(u"Here are the final calculated runtime parameters that are about to be used:" + self.output_newline, self.output_encoding, "internal"), self)
            output_bytes(e_encode(u"use_windows_terminal_colours: " + py23_str(self.use_windows_terminal_colours, self.output_encoding, "internal") + self.output_newline, self.output_encoding, "internal"), self)
            output_bytes(e_encode(u"use_ansi: " + py23_str(self.use_ansi, self.output_encoding, "internal") + self.output_newline, self.output_encoding, "internal"), self)
            output_bytes(e_encode(u"output_encoding: " + py23_str(self.output_encoding, self.output_encoding, "internal") + self.output_newline, self.output_encoding, "internal"), self)
            output_bytes(e_encode(u"oldfile_encoding: " + py23_str(self.oldfile_encoding, self.output_encoding, "internal") + self.output_newline, self.output_encoding, "internal"), self)
            output_bytes(e_encode(u"newfile_encoding: " + py23_str(self.newfile_encoding, self.output_encoding, "internal") + self.output_newline, self.output_encoding, "internal"), self)
            output_bytes(e_encode(u"parameters_encoding: " + py23_str(self.parameters_encoding, self.output_encoding, "internal") + self.output_newline, self.output_encoding, "internal"), self)
            output_bytes(e_encode(u"show_byte_offsets: " + py23_str(self.show_byte_offsets, self.output_encoding, "internal") + self.output_newline, self.output_encoding, "internal"), self)
            output_bytes(e_encode(u"enable_mark: " + py23_str(self.enable_mark, self.output_encoding, "internal") + self.output_newline, self.output_encoding, "internal"), self)
            output_bytes(e_encode(u"Total number of delimiters (includes push and pop): " + py23_str(str(len(self.delimiters)), self.output_encoding, "internal") + self.output_newline, self.output_encoding, "internal"), self)
            for d in self.delimiters:
                output_bytes(e_encode(u"    Level Adjust: " + py23_str(d["level_adjust"], self.output_encoding, "internal") + u" ", self.output_encoding, "internal"), self)
                output_bytes(e_encode(u"Delimiter: " + py23_str(bytearray(d["delimiter"]), self.output_encoding, "internal") + self.output_newline, self.output_encoding, "internal"), self)
            #  TODO:  Rest of params.

class DiffState(object):
    def __init__(self, rp, old_sequence, new_sequence, byte_offsets_old, byte_offsets_new, indents_old, indents_new, edit_script):
        self.indents_new = indents_new
        self.indents_old = indents_old
        self.byte_offsets_new = byte_offsets_new
        self.byte_offsets_old = byte_offsets_old
        self.old_sequence = old_sequence
        self.new_sequence = new_sequence
        self.edit_script = edit_script
        self.correct_symbol = u"="
        self.incorrect_symbol = u"x"
        self.separator = u"|"
        self.marking_symbol_area_width = 2 if rp.enable_mark else 0
        self.largest_line_number = max(len(self.new_sequence), len(self.old_sequence))
        highest_byte_offset_old = 0 if len(byte_offsets_old) == 0 else byte_offsets_old[len(byte_offsets_old) -1]
        highest_byte_offset_new = 0 if len(byte_offsets_new) == 0 else byte_offsets_new[len(byte_offsets_new) -1]
        self.largest_byte_offset = max(highest_byte_offset_old, highest_byte_offset_new)

        self.side_width = int((int(rp.terminal_width) - self.marking_symbol_area_width - (3*len(self.separator))) / 2)
        if rp.show_byte_offsets:
            self.line_number_area_width = len(str(self.largest_byte_offset)) + 3 #  Extra 2 for '0x'
        else:
            self.line_number_area_width = len(str(self.largest_line_number)) + 1
        self.line_data_width = self.side_width - self.line_number_area_width

class SideBySideViewLines(object):
    def __init__(self, old_line, new_line, old_line_number, new_line_number, match, insertion, deletion, change):
        self.old_line = old_line
        self.new_line = new_line
        self.old_line_number = old_line_number
        self.new_line_number = new_line_number
        self.match = match
        self.insertion = insertion
        self.deletion = deletion
        self.change = change

class ColouredCharacter(object):
    def __init__(self, character_bytes, colours):
        #  A character is a list of integers that make up the bytes of the character.
        assert(isinstance(character_bytes, list))
        for i in character_bytes:
            assert(isinstance(i, int))
        self.character_bytes = character_bytes
        self.colours = colours

def coloured_text(line, colours, rp, err):
    #  Expects line to be made up of individual characters (not bytes)
    result = []
    grouped = group_unicode_characters(line)
    for c in encode_unicode_characters(grouped, rp.output_encoding, err):
        i_bytes = [py23_ord(b) for b in c]
        result.append(ColouredCharacter(i_bytes, colours))

    return result


def apply_character_colours(character_bytes, bg_colours, rp, err):
    #  Iterate over all characters, and return a list of coloured characters
    result = []
    if rp.pretty_output:
        for b in list(character_bytes):
            result.append(ColouredCharacter([py23_ord(b)], bg_colours))
    else:
        decoded = e_decode(character_bytes, rp.output_encoding, err)
        grouped = group_unicode_characters(decoded)
        for c in encode_unicode_characters(grouped, rp.output_encoding, err):
            result.append(ColouredCharacter([py23_ord(b) for b in c], bg_colours))

    return result

def get_recursive_diff_list(chrs, rp, err):
    #  Each line is a byte array that contains one character
    if rp.pretty_output:
        return [int_array_as_byte_string([py23_ord(c)]) for c in chrs]
    else:
        decoded = e_decode(chrs, rp.output_encoding, err)
        grouped = group_unicode_characters(decoded)
        return encode_unicode_characters(grouped, rp.output_encoding, err)

class DiffViewIterator(object):
    def __init__(self, diff_state, rp, is_recursive):
        self.rp = rp
        self.is_recursive = is_recursive
        self.diff_state = diff_state
        self.current_edit_script_index = 0
        self.current_view_line = 0
        self.current_old_file_line = 0
        self.current_new_file_line = 0
        self.current_header_line = 0

    def dot_lines(self, old_start, new_start, old_end, new_end):
        enc = self.rp.output_encoding
        things = u"Lines"
        o1 = e_decode(as_byte_string(str(old_start + 1), enc, "internal"), enc, "internal")
        o2 = e_decode(as_byte_string(str(old_end + 1), enc, "internal"), enc, "internal")
        n1 = e_decode(as_byte_string(str(new_start + 1), enc, "internal"), enc, "internal")
        n2 = e_decode(as_byte_string(str(new_end + 1), enc, "internal"), enc, "internal")
        if self.rp.show_byte_offsets:
            things = u"Bytes"
            o1 = u'0x' + e_decode(as_byte_string(str(format(self.diff_state.byte_offsets_old[old_start], 'X')), enc, "internal"), enc, "internal")
            o2 = u'0x' + e_decode(as_byte_string(str(format(self.diff_state.byte_offsets_old[old_end + 1], 'X')), enc, "internal"), enc, "internal")
            n1 = u'0x' + e_decode(as_byte_string(str(format(self.diff_state.byte_offsets_new[new_start], 'X')), enc, "internal"), enc, "internal")
            n2 = u'0x' + e_decode(as_byte_string(str(format(self.diff_state.byte_offsets_new[new_end + 1], 'X')), enc, "internal"), enc, "internal")
        
        old_skip_message = u"--- " + things + u" " + o1 + u"-" + o2 + u" match---"
        new_skip_message = u"--- " + things + u" " + n1 + u"-" + n2 + u" match---"
        rtn = SideBySideViewLines(
            coloured_text(old_skip_message, [], self.rp, "internal"),
            coloured_text(new_skip_message, [], self.rp, "internal"),
            None,
            None,
            True,
            False,
            False,
            False
        )
        return rtn

    def no_change_lines(self):
        indent_old = []
        indent_new = []
        if not self.is_recursive:
            indent_old = coloured_text(self.rp.one_indent * self.diff_state.indents_old[self.current_old_file_line], [], self.rp, "internal")
            indent_new = coloured_text(self.rp.one_indent * self.diff_state.indents_new[self.current_new_file_line], [], self.rp, "internal")
        rtn = SideBySideViewLines(
            indent_old + apply_character_colours(self.diff_state.old_sequence[self.current_old_file_line], [], self.rp, "oldfile"),
            indent_new + apply_character_colours(self.diff_state.new_sequence[self.current_new_file_line], [], self.rp, "newfile"),
            self.current_old_file_line,
            self.current_new_file_line,
            True,
            False,
            False,
            False
        )
        self.current_old_file_line = self.current_old_file_line + 1
        self.current_new_file_line = self.current_new_file_line + 1
        return rtn

    def insertion_lines(self):
        indent_new = []
        if not self.is_recursive:
            indent_new = coloured_text(self.rp.one_indent * self.diff_state.indents_new[self.current_new_file_line], [], self.rp, "internal")

        rtn = SideBySideViewLines(
            None,
            indent_new + apply_character_colours(self.diff_state.new_sequence[self.current_new_file_line], [INSERTION_COLOUR], self.rp, "newfile"),
            None,
            self.current_new_file_line,
            False,
            True,
            False,
            False
        )
        self.current_new_file_line = self.current_new_file_line + 1
        self.current_edit_script_index = self.current_edit_script_index + 1
        return rtn

    def deletion_lines(self):
        indent_old = []
        if not self.is_recursive:
            indent_old = coloured_text(self.rp.one_indent * self.diff_state.indents_old[self.current_old_file_line], [], self.rp, "internal")

        rtn = SideBySideViewLines(
            indent_old + apply_character_colours(self.diff_state.old_sequence[self.current_old_file_line], [DELETION_COLOUR], self.rp, "oldfile"),
            None,
            self.current_old_file_line,
            None,
            False,
            False,
            True,
            False
        )
        self.current_old_file_line = self.current_old_file_line + 1
        self.current_edit_script_index = self.current_edit_script_index + 1
        return rtn

    def change_lines(self):
        if self.is_recursive:
            rtn = SideBySideViewLines(
                apply_character_colours(self.diff_state.old_sequence[self.current_old_file_line], [CHANGE_COLOUR], self.rp, "oldfile"),
                apply_character_colours(self.diff_state.new_sequence[self.current_new_file_line], [CHANGE_COLOUR], self.rp, "newfile"),
                self.current_old_file_line,
                self.current_new_file_line,
                False,
                False,
                False,
                True
            )
        else:
            #  Recursively diff the two lines to get a better view
            old_sequence = get_recursive_diff_list(self.diff_state.old_sequence[self.current_old_file_line], self.rp, "oldfile")
            new_sequence = get_recursive_diff_list(self.diff_state.new_sequence[self.current_new_file_line], self.rp, "newfile")
            edit_script = simplify_edit_script(diff(old_sequence, new_sequence))
            diff_state = DiffState(self.rp, old_sequence, new_sequence, [], [], [], [], edit_script)
            
            diff_view_iterator = DiffViewIterator(diff_state, self.rp, True)
            
            old_line_result = coloured_text(self.rp.one_indent * self.diff_state.indents_old[self.current_old_file_line], [], self.rp, "internal")
            new_line_result = coloured_text(self.rp.one_indent * self.diff_state.indents_new[self.current_new_file_line], [], self.rp, "internal")
            #  Re-construct the two lines with their new highlighted colours
            while True:
                side_by_side = diff_view_iterator.get_next_side_by_side_lines(self.rp, diff_state)
                if side_by_side is None:
                    break

                if not side_by_side.old_line is None:
                    old_line_result += side_by_side.old_line
                if not side_by_side.new_line is None:
                    new_line_result += side_by_side.new_line
            
            rtn = SideBySideViewLines(
                old_line_result,
                new_line_result,
                self.current_old_file_line,
                self.current_new_file_line,
                False,
                False,
                False,
                True
            )
        self.current_old_file_line = self.current_old_file_line + 1
        self.current_new_file_line = self.current_new_file_line + 1
        self.current_edit_script_index = self.current_edit_script_index + 1
        return rtn

    def get_next_side_by_side_lines(self, rp, diff_state):
        if not self.is_recursive and rp.enable_header and self.current_header_line == 0:
            str_new = e_decode(as_byte_string(rp.newfile_message, rp.parameters_encoding, "parameters"), rp.parameters_encoding, "parameters")
            str_old = e_decode(as_byte_string(rp.oldfile_message, rp.parameters_encoding, "parameters"), rp.parameters_encoding, "parameters")
            spaces_padding_new = int(diff_state.line_data_width / 2) - int(len(str_new) / 2)
            spaces_padding_old = int(diff_state.line_data_width / 2) - int(len(str_old) / 2)
            for i in range(0, spaces_padding_new):
                str_new = u" " + str_new
            for i in range(0, spaces_padding_old):
                str_old = u" " + str_old
            self.current_header_line += 1
            return SideBySideViewLines(
                coloured_text(str_old, [], self.rp, "internal"),
                coloured_text(str_new, [], self.rp, "internal"),
                None,
                None,
                None,
                False,
                False,
                False
            )
        elif not self.is_recursive and rp.enable_header and self.current_header_line == 1:
            self.current_header_line += 1
            return SideBySideViewLines(
                coloured_text(u"", [], self.rp, "internal"),
                coloured_text(u"", [], self.rp, "internal"),
                None,
                None,
                None,
                False,
                False,
                False
            )
        else:
            num_edits = len(diff_state.edit_script)
            #  If we're finished with all the edits, and both files
            if (
                self.current_edit_script_index == num_edits and
                self.current_old_file_line >= len(self.diff_state.old_sequence) and
                self.current_new_file_line >= len(self.diff_state.new_sequence)
            ):
                return None

            #  If we're currently after all the edits
            if self.current_edit_script_index == num_edits:
                if self.rp.infinite_context or self.is_recursive or (num_edits > 0 and self.current_old_file_line <= (diff_state.edit_script[num_edits-1]["position_old"] + self.rp.lines_context)):
                    return self.no_change_lines()
                else:
                    #  Finish early.
                    old_b = self.current_old_file_line
                    new_b = self.current_new_file_line
                    self.current_old_file_line = len(self.diff_state.old_sequence)
                    self.current_new_file_line = len(self.diff_state.new_sequence)
                    return self.dot_lines(old_b, new_b, self.current_old_file_line - 1, self.current_new_file_line -1)

            current_edit = diff_state.edit_script[self.current_edit_script_index]

            #  If we're before the next edit starts
            if self.current_old_file_line < current_edit["position_old"]:
                last_i = self.current_edit_script_index - 1
                if (
                    self.rp.infinite_context or
                    self.is_recursive or
                    #  If we're just before the next edit
                    (self.current_old_file_line + self.rp.lines_context >= current_edit["position_old"]) or
                    #  If we're just after the last edit
                    (
                        last_i >= 0 and
                        self.current_old_file_line <= diff_state.edit_script[last_i]["position_old"] + self.rp.lines_context 
                    )
                ):
                    return self.no_change_lines()
                else:
                    #  Just skip to just before the next edit
                    skip_num = current_edit["position_old"] - self.current_old_file_line - self.rp.lines_context
                    old_b = self.current_old_file_line
                    new_b = self.current_new_file_line
                    self.current_old_file_line += skip_num
                    self.current_new_file_line += skip_num
                    return self.dot_lines(old_b, new_b, self.current_old_file_line - 1, self.current_new_file_line - 1)

            #  If we're currently processing one of the edits
            if current_edit["position_old"] == self.current_old_file_line:
                if current_edit["operation"] == "delete":
                    return self.deletion_lines()
                elif current_edit["operation"] == "insert":
                    return self.insertion_lines()
                elif current_edit["operation"] == "change":
                    return self.change_lines()

            raise #  Should never get here.


def render_line_number(side_by_side, num, current_offset_into_line, rp, diff_state, byte_offsets):
    text = None
    if num is None:
        text = u"" #  Header
    else:
        if current_offset_into_line > 0:
            text = u"."
        else:
            enc = rp.output_encoding
            if rp.show_byte_offsets:
                text = u"0x" + e_decode(as_byte_string(str(format(byte_offsets[num], 'X')), "ascii", "internal"), "ascii","internal")

            else:
                text = e_decode(as_byte_string(str(num + 1), "ascii", "internal"), "ascii", "internal")

    if not rp.enable_line_numbers:
        text = u""

    textlen = len(text)
    for i in range(1, (diff_state.line_number_area_width - textlen) + 1):
        text = text + u" "

    rtn = []
    for c in text:
        rtn += coloured_text(
            c, 
            [] if (c == u" " or c == u".") else get_bg_colours(
                side_by_side.insertion, side_by_side.deletion, side_by_side.change
            ),
            rp,
            "internal"
        )
    return rtn

def calculate_character_width(c, rp):
    b, print_length = make_character_presentable(c.character_bytes, rp)
    return print_length

def count_chars_that_fit(text, current_offset_into_line, rp, diff_state):
    #  Since characters can have a variable width, we need to check how many will fit on one line
    total_character_width = 0
    #  Current index of the character in the line
    current_pos = current_offset_into_line
    while (text is not None) and (current_pos < len(text)):
        c = text[current_pos]
        assert(isinstance(c, ColouredCharacter))
        char_width = calculate_character_width(c, rp)
        if (total_character_width + char_width) < diff_state.line_data_width:
            total_character_width += char_width
            current_pos += 1
        else:
            #  Return the number of characters that could fit into one line, and flag if there might be more chrs
            return current_pos - current_offset_into_line, True
    #  Return num of chrs, and that there are no more characters.
    return current_pos - current_offset_into_line, False

def determine_max_chrs_to_show(old_line, new_line, offset_into_old_line, offset_into_new_line, rp, diff_state):
    num_chars_that_fit_old, old_has_more = count_chars_that_fit(old_line, offset_into_old_line, rp, diff_state)
    num_chars_that_fit_new, new_has_more = count_chars_that_fit(new_line, offset_into_new_line, rp, diff_state)
    if old_has_more and new_has_more:
        #  Pick the min, because other one would overflow its side
        return min(num_chars_that_fit_old, num_chars_that_fit_new), False
    elif old_has_more:  #  No more than what fits in old
        return num_chars_that_fit_old, False
    elif new_has_more:  #  No more than what fits in new
        return num_chars_that_fit_new, False
    else:
        #  Both fit, take the max
        return max(num_chars_that_fit_old, num_chars_that_fit_new), not (old_has_more or new_has_more)


def get_replacement_char(c):
    if len(c) > 1:  #  For surrogate pairs.  Currently don't have any we need to replace.
        return None
    o = py23_ord(c)
    if o < 9:
        return u" "
    elif o == 9:
        return u"    "
    elif o < 32:
        return u" "
    elif c == u"\u0085": # Next Line,
        return u" "
    elif c == u"\u2028": # Line separator
        return u" "
    elif c == u"\u2029": # Paragraph separator
        return u" "
    return None

def make_character_presentable(c, rp):
    if len(c) == 0:
        return c, 0  #  The result of an ignored failed decode from an invalid character.

    #  A character at this point should be a list of integers.
    for b in c:
        assert(type(b) == int)
    if rp.pretty_output:
        if len(c) == 1 and ((c[0] > 31 and c[0] < 127) or c[0] == ord('\t')):
            #  Standard ascii character
            if c[0] == ord('\t'):
                return [ord(u" "),ord(u" "),ord(u" "),ord(u" ")], 4
            else:
                return [c[0]], 1
        else:
            #  Extended ASCII characer or multi-byte character.
            rtn = []
            for byte in c:
                rtn += [py23_ord(b) for b in (b"\\x" + as_byte_string(format(byte, '02X'), rp.output_encoding, "internal"))]
            return rtn, len(rtn)
    else:
        #  This is not precise at all, but it is the best that can be done
        char_as_unicode = e_decode(int_array_as_byte_string(c), rp.output_encoding, "internal")
        if len(char_as_unicode) == 0:
            return [], 0  #  Happens sometimes due to decode failure on invalid characters. 
        east_asian_width = get_east_asian_width(char_as_unicode)
        replacement_chars = get_replacement_char(char_as_unicode)
        if replacement_chars is None:
            return c, east_asian_width
        else:
            ls = [get_east_asian_width(c) for c in replacement_chars]
            return [py23_ord(b) for b in as_byte_string(replacement_chars, rp.output_encoding, "internal")], sum(ls)

def get_east_asian_width(unicode_str):
    r = unicodedata.east_asian_width(unicode_str)
    if r == "F":    #  Fullwidth
        return 1
    elif r == "H":  #  Half-width
        return 1
    elif r == "W":  #  Wide
        return 2
    elif r == "Na": #  Narrow
        return 1
    elif r == "A":  #  Ambiguous, go with 2
        return 1
    elif r == "N":  #  Neutral
        return 1
    else:
        return 1

def make_characters_presentable(chrs, rp):
    total_print_length = 0
    for i in range(0, len(chrs)):
        chrs[i].character_bytes, char_print_len = make_character_presentable(chrs[i].character_bytes, rp)
        total_print_length += char_print_len
        for b in chrs[i].character_bytes:
            assert(type(b) == int)
    return chrs, total_print_length


def print_coloured_character(c, rp):
    character_bytes = bytearray(c.character_bytes)

    win = rp.windows_terminal_interface
    unix = rp.unix_terminal_interface

    sys.stdout.flush()
    if rp.use_windows_terminal_colours:
        try:
            win.set_terminal_colours(c.colours)
        except:
            pass

    if rp.use_ansi:
        unix.set_terminal_colours(c.colours)

    output_bytes(character_bytes, rp)
    sys.stdout.flush() #  Required on Windows for terminal colours to appear.

    if rp.use_ansi:
        unix.reset_terminal_colours()

    if rp.use_windows_terminal_colours:
        try:
            win.reset_terminal_colours()
        except:
            pass


def print_coloured_characters(chrs, rp):
    for c in chrs:
        print_coloured_character(c, rp)

def render_line_text(text, current_offset_into_line, max_chars_to_show, rp, diff_state):
    line = coloured_text(u"--", [], rp, "internal")
    if text is not None:
        line = text
    if current_offset_into_line > len(line):  #  Is there nothing more to process?
        return coloured_text(u" " * diff_state.line_data_width, [], rp, "internal")

    #  The rest of the line remaining (if it is a line that must be chopped up)
    chars_to_show = line[current_offset_into_line:(current_offset_into_line + max_chars_to_show)]
    #  This is the number of characters that are presented in the view (for example after hex encoding non-printables)
    characters_view, characters_view_length = make_characters_presentable(chars_to_show, rp)
    #  Add spaces onto the end for alignment:
    if characters_view_length < diff_state.line_data_width:
        num_padding_spaces = diff_state.line_data_width - characters_view_length
        characters_view = characters_view + coloured_text(u" " * num_padding_spaces, [], rp, "internal")

    return characters_view

def get_bg_colours(insertion, deletion, change):
    if insertion:
        return [INSERTION_COLOUR]
    if deletion:
        return [DELETION_COLOUR]
    if change:
       return [CHANGE_COLOUR]
    return []


def do_max_line_length_error(rp):
    msg = u"The specified max line length is " + e_decode(as_byte_string(str(rp.max_line_length), rp.output_encoding, "internal"), rp.output_encoding, "internal") + u" but it must be greater than 0! Exiting..." + rp.output_newline
    output_bytes(e_encode(msg, rp.output_encoding, "internal"), rp)
    do_graceful_exit(rp, INVALID_MAX_LINE_LENGTH_ERROR_EXIT_CODE)

def do_terminal_width_error(rp):
    msg = u"The terminal width is " + e_decode(as_byte_string(str(rp.terminal_width), rp.output_encoding, "internal"), rp.output_encoding, "internal") + u" and that is not enough space to print characters in the current line! Exiting..." + rp.output_newline
    output_bytes(e_encode(msg, rp.output_encoding, "internal"), rp)
    do_graceful_exit(rp, TERMINAL_WIDTH_ERROR_EXIT_CODE)

def output_bytes(s, rp):
    #  Expects already encoded bytes to be passed
    if rp.outfile_f is not None:
        #  Write to file instead of standard out.
        rp.outfile_f.write(s)
    else:
        os.write(sys.stdout.fileno(), s)

def do_error_count_warnings(rp):
    global err_counts
    for k in err_counts:
        if err_counts[k]["count"] > 0:
            count = e_decode(as_byte_string(str(str(err_counts[k]["count"])), rp.output_encoding, "internal"), rp.output_encoding, "internal")
            src = e_decode(as_byte_string(err_counts[k]["src"], rp.output_encoding, "internal"), rp.output_encoding, "internal")
            dst = e_decode(as_byte_string(err_counts[k]["dst"], rp.output_encoding, "internal"), rp.output_encoding, "internal")
            msg = u"WARNING: " + count + u" encoding errors ignored while processing " + src + u" to " + dst + rp.output_newline
            output_bytes(e_encode(msg, rp.output_encoding, "internal"), rp)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("oldfile", help="File name of old version.", type=str)
    parser.add_argument("newfile", help="File name of new version.", type=str)
    parser.add_argument("-c", "--cols", help="Expects an integer.  Used to explicitly define the terminal width for formatting output.  If the terminal width can be detected automatically, this value will default to the current terminal width.  If the terminal width cannot be detect, this value will default to 80.", type=int)
    parser.add_argument("-i", "--infinite-context", help="Showing infinite context before and after edits.  This is often useful if you want to quickly see a hex dump of a file by diffing it with itself, and then using -i to see the entire context since there are no differences.", action='store_true')
    parser.add_argument("-t", "--lines-context", help="Number of lines of context to display before and after.", type=int)
    parser.add_argument("-w", "--max-line-length", help="Chop up lines as if they were multiple lines when they exceed N characters.  Note that you will probably want to set --delimiters to be an empty array if you use this option, otherwise lines will also be split up using the default delimiter too.", type=int)
    parser.add_argument("--oldfile-message", help="Message to display over old file.", type=str)
    parser.add_argument("--newfile-message", help="Message to display over new file.", type=str)
    parser.add_argument("--disable-header", help="Disable header that labels the two files using oldfile message and newfile message.", action='store_true')
    parser.add_argument("--enable-ansi", help="Explicitly attempt to disable ANSI color control sequences.", action='store_true')
    parser.add_argument("--disable-ansi", help="Explicitly attempt to enable ANSI color control sequences.", action='store_true')
    parser.add_argument("--enable-windows-terminal-colours", help="Explicitly attempt to enable Windows colour setting calls.", action='store_true')
    parser.add_argument("--disable-windows-terminal-colours", help="Explicitly attempt to disable Windows colour setting calls.", action='store_true')
    parser.add_argument("--enable-mark", help="Enable a marking symbols on the left-hand side that displays a check mark mark or x.", action='store_true')
    parser.add_argument("--disable-line-numbers", help="Disable line numbers.", action='store_true')
    parser.add_argument("--disable-colours", help="Disable any form of colour output.", action='store_true')
    parser.add_argument("-k", "--include-delimiters", help="Include delimiters in the diff", action='store_true')
    parser.add_argument("--show-byte-offsets", help="Show byte offsets instead of line numbers.", action='store_true')
    parser.add_argument("-d", '--delimiters', type=str, nargs='*', help='An optional list of delimiters to use in deciding when to split lines.  By default if Windows is detected --delimiters will be "\\r\\n".  If Linux is detected --delimiters will be "\\n".  If the platform detection isn\'t working properly, or if you want to diff a file from another platform, you can explicitly specify the line delimiters.  If you specify --delimiters with nothing after it, this means that lines will never be split based on any character.')
    parser.add_argument("-p", '--push-delimiters', type=str, nargs='*', help='Special delimiters used to indicate the start of a new line that should be intended.')
    parser.add_argument("-q", '--pop-delimiters', type=str, nargs='*', help='Special delimiters used to indicate the end of a line should have been intended.')
    parser.add_argument("-r", "--parameters-encoding", help="The encoding to use when processing command-line parameters.", type=str)
    parser.add_argument("-o", "--output-encoding", help="The encoding of the output.", type=str)
    parser.add_argument("-a", "--oldfile-encoding", help="The encoding of oldfile.", type=str)
    parser.add_argument("-b", "--newfile-encoding", help="The encoding of newfile.", type=str)
    parser.add_argument("-f", "--outfile", help="Output to the specified file instead of stdout", type=str)
    parser.add_argument("--newline", help='Optionally choose what character(s) to use when printing a new line of output.  This is useful in some context where printing either "\\n" or "\\r\\n" will result in extra blank lines.  In some context, you may need to use --newline "" to avoid extra blank lines in the output.', type=str)
    parser.add_argument("-v", "--verbose", help="Be verbose.", action='store_true')
    parser.add_argument("-e", help="Set the encoding of oldfile, newfile, output, and parameters at the same time", type=str)
    parser.add_argument("-m", help="Equivalent to explicitly adding flags of the form: --push-delimiters PUSH_DELIMS --pop-delimiters POP_DELIMS --include-delimiters.  For -m json, -m css, or -m js,  PUSH_DELIMS, POP_DELIMS = \"(\" \"{\" \"[\", \")\" \"}\" \"]\".  For -m html: \"(\" \"{\" \"[\" \"<\", \")\" \"}\" \"]\" \">\".", type=str)
    parser.add_argument("-x", help="Display all bytes of the file in a pseudo-hex editor like format.  Requires an integer argument to know how many bytes to display on each line.  All output will be in standard ASCII.  Equivalent to setting adding the following flags: --delimiters --show-byte-offsets --max-line.  If you also explicitly set the output encoding will turn off hex encoding of characters.", type=int)
    parser.add_argument("--version", action='version', version="This is the very first version, so the version number is kind of arbitrary...  Let's call it version 0.01.")

    rp = RunParameters(parser.parse_args())
    global GLOBAL_RUN_PARAMS
    GLOBAL_RUN_PARAMS = rp

    old_sequence, byte_offsets_old, indents_old = read_file_as_list(rp.oldfile, rp, rp.oldfile_encoding, "oldfile", rp.oldfile_as_binary)
    new_sequence, byte_offsets_new, indents_new = read_file_as_list(rp.newfile, rp, rp.newfile_encoding, "newfile", rp.oldfile_as_binary)

    edit_script = simplify_edit_script(diff(old_sequence, new_sequence))
    diff_state = DiffState(rp, old_sequence, new_sequence, byte_offsets_old, byte_offsets_new, indents_old, indents_new, edit_script)
    
    if diff_state.line_data_width < 1:
        do_terminal_width_error(rp)
    
    diff_view_iterator = DiffViewIterator(diff_state, rp, False)

    rendered_separator = coloured_text(diff_state.separator, [], rp, "internal")
    rendered_incorrect_symbol = coloured_text(diff_state.incorrect_symbol, [INCORRECT_COLOUR], rp, "internal")
    rendered_correct_symbol = coloured_text(diff_state.correct_symbol, [CORRECT_COLOUR], rp, "internal")
    rendered_newline = coloured_text(rp.output_newline, [], rp, "internal")
    
    #  Print out all of the lines in the two files
    while True:
        side_by_side = diff_view_iterator.get_next_side_by_side_lines(rp, diff_state)
        if side_by_side is None:
            break
    
        if side_by_side.insertion:
            rp.uses_insertion = True
        if side_by_side.deletion:
            rp.uses_deletion = True
    
        offset_into_old_line = 0
        offset_into_new_line = 0
    
        #  Wrap the current pair of lines from the file as many times as necessary to show it in the terminal.
        while True:
            max_chars_to_show, finished_line = determine_max_chrs_to_show(side_by_side.old_line, side_by_side.new_line, offset_into_old_line, offset_into_new_line, rp, diff_state)

            rendered_line_old = render_line_text(side_by_side.old_line, offset_into_old_line, max_chars_to_show, rp, diff_state)
            rendered_line_new = render_line_text(side_by_side.new_line, offset_into_new_line, max_chars_to_show, rp, diff_state)
    
            rendered_number_old = render_line_number(side_by_side, side_by_side.old_line_number, offset_into_old_line, rp, diff_state, byte_offsets_old)
            rendered_number_new = render_line_number(side_by_side, side_by_side.new_line_number, offset_into_new_line, rp, diff_state, byte_offsets_new)
            offset_into_old_line += max_chars_to_show
            offset_into_new_line += max_chars_to_show
    
            if rp.enable_mark:
                if side_by_side.match:
                    print_coloured_characters(rendered_incorrect_symbol, rp)
                else:
                    print_coloured_characters(rendered_correct_symbol, rp)

            print_coloured_characters(rendered_separator, rp)
    
            print_coloured_characters(rendered_number_new, rp)
    
            print_coloured_characters(rendered_line_new, rp)
    
            print_coloured_characters(rendered_separator, rp)
            print_coloured_characters(rendered_number_old, rp)
    
            print_coloured_characters(rendered_line_old, rp)
    
            print_coloured_characters(rendered_separator, rp)
    
            print_coloured_characters(rendered_newline, rp)

            #  If both the new and old have completely consumed the available characters, move onto the next line
            if finished_line:
                break
            else:
                #  The terminal is too small to display even one character for this line.
                if max_chars_to_show == 0:
                    do_terminal_width_error(rp)

    do_error_count_warnings(rp)
    
if __name__ == "__main__":
    try:
        main()
        do_graceful_exit(GLOBAL_RUN_PARAMS, 0)
    except Exception as e:
        traceback.print_exc()
        do_graceful_exit(GLOBAL_RUN_PARAMS, 1)
