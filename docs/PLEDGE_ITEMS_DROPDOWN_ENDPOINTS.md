# 📋 Pledge Items - Dropdown/Select Endpoints

## Overview

Three new endpoints to get distinct lists of jewel attributes from pledge items. Perfect for frontend dropdown/select options!

---

## 🎯 Endpoints

### 1. Get Jewel Designs

**URL:** `GET /pledges/designs/list`

**Authentication:** Required (Bearer Token)

**Description:** Returns a list of all distinct jewel designs used in pledges

**Example Response:**
```json
[
  "Ankle",
  "Bracelet",
  "Chain",
  "Earring",
  "Necklace",
  "Pendant",
  "Ring",
  "Waist Chain"
]
```

---

### 2. Get Jewel Conditions

**URL:** `GET /pledges/conditions/list`

**Authentication:** Required (Bearer Token)

**Description:** Returns a list of all distinct jewel conditions from pledge items

**Example Response:**
```json
[
  "Excellent",
  "Fair",
  "Good",
  "Poor",
  "Very Good"
]
```

---

### 3. Get Stone Types

**URL:** `GET /pledges/stone-types/list`

**Authentication:** Required (Bearer Token)

**Description:** Returns a list of all distinct stone types used in pledges

**Example Response:**
```json
[
  "Diamond",
  "Emerald",
  "Pearl",
  "Ruby",
  "Sapphire",
  "Semi-Precious"
]
```

---

## 📱 How to Use in Frontend

### React Example - Dropdown Select

```javascript
import { useState, useEffect } from 'react';

function PledgeForm({ token }) {
  const [designs, setDesigns] = useState([]);
  const [conditions, setConditions] = useState([]);
  const [stoneTypes, setStoneTypes] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Fetch all dropdown data
    async function fetchDropdownData() {
      try {
        const headers = { 'Authorization': `Bearer ${token}` };
        
        const [designsRes, conditionsRes, stoneRes] = await Promise.all([
          fetch('http://localhost:8000/pledges/designs/list', { headers }),
          fetch('http://localhost:8000/pledges/conditions/list', { headers }),
          fetch('http://localhost:8000/pledges/stone-types/list', { headers })
        ]);

        setDesigns(await designsRes.json());
        setConditions(await conditionsRes.json());
        setStoneTypes(await stoneRes.json());
        setLoading(false);
      } catch (error) {
        console.error('Error fetching dropdown data:', error);
        setLoading(false);
      }
    }

    fetchDropdownData();
  }, [token]);

  if (loading) return <div>Loading...</div>;

  return (
    <form>
      <div>
        <label>Jewel Design</label>
        <select>
          <option value="">Select Design</option>
          {designs.map(design => (
            <option key={design} value={design}>{design}</option>
          ))}
        </select>
      </div>

      <div>
        <label>Condition</label>
        <select>
          <option value="">Select Condition</option>
          {conditions.map(condition => (
            <option key={condition} value={condition}>{condition}</option>
          ))}
        </select>
      </div>

      <div>
        <label>Stone Type</label>
        <select>
          <option value="">Select Stone Type</option>
          {stoneTypes.map(stone => (
            <option key={stone} value={stone}>{stone}</option>
          ))}
        </select>
      </div>
    </form>
  );
}

export default PledgeForm;
```

### Vue.js Example

