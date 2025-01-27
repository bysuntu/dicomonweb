import React, { useState, useEffect, useMemo, use } from "react";
import "./App.css";
import { useLoader, useThree } from "@react-three/fiber";
import { DataTexture, LuminanceFormat, UnsignedByteType, Vector3, Quaternion } from "three";

import * as THREE from "three";
import { OrbitControls } from "@react-three/drei";

function orientationToRotationMatrix(orientation) {
  const [rowX, rowY, rowZ, colX, colY, colZ] = orientation;

  // Normalize the row and column vectors
  const row = new THREE.Vector3(rowX, rowY, rowZ).normalize();
  const col = new THREE.Vector3(colX, colY, colZ).normalize();

  // Compute the normal vector (cross product of row and column)
  const normal = new THREE.Vector3().crossVectors(row, col).normalize();

  // Construct the rotation matrix
  const matrix = new THREE.Matrix4();
  matrix.set(
    row.x, col.x, normal.x, 0,
    row.y, col.y, normal.y, 0,
    row.z, col.z, normal.z, 0,
    0, 0, 0, 1
  );

  return matrix;
}

function TexturePlane({pixelData, width, height, origin, orientation}) {


    const texture = useMemo(() => {
        const size = height * width;
        if (pixelData.length !== size) {
            return null;
        }

        const minValue = Math.min(...pixelData);
        const maxValue = Math.max(...pixelData);

        const imageData = new Uint8Array(size * 4);
        for (let i = 0; i < size; i++) {
            const gray = Math.min(Math.max(((pixelData[i] - minValue) / (maxValue - minValue)) * 255, 0), 255);
            imageData[i * 4] = gray; // R
            imageData[i * 4 + 1] = gray; // G
            imageData[i * 4 + 2] = gray; // B
            imageData[i * 4 + 3] = 255; // Alpha
        }
        // Create the texture from image data
        const texture = new THREE.DataTexture(imageData, width, height, THREE.RGBAFormat);
        texture.needsUpdate = true; // Ensure texture is updated
        return texture;
    }, [pixelData, width, height]);

  // Calculate plane orientation from rowDir and colDir
    const calculatePlaneRotation = (orientation) => {
        const [rowX, rowY, rowZ, colX, colY, colZ] = orientation;

        const rowDir = [rowX, rowY, rowZ];
        const colDir = [colX, colY, colZ];

        // Normalize the row and column vectors 
        const row = new THREE.Vector3(...rowDir).normalize();
        const col = new THREE.Vector3(...colDir).normalize();

        const normal = new THREE.Vector3()
        .crossVectors(new THREE.Vector3(...row), new THREE.Vector3(...col))
        .normalize();

        const quaternion = new THREE.Quaternion();
        quaternion.setFromUnitVectors(new THREE.Vector3(0, 0, 1), normal); // Rotate Z-axis to match the plane's normal
        return new THREE.Euler().setFromQuaternion(quaternion);
    };

    const rotation = useMemo(() => {
        return calculatePlaneRotation(orientation);
    }, [orientation]);

    return (
        <mesh position={origin} rotation={rotation}>
          {/* Plane geometry with a size of rows x columns */}
          <planeGeometry args={[width, height]} />
          <meshBasicMaterial map={texture} side={THREE.DoubleSide} />
        </mesh>
      );

}

function DicomImage({ pixelData, width, height, origin, orientation }) {
    const { gl } = useThree();
  
    // Convert the 1D pixel array to a 2D texture
    const texture = useMemo(() => {
      if (!pixelData || !width || !height) return null;

          // Step 1: Find the min and max pixel values (for rescaling)
    const minValue = Math.min(...pixelData);
    const maxValue = Math.max(...pixelData);
    console.log("minValue", minValue, "maxValue", maxValue);
    // Step 2: Rescale to 0–255 range
    const data = new Uint8Array(pixelData.length);
    for (let i = 0; i < pixelData.length; i++) {
      data[i] = Math.min(Math.max(((pixelData[i] - minValue) / (maxValue - minValue)) * 255, 0), 255);
    }
    console.log("data", Math.max(...data));
      // Create a Uint8Array from the pixel data
     // const data = new Uint8Array(pixelData);
  
      // Create a DataTexture
      const texture = new DataTexture(data, width, height, LuminanceFormat, UnsignedByteType);
      texture.needsUpdate = true; // Ensure the texture is updated
  
      return texture;
    }, [pixelData, width, height]);
  
    // Convert the orientation to a quaternion
    const quaternion = useMemo(() => {
      if (!orientation) return null;
  
      // Convert the orientation to a rotation matrix
      const matrix = orientationToRotationMatrix(orientation);
  
      // Convert the rotation matrix to a quaternion
      const quaternion = new Quaternion();
      quaternion.setFromRotationMatrix(matrix);
  
      return quaternion;
    }, [orientation]);
  
    // Dispose of the texture when the component unmounts
    useEffect(() => {
      return () => {
        if (texture) texture.dispose();
      };
    }, [texture]);
  
    // Return null if texture or quaternion creation fails
    if (!texture || !quaternion) return null;
  
    return (
      <mesh position={new Vector3(...origin)} quaternion={quaternion}>
        <planeGeometry args={[width, height]} />
        <meshBasicMaterial map={texture} side={THREE.DoubleSide} />
      </mesh>
    );
  }
  
export default TexturePlane;