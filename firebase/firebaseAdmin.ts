import admin from 'firebase-admin';
import dotenv from 'dotenv';

dotenv.config();

let firebaseApp: admin.app.App;
let db: admin.firestore.Firestore;

export function initializeFirebase(): { app: admin.app.App; db: admin.firestore.Firestore } {
  if (firebaseApp) {
    return { app: firebaseApp, db };
  }

  const serviceAccount = {
    type: process.env.FIREBASE_TYPE,
    project_id: process.env.FIREBASE_PROJECT_ID,
    private_key_id: process.env.FIREBASE_PRIVATE_KEY_ID,
    private_key: process.env.FIREBASE_PRIVATE_KEY?.replace(/\\n/g, '\n'),
    client_email: process.env.FIREBASE_CLIENT_EMAIL,
    client_id: process.env.FIREBASE_CLIENT_ID,
    auth_uri: process.env.FIREBASE_AUTH_URI,
    token_uri: process.env.FIREBASE_TOKEN_URI,
    auth_provider_x509_cert_url: process.env.FIREBASE_AUTH_PROVIDER_X509_CERT_URL,
    client_x509_cert_url: process.env.FIREBASE_CLIENT_X509_CERT_URL,
    universe_domain: process.env.FIREBASE_UNIVERSE_DOMAIN
  };

  firebaseApp = admin.initializeApp({
    credential: admin.credential.cert(serviceAccount as admin.ServiceAccount)
  });

  db = admin.firestore();
  
  console.log('Firebase Admin initialized successfully');
  return { app: firebaseApp, db };
}

export async function testFirebaseConnection(): Promise<boolean> {
  try {
    if (!db) {
      throw new Error('Firebase not initialized');
    }
    await db.collection('health').doc('test').get();
    return true;
  } catch (error) {
    console.error('Firebase connection test failed:', error);
    return false;
  }
}

export { db, firebaseApp };