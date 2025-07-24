from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import requests
import os
from pymongo import MongoClient
from datetime import datetime
import uuid
import uvicorn

app = FastAPI()

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB connection
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
client = MongoClient(MONGO_URL)
db = client.tourism_app

# Pydantic models
class UserPreference(BaseModel):
    id: Optional[str] = None
    name: str
    email: str
    preferred_categories: List[str]
    preferred_departments: List[str]
    age_range: str
    travel_style: str
    
class UserInteraction(BaseModel):
    id: Optional[str] = None
    user_id: str
    destination_rnt: str
    action: str  # 'view', 'like', 'save'
    timestamp: Optional[datetime] = None

class TourismDestination(BaseModel):
    rnt: str
    categoria: str
    subcategoria: str
    nomdep: str
    nombre_muni: str
    razon_social: str
    habitaciones: Optional[int] = None
    camas: Optional[int] = None
    empleados: Optional[int] = None

# API endpoints
@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/api/destinations", response_model=List[Dict[str, Any]])
async def get_destinations(department: Optional[str] = None, category: Optional[str] = None, limit: int = 50):
    """Get tourism destinations from Colombian RNT API filtered for Boyacá and Cundinamarca"""
    try:
        # Fetch data from Colombian government API with higher limit to ensure we get enough data
        url = "https://www.datos.gov.co/resource/jqjy-rhzv.json"
        params = {'$limit': 2000}  # Get more data to filter from
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        all_destinations = response.json()
        
        # Filter for Boyacá and Cundinamarca (corrected department names without accents)
        target_departments = ['BOYACA', 'CUNDINAMARCA']
        filtered_destinations = []
        
        for dest in all_destinations:
            dept_name = dest.get('nomdep', '').strip().upper()
            
            # Check if destination is in our target departments
            if dept_name in target_departments:
                # Additional filtering by specific department if requested
                if department:
                    requested_dept = department.strip().upper()
                    # Handle both with and without accents
                    if requested_dept in ['BOYACÁ', 'BOYACA'] and dept_name != 'BOYACA':
                        continue
                    elif requested_dept == 'CUNDINAMARCA' and dept_name != 'CUNDINAMARCA':
                        continue
                
                # Filter by category if specified
                if category:
                    dest_category = dest.get('categoria', '').lower()
                    if category.lower() not in dest_category:
                        continue
                
                # Clean and enrich destination data
                processed_dest = process_destination_data(dest)
                filtered_destinations.append(processed_dest)
        
        # Sort by municipality and limit results
        filtered_destinations.sort(key=lambda x: (x.get('nomdep', ''), x.get('nombre_muni', '')))
        
        return filtered_destinations[:limit]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching destinations: {str(e)}")

def process_destination_data(destination):
    """Process and enrich destination data for better presentation"""
    processed = destination.copy()
    
    # Ensure numeric fields are properly typed
    numeric_fields = ['habitaciones', 'camas', 'empleados']
    for field in numeric_fields:
        if field in processed and processed[field]:
            try:
                processed[field] = int(float(processed[field]))
            except (ValueError, TypeError):
                processed[field] = None
    
    # Add department display name with proper accent
    if processed.get('nomdep') == 'BOYACA':
        processed['department_display'] = 'Boyacá'
    elif processed.get('nomdep') == 'CUNDINAMARCA':
        processed['department_display'] = 'Cundinamarca'
    
    # Clean and format text fields
    text_fields = ['razon_social', 'categoria', 'subcategoria', 'nombre_muni']
    for field in text_fields:
        if field in processed and processed[field]:
            processed[field] = processed[field].strip()
    
    # Add location string for easy display
    processed['location'] = f"{processed.get('nombre_muni', '')}, {processed.get('department_display', processed.get('nomdep', ''))}"
    
    # Add category description for better UX
    category_descriptions = {
        'ALOJAMIENTO HOTELERO': 'Hoteles y hospedajes',
        'ALOJAMIENTO RURAL': 'Turismo rural y ecológico',
        'AGENCIA DE VIAJES': 'Servicios de viaje y turismo',
        'GUÍA DE TURISMO': 'Guías turísticos profesionales',
        'TRANSPORTE TURÍSTICO': 'Transporte especializado'
    }
    
    processed['category_description'] = category_descriptions.get(
        processed.get('categoria', ''), 
        processed.get('categoria', '')
    )
    
    return processed

