import sys
import os
import time
import json
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import win32print
import win32api
import subprocess
import shutil
import ctypes

# try:
#     import requests
#     REQUESTS_AVAILABLE = True
# except ImportError:
#     REQUESTS_AVAILABLE = False

# Windows API Duplex Constants
DMDUP_SIMPLEX = 1 # Single-sided printing
DMDUP_VERTICAL = 2 # Double-sided printing (flip on long edge)
DMDUP_HORIZONTAL = 3 # Double-sided printing (flip on short edge)

# Save in same directory as the script or EXE, on the user's desktop
CONFIG_FILE_PATH = os.path.join(os.path.expanduser("~"), "Desktop", "PrintMultiWatchConfig.json")

class WatchedMultiPrintApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Watched Multi-Printer Router")
        # self.root.geometry("500x600")

        self.is_listening = False

        # Tab container setup
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill="both", expand=True, padx=5, pady=5)

        # Tab 1: Main Controls
        self.main_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.main_tab, text=" Main / Settings ")

        # Tab 2: Activity Log
        self.log_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.log_tab, text=" Activity Log ")

        # Fetch available printers from Windows OS
        printer_info = win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS)
        # Store only the printer names for display and selection
        self.system_printers = [p[2] for p in printer_info]

        # UI Layout Setup
        tk.Label(self.main_tab, text="Select Output Target Printers:", font=("Arial", 10, "bold")).pack(pady=(10, 5))

        # Printer Selection Checkboxes

        # set up a scrollable frame for the printer checkboxes
        container = tk.Frame(self.main_tab)
        container.pack(fill="both", expand=True, padx=20, pady=(0, 10))
        canvas = tk.Canvas(container, height=200)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        self.scrollable_frame = tk.Frame(canvas)

        self.scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        container.pack(fill="both", expand=True, padx=20)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.printer_vars = {}
        for printer in self.system_printers:
            var = tk.BooleanVar()
            self.printer_vars[printer] = var
            cb = tk.Checkbutton(self.scrollable_frame, text=printer, variable=var, anchor="w")
            cb.pack(fill="x", anchor="w", padx=5, pady=2)

        # Print Settings Area (Duplex, Collate, Copies)
        settings_frame = tk.LabelFrame(self.main_tab, text="Print Settings", padx=10, pady=10)
        settings_frame.pack(fill="x", padx=20, pady=(5, 10))

        # Copies SpinBox
        tk.Label(settings_frame, text="Number of Copies:").grid(row=0, column=0, sticky="w", padx=5)
        self.copies_var = tk.IntVar(value=1)
        copies_spinbox = tk.Spinbox(settings_frame, from_=1, to=100, textvariable=self.copies_var, width=5)
        copies_spinbox.grid(row=0, column=1, sticky="w", padx=5)

        # Double-Sided Checkbox
        self.duplex_var = tk.BooleanVar(value=False)
        duplex_cb = tk.Checkbutton(settings_frame, text="Double-Sided Printing", variable=self.duplex_var)
        duplex_cb.grid(row=1, column=0, columnspan=2, sticky="w", padx=5, pady=(5, 0))

        # # DocuWare API Settings Area (Saved Persistently)
        # dw_frame = tk.LabelFrame(root, text="DocuWare API Credentials (Automatically Saved)", font=("Arial", 9, "bold"), padx=10, pady=5)
        # dw_frame.pack(fill="x", padx=20, pady=5)

        # tk.Label(dw_frame, text="Server URL:").grid(row=0, column=0, sticky="w", padx=2)
        # self.dw_url_var = tk.StringVar(value="https://your-docuware-server/DocuWare/Platform")
        # tk.Entry(dw_frame, textvariable=self.dw_url_var, width=38).grid(row=0, column=1, padx=5, pady=2)

        # tk.Label(dw_frame, text="Username:").grid(row=1, column=0, sticky="w", padx=2)
        # self.dw_user_var = tk.StringVar()
        # tk.Entry(dw_frame, textvariable=self.dw_user_var, width=38).grid(row=1, column=1, padx=5, pady=2)

        # tk.Label(dw_frame, text="Password:").grid(row=2, column=0, sticky="w", padx=2)
        # self.dw_pass_var = tk.StringVar()
        # tk.Entry(dw_frame, textvariable=self.dw_pass_var, show="*", width=38).grid(row=2, column=1, padx=5, pady=2)

        # tk.Label(dw_frame, text="Tray (Basket) ID:").grid(row=3, column=0, sticky="w", padx=2)
        # self.dw_tray_var = tk.StringVar()
        # tk.Entry(dw_frame, textvariable=self.dw_tray_var, width=38).grid(row=3, column=1, padx=5, pady=2)

        # Docuware Watch folder
        tk.Label(self.main_tab, text="Folder for Docuware Import", font=("Arial", 10, "bold")).pack(pady=(10,5))
        dir_frame = tk.Frame(self.main_tab)
        dir_frame.pack(fill="x", padx=20)

        default_docuware_folder = os.path.join(os.path.expanduser("~"), "Desktop", "DocuWareImport")
        self.watch_dwfolder_path = tk.StringVar(value=default_docuware_folder)

        tk.Entry(dir_frame, textvariable=self.watch_dwfolder_path, width=35).pack(side="left", padx=5)
        tk.Button(dir_frame, text="Browse...", command=self.browse_dw_folder).pack(side="left")

        # Default folder on desktop
        tk.Label(self.main_tab, text="Folder to Watch for Print Jobs:", font=("Arial", 10, "bold")).pack(pady=(10, 5))
        dir_frame = tk.Frame(self.main_tab)
        dir_frame.pack(fill="x", padx=20)


        default_folder = os.path.join(os.path.expanduser("~"), "Desktop", "PrintMultiWatchJobs")
        self.watch_path = tk.StringVar(value=default_folder)

        tk.Entry(dir_frame, textvariable=self.watch_path, width=35).pack(side="left", padx=5)
        tk.Button(dir_frame, text="Browse...", command=self.browse_folder).pack(side="left")

        # Mode Selection
        tk.Label(self.main_tab, text="Mode Selector", font=("Arial", 10, "bold")).pack(pady=(10,5))
        dir_frame = tk.Frame(self.main_tab)
        dir_frame.pack(fill="x", padx=20)
        self.listen_mode = tk.StringVar(value="continuous") # "continuous" or "once"

        mode_frame = tk.Frame(self.main_tab)
        mode_frame.pack(pady=5)

        tk.Radiobutton(mode_frame, text="Continuous Mode", variable=self.listen_mode, value="continuous").pack(side="left", padx=10)
        tk.Radiobutton(mode_frame, text="Single Job (Listen Once)", variable=self.listen_mode, value="once").pack(side="left", padx=10)

        # Display Status Message
        self.status_var = tk.StringVar(value="Status: Idle (Not Listenting)")
        self.status_label = tk.Label(self.main_tab, textvariable=self.status_var, font=("Arial", 10, "italic"), fg="blue")
        self.status_label.pack(pady=(10, 5))

        # Action button to start/stop listening
        self.listen_btn = tk.Button(self.main_tab, text="START LISTENING", bg="green", fg="white", font=("Arial", 11, "bold"), command=self.toggle_listening)
        self.listen_btn.pack(pady=10)

        self.load_config()  # Load saved DocuWare API settings if available

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)  # Handle window close event

    def load_config(self):
        # Loads saved settings from JSON file if present.
        if os.path.exists(CONFIG_FILE_PATH):
            try:
                with open(CONFIG_FILE_PATH, "r") as f:
                    data = json.load(f)

                    # Restore folder paths
                    if "watch_path" in data and data["watch_path"]:
                        self.watch_path.set(data["watch_path"])
                    if "watch_dwfolder_path" in data and data["watch_dwfolder_path"]:
                        self.watch_dwfolder_path.set(data["watch_dwfolder_path"])

                    # Restore print settings
                    if "copies" in data:
                        self.copies_var.set(data["copies"])
                    if "duplex" in data:
                        self.duplex_var.set(data["duplex"])
                    if "listen_mode" in data and data["listen_mode"]:
                        self.listen_mode.set(data["listen_mode"])

                    # Restore checkbox selections for pritners
                    saved_printers = data.get("selected_printers", [])
                    for printer_name, var in self.printer_vars.items():
                        if printer_name in saved_printers:
                            var.set(True)
                        else:
                            var.set(False)

                print("Configuration loaded successfully.")
            except Exception as e:
                print(f"Error loading config file: {e}")


    def save_config(self):
    # Saves current UI parameters and selected printers to JSON
        selected_printers = [p for p, var in self.printer_vars.items() if var.get()]

        data = {
            "watch_path": self.watch_path.get(),
            "watch_dw_folder_path": self.watch_dwfolder_path.get(),
            "selected_printers": selected_printers,
            "copies": self.copies_var.get(),
            "duplex": self.duplex_var.get(),
            "listen_mode": self.listen_mode.get(),
        }
        try:
            with open(CONFIG_FILE_PATH, "w") as f:
                json.dump(data, f, indent=4)
            print("Configuration saved successfully.")
        except Exception as e:
            print(f"Error loading config file: {e}")

    def on_close(self):
        self.save_config()  # Save settings before closing
        self.root.destroy()

    def browse_folder(self):
        folder = filedialog.askdirectory(title="Select Folder to Watch for Print Jobs")
        if folder:
            self.watch_path.set(folder)

    def browse_dw_folder(self):
        folder = filedialog.askdirectory(title="Select DocuWare Import Folder")
        if folder:
            self.watch_dwfolder_path.set(folder)

    def toggle_listening(self):
        if self.is_listening:
            self.stop_listening("Status: Idle (Listening canceled)")
        else:
            self.start_listening()

    def start_listening(self):
        self.save_config()
        watch_dir = self.watch_path.get()

        # Create the dir automatically if it doesn't exist
        if not os.path.exists(watch_dir):
            try:
                os.makedirs(watch_dir, exist_ok=True)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to create directory: {e}")
                return

        selected_printers = [p for p, var in self.printer_vars.items() if var.get()]
        if not selected_printers:
            messagebox.showerror("Error", "Please check at least one target printer.")
            return

        self.is_listening = True
        self.listen_btn.config(text="CANCEL", bg="red")
        self.status_var.set("Status: Waiting for incoming print jobs...")
        self.status_label.config(fg="green")

        # Start listening in a background thread so UI doesn't freeze
        threading.Thread(target=self.watch_loop, daemon=True).start()

    def stop_listening(self, status_message):
        self.is_listening = False
        self.listen_btn.config(text="START LISTENING", bg="green")
        self.status_var.set(status_message)
        self.status_label.config(fg="blue")

    def wait_until_file_ready(self, file_path, timeout=10):
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                with open(file_path, "a+b") as f:
                    return True
            except IOError:
                time.sleep(0.5)
        return False

    # def upload_to_docuware(self, file_path):
    #     """Uploads the PDF file directly to DocuWare Tray via REST API."""
    #     if not REQUESTS_AVAILABLE:
    #         raise Exception("'requests' library is not installed. Please run 'pip install requests'.")

    #     url = self.dw_url_var.get().rstrip('/')
    #     username = self.dw_user_var.get()
    #     password = self.dw_pass_var.get()
    #     basket_id = self.dw_tray_var.get()

    #     if not username or not password or not basket_id:
    #         raise Exception("DocuWare credentials or Tray ID are missing in UI settings!")

    #     session = requests.Session()
    #     session.headers.update({"Accept": "application/json"})

    #     # 1. Log in
    #     logon_url = f"{url}/Identity/Account/Login"
    #     response = session.post(logon_url, data={"UserName": username, "Password": password}, timeout=15)
    #     response.raise_for_status()

    #     # 2. Upload PDF
    #     upload_url = f"{url}/FileCabinets/{basket_id}/Documents"
    #     filename = os.path.basename(file_path)
    #     with open(file_path, "rb") as f:
    #         files = {"file": (filename, f, "application/pdf")}
    #         upload_res = session.post(upload_url, files=files, timeout=30)
    #         upload_res.raise_for_status()

    #     # 3. Log off
    #     try:
    #         session.post(f"{url}/Account/Logoff", timeout=5)
    #     except Exception:
    #         pass
    #     return True

    def set_printer_duplex(self, printer_name, is_double_sided):
        # modifies windows driver settings for the printer to set duplex mode
        try:
            # Open printer with modification access
            PRINTER_ALL_ACCESS = 0xF000C
            p_handle = win32print.OpenPrinter(printer_name, {"DesiredAccess": PRINTER_ALL_ACCESS})
            try:
                p_info = win32print.GetPrinter(p_handle, 2)  # Level 2 for detailed info
                devmode = p_info["pDevMode"]
                if devmode:
                    devmode.Duplex = DMDUP_VERTICAL if is_double_sided else DMDUP_SIMPLEX
                    devmode.Fields |= win32print.DM_DUPLEX  # Ensure the duplex field is marked as valid
                    win32print.SetPrinter(p_handle, 2, p_info, 0)
            finally:
                win32print.ClosePrinter(p_handle)
        except Exception as e:
            print(f"Error setting duplex mode for {printer_name}: {e}")

    def watch_loop(self):
        watch_dir = self.watch_path.get()

        while self.is_listening:
            try:
                # Look for files inside the target directory
                files = [f for f in os.listdir(watch_dir) if os.path.isfile(os.path.join(watch_dir, f))]

                if files:
                    target_file = os.path.join(watch_dir, files[0])
                    filename = files[0]

                    # Short pause to ensure Windows has finished writing the file
                    self.root.after(0, lambda: self.status_var.set(f"Status: Detected '{filename}', waiting for file to be ready..."))

                    if not self.wait_until_file_ready(target_file, timeout=10):
                        time.sleep(1)
                        continue  # Skip this iteration if file is not ready
                    

                    self.root.after(0, lambda: self.status_var.set(f"Status: Found '{filename}'! Printing..."))

                    # Send job to selected printers
                    selected_printers = [p for p, var in self.printer_vars.items() if var.get()]
                    num_copies = max(1, self.copies_var.get())
                    is_duplex = self.duplex_var.get()

                    # Process printing with selected options (copies, duplex) and send to all selected printers
                    self.process_and_print(target_file, selected_printers, num_copies, is_duplex)

                    # Pause to let Windows process the print job before deleting the file
                    time.sleep(2.0)

                    # Delete temporary source file
                    try:
                        os.remove(target_file)
                    except Exception as e:
                        print(f"Error deleting file': {e}")

                    mode = self.listen_mode.get()

                    if mode == "once":
                        # One-time trigger completed: reset status and stop listener
                        completion_message = f"Status: Job broadcasted to {len(selected_printers)} printers simultaneously!"
                        self.root.after(0, lambda: self.stop_listening(completion_message))
                        self.root.after(0, lambda: messagebox.showinfo(
                            "Success", f"Detected and broadcasted to {len(selected_printers)} printers successfully!"
                        ))
                        break
                    else:
                        # CONTINUOUS MODE: Keep listening for the next file without stopping or popping up
                        status_msg = f"Status: Sent '{filename}' to {len(selected_printers)} target(s). Waiting for next job..."
                        self.root.after(0, lambda msg=status_msg: self.status_var.set(msg))
            except Exception as e:
                print(f"Error during watch loop: {e}")

            time.sleep(1)  # Polling interval

    def print_via_win32print_raw(self, printer_name, file_path, num_copies):
        # Method A: Direct RAW spooling using win32print (Best for physical printers).
        try:
            hPrinter = win32print.OpenPrinter(printer_name)
            try:
                hJob = win32print.StartDocPrinter(hPrinter, 1, ("MultiPrint Job", None, "RAW"))
                win32print.StartPagePrinter(hPrinter)
                with open(file_path, "rb") as f:
                    win32print.WritePrinter(hPrinter, f.read())
                win32print.EndPagePrinter(hPrinter)
                win32print.EndDocPrinter(hPrinter)
                return True
            finally:
                win32print.ClosePrinter(hPrinter)
        except Exception as e:
            print(f"Error printing to {printer_name}: {e}")
            return False

    def print_via_sumatrapdf(self, sumatra_path, printer_name, file_path, num_copies, is_duplex):
        # Method B: Silent background rendering via SumatraPDF CLI executable.
        try:
            duplex_setting = "duplex" if is_duplex else "simplex"
            cmd = [
                sumatra_path,
                "-print-to", printer_name,
                "-print-settings", f"{num_copies}x,{duplex_setting}",
                file_path
            ]
            result = subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return result.returncode == 0
        except Exception as e:
            print(f" SumatraPDF failed: {e}")
            return False

    def print_via_shellexecute(self, printer_name, file_path, num_copies):
        # Method C: Windows ShellExecute printto verb (Fallback for standard files)
        try:
            for _ in range(num_copies):
                # Returns hInstance > 32 if process started successfully
                status = win32api.ShellExecute(0, "printto", file_path, f'"{printer_name}"', ".", 0)
                if status <= 32:
                    return False
                time.sleep(1.0)
            return True
        except Exception as e:
            print(f"ShellExecute failed: {e}")
            return False

    def print_worker(self, printer_name, file_path, num_copies, is_duplex):
        # Apply duplex setting for the printer before sending the job
        ext = os.path.splitext(file_path)[1].lower()

        # Docuware Import target
        if ext == ".pdf" and "docuware" in printer_name.lower():
            try:
                print(f"Copying '{file_path}' to DocuWare Import Folder...")
                self.send_to_docuware_desktop(file_path)
                return
            except Exception as e:
                print(f"Failed to transfer file: {e}")

        # route 1 if docuware specifically
        # if ext == ".pdf" and "docuware" in printer_name.lower():
        #     try:
        #         print(f"Uploading '{file_path}' to DocuWare via REST API...")
        #         self.upload_to_docuware(file_path)
        #         return  # Skip physical printer routine
        #     except Exception as e:
        #         print(f"DocuWare REST API Upload failed: {e}")

        # Configure duplex driver settings for physical hardware
        self.set_printer_duplex(printer_name, is_duplex)

        print(f"Processing print job for: '{printer_name}'...")

        # Try Direct RAW Spooling
        print(" Trying win32print RAW Spooling...")
        if self.print_via_win32print_raw(printer_name, file_path, num_copies):
            print(f"win32print RAW spooling Success: Sent raw bytes to '{printer_name}'")
            return

        sumatra_path = self.get_sumatra_path()
        if ext == ".pdf" and sumatra_path:
            print("SumatraPDF Engine...")
            if self.print_via_sumatrapdf(sumatra_path, printer_name, file_path, num_copies):
                print("Success: SumatraPDF spooled job to '{printer_name}'")
                return
        elif ext == ".pdf" and not sumatra_path:
            print("Skipped: 'SumatraPDF.exe' not found in app directory")

        # ShellExecute Default App Handler (Final Fallback)
        print("Windows ShellExecute (printto)...")
        if self.print_via_shellexecute(printer_name, file_path, num_copies):
            print(f"Success: ShellExecute to '{printer_name}'.")
            return

        # ALL TIERS FAILED
        print(f"All print methods failed for target '{printer_name}'.")

    def process_and_print(self, file_path, printers, num_copies=1, is_duplex=False):
        threads = []
        for printer in printers:
            t = threading.Thread(target=self.print_worker, args=(printer, file_path, num_copies, is_duplex))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()  # Wait for all threads to finish

    def get_sumatra_path():
        # Locates SumatraPDF.exe when running as a script or inside a PyInstaller EXE.
        if getattr(sys, 'frozen', False):
            # Running inside PyInstaller bundled executable
            base_path = sys._MEIPASS
        else:
            # Running as a normal Python script
            base_path = os.path.dirname(os.path.abspath(__file__))

        sumatra_exe = os.path.join(base_path, "SumatraPDF.exe")
        return sumatra_exe if os.path.exists(sumatra_exe) else None

    def is_virtual_printer(self, printer_name):
        """Detects if a printer is a virtual driver (DocuWare, PDF, File Port, etc.)."""
        # Quick name check for common virtual printer keywords
        virtual_keywords = ["pdf", "docuware", "xps", "onenote", "cutepdf", "foxit", "bullzip", "virtual", "fax"]
        if any(keyword in printer_name.lower() for keyword in virtual_keywords):
            return True

        # Inspect port and driver properties via win32print
        try:
            h_printer = win32print.OpenPrinter(printer_name)
            try:
                info = win32print.GetPrinter(h_printer, 2)
                port = info.get("pPortName", "").lower()
                driver = info.get("pDriverName", "").lower()

                # Check if port or driver indicates a file/virtual output
                if any(k in port for k in ["pdf", "file:", "nul:", "prompt", "docuware"]):
                    return True
                if any(k in driver for k in ["pdf", "docuware", "xps"]):
                    return True
            finally:
                win32print.ClosePrinter(h_printer)
        except Exception:
            pass

        return False

    def send_to_docuware_desktop(self, file_path):
        DOCUWARE_WATCH_FOLDER = self.watch_dwfolder_path.get()
        # Copies a pdf into the folder watched by the DocuWare Desktop App
        if not os.path.exists(DOCUWARE_WATCH_FOLDER):
            os.makedirs(DOCUWARE_WATCH_FOLDER, exist_ok=True)

        filename = os.path.basename(file_path)
        destination = os.path.join(DOCUWARE_WATCH_FOLDER, filename)

        shutil.copy2(file_path, destination)
        print(f"File '{filename}' dropped into DocuWare watched folder.")

# Unique identifier string for your application (use any unique name)
APP_MUTEX_NAME = "Global\\WatchedMultiPrintApp_SingleInstance_Mutex_9988"

def is_already_running():
    # Checks if another instance of this application is already running in Windows
    kernel32 = ctypes.windll.kernel32
    # Create or open a named mutex
    mutex = kernel32.CreateMutexW(None, False, APP_MUTEX_NAME)
    last_error = kernel32.GetLastError()

    # 183 = ERROR_ALREADY_EXISTS
    if last_error == 183:
        return True
    return False

def main():
    # Check if application is already open
    if is_already_running():
        root = tk.Tk()
        root.withdraw()
        messagebox.showwarning(
            "Already Running",
            "Watched Multi-Printer Router is already running!"
        )
        root.destroy()
        sys.exit(0)

    root = tk.Tk()
    app = WatchedMultiPrintApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
