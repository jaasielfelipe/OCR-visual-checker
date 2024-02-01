import os
import csv
from tkinter import Tk, Label, Button, Canvas, Frame, messagebox, filedialog, ttk
from PIL import Image, ImageTk

class ImageNavigator:
    def __init__(self, master, image_folder):
        self.master = master
        self.master.title("Image Navigator")
        self.image_folder = image_folder
        self.image_list = [f for f in os.listdir(image_folder) if f.lower().endswith(('.jpg', '.jpeg'))]
        self.current_index = 0
        self.rotation_angle = 0  # Initial rotation angle
        self.zoom_factor = 1.0  # Initial zoom factor
        self.pan_offset = (0, 0)  # Initial pan offset

        # Create a main frame for canvas and image display
        self.main_frame = Frame(master)
        self.main_frame.pack(side="right", fill="both", expand=True)

        # Create a placeholder label
        self.label = Label(self.main_frame)
        self.label.pack()

        # Create a left sidebar
        self.left_sidebar = ttk.Frame(master, width=300, style="Left.TFrame")
        self.left_sidebar.pack_propagate(0)  # Stop frame from resizing to content
        self.left_sidebar.pack(side="left", fill="y")
        
        # Add highlighted label to the left sidebar
        self.flag_label = Label(self.left_sidebar, text="", font=("Helvetica", 26), fg="black")
        self.flag_label.pack(pady=10)        

        # Add buttons to the left sidebar
        buttons = [("Previous", self.show_previous),
                ("Next", self.show_next),
                ("Rotate Clockwise", self.rotate_clockwise),
                ("Flag OK", lambda: self.flag_image("OK")),
                ("Flag NOT OK", lambda: self.flag_image("NOT OK")),
                ("Export CSV", self.export_csv)]

        for text, command in buttons:
            button = ttk.Button(self.left_sidebar, text=text, command=command)
            button.pack(fill="x", padx=5, pady=5)

        # Create a frame for the new labels
        self.data_frame = ttk.Frame(self.left_sidebar, style="Data.TFrame")
        self.data_frame.pack(side="bottom", fill="both")

        # Create new labels for displaying data
        self.data_labels = [("Mês de referência:", ""), ("Ano de Referência:", ""), ("Alíquota:", ""), ("Base de Cálculo:", "")]
        self.data_value_labels = []

        for label_text, placeholder_text in self.data_labels:
            data_label = Label(self.data_frame, text=label_text, font=("Helvetica", 12), fg="black")
            data_label.grid(row=self.data_labels.index((label_text, placeholder_text)), column=0, sticky="e", padx=5, pady=2)

            data_value_label = Label(self.data_frame, text=placeholder_text, font=("Helvetica", 12), fg="black")
            data_value_label.grid(row=self.data_labels.index((label_text, placeholder_text)), column=1, sticky="w", padx=5, pady=2)

            self.data_value_labels.append(data_value_label)

        self.load_data_from_csv()
        self.debug_data_extraction()

        # Create the canvas
        self.canvas = Canvas(self.main_frame, bg="white")
        self.canvas.pack(fill="both", expand=False)

        # Prompt user for starting with a blank image_flags or loading from CSV
        choice = self.prompt_start_option()

        if choice == 'new':
            self.image_flags = {}  # Blank image_flags
        elif choice == 'load':
            self.image_flags = self.load_from_csv()

        self.load_image()

        # Bind key and mouse events
        master.bind("<Left>", lambda event: self.show_previous())
        master.bind("<Right>", lambda event: self.show_next())
        master.bind("o", lambda event: self.flag_image("OK"))
        master.bind("n", lambda event: self.flag_image("NOT OK"))
        master.bind("x", lambda event: self.export_csv())
        master.bind("r", lambda event: self.rotate_clockwise())
        master.bind("<MouseWheel>", self.zoom_image)
        self.canvas.bind("<B1-Motion>", self.pan_image)

        self.update_display()

    
    def load_image(self):
        if not self.image_list:
            # Handle the case where image_list is empty
            messagebox.showinfo("No Images", "No JPEG images found in the selected folder.")
            return

        image_path = os.path.join(self.image_folder, self.image_list[self.current_index])
        self.image = Image.open(image_path)
        self.tk_image = ImageTk.PhotoImage(self.image.rotate(self.rotation_angle).resize(self.get_scaled_dimensions()))

    def update_display(self):
        self.show_image()
        self.canvas.delete("all")
        self.canvas.create_image(self.pan_offset[0], self.pan_offset[1], anchor="nw", image=self.tk_image)

        # Update the flag label
        flag_status = self.get_image_flag()

        if flag_status == "NOT OK":
            self.flag_label.config(text=f" {flag_status}", fg="white", bg="red")
        elif flag_status == "OK":
            self.flag_label.config(text=f" {flag_status}", fg="white", bg="green")
        else:  # "not flagged"
            self.flag_label.config(text=f" {flag_status}", bg="grey")

    def show_image(self):
        self.label.config(text=f"Image {self.current_index + 1}/{len(self.image_list)} - Flag: {self.get_image_flag()} - Zoom: {int(self.zoom_factor * 100)}% - Pan: {self.pan_offset}")
        self.canvas.config(width=self.image.width * self.zoom_factor, height=self.image.height * self.zoom_factor)

    def show_previous(self):
        self.current_index = (self.current_index - 1) % len(self.image_list)
        self.load_image()
        self.update_display()

    def show_next(self):
        self.current_index = (self.current_index + 1) % len(self.image_list)
        self.load_image()
        self.update_display()

    def flag_image(self, flag):
        self.image_flags[self.current_index] = flag
        self.update_display()

    def get_image_flag(self):
        return self.image_flags.get(self.current_index, "Not flagged")

    def export_csv(self):
        csv_file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV Files", "*.csv")],
                                                       title="Save CSV As")
        if csv_file_path:
            with open(csv_file_path, mode='w', newline='') as csv_file:
                fieldnames = ['ImageName', 'Flag']
                writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
                writer.writeheader()

                for index, flag in self.image_flags.items():
                    writer.writerow({'ImageName': self.image_list[index], 'Flag': flag})

    def rotate_clockwise(self):
        self.rotation_angle = (self.rotation_angle - 90) % 360
        self.load_image()
        self.update_display()

    def prompt_start_option(self):
        choice = messagebox.askquestion("Start Option", "Do you want to start with a new set of image flags?")

        if choice == 'yes':
            return 'new'
        else:
            return 'load'

    def load_from_csv(self):
        image_flags = {}
        csv_file_path = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")], title="Select CSV File to Load")
        if csv_file_path:
            try:
                with open(csv_file_path, mode='r') as csv_file:
                    reader = csv.DictReader(csv_file)
                    for row in reader:
                        image_name = row['ImageName']
                        flag = row['Flag']
                        index = self.image_list.index(image_name)
                        image_flags[index] = flag
                return image_flags
            except Exception as e:
                print(f"Error loading CSV file: {e}")
        return {}

    def zoom_image(self, event):
        # Zoom in or out based on the direction of the mouse wheel
        if event.delta > 0:
            self.zoom_factor *= 1.1  # Zoom in
        else:
            self.zoom_factor /= 1.1  # Zoom out

        self.load_image()
        self.update_display()

    def pan_image(self, event):
        if hasattr(self, 'start_x') and hasattr(self, 'start_y'):
            # Pan the image based on mouse drag movement
            dx = event.x - self.start_x
            dy = event.y - self.start_y
            self.start_x, self.start_y = event.x, event.y

            self.pan_offset = (self.pan_offset[0] + dx, self.pan_offset[1] + dy)
            self.update_display()
        else:
            # Initialize start_x and start_y on the first call
            self.start_x, self.start_y = event.x, event.y

    def get_scaled_dimensions(self):
        return int(self.image.width * self.zoom_factor), int(self.image.height * self.zoom_factor)
        
    def debug_data_extraction(self):
        for label, data_value_label in zip(self.data_labels, self.data_value_labels):
            label_text, _ = label
            print(f"Label Text: {label_text}, Data Value: {data_value_label.cget('text')}")


    def load_data_from_csv(self):
        csv_file_path = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")], title="Select CSV File for Data")

        if csv_file_path:
            try:
                with open(csv_file_path, mode='r') as csv_file:
                    reader = csv.DictReader(csv_file, delimiter=';')

                    # Create a dictionary to map image names to data
                    data_mapping = {row['filename'].strip(): (row['mes_ref'], row['ano_ref'], row['alqt'], row['base_de_calculo']) for row in reader}

                    # Get data for the current image
                    current_image_name = self.image_list[self.current_index].strip()
                    data_for_current_image = data_mapping.get(current_image_name, ("", "", "", ""))

                    # Update label texts with data
                    for label, data_value_label in zip(self.data_labels, self.data_value_labels):
                        label_text, _ = label
                        index = self.data_labels.index((label_text, ""))
                        data_value_label.config(text=data_for_current_image[index])

            except Exception as e:
                print(f"Error loading CSV file for data: {e}")



            

if __name__ == "__main__":
    root = Tk()
    root.geometry("900x500")

    # Create a custom style for the left sidebar
    style = ttk.Style()
    style.configure("Left.TFrame", background="lightgray")

    # Ask the user to select a folder containing JPEG images
    image_folder = filedialog.askdirectory(title="Select Image Folder")

    if not image_folder:
        print("Please select a valid image folder.")
    else:
        app = ImageNavigator(root, image_folder)
        root.mainloop()
