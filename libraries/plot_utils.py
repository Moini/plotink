# coding=utf-8
# plot_utils.py
# Common geometric plotting utilities for EiBotBoard
# https://github.com/evil-mad/plotink
# 
# Intended to provide some common interfaces that can be used by 
# EggBot, WaterColorBot, AxiDraw, and similar machines.
#
# See below for version information
#
#
# The MIT License (MIT)
# 
# Copyright (c) 2018 Windell H. Oskay, Evil Mad Scientist Laboratories
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from math import sqrt

import cspsubdiv
import simplepath
from bezmisc import beziersplitatt

def version():    # Version number for this document
    return "0.10" # v 0.10.1 Dated 2018-05-03

PX_PER_INCH = 96.0  # 96 px per inch, for use with Inkscape 0.92 or newer
# This value has migrated from 90 px per inch, as of Inkscape 0.91 or older


# Note that the SVG specification is for 96 px per inch;
# Expect a change to 96 as of Inkscape 0.92.

def checkLimits(value, lower_bound, upper_bound):
    # Limit a value to within a range.
    # Return constrained value with error boolean.
    if value > upper_bound:
        return upper_bound, True
    if value < lower_bound:
        return lower_bound, True
    return value, False


def checkLimitsTol(value, lower_bound, upper_bound, tolerance):
    # Limit a value to within a range.
    # Return constrained value with error boolean.
    # Allow a range of tolerance where we constrain the value without an error message.

    if value > upper_bound:
        if value > (upper_bound + tolerance):
            return upper_bound, True  # Truncate & throw error
        else:
            return upper_bound, False  # Truncate with no error
    if value < lower_bound:
        if value < (lower_bound - tolerance):
            return lower_bound, True  # Truncate & throw error
        else:
            return lower_bound, False  # Truncate with no error
    return value, False  # Return original value without error


def constrainLimits(value, lower_bound, upper_bound):
    # Limit a value to within a range.
    return max(lower_bound, min(upper_bound, value))


def distance(x, y):
    '''
    Pythagorean theorem!
    '''
    return sqrt(x * x + y * y)


def dotProductXY(input_vector_first, input_vector_second):
    temp = input_vector_first[0] * input_vector_second[0] + input_vector_first[1] * input_vector_second[1]
    if temp > 1:
        return 1
    elif temp < -1:
        return -1
    else:
        return temp


def getLength(altself, name, default):
    '''
    Get the <svg> attribute with name "name" and default value "default"
    Parse the attribute into a value and associated units.  Then, accept
    no units (''), units of pixels ('px'), and units of percentage ('%').
    Return value in px.
    '''
    string_to_parse = altself.document.getroot().get(name)

    if string_to_parse:
        v, u = parseLengthWithUnits(string_to_parse)
        if not v:
            # Couldn't parse the value
            return None
        elif u == '' or u == 'px':
            return v
        elif u == 'in':
            return float(v) * PX_PER_INCH
        elif u == 'mm':
            return float(v) * PX_PER_INCH / 25.4
        elif u == 'cm':
            return float(v) * PX_PER_INCH / 2.54
        elif u == 'Q' or u == 'q':
            return float(v) * PX_PER_INCH / (40.0 * 2.54)
        elif u == 'pc':
            return float(v) * PX_PER_INCH / 6.0
        elif u == 'pt':
            return float(v) * PX_PER_INCH / 72.0
        elif u == '%':
            return float(default) * v / 100.0
        else:
            # Unsupported units
            return None
    else:
        # No width specified; assume the default value
        return float(default)


def getLengthInches(altself, name):
    '''
    Get the <svg> attribute with name "name", and parse it as a length,
    into a value and associated units. Return value in inches.
    
    As of version 0.11, units of 'px' or no units ('') are interpreted
    as imported px, at a resolution of 96 px per inch, as per the SVG
    specification. (Prior versions returned None in this case.)
    
    This allows certain imported SVG files, (imported with units of px)
    to plot while they would not previously. However, it may also cause
    new scaling issues in some circumstances. Note, for example, that
    Adobe Illustrator uses 72 px per inch, and Inkscape used 90 px per
    inch prior to version 0.92.
    '''
    string_to_parse = altself.document.getroot().get(name)
    if string_to_parse:
        v, u = parseLengthWithUnits(string_to_parse)
        if not v:
            # Couldn't parse the value
            return None
        elif u == 'in':
            return v
        elif u == 'mm':
            return float(v) / 25.4
        elif u == 'cm':
            return float(v) / 2.54
        elif u == 'Q' or u == 'q':
            return float(v) / (40.0 * 2.54)
        elif u == 'pc':
            return float(v) / 6.0
        elif u == 'pt':
            return float(v) / 72.0
        elif u == '' or u == 'px':
            return float(v) / 96.0
        else:
            # Unsupported units, including '%'
            return None