```vue
<template>
  <div v-if="loading">Loading...</div>
  <form v-else>
    <div>
      <label>Jewel Design</label>
      <select v-model="selectedDesign">
        <option value="">Select Design</option>
        <option v-for="design in designs" :key="design" :value="design">
          {{ design }}
        </option>
      </select>
    </div>

    <div>
      <label>Condition</label>
      <select v-model="selectedCondition">
        <option value="">Select Condition</option>
        <option v-for="condition in conditions" :key="condition" :value="condition">
          {{ condition }}
        </option>
      </select>
    </div>

    <div>
      <label>Stone Type</label>
      <select v-model="selectedStone">
        <option value="">Select Stone Type</option>
        <option v-for="stone in stoneTypes" :key="stone" :value="stone">
          {{ stone }}
        </option>
      </select>
    </div>
  </form>
</template>

<script>
import axios from 'axios';

export default {
  data() {
    return {
      designs: [],
      conditions: [],
      stoneTypes: [],
      selectedDesign: '',
      selectedCondition: '',
      selectedStone: '',
      loading: true
    }
  },
  mounted() {
    this.fetchData();
  },
  methods: {
    async fetchData() {
      const headers = {
        'Authorization': `Bearer ${this.$store.state.token}`
      };

      try {
        const [designRes, condRes, stoneRes] = await Promise.all([
          axios.get('http://localhost:8000/pledges/designs/list', { headers }),
          axios.get('http://localhost:8000/pledges/conditions/list', { headers }),
          axios.get('http://localhost:8000/pledges/stone-types/list', { headers })
        ]);

        this.designs = designRes.data;
        this.conditions = condRes.data;
        this.stoneTypes = stoneRes.data;
        this.loading = false;
      } catch (error) {
        console.error('Error:', error);
        this.loading = false;
      }
    }
  }
}
</script>
```

### JavaScript (Vanilla) Example

```javascript
// Fetch dropdown data
async function loadDropdownOptions() {
  const token = localStorage.getItem('token');
  const headers = { 'Authorization': `Bearer ${token}` };

  try {
    // Fetch all data
    const [designs, conditions, stones] = await Promise.all([
      fetch('http://localhost:8000/pledges/designs/list', { headers })
        .then(r => r.json()),
      fetch('http://localhost:8000/pledges/conditions/list', { headers })
        .then(r => r.json()),
      fetch('http://localhost:8000/pledges/stone-types/list', { headers })
        .then(r => r.json())
    ]);

    // Populate design dropdown
    const designSelect = document.getElementById('design-select');
    designs.forEach(design => {
      const option = document.createElement('option');
      option.value = design;
      option.textContent = design;
      designSelect.appendChild(option);
    });

    // Populate condition dropdown
    const conditionSelect = document.getElementById('condition-select');
    conditions.forEach(condition => {
      const option = document.createElement('option');
      option.value = condition;
      option.textContent = condition;
      conditionSelect.appendChild(option);
    });

    // Populate stone type dropdown
    const stoneSelect = document.getElementById('stone-select');
    stones.forEach(stone => {
      const option = document.createElement('option');
      option.value = stone;
      option.textContent = stone;
      stoneSelect.appendChild(option);
    });
  } catch (error) {
    console.error('Error loading dropdowns:', error);
  }
}

// Call on page load
window.addEventListener('DOMContentLoaded', loadDropdownOptions);
```

### Angular Example

```typescript
import { Component, OnInit } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';

@Component({
  selector: 'app-pledge-form',
  templateUrl: './pledge-form.component.html'
})
export class PledgeFormComponent implements OnInit {
  designs: string[] = [];
  conditions: string[] = [];
  stoneTypes: string[] = [];
  loading = true;
  token = localStorage.getItem('token');

  constructor(private http: HttpClient) {}

  ngOnInit() {
    this.loadDropdowns();
  }

  loadDropdowns() {
    const headers = new HttpHeaders({
      'Authorization': `Bearer ${this.token}`
    });

    Promise.all([
      this.http.get<string[]>('http://localhost:8000/pledges/designs/list', 
        { headers }).toPromise(),
      this.http.get<string[]>('http://localhost:8000/pledges/conditions/list', 
        { headers }).toPromise(),
      this.http.get<string[]>('http://localhost:8000/pledges/stone-types/list', 
        { headers }).toPromise()
    ]).then(([designs, conditions, stones]) => {
      this.designs = designs;
      this.conditions = conditions;
      this.stoneTypes = stones;
      this.loading = false;
    });
  }
}
```

---

## 🧪 Testing with cURL

