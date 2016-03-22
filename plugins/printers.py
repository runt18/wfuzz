import socket
import sys
from xml.dom import minidom

import os
if os.name == "nt":
    import WConio

from externals.moduleman.plugin import moduleman_plugin
from framework.ui.console.output import getTerminalSize
from framework.ui.console.common import exec_banner, term_colors
from framework.core.myexception import FuzzException

@moduleman_plugin("header", "footer", "noresult", "result")
class magictree:
    name = "magictree"
    description = "Prints results in magictree format"
    category = ["default"]
    priority = 99

    def __init__(self):
	self.node_mt = None
	self.node_service = None

    def __create_xml_element(self, parent, caption, text):
	# Create a <xxx> element
	doc = minidom.Document()
	el = doc.createElement(caption)
	parent.appendChild(el)

	# Give the <xxx> element some text
	ptext = doc.createTextNode(text)

	el.appendChild(ptext)
	return el

    def header(self, summary):
	doc = minidom.Document()

	#<magictree class="MtBranchObject">
	self.node_mt = doc.createElement("magictree") 
	self.node_mt.setAttribute("class", "MtBranchObject")

	#<testdata class="MtBranchObject">
	node_td = doc.createElement("testdata") 
	node_td.setAttribute("class", "MtBranchObject")
	self.node_mt.appendChild(node_td)

	#<host>209.85.146.105
	host = summary.seed.history.fr_host()
	if host.find(":") > 0:
	    host, port = host.split(":")
	else:
	    port = 80
	    if summary.seed.history.fr_schema().lower() == "https":
		port = 443

	try:
	    resolving = socket.gethostbyname(host)
	    node_h = self.__create_xml_element(node_td, "host", str(resolving))
	except socket.gaierror:
	    node_h = self.__create_xml_element(node_td, "host", str(host))

	#<ipproto>tcp
	node_ipr = self.__create_xml_element(node_h, "ipproto", "tcp")

	#<port>80<state>open</state><service>http
	node_port = self.__create_xml_element(node_ipr, "port", str(port))
	self.__create_xml_element(node_port, "state", "open")
	if summary.seed.history.fr_schema().lower() == "https":
	    node_port = self.__create_xml_element(node_port, "tunnel", "ssl")

	self.node_service = self.__create_xml_element(node_port, "service", "http")

    def result(self, fuzz_result):
	node_url = self.__create_xml_element(self.node_service, "url", str(fuzz_result.url))

	if 'Server' in fuzz_result.history.fr_headers()['response']:
	    self.__create_xml_element(node_url, "HTTPServer", fuzz_result.history.fr_headers()['response']['Server'])

	location = ""
	if 'Location' in fuzz_result.history.fr_headers()['response']:
	   location = fuzz_result.history.fr_headers()['response']['Location']

	if fuzz_result.code == 301 or fuzz_result.code == 302 and location:
	    self.__create_xml_element(node_url, "RedirectLocation", location)

	self.__create_xml_element(node_url, "ResponseCode", str(fuzz_result.code))
	self.__create_xml_element(node_url, "source", "WFuzz")

    def footer(self, summary):
	sys.stderr.write(self.node_mt.toxml())

    def noresult(self, res):
	pass

