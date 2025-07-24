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
    """Get personalized recommendations using enhanced collaborative filtering for Colombian tourism"""
    try:
        # Get user preferences
        user_prefs = db.user_preferences.find_one({"id": user_id})
        if not user_prefs:
            raise HTTPException(status_code=404, detail="User preferences not found")
        
        # Get user interactions
        user_interactions = list(db.user_interactions.find({"user_id": user_id}))
        user_liked_destinations = [i['destination_rnt'] for i in user_interactions if i['action'] == 'like']
        user_viewed_destinations = [i['destination_rnt'] for i in user_interactions]
        
        # Fetch all destinations for analysis
        url = "https://www.datos.gov.co/resource/jqjy-rhzv.json"
        response = requests.get(url, params={'$limit': 5000})
        response.raise_for_status()
        all_destinations_data = response.json()
        
        # Filter for Boyacá and Cundinamarca
        target_departments = ['BOYACA', 'CUNDINAMARCA']
        available_destinations = [
            d for d in all_destinations_data 
            if d.get('nomdep', '').strip().upper() in target_departments
        ]
        
        # Find similar users (collaborative filtering)
        similar_users = []
        all_users = list(db.user_preferences.find({"id": {"$ne": user_id}}))
        
        for other_user in all_users:
            similarity_score = calculate_user_similarity(user_prefs, other_user)
            if similarity_score > 0:
                similar_users.append((other_user['id'], similarity_score))
        
        # Sort by similarity
        similar_users.sort(key=lambda x: x[1], reverse=True)
        
        # Get destinations liked by similar users
        collaborative_recommendations = []
        for similar_user_id, similarity in similar_users[:3]:  # Top 3 similar users
            similar_user_interactions = list(db.user_interactions.find({
                "user_id": similar_user_id,
                "action": "like"
            }))
            
            for interaction in similar_user_interactions:
                if interaction['destination_rnt'] not in user_viewed_destinations:
                    collaborative_recommendations.append(interaction['destination_rnt'])
        
        # Content-based recommendations based on user preferences
        content_recommendations = []
        user_preferred_categories = user_prefs.get('preferred_categories', [])
        user_preferred_departments = user_prefs.get('preferred_departments', [])
        
        for dest in available_destinations:
            if dest.get('rnt') in user_viewed_destinations:
                continue
                
            score = calculate_content_score(dest, user_prefs)
            if score > 0:
                content_recommendations.append((dest.get('rnt'), score))
        
        # Sort content recommendations by score
        content_recommendations.sort(key=lambda x: x[1], reverse=True)
        content_rnt_list = [rnt for rnt, score in content_recommendations[:limit]]
        
        # Combine collaborative and content-based recommendations
        combined_recommendations = list(set(collaborative_recommendations + content_rnt_list))
        
        # If no collaborative recommendations, use content-based + popular destinations
        if not combined_recommendations:
            # Get popular destinations as fallback
            popular_pipeline = [
                {"$match": {"action": {"$in": ["like", "view"]}}},
                {"$group": {"_id": "$destination_rnt", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}},
                {"$limit": limit}
            ]
            
            popular_destinations = list(db.user_interactions.aggregate(popular_pipeline))
            popular_rnt_list = [item['_id'] for item in popular_destinations]
            combined_recommendations = content_rnt_list + popular_rnt_list
        
        # Remove duplicates and limit
        final_recommendations = list(set(combined_recommendations))[:limit]
        
        # Fetch full destination data and process
        recommendations_data = []
        for dest in available_destinations:
            if dest.get('rnt') in final_recommendations:
                processed_dest = process_destination_data(dest)
                # Add recommendation reason
                processed_dest['recommendation_reason'] = get_recommendation_reason(
                    dest, user_prefs, dest.get('rnt') in collaborative_recommendations
                )
                recommendations_data.append(processed_dest)
        
        return recommendations_data[:limit]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating recommendations: {str(e)}")

