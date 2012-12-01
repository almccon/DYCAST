#! /usr/bin/env python

# The Graphical User Interface for manual operation of the DYCAST system

import Tkinter, tkFileDialog, tkMessageBox
import os
import dycast
import datetime
import optparse
import fileinput

usage = "usage: %prog [options]"
p = optparse.OptionParser(usage)
p.add_option('--config', '-c', 
            default="./dycast.config", 
            help="load config file FILE", 
            metavar="FILE")

options, arguments = p.parse_args()

config_file = options.config

my_bgcolor = "gray"
my_panelcolor = "light gray"
my_highlightcolor = "white"

class DYCAST_control(Tkinter.Frame):
    def connect_to_DYCAST(self):
        dycast.read_config(config_file)
        dycast.init_db()
        dycast.init_logging()
        

    def load_birds(self):
        self.status_label["text"] = "Status: loading birds..."
        self.status_label.update_idletasks()
        self.load_birds_button["state"] = Tkinter.DISABLED
        self.files = self.load_birds_entry.get()
        self.files = self.files.split(" ")
        try:
            for file in self.files:
                dir, base = os.path.split(file)
                self.status_label["text"] = "Status: loading birds... %s" % base
                self.status_label.update_idletasks()
                dycast.load_bird_file(file)
        except:
            if (self.files):
                tkMessageBox.showwarning(
                    "Open file",
                    "Cannot open file(s): %s" % self.files
                )
            else:
                tkMessageBox.showwarning(
                    "Open file",
                    "No files selected"
                )
            
        self.load_birds_button["state"] = Tkinter.NORMAL
        self.status_label["text"] = "Status: ready"
        self.status_label.update_idletasks()

    def set_bird_file(self):
        #file = tkFileDialog.askopenfile(parent=self, mode='rb', title="select dead bird files")
        self.files = tkFileDialog.askopenfilenames(parent=self, title="select dead bird files")
        self.load_birds_entry.delete(0, Tkinter.END)
        self.load_birds_entry.insert(0, self.files)

    def set_export_dir(self):
        self.export_dir = tkFileDialog.askdirectory(parent=self, title="choose export directory")
        self.export_dir_entry.delete(0, Tkinter.END)
        self.export_dir_entry.insert(0, self.export_dir)

    def get_date_range(self, datestring1, datestring2):
        (y,m,d) = datestring1.split('-')
        startdate = datetime.date(int(y), int(m), int(d))
        (y,m,d) = datestring2.split('-')
        enddate = datetime.date(int(y), int(m), int(d))

        datediff = startdate - enddate
        if (enddate > startdate):
            firstdate = startdate
            lastdate = enddate
        else:
            lastdate = startdate
            firstdate = enddate
        curdate = startdate
        return (curdate, lastdate)

    def get_date_iterator(self, datestring1, datestring2):
        (y,m,d) = datestring1.split('-')
        startdate = datetime.date(int(y), int(m), int(d))
        (y,m,d) = datestring2.split('-')
        enddate = datetime.date(int(y), int(m), int(d))
        return range(startdate, enddate)
        
    def run_daily_risk(self):
        self.status_label["text"] = "Status: generating risk..."
        self.status_label.update_idletasks()
        self.daily_risk_button["state"] = Tkinter.DISABLED

        (curdate, enddate) = self.get_date_range(
            self.daily_risk_entry1.get(),
            self.daily_risk_entry2.get()
        )
        oneday = datetime.timedelta(days=1)

        while (curdate <= enddate):
            self.status_label["text"] = "Status: generating risk... %s" % curdate
            self.status_label.update_idletasks()
            try:
                dycast.daily_risk(curdate)
                #dycast.daily_risk(curdate, 5580000, 5710000) # for testing
            except:
                tkMessageBox.showwarning(
                    "Daily risk",
                    "Could not run daily risk for %s" % curdate
                )
                break
            curdate = curdate + oneday

        self.daily_risk_button["state"] = Tkinter.NORMAL
        self.status_label["text"] = "Status: ready"
        self.status_label.update_idletasks()

    def run_export_risk(self):
        self.status_label["text"] = "Status: exporting risk..."        
        self.status_label.update_idletasks()
        self.export_risk_button["state"] = Tkinter.DISABLED

        (curdate, enddate) = self.get_date_range(
            self.export_risk_entry1.get(),
            self.export_risk_entry2.get()
        )

        oneday = datetime.timedelta(days=1)

        while (curdate <= enddate):
            self.status_label["text"] = "Status: exporting risk... %s" % curdate
            self.status_label.update_idletasks()
            self.export_dir = self.export_dir_entry.get()
            try:
                dycast.export_risk(curdate, "dbf", self.export_dir)
            except Exception, inst:
                tkMessageBox.showwarning(
                    "Export risk",
                    "Could not export daily risk for %s: %s" % (curdate, inst)
                )
                break
            curdate = curdate + oneday
        # Working here.

        self.export_risk_button["state"] = Tkinter.NORMAL
        self.status_label["text"] = "Status: ready"
        self.status_label.update_idletasks()
 

    def createWidgets(self):
        self.label1 = Tkinter.Label(self, bg=my_bgcolor)
        self.label1["text"] = "DYCAST actions:\nselect from the options below\n"
        self.label1["justify"] = Tkinter.LEFT
        self.label1.pack(side=Tkinter.TOP, anchor=Tkinter.W)

        self.bird_frame = Tkinter.Frame(self, background=my_panelcolor, borderwidth=2, relief=Tkinter.RAISED)
        self.bird_frame.pack(
            side=Tkinter.TOP,
            anchor=Tkinter.W,
            fill=Tkinter.BOTH,
            ipadx=5, ipady=5, padx=5, pady=5,
            )

        self.label2 = Tkinter.Label(self.bird_frame, bg=my_panelcolor)
        self.label2["text"] = "load dead birds from file(s):\n"
        self.label2["justify"] = Tkinter.LEFT
        self.label2.pack(side=Tkinter.TOP, anchor=Tkinter.W)

        self.load_birds_entry = Tkinter.Entry(self.bird_frame)

        self.load_birds_entry.pack({"side": "left", "expand": 1, "fill": "x"})

        self.load_birds_button = Tkinter.Button(self.bird_frame, background=my_panelcolor)
        self.load_birds_button["text"] = "load birds"
        self.load_birds_button["command"] =  self.load_birds

        self.load_birds_button.pack({"side": "right"})

        self.bird_file_button = Tkinter.Button(self.bird_frame, bg=my_panelcolor)
        self.bird_file_button["text"] = "select files"
        self.bird_file_button["command"] =  self.set_bird_file

        self.bird_file_button.pack({"side": "right"})

        self.risk_frame = Tkinter.Frame(self, background=my_panelcolor, borderwidth=2, relief=Tkinter.RAISED)
        self.risk_frame.pack(
            side=Tkinter.TOP,
            anchor=Tkinter.W,
            fill=Tkinter.BOTH,
            ipadx=5, ipady=5, padx=5, pady=5,
            )

        self.label3 = Tkinter.Label(self.risk_frame, bg=my_panelcolor)
        self.label3["text"] = "generate daily risk for the following date(s): (in YYYY-MM-DD format)\n"
        self.label3["justify"] = Tkinter.LEFT
        self.label3.pack(side=Tkinter.TOP, anchor=Tkinter.W)

        self.label_entry1 = Tkinter.Label(self.risk_frame, bg=my_panelcolor)
        self.label_entry1["text"] = "start date:"
        self.label_entry1.pack({"side": "left"})

        self.daily_risk_entry1 = Tkinter.Entry(self.risk_frame)
        self.daily_risk_entry1.insert(0, datetime.date.today().strftime("%Y-%m-%d"))
        self.daily_risk_entry1.pack({"side": "left"})

        self.label_entry2 = Tkinter.Label(self.risk_frame, bg=my_panelcolor)
        self.label_entry2["text"] = "end date:"
        self.label_entry2.pack({"side": "left"})

        self.daily_risk_entry2 = Tkinter.Entry(self.risk_frame)
        self.daily_risk_entry2.insert(0, datetime.date.today().strftime("%Y-%m-%d"))
        self.daily_risk_entry2.pack({"side": "left"})

        self.daily_risk_button = Tkinter.Button(self.risk_frame, bg=my_panelcolor)
        self.daily_risk_button["text"] = "run risk"
        self.daily_risk_button["command"] = self.run_daily_risk

        self.daily_risk_button.pack({"side": "right"})

        self.export_frame = Tkinter.Frame(self, background=my_panelcolor, borderwidth=2, relief=Tkinter.RAISED)
        self.export_frame.pack(
            side=Tkinter.TOP,
            anchor=Tkinter.W,
            fill=Tkinter.BOTH,
            ipadx=5, ipady=5, padx=5, pady=5,
            )

        self.label3 = Tkinter.Label(self.export_frame, bg=my_panelcolor)
        self.label3["text"] = "export daily risk for the following date(s): (in YYYY-MM-DD format)\n"
        self.label3["justify"] = Tkinter.LEFT
        self.label3.pack(side=Tkinter.TOP, anchor=Tkinter.W)

        self.export_dir_frame = Tkinter.Frame(self.export_frame, background=my_panelcolor)
        self.export_dir_frame.pack({"side": "top", "anchor": "w", "fill": "both"})

        self.label_export_dir_entry = Tkinter.Label(self.export_dir_frame, bg=my_panelcolor)
        self.label_export_dir_entry["text"] = "export directory:"
        self.label_export_dir_entry.pack({"side": "left", "anchor": "w"})

        self.export_dir_entry = Tkinter.Entry(self.export_dir_frame)
        self.export_dir_entry.pack({"side": "left", "expand": 1, "fill": "x"})

        self.browse_export_dir_button = Tkinter.Button(self.export_dir_frame, bg=my_panelcolor)
        self.browse_export_dir_button["text"] = "browse"
        self.browse_export_dir_button["command"] =  self.set_export_dir

        self.browse_export_dir_button.pack({"side": "right", "anchor": "e"})

        self.label_entry1 = Tkinter.Label(self.export_frame, bg=my_panelcolor)
        self.label_entry1["text"] = "start date:"
        self.label_entry1.pack({"side": "left"})

        self.export_risk_entry1 = Tkinter.Entry(self.export_frame)
        self.export_risk_entry1.insert(0, datetime.date.today().strftime("%Y-%m-%d"))
        self.export_risk_entry1.pack({"side": "left"})

        self.label_entry2 = Tkinter.Label(self.export_frame, bg=my_panelcolor)
        self.label_entry2["text"] = "end date:"
        self.label_entry2.pack({"side": "left"})

        self.export_risk_entry2 = Tkinter.Entry(self.export_frame)
        self.export_risk_entry2.insert(0, datetime.date.today().strftime("%Y-%m-%d"))
        self.export_risk_entry2.pack({"side": "left"})

        self.export_risk_button = Tkinter.Button(self.export_frame, bg=my_panelcolor)
        self.export_risk_button["text"] = "export"
        self.export_risk_button["command"] = self.run_export_risk

        self.export_risk_button.pack({"side": "right"})

        #self.QUIT = Tkinter.Button(self)
        #self.QUIT["text"] = "QUIT"
        #self.QUIT["fg"]   = "red"
        #self.QUIT["command"] =  self.quit
        #self.QUIT.pack({"side": "right"})

        self.status_label = Tkinter.Label(self, relief=Tkinter.SUNKEN, anchor=Tkinter.W, bg=my_bgcolor)
        self.status_label["text"] = "Status: ready"
        self.status_label.pack(fill=Tkinter.X)

    def __init__(self, master=None):
        Tkinter.Frame.__init__(self, master)
        self.config(bg = my_bgcolor)
        self.pack()
        self.connect_to_DYCAST()
        self.createWidgets()
        self.files = None
        self.export_dir = None

root = Tkinter.Tk()
root.title("DYCAST control")
app = DYCAST_control(master=root)
app.mainloop()
#root.destroy()
