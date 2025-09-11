import { fetchImageFromFirebase } from './firebaseImagetoComfy/fetchImageFirebase';
import { saveImageToComfy } from './firebaseImagetoComfy/saveImageToComfy';
import { provisionFileName } from './firebaseImagetoComfy/provisionFileName';

export class FirebaseImageToComfyService {
  
  async processImage(uid: string, fileName: string): Promise<string> {
    try {
      console.log(`Starting Firebase to ComfyUI image processing for user: ${uid}, file: ${fileName}`);
      
      // Step 1: Fetch image from Firebase Storage
      const imageBuffer = await fetchImageFromFirebase(uid, fileName);
      
      // Step 2: Save image to ComfyUI input directory
      const comfyFileName = await saveImageToComfy(imageBuffer, fileName);
      
      // Step 3: Provision and return the filename for ComfyUI workflow
      const provisionedFileName = provisionFileName(comfyFileName);
      
      console.log(`Image processing completed successfully. Final filename: ${provisionedFileName}`);
      return provisionedFileName;
      
    } catch (error) {
      console.error('Firebase to ComfyUI processing failed:', error);
      throw new Error(`Image processing failed: ${(error as Error).message}`);
    }
  }
}

export const firebaseImageToComfyService = new FirebaseImageToComfyService();