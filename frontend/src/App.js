import React, { useState, useEffect } from 'react';
import './App.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

function App() {
  const [currentView, setCurrentView] = useState('home');
  const [destinations, setDestinations] = useState([]);
  const [userDestinations, setUserDestinations] = useState([]);
  const [statistics, setStatistics] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedDepartment, setSelectedDepartment] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('');
  const [userPreferences, setUserPreferences] = useState({
    name: '',
    email: '',
    preferred_categories: [],
    preferred_departments: ['Boyacá', 'Cundinamarca'],
    age_range: '',
    travel_style: ''
  });
  const [userId, setUserId] = useState(localStorage.getItem('tourism_user_id'));
  const [recommendations, setRecommendations] = useState([]);
  const [analytics, setAnalytics] = useState(null);
  const [userPoints, setUserPoints] = useState({ total_points: 0, level: {}, transactions: [] });
  const [rewards, setRewards] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showAddDestination, setShowAddDestination] = useState(false);
  const [newDestination, setNewDestination] = useState({
    name: '',
    description: '',
    category: '',
    subcategory: '',
    department: '',
    municipality: '',
    address: '',
    phone: '',
    email: '',
    website: '',
    services: []
  });

  useEffect(() => {
    fetchDestinations();
    fetchStatistics();
    fetchRewards();
    if (userId) {
      fetchRecommendations();
      fetchAnalytics();
      fetchUserPoints();
      fetchUserDestinations();
    }
  }, [userId]);

  const fetchDestinations = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${BACKEND_URL}/api/destinations?limit=30`);
      const data = await response.json();
      setDestinations(data);
    } catch (error) {
      console.error('Error fetching destinations:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchUserDestinations = async () => {
    if (!userId) return;
    try {
      const response = await fetch(`${BACKEND_URL}/api/user-destinations/${userId}`);
      const data = await response.json();
      setUserDestinations(data);
    } catch (error) {
      console.error('Error fetching user destinations:', error);
    }
  };

  const fetchUserPoints = async () => {
    if (!userId) return;
    try {
      const response = await fetch(`${BACKEND_URL}/api/points/${userId}`);
      const data = await response.json();
      setUserPoints(data);
    } catch (error) {
      console.error('Error fetching user points:', error);
    }
  };

  const fetchRewards = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/rewards`);
      const data = await response.json();
      setRewards(data);
    } catch (error) {
      console.error('Error fetching rewards:', error);
    }
  };

  const fetchStatistics = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/destinations/statistics`);
      const data = await response.json();
      setStatistics(data);
    } catch (error) {
      console.error('Error fetching statistics:', error);
    }
  };

  const searchDestinations = async () => {
    try {
      setLoading(true);
      let url = `${BACKEND_URL}/api/destinations/search?limit=30`;
      
      if (searchQuery) url += `&query=${encodeURIComponent(searchQuery)}`;
      if (selectedDepartment) url += `&department=${encodeURIComponent(selectedDepartment)}`;
      if (selectedCategory) url += `&category=${encodeURIComponent(selectedCategory)}`;
      
      const response = await fetch(url);
      const data = await response.json();
      setDestinations(data);
    } catch (error) {
      console.error('Error searching destinations:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchRecommendations = async () => {
    if (!userId) return;
    try {
      const response = await fetch(`${BACKEND_URL}/api/recommendations/${userId}`);
      const data = await response.json();
      setRecommendations(data);
    } catch (error) {
      console.error('Error fetching recommendations:', error);
    }
  };

  const fetchAnalytics = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/analytics/trends`);
      const data = await response.json();
      setAnalytics(data);
    } catch (error) {
      console.error('Error fetching analytics:', error);
    }
  };

  const saveUserPreferences = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/users/preferences`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(userPreferences),
      });
      const data = await response.json();
      
      if (response.ok) {
        const newUserId = data.user_id;
        setUserId(newUserId);
        localStorage.setItem('tourism_user_id', newUserId);
        alert('¡Preferencias guardadas exitosamente!');
        setCurrentView('destinations');
        fetchRecommendations();
      }
    } catch (error) {
      console.error('Error saving preferences:', error);
      alert('Error al guardar preferencias');
    }
  };

  const trackInteraction = async (destinationRnt, action) => {
    if (!userId) return;
    
    try {
      const response = await fetch(`${BACKEND_URL}/api/users/interactions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: userId,
          destination_rnt: destinationRnt,
          action: action
        }),
      });
      
      const data = await response.json();
      if (data.points_earned) {
        // Show points notification
        alert(`¡Ganaste ${data.points_earned} puntos por esta acción!`);
        fetchUserPoints(); // Refresh points
      }
    } catch (error) {
      console.error('Error tracking interaction:', error);
    }
  };

  const submitNewDestination = async () => {
    if (!userId) {
      alert('Debes iniciar sesión para agregar destinos');
      return;
    }
    
    try {
      const response = await fetch(`${BACKEND_URL}/api/user-destinations`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          ...newDestination,
          user_id: userId
        }),
      });
      
      const data = await response.json();
      if (response.ok) {
        alert('¡Destino enviado para revisión! Ganaste 5 puntos.');
        setShowAddDestination(false);
        setNewDestination({
          name: '',
          description: '',
          category: '',
          subcategory: '',
          department: '',
          municipality: '',
          address: '',
          phone: '',
          email: '',
          website: '',
          services: []
        });
        fetchUserDestinations();
        fetchUserPoints();
      }
    } catch (error) {
      console.error('Error submitting destination:', error);
      alert('Error al enviar destino');
    }
  };

  const redeemReward = async (rewardId) => {
    if (!userId) return;
    
    try {
      const response = await fetch(`${BACKEND_URL}/api/rewards/redeem`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: userId,
          reward_id: rewardId
        }),
      });
      
      const data = await response.json();
      if (response.ok) {
        alert(`¡Recompensa canjeada exitosamente! Contacta: ${data.partner_contact}`);
        fetchUserPoints();
        fetchRewards();
      } else {
        alert(data.detail || 'Error al canjear recompensa');
      }
    } catch (error) {
      console.error('Error redeeming reward:', error);
      alert('Error al canjear recompensa');
    }
  };

  const handleDestinationClick = (destination) => {
    trackInteraction(destination.rnt, 'view');
  };

  const handleDestinationLike = (destination) => {
    trackInteraction(destination.rnt, 'like');
  };

  const renderHero = () => (
    <div className="hero-section">
      <div className="hero-content">
        <h1 className="hero-title">Descubre Boyacá y Cundinamarca</h1>
        <p className="hero-subtitle">
          Explora los mejores destinos turísticos de Colombia con recomendaciones personalizadas
        </p>
        <button 
          className="hero-button"
          onClick={() => setCurrentView('preferences')}
        >
          Comenzar Exploración
        </button>
      </div>
    </div>
  );

  const renderPreferencesForm = () => (
    <div className="preferences-container">
      <div className="preferences-card">
        <h2 className="preferences-title">Cuéntanos sobre tus preferencias</h2>
        
        <div className="form-group">
          <label>Nombre:</label>
          <input
            type="text"
            value={userPreferences.name}
            onChange={(e) => setUserPreferences({...userPreferences, name: e.target.value})}
            className="form-input"
          />
        </div>

        <div className="form-group">
          <label>Email:</label>
          <input
            type="email"
            value={userPreferences.email}
            onChange={(e) => setUserPreferences({...userPreferences, email: e.target.value})}
            className="form-input"
          />
        </div>

        <div className="form-group">
          <label>Departamentos de interés:</label>
          <div className="checkbox-group">
            {['Boyacá', 'Cundinamarca'].map(department => (
              <label key={department} className="checkbox-label">
                <input
                  type="checkbox"
                  checked={userPreferences.preferred_departments.includes(department)}
                  onChange={(e) => {
                    if (e.target.checked) {
                      setUserPreferences({
                        ...userPreferences,
                        preferred_departments: [...userPreferences.preferred_departments, department]
                      });
                    } else {
                      setUserPreferences({
                        ...userPreferences,
                        preferred_departments: userPreferences.preferred_departments.filter(d => d !== department)
                      });
                    }
                  }}
                />
                {department}
              </label>
            ))}
          </div>
        </div>

        <div className="form-group">
          <label>Tipo de turismo preferido:</label>
          <div className="checkbox-group">
            {[
              { key: 'ALOJAMIENTO HOTELERO', label: 'Hoteles y hospedajes' },
              { key: 'ALOJAMIENTO RURAL', label: 'Turismo rural y ecológico' },
              { key: 'AGENCIA DE VIAJES', label: 'Servicios de viaje y turismo' },
              { key: 'GUÍA DE TURISMO', label: 'Guías turísticos profesionales' },
              { key: 'TRANSPORTE TURÍSTICO', label: 'Transporte especializado' }
            ].map(category => (
              <label key={category.key} className="checkbox-label">
                <input
                  type="checkbox"
                  checked={userPreferences.preferred_categories.includes(category.key)}
                  onChange={(e) => {
                    if (e.target.checked) {
                      setUserPreferences({
                        ...userPreferences,
                        preferred_categories: [...userPreferences.preferred_categories, category.key]
                      });
                    } else {
                      setUserPreferences({
                        ...userPreferences,
                        preferred_categories: userPreferences.preferred_categories.filter(c => c !== category.key)
                      });
                    }
                  }}
                />
                {category.label}
              </label>
            ))}
          </div>
        </div>

        <div className="form-group">
          <label>Rango de edad:</label>
          <select
            value={userPreferences.age_range}
            onChange={(e) => setUserPreferences({...userPreferences, age_range: e.target.value})}
            className="form-select"
          >
            <option value="">Selecciona tu rango de edad</option>
            <option value="18-25">18-25</option>
            <option value="26-35">26-35</option>
            <option value="36-45">36-45</option>
            <option value="46-55">46-55</option>
            <option value="56+">56+</option>
          </select>
        </div>

        <div className="form-group">
          <label>Estilo de viaje:</label>
          <select
            value={userPreferences.travel_style}
            onChange={(e) => setUserPreferences({...userPreferences, travel_style: e.target.value})}
            className="form-select"
          >
            <option value="">Selecciona tu estilo</option>
            <option value="aventura">Aventura</option>
            <option value="cultural">Cultural</option>
            <option value="relajacion">Relajación</option>
            <option value="familiar">Familiar</option>
            <option value="romantico">Romántico</option>
          </select>
        </div>

        <button onClick={saveUserPreferences} className="save-button">
          Guardar Preferencias
        </button>
      </div>
    </div>
  );

  const renderDestinations = () => (
    <div className="destinations-container">
      <h2 className="section-title">Destinos Turísticos de Boyacá y Cundinamarca</h2>
      
      {/* Search and Filter Section */}
      <div className="search-filters">
        <div className="search-bar">
          <input
            type="text"
            placeholder="Buscar destinos, hoteles, actividades..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="search-input"
            onKeyPress={(e) => e.key === 'Enter' && searchDestinations()}
          />
          <button onClick={searchDestinations} className="search-button">
            🔍 Buscar
          </button>
        </div>
        
        <div className="filter-row">
          <select
            value={selectedDepartment}
            onChange={(e) => setSelectedDepartment(e.target.value)}
            className="filter-select"
          >
            <option value="">Todos los departamentos</option>
            <option value="Boyacá">Boyacá</option>
            <option value="Cundinamarca">Cundinamarca</option>
          </select>
          
          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            className="filter-select"
          >
            <option value="">Todas las categorías</option>
            <option value="ALOJAMIENTO HOTELERO">Hoteles</option>
            <option value="ALOJAMIENTO RURAL">Turismo Rural</option>
            <option value="AGENCIA DE VIAJES">Agencias de Viaje</option>
            <option value="GUÍA DE TURISMO">Guías Turísticos</option>
            <option value="TRANSPORTE TURÍSTICO">Transporte</option>
          </select>
          
          <button onClick={searchDestinations} className="filter-button">
            Aplicar Filtros
          </button>
        </div>
      </div>

      {/* Statistics Overview */}
      {statistics && (
        <div className="statistics-overview">
          <div className="stat-card">
            <span className="stat-number">{statistics.total_destinations}</span>
            <span className="stat-label">Destinos Registrados</span>
          </div>
          <div className="stat-card">
            <span className="stat-number">{statistics.by_department['Boyacá']?.count || 0}</span>
            <span className="stat-label">En Boyacá</span>
          </div>
          <div className="stat-card">
            <span className="stat-number">{statistics.by_department['Cundinamarca']?.count || 0}</span>
            <span className="stat-label">En Cundinamarca</span>
          </div>
          <div className="stat-card">
            <span className="stat-number">{statistics.accommodation_stats.total_rooms}</span>
            <span className="stat-label">Habitaciones Disponibles</span>
          </div>
        </div>
      )}
      
      {userId && recommendations.length > 0 && (
        <div className="recommendations-section">
          <h3 className="recommendations-title">⭐ Recomendado para ti</h3>
          <div className="destinations-grid">
            {recommendations.slice(0, 4).map((destination) => (
              <div key={destination.rnt} className="destination-card recommended">
                <div className="destination-header">
                  <h4 className="destination-name">{destination.razon_social}</h4>
                  <span className="recommendation-badge">Recomendado</span>
                </div>
                <div className="destination-info">
                  <p><strong>Categoría:</strong> {destination.category_description || destination.categoria}</p>
                  <p><strong>Ubicación:</strong> {destination.location || `${destination.nombre_muni}, ${destination.department_display || destination.nomdep}`}</p>
                  {destination.habitaciones && (
                    <p><strong>Habitaciones:</strong> {destination.habitaciones}</p>
                  )}
                  {destination.recommendation_reason && (
                    <p className="recommendation-reason"><em>{destination.recommendation_reason}</em></p>
                  )}
                </div>
                <div className="destination-actions">
                  <button 
                    onClick={() => handleDestinationClick(destination)}
                    className="view-button"
                  >
                    Ver Detalles
                  </button>
                  <button 
                    onClick={() => handleDestinationLike(destination)}
                    className="like-button"
                  >
                    ❤️ Me Gusta
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="all-destinations-section">
        <h3 className="section-subtitle">
          {searchQuery || selectedDepartment || selectedCategory ? 'Resultados de Búsqueda' : 'Todos los Destinos'}
        </h3>
        {loading ? (
          <div className="loading">Cargando destinos...</div>
        ) : destinations.length === 0 ? (
          <div className="no-results">
            <p>No se encontraron destinos con los criterios seleccionados.</p>
            <button onClick={() => {
              setSearchQuery('');
              setSelectedDepartment('');
              setSelectedCategory('');
              fetchDestinations();
            }} className="reset-button">
              Ver Todos los Destinos
            </button>
          </div>
        ) : (
          <div className="destinations-grid">
            {destinations.map((destination) => (
              <div key={destination.rnt} className="destination-card">
                <div className="destination-header">
                  <h4 className="destination-name">{destination.razon_social}</h4>
                  <span className="department-badge">
                    {destination.department_display || destination.nomdep}
                  </span>
                </div>
                <div className="destination-info">
                  <p><strong>Categoría:</strong> {destination.category_description || destination.categoria}</p>
                  <p><strong>Subcategoría:</strong> {destination.subcategoria}</p>
                  <p><strong>Ubicación:</strong> {destination.location || `${destination.nombre_muni}, ${destination.department_display || destination.nomdep}`}</p>
                  {destination.habitaciones && (
                    <p><strong>Habitaciones:</strong> {destination.habitaciones}</p>
                  )}
                  {destination.camas && (
                    <p><strong>Camas:</strong> {destination.camas}</p>
                  )}
                  {destination.empleados && (
                    <p><strong>Empleados:</strong> {destination.empleados}</p>
                  )}
                </div>
                <div className="destination-actions">
                  <button 
                    onClick={() => handleDestinationClick(destination)}
                    className="view-button"
                  >
                    Ver Detalles
                  </button>
                  <button 
                    onClick={() => handleDestinationLike(destination)}
                    className="like-button"
                  >
                    ❤️ Me Gusta
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );

  const renderAnalytics = () => (
    <div className="analytics-container">
      <h2 className="section-title">Tendencias y Análisis</h2>
      
      {analytics && (
        <div className="analytics-grid">
          <div className="analytics-card">
            <h3>Estadísticas Generales</h3>
            <div className="stats">
              <div className="stat-item">
                <span className="stat-number">{analytics.total_users}</span>
                <span className="stat-label">Usuarios Registrados</span>
              </div>
              <div className="stat-item">
                <span className="stat-number">{analytics.total_interactions}</span>
                <span className="stat-label">Interacciones Totales</span>
              </div>
            </div>
          </div>

          <div className="analytics-card">
            <h3>Departamentos Populares</h3>
            <div className="trend-list">
              {analytics.department_trends.map((item, index) => (
                <div key={index} className="trend-item">
                  <span className="trend-name">{item._id}</span>
                  <span className="trend-count">{item.count}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="analytics-card">
            <h3>Categorías Favoritas</h3>
            <div className="trend-list">
              {analytics.category_trends.map((item, index) => (
                <div key={index} className="trend-item">
                  <span className="trend-name">{item._id}</span>
                  <span className="trend-count">{item.count}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="analytics-card">
            <h3>Estilos de Viaje</h3>
            <div className="trend-list">
              {analytics.travel_style_trends.map((item, index) => (
                <div key={index} className="trend-item">
                  <span className="trend-name">{item._id}</span>
                  <span className="trend-count">{item.count}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );

  const renderAddDestination = () => (
    <div className="add-destination-container">
      <h2 className="section-title">Agregar Nuevo Destino Turístico</h2>
      <p className="section-subtitle">Comparte un lugar especial de Boyacá o Cundinamarca y gana puntos</p>
      
      <div className="add-destination-card">
        <div className="form-group">
          <label>Nombre del destino:</label>
          <input
            type="text"
            value={newDestination.name}
            onChange={(e) => setNewDestination({...newDestination, name: e.target.value})}
            className="form-input"
            placeholder="Ej: Hotel Casa Colonial Villa de Leyva"
          />
        </div>

        <div className="form-group">
          <label>Descripción:</label>
          <textarea
            value={newDestination.description}
            onChange={(e) => setNewDestination({...newDestination, description: e.target.value})}
            className="form-textarea"
            rows="4"
            placeholder="Describe el destino, sus atractivos, servicios y qué lo hace especial..."
          />
        </div>

        <div className="form-row">
          <div className="form-group">
            <label>Departamento:</label>
            <select
              value={newDestination.department}
              onChange={(e) => setNewDestination({...newDestination, department: e.target.value})}
              className="form-select"
            >
              <option value="">Selecciona departamento</option>
              <option value="Boyacá">Boyacá</option>
              <option value="Cundinamarca">Cundinamarca</option>
            </select>
          </div>

          <div className="form-group">
            <label>Municipio:</label>
            <input
              type="text"
              value={newDestination.municipality}
              onChange={(e) => setNewDestination({...newDestination, municipality: e.target.value})}
              className="form-input"
              placeholder="Ej: Villa de Leyva"
            />
          </div>
        </div>

        <div className="form-row">
          <div className="form-group">
            <label>Categoría:</label>
            <select
              value={newDestination.category}
              onChange={(e) => setNewDestination({...newDestination, category: e.target.value})}
              className="form-select"
            >
              <option value="">Selecciona categoría</option>
              <option value="ALOJAMIENTO HOTELERO">Alojamiento Hotelero</option>
              <option value="ALOJAMIENTO RURAL">Alojamiento Rural</option>
              <option value="AGENCIA DE VIAJES">Agencia de Viajes</option>
              <option value="GUÍA DE TURISMO">Guía de Turismo</option>
              <option value="TRANSPORTE TURÍSTICO">Transporte Turístico</option>
              <option value="RESTAURANTE">Restaurante</option>
              <option value="ATRACTIVO NATURAL">Atractivo Natural</option>
              <option value="SITIO HISTÓRICO">Sitio Histórico</option>
            </select>
          </div>

          <div className="form-group">
            <label>Subcategoría:</label>
            <input
              type="text"
              value={newDestination.subcategory}
              onChange={(e) => setNewDestination({...newDestination, subcategory: e.target.value})}
              className="form-input"
              placeholder="Ej: Hotel boutique, Ecoturismo, etc."
            />
          </div>
        </div>

        <div className="form-group">
          <label>Dirección:</label>
          <input
            type="text"
            value={newDestination.address}
            onChange={(e) => setNewDestination({...newDestination, address: e.target.value})}
            className="form-input"
            placeholder="Dirección completa del destino"
          />
        </div>

        <div className="form-row">
          <div className="form-group">
            <label>Teléfono:</label>
            <input
              type="tel"
              value={newDestination.phone}
              onChange={(e) => setNewDestination({...newDestination, phone: e.target.value})}
              className="form-input"
              placeholder="(57) 300-555-0000"
            />
          </div>

          <div className="form-group">
            <label>Email:</label>
            <input
              type="email"
              value={newDestination.email}
              onChange={(e) => setNewDestination({...newDestination, email: e.target.value})}
              className="form-input"
              placeholder="contacto@destino.com"
            />
          </div>
        </div>

        <div className="form-group">
          <label>Sitio web (opcional):</label>
          <input
            type="url"
            value={newDestination.website}
            onChange={(e) => setNewDestination({...newDestination, website: e.target.value})}
            className="form-input"
            placeholder="https://www.sitiowebdestino.com"
          />
        </div>

        <div className="points-info">
          <div className="points-card">
            <h4>🎯 Gana Puntos por Contribuir</h4>
            <ul>
              <li>+5 puntos por enviar destino</li>
              <li>+15 puntos adicionales si es aprobado</li>
              <li>¡Total: 20 puntos por destino aprobado!</li>
            </ul>
          </div>
        </div>

        <div className="form-actions">
          <button 
            onClick={submitNewDestination} 
            className="submit-button"
            disabled={!newDestination.name || !newDestination.department || !newDestination.category}
          >
            📍 Enviar Destino (+5 puntos)
          </button>
          <button 
            onClick={() => setCurrentView('destinations')} 
            className="cancel-button"
          >
            Cancelar
          </button>
        </div>
      </div>
    </div>
  );

  const renderPointsAndRewards = () => (
    <div className="points-container">
      <h2 className="section-title">Mi Sistema de Puntos</h2>
      
      {/* User Level and Points */}
      <div className="user-level-card">
        <div className="level-info">
          <div className="level-badge-large">
            {userPoints.level?.current_level || 'Explorador'}
          </div>
          <div className="points-info-large">
            <span className="current-points">{userPoints.total_points}</span>
            <span className="points-label">puntos</span>
          </div>
        </div>
        
        {userPoints.level?.next_level && (
          <div className="progress-section">
            <p>Próximo nivel: <strong>{userPoints.level.next_level}</strong></p>
            <div className="progress-bar">
              <div 
                className="progress-fill" 
                style={{
                  width: `${Math.max(0, 100 - (userPoints.level.points_to_next / 50) * 100)}%`
                }}
              ></div>
            </div>
            <p className="progress-text">Te faltan {userPoints.level.points_to_next} puntos</p>
          </div>
        )}

        <div className="level-benefits">
          <h4>Beneficios de tu nivel:</h4>
          <ul>
            {(userPoints.level?.current_benefits || []).map((benefit, index) => (
              <li key={index}>{benefit}</li>
            ))}
          </ul>
        </div>
      </div>

      {/* Ways to Earn Points */}
      <div className="earn-points-section">
        <h3>💰 Maneras de Ganar Puntos</h3>
        <div className="earn-points-grid">
          <div className="earn-point-card">
            <div className="point-value">+20</div>
            <div className="point-action">Destino aprobado</div>
          </div>
          <div className="earn-point-card">
            <div className="point-value">+3</div>
            <div className="point-action">Like a destino</div>
          </div>
          <div className="earn-point-card">
            <div className="point-value">+2</div>
            <div className="point-action">Guardar destino</div>
          </div>
          <div className="earn-point-card">
            <div className="point-value">+1</div>
            <div className="point-action">Ver destino</div>
          </div>
        </div>
      </div>

      {/* Rewards Catalog */}
      <div className="rewards-section">
        <h3>🎁 Catálogo de Recompensas</h3>
        <div className="rewards-grid">
          {rewards.map((reward) => (
            <div key={reward.id} className="reward-card">
              <div className="reward-header">
                <h4 className="reward-title">{reward.title}</h4>
                <div className="reward-cost">{reward.points_required} pts</div>
              </div>
              
              <div className="reward-content">
                <p className="reward-description">{reward.description}</p>
                <div className="reward-details">
                  <p><strong>Partner:</strong> {reward.partner_name}</p>
                  {reward.discount_percentage && (
                    <p><strong>Descuento:</strong> {reward.discount_percentage}%</p>
                  )}
                  <p className="reward-terms">{reward.terms_conditions}</p>
                </div>
              </div>
              
              <div className="reward-footer">
                <div className="reward-availability">
                  {reward.max_redemptions - reward.current_redemptions} disponibles
                </div>
                <button 
                  onClick={() => redeemReward(reward.id)}
                  className="redeem-button"
                  disabled={userPoints.total_points < reward.points_required}
                >
                  {userPoints.total_points >= reward.points_required ? 'Canjear' : 'Puntos insuficientes'}
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Recent Transactions */}
      {userPoints.transactions && userPoints.transactions.length > 0 && (
        <div className="transactions-section">
          <h3>📊 Historial de Puntos</h3>
          <div className="transactions-list">
            {userPoints.transactions.slice(0, 10).map((transaction) => (
              <div key={transaction.id} className="transaction-item">
                <div className="transaction-info">
                  <span className="transaction-description">{transaction.description}</span>
                  <span className="transaction-date">
                    {new Date(transaction.timestamp).toLocaleDateString('es-CO')}
                  </span>
                </div>
                <div className={`transaction-points ${transaction.points > 0 ? 'positive' : 'negative'}`}>
                  {transaction.points > 0 ? '+' : ''}{transaction.points}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* My Submitted Destinations */}
      {userDestinations && userDestinations.length > 0 && (
        <div className="my-destinations-section">
          <h3>📍 Mis Destinos Enviados</h3>
          <div className="my-destinations-grid">
            {userDestinations.map((destination) => (
              <div key={destination.id} className="my-destination-card">
                <div className="destination-status">
                  <span className={`status-badge ${destination.status}`}>
                    {destination.status === 'pending' ? '⏳ Pendiente' : 
                     destination.status === 'approved' ? '✅ Aprobado' : '❌ Rechazado'}
                  </span>
                </div>
                <h4>{destination.name}</h4>
                <p>{destination.municipality}, {destination.department}</p>
                <p className="destination-category">{destination.category}</p>
                {destination.approved_at && (
                  <p className="approval-date">
                    Aprobado: {new Date(destination.approved_at).toLocaleDateString('es-CO')}
                  </p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );

  return (
    <div className="App">
      <nav className="navbar">
        <div className="nav-brand">TurismoCol</div>
        <div className="nav-center">
          <div className="nav-links">
            <button 
              className={currentView === 'home' ? 'nav-link active' : 'nav-link'}
              onClick={() => setCurrentView('home')}
            >
              Inicio
            </button>
            <button 
              className={currentView === 'preferences' ? 'nav-link active' : 'nav-link'}
              onClick={() => setCurrentView('preferences')}
            >
              Preferencias
            </button>
            <button 
              className={currentView === 'destinations' ? 'nav-link active' : 'nav-link'}
              onClick={() => setCurrentView('destinations')}
            >
              Destinos
            </button>
            <button 
              className={currentView === 'add-destination' ? 'nav-link active' : 'nav-link'}
              onClick={() => setCurrentView('add-destination')}
            >
              ➕ Agregar Destino
            </button>
            <button 
              className={currentView === 'points' ? 'nav-link active' : 'nav-link'}
              onClick={() => setCurrentView('points')}
            >
              🏆 Mis Puntos
            </button>
            <button 
              className={currentView === 'analytics' ? 'nav-link active' : 'nav-link'}
              onClick={() => setCurrentView('analytics')}
            >
              Análisis
            </button>
          </div>
        </div>
        <div className="nav-right">
          {userId && userPoints && (
            <div className="points-display">
              <span className="points-badge">⭐ {userPoints.total_points} pts</span>
              <span className="level-badge">{userPoints.level?.current_level || 'Explorador'}</span>
            </div>
          )}
        </div>
      </nav>

      <main className="main-content">
        {currentView === 'home' && renderHero()}
        {currentView === 'preferences' && renderPreferencesForm()}
        {currentView === 'destinations' && renderDestinations()}
        {currentView === 'add-destination' && renderAddDestination()}
        {currentView === 'points' && renderPointsAndRewards()}
        {currentView === 'analytics' && renderAnalytics()}
      </main>

      <footer className="footer">
        <p>&copy; 2025 TurismoCol - Descubre Boyacá y Cundinamarca</p>
      </footer>
    </div>
  );
}

export default App;