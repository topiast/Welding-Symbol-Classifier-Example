import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox
from PIL import Image, ImageTk
import os
import uuid

class DatasetCreator:
    def __init__(self, root):
        self.root = root
        self.root.title("Image Dataset Creator")

        self.canvas = tk.Canvas(root, cursor="cross")
        self.canvas.pack(fill="both", expand=True)

        self.btn_frame = tk.Frame(root)
        self.btn_frame.pack(fill="x")

        tk.Button(self.btn_frame, text="Open Image", command=self.open_image).pack(side="left")
        tk.Button(self.btn_frame, text="Set Bounding Box Size", command=self.set_bbox_size).pack(side="left")
        tk.Button(self.btn_frame, text="Start Create Dataset", command=self.enable_extraction).pack(side="left")
        tk.Button(self.btn_frame, text="Save Dataset", command=self.save_dataset).pack(side="left")
        tk.Button(self.btn_frame, text="Resize Dataset Images", command=self.resize_dataset_images).pack(side="left")

        self.image = None
        self.tk_img = None
        self.bbox_size = (50, 50)
        self.dataset = {}
        self.image_path = None
        self.extracting = False
        self.canvas.bind("<Motion>", self.track_mouse)
        self.canvas.bind("<Button-1>", self.extract_patch)

        self.cursor_x = 0
        self.cursor_y = 0

    def open_image(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.JPG *.JPEG *.PNG")]
        )
        if file_path:
            self.image_path = file_path
            self.image = Image.open(file_path).convert("RGB")
            self.tk_img = ImageTk.PhotoImage(self.image)
            self.canvas.create_image(0, 0, anchor="nw", image=self.tk_img)

    def set_bbox_size(self):
        w = simpledialog.askinteger("Width", "Enter bounding box width:", initialvalue=50)
        h = simpledialog.askinteger("Height", "Enter bounding box height:", initialvalue=50)
        if w and h:
            self.bbox_size = (w, h)

    def enable_extraction(self):
        if self.image:
            self.extracting = True
            messagebox.showinfo("Extraction Enabled", "Click on image to extract symbols.")
        else:
            messagebox.showwarning("No Image", "Open an image first.")

    def track_mouse(self, event):
        self.cursor_x = event.x
        self.cursor_y = event.y
        self.canvas.delete("cursor_bbox")
        x0 = event.x - self.bbox_size[0] // 2
        y0 = event.y - self.bbox_size[1] // 2
        x1 = x0 + self.bbox_size[0]
        y1 = y0 + self.bbox_size[1]
        self.canvas.create_rectangle(x0, y0, x1, y1, outline="red", tag="cursor_bbox")

    def extract_patch(self, event):
        if not self.extracting:
            return

        x0 = event.x - self.bbox_size[0] // 2
        y0 = event.y - self.bbox_size[1] // 2
        x1 = x0 + self.bbox_size[0]
        y1 = y0 + self.bbox_size[1]

        patch = self.image.crop((x0, y0, x1, y1))
        label = simpledialog.askstring("Class Label", "Enter label for this symbol:")

        if label:
            if label not in self.dataset:
                self.dataset[label] = []
            self.dataset[label].append(patch)

    def save_dataset(self):
        if not self.dataset:
            messagebox.showwarning("No Data", "No data to save.")
            return

        folder = filedialog.askdirectory(title="Select folder to save dataset")
        if not folder:
            return

        for label, images in self.dataset.items():
            class_dir = os.path.join(folder, label)
            os.makedirs(class_dir, exist_ok=True)
            for img in images:
                file_name = f"{uuid.uuid4().hex[:8]}.jpg"
                img.save(os.path.join(class_dir, file_name))

        messagebox.showinfo("Saved", "Dataset saved successfully.")
        self.dataset.clear()

    def resize_dataset_images(self):
        src_folder = filedialog.askdirectory(title="Select dataset folder")
        if not src_folder:
            return

        new_w = simpledialog.askinteger("New Width", "Enter new image width:", initialvalue=100)
        new_h = simpledialog.askinteger("New Height", "Enter new image height:", initialvalue=100)
        if not new_w or not new_h:
            return

        dst_folder = f"{src_folder}_{new_w}x{new_h}_resized"
        os.makedirs(dst_folder, exist_ok=True)

        for class_name in os.listdir(src_folder):
            class_src = os.path.join(src_folder, class_name)
            class_dst = os.path.join(dst_folder, class_name)
            if os.path.isdir(class_src):
                os.makedirs(class_dst, exist_ok=True)
                for file_name in os.listdir(class_src):
                    img_path = os.path.join(class_src, file_name)
                    try:
                        img = Image.open(img_path).convert("RGB")
                        new_img = Image.new("RGB", (new_w, new_h), (255, 255, 255))
                        offset = ((new_w - img.width) // 2, (new_h - img.height) // 2)
                        new_img.paste(img, offset)
                        new_img.save(os.path.join(class_dst, file_name))
                    except Exception as e:
                        print(f"Error processing {img_path}: {e}")

        messagebox.showinfo("Resized", f"Images resized and saved to: {dst_folder}")

if __name__ == "__main__":
    root = tk.Tk()
    app = DatasetCreator(root)
    root.mainloop()