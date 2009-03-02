import wx
import urllib2
import time
import random
import re

ID_ABOUT = 101
ID_EXIT = 110
ID_CONVERT = 201
version = "1.0"

def fetch():
    url = "http://www.xe.com/ict/"
    ## XE doesn't seem to like python's urllib
    headers = { 'User-Agent' : useragent }
    ## Also, they don't seem to know the day
    dateinfo = time.strftime("%m %d %Y").split()
    ## And lets click on the button differently each time (the randints)
    postcontents = "basecur=%s&historical=false&month=%i&day=%i&year=%i&sort_by=name&image.x=%i&image.y=%i&image=Submit" % (currencies[0], int(dateinfo[0]), int(dateinfo[1]), int(dateinfo[2]), random.randint(1,89), random.randint(1,24))

    req = urllib2.Request(url, postcontents, headers)
    response = urllib2.urlopen(req)
    results = response.read()

    return results

def extract(cur, data, comm1list, comm2list):
    ## Get values
    p = re.compile("%s</td><td align=\"left\">([a-zA-Z\s])*</td><td align=\"right\">([\d.])*</td>" % cur)
    m = p.finditer(data)

    ## Check whether the found values are commented
    ## (Checks whether '<!' or '-->' comes first after the found values)
    for match in m:
        a = match.end()
        found = False
        for x in comm1list:
            if (x > a) and (found == False):
                found = True
                comm1pos = x
        found = False
        for x in comm2list:
            if (x > a) and (found == False):
                found = True
                comm2pos = x
        if comm1pos < comm2pos:
            line = match.group()
            
    ## Some numbers are longer than 12 characters, so we use a re to exactly determine the starting position.
    p2 = re.compile("right")
    m2 = p2.search(line)
    return float(line[m2.end()+2:-5])

def parse(data):
    ## Check commented postitions
    commp1 = re.compile("<!")
    commiter1 = commp1.finditer(data)
    commp2 = re.compile("-->")
    commiter2 = commp2.finditer(data)
    comm1list = []
    comm2list = []
    for match in commiter1:
        comm1list += [match.start()]
    for match in commiter2:
        comm2list += [match.start()]

    #Get exchange rates
    for i in range(1, len(currencies)):
        curvals[i] = extract(currencies[i], data, comm1list, comm2list)

    return curvals
    
def conv(fromcur, tocur, amount):
    ## Check whether it should be converted from or to eur,
    ## and if neither, convert to eur first and then from eur.
    ## (Bit sloppy, but uses way less bandwith and processing power.
    ##  The difference will be too little to notice anyway.)
    if fromcur == currencies[0]:
        for i in range(1, len(currencies)):
            if tocur == currencies[i]:
                answer = amount * curvals[i]
    elif tocur == currencies[0]:
        for i in range(1, len(currencies)):
            if fromcur == currencies[i]:
                answer = amount / curvals[i]
    else:
        answer = conv(currencies[0], tocur, conv(fromcur, currencies[0], amount))
    return round(answer, 2)

def loadconfig(filename):
    #Default vars, they'll get overwritten if they are defined in the file.
    currencies = ["EUR", "USD", "PLN", "GBP"]
    useragent = "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.8.1.13) Gecko/20080311 Firefox/2.0.0.13"
    
    f = open(filename, 'r')
    for line in f:
        line = line.split()
        if len(line):
            if line[0] == "currencies":
                currencies = line[1:]
            elif line[0] == "useragent":
                useragent = ' '.join(line[1:])
    f.close()
    return currencies, useragent