```bash
# Get Designs
curl -X GET http://localhost:8000/pledges/designs/list \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"

# Get Conditions
curl -X GET http://localhost:8000/pledges/conditions/list \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"

# Get Stone Types
curl -X GET http://localhost:8000/pledges/stone-types/list \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

---

## 🧪 Testing in Swagger UI

1. **Login to Swagger**
   - Click green "Authorize" button
   - Enter credentials
   - Click "Authorize"

2. **Find the endpoint**
   - Go to "pledges" section
   - Find "GET /pledges/designs/list"
   - Find "GET /pledges/conditions/list"
   - Find "GET /pledges/stone-types/list"

3. **Click "Try it out"**
   - Click "Execute"
   - See the response with all available options

---

## 📊 Response Format

All three endpoints return the same format:

```json
[
  "Option 1",
  "Option 2",
  "Option 3",
  "Option 4"
]
```

**Features:**
- ✅ Already sorted alphabetically
- ✅ No duplicates (distinct values)
- ✅ Null and empty strings filtered out
- ✅ Ready to use in dropdowns
- ✅ No pagination needed

---

## 🔧 Implementation Details

### Database Query
```sql
-- Get distinct jewel designs
SELECT DISTINCT jewel_design 
FROM pledge_items 
WHERE jewel_design IS NOT NULL 
  AND jewel_design != '' 
ORDER BY jewel_design;

-- Similar for conditions and stone_types
```

### SQLAlchemy Query
```python
# Example for designs
designs = db.query(PledgeItemsModel.jewel_design).filter(
    PledgeItemsModel.jewel_design.isnot(None),
    PledgeItemsModel.jewel_design != ""
).distinct().order_by(PledgeItemsModel.jewel_design).all()
```

---

## 💡 Use Cases

### 1. Create Pledge Form
```
Select Design → Select Condition → Select Stone Type
   (dropdown)      (dropdown)         (dropdown)
```

### 2. Search/Filter Pledges
```
Filter by Design: [Necklace]
Filter by Condition: [Good]
Filter by Stone: [Diamond]
```

### 3. Reports
```
Pledge Items by Design
Pledge Items by Condition
Pledge Items by Stone Type
```

### 4. Data Analysis
```
Most common designs
Most common conditions
Most common stones
```

---

## 📈 Performance

- **Query Type:** DISTINCT (fast, indexed)
- **Result Size:** Small (typically < 100 items)
- **Caching:** Suitable for client-side caching
- **Frequency:** Can be loaded once on app startup

---

## 🔒 Security

✅ **Authentication Required** - All endpoints require valid JWT token  
✅ **Authorization Checked** - User must be authenticated  
✅ **No Sensitive Data** - Returns only public field values  
✅ **Read-Only** - GET requests, no data modification  

---

## 📝 Frontend Best Practices

### 1. Cache the Results
```javascript
// Store in localStorage or state management
localStorage.setItem('designs', JSON.stringify(designs));
```

### 2. Load on App Startup
```javascript
// Load once when app starts, not every time user opens a form
componentDidMount() {
  if (!this.state.designsLoaded) {
    this.loadDesigns();
  }
}
```

### 3. Handle Errors
```javascript
try {
  const data = await fetch(...).then(r => r.json());
} catch (error) {
  console.error('Failed to load options', error);
  // Show fallback UI or predefined list
}
```

### 4. Show Loading State
```javascript
{loading ? <Spinner /> : <select>{options}</select>}
```

---

## 🚀 Deployment

No special configuration needed for deployment:
- ✅ Works on Render automatically
- ✅ No database migrations needed
- ✅ No new environment variables
- ✅ Ready for production

---

## 📋 API Summary

| Endpoint | Method | Returns | Use For |
|----------|--------|---------|---------|
| `/pledges/designs/list` | GET | Array of strings | Jewel design dropdown |
| `/pledges/conditions/list` | GET | Array of strings | Condition dropdown |
| `/pledges/stone-types/list` | GET | Array of strings | Stone type dropdown |

---

## ✅ Verification Checklist

- [x] All three endpoints added
- [x] Results are distinct
- [x] Results are sorted
- [x] Null/empty values filtered
- [x] Authentication required
- [x] Ready for production

---

**Status:** ✅ Production Ready  
**Last Updated:** October 24, 2025  
**Version:** 1.0
