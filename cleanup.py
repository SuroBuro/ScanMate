import tkinter as tk
from tkinter import filedialog, ttk
from PIL import Image, ImageTk
import threading
import cv2
import easyocr
import os



class OCRapp:
    def __init__(self, root):
        self.root = root
        self.root.title("TText Remover")
        self.canvas = tk.Canvas(root, width=750, height=800)
        self.canvas.pack()

        self.button_load = tk.Button(root, text="Load Image", command=self.image_loader)
        self.button_load.place(x=650, y=25)

        self.button_process = tk.Button(root, text="Read Image", command=self.ocr_detector)
        self.button_process.place(x=650,y=55)

        self.button_erase = tk.Button(root, text="Erase Image", command=self.erase_text)
        self.button_erase.place(x=650, y=85)

        self.button_save = tk.Button(root, text="Save Image", command=self.image_saver)
        self.button_save.place(x=650, y=115)

        self.progress = ttk.Progressbar(root, orient="horizontal", length=150, mode="determinate")
        self.progress.place(x=600, y=145)

        self.ocr = easyocr.Reader(['ja'], gpu=False)
        self.image = None
        self.tk_image = None
        self.rectangles = []
        self.selected_boxes = set()
        self.scale_x = 1
        self.scale_y = 1

    def image_loader(self):
        path = filedialog.askopenfilename()
        if not path:
            return
        
        self.image = cv2.imread(path)
        self.image_2_rgb = cv2.cvtColor(self.image, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(self.image_2_rgb)
        orig_w,orig_h = pil_image.size

        pil_image.thumbnail((800,800), Image.Resampling.LANCZOS)
        new_w, new_h = pil_image.size
        self.tk_image = ImageTk.PhotoImage(pil_image)
        
        self.scale_x = new_w/ orig_w
        self.scale_y = new_h/ orig_h

        self.canvas.delete('all')
        self.canvas.create_image(0,0, anchor="nw", image=self.tk_image)
       
    def ocr_detector(self):
        if self.image is None:
            return
        
        thread = threading.Thread(target=self.run_ocr)
        thread.start()


    def run_ocr(self):
        self.rectangles.clear()
        self.selected_boxes.clear()

        results = self.ocr.readtext(self.image_2_rgb)

        total = len(results)
        self.progress["maximum"] = total

        for i, (bbox, text, conf) in enumerate(results):
            top_left = bbox[0]
            bottom_right = bbox[2]

            x1,y1 = int(top_left[0] * self.scale_x), int(top_left[1] * self.scale_y)
            x2,y2 = int(bottom_right[0] * self.scale_x), int(bottom_right[1] * self.scale_y)

            self.canvas.after(0, self.draw_rectangles, x1,y1,x2,y2,i)
            
            self.selected_boxes.add(i)

            self.progress["value"] = i+1
            self.progress.update()
        
        self.progress['value'] = 0
          

    def draw_rectangles(self, x1,y1,x2,y2, i):
        rect = self.canvas.create_rectangle(
                x1,y1, x2 ,y2,
                outline='blue', width=2, tags=(f"box_{i}",)
            )

        self.rectangles.append((rect, (x1,y1,x2,y2)))
        self.canvas.tag_bind(f"box_{i}", "<Button-1>", lambda e, i=i: self.toggle_box(i))

        self.canvas.tag_bind(f"handle_{i}", "<Button-1>", lambda e , i=i: self.start_resize(e, i))
        self.canvas.tag_bind(f"handle_{i}", "<B1-Motion>", lambda e, i=i: self.perform_resize(e ,1))

    def start_resize(self, event , index):
        self.resizing_index = index
        self.resize_start_x = event.x
        self.resize_start_y = event.y 

    def perform_resize(self, event , index):
        if self.resizing_index is None:
            return
        
        _, (x1,y1, _,_), handle_id = self.rectangles[index]
        x1_new = event.x
        y1_new = event.y

        #Updating rectangle on canvas
        self.canvas.coords(self.rectangles[index][0], x1,y1, x1_new, y1_new)
        self.canvas.coords(handle_id, x1_new-5, y1_new-5, x1_new+5, y1_new+5)

        #updating rectangle data
        self.rectangles[index] = (self.rectangles[index][0], (x1,y1,x1_new,y1_new), handle_id)

    def erase_text(self):
        if self.image is None:
            return
        
        for index in self.selected_boxes:
            _, (x1_disp, y1_disp, x2_disp, y2_disp) = self.rectangles[index]

            x1 = int(x1_disp / self.scale_x)
            y1 = int(y1_disp / self.scale_y)
            x2 = int(x2_disp / self.scale_x)
            y2 = int(y2_disp / self.scale_y)

            cv2.rectangle(self.image, (x1,y1), (x2,y2), (255,255,255), thickness=-1)

        self.image_2_rgb = cv2.cvtColor(self.image, cv2.COLOR_BGR2RGB)

        pil_image = Image.fromarray(self.image_2_rgb)
        pil_image.thumbnail((800,800), Image.Resampling.LANCZOS)
        self.tk_image = ImageTk.PhotoImage(pil_image)
        self.canvas.create_image(0,0,anchor="nw", image = self.tk_image)


    def image_saver(self):
        if self.image is not None:
            path = filedialog.asksaveasfilename(defaultextension=".png")
            if path:
                cv2.imwrite(path, self.image)

    def toggle_box(self, index):
        rect_id, _ = self.rectangles[index]
        if index in self.selected_boxes:
            self.canvas.itemconfig(rect_id, outline='red')
            self.selected_boxes.remove(index)
        else:
            self.canvas.itemconfig(rect_id, outline="green")
            self.selected_boxes.add(index)

if __name__ =="__main__":
    root = tk.Tk()
    root.resizable(False, False)
    app = OCRapp(root)
    root.mainloop()