def parseLengthWithUnits(string_to_parse):
    '''
    Parse an SVG value which may or may not have units attached.
    There is a more general routine to consider in scour.py if more
    generality is ever needed.
    '''
    u = 'px'
    s = string_to_parse.strip()
    if s[-2:] == 'px':  # pixels, at a size of PX_PER_INCH per inch
        s = s[:-2]
    elif s[-2:] == 'in':  # inches
        s = s[:-2]
        u = 'in'
    elif s[-2:] == 'mm':  # millimeters
        s = s[:-2]
        u = 'mm'
    elif s[-2:] == 'cm':  # centimeters
        s = s[:-2]
        u = 'cm'
    elif s[-2:] == 'pt':  # points; 1pt = 1/72th of 1in
        s = s[:-2]
        u = 'pt'
    elif s[-2:] == 'pc':  # picas; 1pc = 1/6th of 1in
        s = s[:-2]
        u = 'pc'
    elif s[-1:] == 'Q' or s[-1:] == 'q':  # quarter-millimeters. 1q = 1/40th of 1cm
        s = s[:-1]
        u = 'Q'
    elif s[-1:] == '%':
        u = '%'
        s = s[:-1]

    try:
        v = float(s)
    except:
        return None, None

    return v, u


def unitsToUserUnits(input_string):
    '''
    Custom replacement for the unittouu routine in inkex.py

    Parse the attribute into a value and associated units.
    Return value in user units (typically "px").
    '''

    v, u = parseLengthWithUnits(input_string)
    if not v:
        # Couldn't parse the value
        return None
    elif u == '' or u == 'px':
        return v
    elif u == 'in':
        return float(v) * PX_PER_INCH
    elif u == 'mm':
        return float(v) * PX_PER_INCH / 25.4
    elif u == 'cm':
        return float(v) * PX_PER_INCH / 2.54
    elif u == 'Q' or u == 'q':
        return float(v) * PX_PER_INCH / (40.0 * 2.54)
    elif u == 'pc':
        return float(v) * PX_PER_INCH / 6.0
    elif u == 'pt':
        return float(v) * PX_PER_INCH / 72.0
    elif u == '%':
        return float(v) / 100.0
    else:
        # Unsupported units
        return None


def subdivideCubicPath(sp, flat, i=1):
    '''
    Break up a bezier curve into smaller curves, each of which
    is approximately a straight line within a given tolerance
    (the "smoothness" defined by [flat]).

    This is a modified version of cspsubdiv.cspsubdiv(). I rewrote the recursive
    call because it caused recursion-depth errors on complicated line segments.
    '''

    while True:
        while True:
            if i >= len(sp):
                return
            p0 = sp[i - 1][1]
            p1 = sp[i - 1][2]
            p2 = sp[i][0]
            p3 = sp[i][1]

            b = (p0, p1, p2, p3)

            if cspsubdiv.maxdist(b) > flat:
                break
            i += 1

        one, two = beziersplitatt(b, 0.5)
        sp[i - 1][2] = one[1]
        sp[i][0] = two[2]
        p = [one[2], one[3], two[1]]
        sp[i:1] = [p]


def userUnitToUnits(distance_uu, unit_string):
    '''
    Custom replacement for the uutounit routine in inkex.py

    Parse the attribute into a value and associated units.
    Return value in user units (typically "px").
    '''

    if not distance_uu:  # Couldn't parse the value
        return None
    elif unit_string == '' or unit_string == 'px':
        return distance_uu
    elif unit_string == 'in':
        return float(distance_uu) / PX_PER_INCH
    elif unit_string == 'mm':
        return float(distance_uu) / (PX_PER_INCH / 25.4)
    elif unit_string == 'cm':
        return float(distance_uu) / (PX_PER_INCH / 2.54)
    elif unit_string == 'Q' or unit_string == 'q':
        return float(distance_uu) / (PX_PER_INCH / (40.0 * 2.54))
    elif unit_string == 'pc':
        return float(distance_uu) / (PX_PER_INCH / 6.0)
    elif unit_string == 'pt':
        return float(distance_uu) / (PX_PER_INCH / 72.0)
    elif unit_string == '%':
        return float(distance_uu) * 100.0
    else:
        # Unsupported units
        return None


