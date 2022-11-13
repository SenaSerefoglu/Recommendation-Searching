from tkinter import *
from clusters import *
from classes import *
import tkinter.messagebox as msgbox
import tkinter.scrolledtext as tkst

class Example(Frame):
    def __init__(self, parent):
        Frame.__init__(self, parent)
        self.parent = parent
        self.initUI()

    def initUI(self):

        # Frameler
        self.frame1 = Frame(width=750, height=60, )
        self.frame1.grid()
        self.frame2 = Frame(width=750, height=60, )
        self.frame2.grid()
        self.frame3 = Frame(width=750, height=60, )
        self.frame3.grid()

        # Frame1
        self.b1 = Button(self.frame1, text="Start crawling", command=self.StartCraw)
        self.txt1 = Label(self.frame1, text="Crawling finished.")

        # Frame2
        self.lb1 = Listbox(self.frame2, width=40, selectmode=MULTIPLE)
        self.txt2 = Label(self.frame2, text='Type in the word you want to search:')
        self.var = StringVar()
        self.e1 = Entry(self.frame2, textvariable=self.var)
        self.b2 = Button(self.frame2, text='List the similar words', command = self.ListWords)
        self.b3 = Button(self.frame2, text='Add the words', command = self.AddWord)
        self.b4 = Button(self.frame2, text='Search for the class', command = self.SearchClass)

        # Frame3
        self.txt3 = Label(self.frame3, text="Searching results:")
        self.textbox1 = tkst.ScrolledText(self.frame3, width=77, height=17)
        self.textbox2 = tkst.ScrolledText(self.frame3, width=27, height=17)
        self.txt4 = Label(self.frame3, text="Probability of the year:")

        # The Design
        # Frame1
        self.b1.grid(row=0, column=0)
        self.txt1.grid(row=1, column=0)

        # Frame2
        self.lb1.grid(row=1, column=5, rowspan=5)
        self.txt2.grid(row=1, column=3, columnspan=2)
        self.e1.grid(row=4, column=3)
        self.b2.grid(row=4, column=4)
        self.b3.grid(row=1, column=7)
        self.b4.grid(row=4, column=7)

        # Frame3
        self.txt3.grid(row=0, column=0)
        self.txt4.grid(row=0, column=1)
        self.textbox2.grid(row=1, column=1)
        self.textbox1.grid(row=1, column=0)


    def selected_items(self):
        items=[]
        for i in self.lb1.curselection():
            items.append(self.lb1.get(i))
        if len(items) == 0:
            msgbox.showerror(title="Error", message="There is no item selected in the listbox.")
        return items


    def StartCraw(self):
        self.txt1['text'] = "Crawling..."
        try:
            crawler_ = crawler(dbtables)
            crawler_.openindextables()
            crawler_.wordlocation['derin'] # We are checking if the databases works alright.
            crawler_.urllist['https://ois.istinye.edu.tr/bilgipaketi/index/ders/ders_id/7249/program_kodu/0401001/s/2/st/M/ln/tr/print/1/']
            crawler_.close()
            self.txt1['text'] = "Crawling Finished."

        except: # Starts crawling if it isnt done.
            crawler_ = crawler(dbtables)
            crawler_.createindextables()
            crawler_.crawl(pagelist, depth=2)
            crawler_.close()
            self.txt1['text'] = "Crawling finished."


    def ListWords(self):
        if self.var.get() == "":
            msgbox.showerror(title="Error", message="Entry object doesnt have a value.")
        
        crawler_ = crawler(dbtables)
        crawler_.openindextables()
        list0 = data_creation(crawler_.wordlocation)

        kclust = kcluster(list0, k=5)


        i = 0  # Adds the words that are in the same cluster with the word that user typed in the entry object to the listbox object.
        for word in list0:
            if self.var.get() == word:
                valueofWord = i
            i += 1
        for list1 in kclust:
            if valueofWord in list1:
                result = list1
        for val in result:
            self.lb1.insert(END, list0[val])
        crawler_.close()


    def AddWord(self): # Adds the words that user selected in the listbox to the entry object.
        list0 = self.selected_items()
        string = self.var.get()
        for element in list0:
            string = string + " " + element
        self.var.set(string)
    

    def SearchClass(self): # Runs the search class functions for the string in the entry object.
        self.textbox1.delete('1.0', END)
        crawler_ = crawler(dbtables)
        crawler_.openindextables()
        searcher_ = searcher(crawler_.urllist, crawler_.wordlocation)
        if self.var.get() == "":
            msgbox.showerror(title="Error", message="Entry object doesnt have a value.")
            return
        try:
            data = searcher_.query(self.var.get())
            for element in data:
                string = str(element[0]) + " --------> " + str(element[1]) + "\n"
                self.textbox1.insert(END, string)
        except:
            msgbox.showerror(title="Error", message="Couldnt find a matching page...")
        crawler_.close()