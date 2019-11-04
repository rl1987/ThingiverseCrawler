#!/usr/bin/python3

import thingiverse_crawler
import tkinter as tk
from tkinter.filedialog import askdirectory
from tkinter import messagebox

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

        self.dir_button = tk.Button(self.left_frame, text="Choose dir...")
        self.dir_button.pack()

        self.right_frame = tk.Frame(self.master)
        self.right_frame.pack(side=tk.RIGHT)

        self.start_button = tk.Button(self.right_frame, text="Start")
        self.start_button.pack()

root = tk.Tk()
gui = CrawlerGUI(root)
root.mainloop()