class MainWindow(wx.Frame):
    def __init__(self, parent, id, title):
        
        wx.Frame.__init__(self, parent, id, title)
        #Create a panel, this looks a lot nicer.
        panel = wx.Panel(self)

        #Topleft, currency names
        self.topleftsizer = wx.BoxSizer(wx.VERTICAL)
        for i in range(1, len(currencies)):
            self.topleftsizer.Add(wx.StaticText(panel, -1, label=currencies[i]), 1, wx.ALL)

        #Topright, rates
        self.toprightsizer = wx.BoxSizer(wx.VERTICAL)
        for i in range(1, len(curvals)):
            self.toprightsizer.Add(wx.StaticText(panel, -1, label=str(curvals[i])), 1, wx.ALL)

        #Bottom1, dropdowns
        self.bottom1sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.fromcurdd = wx.Choice(panel)
        self.fromcurdd.AppendItems(currencies)
        self.tocurdd = wx.Choice(panel)
        self.tocurdd.AppendItems(currencies)
        self.bottom1sizer.Add(self.fromcurdd, 1, wx.ALL, 5)
        self.bottom1sizer.Add(self.tocurdd, 1, wx.ALL, 5)

        #Bottom2, inputs
        self.bottom2sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.frominput = wx.TextCtrl(panel)
        self.toinput = wx.TextCtrl(panel, style=wx.TE_READONLY)
        self.bottom2sizer.Add(self.frominput, 1, wx.ALL, 5)
        self.bottom2sizer.Add(self.toinput, 1, wx.ALL, 5)
        #EVENT ON ENTER?
        
        self.CreateStatusBar()

        filemenu = wx.Menu()
        filemenu.Append(ID_ABOUT, "&About", "Information about this program")
        filemenu.AppendSeparator()
        filemenu.Append(ID_EXIT, "&Exit", "Terminate the program")

        menuBar = wx.MenuBar()
        menuBar.Append(filemenu, "&File")
        self.SetMenuBar(menuBar)

        wx.EVT_MENU(self, ID_ABOUT, self.OnAbout)
        wx.EVT_MENU(self, ID_EXIT, self.OnExit)

        #Setting all the sizers etc.
        self.topsizer = wx.BoxSizer(wx.HORIZONTAL)
        self.topsizer.Add(self.topleftsizer, 0, wx.ALL, 2)
        self.topsizer.Add(self.toprightsizer, 0, wx.ALL, 2)

        self.bottomsizer = wx.BoxSizer(wx.VERTICAL)
        self.bottomsizer.Add(self.bottom1sizer, 0, wx.ALIGN_CENTER, 2)
        self.bottomsizer.Add(self.bottom2sizer, 0, wx.EXPAND, 2)

        self.mainsizer = wx.BoxSizer(wx.VERTICAL)
        self.label1 = wx.StaticText(panel, -1, label="Current rates:")
        self.label2 = wx.StaticText(panel, -1, label="(fetched at %s)" % fetchtime)
        self.label3 = wx.StaticText(panel, -1, label="(base currency: %s)" % currencies[0])
        self.mainsizer.Add(self.label1, 0, wx.ALIGN_CENTER, 2)
        self.mainsizer.Add(self.label2, 0, wx.ALIGN_CENTER, 2)
        self.mainsizer.Add(self.label3, 0, wx.ALIGN_CENTER, 2)
        self.mainsizer.Add(self.topsizer, 0, wx.ALIGN_CENTER, 10)
        self.mainsizer.Add(self.bottomsizer, 0, wx.EXPAND, 5)
        self.convertbtn = wx.Button(panel, ID_CONVERT, "Convert")
        self.mainsizer.Add(self.convertbtn, 0, wx.ALIGN_CENTER, 2)

        wx.EVT_BUTTON(panel, ID_CONVERT, self.OnConvert)
        
        panel.SetSizer(self.mainsizer)
        panel.SetAutoLayout(True)
        self.mainsizer.Fit(self)
        
        self.Show(True)

    def OnAbout(self, e):
        d = wx.MessageDialog(self, "A currency converter in python using wxpython to convert different currencies.\nThe rates are fetched from www.xe.com .\nMade by krisje8. Version: %s.\nCheck www.krisje8.nl for updates." % version, "About Currency Converter", wx.OK)
        d.ShowModal()
        d.Destroy()

    def OnExit(self, e):
        self.Close(True)

    def OnConvert(self, e):
        if self.fromcurdd.GetSelection() is not -1:
            if self.tocurdd.GetSelection() is not -1:
                if self.fromcurdd.GetSelection() is not self.tocurdd.GetSelection():
                    try:
                        float(self.frominput.GetValue())
                        self.toinput.SetValue(str(conv(currencies[self.fromcurdd.GetSelection()], currencies[self.tocurdd.GetSelection()], float(self.frominput.GetValue()))))
                    except:
                        d = wx.MessageDialog(self, "Input a number in the left inputfield, and use dots ( . ) instead of commas ( , ).", "Error", wx.OK)
                else:
                    d = wx.MessageDialog(self, "The currency to convert from and the currency to convert to should be different from each other.", "Error", wx.OK)
            else:
                d = wx.MessageDialog(self, "Select a currency to convert to.", "Error", wx.OK)
        else:
            d = wx.MessageDialog(self, "Select a currency to convert from.", "Error", wx.OK)
        ## Display an error message if set.
        try:
            d.ShowModal()
            d.Destroy()
        except:
            pass


#Main app
currencies, useragent = loadconfig("config.txt")
curvals = [1] * len(currencies)
curvals = parse(fetch())
fetchtime = time.strftime("%d-%m-%Y %H:%M")

app = wx.PySimpleApp()
frame = MainWindow(None, -1, "Currency Converter by krisje8")
app.MainLoop()
