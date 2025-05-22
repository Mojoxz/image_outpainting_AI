import cv2
import numpy as np
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
import os

class ImageOutpaintingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Image Outpainting Application")
        self.root.geometry("1200x800")
        
        # Variables
        self.original_image = None
        self.processed_image = None
        self.canvas_width = 600
        self.canvas_height = 400
        
        self.setup_ui()
    
    def setup_ui(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Title
        title_label = ttk.Label(main_frame, text="Image Outpainting Tool", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # Control Panel
        control_frame = ttk.LabelFrame(main_frame, text="Controls", padding="10")
        control_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        
        # Load Image Button
        ttk.Button(control_frame, text="Load Image", 
                  command=self.load_image).grid(row=0, column=0, sticky=tk.W, pady=5)
        
        # Expansion Parameters
        ttk.Label(control_frame, text="Expansion Size:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.expansion_var = tk.IntVar(value=50)
        expansion_scale = ttk.Scale(control_frame, from_=10, to=200, 
                                  variable=self.expansion_var, orient=tk.HORIZONTAL)
        expansion_scale.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(control_frame, text="Direction:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.direction_var = tk.StringVar(value="all")
        direction_combo = ttk.Combobox(control_frame, textvariable=self.direction_var,
                                     values=["all", "left", "right", "top", "bottom"])
        direction_combo.grid(row=4, column=0, sticky=(tk.W, tk.E), pady=5)
        
        # Inpainting Method
        ttk.Label(control_frame, text="Method:").grid(row=5, column=0, sticky=tk.W, pady=5)
        self.method_var = tk.StringVar(value="telea")
        method_combo = ttk.Combobox(control_frame, textvariable=self.method_var,
                                  values=["telea", "ns"])
        method_combo.grid(row=6, column=0, sticky=(tk.W, tk.E), pady=5)
        
        # Process Button
        ttk.Button(control_frame, text="Process Outpainting", 
                  command=self.process_outpainting).grid(row=7, column=0, sticky=tk.W, pady=10)
        
        # Save Button
        ttk.Button(control_frame, text="Save Result", 
                  command=self.save_image).grid(row=8, column=0, sticky=tk.W, pady=5)
        
        # Image Display Frame
        image_frame = ttk.LabelFrame(main_frame, text="Image Preview", padding="10")
        image_frame.grid(row=1, column=1, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Original Image Canvas
        ttk.Label(image_frame, text="Original Image").grid(row=0, column=0, pady=5)
        self.original_canvas = tk.Canvas(image_frame, width=self.canvas_width//2, 
                                       height=self.canvas_height, bg="white", relief=tk.SUNKEN)
        self.original_canvas.grid(row=1, column=0, padx=5)
        
        # Processed Image Canvas
        ttk.Label(image_frame, text="Outpainted Image").grid(row=0, column=1, pady=5)
        self.processed_canvas = tk.Canvas(image_frame, width=self.canvas_width//2, 
                                        height=self.canvas_height, bg="white", relief=tk.SUNKEN)
        self.processed_canvas.grid(row=1, column=1, padx=5)
        
        # Progress Bar
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)
    
    def load_image(self):
        """Load an image file"""
        file_path = filedialog.askopenfilename(
            title="Select Image",
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp *.tiff")]
        )
        
        if file_path:
            try:
                # Load image using OpenCV
                self.original_image = cv2.imread(file_path)
                if self.original_image is None:
                    messagebox.showerror("Error", "Could not load image")
                    return
                
                # Convert BGR to RGB for display
                rgb_image = cv2.cvtColor(self.original_image, cv2.COLOR_BGR2RGB)
                
                # Display original image
                self.display_image(rgb_image, self.original_canvas)
                
                # Clear processed canvas
                self.processed_canvas.delete("all")
                self.processed_image = None
                
                messagebox.showinfo("Success", "Image loaded successfully!")
                
            except Exception as e:
                messagebox.showerror("Error", f"Error loading image: {str(e)}")
    
    def display_image(self, image, canvas):
        """Display image on canvas with proper scaling"""
        if image is None:
            return
        
        # Get canvas dimensions
        canvas_width = canvas.winfo_width() if canvas.winfo_width() > 1 else self.canvas_width//2
        canvas_height = canvas.winfo_height() if canvas.winfo_height() > 1 else self.canvas_height
        
        # Calculate scaling to fit canvas
        h, w = image.shape[:2]
        scale = min(canvas_width/w, canvas_height/h)
        
        new_width = int(w * scale)
        new_height = int(h * scale)
        
        # Resize image
        resized_image = cv2.resize(image, (new_width, new_height))
        
        # Convert to PIL Image and then to PhotoImage
        pil_image = Image.fromarray(resized_image)
        photo = ImageTk.PhotoImage(pil_image)
        
        # Clear canvas and display image
        canvas.delete("all")
        canvas.create_image(canvas_width//2, canvas_height//2, image=photo)
        
        # Keep a reference to prevent garbage collection
        canvas.image = photo
    
    def create_outpainting_mask(self, image, expansion_size, direction):
        """Create mask for outpainting based on direction and expansion size"""
        h, w = image.shape[:2]
        
        # Calculate new dimensions
        if direction == "all":
            new_h = h + 2 * expansion_size
            new_w = w + 2 * expansion_size
            offset_x, offset_y = expansion_size, expansion_size
        elif direction == "left":
            new_h = h
            new_w = w + expansion_size
            offset_x, offset_y = expansion_size, 0
        elif direction == "right":
            new_h = h
            new_w = w + expansion_size
            offset_x, offset_y = 0, 0
        elif direction == "top":
            new_h = h + expansion_size
            new_w = w
            offset_x, offset_y = 0, expansion_size
        elif direction == "bottom":
            new_h = h + expansion_size
            new_w = w
            offset_x, offset_y = 0, 0
        else:
            raise ValueError("Invalid direction")
        
        # Create expanded canvas
        expanded_image = np.zeros((new_h, new_w, 3), dtype=np.uint8)
        
        # Place original image in the expanded canvas
        expanded_image[offset_y:offset_y+h, offset_x:offset_x+w] = image
        
        # Create mask (white = area to inpaint, black = known area)
        mask = np.ones((new_h, new_w), dtype=np.uint8) * 255
        mask[offset_y:offset_y+h, offset_x:offset_x+w] = 0
        
        return expanded_image, mask
    
    def process_outpainting(self):
        """Process the outpainting operation"""
        if self.original_image is None:
            messagebox.showwarning("Warning", "Please load an image first")
            return
        
        try:
            # Start progress bar
            self.progress.start(10)
            self.root.update()
            
            # Get parameters
            expansion_size = self.expansion_var.get()
            direction = self.direction_var.get()
            method = self.method_var.get()
            
            # Create expanded image and mask
            expanded_image, mask = self.create_outpainting_mask(
                self.original_image, expansion_size, direction
            )
            
            # Apply inpainting
            if method == "telea":
                inpaint_method = cv2.INPAINT_TELEA
            else:  # ns
                inpaint_method = cv2.INPAINT_NS
            
            # Perform inpainting
            self.processed_image = cv2.inpaint(expanded_image, mask, 3, inpaint_method)
            
            # Convert BGR to RGB for display
            rgb_processed = cv2.cvtColor(self.processed_image, cv2.COLOR_BGR2RGB)
            
            # Display processed image
            self.display_image(rgb_processed, self.processed_canvas)
            
            # Stop progress bar
            self.progress.stop()
            
            messagebox.showinfo("Success", "Outpainting completed successfully!")
            
        except Exception as e:
            self.progress.stop()
            messagebox.showerror("Error", f"Error during outpainting: {str(e)}")
    
    def save_image(self):
        """Save the processed image"""
        if self.processed_image is None:
            messagebox.showwarning("Warning", "No processed image to save")
            return
        
        file_path = filedialog.asksaveasfilename(
            title="Save Outpainted Image",
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("JPEG files", "*.jpg"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                cv2.imwrite(file_path, self.processed_image)
                messagebox.showinfo("Success", f"Image saved to {file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Error saving image: {str(e)}")


def main():
    """Main function to run the application"""
    root = tk.Tk()
    app = ImageOutpaintingApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()