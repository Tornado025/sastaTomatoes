document.addEventListener('DOMContentLoaded', function () {
    const searchForm = document.getElementById('search-form');
    const movieInput = document.getElementById('movie-input');
    const resultsContainer = document.getElementById('results-container');
    const loadingIndicator = document.getElementById('loading');
    const errorContainer = document.getElementById('error-message');
    const autocompleteContainer = document.getElementById('autocomplete-suggestions');
  
    let searchTimeout;
  
    fetchMovies(1);
  
    movieInput.addEventListener('input', function () {
      const query = this.value.trim();
      clearTimeout(searchTimeout);
  
      if (query.length >= 2) {
        searchTimeout = setTimeout(() => {
          fetchAutocompleteSuggestions(query);
        }, 300);
      } else {
        hideAutocomplete();
      }
    });
  
    document.addEventListener('click', function (e) {
      if (!searchForm.contains(e.target)) {
        hideAutocomplete();
      }
    });
  
    searchForm.addEventListener('submit', function (e) {
      e.preventDefault();
      const movieTitle = movieInput.value.trim();
  
      if (movieTitle) {
        hideAutocomplete();
        getRecommendations(movieTitle);
      }
    });
  
    async function fetchAutocompleteSuggestions(query) {
      try {
        const response = await fetch(`http://localhost:5000/search?q=${encodeURIComponent(query)}`);
        const data = await response.json();
  
        if (data.matches && data.matches.length > 0) {
          showAutocomplete(data.matches);
        } else {
          hideAutocomplete();
        }
      } catch (error) {
        console.error('Autocomplete error:', error);
        hideAutocomplete();
      }
    }
  
    function showAutocomplete(matches) {
      autocompleteContainer.innerHTML = matches
        .map(match => `<div class="suggestion-item" data-movie="${match}">${match}</div>`)
        .join('');
      autocompleteContainer.style.display = 'block';
  
      autocompleteContainer.querySelectorAll('.suggestion-item').forEach(item => {
        item.addEventListener('click', function () {
          movieInput.value = this.dataset.movie;
          hideAutocomplete();
          getRecommendations(this.dataset.movie);
        });
      });
    }
  
    function hideAutocomplete() {
      autocompleteContainer.style.display = 'none';
    }
  
    async function fetchMovies(page = 1) {
      try {
        showLoading(true);
        const response = await fetch(`http://localhost:5000/movies?page=${page}&per_page=20`);
        const data = await response.json();
  
        if (data.movies && data.movies.length > 0) {
          displayMovieList(data.movies);
        }
      } catch (error) {
        showError("Failed to fetch movies. Please try again later.");
      } finally {
        showLoading(false);
      }
    }
  
    async function getRecommendations(movieTitle) {
      try {
        showLoading(true);
        clearResults();
        hideError();
  
        const response = await fetch(`http://localhost:5000/recommend?title=${encodeURIComponent(movieTitle)}`);
        const data = await response.json();
  
        if (response.ok) {
          if (data.searched_movie && data.recommendations) {
            displayRecommendations(data.searched_movie, data.recommendations);
          } else {
            showError(`No recommendations found for "${movieTitle}"`);
          }
        } else {
          if (data.suggestions && data.suggestions.length > 0) {
            showErrorWithSuggestions(data.error, data.suggestions);
          } else {
            showError(data.error || "An error occurred");
          }
        }
      } catch (error) {
        showError("Failed to get recommendations. Please try again later.");
      } finally {
        showLoading(false);
      }
    }
  
    function displayMovieList(movies) {
      resultsContainer.innerHTML = `
        <div class="movie-list">
          <h3>Popular Movies - Click to get recommendations</h3>
          <ul>
            ${movies.map(movie => `<li><a href="#" class="movie-link">${movie}</a></li>`).join('')}
          </ul>
        </div>
      `;
  
      document.querySelectorAll('.movie-link').forEach(link => {
        link.addEventListener('click', function (e) {
          e.preventDefault();
          movieInput.value = this.textContent;
          getRecommendations(this.textContent);
        });
      });
    }
  
    function displayRecommendations(searchedMovie, recommendations) {
      resultsContainer.innerHTML = `
        <div class="movie-details">
          <div class="movie-title">${searchedMovie.title}</div>
  
          <div class="movie-info">
            <div class="info-item">
              <div class="info-label">Runtime</div>
              <div class="info-value">${searchedMovie.runtime} minutes</div>
            </div>
            <div class="info-item">
              <div class="info-label">Director</div>
              <div class="info-value">${searchedMovie.director.length > 0 ? searchedMovie.director.join(', ') : 'Unknown'}</div>
            </div>
            <div class="info-item">
              <div class="info-label">Cast</div>
              <div class="info-value">${searchedMovie.cast.length > 0 ? searchedMovie.cast.join(', ') : 'Unknown'}</div>
            </div>
            <div class="info-item">
              <div class="info-label">Genres</div>
              <div class="info-value">${searchedMovie.genres.length > 0 ? searchedMovie.genres.join(', ') : 'Unknown'}</div>
            </div>
          </div>
  
          <div class="movie-overview">
            <div class="info-label">Overview</div>
            <div class="info-value">${searchedMovie.overview}</div>
          </div>
        </div>
  
        <div class="recommendations-section">
          <div class="recommendations-title">Recommended Movies</div>
          <div class="recommendations-grid">
            ${recommendations.map(movie => createRecommendationCard(movie)).join('')}
          </div>
        </div>
      `;
  
      document.querySelectorAll('.recommendation-card').forEach(card => {
        card.addEventListener('click', function () {
          const selectedTitle = this.getAttribute('data-title');
          movieInput.value = selectedTitle;
          getRecommendations(selectedTitle);
        });
      });
    }
  
    function createRecommendationCard(movie) {
      return `
        <div class="recommendation-card" data-title="${movie.title}" style="cursor: pointer;">
          <div class="card-title">${movie.title}</div>
          <div class="card-info"><strong>Runtime:</strong> ${movie.runtime} minutes</div>
          <div class="card-info"><strong>Director:</strong> ${movie.director.length > 0 ? movie.director.join(', ') : 'Unknown'}</div>
          <div class="card-info"><strong>Cast:</strong> ${movie.cast.length > 0 ? movie.cast.slice(0, 2).join(', ') : 'Unknown'}</div>
          <div class="card-info"><strong>Genres:</strong> ${movie.genres.length > 0 ? movie.genres.slice(0, 3).join(', ') : 'Unknown'}</div>
          <div class="card-overview">${movie.overview}</div>
        </div>
      `;
    }
  
    function clearResults() {
      resultsContainer.innerHTML = '';
    }
  
    function showLoading(show) {
      loadingIndicator.style.display = show ? 'block' : 'none';
    }
  
    function showError(message) {
      errorContainer.innerHTML = message;
      errorContainer.style.display = 'block';
    }
  
    function showErrorWithSuggestions(errorMessage, suggestions) {
      const suggestionsHtml = `
        <div class="suggestions">
          <h4>Did you mean:</h4>
          <ul>
            ${suggestions.map(suggestion =>
              `<li><a href="#" class="suggestion-link">${suggestion}</a></li>`
            ).join('')}
          </ul>
        </div>
      `;
  
      errorContainer.innerHTML = errorMessage + suggestionsHtml;
      errorContainer.style.display = 'block';
  
      errorContainer.querySelectorAll('.suggestion-link').forEach(link => {
        link.addEventListener('click', function (e) {
          e.preventDefault();
          movieInput.value = this.textContent;
          getRecommendations(this.textContent);
        });
      });
    }
  
    function hideError() {
      errorContainer.style.display = 'none';
    }
  });
    
  const root = document.documentElement;
  
  function toggleTheme() {
    const current = root.getAttribute('data-theme') || 'dark';
    const next = current === 'light' ? 'dark' : 'light';
    root.setAttribute('data-theme', next);
    localStorage.setItem('theme', next);
    updateThemeIcon(next);
  }
  
  function updateThemeIcon(theme) {
    const icon = document.getElementById('theme-icon');
    if (theme === 'light') {
      icon.classList.remove('fa-moon');
      icon.classList.add('fa-sun');
    } else {
      icon.classList.remove('fa-sun');
      icon.classList.add('fa-moon');
    }
  }
  
  document.addEventListener('DOMContentLoaded', () => {
    const savedTheme = localStorage.getItem('theme') || 'dark';
    root.setAttribute('data-theme', savedTheme);
    updateThemeIcon(savedTheme);
  });
  