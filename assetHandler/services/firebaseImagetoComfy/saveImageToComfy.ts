import * as fs from 'fs';
import * as path from 'path';
import { v4 as uuidv4 } from 'uuid';

export async function saveImageToComfy(imageBuffer: Buffer, originalFileName: string): Promise<string> {
  try {
    // Extract file extension from original filename
    const fileExtension = path.extname(originalFileName);
    
    // Generate unique filename for ComfyUI
    const uniqueFileName = `${uuidv4()}${fileExtension}`;
    
    // ComfyUI input directory path
    const comfyInputDir = process.env.COMFYUI_INPUT_PATH || '/data/ComfyUI/input';
    const filePath = path.join(comfyInputDir, uniqueFileName);
    
    console.log(`Saving image to ComfyUI input directory: ${filePath}`);
    
    // Ensure the directory exists
    if (!fs.existsSync(comfyInputDir)) {
      fs.mkdirSync(comfyInputDir, { recursive: true });
      console.log(`Created ComfyUI input directory: ${comfyInputDir}`);
    }
    
    // Write image buffer to file
    fs.writeFileSync(filePath, imageBuffer);
    
    console.log(`Successfully saved image to ComfyUI: ${uniqueFileName}`);
    return uniqueFileName;
    
  } catch (error) {
    console.error(`Failed to save image to ComfyUI: ${(error as Error).message}`);
    throw new Error(`ComfyUI save failed: ${(error as Error).message}`);
  }
}