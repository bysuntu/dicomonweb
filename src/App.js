import React, { useState, useEffect, useMemo, use } from "react";
import "./App.css";
import msgpack from "msgpack-lite";
import { Canvas, useLoader, useThree } from "@react-three/fiber";
import { OrbitControls } from "@react-three/drei";
import {
  TextureLoader,
  DataTexture,
  RGBAFormat,
  UnsignedByteType,
  Matrix4,
  Vector3,
} from "three";

import * as THREE from "three";

import TexturePlane from "./DicomImage";

function App() {
  const [dicomFolder, setDicomFolder] = useState("");
  const [response, setResponse] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [protocols, setProtocols] = useState({}); // { "ProtocolName": ["file1.dcm", "file2.dcm"] }
  const [selectedProtocol, setSelectedProtocol] = useState(null);

  const [selectedFile, setSelectedFile] = useState(null);
  const [pixelData, setPixelData] = useState({});

  const pixelDataRef = React.useRef(pixelData);

  const sendQuery = () => {
    if (!dicomFolder) {
      setError("Please enter a DICOM folder path.");
      return;
    }

    setLoading(true);
    setError(null);
    setResponse(null);

    const ws = new WebSocket("ws://localhost:8765");

    ws.onopen = () => {
      console.log("Connected to server");
      ws.send(
        JSON.stringify({
          action: "get_sorted_dicom",
          dicom_folder: dicomFolder,
        })
      );
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      console.log(data);
      if (data.status === "success") {
        // Group files by protocol name
        const groupedProtocols = data.sorted_dicom_files.reduce((acc, file) => {
          const protocol = file.protocol_name;
          if (!acc[protocol]) {
            acc[protocol] = [];
          }
          acc[protocol].push(file.file_path);
          return acc;
        }, {});

        setProtocols(groupedProtocols);
      } else {
        setError(data.error || "Failed to fetch data");
      }

      setResponse(data);
      setLoading(false);
      ws.close();
    };

    ws.onerror = (error) => {
      console.error("WebSocket error:", error);
      setError("Error connecting to the server.");
      setLoading(false);
    };

    ws.onclose = () => {
      console.log("WebSocket connection closed");
    };
  };

  useEffect(() => {
    console.log("pixelData: ", pixelData);
  }, [pixelData]);

  const handleFileClick = (filePath) => {
    setLoading(true);
    setSelectedFile(filePath);

    const ws = new WebSocket("ws://localhost:8765");
    console.log("Connected to server");
    ws.onopen = () => {
      console.log("sending to server");
      ws.send(
        JSON.stringify({
          action: "get_dicom_pixel_data",
          file_path: filePath,
        })
      );
    };
    console.log("Sending pixel data request", filePath);

    ws.onmessage = async (event) => {
      console.log("data type: === ", typeof event.data);
      if (typeof event.data === "string") {
        console.log("Received string data");
        const data = JSON.parse(event.data);
        console.log("before: ", data);
        if (data.status === "success") {
          const img_info = data;
          console.log("string before ==== : ", pixelDataRef.current);
          console.log("string after ==== : ", img_info);
          setPixelData((preState) => ({ ...preState, ...img_info }));
        } else {
          setError(data.error || "Failed to fetch pixel data");
        }
      }
      if (typeof event.data === "object") {
        const arrayBuffer = await event.data.arrayBuffer(); // Get the binary data
        const data = msgpack.decode(new Uint8Array(arrayBuffer)); // Decode msgpack
        // Extract the pixel data, origin, orientation, and shape

        // Convert the pixel list back to a typed array (e.g., Uint8Array or Float32Array)
        const pixel_array = new Float32Array(data);
        console.log("obje before =====:", pixelData);
        setPixelData((preState) => ({ ...preState, pixelArray: pixel_array }));

        setLoading(false);
        ws.close();
      }

      return;
    };
  };

  return (
    <>
      <div className="App">
        <h1>DICOM Sorter</h1>
        <div>
          <label htmlFor="dicomFolder">DICOM Folder Path:</label>
          <input
            id="dicomFolder"
            type="text"
            value={dicomFolder}
            onChange={(e) => setDicomFolder(e.target.value)}
            placeholder="Enter DICOM folder path"
          />
          <button onClick={sendQuery} disabled={loading}>
            {loading ? "Loading..." : "Send Query"}
          </button>
        </div>
      </div>

      <div className="Options">
        <h1>DICOM Sorter</h1>
        {pixelData &&
          pixelData.pixelArray &&
          pixelData.origin &&
          pixelData.orientation &&
          pixelData.shape && (
            <Canvas
              orthographic // Enable orthographic camera
              camera={{
                position: [0, 0, 500], // Camera position
                zoom: 1, // Initial zoom level
                near: 0.1, // Near clipping plane
                far: 1000, // Far clipping plane

              }}
              className="canvas-container"
            >
              <OrbitControls enableZoom={true} enablePan={true} />
              <ambientLight intensity={0.5} />
              <pointLight position={[10, 10, 10]} />
              {pixelData && (
                <TexturePlane
                  pixelData={pixelData.pixelArray}
                  origin={pixelData.origin}
                  orientation={pixelData.orientation}
                  width={pixelData.shape[1]}
                  height={pixelData.shape[0]}
                />
              )}
            </Canvas>
          )}

        {loading && <div>Loading...</div>}
        {error && <div className="error">{error}</div>}

        <div className="two-column-layout">
          {/* First Column: Protocols */}
          <div className="column">
            <h2>Protocols</h2>
            <ul>
              {Object.keys(protocols).map((protocol) => (
                <li
                  key={protocol}
                  onClick={() => setSelectedProtocol(protocol)}
                  className={selectedProtocol === protocol ? "selected" : ""}
                >
                  {protocol}
                </li>
              ))}
            </ul>
          </div>

          {/* Second Column: Files */}
          <div className="column">
            <h2>Files</h2>
            {selectedProtocol ? (
              <ul>
                {protocols[selectedProtocol].map((file, index) => (
                  <li key={index} onClick={() => handleFileClick(file)}>
                    {file}{" "}
                  </li>
                ))}
              </ul>
            ) : (
              <div>Select a protocol to view files.</div>
            )}
          </div>
        </div>
      </div>
    </>
  );
}

export default App;
