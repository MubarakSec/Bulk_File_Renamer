import customtkinter as ctk
import os
import re
import threading
import json
from tkinter import filedialog, messagebox
from collections import deque

class BulkFileRenamer(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Configure window
        self.title("Bulk File Renamer")
        self.geometry("1000x550")
        ctk.set_appearance_mode("Dark")
        self._undo_stack = deque(maxlen=10)  # Store last 10 rename operations

        # Create main container
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(fill="both", expand=True, padx=15, pady=15)

        # Folder selection
        self.folder_frame = ctk.CTkFrame(self.main_frame)
        self.folder_frame.grid(row=0, column=0, columnspan=2, padx=5, pady=5, sticky="ew")
        
        self.folder_button = ctk.CTkButton(self.folder_frame, 
                                        text="Select Folder",
                                        command=self.select_folder,
                                        width=120)
        self.folder_button.pack(side="left", padx=(5, 10), pady=5)
        
        self.folder_label = ctk.CTkLabel(self.folder_frame, text="No folder selected", anchor="w")
        self.folder_label.pack(side="left", fill="x", expand=True, padx=(0, 5), pady=5)

        # Rename controls
        control_frame = ctk.CTkFrame(self.main_frame)
        control_frame.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")
        
        # Prefix
        ctk.CTkLabel(control_frame, text="Prefix:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.prefix_entry = ctk.CTkEntry(control_frame, placeholder_text="Add prefix")
        self.prefix_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        # Suffix
        ctk.CTkLabel(control_frame, text="Suffix:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.suffix_entry = ctk.CTkEntry(control_frame, placeholder_text="Add suffix")
        self.suffix_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        
        # Replace
        ctk.CTkLabel(control_frame, text="Replace:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.replace_frame = ctk.CTkFrame(control_frame, fg_color="transparent")
        self.replace_frame.grid(row=2, column=1, padx=0, pady=0, sticky="ew")
        
        self.find_entry = ctk.CTkEntry(self.replace_frame, placeholder_text="Find text")
        self.find_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        self.replace_entry = ctk.CTkEntry(self.replace_frame, placeholder_text="Replace with")
        self.replace_entry.pack(side="left", fill="x", expand=True)
        
        # Regex option
        self.regex_var = ctk.BooleanVar(value=False)
        regex_cb = ctk.CTkCheckBox(control_frame, text="Use Regex", variable=self.regex_var)
        regex_cb.grid(row=3, column=0, columnspan=2, padx=5, pady=5, sticky="w")
        
        # Extension filter
        ctk.CTkLabel(control_frame, text="Extensions:").grid(row=4, column=0, padx=5, pady=5, sticky="w")
        self.ext_filter_entry = ctk.CTkEntry(control_frame, 
                                          placeholder_text="jpg,png,txt (comma separated)")
        self.ext_filter_entry.grid(row=4, column=1, padx=5, pady=5, sticky="ew")
        
        # Action buttons
        btn_frame = ctk.CTkFrame(control_frame, fg_color="transparent")
        btn_frame.grid(row=5, column=0, columnspan=2, pady=10)
        
        self.preview_button = ctk.CTkButton(btn_frame,
                                          text="Preview Changes",
                                          command=self.preview_changes)
        self.preview_button.pack(pady=5, fill="x")
        
        self.apply_button = ctk.CTkButton(btn_frame,
                                        text="Apply Renames",
                                        command=self.start_rename_thread)
        self.apply_button.pack(pady=5, fill="x")
        
        self.undo_button = ctk.CTkButton(btn_frame,
                                       text="Undo Last Rename",
                                       command=self.undo_rename,
                                       state="disabled")
        self.undo_button.pack(pady=5, fill="x")
        
        # Preset buttons
        preset_frame = ctk.CTkFrame(btn_frame, fg_color="transparent")
        preset_frame.pack(fill="x", pady=(10, 0))
        
        save_btn = ctk.CTkButton(preset_frame, text="Save Preset", command=self.save_preset)
        save_btn.pack(side="left", padx=(0, 5), fill="x", expand=True)
        
        load_btn = ctk.CTkButton(preset_frame, text="Load Preset", command=self.load_preset)
        load_btn.pack(side="right", padx=(5, 0), fill="x", expand=True)

        # File list display
        list_frame = ctk.CTkFrame(self.main_frame)
        list_frame.grid(row=1, column=1, padx=(10, 5), pady=5, sticky="nsew")
        list_frame.grid_columnconfigure(0, weight=1)
        list_frame.grid_rowconfigure(0, weight=1)
        
        self.file_list = ctk.CTkTextbox(list_frame, wrap="none", font=ctk.CTkFont(family="Courier", size=12))
        self.file_list.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Status bar
        self.status_bar = ctk.CTkLabel(self.main_frame, text="Ready", anchor="w")
        self.status_bar.grid(row=2, column=0, columnspan=2, padx=5, pady=(0, 5), sticky="ew")

        # Configure grid weights
        self.main_frame.columnconfigure(0, weight=0)
        self.main_frame.columnconfigure(1, weight=1)
        self.main_frame.rowconfigure(1, weight=1)
        
        # Initialize state
        self.folder_path = ""
        self.original_files = []
        self.preview_data = []  # (original, new, status)
        self.current_display = []  # Current files being displayed

    def select_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.folder_path = folder
            self.folder_label.configure(text=os.path.basename(folder))
            self.load_files()
            self.status_bar.configure(text=f"Loaded {len(self.original_files)} files")
            
    def load_files(self):
        self.original_files = []
        if not self.folder_path:
            return
            
        # Get extension filter
        ext_text = self.ext_filter_entry.get().strip()
        extensions = [ext.strip().lower() for ext in ext_text.split(",")] if ext_text else []
        
        for filename in os.listdir(self.folder_path):
            filepath = os.path.join(self.folder_path, filename)
            if os.path.isfile(filepath):
                if extensions:
                    file_ext = os.path.splitext(filename)[1].lower()
                    if file_ext and file_ext[1:] not in extensions:
                        continue
                self.original_files.append(filename)
        
        self.current_display = self.original_files.copy()
        self.display_files()

    def display_files(self):
        self.file_list.delete("1.0", "end")
        if not self.current_display:
            self.file_list.insert("end", "No files to display")
            return
            
        # Display in two columns if preview exists
        if hasattr(self, 'preview_data') and self.preview_data:
            header = "Original".ljust(45) + "New Name".ljust(45) + "Status\n"
            self.file_list.insert("end", header)
            self.file_list.insert("end", "-"*100 + "\n")
            
            for original, new, status in self.preview_data:
                orig_trunc = (original[:42] + '...') if len(original) > 45 else original.ljust(45)
                new_trunc = (new[:42] + '...') if len(new) > 45 else new.ljust(45)
                status_color = "green" if "Success" in status else "red" if "Error" in status else "white"
                
                self.file_list.insert("end", f"{orig_trunc} {new_trunc} ")
                self.file_list.insert("end", status, status_color)
                self.file_list.insert("end", "\n")
        else:
            # Display simple list
            for filename in self.current_display:
                self.file_list.insert("end", filename + "\n")
        
        # Configure tag colors
        self.file_list.tag_config("green", foreground="#2ECC71")
        self.file_list.tag_config("red", foreground="#E74C3C")

    def generate_new_name(self, filename):
        name, ext = os.path.splitext(filename)
        
        # Apply find/replace
        find_text = self.find_entry.get()
        replace_text = self.replace_entry.get()
        if find_text:
            if self.regex_var.get():
                try:
                    name = re.sub(find_text, replace_text, name)
                except re.error:
                    return filename  # Return original on regex error
            else:
                name = name.replace(find_text, replace_text)
        
        # Apply prefix and suffix
        prefix = self.prefix_entry.get()
        suffix = self.suffix_entry.get()
        new_name = f"{prefix}{name}{suffix}{ext}"
        
        return new_name

    def preview_changes(self):
        if not self.folder_path:
            self.status_bar.configure(text="Error: Please select a folder first!")
            return
            
        self.load_files()  # Refresh file list with current filter
        self.preview_data = []
        seen_names = set()
        collision_names = set()
        
        for filename in self.original_files:
            new_name = self.generate_new_name(filename)
            original_path = os.path.join(self.folder_path, filename)
            new_path = os.path.join(self.folder_path, new_name)
            
            # Check for potential issues
            status = "Ready"
            if new_name in seen_names:
                status = "Error: Duplicate name"
                collision_names.add(new_name)
            elif os.path.exists(new_path) and filename != new_name:
                status = "Error: File exists"
            elif not os.access(original_path, os.W_OK):
                status = "Error: Permission denied"
            
            self.preview_data.append((filename, new_name, status))
            seen_names.add(new_name)
        
        # Update duplicate status for all collisions
        for i, (original, new_name, status) in enumerate(self.preview_data):
            if new_name in collision_names and status == "Ready":
                self.preview_data[i] = (original, new_name, "Error: Duplicate name")
        
        self.current_display = self.preview_data
        self.display_files()
        self.status_bar.configure(text=f"Preview generated for {len(self.preview_data)} files")

    def start_rename_thread(self):
        if not self.preview_data:
            self.status_bar.configure(text="Error: Generate preview first!")
            return
            
        # Disable buttons during operation
        self.apply_button.configure(state="disabled")
        self.preview_button.configure(state="disabled")
        self.status_bar.configure(text="Starting rename process...")
        
        # Start renaming in a separate thread
        threading.Thread(target=self.perform_renaming, daemon=True).start()

    def perform_renaming(self):
        rename_actions = []
        undo_actions = []
        
        for original, new, status in self.preview_data:
            if "Error" in status:
                continue
                
            src = os.path.join(self.folder_path, original)
            dst = os.path.join(self.folder_path, new)
            rename_actions.append((src, dst, original))
            undo_actions.append((dst, src))  # For undo
        
        if not rename_actions:
            self.status_bar.configure(text="No valid files to rename")
            self.enable_buttons()
            return
            
        # Store for undo
        self._undo_stack.append(undo_actions)
        self.undo_button.configure(state="normal")
        
        success_count = 0
        total = len(rename_actions)
        
        for i, (src, dst, original) in enumerate(rename_actions):
            try:
                os.rename(src, dst)
                self.update_file_status(original, "Success")
                success_count += 1
            except OSError as e:
                self.update_file_status(original, f"Error: {str(e)}")
            
            progress = int((i + 1) / total * 100)
            self.status_bar.configure(text=f"Renaming: {progress}% ({i+1}/{total})")
        
        self.status_bar.configure(
            text=f"Renaming complete! {success_count} of {total} files renamed"
        )
        self.enable_buttons()
        
        # Refresh file list
        self.load_files()

    def update_file_status(self, original, status):
        # Update status in preview data
        for i, (orig, new, st) in enumerate(self.preview_data):
            if orig == original:
                self.preview_data[i] = (original, new, status)
                break
        
        # Update UI
        self.after(0, self.display_files)

    def enable_buttons(self):
        self.apply_button.configure(state="normal")
        self.preview_button.configure(state="normal")

    def undo_rename(self):
        if not self._undo_stack:
            return
            
        # Disable buttons during undo
        self.undo_button.configure(state="disabled")
        self.apply_button.configure(state="disabled")
        self.preview_button.configure(state="disabled")
        self.status_bar.configure(text="Starting undo process...")
        
        # Start undo in a separate thread
        threading.Thread(target=self.perform_undo, daemon=True).start()

    def perform_undo(self):
        undo_actions = self._undo_stack.pop()
        if not self._undo_stack:
            self.undo_button.configure(state="disabled")
        
        total = len(undo_actions)
        success_count = 0
        
        for i, (src, dst) in enumerate(undo_actions):
            try:
                if os.path.exists(src):
                    os.rename(src, dst)
                    success_count += 1
            except OSError:
                pass  # Silently continue
            
            progress = int((i + 1) / total * 100)
            self.status_bar.configure(text=f"Undoing: {progress}% ({i+1}/{total})")
        
        self.status_bar.configure(
            text=f"Undo complete! {success_count} of {total} files restored"
        )
        self.enable_buttons()
        self.load_files()  # Refresh file list

    def save_preset(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")]
        )
        if not file_path:
            return
            
        preset = {
            "prefix": self.prefix_entry.get(),
            "suffix": self.suffix_entry.get(),
            "find_text": self.find_entry.get(),
            "replace_text": self.replace_entry.get(),
            "extensions": self.ext_filter_entry.get(),
            "use_regex": self.regex_var.get()
        }
        
        try:
            with open(file_path, "w") as f:
                json.dump(preset, f, indent=2)
            self.status_bar.configure(text=f"Preset saved: {os.path.basename(file_path)}")
        except Exception as e:
            self.status_bar.configure(text=f"Error saving preset: {str(e)}")

    def load_preset(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json")]
        )
        if not file_path:
            return
            
        try:
            with open(file_path, "r") as f:
                preset = json.load(f)
                
            self.prefix_entry.delete(0, "end")
            self.prefix_entry.insert(0, preset.get("prefix", ""))
            
            self.suffix_entry.delete(0, "end")
            self.suffix_entry.insert(0, preset.get("suffix", ""))
            
            self.find_entry.delete(0, "end")
            self.find_entry.insert(0, preset.get("find_text", ""))
            
            self.replace_entry.delete(0, "end")
            self.replace_entry.insert(0, preset.get("replace_text", ""))
            
            self.ext_filter_entry.delete(0, "end")
            self.ext_filter_entry.insert(0, preset.get("extensions", ""))
            
            self.regex_var.set(preset.get("use_regex", False))
            
            self.status_bar.configure(text=f"Preset loaded: {os.path.basename(file_path)}")
        except Exception as e:
            self.status_bar.configure(text=f"Error loading preset: {str(e)}")

if __name__ == "__main__":
    app = BulkFileRenamer()
    app.mainloop()
