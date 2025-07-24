import React, { useState, useEffect } from 'react';
import './App.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

function App() {
  const [currentView, setCurrentView] = useState('home');
  const [destinations, setDestinations] = useState([]);
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
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchDestinations();
    fetchStatistics();
    if (userId) {
      fetchRecommendations();
      fetchAnalytics();
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
      await fetch(`${BACKEND_URL}/api/users/interactions`, {
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
    } catch (error) {
      console.error('Error tracking interaction:', error);
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
          <label>Tipo de turismo preferido:</label>
          <div className="checkbox-group">
            {['ALOJAMIENTO HOTELERO', 'ALOJAMIENTO RURAL', 'AGENCIA DE VIAJES', 'GUÍA DE TURISMO', 'TRANSPORTE TURÍSTICO'].map(category => (
              <label key={category} className="checkbox-label">
                <input
                  type="checkbox"
                  checked={userPreferences.preferred_categories.includes(category)}
                  onChange={(e) => {
                    if (e.target.checked) {
                      setUserPreferences({
                        ...userPreferences,
                        preferred_categories: [...userPreferences.preferred_categories, category]
                      });
                    } else {
                      setUserPreferences({
                        ...userPreferences,
                        preferred_categories: userPreferences.preferred_categories.filter(c => c !== category)
                      });
                    }
                  }}
                />
                {category}
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

  return (
    <div className="App">
      <nav className="navbar">
        <div className="nav-brand">TurismoCol</div>
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
            className={currentView === 'analytics' ? 'nav-link active' : 'nav-link'}
            onClick={() => setCurrentView('analytics')}
          >
            Análisis
          </button>
        </div>
      </nav>

      <main className="main-content">
        {currentView === 'home' && renderHero()}
        {currentView === 'preferences' && renderPreferencesForm()}
        {currentView === 'destinations' && renderDestinations()}
        {currentView === 'analytics' && renderAnalytics()}
      </main>

      <footer className="footer">
        <p>&copy; 2025 TurismoCol - Descubre Boyacá y Cundinamarca</p>
      </footer>
    </div>
  );
}

export default App;