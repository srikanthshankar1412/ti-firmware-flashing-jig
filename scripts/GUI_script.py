#!/usr/bin/env python3
"""
CC2650 Single Flash GUI Launcher
Updated GUI for single firmware flash (combined stack + app)

Features:
- Browse and select your single flash Python script
- Execute with one click
- Real-time output display
- Progress tracking
"""
BG_COLOR = "#2c3e50"
FG_COLOR = "#ecf0f1"
BTN_COLOR = "#e74c3c"
BTN_HOVER = "#c0392b"
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import subprocess
import threading
import os
import sys
from datetime import datetime


class CC2650SingleFlashGUI:
    """GUI for CC2650 single firmware flash"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("CC2650 Single Flash GUI v1.0")
        self.root.geometry("900x700")
        self.root.resizable(True, True)
        
        # Application state
        self.flash_folder = None
        self.execution_thread = None
        self.process = None
        
        # Create GUI
        self.create_widgets()
        
        # Try to auto-detect flash folder
        self.auto_detect_flash_folder()
    
    def create_widgets(self):
        """Create all GUI widgets"""
        
        # Configure styles
        style = ttk.Style()
        style.configure("Title.TLabel", font=('Arial', 16, 'bold'))
        style.configure("Heading.TLabel", font=('Arial', 10, 'bold'))
        
        # Main container
        main_frame = ttk.Frame(self.root, padding="15")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(4, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="CC2650 Single Flash GUI", 
                               style="Title.TLabel")
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        subtitle_label = ttk.Label(main_frame, text="Flash combined CC2650 firmware (Stack + Application)")
        subtitle_label.grid(row=1, column=0, columnspan=3, pady=(0, 20))
        
        # Flash Folder Selection Frame
        folder_frame = ttk.LabelFrame(main_frame, text="UniFlash Project Folder", padding="10")
        folder_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        folder_frame.columnconfigure(1, weight=1)
        
        ttk.Label(folder_frame, text="Flash Folder:", style="Heading.TLabel").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.folder_var = tk.StringVar()
        folder_entry = ttk.Entry(folder_frame, textvariable=self.folder_var, width=70)
        folder_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
        
        ttk.Button(folder_frame, text="Browse Folder", 
                  command=self.browse_flash_folder,bg=BTN_COLOR, fg=FG_COLOR,font=('Arial', 10, 'bold'),  # Fixed: missing closing quote and added comma
          relief='raised', bd=2,
          activebackground=BTN_HOVER,
          activeforeground=FG_COLOR).grid(row=0, column=2)
        
        # Folder info
        self.folder_info_var = tk.StringVar(value="Select your UniFlash standalone project folder")
        folder_info_label = ttk.Label(folder_frame, textvariable=self.folder_info_var)
        folder_info_label.grid(row=1, column=0, columnspan=3, pady=(10, 0))
        
        # Quick Actions Frame
        actions_frame = ttk.LabelFrame(main_frame, text="Quick Actions", padding="10")
        actions_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        actions_button_frame = ttk.Frame(actions_frame)
        actions_button_frame.grid(row=0, column=0)
        
        ttk.Button(actions_button_frame, text="Open UniFlash", 
                  command=self.open_uniflash).grid(row=0, column=0, padx=(0, 10))
        
        ttk.Button(actions_button_frame, text="Detect Device", 
                  command=self.detect_device).grid(row=0, column=1, padx=(0, 10))
        
        ttk.Button(actions_button_frame, text="Test Connection", 
                  command=self.test_connection).grid(row=0, column=2)
        
        # Flash Control Frame
        control_frame = ttk.LabelFrame(main_frame, text="Flash Control", padding="10")
        control_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Control buttons
        button_frame = ttk.Frame(control_frame)
        button_frame.grid(row=0, column=0, sticky=tk.W)
        
        self.flash_button = ttk.Button(button_frame, text="Flash Firmware", 
                                     command=self.start_flash, state="disabled")
        self.flash_button.grid(row=0, column=0, padx=(0, 10))
        
        self.stop_button = ttk.Button(button_frame, text="Stop Flash", 
                                    command=self.stop_flash, state="disabled")
        self.stop_button.grid(row=0, column=1, padx=(0, 10))
        
        ttk.Button(button_frame, text="Refresh", 
                  command=self.refresh_info).grid(row=0, column=2, padx=(0, 10))
        
        # Status
        self.status_var = tk.StringVar(value="Ready - Select UniFlash project folder")
        status_label = ttk.Label(control_frame, textvariable=self.status_var)
        status_label.grid(row=1, column=0, pady=(10, 0), sticky=tk.W)
        
        # Output Frame with tabs
        output_frame = ttk.LabelFrame(main_frame, text="Flash Output", padding="10")
        output_frame.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S))
        output_frame.columnconfigure(0, weight=1)
        output_frame.rowconfigure(0, weight=1)
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(output_frame)
        self.notebook.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Real-time output tab
        output_tab = ttk.Frame(self.notebook)
        self.notebook.add(output_tab, text="Flash Output")
        
        output_tab.columnconfigure(0, weight=1)
        output_tab.rowconfigure(0, weight=1)
        
        self.output_text = scrolledtext.ScrolledText(output_tab, height=20, width=100, 
                                                   wrap=tk.WORD, font=('Consolas', 9))
        self.output_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Log tab
        log_tab = ttk.Frame(self.notebook)
        self.notebook.add(log_tab, text="Activity Log")
        
        log_tab.columnconfigure(0, weight=1)
        log_tab.rowconfigure(0, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(log_tab, height=20, width=100, 
                                                wrap=tk.WORD, font=('Consolas', 9))
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Output controls
        output_controls = ttk.Frame(output_frame)
        output_controls.grid(row=1, column=0, pady=(10, 0))
        
        ttk.Button(output_controls, text="Clear Output", 
                  command=self.clear_output).grid(row=0, column=0, padx=(0, 10))
        ttk.Button(output_controls, text="Save Output", 
                  command=self.save_output).grid(row=0, column=1, padx=(0, 10))
        ttk.Button(output_controls, text="Copy Output", 
                  command=self.copy_output).grid(row=0, column=2)
        
        # Initial messages
        self.log_message("CC2650 Single Flash GUI initialized")
        self.log_message("Select your UniFlash standalone project folder")
        
        # Add info about expected structure
        self.output_message("Expected folder structure:")
        self.output_message("your_uniflash_project/")
        self.output_message("├── dslite.bat                    ← Main flash script")
        self.output_message("├── user_files/")
        self.output_message("│   ├── configs/")
        self.output_message("│   │   └── cc2650f128.ccxml      ← Device config")
        self.output_message("│   ├── settings/")
        self.output_message("│   │   └── generated.ufsettings  ← Flash settings")
        self.output_message("│   └── images/")
        self.output_message("│       └── combined_firmware.*   ← Your firmware")
        self.output_message("└── ccs_base_app/                 ← UniFlash tools")
        self.output_message("")
        self.output_message("To create this folder:")
        self.output_message("1. Open TI UniFlash")
        self.output_message("2. Create new project for CC2650F128")
        self.output_message("3. Load your combined firmware")
        self.output_message("4. Settings → 'Create standalone package'")
        self.output_message("5. Export to a folder")
        self.output_message("\n" + "="*60 + "\n")
    
    def auto_detect_flash_folder(self):
        possible_folders = [
            "single_flash",          # Your current folder
            ".",                     # Current directory if files are here
            "cc2650_project",
            "uniflash_export"
        ]
        
        for folder_name in possible_folders:
            if os.path.exists(folder_name):
                dslite_path = os.path.join(folder_name, "dslite.bat")
                if os.path.exists(dslite_path):
                    self.flash_folder = os.path.abspath(folder_name)
                    self.folder_var.set(self.flash_folder)
                    self.folder_info_var.set(f"[OK] Auto-detected: {folder_name}")
                    self.flash_button.config(state="normal")
                    self.log_message(f"Auto-detected UniFlash project: {folder_name}")
                    return
        
        self.log_message("No UniFlash project folder auto-detected")
    
    def browse_flash_folder(self):
        """Browse for UniFlash project folder"""
        folder_path = filedialog.askdirectory(
            title="Select UniFlash Standalone Project Folder",
            initialdir=os.getcwd()
        )
        
        if folder_path:
            # Check if it contains dslite.bat
            dslite_path = os.path.join(folder_path, "dslite.bat")
            
            if os.path.exists(dslite_path):
                self.flash_folder = folder_path
                self.folder_var.set(folder_path)
                
                # Get folder info
                folder_name = os.path.basename(folder_path)
                info_text = f"[OK] Selected: {folder_name}\n"
                info_text += f"Path: {folder_path}\n"
                info_text += f"Contains: dslite.bat"
                
                self.folder_info_var.set(info_text)
                self.flash_button.config(state="normal")
                self.log_message(f"Selected UniFlash project: {folder_name}")
            else:
                messagebox.showerror("Invalid Folder", 
                    f"Selected folder does not contain dslite.bat\n\n"
                    f"Please select a UniFlash standalone project folder.")
                self.folder_info_var.set("ERROR: Not a valid UniFlash project folder")
    
    def open_uniflash(self):
        """Open TI UniFlash application"""
        try:
            # Try to find and open UniFlash
            uniflash_paths = [
                r"C:\ti\uniflash_*\uniflash.bat",
                r"C:\Program Files\Texas Instruments\UniFlash\uniflash.exe"
            ]
            
            import glob
            for pattern in uniflash_paths:
                matches = glob.glob(pattern)
                if matches:
                    subprocess.Popen([matches[0]], shell=True)
                    self.log_message("Opening TI UniFlash...")
                    return
            
            # If not found, show message
            messagebox.showinfo("UniFlash Not Found", 
                "Could not find TI UniFlash installation.\n\n"
                "Please open UniFlash manually and create a standalone project.")
            
        except Exception as e:
            self.log_message(f"Error opening UniFlash: {str(e)}")
    
    def detect_device(self):
        """Detect connected CC2650 device"""
        self.log_message("Checking for connected CC2650 device...")
        
        def detect_thread():
            try:
                # Try to run a simple detection command
                result = subprocess.run(
                    ["wmic", "path", "Win32_PnPEntity", "where", 
                     'Name like "%XDS110%" or Name like "%LaunchPad%"', 
                     "get", "Name"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if "XDS110" in result.stdout or "LaunchPad" in result.stdout:
                    self.root.after(0, lambda: self.log_message("Device detected: CC2650 LaunchPad found"))
                    self.root.after(0, lambda: messagebox.showinfo("Device Found", 
                        "CC2650 LaunchPad detected!\nReady for programming."))
                else:
                    self.root.after(0, lambda: self.log_message("No CC2650 device detected"))
                    self.root.after(0, lambda: messagebox.showwarning("No Device", 
                        "No CC2650 LaunchPad detected.\n\n"
                        "Please check:\n"
                        "• USB connection\n"
                        "• Device drivers\n"
                        "• Power LED on LaunchPad"))
                        
            except Exception as e:
                self.root.after(0, lambda: self.log_message(f"Device detection error: {str(e)}"))
        
        threading.Thread(target=detect_thread, daemon=True).start()
    
    def test_connection(self):
        """Test connection to CC2650"""
        if not self.flash_folder:
            messagebox.showwarning("Warning", "Please select UniFlash project folder first")
            return
        
        self.log_message("Testing connection to CC2650...")
        messagebox.showinfo("Test Connection", 
            "Connection test will be implemented.\n\n"
            "For now, use 'Detect Device' to check if LaunchPad is connected.")
    
    def start_flash(self):
        """Start firmware flashing"""
        if not self.flash_folder or not os.path.exists(self.flash_folder):
            messagebox.showerror("Error", "Please select a valid UniFlash project folder first")
            return
        
        if self.execution_thread and self.execution_thread.is_alive():
            messagebox.showwarning("Warning", "Flash operation is already running")
            return
        
        # Clear output
        self.clear_output()
        
        # Start flashing in thread
        self.execution_thread = threading.Thread(target=self.flash_thread)
        self.execution_thread.daemon = True
        self.execution_thread.start()
    
    def flash_thread(self):
        """Flash firmware in separate thread"""
        try:
            # Update UI
            self.root.after(0, lambda: self.flash_button.config(state="disabled"))
            self.root.after(0, lambda: self.stop_button.config(state="normal"))
            self.root.after(0, lambda: self.status_var.set("Flashing CC2650 firmware..."))
            
            folder_name = os.path.basename(self.flash_folder)
            
            self.root.after(0, lambda: self.log_message(f"Starting flash: {folder_name}"))
            self.root.after(0, lambda: self.output_message(f"Flashing CC2650 from: {folder_name}"))
            self.root.after(0, lambda: self.output_message("=" * 60))
            
            # Change to flash folder and execute dslite.bat
            original_dir = os.getcwd()
            os.chdir(self.flash_folder)
            
            self.process = subprocess.Popen(
                ["dslite.bat"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                universal_newlines=True,
                bufsize=1,
                shell=True
            )
            
            # Read output line by line
            for line in iter(self.process.stdout.readline, ''):
                if line:
                    clean_line = line.rstrip('\r\n')
                    if clean_line:
                        self.root.after(0, lambda msg=clean_line: self.output_message(msg))
                
                if self.process.poll() is not None:
                    break
            
            # Change back to original directory
            os.chdir(original_dir)
            
            # Wait for process to complete
            self.process.wait()
            return_code = self.process.returncode
            
            # Update UI with results
            if return_code == 0:
                self.root.after(0, lambda: self.status_var.set("CC2650 flash completed successfully"))
                self.root.after(0, lambda: self.log_message("CC2650 flash completed successfully"))
                self.root.after(0, lambda: self.output_message("\n" + "=" * 60))
                self.root.after(0, lambda: self.output_message("SUCCESS: CC2650 FIRMWARE FLASHED"))
                self.root.after(0, lambda: messagebox.showinfo("Success", 
                    "CC2650 firmware flashed successfully!\n\n"
                    "Your device is ready to use."))
            else:
                self.root.after(0, lambda: self.status_var.set(f"CC2650 flash failed (exit code: {return_code})"))
                self.root.after(0, lambda: self.log_message(f"CC2650 flash failed with exit code: {return_code}"))
                self.root.after(0, lambda: self.output_message("\n" + "=" * 60))
                self.root.after(0, lambda: self.output_message(f"FAILED: FLASH FAILED (Exit Code: {return_code})"))
                self.root.after(0, lambda: messagebox.showerror("Failed", 
                    f"CC2650 flash failed with exit code: {return_code}\n\n"
                    f"Check the output for details."))
            
        except Exception as e:
            error_msg = f"Flash error: {str(e)}"
            self.root.after(0, lambda: self.status_var.set("Flash error"))
            self.root.after(0, lambda: self.log_message(f"ERROR: {error_msg}"))
            self.root.after(0, lambda: self.output_message(f"\nERROR: {error_msg}"))
            self.root.after(0, lambda: messagebox.showerror("Error", error_msg))
        
        finally:
            # Reset UI
            self.root.after(0, lambda: self.flash_button.config(state="normal"))
            self.root.after(0, lambda: self.stop_button.config(state="disabled"))
            self.process = None
    
    def stop_flash(self):
        """Stop the flashing process"""
        if self.process:
            try:
                self.process.terminate()
                self.log_message("Flash operation stopped by user")
                self.output_message("\nSTOPPED: FLASH OPERATION STOPPED BY USER")
                self.status_var.set("Flash operation stopped")
            except Exception as e:
                self.log_message(f"Error stopping flash: {str(e)}")
        
        self.flash_button.config(state="normal")
        self.stop_button.config(state="disabled")
    
    def refresh_info(self):
        """Refresh information"""
        self.auto_detect_flash_folder()
        self.log_message("Information refreshed")
    
    def output_message(self, message):
        """Add message to output display"""
        self.output_text.insert(tk.END, message + "\n")
        self.output_text.see(tk.END)
        self.root.update_idletasks()
    
    def log_message(self, message):
        """Add message to log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)
    
    def clear_output(self):
        """Clear output displays"""
        self.output_text.delete(1.0, tk.END)
        self.log_text.delete(1.0, tk.END)
        self.log_message("Output cleared")
    
    def save_output(self):
        """Save output to file"""
        file_path = filedialog.asksaveasfilename(
            title="Save CC2650 Flash Output",
            defaultextension=".log",
            filetypes=[("Log files", "*.log"), ("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, 'w') as f:
                    f.write("=== CC2650 SINGLE FLASH OUTPUT ===\n")
                    f.write(self.output_text.get("1.0", tk.END))
                    f.write("\n=== ACTIVITY LOG ===\n")
                    f.write(self.log_text.get("1.0", tk.END))
                
                self.log_message(f"Output saved to: {file_path}")
                messagebox.showinfo("Saved", f"Flash output saved to:\n{file_path}")
            except Exception as e:
                self.log_message(f"Save failed: {str(e)}")
                messagebox.showerror("Save Failed", f"Failed to save output:\n{str(e)}")
    
    def copy_output(self):
        """Copy output to clipboard"""
        try:
            output_content = self.output_text.get("1.0", tk.END)
            self.root.clipboard_clear()
            self.root.clipboard_append(output_content)
            self.log_message("Output copied to clipboard")
            messagebox.showinfo("Copied", "Flash output copied to clipboard")
        except Exception as e:
            self.log_message(f"Copy failed: {str(e)}")


def main():
    """Main application entry point"""
    
    # Check dependencies
    try:
        import tkinter as tk
    except ImportError:
        print("Error: tkinter not available")
        sys.exit(1)
    
    # Create and run GUI
    root = tk.Tk()
    
    # Set application style
    try:
        root.tk.call('tk', 'scaling', 1.0)
    except:
        pass
    
    app = CC2650SingleFlashGUI(root)
    
    print("Starting CC2650 Single Flash GUI...")
    print("Create your UniFlash standalone project and select the folder")
    
    # Start the GUI
    root.mainloop()


if __name__ == "__main__":
    main()
