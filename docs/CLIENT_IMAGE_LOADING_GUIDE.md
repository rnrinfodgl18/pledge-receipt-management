# Client-Side Image Loading Guide

## Overview

This guide explains how to retrieve and display uploaded images (pledge photos, company logos, ID proofs) on the client side from your FastAPI server.

---

## 📁 File Structure & Storage

### Server-Side Storage
```
project/
├── uploads/
│   ├── company_logos/       (Company logos)
│   ├── id_proofs/          (Customer ID proofs)
│   └── pledge_photos/      (Pledge photos)
```

### Access URLs
All files are served via the `/uploads` endpoint:
- **Local Development:** `http://localhost:8000/uploads/...`
- **Production (Render):** `https://your-app.onrender.com/uploads/...`

---

## 🔗 Image URL Construction

### Example Image Paths in Database
```
uploads/company_logos/company_1_20251024_120530.jpg
uploads/pledge_photos/pledge_123_20251024_143022.png
uploads/id_proofs/customer_5_20251024_095015.pdf
```

### Complete URLs
```
http://localhost:8000/uploads/company_logos/company_1_20251024_120530.jpg
http://localhost:8000/uploads/pledge_photos/pledge_123_20251024_143022.png
http://localhost:8000/uploads/id_proofs/customer_5_20251024_095015.pdf
```

---

## 💻 Client Implementation Examples

### 1. **HTML - Simple Image Tag**

```html
<!-- Pledge Photo -->
<img src="http://localhost:8000/uploads/pledge_photos/pledge_123_20251024_143022.png" 
     alt="Pledge Photo" 
     width="300" 
     height="300">

<!-- Company Logo -->
<img src="http://localhost:8000/uploads/company_logos/company_1_20251024_120530.jpg" 
     alt="Company Logo" 
     width="150" 
     height="150">
```

### 2. **JavaScript - Dynamic Image Loading**

```javascript
// Function to construct image URL
function getImageUrl(filePath, baseUrl = 'http://localhost:8000') {
  return `${baseUrl}/${filePath}`;
}

// Load pledge photo
const pledgePhotoUrl = getImageUrl('uploads/pledge_photos/pledge_123_20251024_143022.png');
document.getElementById('pledgeImage').src = pledgePhotoUrl;

// Load company logo
const logoUrl = getImageUrl('uploads/company_logos/company_1_20251024_120530.jpg');
document.getElementById('companyLogo').src = logoUrl;
```

### 3. **React Component - Image with Error Handling**

```jsx
import React, { useState } from 'react';

function ImageDisplay({ filePath, alt = 'Image', baseUrl = 'http://localhost:8000' }) {
  const [isLoading, setIsLoading] = useState(true);
  const [hasError, setHasError] = useState(false);

  const imageUrl = `${baseUrl}/${filePath}`;

  const handleLoadStart = () => setIsLoading(true);
  const handleLoadEnd = () => setIsLoading(false);
  const handleError = () => {
    setHasError(true);
    setIsLoading(false);
  };

  return (
    <div className="image-container">
      {isLoading && <p>Loading...</p>}
      {hasError && <p>Failed to load image</p>}
      <img
        src={imageUrl}
        alt={alt}
        onLoadStart={handleLoadStart}
        onLoad={handleLoadEnd}
        onError={handleError}
        style={{ display: isLoading || hasError ? 'none' : 'block' }}
      />
    </div>
  );
}

export default ImageDisplay;
```

### 4. **React - Fetch and Display Pledge with Photo**

```jsx
import React, { useEffect, useState } from 'react';
import axios from 'axios';

function PledgeDetail({ pledgeId, token }) {
  const [pledge, setPledge] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchPledge = async () => {
      try {
        const response = await axios.get(
          `http://localhost:8000/pledges/${pledgeId}`,
          {
            headers: { Authorization: `Bearer ${token}` }
          }
        );
        setPledge(response.data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchPledge();
  }, [pledgeId, token]);

  if (loading) return <p>Loading...</p>;
  if (error) return <p>Error: {error}</p>;
  if (!pledge) return <p>No pledge found</p>;

  const imageUrl = pledge.photo_path 
    ? `http://localhost:8000/${pledge.photo_path}`
    : null;

  return (
    <div className="pledge-card">
      <h2>Pledge #{pledge.pledge_no}</h2>
      
      {imageUrl && (
        <div className="pledge-photo">
          <img 
            src={imageUrl} 
            alt={`Pledge ${pledge.pledge_no}`}
            onError={(e) => e.target.style.display = 'none'}
            style={{ maxWidth: '300px', maxHeight: '300px' }}
          />
        </div>
      )}
      
      <div className="pledge-details">
        <p><strong>Customer:</strong> {pledge.customer.customer_name}</p>
        <p><strong>Amount:</strong> ₹{pledge.amount}</p>
        <p><strong>Status:</strong> {pledge.status}</p>
      </div>
    </div>
  );
}

