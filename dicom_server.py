import os
import json
import asyncio
import websockets
from datetime import datetime
import pydicom
import io
import msgpack

def get_dicom_pixel_data(file_path):
    """
    Retrieve DICOM pixel data, origin, orientation, and shape, and serialize using msgpack.

    Args:
        file_path (str): Path to the DICOM file.

    Returns:
        bytes: Serialized data using msgpack.
    """
    # Read the DICOM file
    dicom_data = pydicom.dcmread(file_path)
    pixel_array = dicom_data.pixel_array  # Get pixel data as a NumPy array
    origin = list(dicom_data.ImagePositionPatient)  # [x, y, z]
    orientation = list(dicom_data.ImageOrientationPatient)  # [x1, y1, z1, x2, y2, z2]
    shape = list(pixel_array.shape)  # Shape of the pixel array
    # Convert pixel array to a list (msgpack cannot serialize NumPy arrays directly)
    print(pixel_array.shape)
    '''
    pixel_list = []
    for i, row in enumerate(pixel_array):
        # row = [float(x) for x in row]
        row = row.astype(int).tolist()
        pixel_list.extend(row)
    '''
    pixel_list = pixel_array.astype(int).flatten().tolist()
    print("First 10 elements of pixel_list:", pixel_list[:10])
    # Prepare the data for serialization
    data = {
        # "pixel_data": pixel_list,
        'status': 'success',
        "origin": origin,
        "orientation": orientation,
        "shape": shape,
    }
    # Serialize the data using msgpack
    serialized_data = msgpack.packb(pixel_list, use_bin_type=True)
    
    return serialized_data, data

def is_dicom_file(file_path):
    """
    Check if a file is a valid DICOM file.

    Args:
        file_path (str): Path to the file to check.

    Returns:
        bool: True if the file is a valid DICOM file, False otherwise.
    """
    try:
        # Attempt to read the file using pydicom
        pydicom.dcmread(file_path)
        return True
    except:
        # If an exception occurs, the file is not a valid DICOM file
        return False


# Function to parse DICOM files and sort them
def parse_and_sort_dicom_files(dicom_folder):
    dicom_files = []
    
    for root, _, files in os.walk(dicom_folder):
        for file in files:
            if is_dicom_file(os.path.join(root, file)):
                file_path = os.path.join(root, file)
                try:
                    dicom_data = pydicom.dcmread(file_path)
                    protocol_name = dicom_data.get("ProtocolName", "Unknown")
                    scan_time = dicom_data.get("SOPInstanceUID", "000000")
                    # print(f"Protocol Name: {protocol_name}, Scan Time: {scan_time}")
                    image_position = [float(x) for x in dicom_data.get("ImagePositionPatient")]
                    image_orientation = [float(x) for x in dicom_data.get("ImageOrientationPatient")]
                    # Convert scan time to a datetime object for sorting
                    # scan_time_obj = datetime.strptime(scan_time, "%H%M%S")
                    # print(f"Protocol Name: {protocol_name}, Scan Time: {scan_time}, Image Position: {image_position}, Image Orientation: {image_orientation}")
                    dicom_files.append({
                        "file_path": file_path,
                        "protocol_name": protocol_name,
                        "scan_time": scan_time,  # scan_time_obj.strftime("%H:%M:%S"),
                        # "dicom_data": dicom_data,
                        "image_position": image_position,
                        "image_orientation": image_orientation,
                    })
                except Exception as e:
                    print(f"Error reading {file_path}: {e}")
    
    # Sort by protocol name and then by scan time
    dicom_files.sort(key=lambda x: (x["protocol_name"], x["scan_time"]))
    
    return dicom_files

# WebSocket server to communicate with the client
async def dicom_server(websocket, path):
    async for message in websocket:
        try:
            print(f"Received message: {message}")
            data = json.loads(message)
            print(f"Received data: {data}")
            if data.get("action") == "get_sorted_dicom":
                dicom_folder = data.get("dicom_folder", "")
                if not dicom_folder:
                    await websocket.send(json.dumps({"error": "No DICOM folder provided"}))
                    continue
                print(f"Received DICOM folder: {dicom_folder}")
                sorted_dicom_files = parse_and_sort_dicom_files(dicom_folder)
                
                # Prepare the response
                response = {
                    "status": "success",
                    "sorted_dicom_files": [
                        {
                            "file_path": file["file_path"],
                            "protocol_name": file["protocol_name"],
                            "scan_time": file["scan_time"],
                            "image_position": file["image_position"],
                            "image_orientation": file["image_orientation"],
                        }
                        for file in sorted_dicom_files
                    ]
                }
                
                await websocket.send(json.dumps(response))
            
            elif data.get("action") == "get_dicom_pixel_data":
                print("Received get_dicom_pixel_data request")
                file_path = data.get("file_path", "")
                if not file_path:
                    await websocket.send(json.dumps({"error": "No file path provided"}))
                    continue
                
                print(f"Received file path: {file_path}")
                serialized_data, img_data = get_dicom_pixel_data(file_path)
                print("Sending pixel data: xxx", img_data)

                # Send the serialized data over WebSocket
                await websocket.send(json.dumps(img_data))
                await websocket.send(serialized_data)


            else:
                await websocket.send(json.dumps({"error": "Invalid action"}))
        except Exception as e:
            await websocket.send(json.dumps({"error": str(e)}))

# Start the WebSocket server
start_server = websockets.serve(dicom_server, "localhost", 8765)

print("WebSocket server started on ws://localhost:8765")

# Run the server
asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()