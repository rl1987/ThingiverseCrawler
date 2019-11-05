#!/usr/bin/python3

import thingiverse_crawler as crawler
import tkinter as tk
from tkinter.filedialog import askdirectory
from tkinter import messagebox
import os

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

    def choose_dir_pressed(self):
        out_dir = askdirectory(initialdir=os.getcwd())

        self.out_dir_entry.delete(0, tk.END)
        self.out_dir_entry.insert(0, out_dir)

    def start_button_pressed(self):
        # TODO: validate
        out_dir = self.out_dir_entry.get()

        url = self.url_entry.get()

        url += "/page:{}"

        crawler.crawl_things_internal(None, out_dir, url, None)

root = tk.Tk()
gui = CrawlerGUI(root)
root.mainloop()