export default PledgeDetail;
```

### 5. **Vue.js - Image Loading**

```vue
<template>
  <div class="pledge-container">
    <h2>Pledge Details</h2>
    
    <!-- Display pledge photo -->
    <div v-if="pledge.photo_path" class="photo-section">
      <img 
        :src="getImageUrl(pledge.photo_path)" 
        :alt="`Pledge ${pledge.pledge_no}`"
        @error="handleImageError"
        class="pledge-photo"
      />
    </div>

    <!-- Pledge details -->
    <div class="details">
      <p><strong>Pledge No:</strong> {{ pledge.pledge_no }}</p>
      <p><strong>Customer:</strong> {{ pledge.customer.customer_name }}</p>
      <p><strong>Amount:</strong> ₹{{ pledge.amount }}</p>
      <p><strong>Status:</strong> {{ pledge.status }}</p>
    </div>
  </div>
</template>

<script>
export default {
  name: 'PledgeDetail',
  data() {
    return {
      pledge: null,
      baseUrl: 'http://localhost:8000'
    };
  },
  methods: {
    getImageUrl(filePath) {
      return `${this.baseUrl}/${filePath}`;
    },
    handleImageError() {
      console.error('Failed to load image');
    },
    async fetchPledge(pledgeId) {
      try {
        const response = await fetch(
          `${this.baseUrl}/pledges/${pledgeId}`,
          {
            headers: {
              'Authorization': `Bearer ${this.$store.state.token}`
            }
          }
        );
        this.pledge = await response.json();
      } catch (error) {
        console.error('Error fetching pledge:', error);
      }
    }
  },
  mounted() {
    this.fetchPledge(this.$route.params.pledgeId);
  }
};
</script>

<style scoped>
.pledge-photo {
  max-width: 300px;
  max-height: 300px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  margin: 20px 0;
}
</style>
```

### 6. **Angular - Image Loading Service**

```typescript
// image.service.ts
import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class ImageService {
  private baseUrl = 'http://localhost:8000';

  constructor(private http: HttpClient) { }

  getImageUrl(filePath: string): string {
    return `${this.baseUrl}/${filePath}`;
  }

  fetchPledge(pledgeId: number, token: string): Observable<any> {
    return this.http.get(
      `${this.baseUrl}/pledges/${pledgeId}`,
      {
        headers: { Authorization: `Bearer ${token}` }
      }
    );
  }
}

// pledge-detail.component.ts
import { Component, OnInit } from '@angular/core';
import { ImageService } from './image.service';
import { ActivatedRoute } from '@angular/router';

@Component({
  selector: 'app-pledge-detail',
  template: `
    <div class="pledge-container">
      <h2>Pledge Details</h2>
      
      <img 
        *ngIf="pledge.photo_path" 
        [src]="getImageUrl(pledge.photo_path)" 
        [alt]="'Pledge ' + pledge.pledge_no"
        (error)="handleImageError()"
        class="pledge-photo"
      />
      
      <div class="details">
        <p><strong>Pledge No:</strong> {{ pledge.pledge_no }}</p>
        <p><strong>Customer:</strong> {{ pledge.customer.customer_name }}</p>
        <p><strong>Amount:</strong> ₹{{ pledge.amount }}</p>
      </div>
    </div>
  `
})
export class PledgeDetailComponent implements OnInit {
  pledge: any;

  constructor(
    private imageService: ImageService,
    private route: ActivatedRoute
  ) { }

  ngOnInit() {
    this.route.params.subscribe(params => {
      this.imageService.fetchPledge(params['id'], this.getToken())
        .subscribe(data => this.pledge = data);
    });
  }

  getImageUrl(filePath: string): string {
    return this.imageService.getImageUrl(filePath);
  }

  handleImageError() {
    console.error('Failed to load image');
  }

  private getToken(): string {
    return localStorage.getItem('token') || '';
  }
}
```

---

## 🔒 Security Considerations

### 1. **CORS Configuration**
In production, ensure CORS is properly configured in `.env`:
```
CORS_ORIGINS=https://yourdomain.com,https://app.yourdomain.com
```

### 2. **Environment-Based URLs**
```javascript
// Development
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Production (Render)
// API_BASE_URL = https://your-app.onrender.com

const imageUrl = `${API_BASE_URL}/${filePath}`;
```

### 3. **Authentication for Protected Images**
If images should only be accessible to authenticated users:

```javascript
// Fetch image with authentication
async function fetchImageWithAuth(filePath, token) {
  const response = await fetch(
    `http://localhost:8000/${filePath}`,
    {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    }
  );
  
  if (!response.ok) {
    throw new Error('Unauthorized or image not found');
  }
  
  const blob = await response.blob();
  return URL.createObjectURL(blob);
}

// Usage in img tag
async function loadImage(filePath, token) {
  const imageUrl = await fetchImageWithAuth(filePath, token);
  document.getElementById('image').src = imageUrl;
}
```

---

## 🎨 Advanced: Image Gallery

### React Image Gallery Component

```jsx
import React, { useEffect, useState } from 'react';
import axios from 'axios';

