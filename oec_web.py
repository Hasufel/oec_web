import xml.etree.ElementTree as ET
import glob
from flask import Flask, abort, render_template
from math import *


OEC_PATH = "open_exoplanet_catalogue/"

print "Parsing OEC ..."
planet_names = {}
planets = []
stars = []
binaries = []

# Loop over all files and  create new data
for filename in glob.glob(OEC_PATH + "systems/*.xml"):
    # Open file
    f = open(filename, 'rt')

    # Try to parse file
    try:
        root = ET.parse(f).getroot()
        planets += root.findall(".//planet")
        stars += root.findall(".//star")
        binaries += root.findall(".//binary")
    except ET.ParseError as error:
        print '{}, {}'.format(filename, error)
        continue
    finally:
        f.close()

    for planet in planets:
        names = planet.findall("./name")
        for name in names:
            planet_names[name.text] = filename

print "Parsing OEC done"

def toFixed(f,digits):
    formatstring = "%%.%df"%digits
    return formatstring % f

notAvailableString = "<span class=\"NA\">N/A</span>"
def renderFloat(tag, factor=1.):
    if tag is None:
        return notAvailableString
    if "errorplus" in tag.attrib:
        error_plus = float(tag.attrib["errorplus"])*factor
    else:
        error_plus = None
    if "errorminus" in tag.attrib:
        error_minus = float(tag.attrib["errorminus"])*factor
    else:
        error_minus = None
    if "upperlimit" in tag.attrib:
        upperlimit = float(tag.attrib["upperlimit"])*factor
    else:
        upperlimit = None
    if "lowerlimit" in tag.attrib:
        lowerlimit = float(tag.attrib["lowerlimit"])*factor
    else:
        lowerlimit = None
    if tag.text is not None:
        value = float(tag.text)*factor
    else:
        value = None

    hideErrors = False
    dataString = ""
    exp0String = ""
    exp1String = ""
    exp2String = ""
    errorMinusString = ""
    errorPlusString = ""
    errorString = ""
    
    isExp = True
    exponent = ""
    dexponent = ""
    if value is not None:
        exponent = floor(log10(value))
        dexponent = pow(10, exponent)
    elif upperlimit is not None:
        exponent = floor(log10(upperlimit))
        dexponent = pow(10, exponent)
    elif lowerlimit is not None:
        exponent = floor(log10(lowerlimit))
        dexponent = pow(10, exponent)
    else:
        return notAvailableString
            
    if (exponent>-4 and exponent<5) or (value is not None and value<=0.):
        isExp = False
    else:
        diexponent = 1./dexponent
        if value is not None:
            value		*=diexponent
        if error_minus is not None:
            error_minus	*=diexponent
        if error_plus is not None:
            error_plus	*=diexponent
        if upperlimit is not None:
            upperlimit	*=diexponent
        if lowerlimit is not None:
            lowerlimit	*=diexponent
    
    significantdigits = 2
    if value is not None:
        significantdigits = -floor(log10(fabs(value/2.)))
        if error_plus is not None and error_minus is not None:
            error_significantdigits = max(-floor(log10(error_plus/2.)),-floor(log10(error_minus/2.)))
            significantdigits = max(error_significantdigits,significantdigits)
        else:
            significantdigits +=2
        
    else:
        # upper/lower limits
        significantdigits = 4
    
    significantdigits = min(significantdigits,4.)
    significantdigits = max(significantdigits,0.)

    hasErrors = False
    if (error_plus is not None or error_minus is not None) and (not hideErrors):
        hasErrors = True
    
    
    if value is not None:
        dataString = toFixed(value,significantdigits)
    else:
        if lowerlimit is not None:
            dataString = "&gt; "+toFixed(lowerlimit,significantdigits)
        elif upperlimit is not None:
            dataString = "&lt; "+toFixed(upperlimit,significantdigits)
        
    
    if isExp:
        exp2String = "%d"%int(exponent)
        if hasErrors:
            exp1String = " )&#183;10"
        else:
            exp1String = " &#183;10"
        
    else:
        exp1String = ""
        exp2String = ""
    
    
    if hasErrors:
    	if error_minus is not None:
    		errorMinusString = "&#8722;"+toFixed(error_minus,significantdigits)
    	else:
    		errorMinusString = ""
    	
    	if error_plus is not None:
    		errorPlusString = "&#43;"+toFixed(error_plus,significantdigits)
    	else:
    		errorPlusString = ""
    	
    	if error_minus is not None and error_plus is not None:
            if errorMinusString[7:]==errorPlusString[5:]:
                errorString = "&#177;"+ errorMinusString[7:]
                errorMinusString = ""
                errorPlusString = ""
            else:
                errorString = ""
    	else:
            errorString = ""
    
    else:
        errorString		= ""
        errorMinusString	= ""
        errorPlusString		= ""
    
    
    if isExp and hasErrors:
        exp0String = "( "
    else:
        exp0String = ""
    
    returnString = ""
    returnString += exp0String
    returnString += dataString
    returnString += errorString
    if errorPlusString or errorMinusString:
        returnString += "<span class=\"errorbars\">"
        returnString += "<span class=\"errorplus\">"+errorPlusString+"</span>"
        returnString += "<span class=\"errorminus\">"+errorMinusString+"</span>"
        returnString += "</span>"
    
    if exp2String or exp1String:
        returnString += exp1String+"<sup>"+exp2String+"</sup>"
    
    
    return returnString;

app = Flask(__name__)
@app.route('/')
@app.route('/index.html')
def main_page():
    return render_template("index.html")

@app.route('/systems/')
def systems():
    p = []
    for planet in planets:
        d = {}
        try:
            name = planet.find("./name").text
        except:
            name = "None"
        d["name"] = name 
        f = []
        mass = renderFloat(planet.find("./mass"))
        f.append(mass)
        d["fields"] = f
        p.append(d)
    return render_template("systems.html",planets=p)


@app.route('/planet/<planetname>')
def hello_planet(planetname):
    try:
        with open(planet_names[planetname],'r') as f:
            return f.read()
    except KeyError, e:
        abort(404)
    abort(404)


if __name__ == '__main__':
    app.run(debug=True)