@moduleman_plugin("header", "footer", "noresult", "result")
class html:
    name = "html"
    description = "Prints results in html format"
    category = ["default"]
    priority = 99

    def header(self, summary):
	url = summary.url

	sys.stderr.write("<html><head></head><body bgcolor=#000000 text=#FFFFFF><h1>Fuzzing {0!s}</h1>\r\n<table border=\"1\">\r\n<tr><td>#request</td><td>Code</td><td>#lines</td><td>#words</td><td>Url</td></tr>\r\n".format((url)) )

    def result(self, fuzz_result):
	htmlc="<font>"

	if fuzz_result.code >= 400 and fuzz_result.code < 500:
	    htmlc = "<font color=#FF0000>"
	elif fuzz_result.code>=300 and fuzz_result.code < 400:
	    htmlc = "<font color=#8888FF>"
	elif fuzz_result.code>=200 and fuzz_result.code < 300:
	    htmlc = "<font color=#00aa00>"

	if fuzz_result.history.fr_method().lower() == "post":
	    inputs=""
	    for n, v in fuzz_result.history.fr_parameters()['post'].items():
		inputs+="<input type=\"hidden\" name=\"{0!s}\" value=\"{1!s}\">".format(n, v)

	    sys.stderr.write ("\r\n<tr><td>{0:05d}</td>\r\n<td>{1!s}{2:d}</font></td>\r\n<td>{3:4d}L</td>\r\n<td>{4:5d}W</td>\r\n<td><table><tr><td>{5!s}</td><td><form method=\"post\" action=\"{6!s}\">{7!s}<input type=submit name=b value=\"send POST\"></form></td></tr></table></td>\r\n</tr>\r\n".format(fuzz_result.nres, htmlc, fuzz_result.code, fuzz_result.lines, fuzz_result.words, fuzz_result.description, fuzz_result.url, inputs))
	else:
	    sys.stderr.write("\r\n<tr><td>{0:05d}</td><td>{1!s}{2:d}</font></td><td>{3:4d}L</td><td>{4:5d}W</td><td><a href={5!s}>{6!s}</a></td></tr>\r\n".format(fuzz_result.nres, htmlc, fuzz_result.code, fuzz_result.lines, fuzz_result.words, fuzz_result.url, fuzz_result.url))

    def footer(self, summary):
	sys.stderr.write("</table></body></html><h5>Wfuzz by EdgeSecurity<h5>\r\n")
	sys.stdout.flush()

    def noresult(self, res):
	pass

@moduleman_plugin("header", "footer", "noresult", "result")
class default:
    name = "default"
    description = "Default output format"
    category = ["default"]
    priority = 99

    def __init__(self):
	if self.kbase.has("colour"):
	    self.colour = self.kbase.get("colour")
	else:
	    self.colour = False

	self.sizex, sizey = getTerminalSize()
	self.written_x = 0

	self.OS = os.name

    def _erase(self):
	self.written_x = 0
	sys.stdout.write ("\r")
	if self.OS != 'nt':
	    sys.stdout.write ("\x1b[0K")
	else:
	    WConio.clreol()

    def _write_line(self, string, line_suffix):
	self.written_x += len(string)

	if self.written_x + 31 > self.sizex:
	    string = string[:self.sizex-31] + "...\"" +  line_suffix

	sys.stdout.write(string)

    def _get_code_color(self, code):
	if code == 0:
	    cc = term_colors.fgYellow
	    wc = 12
	elif code >= 400 and code < 500:
	    cc = term_colors.fgRed
	    wc = 12
	elif code >= 300 and code < 400:
	    cc = term_colors.fgBlue
	    wc = 11
	elif code >= 200 and code < 300:
	    cc = term_colors.fgGreen
	    wc = 10
	else:
	    cc = term_colors.fgMagenta
	    wc = 1

	return (cc, wc)

    def _write(self, text, line_suffix, color = ("", 8)):
	cc, wc = color

	if cc != "":
	    if self.OS != 'nt':
		sys.stdout.write(cc)
	    else:
		WConio.textcolor(wc)

	self._write_line(text, line_suffix) 
		
	if wc != "":
	    if self.OS!='nt':
		sys.stdout.write("\033[0;0m")
	    else:
		WConio.textcolor(8)
	
    def _print(self, res, line_suffix):
	self._erase()

	txt_color = ("", 8) if not res.is_baseline or not self.colour else (term_colors.fgCyan, 8)

	self._write("{0:05d}:  C=".format((res.nres)), line_suffix, txt_color)
	if res.exception:
	    self._write("XXX", line_suffix, self._get_code_color(res.code) if self.colour else ("",8))
	else:
	    self._write("{0:03d}".format((res.code)), line_suffix, self._get_code_color(res.code) if self.colour else ("",8)) 
	self._write("   {0:4d} L\t   {1:5d} W\t  {2:5d} Ch\t  \"{3!s}\"{4!s}".format(res.lines, res.words, res.chars, res.description, line_suffix), line_suffix, txt_color)

	if line_suffix != "":
	    for i in res.plugins_res:
		print "  |_ {0!s}\r".format(i.issue)
	
	sys.stdout.flush()

    def header(self, summary):
	print exec_banner
	print "Target: {0!s}\r".format(summary.url)
	#print "Payload type: " + payloadtype + "\n"
	print "Total requests: {0:d}\r\n".format(summary.total_req)
	print "==================================================================\r"
	print "ID	Response   Lines      Word         Chars          Request    \r"
	print "==================================================================\r\n"

    def result(self, res):
	self._print(res, "\r\n")

    def noresult(self, res):
	self._print(res, "")

    def footer(self, summary):
	self._erase()
	sys.stdout.write("\r\n")

	print "Total time: {0!s}\r".format(str(summary.totaltime)[:8])

	if summary.backfeed > 0:
	    print "Processed Requests: {0!s} ({1:d} + {2:d})\r".format(str(summary.processed)[:8], (summary.processed - summary.backfeed), summary.backfeed)
	else:
	    print "Processed Requests: {0!s}\r".format((str(summary.processed)[:8]))
	print "Filtered Requests: {0!s}\r".format((str(summary.filtered)[:8]))
	print "Requests/sec.: {0!s}\r\n".format(str(summary.processed/summary.totaltime if summary.totaltime > 0 else 0)[:8])