function PledgeGallery({ pledgeId, token }) {
  const [images, setImages] = useState([]);
  const [selectedImage, setSelectedImage] = useState(null);

  useEffect(() => {
    const fetchPledge = async () => {
      try {
        const response = await axios.get(
          `http://localhost:8000/pledges/${pledgeId}`,
          { headers: { Authorization: `Bearer ${token}` } }
        );
        
        if (response.data.photo_path) {
          setImages([{
            url: `http://localhost:8000/${response.data.photo_path}`,
            title: response.data.pledge_no
          }]);
          setSelectedImage(0);
        }
      } catch (error) {
        console.error('Error loading images:', error);
      }
    };

    fetchPledge();
  }, [pledgeId, token]);

  return (
    <div className="gallery">
      {images.length > 0 && (
        <>
          <div className="main-image">
            <img 
              src={images[selectedImage]?.url} 
              alt={images[selectedImage]?.title}
              style={{ maxWidth: '500px', maxHeight: '500px' }}
            />
          </div>
          <div className="thumbnails">
            {images.map((img, idx) => (
              <img
                key={idx}
                src={img.url}
                alt={img.title}
                onClick={() => setSelectedImage(idx)}
                className={selectedImage === idx ? 'active' : ''}
                style={{ 
                  width: '80px', 
                  height: '80px', 
                  cursor: 'pointer',
                  opacity: selectedImage === idx ? 1 : 0.6
                }}
              />
            ))}
          </div>
        </>
      )}
    </div>
  );
}

export default PledgeGallery;
```

---

## 📊 API Response Example

### GET /pledges/{pledge_id}
```json
{
  "id": 1,
  "pledge_no": "GLD-2024-001",
  "company_id": 1,
  "customer_id": 5,
  "scheme_id": 1,
  "amount": 50000.00,
  "weight": 2.5,
  "status": "active",
  "photo_path": "uploads/pledge_photos/pledge_1_20251024_143022.png",
  "items": [...],
  "created_at": "2025-10-24T14:30:22",
  "updated_at": "2025-10-24T14:30:22"
}
```

---

## 🚀 Environment-Specific Setup

### Development (Local)
```javascript
// .env.local
REACT_APP_API_URL=http://localhost:8000
```

### Production (Render)
```javascript
// .env.production
REACT_APP_API_URL=https://your-app.onrender.com
```

### Configuration Hook (React)
```javascript
const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export function useImageUrl(filePath) {
  return `${API_URL}/${filePath}`;
}

// Usage
function Component({ filePath }) {
  const imageUrl = useImageUrl(filePath);
  return <img src={imageUrl} alt="Image" />;
}
```

---

## ⚠️ Common Issues & Solutions

| Issue | Cause | Solution |
|-------|-------|----------|
| Image shows broken link | Wrong file path | Verify path from database API response |
| CORS error | Frontend domain not in CORS_ORIGINS | Update CORS_ORIGINS in .env |
| 404 Not Found | File path incorrect | Check `/uploads` endpoint is mounted |
| 403 Forbidden | Authentication required | Add Bearer token to request headers |
| Slow loading | Large image file | Compress images before upload |

---

## 🔧 Troubleshooting Guide

### 1. **Verify Image Exists**
```bash
# Check if file exists on server
curl -I http://localhost:8000/uploads/pledge_photos/pledge_1_20251024_143022.png
```

### 2. **Check CORS Configuration**
```javascript
// In browser console
fetch('http://localhost:8000/uploads/pledge_photos/pledge_1_20251024_143022.png')
  .then(r => r.blob())
  .then(b => console.log('Success:', b.size))
  .catch(e => console.error('Error:', e));
```

### 3. **Verify Database Path**
```bash
# Get pledge details to confirm photo_path
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/pledges/1
```

---

## 📱 Mobile Optimization

### Responsive Image Loading
```html
<picture>
  <source media="(max-width: 600px)" srcset="image-small.jpg">
  <source media="(max-width: 1024px)" srcset="image-medium.jpg">
  <img src="http://localhost:8000/uploads/pledge_photos/pledge_1_20251024_143022.png" 
       alt="Pledge Photo" 
       style="width: 100%; height: auto;">
</picture>
```

### React Responsive Component
```jsx
function ResponsiveImage({ filePath }) {
  const baseUrl = 'http://localhost:8000';
  
  return (
    <img 
      src={`${baseUrl}/${filePath}`}
      alt="Image"
      style={{
        width: '100%',
        maxWidth: '500px',
        height: 'auto',
        borderRadius: '8px'
      }}
    />
  );
}
```

---

## 💡 Best Practices

✅ **Always verify image path** from API response  
✅ **Handle loading states** with spinners/placeholders  
✅ **Add error handling** with fallback images  
✅ **Use HTTPS in production** (automatic on Render)  
✅ **Cache images** in browser where appropriate  
✅ **Optimize image sizes** before upload  
✅ **Validate CORS settings** in production  
✅ **Test image loading** on real network conditions  

---

## 📚 Related Documentation

- [FastAPI Static Files](https://fastapi.tiangolo.com/en/tutorial/static-files/)
- [CORS in FastAPI](https://fastapi.tiangolo.com/tutorial/cors/)
- [Render Deployment Guide](./DEPLOYMENT_READY.md)

---

**Last Updated:** October 24, 2025  
**Status:** ✅ Production Ready
