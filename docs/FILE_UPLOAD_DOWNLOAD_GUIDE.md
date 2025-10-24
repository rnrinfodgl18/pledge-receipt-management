# File Upload & Download Guide

## Complete Implementation for Uploading & Retrieving Files

---

## 📤 File Upload (Client → Server)

### 1. **HTML Form Upload**

```html
<form id="pledgePhotoForm" enctype="multipart/form-data">
  <input type="file" id="photoInput" accept="image/*" required>
  <button type="submit">Upload Photo</button>
</form>

<script>
document.getElementById('pledgePhotoForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  
  const file = document.getElementById('photoInput').files[0];
  const pledgeId = 1; // Replace with actual pledge ID
  const token = localStorage.getItem('token');
  
  const formData = new FormData();
  formData.append('file', file);
  
  try {
    const response = await fetch(
      `http://localhost:8000/pledges/${pledgeId}/upload-photo`,
      {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      }
    );
    
    const data = await response.json();
    if (response.ok) {
      alert('Photo uploaded successfully!');
      console.log('Photo path:', data.photo_path);
    } else {
      alert('Upload failed: ' + data.detail);
    }
  } catch (error) {
    console.error('Error:', error);
  }
});
</script>
```

### 2. **React File Upload Component**

```jsx
import React, { useState } from 'react';
import axios from 'axios';

function PledgePhotoUpload({ pledgeId, token, onSuccess }) {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [preview, setPreview] = useState(null);

  const handleFileSelect = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      // Validate file type
      if (!selectedFile.type.startsWith('image/')) {
        setError('Please select an image file');
        return;
      }
      
      // Validate file size (max 8MB)
      if (selectedFile.size > 8 * 1024 * 1024) {
        setError('File size exceeds 8MB limit');
        return;
      }
      
      setFile(selectedFile);
      setError(null);
      
      // Create preview
      const reader = new FileReader();
      reader.onloadend = () => setPreview(reader.result);
      reader.readAsDataURL(selectedFile);
    }
  };

  const handleUpload = async () => {
    if (!file) {
      setError('Please select a file');
      return;
    }

    setLoading(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post(
        `http://localhost:8000/pledges/${pledgeId}/upload-photo`,
        formData,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'multipart/form-data'
          }
        }
      );

      console.log('Upload successful:', response.data);
      if (onSuccess) {
        onSuccess(response.data.photo_path);
      }
      
      // Reset form
      setFile(null);
      setPreview(null);
    } catch (err) {
      setError(err.response?.data?.detail || 'Upload failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="upload-container">
      <h3>Upload Pledge Photo</h3>
      
      <div className="file-input-wrapper">
        <input
          type="file"
          accept="image/*"
          onChange={handleFileSelect}
          disabled={loading}
        />
      </div>

      {preview && (
        <div className="preview">
          <img src={preview} alt="Preview" style={{ maxWidth: '200px' }} />
        </div>
      )}

      {error && <div className="error">{error}</div>}

      <button onClick={handleUpload} disabled={!file || loading}>
        {loading ? 'Uploading...' : 'Upload'}
      </button>
    </div>
  );
}

export default PledgePhotoUpload;
```

### 3. **Vue.js Upload Component**

```vue
<template>
  <div class="upload-container">
    <h3>Upload Pledge Photo</h3>
    
    <input 
      type="file" 
      accept="image/*"
      @change="handleFileSelect"
      :disabled="loading"
    />

    <div v-if="preview" class="preview">
      <img :src="preview" alt="Preview" style="max-width: 200px;">
    </div>

    <div v-if="error" class="error">{{ error }}</div>

    <button @click="uploadFile" :disabled="!file || loading">
      {{ loading ? 'Uploading...' : 'Upload' }}
    </button>
  </div>
</template>

