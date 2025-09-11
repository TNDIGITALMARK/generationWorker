import { firebaseImageToComfyService } from '../services/firebaseImagetoComfy';

export interface SQSImageMessage {
  uid: string;
  fileName: string;
  taskType: 'img2vid' | 'txt2img';
}

export class AssetHandlerController {
  
  async processImageAsset(message: SQSImageMessage): Promise<string> {
    try {
      console.log(`Processing image asset for user: ${message.uid}, file: ${message.fileName}`);
      
      // Route to Firebase image to ComfyUI service
      const comfyFileName = await firebaseImageToComfyService.processImage(
        message.uid,
        message.fileName
      );
      
      console.log(`Image processed successfully. ComfyUI filename: ${comfyFileName}`);
      return comfyFileName;
      
    } catch (error) {
      console.error('Asset handler failed:', error);
      throw new Error(`Asset processing failed: ${(error as Error).message}`);
    }
  }
  
  async routeAssetRequest(taskType: string, message: SQSImageMessage): Promise<string> {
    switch (taskType) {
      case 'img2vid':
      case 'txt2img':
        return await this.processImageAsset(message);
      
      default:
        throw new Error(`Unknown task type: ${taskType}`);
    }
  }
}

export const assetHandlerController = new AssetHandlerController();