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
  
export default DicomImage;