def calculate_user_similarity(user1_prefs, user2_prefs):
    """Calculate similarity score between two users"""
    similarity_score = 0
    
    # Department preference similarity (weight: 3)
    common_departments = set(user1_prefs.get('preferred_departments', [])) & set(user2_prefs.get('preferred_departments', []))
    similarity_score += len(common_departments) * 3
    
    # Category preference similarity (weight: 2)
    common_categories = set(user1_prefs.get('preferred_categories', [])) & set(user2_prefs.get('preferred_categories', []))
    similarity_score += len(common_categories) * 2
    
    # Age range similarity (weight: 1)
    if user1_prefs.get('age_range') == user2_prefs.get('age_range'):
        similarity_score += 1
    
    # Travel style similarity (weight: 2)
    if user1_prefs.get('travel_style') == user2_prefs.get('travel_style'):
        similarity_score += 2
    
    return similarity_score

def calculate_content_score(destination, user_prefs):
    """Calculate content-based recommendation score"""
    score = 0
    
    # Category match
    dest_category = destination.get('categoria', '')
    for pref_category in user_prefs.get('preferred_categories', []):
        if pref_category.lower() in dest_category.lower():
            score += 3
    
    # Department match
    dest_dept = destination.get('nomdep', '').strip().upper()
    for pref_dept in user_prefs.get('preferred_departments', []):
        pref_dept_clean = pref_dept.strip().upper()
        if pref_dept_clean in ['BOYACÁ', 'BOYACA'] and dest_dept == 'BOYACA':
            score += 2
        elif pref_dept_clean == 'CUNDINAMARCA' and dest_dept == 'CUNDINAMARCA':
            score += 2
    
    # Travel style bonuses
    travel_style = user_prefs.get('travel_style', '').lower()
    if travel_style == 'aventura' and 'rural' in dest_category.lower():
        score += 1
    elif travel_style == 'cultural' and any(word in dest_category.lower() for word in ['guía', 'agencia']):
        score += 1
    elif travel_style == 'relajacion' and 'alojamiento' in dest_category.lower():
        score += 1
    
    return score

def get_recommendation_reason(destination, user_prefs, is_collaborative):
    """Generate explanation for why destination was recommended"""
    reasons = []
    
    if is_collaborative:
        reasons.append("Recomendado por usuarios con gustos similares")
    
    # Category match
    dest_category = destination.get('categoria', '')
    for pref_category in user_prefs.get('preferred_categories', []):
        if pref_category.lower() in dest_category.lower():
            reasons.append(f"Coincide con tu interés en {pref_category.lower()}")
            break
    
    # Location match
    dest_dept = destination.get('nomdep', '').strip().upper()
    dept_display = 'Boyacá' if dest_dept == 'BOYACA' else 'Cundinamarca'
    if dept_display in user_prefs.get('preferred_departments', []):
        reasons.append(f"Ubicado en {dept_display}, tu departamento preferido")
    
    return "; ".join(reasons) if reasons else "Destino popular en la región"

