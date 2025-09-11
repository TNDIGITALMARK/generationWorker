import { storage } from '../../../firebase/firebaseAdmin';

export async function fetchImageFromFirebase(uid: string, fileName: string): Promise<Buffer> {
  try {
    console.log(`Fetching image from Firebase Storage: users/${uid}/images/${fileName}`);
    
    const bucket = storage.bucket();
    const filePath = `users/${uid}/images/${fileName}`;
    
    // Get file reference
    const file = bucket.file(filePath);
    
    // Check if file exists
    const [exists] = await file.exists();
    if (!exists) {
      throw new Error(`File not found in Firebase Storage: ${filePath}`);
    }
    
    // Download file as buffer
    const [buffer] = await file.download();
    
    console.log(`Successfully fetched image from Firebase. Size: ${buffer.length} bytes`);
    return buffer;
    
  } catch (error) {
    console.error(`Failed to fetch image from Firebase: ${(error as Error).message}`);
    throw new Error(`Firebase image fetch failed: ${(error as Error).message}`);
  }
}