@moduleman_plugin("header", "footer", "noresult", "result")
class verbose(default):
    name = "verbose"
    description = "Results in verbose format"
    category = ["default"]
    priority = 99

    def __init__(self):
	default.__init__(self)

    def header(self, summary):
	print exec_banner
	print "Target: {0!s}\r".format(summary.url)
	#print "Payload type: " + payloadtype + "\n"
	print "Total requests: {0:d}\r\n".format(summary.total_req)
	print

	print "==============================================================================================================================================\r"
	print "ID	C.Time   Response   Lines      Word         Chars                  Server                                             Redirect   Request    \r"
	print "==============================================================================================================================================\r\n"

    def _print(self, res, line_suffix):
	self._erase()

	txt_color = ("", 8) if not res.is_baseline or not self.colour else (term_colors.fgCyan, 8)

	self._write("{0:05d}:  ".format((res.nres)), line_suffix, txt_color) 
	self._write("{0:.3f}s   C=".format((res.timer)), line_suffix, txt_color) 

	location = ""
	if 'Location' in res.history.fr_headers()['response']:
	   location = res.history.fr_headers()['response']['Location']
	elif res.history.fr_url() != res.history.fr_redirect_url():
	    location = "(*) {0!s}".format(res.history.fr_url())

	server = ""
	if 'Server' in res.history.fr_headers()['response']:
	    server = res.history.fr_headers()['response']['Server']

	if res.exception:
	    self._write("XXX", line_suffix, self._get_code_color(res.code) if self.colour else ("",8))
	else:
	    self._write("{0:03d}".format((res.code)), line_suffix, self._get_code_color(res.code) if self.colour else ("",8)) 

	self._write("   {0:4d} L\t   {1:5d} W\t  {2:5d} Ch  {3:20.20!s}  {4:51.51!s}   \"{5!s}\"{6!s}".format(res.lines, res.words, res.chars, server[:17], location[:48], res.description, line_suffix), line_suffix, txt_color)

	if line_suffix != "":
	    for i in res.plugins_res:
		print "  |_ {0!s}\r".format(i.issue)
	
	sys.stdout.flush()

