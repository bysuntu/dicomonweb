import pystray
from pystray import Icon, MenuItem, Menu
from PIL import Image, ImageTk  # Needed for creating icons
import os
import tkinter as tk
import threading
# import pygetwindow as gw
from tkinter import Label, Button, Entry, Toplevel, filedialog, messagebox
import asyncio
import subprocess
import sys

'''
# Import the server module
import importlib.util
pyc_file = "octopus.pyc"
spec = importlib.util.spec_from_file_location("SOM", pyc_file)
SOM = importlib.util.module_from_spec(spec)
spec.loader.exec_module(SOM)
'''

parentDir = os.path.dirname(os.path.abspath(__file__))

sys.path.append(os.path.join(parentDir, 'WPy64-310111', 'python-3.10.11.amd64'))
sys.path.append(os.path.join(parentDir, 'WPy64-310111', 'python-3.10.11.amd64', 'Scripts'))

import octopus as SOM

from toDICT import *

def mainGUI(host_address = "localhost", port = 2020):
    root = tk.Tk()

    # Start the server
    if os.name == 'nt':
        root.docker_path = r"C:/Program Files/Docker/Docker/Docker Desktop.exe"
        if os.path.exists('.configure'):
            with open('.configure', 'r') as f:
                root.docker_path = f.readline().strip()
        if os.path.exists(root.docker_path):
            print("Docker Desktop found.")
        else:
            print("Docker Desktop not found.")
            # popup a messge box to ask the user to select the docker desktop path
            root.docker_path = tk.filedialog.askopenfilename(
                initialdir="C:\\Program Files\\Docker\\Docker", 
                title="Select Docker Desktop Path",
                filetypes=[("Executable Files", "*.exe")]
            )

            if not os.path.exists(root.docker_path):
                messagebox.showerror("Error", "Docker Desktop not found!")
                root.destroy()
                return

            with open('.configure', 'w') as f:
                f.write(root.docker_path)
        print(f"Docker Desktop path: {root.docker_path}")
        root.host_address = host_address
        root.docker_image = "simonmesh/meshos:2406"
    
    if os.name == 'posix':
        root.docker_path = None
        root.host_address = host_address
        root.docker_image = None

    server = SOM.OCTOPUSServer(root)
    server.start()
    root.server = server

    # GUI 
    root.title("wsServer @ localhost")

    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    # Window GUI
    hex_color = "#555555"  # Sky blue color
    root.configure(bg=hex_color)

    root.geometry(f"130x80+{screen_width - 140}+{screen_height - 160}")
    root.resizable(False, True)

    # Set the icon image
    logoImage = Image.open(os.path.join(parentDir, "asset", "newLogo.png"))
    logoImage = logoImage.resize((20, 20), Image.LANCZOS)
    root.iconphoto(False, ImageTk.PhotoImage(logoImage))

    # Default home directory is the Downloads folder
    root.home = os.path.join(os.path.abspath(os.path.expanduser("~")))#, "Downloads")
    root.case_dir = root.home

    def choose_home_dir():
        home_dir = tk.filedialog.askdirectory(initialdir=root.home, title="Select Home Directory")
        home_dir = os.path.abspath(home_dir)
        if home_dir.startswith(root.home):
            root.home = home_dir
        else:
            messagebox.showerror("Invalid Directory", "Please select a directory in the allowed directory.")
            root.home = home_dir
        print(f"Home directory set to {root.home}")


    def create_case_dir():
        def create_folder():
            folder_name = folder_name_entry.get().strip()
            os.makedirs(os.path.join(root.case_dir, folder_name, 'system'), exist_ok=True)
            popup.destroy()
            root.folder_name = folder_name

            return
            
            folder_name = folder_name_entry.get().strip()
            
            if not folder_name:
                messagebox.showerror("Error", "Folder name cannot be empty!")
                return
            
            # Ask the user to select a parent directory
            selected_path = filedialog.askdirectory(title="Select a Parent Directory")
            if not selected_path:
                messagebox.showwarning("Warning", "No directory selected!")
                return

            full_path = os.path.join(selected_path, folder_name)

            try:
                os.makedirs(full_path, exist_ok=False)  # Will raise an error if the folder exists
                messagebox.showinfo("Success", f"Folder '{folder_name}' created at:\n{selected_path}")
                popup.destroy()
            except FileExistsError:
                messagebox.showerror("Error", "Folder already exists!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to create folder: {e}")

        # Set the icon image for the popup window
        popImage = Image.open(os.path.join("asset","newLogo.png"))
        popImage = popImage.resize((20, 20), Image.LANCZOS)
        # root.iconphoto(False, ImageTk.PhotoImage(logoImage))
        # Set it for the popup window

        popup = Toplevel(root)
        popup.title("Enter Case Name")
        popup.geometry("200x100")
        popup.transient(root)  # Keep popup on top of the main window
        popup.grab_set()  # Disable interaction with the main window
        popup.iconphoto(False, ImageTk.PhotoImage(popImage))

        Label(popup, text="Enter Case Name:").pack(pady=5)
        folder_name_entry = Entry(popup, width=20)
        folder_name_entry.pack(pady=5)
        Button(popup, text="Create Folder", command=create_folder).pack(pady=5)

    def import_stl_file():
        if root.case_dir:
            stl_file = tk.filedialog.askopenfilename(initialdir=root.home, title="Select STL File",
                                                    filetypes=(("STL Files", "*.stl"), ("All Files", "*.*")))
            stl_file = os.path.abspath(stl_file)
            
            if stl_file.startswith(root.home):
                root.stl_file = stl_file
                asyncio.run(server.updatetkRoot(root))
            else:
                messagebox.showerror("Invalid File", "Please select a file in the allowed directory.")
        else:
            messagebox.showerror("No Case Directory", "Please select a case directory first.")
    
    # check home directory
    if os.name == 'nt':
        try:
            result = subprocess.run(
                ['docker', 'inspect', root.docker_image],
                capture_output=True,
                text=True,
                check=True
            )
            
            # Parse the JSON output
            container_info = json.loads(result.stdout)
            sources = [mount['Source'] for mount in container_info[0].get('Mounts', [])]
            print(f"Sources: {sources}")
        except subprocess.CalledProcessError as e:
            print(f"Error: {e}")
        except Exception as e:
            print(f"Error: {e}")
    elif os.name == 'posix':
        pass
    else:
        print("Unsupported OS")
    

    # Load and configure the case folder image
    homeImage = Image.open(os.path.join(parentDir, "asset", "home.png"))
    homeImage = homeImage.resize((20, 20), Image.LANCZOS)
    homePhoto = ImageTk.PhotoImage(homeImage)  # Keep a reference to this object
    homeButton = tk.Button(
        root, 
        text="Work Directory", 
        font=("Helvetica", 10),
        command=choose_home_dir, 
        image=homePhoto, 
        # width=110,
        compound=tk.LEFT  # Image on the left, text on the right
    )

    caseImage = Image.open(os.path.join(parentDir, "asset", "collection_new.png"))
    caseImage = caseImage.resize((20, 20), Image.LANCZOS)
    casePhoto = ImageTk.PhotoImage(caseImage)  # Keep a reference to this object
    caseButton = tk.Button(
        root, 
        # text="Create", 
        font=("Helvetica", 10),
        command=create_case_dir, 
        image=casePhoto, 
        #width=2,
        # compound=tk.LEFT  # Image on the left, text on the right
    )

    root.stl_file = None
    geoImage = Image.open(os.path.join(parentDir, "asset", "geo.png"))
    geoImage = geoImage.resize((20, 20), Image.LANCZOS)
    geoPhoto = ImageTk.PhotoImage(geoImage)  # Keep a reference to this object
    geoButton = tk.Button(
        root, 
        # text="Geom", 
        font=("Helvetica", 10),
        image=geoPhoto, 
        command=import_stl_file,
        #width=2,
        # compound=tk.LEFT  # Image on the left, text on the right
    )
    meshImage = Image.open(os.path.join(parentDir, "asset", "mesh.png"))
    meshImage = meshImage.resize((20, 20), Image.LANCZOS)
    meshPhoto = ImageTk.PhotoImage(meshImage)  # Keep a reference to this object
    meshButton = tk.Button(
        root, 
        # text="Mesh", 
        font=("Helvetica", 10),
        image=meshPhoto,
        command = lambda: asyncio.run(server.run_linux_command(f'cd /OpenFOAM && blockMesh -case {root.folder_name}')),
        #width=2,
        # compound=tk.LEFT  # Image on the left, text on the right
    )

    custom1 = tk.Button(
        root,
        # text="Custom1",
        font=("Helvetica", 10),
    )
    custom2 = tk.Button(
        root,
        # text="Custom2",
        font=("Helvetica", 10),
    )
    custom3 = tk.Button(
        root,
        # text="Custom3",
        font=("Helvetica", 10),
    )

    # workButton.grid(row=0, column=0, padx=5, pady=5, ipadx=5, ipady=5, sticky="ew")
    homeButton.grid(row=0, column=0, columnspan=3, sticky="nsew")  # Centered in the first row
    caseButton.grid(row=1, column=0, sticky="nsew")   # First icon on second row
    geoButton.grid(row=1, column=1, sticky="nsew")   # Second icon on second row
    meshButton.grid(row=1, column=2, sticky="nsew")   # Third icon on second row

    custom1.grid(row=2, column=0, sticky="nsew")   # First icon on third row
    custom2.grid(row=2, column=1, sticky="nsew")   # Second icon on third row
    custom3.grid(row=2, column=2, sticky="nsew")   # Third icon on third row

    root.grid_columnconfigure(0, weight=1)
    root.grid_columnconfigure(1, weight=1)
    root.grid_columnconfigure(2, weight=1)
    # root.grid_rowconfigure(0, weight=1)
    # root.grid_rowconfigure(1, weight=1)


    # Load the icon image from a file
    def load_image():
        icon_path = os.path.join(parentDir, "asset", "newLogo.ico")
        if not os.path.exists(icon_path):
            raise FileNotFoundError(f"Icon file not found: {icon_path}")
        print('image path: ', icon_path)
        return Image.open(icon_path)

    # Callback for menu actions
    '''
    def resizeBrowser(showMode):
        browserWindows = gw.getAllTitles()
        for tabTitle in browserWindows:
            if tabTitle.find("sim.on.mesh") >= 0:
                #print("browser")
                mWindow = gw.getWindowsWithTitle(tabTitle)[0]
                mWindow.maximize()
                width_, height_ = mWindow.width, mWindow.height
                top_, left_ = mWindow.top, mWindow.left
                #print(width_, left_, height_, top_)
                mWindow.restore()
                mWindow.moveTo(top_, left_)
                if showMode == "partial":
                    mWindow.resizeTo(width_ - 130, height_)
                    #print(mWindow.width, mWindow.height, mWindow.top, mWindow.left)
                    # root.geometry(f"100x300+{width_-100 + left_}+0")
                    # resize the tkInter window
                    newPosition = f"130x300+{width_ - 130 + 3 * left_}+0"
                    #print('newPosition', newPosition)
                    root.geometry(newPosition)
                else:
                    mWindow.maximize()
    '''

    def minimize_to_tray():
        """Minimize the GUI to the system tray."""
        root.withdraw()  # Hide the main window
        # resizeBrowser("full")
        # start_tray_icon()
    def restore_from_tray():
        """Restore the GUI from the system tray."""
        #print("Restoring the application.")
        root.deiconify()
        # resizeBrowser("full")
    def on_closing():
        print("Closing OCTUPUS server.")
        root.server.stop()
        root.destroy()
    def on_quit():
        """Exit the application when quit is selected from the tray menu."""
        #print("Quitting ======== the application.")
        root.icon.visible = False
        root.icon.stop()
        root.icon = None
        root.quit()
        server.stop()
        root.destroy()

    # Create the tray icon
    tray_thread = None
    def setup_tray():
        root.icon = Icon(
            "sim.on.mesh", 
            icon=load_image(), 
            menu=Menu(
                MenuItem("Restore", restore_from_tray), MenuItem("Quit", on_quit)
            ))
        tray_thread = threading.Thread(target=root.icon.run, daemon=True)
        tray_thread.start()
    
    # Run the tray icon
    root.protocol("WM_DELETE_WINDOW", minimize_to_tray)
    setup_tray()
    root.mainloop()

    #print("Closing the tkinter UI server.")
    if server.server_thread.is_alive():
        server.server_thread.join()
    #print("Exiting the program.")
    if tray_thread and tray_thread.is_alive():
        tray_thread.join()
    # print("Tray thread joined.")

if __name__ == "__main__":
    mainGUI()
