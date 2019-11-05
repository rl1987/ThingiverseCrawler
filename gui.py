#!/usr/bin/python3

import thingiverse_crawler as crawler
import tkinter as tk
from tkinter.filedialog import askdirectory
from tkinter import messagebox
import os
import threading
import time

class CrawlerGUI():
    def __init__(self, master):
        self.master = master
        master.title("ThingInverse crawler")

        self.left_frame = tk.Frame(self.master)
        self.left_frame.pack(side=tk.LEFT)

        self.url_label = tk.Label(self.left_frame, text="URL:")
        self.url_label.pack()

        self.url_entry = tk.Entry(self.left_frame)
        self.url_entry.pack()

        self.out_dir_label = tk.Label(self.left_frame, text="Output dir:")
        self.out_dir_label.pack()

        self.out_dir_entry = tk.Entry(self.left_frame)
        self.out_dir_entry.pack()

        self.dir_button = tk.Button(self.left_frame, text="Choose dir...", command=self.choose_dir_pressed)
        self.dir_button.pack()

        self.right_frame = tk.Frame(self.master)
        self.right_frame.pack(side=tk.RIGHT)

        self.start_button = tk.Button(self.right_frame, text="Start", command=self.start_button_pressed)
        self.start_button.pack()

        self.crawling = False

    def choose_dir_pressed(self):
        if self.crawling:
            return

        out_dir = askdirectory(initialdir=os.getcwd())

        self.out_dir_entry.delete(0, tk.END)
        self.out_dir_entry.insert(0, out_dir)

    def is_valid_url(self, url):
        if not "thingiverse.com" in url:
            return False

        if not "collections" in url and not "explore" in url and not "search" in url:
            return False

        return True

    def start_crawling(self, out_dir, url):
        crawler.crawl_things_internal(None, out_dir, url, None)
        self.crawling = False

    def start_button_pressed(self):
        if self.crawling:
            return
        
        out_dir = self.out_dir_entry.get()

        if out_dir is None or len(out_dir) == 0:
            messagebox.showerror('Error', 'Output directory path must be set')
            return

        url = self.url_entry.get()

        if not self.is_valid_url(url):
            messagebox.showerror('Error', 'URL must be one of: 1) explore page (e.g. https://www.thingiverse.com/newest/), 2) search page (e.g. https://www.thingiverse.com/search?q=toy), 3) collection page (e.g. https://www.thingiverse.com/MakerTinkerSoldierSpy/collections/space-marines) without page parameter')
            return

        url += "/page:{}"

        t = threading.Thread(target=self.start_crawling, args=(out_dir, url, ), daemon=True)
        t.start()

        print("!!!")

        self.crawling = True

        x = 0

        while self.crawling:
            time.sleep(0.5)
            
            x = (x + 1) % 4

            header = "Crawling"

            for _ in range(x):
                header += "."

            self.master.title(header)
            self.master.update()
            
        self.master.title("ThingInverse crawler")
        self.master.update()

root = tk.Tk()
gui = CrawlerGUI(root)
root.mainloop()