<script>
export default {
  props: ['pledgeId', 'token'],
  data() {
    return {
      file: null,
      preview: null,
      loading: false,
      error: null
    };
  },
  methods: {
    handleFileSelect(e) {
      const selectedFile = e.target.files[0];
      if (!selectedFile) return;

      // Validate
      if (!selectedFile.type.startsWith('image/')) {
        this.error = 'Please select an image file';
        return;
      }
      if (selectedFile.size > 8 * 1024 * 1024) {
        this.error = 'File size exceeds 8MB limit';
        return;
      }

      this.file = selectedFile;
      this.error = null;

      // Create preview
      const reader = new FileReader();
      reader.onloadend = () => this.preview = reader.result;
      reader.readAsDataURL(selectedFile);
    },

    async uploadFile() {
      if (!this.file) {
        this.error = 'Please select a file';
        return;
      }

      this.loading = true;
      const formData = new FormData();
      formData.append('file', this.file);

      try {
        const response = await fetch(
          `http://localhost:8000/pledges/${this.pledgeId}/upload-photo`,
          {
            method: 'POST',
            headers: {
              'Authorization': `Bearer ${this.token}`
            },
            body: formData
          }
        );

        if (response.ok) {
          const data = await response.json();
          this.$emit('success', data.photo_path);
          this.file = null;
          this.preview = null;
        } else {
          const error = await response.json();
          this.error = error.detail || 'Upload failed';
        }
      } catch (err) {
        this.error = 'Upload error: ' + err.message;
      } finally {
        this.loading = false;
      }
    }
  }
};
</script>
```

---

## 📥 Image Retrieval & Display

### 1. **Simple Image Tag**

```html
<!-- Direct URL from database -->
<img id="pledgePhoto" src="" alt="Pledge Photo">

<script>
async function loadPledgePhoto(pledgeId, token) {
  try {
    // Fetch pledge data
    const response = await fetch(
      `http://localhost:8000/pledges/${pledgeId}`,
      { headers: { 'Authorization': `Bearer ${token}` } }
    );
    
    const pledge = await response.json();
    
    // Set image source
    if (pledge.photo_path) {
      document.getElementById('pledgePhoto').src = 
        `http://localhost:8000/${pledge.photo_path}`;
    }
  } catch (error) {
    console.error('Error loading photo:', error);
  }
}

// Call when page loads
loadPledgePhoto(1, localStorage.getItem('token'));
</script>
```

### 2. **React Image Carousel**

```jsx
import React, { useEffect, useState } from 'react';