@app.get("/api/destinations/statistics")
async def get_destinations_statistics():
    """Get detailed statistics about tourism destinations in Boyacá and Cundinamarca"""
    try:
        url = "https://www.datos.gov.co/resource/jqjy-rhzv.json"
        response = requests.get(url, params={'$limit': 5000})
        response.raise_for_status()
        
        all_data = response.json()
        
        # Filter for our target departments
        target_departments = ['BOYACA', 'CUNDINAMARCA']
        filtered_data = [d for d in all_data if d.get('nomdep', '').strip().upper() in target_departments]
        
        # Calculate statistics
        stats = {
            'total_destinations': len(filtered_data),
            'by_department': {},
            'by_category': {},
            'by_municipality': {},
            'accommodation_stats': {
                'total_rooms': 0,
                'total_beds': 0,
                'establishments_with_rooms': 0
            }
        }
        
        # Department statistics
        for dept in target_departments:
            dept_data = [d for d in filtered_data if d.get('nomdep', '').strip().upper() == dept]
            dept_display = 'Boyacá' if dept == 'BOYACA' else 'Cundinamarca'
            
            stats['by_department'][dept_display] = {
                'count': len(dept_data),
                'categories': {}
            }
            
            # Categories by department
            for item in dept_data:
                category = item.get('categoria', 'No especificado')
                if category not in stats['by_department'][dept_display]['categories']:
                    stats['by_department'][dept_display]['categories'][category] = 0
                stats['by_department'][dept_display]['categories'][category] += 1
        
        # Overall category statistics
        for item in filtered_data:
            category = item.get('categoria', 'No especificado')
            if category not in stats['by_category']:
                stats['by_category'][category] = 0
            stats['by_category'][category] += 1
            
            # Municipality statistics
            municipality = item.get('nombre_muni', 'No especificado')
            dept_name = 'Boyacá' if item.get('nomdep', '').strip().upper() == 'BOYACA' else 'Cundinamarca'
            muni_key = f"{municipality} ({dept_name})"
            
            if muni_key not in stats['by_municipality']:
                stats['by_municipality'][muni_key] = 0
            stats['by_municipality'][muni_key] += 1
            
            # Accommodation statistics
            if item.get('habitaciones'):
                try:
                    rooms = int(float(item['habitaciones']))
                    stats['accommodation_stats']['total_rooms'] += rooms
                    stats['accommodation_stats']['establishments_with_rooms'] += 1
                except (ValueError, TypeError):
                    pass
            
            if item.get('camas'):
                try:
                    beds = int(float(item['camas']))
                    stats['accommodation_stats']['total_beds'] += beds
                except (ValueError, TypeError):
                    pass
        
        # Sort municipalities by count
        stats['by_municipality'] = dict(
            sorted(stats['by_municipality'].items(), key=lambda x: x[1], reverse=True)
        )
        
        return stats
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching statistics: {str(e)}")

@app.get("/api/destinations/search")
async def search_destinations(
    query: Optional[str] = None,
    department: Optional[str] = None,
    category: Optional[str] = None,
    municipality: Optional[str] = None,
    limit: int = 20
):
    """Advanced search for tourism destinations"""
    try:
        url = "https://www.datos.gov.co/resource/jqjy-rhzv.json"
        response = requests.get(url, params={'$limit': 5000})
        response.raise_for_status()
        
        all_data = response.json()
        
        # Filter for Boyacá and Cundinamarca
        target_departments = ['BOYACA', 'CUNDINAMARCA']
        results = []
        
        for item in all_data:
            dept_name = item.get('nomdep', '').strip().upper()
            if dept_name not in target_departments:
                continue
            
            # Apply filters
            if department:
                req_dept = department.strip().upper()
                if req_dept in ['BOYACÁ', 'BOYACA'] and dept_name != 'BOYACA':
                    continue
                elif req_dept == 'CUNDINAMARCA' and dept_name != 'CUNDINAMARCA':
                    continue
            
            if category and category.lower() not in item.get('categoria', '').lower():
                continue
            
            if municipality and municipality.lower() not in item.get('nombre_muni', '').lower():
                continue
            
            # Text search in name and category
            if query:
                search_text = f"{item.get('razon_social', '')} {item.get('categoria', '')} {item.get('nombre_muni', '')}".lower()
                if query.lower() not in search_text:
                    continue
            
            # Process and add to results
            processed_item = process_destination_data(item)
            results.append(processed_item)
        
        # Sort by relevance (name match first, then by municipality)
        if query:
            results.sort(key=lambda x: (
                0 if query.lower() in x.get('razon_social', '').lower() else 1,
                x.get('nombre_muni', '')
            ))
        else:
            results.sort(key=lambda x: (x.get('nomdep', ''), x.get('nombre_muni', '')))
        
        return results[:limit]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching destinations: {str(e)}")
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