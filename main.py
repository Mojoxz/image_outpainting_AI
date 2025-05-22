import cv2
import numpy as np
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk, ImageEnhance
import os
from datetime import datetime
import threading
import json

class ImageOutpaintingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Advanced Image Outpainting Application v2.0")
        self.root.geometry("1400x900")
        self.root.configure(bg='#f0f0f0')
        
        # Variables
        self.original_image = None
        self.processed_image = None
        self.canvas_width = 600
        self.canvas_height = 400
        self.processing = False
        
        # Setup project folders
        self.setup_project_folders()
        
        # Load settings
        self.load_settings()
        
        self.setup_ui()
        self.setup_shortcuts()
    
    def setup_project_folders(self):
        """Create project folder structure"""
        self.project_path = "Project_image_outpainting_app"
        self.folders = {
            'input': os.path.join(self.project_path, 'input'),
            'output': os.path.join(self.project_path, 'output'),
            'temp': os.path.join(self.project_path, 'temp'),
            'settings': os.path.join(self.project_path, 'settings')
        }
        
        # Create folders if they don't exist
        for folder_path in self.folders.values():
            os.makedirs(folder_path, exist_ok=True)
        
        print(f"Project folders created at: {os.path.abspath(self.project_path)}")
    
    def load_settings(self):
        """Load application settings"""
        settings_file = os.path.join(self.folders['settings'], 'config.json')
        self.settings = {
            'last_expansion_size': 50,
            'last_direction': 'all',
            'last_method': 'telea',
            'auto_save': True,
            'quality': 95,
            'preview_size': 300
        }
        
        if os.path.exists(settings_file):
            try:
                with open(settings_file, 'r') as f:
                    loaded_settings = json.load(f)
                    self.settings.update(loaded_settings)
            except:
                pass
    
    def save_settings(self):
        """Save current settings"""
        settings_file = os.path.join(self.folders['settings'], 'config.json')
        try:
            with open(settings_file, 'w') as f:
                json.dump(self.settings, f, indent=2)
        except:
            pass
    
    def setup_ui(self):
        # Style configuration
        style = ttk.Style()
        style.theme_use('clam')
        
        # Main frame
        main_frame = ttk.Frame(self.root, padding="15")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Title with version
        title_frame = ttk.Frame(main_frame)
        title_frame.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        title_label = ttk.Label(title_frame, text="Advanced Image Outpainting Tool v2.0", 
                               font=("Arial", 18, "bold"))
        title_label.grid(row=0, column=0)
        
        status_label = ttk.Label(title_frame, text=f"Project: {self.project_path}", 
                                font=("Arial", 10), foreground="gray")
        status_label.grid(row=1, column=0)
        
        # Left Panel - Controls
        self.setup_control_panel(main_frame)
        
        # Center Panel - Image Display  
        self.setup_image_panel(main_frame)
        
        # Right Panel - Advanced Options
        self.setup_advanced_panel(main_frame)
        
        # Bottom Panel - Progress and Info
        self.setup_bottom_panel(main_frame)
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=2)
        main_frame.rowconfigure(1, weight=1)
    
    def setup_control_panel(self, parent):
        """Setup main control panel"""
        control_frame = ttk.LabelFrame(parent, text="Main Controls", padding="15")
        control_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        
        # File Operations
        file_frame = ttk.LabelFrame(control_frame, text="File Operations", padding="10")
        file_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(file_frame, text="📁 Load Image", 
                  command=self.load_image, width=20).pack(pady=2)
        ttk.Button(file_frame, text="💾 Save Result", 
                  command=self.save_image, width=20).pack(pady=2)
        ttk.Button(file_frame, text="📂 Open Output Folder", 
                  command=self.open_output_folder, width=20).pack(pady=2)
        
        # Quick Actions
        quick_frame = ttk.LabelFrame(control_frame, text="Quick Actions", padding="10")
        quick_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(quick_frame, text="🔄 Process", 
                  command=self.process_outpainting_threaded, width=20).pack(pady=2)
        ttk.Button(quick_frame, text="🔍 Preview", 
                  command=self.quick_preview, width=20).pack(pady=2)
        ttk.Button(quick_frame, text="↩️ Reset", 
                  command=self.reset_image, width=20).pack(pady=2)
        
        # Parameters
        param_frame = ttk.LabelFrame(control_frame, text="Parameters", padding="10")
        param_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Expansion Size
        ttk.Label(param_frame, text="Expansion Size:").pack(anchor=tk.W)
        self.expansion_var = tk.IntVar(value=self.settings['last_expansion_size'])
        expansion_frame = ttk.Frame(param_frame)
        expansion_frame.pack(fill=tk.X, pady=2)
        
        expansion_scale = ttk.Scale(expansion_frame, from_=10, to=300, 
                                  variable=self.expansion_var, orient=tk.HORIZONTAL)
        expansion_scale.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.expansion_label = ttk.Label(expansion_frame, text=str(self.expansion_var.get()))
        self.expansion_label.pack(side=tk.RIGHT, padx=(5, 0))
        expansion_scale.configure(command=self.update_expansion_label)
        
        # Direction
        ttk.Label(param_frame, text="Direction:").pack(anchor=tk.W, pady=(10, 0))
        self.direction_var = tk.StringVar(value=self.settings['last_direction'])
        direction_combo = ttk.Combobox(param_frame, textvariable=self.direction_var,
                                     values=["all", "left", "right", "top", "bottom", "horizontal", "vertical"],
                                     state="readonly")
        direction_combo.pack(fill=tk.X, pady=2)
        
        # Method
        ttk.Label(param_frame, text="Inpainting Method:").pack(anchor=tk.W, pady=(10, 0))
        self.method_var = tk.StringVar(value=self.settings['last_method'])
        method_combo = ttk.Combobox(param_frame, textvariable=self.method_var,
                                  values=["telea", "ns"], state="readonly")
        method_combo.pack(fill=tk.X, pady=2)
        
        # Auto-save checkbox
        self.auto_save_var = tk.BooleanVar(value=self.settings['auto_save'])
        ttk.Checkbutton(param_frame, text="Auto-save results", 
                       variable=self.auto_save_var).pack(anchor=tk.W, pady=(10, 0))
    
    def setup_image_panel(self, parent):
        """Setup image display panel"""
        image_frame = ttk.LabelFrame(parent, text="Image Preview", padding="15")
        image_frame.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5)
        
        # Image containers
        images_container = ttk.Frame(image_frame)
        images_container.pack(fill=tk.BOTH, expand=True)
        
        # Original Image
        original_frame = ttk.LabelFrame(images_container, text="Original Image", padding="10")
        original_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        self.original_canvas = tk.Canvas(original_frame, bg="white", relief=tk.SUNKEN, bd=2)
        self.original_canvas.pack(fill=tk.BOTH, expand=True)
        
        # Result Image
        result_frame = ttk.LabelFrame(images_container, text="Outpainted Result", padding="10")
        result_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        self.processed_canvas = tk.Canvas(result_frame, bg="white", relief=tk.SUNKEN, bd=2)
        self.processed_canvas.pack(fill=tk.BOTH, expand=True)
        
        # Image info
        self.info_label = ttk.Label(image_frame, text="No image loaded", font=("Arial", 10))
        self.info_label.pack(pady=(10, 0))
    
    def setup_advanced_panel(self, parent):
        """Setup advanced options panel"""
        advanced_frame = ttk.LabelFrame(parent, text="Advanced Options", padding="15")
        advanced_frame.grid(row=1, column=2, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(10, 0))
        
        # Quality Settings
        quality_frame = ttk.LabelFrame(advanced_frame, text="Quality Settings", padding="10")
        quality_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(quality_frame, text="Output Quality:").pack(anchor=tk.W)
        self.quality_var = tk.IntVar(value=self.settings['quality'])
        quality_scale = ttk.Scale(quality_frame, from_=50, to=100, 
                                variable=self.quality_var, orient=tk.HORIZONTAL)
        quality_scale.pack(fill=tk.X, pady=2)
        
        # Batch Processing
        batch_frame = ttk.LabelFrame(advanced_frame, text="Batch Processing", padding="10")
        batch_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(batch_frame, text="Process Folder", 
                  command=self.batch_process, width=20).pack(pady=2)
        ttk.Button(batch_frame, text="Process Multiple", 
                  command=self.process_multiple, width=20).pack(pady=2)
        
        # Enhancement Options
        enhance_frame = ttk.LabelFrame(advanced_frame, text="Enhancement", padding="10")
        enhance_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.enhance_contrast = tk.BooleanVar()
        ttk.Checkbutton(enhance_frame, text="Enhance Contrast", 
                       variable=self.enhance_contrast).pack(anchor=tk.W)
        
        self.enhance_sharpness = tk.BooleanVar()
        ttk.Checkbutton(enhance_frame, text="Enhance Sharpness", 
                       variable=self.enhance_sharpness).pack(anchor=tk.W)
        
        # History
        history_frame = ttk.LabelFrame(advanced_frame, text="Recent Files", padding="10")
        history_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.history_listbox = tk.Listbox(history_frame, height=5, font=("Arial", 9))
        self.history_listbox.pack(fill=tk.X)
        self.history_listbox.bind('<Double-1>', self.load_from_history)
        
        # Update history
        self.update_history()
    
    def setup_bottom_panel(self, parent):
        """Setup bottom panel with progress and info"""
        bottom_frame = ttk.Frame(parent)
        bottom_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(15, 0))
        
        # Progress bar
        self.progress = ttk.Progressbar(bottom_frame, mode='indeterminate')
        self.progress.pack(fill=tk.X, pady=(0, 5))
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        self.status_label = ttk.Label(bottom_frame, textvariable=self.status_var, 
                                     font=("Arial", 10), relief=tk.SUNKEN, padding="5")
        self.status_label.pack(fill=tk.X)
    
    def setup_shortcuts(self):
        """Setup keyboard shortcuts"""
        self.root.bind('<Control-o>', lambda e: self.load_image())
        self.root.bind('<Control-s>', lambda e: self.save_image())
        self.root.bind('<Control-p>', lambda e: self.process_outpainting_threaded())
        self.root.bind('<F5>', lambda e: self.quick_preview())
        self.root.bind('<Escape>', lambda e: self.reset_image())
    
    def update_expansion_label(self, value):
        """Update expansion size label"""
        self.expansion_label.config(text=str(int(float(value))))
    
    def update_status(self, message):
        """Update status bar"""
        self.status_var.set(message)
        self.root.update_idletasks()
    
    def load_image(self):
        """Load an image file with enhanced features"""
        file_path = filedialog.askopenfilename(
            title="Select Image",
            initialdir=self.folders['input'],
            filetypes=[
                ("All Images", "*.jpg *.jpeg *.png *.bmp *.tiff *.webp"),
                ("JPEG files", "*.jpg *.jpeg"),
                ("PNG files", "*.png"),
                ("All files", "*.*")
            ]
        )
        
        if file_path:
            try:
                self.update_status("Loading image...")
                
                # Load image using OpenCV
                self.original_image = cv2.imread(file_path)
                if self.original_image is None:
                    messagebox.showerror("Error", "Could not load image")
                    return
                
                # Store original path
                self.original_path = file_path
                
                # Convert BGR to RGB for display
                rgb_image = cv2.cvtColor(self.original_image, cv2.COLOR_BGR2RGB)
                
                # Display original image
                self.display_image(rgb_image, self.original_canvas)
                
                # Update image info
                h, w, c = self.original_image.shape
                file_size = os.path.getsize(file_path) / 1024  # KB
                self.info_label.config(text=f"Size: {w}x{h} | Channels: {c} | File: {file_size:.1f} KB")
                
                # Clear processed canvas
                self.processed_canvas.delete("all")
                self.processed_image = None
                
                # Add to history
                self.add_to_history(file_path)
                
                self.update_status("Image loaded successfully")
                messagebox.showinfo("Success", "Image loaded successfully!")
                
            except Exception as e:
                self.update_status("Error loading image")
                messagebox.showerror("Error", f"Error loading image: {str(e)}")
    
    def display_image(self, image, canvas):
        """Enhanced image display with better scaling"""
        if image is None:
            return
        
        # Get canvas dimensions
        canvas.update_idletasks()
        canvas_width = canvas.winfo_width() if canvas.winfo_width() > 1 else 300
        canvas_height = canvas.winfo_height() if canvas.winfo_height() > 1 else 200
        
        # Calculate scaling to fit canvas with margin
        h, w = image.shape[:2]
        margin = 20
        scale = min((canvas_width - margin)/w, (canvas_height - margin)/h)
        
        new_width = int(w * scale)
        new_height = int(h * scale)
        
        # Resize image
        resized_image = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)
        
        # Convert to PIL Image and then to PhotoImage
        pil_image = Image.fromarray(resized_image)
        photo = ImageTk.PhotoImage(pil_image)
        
        # Clear canvas and display image
        canvas.delete("all")
        canvas.create_image(canvas_width//2, canvas_height//2, image=photo)
        
        # Keep a reference to prevent garbage collection
        canvas.image = photo
    
    def create_outpainting_mask(self, image, expansion_size, direction):
        """Enhanced mask creation with new direction options"""
        h, w = image.shape[:2]
        
        # Calculate new dimensions based on direction
        if direction == "all":
            new_h = h + 2 * expansion_size
            new_w = w + 2 * expansion_size
            offset_x, offset_y = expansion_size, expansion_size
        elif direction == "horizontal":
            new_h = h
            new_w = w + 2 * expansion_size
            offset_x, offset_y = expansion_size, 0
        elif direction == "vertical":
            new_h = h + 2 * expansion_size
            new_w = w
            offset_x, offset_y = 0, expansion_size
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
        
        # Create expanded canvas
        expanded_image = np.zeros((new_h, new_w, 3), dtype=np.uint8)
        
        # Place original image in the expanded canvas
        expanded_image[offset_y:offset_y+h, offset_x:offset_x+w] = image
        
        # Create mask (white = area to inpaint, black = known area)
        mask = np.ones((new_h, new_w), dtype=np.uint8) * 255
        mask[offset_y:offset_y+h, offset_x:offset_x+w] = 0
        
        return expanded_image, mask
    
    def enhance_image(self, image):
        """Apply image enhancements"""
        if not self.enhance_contrast.get() and not self.enhance_sharpness.get():
            return image
        
        # Convert to PIL for enhancement
        pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        
        if self.enhance_contrast.get():
            enhancer = ImageEnhance.Contrast(pil_image)
            pil_image = enhancer.enhance(1.2)
        
        if self.enhance_sharpness.get():
            enhancer = ImageEnhance.Sharpness(pil_image)
            pil_image = enhancer.enhance(1.1)
        
        # Convert back to OpenCV format
        return cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
    
    def process_outpainting_threaded(self):
        """Process outpainting in a separate thread"""
        if self.processing:
            messagebox.showwarning("Warning", "Processing already in progress")
            return
        
        if self.original_image is None:
            messagebox.showwarning("Warning", "Please load an image first")
            return
        
        # Start processing in thread
        self.processing = True
        self.progress.start(10)
        self.update_status("Processing outpainting...")
        
        thread = threading.Thread(target=self.process_outpainting)
        thread.daemon = True
        thread.start()
    
    def process_outpainting(self):
        """Enhanced outpainting process"""
        try:
            # Get parameters
            expansion_size = self.expansion_var.get()
            direction = self.direction_var.get()
            method = self.method_var.get()
            
            # Create expanded image and mask
            expanded_image, mask = self.create_outpainting_mask(
                self.original_image, expansion_size, direction
            )
            
            # Apply inpainting
            inpaint_method = cv2.INPAINT_TELEA if method == "telea" else cv2.INPAINT_NS
            
            # Perform inpainting with enhanced radius
            inpaint_radius = max(3, expansion_size // 10)
            self.processed_image = cv2.inpaint(expanded_image, mask, inpaint_radius, inpaint_method)
            
            # Apply enhancements
            self.processed_image = self.enhance_image(self.processed_image)
            
            # Display result on main thread
            self.root.after(0, self.display_result)
            
        except Exception as e:
            self.root.after(0, lambda: self.handle_processing_error(str(e)))
    
    def display_result(self):
        """Display processing result"""
        try:
            # Convert BGR to RGB for display
            rgb_processed = cv2.cvtColor(self.processed_image, cv2.COLOR_BGR2RGB)
            
            # Display processed image
            self.display_image(rgb_processed, self.processed_canvas)
            
            # Stop progress bar
            self.progress.stop()
            self.processing = False
            
            # Auto-save if enabled
            if self.auto_save_var.get():
                self.auto_save_result()
            
            # Save current settings
            self.settings.update({
                'last_expansion_size': self.expansion_var.get(),
                'last_direction': self.direction_var.get(),
                'last_method': self.method_var.get(),
                'auto_save': self.auto_save_var.get(),
                'quality': self.quality_var.get()
            })
            self.save_settings()
            
            self.update_status("Outpainting completed successfully")
            messagebox.showinfo("Success", "Outpainting completed successfully!")
            
        except Exception as e:
            self.handle_processing_error(str(e))
    
    def handle_processing_error(self, error_msg):
        """Handle processing errors"""
        self.progress.stop()
        self.processing = False
        self.update_status("Error during processing")
        messagebox.showerror("Error", f"Error during outpainting: {error_msg}")
    
    def auto_save_result(self):
        """Automatically save result to output folder"""
        if self.processed_image is None:
            return
        
        try:
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            original_name = os.path.splitext(os.path.basename(self.original_path))[0]
            filename = f"{original_name}_outpainted_{timestamp}.png"
            filepath = os.path.join(self.folders['output'], filename)
            
            # Save with specified quality
            if filepath.lower().endswith('.jpg') or filepath.lower().endswith('.jpeg'):
                cv2.imwrite(filepath, self.processed_image, [cv2.IMWRITE_JPEG_QUALITY, self.quality_var.get()])
            else:
                cv2.imwrite(filepath, self.processed_image)
            
            self.update_status(f"Auto-saved: {filename}")
            
        except Exception as e:
            print(f"Auto-save error: {e}")
    
    def save_image(self):
        """Enhanced save functionality"""
        if self.processed_image is None:
            messagebox.showwarning("Warning", "No processed image to save")
            return
        
        # Generate default filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_name = f"outpainted_{timestamp}.png"
        
        file_path = filedialog.asksaveasfilename(
            title="Save Outpainted Image",
            initialdir=self.folders['output'],
            initialfile=default_name,
            filetypes=[
                ("PNG files", "*.png"),
                ("JPEG files", "*.jpg"),
                ("All files", "*.*")
            ]
        )
        
        if file_path:
            try:
                # Save with quality settings
                if file_path.lower().endswith('.jpg') or file_path.lower().endswith('.jpeg'):
                    cv2.imwrite(file_path, self.processed_image, [cv2.IMWRITE_JPEG_QUALITY, self.quality_var.get()])
                else:
                    cv2.imwrite(file_path, self.processed_image)
                
                self.update_status(f"Saved: {os.path.basename(file_path)}")
                messagebox.showinfo("Success", f"Image saved to {file_path}")
                
            except Exception as e:
                messagebox.showerror("Error", f"Error saving image: {str(e)}")
    
    def quick_preview(self):
        """Quick preview with lower quality for speed"""
        if self.original_image is None:
            messagebox.showwarning("Warning", "Please load an image first")
            return
        
        try:
            # Create smaller version for quick preview
            small_image = cv2.resize(self.original_image, (200, 150))
            expansion = max(10, self.expansion_var.get() // 4)
            
            expanded_image, mask = self.create_outpainting_mask(small_image, expansion, self.direction_var.get())
            method = cv2.INPAINT_TELEA if self.method_var.get() == "telea" else cv2.INPAINT_NS
            
            preview_result = cv2.inpaint(expanded_image, mask, 2, method)
            rgb_preview = cv2.cvtColor(preview_result, cv2.COLOR_BGR2RGB)
            
            self.display_image(rgb_preview, self.processed_canvas)
            self.update_status("Quick preview generated")
            
        except Exception as e:
            messagebox.showerror("Error", f"Preview error: {str(e)}")
    
    def reset_image(self):
        """Reset to original image"""
        if self.original_image is not None:
            self.processed_canvas.delete("all")
            self.processed_image = None
            self.update_status("Reset to original")
    
    def open_output_folder(self):
        """Open output folder in file explorer"""
        try:
            if os.name == 'nt':  # Windows
                os.startfile(self.folders['output'])
            elif os.name == 'posix':  # macOS and Linux
                output_path = self.folders['output']
                if os.uname().sysname == 'Darwin':
                    os.system(f'open "{output_path}"')
                else:
                    os.system(f'xdg-open "{output_path}"')
            self.update_status("Output folder opened")
        except Exception as e:
            messagebox.showerror("Error", f"Could not open folder: {str(e)}")
    
    def add_to_history(self, filepath):
        """Add file to recent history"""
        history_file = os.path.join(self.folders['settings'], 'history.txt')
        try:
            # Read existing history
            history = []
            if os.path.exists(history_file):
                with open(history_file, 'r') as f:
                    history = [line.strip() for line in f.readlines()]
            
            # Add new file to top, remove if already exists
            if filepath in history:
                history.remove(filepath)
            history.insert(0, filepath)
            
            # Keep only last 10 files
            history = history[:10]
            
            # Write back
            with open(history_file, 'w') as f:
                f.write('\n'.join(history))
            
            self.update_history()
            
        except Exception as e:
            print(f"History error: {e}")
    
    def update_history(self):
        """Update history listbox"""
        try:
            history_file = os.path.join(self.folders['settings'], 'history.txt')
            self.history_listbox.delete(0, tk.END)
            
            if os.path.exists(history_file):
                with open(history_file, 'r') as f:
                    for line in f:
                        filepath = line.strip()
                        if os.path.exists(filepath):
                            filename = os.path.basename(filepath)
                            self.history_listbox.insert(tk.END, filename)
        except:
            pass
    
    def load_from_history(self, event):
        """Load image from history"""
        try:
            selection = self.history_listbox.curselection()
            if selection:
                index = selection[0]
                history_file = os.path.join(self.folders['settings'], 'history.txt')
                
                with open(history_file, 'r') as f:
                    lines = f.readlines()
                    if index < len(lines):
                        filepath = lines[index].strip()
                        if os.path.exists(filepath):
                            self.original_path = filepath
                            self.original_image = cv2.imread(filepath)
                            if self.original_image is not None:
                                rgb_image = cv2.cvtColor(self.original_image, cv2.COLOR_BGR2RGB)
                                self.display_image(rgb_image, self.original_canvas)
                                
                                # Update image info
                                h, w, c = self.original_image.shape
                                file_size = os.path.getsize(filepath) / 1024
                                self.info_label.config(text=f"Size: {w}x{h} | Channels: {c} | File: {file_size:.1f} KB")
                                self.update_status("Image loaded from history")
        except Exception as e:
            print(f"Load from history error: {e}")
    
    def batch_process(self):
        """Process all images in a folder"""
        folder_path = filedialog.askdirectory(
            title="Select folder with images",
            initialdir=self.folders['input']
        )
        
        if not folder_path:
            return
        
        try:
            # Get all image files
            image_extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.tiff')
            image_files = [f for f in os.listdir(folder_path) 
                          if f.lower().endswith(image_extensions)]
            
            if not image_files:
                messagebox.showwarning("Warning", "No image files found in selected folder")
                return
            
            # Confirm batch processing
            result = messagebox.askyesno("Batch Processing", 
                                       f"Found {len(image_files)} images. Continue with batch processing?")
            if not result:
                return
            
            # Process each image
            processed_count = 0
            for i, filename in enumerate(image_files):
                try:
                    filepath = os.path.join(folder_path, filename)
                    self.update_status(f"Processing {i+1}/{len(image_files)}: {filename}")
                    
                    # Load image
                    image = cv2.imread(filepath)
                    if image is None:
                        continue
                    
                    # Process outpainting
                    expanded_image, mask = self.create_outpainting_mask(
                        image, self.expansion_var.get(), self.direction_var.get()
                    )
                    
                    method = cv2.INPAINT_TELEA if self.method_var.get() == "telea" else cv2.INPAINT_NS
                    inpaint_radius = max(3, self.expansion_var.get() // 10)
                    result_image = cv2.inpaint(expanded_image, mask, inpaint_radius, method)
                    
                    # Apply enhancements
                    result_image = self.enhance_image(result_image)
                    
                    # Save result
                    name_without_ext = os.path.splitext(filename)[0]
                    output_filename = f"{name_without_ext}_batch_outpainted.png"
                    output_path = os.path.join(self.folders['output'], output_filename)
                    
                    cv2.imwrite(output_path, result_image)
                    processed_count += 1
                    
                except Exception as e:
                    print(f"Error processing {filename}: {e}")
                    continue
            
            self.update_status(f"Batch processing completed: {processed_count} images")
            messagebox.showinfo("Batch Complete", 
                              f"Successfully processed {processed_count} out of {len(image_files)} images")
            
        except Exception as e:
            messagebox.showerror("Error", f"Batch processing error: {str(e)}")
    
    def process_multiple(self):
        """Process multiple selected images"""
        file_paths = filedialog.askopenfilenames(
            title="Select multiple images",
            initialdir=self.folders['input'],
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp *.tiff")]
        )
        
        if not file_paths:
            return
        
        try:
            processed_count = 0
            for i, filepath in enumerate(file_paths):
                try:
                    filename = os.path.basename(filepath)
                    self.update_status(f"Processing {i+1}/{len(file_paths)}: {filename}")
                    
                    # Load and process image
                    image = cv2.imread(filepath)
                    if image is None:
                        continue
                    
                    expanded_image, mask = self.create_outpainting_mask(
                        image, self.expansion_var.get(), self.direction_var.get()
                    )
                    
                    method = cv2.INPAINT_TELEA if self.method_var.get() == "telea" else cv2.INPAINT_NS
                    inpaint_radius = max(3, self.expansion_var.get() // 10)
                    result_image = cv2.inpaint(expanded_image, mask, inpaint_radius, method)
                    
                    # Apply enhancements
                    result_image = self.enhance_image(result_image)
                    
                    # Save result
                    name_without_ext = os.path.splitext(filename)[0]
                    timestamp = datetime.now().strftime("%H%M%S")
                    output_filename = f"{name_without_ext}_multi_{timestamp}.png"
                    output_path = os.path.join(self.folders['output'], output_filename)
                    
                    cv2.imwrite(output_path, result_image)
                    processed_count += 1
                    
                except Exception as e:
                    print(f"Error processing {filepath}: {e}")
                    continue
            
            self.update_status(f"Multiple processing completed: {processed_count} images")
            messagebox.showinfo("Processing Complete", 
                              f"Successfully processed {processed_count} out of {len(file_paths)} images")
            
        except Exception as e:
            messagebox.showerror("Error", f"Multiple processing error: {str(e)}")
    
    def on_closing(self):
        """Handle application closing"""
        # Save settings
        self.save_settings()
        
        # Stop any ongoing processing
        if self.processing:
            self.processing = False
            self.progress.stop()
        
        self.root.destroy()


def main():
    """Main function to run the application"""
    root = tk.Tk()
    app = ImageOutpaintingApp(root)
    
    # Handle window closing
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    
    # Center window on screen
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'{width}x{height}+{x}+{y}')
    
    root.mainloop()


if __name__ == "__main__":
    main()