@app.post("/api/users/preferences")
async def save_user_preferences(preferences: UserPreference):
    """Save user preferences"""
    try:
        if not preferences.id:
            preferences.id = str(uuid.uuid4())
        
        user_data = preferences.dict()
        user_data['created_at'] = datetime.now()
        
        # Update or insert user preferences
        db.user_preferences.replace_one(
            {"id": preferences.id},
            user_data,
            upsert=True
        )
        
        return {"message": "Preferences saved successfully", "user_id": preferences.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving preferences: {str(e)}")

@app.post("/api/users/interactions")
async def track_user_interaction(interaction: UserInteraction):
    """Track user interactions with destinations"""
    try:
        if not interaction.id:
            interaction.id = str(uuid.uuid4())
        
        interaction.timestamp = datetime.now()
        
        interaction_data = interaction.dict()
        db.user_interactions.insert_one(interaction_data)
        
        return {"message": "Interaction tracked successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error tracking interaction: {str(e)}")

@app.get("/api/recommendations/{user_id}")
async def get_user_recommendations(user_id: str, limit: int = 10):
    """Get personalized recommendations using collaborative filtering"""
    try:
        # Get user preferences
        user_prefs = db.user_preferences.find_one({"id": user_id})
        if not user_prefs:
            raise HTTPException(status_code=404, detail="User preferences not found")
        
        # Get user interactions
        user_interactions = list(db.user_interactions.find({"user_id": user_id}))
        user_liked_destinations = [i['destination_rnt'] for i in user_interactions if i['action'] == 'like']
        
        # Find similar users (collaborative filtering)
        similar_users = []
        all_users = list(db.user_preferences.find({"id": {"$ne": user_id}}))
        
        for other_user in all_users:
            # Calculate similarity based on preferences
            similarity_score = 0
            
            # Department preference similarity
            common_departments = set(user_prefs['preferred_departments']) & set(other_user['preferred_departments'])
            similarity_score += len(common_departments) * 2
            
            # Category preference similarity  
            common_categories = set(user_prefs['preferred_categories']) & set(other_user['preferred_categories'])
            similarity_score += len(common_categories) * 2
            
            # Age and travel style similarity
            if user_prefs['age_range'] == other_user['age_range']:
                similarity_score += 1
            if user_prefs['travel_style'] == other_user['travel_style']:
                similarity_score += 1
                
            if similarity_score > 0:
                similar_users.append((other_user['id'], similarity_score))
        
        # Sort by similarity
        similar_users.sort(key=lambda x: x[1], reverse=True)
        
        # Get destinations liked by similar users
        recommended_destinations = []
        for similar_user_id, _ in similar_users[:5]:  # Top 5 similar users
            similar_user_interactions = list(db.user_interactions.find({
                "user_id": similar_user_id,
                "action": "like"
            }))
            
            for interaction in similar_user_interactions:
                if interaction['destination_rnt'] not in user_liked_destinations:
                    recommended_destinations.append(interaction['destination_rnt'])
        
        # Remove duplicates and limit
        recommended_destinations = list(set(recommended_destinations))[:limit]
        
        # Fetch full destination data
        if recommended_destinations:
            url = "https://www.datos.gov.co/resource/jqjy-rhzv.json"
            response = requests.get(url, params={"$limit": 1000})
            all_destinations = response.json()
            
            recommendations = [
                dest for dest in all_destinations 
                if dest.get('rnt') in recommended_destinations
            ]
        else:
            # Fallback: recommend based on user preferences
            recommendations = await get_destinations(
                department=user_prefs['preferred_departments'][0] if user_prefs['preferred_departments'] else None,
                category=user_prefs['preferred_categories'][0] if user_prefs['preferred_categories'] else None,
                limit=limit
            )
        
        return recommendations
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating recommendations: {str(e)}")

@app.get("/api/analytics/popular-destinations")
async def get_popular_destinations(limit: int = 10):
    """Get most popular destinations based on user interactions"""
    try:
        pipeline = [
            {"$match": {"action": {"$in": ["like", "view"]}}},
            {"$group": {"_id": "$destination_rnt", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": limit}
        ]
        
        popular_destinations = list(db.user_interactions.aggregate(pipeline))
        
        # Fetch full destination data
        destination_rnts = [item['_id'] for item in popular_destinations]
        if destination_rnts:
            url = "https://www.datos.gov.co/resource/jqjy-rhzv.json"
            response = requests.get(url, params={"$limit": 1000})
            all_destinations = response.json()
            
            result = []
            for item in popular_destinations:
                dest = next((d for d in all_destinations if d.get('rnt') == item['_id']), None)
                if dest:
                    dest['interaction_count'] = item['count']
                    result.append(dest)
            
            return result
        
        return []
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching popular destinations: {str(e)}")

@app.get("/api/analytics/trends")
async def get_travel_trends():
    """Get travel trends and patterns"""
    try:
        # Department trends
        dept_pipeline = [
            {"$lookup": {
                "from": "user_preferences",
                "localField": "user_id", 
                "foreignField": "id",
                "as": "user_prefs"
            }},
            {"$unwind": "$user_prefs"},
            {"$unwind": "$user_prefs.preferred_departments"},
            {"$group": {"_id": "$user_prefs.preferred_departments", "count": {"$sum": 1}}}
        ]
        
        department_trends = list(db.user_interactions.aggregate(dept_pipeline))
        
        # Category trends
        cat_pipeline = [
            {"$lookup": {
                "from": "user_preferences",
                "localField": "user_id",
                "foreignField": "id", 
                "as": "user_prefs"
            }},
            {"$unwind": "$user_prefs"},
            {"$unwind": "$user_prefs.preferred_categories"},
            {"$group": {"_id": "$user_prefs.preferred_categories", "count": {"$sum": 1}}}
        ]
        
        category_trends = list(db.user_interactions.aggregate(cat_pipeline))
        
        # Travel style trends
        style_pipeline = [
            {"$lookup": {
                "from": "user_preferences",
                "localField": "user_id",
                "foreignField": "id",
                "as": "user_prefs"
            }},
            {"$unwind": "$user_prefs"},
            {"$group": {"_id": "$user_prefs.travel_style", "count": {"$sum": 1}}}
        ]
        
        travel_style_trends = list(db.user_interactions.aggregate(style_pipeline))
        
        return {
            "department_trends": department_trends,
            "category_trends": category_trends,
            "travel_style_trends": travel_style_trends,
            "total_users": db.user_preferences.count_documents({}),
            "total_interactions": db.user_interactions.count_documents({})
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching trends: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)