function PledgePhotoCarousel({ pledgeId, token }) {
  const [photos, setPhotos] = useState([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchPhotos = async () => {
      try {
        const response = await fetch(
          `http://localhost:8000/pledges/${pledgeId}`,
          { headers: { 'Authorization': `Bearer ${token}` } }
        );
        const pledge = await response.json();
        
        if (pledge.photo_path) {
          setPhotos([{
            path: pledge.photo_path,
            url: `http://localhost:8000/${pledge.photo_path}`
          }]);
        }
      } catch (error) {
        console.error('Error:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchPhotos();
  }, [pledgeId, token]);

  const goToPrevious = () => {
    setCurrentIndex((prev) => (prev - 1 + photos.length) % photos.length);
  };

  const goToNext = () => {
    setCurrentIndex((prev) => (prev + 1) % photos.length);
  };

  if (loading) return <div>Loading...</div>;
  if (photos.length === 0) return <div>No photos</div>;

  const currentPhoto = photos[currentIndex];

  return (
    <div className="carousel">
      <div className="main-image">
        <img 
          src={currentPhoto.url} 
          alt={`Pledge Photo ${currentIndex + 1}`}
          onError={(e) => e.target.src = '/placeholder.jpg'}
        />
      </div>
      
      <div className="controls">
        <button onClick={goToPrevious} disabled={photos.length <= 1}>
          ← Previous
        </button>
        <span>{currentIndex + 1} / {photos.length}</span>
        <button onClick={goToNext} disabled={photos.length <= 1}>
          Next →
        </button>
      </div>
    </div>
  );
}

export default PledgePhotoCarousel;
```

---

## 📊 API Endpoints for File Operations

### Upload Pledge Photo
```
POST /pledges/{pledge_id}/upload-photo

Headers:
  Authorization: Bearer <token>

Body:
  multipart/form-data
  file: <image file>

Response (200):
{
  "message": "Photo uploaded successfully",
  "photo_path": "uploads/pledge_photos/pledge_1_20251024_143022.png"
}
```

### Get Pledge with Photo
```
GET /pledges/{pledge_id}

Headers:
  Authorization: Bearer <token>

Response (200):
{
  "id": 1,
  "pledge_no": "GLD-2024-001",
  "photo_path": "uploads/pledge_photos/pledge_1_20251024_143022.png",
  ...
}
```

### Download Image
```
GET /uploads/pledge_photos/{filename}

Response: Image file (binary data)

Example:
GET /uploads/pledge_photos/pledge_1_20251024_143022.png
```

---

## 🖼️ Image Display with Loading State

### React Component with Loading & Error Handling

```jsx
function PledgeImage({ filePath, token }) {
  const [status, setStatus] = useState('loading'); // loading, success, error
  const [imageUrl, setImageUrl] = useState(null);

  useEffect(() => {
    if (!filePath) {
      setStatus('error');
      return;
    }

    const url = `http://localhost:8000/${filePath}`;
    setImageUrl(url);
    setStatus('loading');
  }, [filePath]);

  return (
    <div className="image-wrapper">
      {status === 'loading' && (
        <div className="skeleton">
          <div className="spinner"></div>
          <p>Loading image...</p>
        </div>
      )}

      {status === 'success' && (
        <img 
          src={imageUrl} 
          alt="Pledge"
          style={{ width: '100%', maxWidth: '500px' }}
        />
      )}

      {status === 'error' && (
        <div className="error-state">
          <p>Failed to load image</p>
          <img src="/placeholder.jpg" alt="Placeholder" />
        </div>
      )}

      <img
        src={imageUrl}
        alt="Pledge"
        onLoad={() => setStatus('success')}
        onError={() => setStatus('error')}
        style={{ display: 'none' }}
      />
    </div>
  );
}
```

---

## 🔐 Secure File Operations

### Upload with Validation

```javascript
async function uploadFileSecurely(pledgeId, file, token) {
  // Client-side validation
  const MAX_SIZE = 8 * 1024 * 1024; // 8MB
  const ALLOWED_TYPES = ['image/jpeg', 'image/png', 'image/gif', 'image/webp'];

  if (!ALLOWED_TYPES.includes(file.type)) {
    throw new Error('Invalid file type');
  }

  if (file.size > MAX_SIZE) {
    throw new Error('File too large');
  }

  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(
    `http://localhost:8000/pledges/${pledgeId}/upload-photo`,
    {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}` },
      body: formData
    }
  );

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Upload failed');
  }

  return response.json();
}
```

### Download with Authentication

```javascript
async function downloadImage(filePath, token) {
  const response = await fetch(
    `http://localhost:8000/${filePath}`,
    { headers: { 'Authorization': `Bearer ${token}` } }
  );

  if (!response.ok) {
    throw new Error('Download failed');
  }

  const blob = await response.blob();
  const url = window.URL.createObjectURL(blob);
  
  // Create download link
  const a = document.createElement('a');
  a.href = url;
  a.download = filePath.split('/').pop();
  document.body.appendChild(a);
  a.click();
  window.URL.revokeObjectURL(url);
  document.body.removeChild(a);
}
```

---

## 📱 Image Optimization

### Compress Image Before Upload

```javascript
async function compressImage(file, maxWidth = 800, maxHeight = 800) {
  return new Promise((resolve) => {
    const reader = new FileReader();
    
    reader.onload = (e) => {
      const img = new Image();
      
      img.onload = () => {
        const canvas = document.createElement('canvas');
        let width = img.width;
        let height = img.height;

        // Calculate new dimensions
        if (width > height) {
          if (width > maxWidth) {
            height = (height * maxWidth) / width;
            width = maxWidth;
          }
        } else {
          if (height > maxHeight) {
            width = (width * maxHeight) / height;
            height = maxHeight;
          }
        }

        canvas.width = width;
        canvas.height = height;
        
        const ctx = canvas.getContext('2d');
        ctx.drawImage(img, 0, 0, width, height);

        canvas.toBlob((blob) => {
          resolve(new File([blob], file.name, { type: 'image/jpeg' }));
        }, 'image/jpeg', 0.8);
      };
      
      img.src = e.target.result;
    };
    
    reader.readAsDataURL(file);
  });
}

// Usage
const compressedFile = await compressImage(selectedFile);
await uploadFileSecurely(pledgeId, compressedFile, token);
```

---

## 🌐 Production Deployment

### Environment Configuration

```javascript
// config.js
const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export function getImageUrl(filePath) {
  return `${API_URL}/${filePath}`;
}

// .env.development
REACT_APP_API_URL=http://localhost:8000

// .env.production
REACT_APP_API_URL=https://your-app.onrender.com
```

### CORS Configuration in .env (Production)
```
CORS_ORIGINS=https://yourdomain.com,https://app.yourdomain.com
```

---

## 🧪 Testing Checklist

- [ ] Upload image with valid format
- [ ] Upload image with size > 8MB (should fail)
- [ ] Upload with invalid format (should fail)
- [ ] Retrieve image after upload
- [ ] Display image in multiple browsers
- [ ] Test on mobile devices
- [ ] Test with slow network
- [ ] Test CORS in production
- [ ] Test image caching
- [ ] Test fallback for missing images

---

**Last Updated:** October 24, 2025  
**Status:** ✅ Production Ready