def vInitial_VF_A_Dx(v_final, acceleration, delta_x):
    '''
    Kinematic calculation: Maximum allowed initial velocity to arrive at distance X
    with specified final velocity, and given maximum linear acceleration.

    Calculate and return the (real) initial velocity, given an final velocity,
        acceleration rate, and distance interval.

    Uses the kinematic equation Vi^2 = Vf^2 - 2 a D_x , where
            Vf is the final velocity,
            a is the acceleration rate,
            D_x (delta x) is the distance interval, and
            Vi is the initial velocity.

    We are looking at the positive root only-- if the argument of the sqrt
        is less than zero, return -1, to indicate a failure.
    '''
    initial_v_squared = (v_final * v_final) - (2 * acceleration * delta_x)
    if initial_v_squared > 0:
        return sqrt(initial_v_squared)
    else:
        return -1


def vFinal_Vi_A_Dx(v_initial, acceleration, delta_x):
    '''
    Kinematic calculation: Final velocity with constant linear acceleration.

    Calculate and return the (real) final velocity, given an initial velocity,
        acceleration rate, and distance interval.

    Uses the kinematic equation Vf^2 = 2 a D_x + Vi^2, where
            Vf is the final velocity,
            a is the acceleration rate,
            D_x (delta x) is the distance interval, and
            Vi is the initial velocity.

    We are looking at the positive root only-- if the argument of the sqrt
        is less than zero, return -1, to indicate a failure.
    '''
    final_v_squared = (2 * acceleration * delta_x) + (v_initial * v_initial)
    if final_v_squared > 0:
        return sqrt(final_v_squared)
    else:
        return -1


def pathdata_first_point(path):
    '''
    Return the first (X,Y) point from an SVG path data string
    
    Input:  A path data string; the text of the 'd' attribute of an SVG path
    Output: Two floats in a list representing the x and y coordinates of the first point
    '''
    
    # Path origin's default values are used to see if we have
    # Written anything to the path_origin variable yet
    MaxLength = len(path)
    ix = 0
    tempString = ''
    x_val = ''
    y_val = ''
    # Check one char at a time
    # until we have the moveTo Command
    while ix < MaxLength:
        if path[ix].upper() == 'M':
            break
        # Increment until we have M
        ix = ix + 1

    # Parse path until we reach a digit, decimal point or negative sign
    while ix < MaxLength:
        if(path[ix].isdigit()) or path[ix] == '.' or path[ix] == '-':
            break
        ix = ix + 1

    # Add digits and decimal points to x_val
    # Stop parsing when next character is neither a digit nor a decimal point
    while ix < MaxLength:
        if  (path[ix].isdigit()):
            tempString = tempString + path[ix]
            x_val = float(tempString )
            ix = ix + 1
        # If next character is a decimal place, save the decimal and continue parsing
        # This allows for paths without leading zeros to be parsed correctly
        elif (path[ix] == '.' or path[ix] == '-'):
            tempString = tempString + path[ix]
            ix = ix + 1
        else:
            ix = ix + 1
            break

    # Reset tempString for y coordinate
    tempString = ''
    
    # Parse path until we reach a digit or decimal point
    while ix < MaxLength:
        if(path[ix].isdigit()) or path[ix] == '.' or path[ix] == '-':
            break
            ix = ix + 1
    
    # Add digits and decimal points to y_val
    # Stop parsin when next character is neither a digit nor a decimal point
    while ix < MaxLength:
        if (path[ix].isdigit() ):
            tempString = tempString + path[ix]
            y_val = float(tempString)
            ix = ix + 1
        # If next character is a decimal place, save the decimal and continue parsing
        # This allows for paths without leading zeros to be parsed correctly
        elif (path[ix] == '.' or path[ix] == '-'):
            tempString = tempString + path[ix]
            ix = ix + 1
        else:
            ix = ix + 1
            break
    return [x_val,y_val]


def pathdata_last_point(path):
    '''
    Return the last (X,Y) point from an SVG path data string
    
    Input:  A path data string; the text of the 'd' attribute of an SVG path
    Output: Two floats in a list representing the x and y coordinates of the last point
    '''

    command, params = simplepath.parsePath(path)[-1] # parsePath splits path into segments

    if command.upper() == 'Z':
        return pathdata_first_point(path)	# Trivial case
    
    '''
    Otherwise: The last command should be in the set 'MLCQA'
        - All commands converted to absolute by parsePath.
        - Can ignore Z (case handled)
        - Can ignore H,V, since those are converted to L by parsePath.
        - Can ignore S, converted to C by parsePath.
        - Can ignore T, converted to Q by parsePath.
        
        MLCQA: Commands all ending in (X,Y) pair. 
    '''
    
    x_val = params[-2] # Second to last parameter given
    y_val = params[-1] # Last parameter given
    
    return [x_val,y_val]
