import customtkinter as ctk
from utils.logger import get_logs, clear_logs

class LogsView(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Header Controls
        header_frame = ctk.CTkFrame(self, fg_color="#1e1e1e", corner_radius=12, border_width=1, border_color="#2e2e2e")
        header_frame.grid(row=0, column=0, padx=15, pady=(15, 10), sticky="ew")
        
        lbl = ctk.CTkLabel(header_frame, text="📜 EVENT LOGS AND HISTORY", font=("Helvetica", 14, "bold"), text_color="#ffffff")
        lbl.pack(side="left", padx=20, pady=15)
        
        # Clear Logs Button
        self.clear_btn = ctk.CTkButton(
            header_frame, 
            text="CLEAR HISTORY", 
            font=("Helvetica", 11, "bold"),
            fg_color="#ff453a",
            hover_color="#c9362e",
            text_color="#ffffff",
            height=32,
            width=110,
            corner_radius=16,
            command=self.clear_history
        )
        self.clear_btn.pack(side="right", padx=20, pady=15)
        
        # Refresh Button
        self.refresh_btn = ctk.CTkButton(
            header_frame, 
            text="REFRESH", 
            font=("Helvetica", 11, "bold"),
            fg_color="#2c2c2c",
            hover_color="#3c3c3c",
            text_color="#aaaaaa",
            height=32,
            width=90,
            corner_radius=16,
            command=self.refresh_history
        )
        self.refresh_btn.pack(side="right")
        
        # Textbox container
        self.txt_card = ctk.CTkFrame(self, fg_color="#1e1e1e", corner_radius=12, border_width=1, border_color="#2e2e2e")
        self.txt_card.grid(row=1, column=0, padx=15, pady=(0, 15), sticky="nsew")
        self.txt_card.grid_columnconfigure(0, weight=1)
        self.txt_card.grid_rowconfigure(0, weight=1)
        
        # Textbox
        self.textbox = ctk.CTkTextbox(
            self.txt_card,
            fg_color="transparent",
            text_color="#dcdcdc",
            font=("Consolas", 12),
            wrap="word",
            state="disabled",
            border_width=0
        )
        self.textbox.grid(row=0, column=0, padx=15, pady=15, sticky="nsew")
        
        self.refresh_history()

    def refresh_history(self):
        """Loads and formats logs into the textbox."""
        self.textbox.configure(state="normal")
        self.textbox.delete("1.0", "end")
        
        logs = get_logs()
        if not logs:
            self.textbox.insert("end", "System logs are empty. Activities will appear here as they occur.")
        else:
            formatted_lines = []
            for entry in logs:
                timestamp = entry.get("timestamp", "")
                event = entry.get("event", "").upper()
                details = entry.get("details", "")
                
                # Format: [2026-05-27 10:15:30] EVENT: Details
                line = f"[{timestamp}] {event:<20} | {details}\n"
                formatted_lines.append(line)
                
            self.textbox.insert("end", "".join(formatted_lines))
            
        self.textbox.configure(state="disabled")

    def clear_history(self):
        """Asks confirmation and clears logs."""
        from tkinter import messagebox
        if messagebox.askyesno("Confirm Clear", "Are you sure you want to clear all history logs?"):
            clear_logs()
            self.refresh_history()
