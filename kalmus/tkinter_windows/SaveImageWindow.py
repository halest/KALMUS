""" SaveImageWindow Class """

import tkinter
from tkinter.messagebox import showerror, showinfo
import tkinter.filedialog
import matplotlib.pyplot as plt
import cv2
import os

from kalmus.tkinter_windows.gui_utils import resource_path


class SaveImageWindow():
    """
    SaveImageWindow Class
    Save the barcode into the image
    """
    def __init__(self, barcode_1, barcode_2):
        """
        Initialize
        :param barcode_1: The barcode 1
        :param barcode_2: The barcode 2
        """
        # Initialize the window
        self.window = tkinter.Tk()
        self.window.iconbitmap(resource_path("kalmus_icon.ico"))
        self.window.wm_title("Save Image")

        self.barcode_1 = barcode_1
        self.barcode_2 = barcode_2

        # Label prompt for which barcode to save
        which_barcode_label = tkinter.Label(self.window, text="Barcode: ")
        which_barcode_label.grid(row=0, column=0, columnspan=1)

        # Barcode option variable
        self.barcode_option = tkinter.StringVar(self.window)
        self.barcode_option.set("Barcode 1")

        # Radio button for which barcode to save
        radio_barcode_1 = tkinter.Radiobutton(self.window, text="Barcode 1", variable=self.barcode_option,
                                              value="Barcode 1", command=self.update_size_entry)
        radio_barcode_1.grid(row=1, column=0)
        radio_barcode_1.select()

        radio_barcode_2 = tkinter.Radiobutton(self.window, text="Barcode 2", variable=self.barcode_option,
                                              value="Barcode 2", command=self.update_size_entry)
        radio_barcode_2.grid(row=2, column=0)

        # The width and height (in pixels) of the selected barcode
        width = self.barcode_1.get_barcode().shape[1]
        height = self.barcode_1.get_barcode().shape[0]

        # Native aspect of the currently selected barcode, refreshed in update_size_entry().
        # Used by _sync_height_from_width / _sync_width_from_height when "Lock aspect ratio"
        # is enabled. Guard prevents programmatic Entry updates from re-triggering each other.
        self._aspect_w_over_h = width / height
        self._suppress_aspect_sync = False

        # Resize the barcode into desirable size before saving
        self.resize_x_label = tkinter.Label(self.window, text="Saved Width (pixels): ")
        self.resize_x_label.grid(row=1, column=1, sticky=tkinter.E)

        self.resize_x_entry = tkinter.Entry(self.window, textvariable=-2, width=5)
        self.resize_x_entry.grid(row=1, column=2, padx=15, sticky=tkinter.W)
        self.resize_x_entry.insert(0, str(width))
        self.resize_x_entry.bind("<KeyRelease>", self._sync_height_from_width)

        self.resize_y_label = tkinter.Label(self.window, text="Saved Height (pixels): ")
        self.resize_y_label.grid(row=2, column=1, sticky=tkinter.E)

        self.resize_y_entry = tkinter.Entry(self.window, textvariable=-3, width=5)
        self.resize_y_entry.grid(row=2, column=2, padx=15, sticky=tkinter.W)
        self.resize_y_entry.insert(0, str(height))
        self.resize_y_entry.bind("<KeyRelease>", self._sync_width_from_height)

        # Lock-aspect checkbox. When enabled, editing W recomputes H from the captured
        # aspect ratio (and vice versa). The ratio is captured at the moment the lock is
        # toggled on, or refreshed when the user switches barcode via the radio.
        self.lock_aspect_var = tkinter.BooleanVar(value=True)
        self.lock_aspect_check = tkinter.Checkbutton(self.window, text="Lock aspect ratio",
                                                     variable=self.lock_aspect_var,
                                                     command=self._on_lock_toggle)
        self.lock_aspect_check.grid(row=3, column=1, columnspan=2, sticky=tkinter.W, padx=15)

        # Label prompt for the file name (path) of the saved image
        filename_label = tkinter.Label(self.window, text="Image file path: ")
        filename_label.grid(row=4, column=0)

        # Text entry for user to specify the path of the saved image
        self.filename_entry = tkinter.Entry(self.window, textvariable="", width=40)
        self.filename_entry.grid(row=4, column=1, columnspan=1, sticky=tkinter.W)

        # Button to browse the location in a file manager window
        self.button_browse_folder = tkinter.Button(self.window, text="Browse", command=self.browse_folder)
        self.button_browse_folder.grid(row=4, column=2, sticky=tkinter.W)

        # Button to save the image into the given path using the given size
        self.button_save_image = tkinter.Button(master=self.window, text="Save Barcode", command=self.save_image)
        self.button_save_image.grid(row=5, column=0)

    def _on_lock_toggle(self):
        """When the user just turned the lock on, capture aspect from the current entries
        so subsequent edits preserve whatever ratio they had set up (rather than snapping
        back to the barcode's native ratio)."""
        if not self.lock_aspect_var.get():
            return
        try:
            w = int(self.resize_x_entry.get())
            h = int(self.resize_y_entry.get())
        except ValueError:
            return  # invalid contents — keep the previous captured aspect
        if w > 0 and h > 0:
            self._aspect_w_over_h = w / h

    def _sync_height_from_width(self, _event=None):
        """When lock is on, recompute the height entry from the width entry's value."""
        if self._suppress_aspect_sync or not self.lock_aspect_var.get():
            return
        try:
            width = int(self.resize_x_entry.get())
        except ValueError:
            return  # mid-typing / empty / non-numeric — leave height alone
        if width <= 0:
            return
        new_height = max(1, round(width / self._aspect_w_over_h))
        self._suppress_aspect_sync = True
        try:
            self.resize_y_entry.delete(0, tkinter.END)
            self.resize_y_entry.insert(0, str(new_height))
        finally:
            self._suppress_aspect_sync = False

    def _sync_width_from_height(self, _event=None):
        """When lock is on, recompute the width entry from the height entry's value."""
        if self._suppress_aspect_sync or not self.lock_aspect_var.get():
            return
        try:
            height = int(self.resize_y_entry.get())
        except ValueError:
            return
        if height <= 0:
            return
        new_width = max(1, round(height * self._aspect_w_over_h))
        self._suppress_aspect_sync = True
        try:
            self.resize_x_entry.delete(0, tkinter.END)
            self.resize_x_entry.insert(0, str(new_width))
        finally:
            self._suppress_aspect_sync = False

    def browse_folder(self):
        """
        Browse the folders in a file manager window
        """
        # Get the file name/path from the user input in the file manager
        filename = tkinter.filedialog.asksaveasfilename(initialdir=".", title="Save Image file",
                                                    filetypes=(("JPEG files", "*.jpg"), ("PNG files", "*.png"),
                                                               ("All files", "*.*")))

        # Update the file name/path to the file name entry
        self.filename_entry.delete(0, tkinter.END)
        self.filename_entry.insert(0, filename)

    def update_size_entry(self):
        """
        Update the size of current selected barcodes displayed in the resize entries
        """
        # Find the current selected barcode
        # Update the width and height (in pixels) of that barcode in the resize entries
        if self.barcode_option.get() == "Barcode 1":
            width = self.barcode_1.get_barcode().shape[1]
            height = self.barcode_1.get_barcode().shape[0]

        elif self.barcode_option.get() == "Barcode 2":
            width = self.barcode_2.get_barcode().shape[1]
            height = self.barcode_2.get_barcode().shape[0]

        # Refresh native aspect for the newly selected barcode so the lock recomputes correctly.
        self._aspect_w_over_h = width / height

        # Suppress the KeyRelease binding while we programmatically rewrite both entries —
        # otherwise the second .insert() would re-fire on a stale partial value.
        self._suppress_aspect_sync = True
        try:
            self.resize_x_entry.delete(0, tkinter.END)
            self.resize_x_entry.insert(0, width)

            self.resize_y_entry.delete(0, tkinter.END)
            self.resize_y_entry.insert(0, height)
        finally:
            self._suppress_aspect_sync = False

    def save_image(self):
        """
        Save the currently selected barcode into the image with the given size
        """
        # Check if the filename is given
        filename = self.filename_entry.get()
        if len(filename) == 0:
            showerror("File Name is Not Given", "Please specify the path to the saved image.")
            return

        # On Linux/X11 the file dialog does not auto-append the filtered extension, and a
        # user typing the path by hand may also omit it. Default to .jpg so the call into
        # matplotlib/PIL has something to dispatch on.
        _, ext = os.path.splitext(filename)
        if ext == "":
            filename += ".jpg"

        # Get which barcode to save
        if self.barcode_option.get() == "Barcode 1":
            barcode = self.barcode_1.get_barcode().astype("uint8")
            barcode_type = self.barcode_1.barcode_type
        elif self.barcode_option.get() == "Barcode 2":
            barcode = self.barcode_2.get_barcode().astype("uint8")
            barcode_type = self.barcode_2.barcode_type

        # Resize the barcode into the desired shape (notice that the original barcode won't be affected)
        barcode = cv2.resize(barcode, dsize=(int(self.resize_x_entry.get()), int(self.resize_y_entry.get())),
                             interpolation=cv2.INTER_NEAREST)

        # Save the barcode with desirable color map based on its barcode type. Surface any
        # save error (unsupported extension, permission denied, ...) as a dialog instead of
        # letting it tear up the Tk callback.
        try:
            if barcode_type == "Color":
                plt.imsave(filename, barcode)
            else:
                plt.imsave(filename, barcode, cmap="gray")
        except (ValueError, OSError) as exc:
            showerror("Could Not Save Image", "Failed to save image to {:s}\n\n{:s}".format(filename, str(exc)))
            return

        # Quit the window
        self.window.destroy()

        showinfo("Image Saved Successfully", "The image is saved successfully.\n\n"
                                             "The Path to the Image: {:20s}".format(os.path.abspath(filename)))
