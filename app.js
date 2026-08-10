// Creative Tech Tutorial Index - Unified TouchDesigner & Blender Application Logic

document.addEventListener('DOMContentLoaded', () => {
  const searchInput = document.getElementById('search-input');
  const filterCategory = document.getElementById('filter-category');
  const filterAuthor = document.getElementById('filter-author');
  const sortSelect = document.getElementById('sort-select');
  const filterDurationMin = document.getElementById('filter-duration-min');
  const filterDurationMax = document.getElementById('filter-duration-max');
  const durationValBadge = document.getElementById('duration-val-badge');
  const dualRangeFill = document.getElementById('dual-range-fill');
  const itemsCounter = document.getElementById('items-counter');

  const viewBtns = document.querySelectorAll('.view-btn');
  const viewGrid = document.getElementById('view-grid');
  const viewTable = document.getElementById('view-table');
  const viewLatent = document.getElementById('view-latent');
  const emptyState = document.getElementById('empty-state');

  const gridContainer = document.getElementById('grid-container');
  const tableBody = document.getElementById('table-body');

  const themeBtns = document.querySelectorAll('.theme-btn');

  const videoModal = document.getElementById('video-modal');
  const modalIframe = document.getElementById('modal-iframe');
  const modalVideoTitle = document.getElementById('modal-video-title');
  const modalVideoMeta = document.getElementById('modal-video-meta');
  const modalExternalLink = document.getElementById('modal-external-link');
  const modalCloseBtn = document.getElementById('modal-close-btn');

  // Latent 3D DOM Elements
  const latentViewport = document.getElementById('latent-viewport');
  const latent3dContainer = document.getElementById('latent-3d-container');
  const latentTooltip = document.getElementById('latent-tooltip');
  const btnResetLatent = document.getElementById('btn-reset-latent');

  // Active Software State ('td' vs 'blender')
  let activeSoftware = 'td';
  let activeDataset = window.TD_DATA || [];

  // Application State - Table Index Active by Default
  let currentView = 'grid';
  let searchTerm = '';
  let selectedCategory = 'ALL';
  let selectedAuthor = 'ALL';
  let sortBy = 'default';
  let selectedUserFilter = 'all'; // 'all', 'favorites', 'saved', 'watched'
  let minDurationMinutes = 0;
  let maxDurationMinutes = 40;

  function getItemDurationSeconds(item) {
    if (typeof item.duration_seconds === 'number' && !isNaN(item.duration_seconds)) {
      return item.duration_seconds;
    }
    if (item.duracion) {
      const parts = item.duracion.split(':').map(Number);
      if (parts.length === 3) return parts[0] * 3600 + parts[1] * 60 + parts[2];
      if (parts.length === 2) return parts[0] * 60 + parts[1];
    }
    return 0;
  }

  function formatDuration(seconds) {
    if (seconds === null || seconds === undefined || isNaN(seconds)) return '';
    const sec = parseInt(seconds, 10);
    const m = Math.floor(sec / 60);
    const s = sec % 60;
    const h = Math.floor(m / 60);
    const remM = m % 60;
    const sStr = s < 10 ? '0' + s : s;
    if (h > 0) {
      const mStr = remM < 10 ? '0' + remM : remM;
      return `${h}:${mStr}:${sStr}`;
    }
    return `${m}:${sStr}`;
  }

  function getItemDurationFormatted(item) {
    if (item.duracion) return item.duracion;
    if (typeof item.duration_seconds === 'number' && !isNaN(item.duration_seconds)) {
      return formatDuration(item.duration_seconds);
    }
    return '';
  }

  function updateDurationBadge() {
    if (!durationValBadge || !filterDurationMin || !filterDurationMax) return;

    let minVal = parseInt(filterDurationMin.value, 10);
    let maxVal = parseInt(filterDurationMax.value, 10);

    if (minVal > maxVal) {
      if (document.activeElement === filterDurationMin) {
        minVal = maxVal;
        filterDurationMin.value = minVal;
      } else {
        maxVal = minVal;
        filterDurationMax.value = maxVal;
      }
    }

    minDurationMinutes = minVal;
    maxDurationMinutes = maxVal;

    const minPercent = (minVal / 40) * 100;
    const maxPercent = (maxVal / 40) * 100;

    if (dualRangeFill) {
      dualRangeFill.style.left = `${minPercent}%`;
      dualRangeFill.style.width = `${maxPercent - minPercent}%`;
    }

    const minStr = minVal === 0 ? '0' : `${minVal}`;
    const maxStr = maxVal >= 40 ? '+40' : `${maxVal}`;

    if (minVal === 0 && maxVal >= 40) {
      durationValBadge.textContent = '0 – +40 min';
      durationValBadge.classList.remove('active');
    } else if (minVal === maxVal) {
      durationValBadge.textContent = minVal >= 40 ? '+40 min' : `${minVal} min`;
      durationValBadge.classList.add('active');
    } else {
      durationValBadge.textContent = `${minStr} – ${maxStr} min`;
      durationValBadge.classList.add('active');
    }
  }

  let durationDebounceTimer = null;

  function onDurationInput() {
    // 1. Instant 60 FPS badge & track fill tracking (0ms delay)
    updateDurationBadge();

    // 2. Debounce heavy DOM grid re-rendering while dragging
    if (durationDebounceTimer) {
      clearTimeout(durationDebounceTimer);
    }
    durationDebounceTimer = setTimeout(() => {
      updateUI();
      durationDebounceTimer = null;
    }, 140);
  }

  function onDurationChange() {
    // Instant update on release / stop
    if (durationDebounceTimer) {
      clearTimeout(durationDebounceTimer);
      durationDebounceTimer = null;
    }
    updateDurationBadge();
    updateUI();
  }

  if (filterDurationMin && filterDurationMax) {
    filterDurationMin.addEventListener('input', onDurationInput);
    filterDurationMin.addEventListener('change', onDurationChange);
    filterDurationMax.addEventListener('input', onDurationInput);
    filterDurationMax.addEventListener('change', onDurationChange);
    updateDurationBadge();
  }

  // --- User Personal Library Store (localStorage) ---
  const SVG_ICONS = {
    heartOutline: `<svg class="svg-action-icon fav-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l8.72-8.72 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"></path></svg>`,
    heartFilled: `<svg class="svg-action-icon fav-icon filled" width="14" height="14" viewBox="0 0 24 24" fill="currentColor" stroke="none"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l8.72-8.72 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"></path></svg>`,
    bookmarkOutline: `<svg class="svg-action-icon save-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"></path></svg>`,
    bookmarkFilled: `<svg class="svg-action-icon save-icon filled" width="14" height="14" viewBox="0 0 24 24" fill="currentColor" stroke="none"><path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"></path></svg>`,
    watchedOutline: `<svg class="svg-action-icon watched-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg>`,
    watchedFilled: `<svg class="svg-action-icon watched-icon filled" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>`
  };

  const UserStore = {
    KEY: 'ct_user_tutorials_v1',
    data: {
      favorites: new Set(),
      saved: new Set(),
      watched: new Set()
    },
    init() {
      try {
        const stored = localStorage.getItem(this.KEY);
        if (stored) {
          const parsed = JSON.parse(stored);
          this.data.favorites = new Set(Array.isArray(parsed.favorites) ? parsed.favorites : []);
          this.data.saved = new Set(Array.isArray(parsed.saved) ? parsed.saved : []);
          this.data.watched = new Set(Array.isArray(parsed.watched) ? parsed.watched : []);
        }
      } catch (e) {
        console.warn("Could not load user library from localStorage", e);
      }
      this.updateCounts();
    },
    save() {
      try {
        const toStore = {
          favorites: Array.from(this.data.favorites),
          saved: Array.from(this.data.saved),
          watched: Array.from(this.data.watched)
        };
        localStorage.setItem(this.KEY, JSON.stringify(toStore));
      } catch (e) {
        console.warn("Could not save user library to localStorage", e);
      }
      this.updateCounts();
    },
    isFavorite(vid) { return Boolean(vid && this.data.favorites.has(vid)); },
    isSaved(vid) { return Boolean(vid && this.data.saved.has(vid)); },
    isWatched(vid) { return Boolean(vid && this.data.watched.has(vid)); },
    toggleFavorite(vid) {
      if (!vid) return false;
      if (this.data.favorites.has(vid)) this.data.favorites.delete(vid);
      else this.data.favorites.add(vid);
      this.save();
      return this.isFavorite(vid);
    },
    toggleSaved(vid) {
      if (!vid) return false;
      if (this.data.saved.has(vid)) this.data.saved.delete(vid);
      else this.data.saved.add(vid);
      this.save();
      return this.isSaved(vid);
    },
    toggleWatched(vid) {
      if (!vid) return false;
      if (this.data.watched.has(vid)) this.data.watched.delete(vid);
      else this.data.watched.add(vid);
      this.save();
      return this.isWatched(vid);
    },
    updateCounts() {
      const favBadge = document.getElementById('fav-count');
      const savedBadge = document.getElementById('saved-count');
      const watchedBadge = document.getElementById('watched-count');
      
      const currentDataset = (typeof activeDataset !== 'undefined' && Array.isArray(activeDataset)) ? activeDataset : [];

      let favCount = 0, savedCount = 0, watchedCount = 0;
      for (let i = 0; i < currentDataset.length; i++) {
        const vid = currentDataset[i].vid;
        if (vid) {
          if (this.data.favorites.has(vid)) favCount++;
          if (this.data.saved.has(vid)) savedCount++;
          if (this.data.watched.has(vid)) watchedCount++;
        }
      }

      if (favBadge) favBadge.textContent = favCount;
      if (savedBadge) savedBadge.textContent = savedCount;
      if (watchedBadge) watchedBadge.textContent = watchedCount;
    },
    exportJSON() {
      const jsonStr = JSON.stringify({
        favorites: Array.from(this.data.favorites),
        saved: Array.from(this.data.saved),
        watched: Array.from(this.data.watched)
      }, null, 2);
      const blob = new Blob([jsonStr], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `creative_tech_tutorials_backup_${new Date().toISOString().slice(0, 10)}.json`;
      a.click();
      URL.revokeObjectURL(url);
    },
    importJSON(jsonString) {
      try {
        const parsed = JSON.parse(jsonString);
        if (parsed && typeof parsed === 'object') {
          if (Array.isArray(parsed.favorites)) this.data.favorites = parsed.favorites;
          if (Array.isArray(parsed.saved)) this.data.saved = parsed.saved;
          if (Array.isArray(parsed.watched)) this.data.watched = parsed.watched;
          this.save();
          return true;
        }
      } catch (e) {
        console.error(e);
      }
      return false;
    }
  };

  UserStore.init();

  // Category Colors Taxonomy
  const categoryColors = {
    // TouchDesigner
    "Generative Art": "#e255a1",
    "3D Model & Geometry": "#3b82f6",
    "Scripting & Python": "#22c55e",
    "Audio Reactive": "#a855f7",
    "Instancing & Particles": "#eab308",
    "Pixel Mapping & LED": "#ef4444",
    "Beginner & Fundamentals": "#14b8a6",
    "Projection Mapping": "#f97316",
    "GLSL & Shaders": "#6366f1",
    "Feedback & Post-Processing": "#f43f5e",
    "Interactive & Sensors": "#06b6d4",
    "UI & Systems": "#9ca3af",
    // Blender
    "Geometry Nodes": "#f97316",
    "3D Modeling & Hard Surface": "#3b82f6",
    "Shading & Procedural Materials": "#22c55e",
    "Animation & Rigging": "#a855f7",
    "VFX & Physics Simulation": "#ef4444",
    "Lighting & Rendering (Cycles/EEVEE)": "#eab308",
    "Grease Pencil & 2D Animation": "#14b8a6",
    "Motion Graphics & Loops": "#e255a1",
    "Sculpting & Character Creation": "#f43f5e",
    // Ableton
    "Beat Making": "#f59e0b",
    "Mastering": "#3b82f6",
    "Sound Design & Synths": "#8b5cf6",
    "Mixing & Mastering": "#3b82f6",
    "Vocal Processing": "#ec4899",
    "Audio Effects & Racks": "#10b981",
    "MIDI & Composition": "#06b6d4",
    "Automation & Modulation": "#f97316",
    "Live Performance & Push": "#e11d48",
    "Max for Live & Devices": "#6366f1",
    "Genre Production": "#a855f7",
    // Premiere Pro
    "Video Editing & Cutting": "#0055ff",
    "Color Grading & Lumetri": "#f59e0b",
    "Audio Editing & Sound": "#10b981",
    "Titles & Motion Graphics": "#ec4899",
    "VFX & Green Screen": "#8b5cf6",
    "Export & Settings": "#64748b",
    // After Effects
    "Motion Graphics & Typography": "#ec4899",
    "VFX & Compositing": "#8b5cf6",
    "3D & Camera Tracker": "#06b6d4",
    "Expressions & Automation": "#22c55e",
    "Visual Effects & Particles": "#f97316",
    "Character Animation & Rigging": "#a855f7",
    // Photoshop
    "Photo Editing & Retouching": "#0284c7",
    "Photo Compositing": "#8b5cf6",
    "Graphic Design & Poster": "#ec4899",
    "Digital Painting & Drawing": "#f59e0b",
    "Text Effects & Typography": "#10b981",
    "Generative AI & Firefly": "#f43f5e",
    // Max/MSP
    "Jitter & Visuals": "#e255a1",
    "MSP Audio & DSP": "#3b82f6",
    "Max for Live (M4L)": "#22c55e",
    "MIDI & OSC Control": "#f59e0b",
    "Generative Audio & Algorithmic": "#a855f7",
    "Advanced & Gen~": "#ef4444",
    // Logic Pro
    "Automation": "#10b981",
    "Native Synths": "#8b5cf6",
    "Mixing Techniques": "#3b82f6",
    "MIDI": "#06b6d4",
    "Flex Pitch & Vocals": "#ec4899",
    "Smart Controls & Automation": "#10b981",
    "Orchestral & Composition": "#06b6d4",
    // Sibelius
    "Playback": "#e255a1",
    "Lead Sheets": "#f59e0b",
    // REAPER
    "MIDI & VST": "#6366f1",
    "Customization & Scripts": "#f97316",
    "Audio Editing & Comping": "#e11d48",
    "MIDI & Virtual Instruments": "#6366f1",
    "JSFX & Stock Plugins": "#a855f7",
    "Game Audio & Sound Design": "#14b8a6"
  };

  // Official Downloaded Software SVG Logos
  const TD_LOGO_SVG = `<img src="assets/logos/touchdesigner.png" class="sw-logo-img" alt="TouchDesigner" />`;
  const BLENDER_LOGO_SVG = `<img src="assets/logos/blender.svg" class="sw-logo-img" alt="Blender 3D" />`;
  const ABLETON_LOGO_SVG = `<img src="assets/logos/ableton.svg" class="sw-logo-img" alt="Ableton Live" />`;
  const PREMIERE_LOGO_SVG = `<img src="assets/logos/premiere.svg" class="sw-logo-img" alt="Premiere Pro" />`;
  const AFTEREFFECTS_LOGO_SVG = `<img src="assets/logos/aftereffects.svg" class="sw-logo-img" alt="After Effects" />`;
  const PHOTOSHOP_LOGO_SVG = `<img src="assets/logos/photoshop.svg" class="sw-logo-img" alt="Photoshop" />`;
  const MAXMSP_LOGO_SVG = `<img src="assets/logos/maxmsp.png" class="sw-logo-img" alt="Max/MSP" />`;
  const LOGICPRO_LOGO_SVG = `<img src="assets/logos/logicpro.png" class="sw-logo-img" alt="Logic Pro" />`;
  const REAPER_LOGO_SVG = `<img src="assets/logos/reaper.svg" class="sw-logo-img" alt="REAPER" />`;
  const ILLUSTRATOR_LOGO_SVG = `<img src="assets/logos/illustrator.svg" class="sw-logo-img" alt="Illustrator" />`;
  const DAVINCI_LOGO_SVG = `<img src="assets/logos/davinci.svg" class="sw-logo-img" alt="DaVinci Resolve" />`;
  const SIBELIUS_LOGO_SVG = `<img src="assets/logos/sibelius.png" class="sw-logo-img" alt="Sibelius" />`;
  const VSC_LOGO_SVG = `<img src="assets/logos/vsc.svg" class="sw-logo-img" alt="Visual Studio Code" />`;
  const UNITY_LOGO_SVG = `<img src="assets/logos/unity.svg" class="sw-logo-img" alt="Unity Engine" />`;
  const UNREAL_LOGO_SVG = `<img src="assets/logos/unreal.svg" class="sw-logo-img" alt="Unreal Engine" />`;
  const PYTHON_LOGO_SVG = `<img src="assets/logos/python.svg" class="sw-logo-img" alt="Python" />`;
  const RESOLUME_LOGO_SVG = `<img src="assets/logos/resolume.svg" class="sw-logo-img" alt="Resolume Arena" />`;
  const COMFYUI_LOGO_SVG = `<img src="assets/logos/comfyui.png" class="sw-logo-img" alt="ComfyUI" />`;
  const MADMAPPER_LOGO_SVG = `<img src="assets/logos/madmapper.svg" class="sw-logo-img" alt="MadMapper" />`;

  // Scalable Software Registry (Extensible for 50+ softwares)
  const SOFTWARE_REGISTRY = {
    'td': {
      name: 'TouchDesigner',
      icon: TD_LOGO_SVG,
      title: 'TouchDesigner Tutorials',
      getDataset: () => window.TD_DATA || window.TUTORIALS_DATA || []
    },
    'blender': {
      name: 'Blender 3D',
      icon: BLENDER_LOGO_SVG,
      title: 'Blender 3D Tutorials',
      getDataset: () => window.BLENDER_DATA || window.BLENDER_TUTORIALS_DATA || []
    },
    'ableton': {
      name: 'Ableton Live',
      icon: ABLETON_LOGO_SVG,
      title: 'Ableton Live Tutorials',
      getDataset: () => window.ABLETON_DATA || window.ABLETON_TUTORIALS_DATA || []
    },
    'premiere': {
      name: 'Premiere Pro',
      icon: PREMIERE_LOGO_SVG,
      title: 'Adobe Premiere Pro Tutorials',
      getDataset: () => window.PREMIERE_DATA || window.PREMIERE_TUTORIALS_DATA || []
    },
    'aftereffects': {
      name: 'After Effects',
      icon: AFTEREFFECTS_LOGO_SVG,
      title: 'Adobe After Effects Tutorials',
      getDataset: () => window.AFTEREFFECTS_DATA || window.AFTEREFFECTS_TUTORIALS_DATA || []
    },
    'photoshop': {
      name: 'Photoshop',
      icon: PHOTOSHOP_LOGO_SVG,
      title: 'Adobe Photoshop Tutorials',
      getDataset: () => window.PHOTOSHOP_DATA || window.PHOTOSHOP_TUTORIALS_DATA || []
    },
    'maxmsp': {
      name: 'Max/MSP',
      icon: MAXMSP_LOGO_SVG,
      title: 'Max/MSP Tutorials',
      getDataset: () => window.MAXMSP_DATA || window.MAXMSP_TUTORIALS_DATA || []
    },
    'logicpro': {
      name: 'Logic Pro',
      icon: LOGICPRO_LOGO_SVG,
      title: 'Logic Pro Tutorials',
      getDataset: () => window.LOGICPRO_DATA || window.LOGICPRO_TUTORIALS_DATA || []
    },
    'reaper': {
      name: 'REAPER',
      icon: REAPER_LOGO_SVG,
      title: 'REAPER Tutorials',
      getDataset: () => window.REAPER_DATA || window.REAPER_TUTORIALS_DATA || []
    },
    'illustrator': {
      name: 'Illustrator',
      icon: ILLUSTRATOR_LOGO_SVG,
      title: 'Adobe Illustrator Tutorials',
      getDataset: () => window.ILLUSTRATOR_DATA || window.ILLUSTRATOR_TUTORIALS_DATA || []
    },
    'davinci': {
      name: 'DaVinci Resolve',
      icon: DAVINCI_LOGO_SVG,
      title: 'DaVinci Resolve Tutorials',
      getDataset: () => window.DAVINCI_DATA || window.DAVINCI_TUTORIALS_DATA || []
    },
    'sibelius': {
      name: 'Sibelius',
      icon: SIBELIUS_LOGO_SVG,
      title: 'Avid Sibelius Tutorials',
      getDataset: () => window.SIBELIUS_DATA || window.SIBELIUS_TUTORIALS_DATA || []
    },
    'vsc': {
      name: 'Visual Studio Code',
      icon: VSC_LOGO_SVG,
      title: 'Visual Studio Code Tutorials',
      getDataset: () => window.VSC_DATA || window.VSC_TUTORIALS_DATA || []
    },
    'unity': {
      name: 'Unity Engine',
      icon: UNITY_LOGO_SVG,
      title: 'Unity Engine Tutorials',
      getDataset: () => window.UNITY_DATA || window.UNITY_TUTORIALS_DATA || []
    },
    'unreal': {
      name: 'Unreal Engine',
      icon: UNREAL_LOGO_SVG,
      title: 'Unreal Engine Tutorials',
      getDataset: () => window.UNREAL_DATA || window.UNREAL_TUTORIALS_DATA || []
    },
    'python': {
      name: 'Python',
      icon: PYTHON_LOGO_SVG,
      title: 'Python Tutorials',
      getDataset: () => window.PYTHON_DATA || window.PYTHON_TUTORIALS_DATA || []
    },
    'resolume': {
      name: 'Resolume Arena',
      icon: RESOLUME_LOGO_SVG,
      title: 'Resolume Arena Tutorials',
      getDataset: () => window.RESOLUME_DATA || window.RESOLUME_TUTORIALS_DATA || []
    },
    'comfyui': {
      name: 'ComfyUI',
      icon: COMFYUI_LOGO_SVG,
      title: 'ComfyUI Tutorials',
      getDataset: () => window.COMFYUI_DATA || window.COMFYUI_TUTORIALS_DATA || []
    },
    'madmapper': {
      name: 'MadMapper',
      icon: MADMAPPER_LOGO_SVG,
      title: 'MadMapper Tutorials',
      getDataset: () => window.MADMAPPER_DATA || window.MADMAPPER_TUTORIALS_DATA || []
    }
  };

  const softwareSelect = document.getElementById('software-select');
  const softwareIcon = document.getElementById('software-icon');
  const appTitle = document.getElementById('app-title');
  const headerSubtitle = document.getElementById('header-subtitle');
  const homeView = document.getElementById('home-view');
  const dbView = document.getElementById('db-view');
  const btnGoHome = document.getElementById('btn-go-home');
  const softwareSelectContainer = document.querySelector('.software-select-container');

  function showHome() {
    destroyThreeScene();
    if (homeView) homeView.style.display = 'block';
    if (dbView) dbView.style.display = 'none';
    if (btnGoHome) btnGoHome.style.display = 'none';
    if (appTitle) appTitle.textContent = 'Software Tutorial Library';
    if (headerSubtitle) headerSubtitle.style.display = 'block';
    window.location.hash = '#home';
    window.scrollTo(0, 0);
  }

  function showDatabase(swKey) {
    if (swKey && SOFTWARE_REGISTRY[swKey]) {
      switchSoftware(swKey);
    }
    if (homeView) homeView.style.display = 'none';
    if (dbView) dbView.style.display = 'block';
    if (btnGoHome) btnGoHome.style.display = 'inline-flex';
    if (headerSubtitle) headerSubtitle.style.display = 'none';
    window.location.hash = `#${activeSoftware}`;
    window.scrollTo(0, 0);
  }

  // Bind Home Button
  if (btnGoHome) {
    btnGoHome.addEventListener('click', () => {
      showHome();
    });
  }

  // Bind Software Cards on Home View
  document.querySelectorAll('.software-card').forEach(card => {
    card.addEventListener('click', () => {
      const sw = card.dataset.software;
      showDatabase(sw);
    });
  });

  // Home View Software Live Search Filter
  const homeSearchInput = document.getElementById('home-search-input');
  const homeSearchEmpty = document.getElementById('home-search-empty');

  if (homeSearchInput) {
    homeSearchInput.addEventListener('input', (e) => {
      const q = e.target.value.toLowerCase().trim();
      let totalVisibleCards = 0;

      document.querySelectorAll('.software-domain-section').forEach(section => {
        let visibleCardsInSection = 0;
        section.querySelectorAll('.software-card').forEach(card => {
          const swName = card.querySelector('.software-card-title')?.textContent.toLowerCase() || '';
          const swKey = card.dataset.software || '';
          
          if (!q || swName.includes(q) || swKey.includes(q)) {
            card.style.display = 'flex';
            visibleCardsInSection++;
            totalVisibleCards++;
          } else {
            card.style.display = 'none';
          }
        });

        section.style.display = visibleCardsInSection > 0 ? 'block' : 'none';
      });

      if (homeSearchEmpty) {
        homeSearchEmpty.style.display = totalVisibleCards === 0 ? 'block' : 'none';
      }
    });
  }

  // URL Hash Router
  function checkHash() {
    const hash = window.location.hash.replace('#', '');
    if (hash && SOFTWARE_REGISTRY[hash]) {
      showDatabase(hash);
    } else if (hash === 'home' || !hash) {
      showHome();
    }
  }

  window.addEventListener('hashchange', checkHash);

  function switchSoftware(swKey) {
    const swInfo = SOFTWARE_REGISTRY[swKey];
    if (!swInfo) return;

    activeSoftware = swKey;
    activeDataset = swInfo.getDataset();
    if (appTitle) appTitle.textContent = swInfo.title;
    if (softwareIcon) softwareIcon.innerHTML = swInfo.icon;

    if (searchInput) searchInput.value = '';
    searchTerm = '';
    populateFilters();
    updateUI();

    if (currentView === 'latent') {
      initThreeScene();
    }

    window.scrollTo(0, 0);
  }

  // Universal Custom Dropdown Widget Generator (Bypasses Mac OS Native Popovers)
  const softwareIconsMap = {
    'td': TD_LOGO_SVG,
    'blender': BLENDER_LOGO_SVG,
    'ableton': ABLETON_LOGO_SVG,
    'premiere': PREMIERE_LOGO_SVG,
    'aftereffects': AFTEREFFECTS_LOGO_SVG,
    'photoshop': PHOTOSHOP_LOGO_SVG,
    'maxmsp': MAXMSP_LOGO_SVG,
    'logicpro': LOGICPRO_LOGO_SVG,
    'reaper': REAPER_LOGO_SVG
  };

  function closeAllCustomDropdowns() {
    document.querySelectorAll('.custom-select-portal').forEach(m => m.remove());
    document.querySelectorAll('.custom-select-widget.open').forEach(w => w.classList.remove('open'));
  }

  function createCustomDropdown(selectEl, iconMap = {}) {
    if (!selectEl) return;

    let parent = selectEl.parentElement;
    let widget = parent.querySelector(`.custom-select-widget[data-select-id="${selectEl.id}"]`);

    if (!widget) {
      widget = document.createElement('div');
      widget.className = 'custom-select-widget';
      widget.setAttribute('data-select-id', selectEl.id);
      selectEl.style.display = 'none';
      parent.appendChild(widget);
    }

    if (selectEl.id === 'sort-select') {
      widget.classList.add('align-right');
    }

    const selectedOption = selectEl.options[selectEl.selectedIndex] || selectEl.options[0];
    const initialText = selectedOption ? selectedOption.textContent : '';
    const initialVal = selectedOption ? selectedOption.value : '';
    const initialIcon = iconMap[initialVal] || '';

    let optionsHtml = '';
    Array.from(selectEl.options).forEach(opt => {
      const isSelected = opt.value === initialVal;
      const optIcon = iconMap[opt.value] ? `<span class="custom-select-icon" style="margin-right:6px;">${iconMap[opt.value]}</span>` : '';
      optionsHtml += `
        <div class="custom-select-option ${isSelected ? 'selected' : ''}" data-value="${opt.value}">
          <span>${optIcon}${opt.textContent}</span>
          ${isSelected ? '<span class="check-icon">✓</span>' : ''}
        </div>
      `;
    });

    widget.innerHTML = `
      <button type="button" class="custom-select-trigger" aria-haspopup="listbox" aria-expanded="false">
        ${initialIcon ? `<span class="custom-select-icon">${initialIcon}</span>` : ''}
        <span class="custom-select-text">${initialText}</span>
        <span class="custom-select-arrow">▾</span>
      </button>
      <div class="custom-select-menu-template" style="display:none;">
        <div class="custom-select-options-list">
          ${optionsHtml}
        </div>
      </div>
    `;

    const trigger = widget.querySelector('.custom-select-trigger');
    const menuTemplate = widget.querySelector('.custom-select-menu-template');

    trigger.addEventListener('click', (e) => {
      e.stopPropagation();
      const isOpen = widget.classList.contains('open');
      closeAllCustomDropdowns();

      if (isOpen) return;

      const rect = trigger.getBoundingClientRect();
      const portalMenu = document.createElement('div');
      portalMenu.className = 'custom-select-menu custom-select-portal open-portal';
      portalMenu.innerHTML = menuTemplate.innerHTML;

      portalMenu.style.position = 'fixed';
      portalMenu.style.zIndex = '999999';
      portalMenu.style.top = `${rect.bottom + 6}px`;

      const isRightAligned = selectEl.id === 'sort-select' || widget.classList.contains('align-right') || rect.right > (window.innerWidth - 260);

      if (isRightAligned) {
        portalMenu.style.left = 'auto';
        portalMenu.style.right = `${window.innerWidth - rect.right}px`;
      } else {
        portalMenu.style.left = `${rect.left}px`;
        portalMenu.style.right = 'auto';
      }

      document.body.appendChild(portalMenu);
      widget.classList.add('open');

      const portalOptionsList = portalMenu.querySelector('.custom-select-options-list');
      if (portalOptionsList) {
        portalOptionsList.addEventListener('wheel', (evt) => {
          portalOptionsList.scrollTop += evt.deltaY;
        }, { passive: true });

        portalOptionsList.querySelectorAll('.custom-select-option').forEach(opt => {
          opt.addEventListener('click', (evt) => {
            evt.stopPropagation();
            const val = opt.dataset.value;
            selectEl.value = val;
            selectEl.dispatchEvent(new Event('change', { bubbles: true }));
            closeAllCustomDropdowns();
            syncAllCustomDropdowns();
          });
        });
      }
    });
  }

  function syncAllCustomDropdowns() {
    createCustomDropdown(softwareSelect, softwareIconsMap);
    createCustomDropdown(filterCategory);
    createCustomDropdown(filterAuthor);
    createCustomDropdown(sortSelect);
  }

  document.addEventListener('click', closeAllCustomDropdowns);
  window.addEventListener('resize', closeAllCustomDropdowns);
  window.addEventListener('scroll', closeAllCustomDropdowns, { passive: true });

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') closeAllCustomDropdowns();
  });

  if (softwareSelect) {
    softwareSelect.addEventListener('change', (e) => {
      switchSoftware(e.target.value);
    });
  }

  // 1. Populate Dropdowns dynamically based on active software
  function populateFilters() {
    // Category Filter
    filterCategory.innerHTML = '<option value="ALL">All Topics</option>';
    const categoriesSet = new Set();
    activeDataset.forEach(item => {
      if (item.categoria_principal) categoriesSet.add(item.categoria_principal);
    });
    Array.from(categoriesSet).sort().forEach(cat => {
      const opt = document.createElement('option');
      opt.value = cat;
      opt.textContent = cat;
      filterCategory.appendChild(opt);
    });

    // Author Filter
    filterAuthor.innerHTML = '<option value="ALL">All Creators</option>';
    const authorsSet = new Set();
    activeDataset.forEach(item => {
      if (item.autor && item.autor !== 'Desconocido') {
        authorsSet.add(item.autor);
      }
    });

    Array.from(authorsSet).sort().forEach(author => {
      const opt = document.createElement('option');
      opt.value = author;
      opt.textContent = author;
      filterAuthor.appendChild(opt);
    });

    selectedCategory = 'ALL';
    selectedAuthor = 'ALL';
    filterCategory.value = 'ALL';
    filterAuthor.value = 'ALL';

    syncAllCustomDropdowns();
  }

  function renderTag(tag) {
    const safeTag = tag.replace(/'/g, "\\'");
    return `<span class="topic-tag" data-tag="${tag}" onclick="event.stopPropagation(); window.filterByTopic('${safeTag}')">${tag}</span>`;
  }

  function renderCreatorLink(author) {
    if (!author || author === 'Desconocido') return '<span class="creator-name">Unknown</span>';
    
    let handle = author.replace(/[\s\-\&\.\,\'\"]/g, '');
    let channelUrl = `https://www.youtube.com/@${handle}`;

    if (author === 'Derivative' || author === 'Ben Voigt') channelUrl = 'https://www.youtube.com/@TouchDesigner';
    else if (author === 'Blender Guru') channelUrl = 'https://www.youtube.com/@blenderguru';
    else if (author === 'Blender Studio' || author === 'Blender Official') channelUrl = 'https://www.youtube.com/@BlenderOfficial';
    else if (author === 'The Interactive & Immersive HQ') channelUrl = 'https://www.youtube.com/@InteractiveImmersiveHQ';
    else if (author === 'Ducky 3D') channelUrl = 'https://www.youtube.com/@Ducky3D';
    else if (author === 'CG Boost') channelUrl = 'https://www.youtube.com/@CGBoost';
    else if (author === 'Grant Abbitt' || author === 'Grant Abbitt (Gabbitt)') channelUrl = 'https://www.youtube.com/@gabbitt';
    else if (author === 'CG Matter' || author === 'Default Cube') channelUrl = 'https://www.youtube.com/@CGMatter';
    else if (author === 'Ableton') channelUrl = 'https://www.youtube.com/@Ableton';
    else if (author === 'You Suck at Producing') channelUrl = 'https://www.youtube.com/@yousuckatproducing';
    else if (author === 'Seed to Stage') channelUrl = 'https://www.youtube.com/@SeedtoStage';
    else if (author === 'Venus Theory') channelUrl = 'https://www.youtube.com/@VenusTheory';
    else if (author === 'TAETRO') channelUrl = 'https://www.youtube.com/@TAETRO';
    else if (author === 'Production Music Live' || author === 'Ableton Tips by PML') channelUrl = 'https://www.youtube.com/@ProductionMusicLive';
    else if (author === 'In The Mix') channelUrl = 'https://www.youtube.com/@inthemix';
    else if (author === 'Cinecom.net' || author === 'Cinecom') channelUrl = 'https://www.youtube.com/@cinecom';
    else if (author === 'Peter McKinnon') channelUrl = 'https://www.youtube.com/@petermckinnon';
    else if (author === 'Premiere Gal') channelUrl = 'https://www.youtube.com/@PremiereGal';
    else if (author === 'Justin Odisho') channelUrl = 'https://www.youtube.com/@JustinOdisho';
    else if (author === 'Ben Marriott') channelUrl = 'https://www.youtube.com/@benmarriott';
    else if (author === 'SonduckFilm' || author === 'Sonduck Film') channelUrl = 'https://www.youtube.com/@SonduckFilm';
    else if (author === 'PiXimperfect') channelUrl = 'https://www.youtube.com/@PiXimperfect';
    else if (author === 'PHLEARN') channelUrl = 'https://www.youtube.com/@phlearn';
    else if (author === 'Nemanja Sekulic') channelUrl = 'https://www.youtube.com/@NemanjaSekulic';
    else if (author === 'Benny Productions') channelUrl = 'https://www.youtube.com/@BennyProductions';
    else if (author === 'Federico Foderaro') channelUrl = 'https://www.youtube.com/@FedericoFoderaro';
    else if (author === 'REAPER Mania' || author === 'Kenny Gioia') channelUrl = 'https://www.youtube.com/@REAPERMania';
    else if (author === 'The REAPER Blog') channelUrl = 'https://www.youtube.com/@TheREAPERBlog';
    else if (author === 'Music Tech Help Guy') channelUrl = 'https://www.youtube.com/@MusicTechHelpGuy';
    else if (author === 'Why Logic Pro Rules') channelUrl = 'https://www.youtube.com/@WhyLogicProRules';

    return `<a class="creator-link" href="${channelUrl}" target="_blank" onclick="event.stopPropagation()" title="${author}'s YouTube Channel">${author}</a>`;
  }

  // Global Topic Tag Click Filter Handler
  window.filterByTopic = function(tag) {
    let matchedOption = false;
    for (let opt of filterCategory.options) {
      if (opt.value === tag || opt.textContent.includes(tag)) {
        filterCategory.value = opt.value;
        selectedCategory = opt.value;
        matchedOption = true;
        break;
      }
    }

    if (!matchedOption) {
      searchInput.value = tag;
      searchTerm = tag;
    }

    syncAllCustomDropdowns();
    updateUI();
  };

  // 2. Filtering & Sorting Engine
  function getFilteredData() {
    let result = activeDataset.filter(item => {
      // User collections filter
      if (selectedUserFilter === 'favorites' && (!item.vid || !UserStore.isFavorite(item.vid))) {
        return false;
      }
      if (selectedUserFilter === 'saved' && (!item.vid || !UserStore.isSaved(item.vid))) {
        return false;
      }
      if (selectedUserFilter === 'watched' && (!item.vid || !UserStore.isWatched(item.vid))) {
        return false;
      }

      if (searchTerm) {
        const query = searchTerm.toLowerCase();
        const titleMatch = item.titulo.toLowerCase().includes(query);
        const authorMatch = item.autor.toLowerCase().includes(query);
        const tagMatch = item.tags.some(t => t.toLowerCase().includes(query));
        const catMatch = item.categoria_principal.toLowerCase().includes(query);
        if (!titleMatch && !authorMatch && !tagMatch && !catMatch) {
          return false;
        }
      }

      if (selectedCategory !== 'ALL') {
        const inPrimary = item.categoria_principal === selectedCategory;
        const inTags = item.tags.includes(selectedCategory);
        if (!inPrimary && !inTags) return false;
      }

      if (selectedAuthor !== 'ALL' && item.autor !== selectedAuthor) {
        return false;
      }

      if (minDurationMinutes > 0 || maxDurationMinutes < 40) {
        const itemSec = getItemDurationSeconds(item);
        const minSec = minDurationMinutes * 60;
        const maxSec = maxDurationMinutes >= 40 ? Infinity : (maxDurationMinutes === 0 ? 60 : maxDurationMinutes * 60);

        if (itemSec < minSec || itemSec > maxSec) {
          return false;
        }
      }

      return true;
    });

    if (sortBy === 'popular-desc') {
      result.sort((a, b) => (b.views || 0) - (a.views || 0));
    } else if (sortBy === 'popular-asc') {
      result.sort((a, b) => (a.views || 0) - (b.views || 0));
    } else if (sortBy === 'recent-asc') {
      result.sort((a, b) => (b.upload_date || '').localeCompare(a.upload_date || ''));
    } else if (sortBy === 'recent-desc') {
      result.sort((a, b) => (a.upload_date || '').localeCompare(b.upload_date || ''));
    } else if (sortBy === 'dur-asc') {
      result.sort((a, b) => getItemDurationSeconds(a) - getItemDurationSeconds(b));
    } else if (sortBy === 'dur-desc') {
      result.sort((a, b) => getItemDurationSeconds(b) - getItemDurationSeconds(a));
    } else if (sortBy === 'title-asc') {
      result.sort((a, b) => a.titulo.localeCompare(b.titulo));
    } else if (sortBy === 'title-desc') {
      result.sort((a, b) => b.titulo.localeCompare(a.titulo));
    } else if (sortBy === 'author-asc') {
      result.sort((a, b) => a.autor.localeCompare(b.autor));
    }

    return result;
  }

  function formatViews(num) {
    if (!num) return '';
    if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M views';
    if (num >= 1000) return (num / 1000).toFixed(1) + 'K views';
    return num.toLocaleString() + ' views';
  }

  function formatDate(dateStr) {
    if (!dateStr) return '';
    try {
      const parts = dateStr.split('-');
      if (parts.length === 3) {
        const d = new Date(parts[0], parts[1] - 1, parts[2]);
        return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
      }
    } catch(e) {}
    return dateStr;
  }

  // 3. Render Grid View
  function renderGrid(data) {
    gridContainer.innerHTML = '';
    const fragment = document.createDocumentFragment();

    data.forEach(item => {
      const card = document.createElement('div');
      card.className = 'card-item';
      const isFav = item.vid && UserStore.isFavorite(item.vid);
      const isSaved = item.vid && UserStore.isSaved(item.vid);
      const isWatched = item.vid && UserStore.isWatched(item.vid);

      if (isWatched) card.classList.add('card-watched');
      card.addEventListener('click', () => openModal(item));

      const thumbUrl = item.vid 
        ? `https://img.youtube.com/vi/${item.vid}/hqdefault.jpg`
        : 'https://images.unsplash.com/photo-1550745165-9bc0b252726f?w=600';

      const tagsHtml = item.tags.slice(0, 2).map(t => renderTag(t)).join(' ');
      const viewsStr = item.views ? ` • ${formatViews(item.views)}` : '';
      const dateStr = item.upload_date ? ` • ${formatDate(item.upload_date)}` : '';
      const durationText = getItemDurationFormatted(item);
      const creatorHtml = renderCreatorLink(item.autor);

      card.innerHTML = `
        <div class="card-thumb-frame">
          <img class="card-thumb-img" src="${thumbUrl}" alt="${item.titulo}" loading="lazy" />
          ${durationText ? `<span class="card-duration-badge">${durationText}</span>` : ''}
          <div class="card-actions-overlay" onclick="event.stopPropagation()">
            <button class="card-act-btn ${isFav ? 'active-fav' : ''}" data-act="fav" data-vid="${item.vid || ''}" title="${isFav ? 'Remove Favorite' : 'Favorite'}">
              ${isFav ? SVG_ICONS.heartFilled : SVG_ICONS.heartOutline}
            </button>
            <button class="card-act-btn ${isSaved ? 'active-saved' : ''}" data-act="save" data-vid="${item.vid || ''}" title="${isSaved ? 'Remove Saved' : 'Watch Later'}">
              ${isSaved ? SVG_ICONS.bookmarkFilled : SVG_ICONS.bookmarkOutline}
            </button>
            <button class="card-act-btn ${isWatched ? 'active-watched' : ''}" data-act="watched" data-vid="${item.vid || ''}" title="${isWatched ? 'Mark Unwatched' : 'Mark Watched'}">
              ${isWatched ? SVG_ICONS.watchedFilled : SVG_ICONS.watchedOutline}
            </button>
          </div>
          ${isWatched ? `<span class="card-watched-badge">${SVG_ICONS.watchedFilled} Watched</span>` : ''}
        </div>
        <div class="card-body">
          <h4 class="card-title">${item.titulo}</h4>
          <div class="card-footer">
            <div class="card-meta-row">${creatorHtml}${viewsStr}${dateStr}</div>
            <div class="card-tags-row">${tagsHtml}</div>
          </div>
        </div>
      `;

      fragment.appendChild(card);
    });

    gridContainer.appendChild(fragment);
  }

  // 4. Render Table View
  function renderTable(data) {
    tableBody.innerHTML = '';
    const fragment = document.createDocumentFragment();

    data.forEach(item => {
      const tr = document.createElement('tr');
      const isFav = item.vid && UserStore.isFavorite(item.vid);
      const isSaved = item.vid && UserStore.isSaved(item.vid);
      const isWatched = item.vid && UserStore.isWatched(item.vid);

      if (isWatched) tr.classList.add('tr-watched');
      tr.addEventListener('click', () => openModal(item));

      const tagsHtml = item.tags.map(t => renderTag(t)).join(' ');
      const viewsText = item.views ? formatViews(item.views) : 'N/A';
      const dateText = item.upload_date ? formatDate(item.upload_date) : 'N/A';
      const durationText = getItemDurationFormatted(item);
      const durationStr = durationText ? ` • ${durationText}` : '';
      const creatorHtml = renderCreatorLink(item.autor);

      tr.innerHTML = `
        <td>
          <div class="table-title">
            ${isWatched ? `<span class="table-watched-icon" title="Watched">${SVG_ICONS.watchedFilled} </span>` : ''}
            ${item.titulo}
          </div>
        </td>
        <td>
          ${creatorHtml}
          <div style="font-size: 11px; color: var(--text-muted);">${viewsText} • ${dateText}${durationStr}</div>
        </td>
        <td>${tagsHtml}</td>
        <td style="text-align: center;" onclick="event.stopPropagation()">
          <div class="table-actions-cell" onclick="event.stopPropagation()">
            <button class="table-act-btn ${isFav ? 'active-fav' : ''}" data-act="fav" data-vid="${item.vid || ''}" title="${isFav ? 'Remove Favorite' : 'Favorite'}">
              ${isFav ? SVG_ICONS.heartFilled : SVG_ICONS.heartOutline}
            </button>
            <button class="table-act-btn ${isSaved ? 'active-saved' : ''}" data-act="save" data-vid="${item.vid || ''}" title="${isSaved ? 'Remove Saved' : 'Watch Later'}">
              ${isSaved ? SVG_ICONS.bookmarkFilled : SVG_ICONS.bookmarkOutline}
            </button>
            <button class="table-act-btn ${isWatched ? 'active-watched' : ''}" data-act="watched" data-vid="${item.vid || ''}" title="${isWatched ? 'Mark Unwatched' : 'Mark Watched'}">
              ${isWatched ? SVG_ICONS.watchedFilled : SVG_ICONS.watchedOutline}
            </button>
            <a href="${item.enlace}" target="_blank" class="link-action" onclick="event.stopPropagation()">
              Open ↗
            </a>
          </div>
        </td>
      `;

      fragment.appendChild(tr);
    });

    tableBody.appendChild(fragment);
  }

  // Global Event Delegation for Card & Table Action Buttons
  function handleActionClick(e) {
    const actBtn = e.target.closest('[data-act]');
    if (!actBtn) return;
    
    e.stopPropagation();
    if (e.stopImmediatePropagation) e.stopImmediatePropagation();

    const vid = actBtn.dataset.vid;
    const act = actBtn.dataset.act;
    if (!vid || !act) return;

    if (act === 'fav') {
      const newState = UserStore.toggleFavorite(vid);
      actBtn.innerHTML = newState ? SVG_ICONS.heartFilled : SVG_ICONS.heartOutline;
      actBtn.classList.toggle('active-fav', newState);
      actBtn.title = newState ? 'Remove Favorite' : 'Favorite';
    } else if (act === 'save') {
      const newState = UserStore.toggleSaved(vid);
      actBtn.innerHTML = newState ? SVG_ICONS.bookmarkFilled : SVG_ICONS.bookmarkOutline;
      actBtn.classList.toggle('active-saved', newState);
      actBtn.title = newState ? 'Remove Saved' : 'Watch Later';
    } else if (act === 'watched') {
      const newState = UserStore.toggleWatched(vid);
      actBtn.innerHTML = newState ? SVG_ICONS.watchedFilled : SVG_ICONS.watchedOutline;
      actBtn.classList.toggle('active-watched', newState);
      actBtn.title = newState ? 'Mark Unwatched' : 'Mark Watched';

      const card = actBtn.closest('.card-item');
      if (card) {
        card.classList.toggle('card-watched', newState);
        let badge = card.querySelector('.card-watched-badge');
        if (newState && !badge) {
          const frame = card.querySelector('.card-thumb-frame');
          if (frame) {
            const span = document.createElement('span');
            span.className = 'card-watched-badge';
            span.innerHTML = `${SVG_ICONS.watchedFilled} Watched`;
            frame.appendChild(span);
          }
        } else if (!newState && badge) {
          badge.remove();
        }
      }

      const tr = actBtn.closest('tr');
      if (tr) {
        tr.classList.toggle('tr-watched', newState);
      }
    }

    if (selectedUserFilter !== 'all') updateUI();
  }

  if (gridContainer) gridContainer.addEventListener('click', handleActionClick, true);
  if (tableBody) tableBody.addEventListener('click', handleActionClick, true);

  // --- 5. Three.js 3D Latent Space Universe Engine ---
  let scene, camera, renderer, controls;
  let cardMeshes = [];
  let raycaster, mouseVector;
  let hoveredCard = null;
  let animFrameId = null;

  function stopThreeLoop() {
    if (animFrameId) {
      cancelAnimationFrame(animFrameId);
      animFrameId = null;
    }
  }

  function destroyThreeScene() {
    stopThreeLoop();
    if (scene) {
      scene.traverse(object => {
        if (object.geometry) object.geometry.dispose();
        if (object.material) {
          if (Array.isArray(object.material)) {
            object.material.forEach(m => {
              if (m.map) m.map.dispose();
              m.dispose();
            });
          } else {
            if (object.material.map) object.material.map.dispose();
            object.material.dispose();
          }
        }
      });
      scene = null;
    }
    if (renderer) {
      if (renderer.domElement && renderer.domElement.parentElement) {
        renderer.domElement.parentElement.removeChild(renderer.domElement);
      }
      renderer.dispose();
      renderer = null;
    }
    camera = null;
    controls = null;
    cardMeshes = [];
    hoveredCard = null;
  }

  function initThreeScene() {
    if (typeof THREE === 'undefined' || !latent3dContainer) return;

    destroyThreeScene();

    const width = latent3dContainer.clientWidth || 1000;
    const height = latent3dContainer.clientHeight || 680;

    scene = new THREE.Scene();
    camera = new THREE.PerspectiveCamera(55, width / height, 1, 2500);
    camera.position.set(0, 0, 320);

    renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    latent3dContainer.appendChild(renderer.domElement);

    if (typeof THREE.OrbitControls !== 'undefined') {
      controls = new THREE.OrbitControls(camera, renderer.domElement);
      controls.enableDamping = true;
      controls.dampingFactor = 0.05;
      controls.rotateSpeed = 0.8;
      controls.enableZoom = false; // Disable wheel zoom so mouse scroll moves the webpage naturally
    }

    const ambientLight = new THREE.AmbientLight(0xffffff, 0.9);
    scene.add(ambientLight);

    const dirLight = new THREE.DirectionalLight(0xffffff, 0.6);
    dirLight.position.set(100, 200, 150);
    scene.add(dirLight);

    // Cosmic Starfield Background
    const starsGeo = new THREE.BufferGeometry();
    const starsCount = 1400;
    const posArray = new Float32Array(starsCount * 3);

    for (let i = 0; i < starsCount * 3; i++) {
      posArray[i] = (Math.random() - 0.5) * 1200;
    }
    starsGeo.setAttribute('position', new THREE.BufferAttribute(posArray, 3));
    const starsMat = new THREE.PointsMaterial({
      size: 1.5,
      color: 0x888888,
      transparent: true,
      opacity: 0.5
    });
    const starField = new THREE.Points(starsGeo, starsMat);
    scene.add(starField);

    // 3D Latent Space Bounding Box Wireframe
    const boxGeo = new THREE.BoxGeometry(450, 450, 450);
    const boxEdges = new THREE.EdgesGeometry(boxGeo);
    const boxLineMat = new THREE.LineBasicMaterial({
      color: activeSoftware === 'blender' ? 0xea580c : 0x666666,
      linewidth: 1.5,
      transparent: true,
      opacity: 0.45
    });
    const boundingBoxMesh = new THREE.LineSegments(boxEdges, boxLineMat);
    scene.add(boundingBoxMesh);

    // Build 3D Thumbnail Cards Mesh
    const textureLoader = new THREE.TextureLoader();
    const cardGeo = new THREE.PlaneGeometry(16 * 0.85, 9 * 0.85);
    const borderGeo = new THREE.PlaneGeometry(16.6 * 0.85, 9.6 * 0.85);

    cardMeshes = [];

    activeDataset.forEach(item => {
      const vid = item.vid;
      const thumbUrl = vid 
        ? `https://img.youtube.com/vi/${vid}/hqdefault.jpg`
        : 'https://images.unsplash.com/photo-1550745165-9bc0b252726f?w=600';

      const catColorHex = categoryColors[item.categoria_principal] || (activeSoftware === 'blender' ? '#f97316' : '#ffffff');

      const texture = textureLoader.load(thumbUrl);

      const cardMat = new THREE.MeshBasicMaterial({
        map: texture,
        side: THREE.DoubleSide,
        transparent: true,
        opacity: 0.95
      });

      const cardMesh = new THREE.Mesh(cardGeo, cardMat);

      const borderMat = new THREE.MeshBasicMaterial({
        color: new THREE.Color(catColorHex),
        side: THREE.DoubleSide,
        transparent: true,
        opacity: 0.8
      });
      const borderMesh = new THREE.Mesh(borderGeo, borderMat);
      borderMesh.position.z = -0.05;
      cardMesh.add(borderMesh);

      const px = (item.latent_x || 0) * 1.8;
      const py = (item.latent_y || 0) * 1.8;
      const pz = (item.latent_z || 0) * 1.8;

      cardMesh.position.set(px, py, pz);
      cardMesh.rotation.y = (Math.random() - 0.5) * 0.2;
      cardMesh.rotation.x = (Math.random() - 0.5) * 0.1;

      cardMesh.userData = {
        item: item,
        borderMat: borderMat,
        cardMat: cardMat,
        originalPos: new THREE.Vector3(px, py, pz)
      };

      scene.add(cardMesh);
      cardMeshes.push(cardMesh);
    });

    raycaster = new THREE.Raycaster();
    mouseVector = new THREE.Vector2(-999, -999);

    latent3dContainer.addEventListener('pointerdown', on3dPointerDown);
    latent3dContainer.addEventListener('pointermove', on3dPointerMove);
    // Attach wheel/gesture to the PARENT viewport so zoom works everywhere in the frame
    const zoomTarget = latentViewport || latent3dContainer;
    zoomTarget.addEventListener('wheel', on3dWheel, { passive: false, capture: true });
    if (renderer && renderer.domElement) {
      renderer.domElement.addEventListener('wheel', on3dWheel, { passive: false, capture: true });
    }
    latent3dContainer.addEventListener('click', on3dClick);
    window.addEventListener('resize', on3dResize);

    if (btnResetLatent) {
      btnResetLatent.addEventListener('click', () => {
        camera.position.set(0, 0, 320);
        targetZoomDist = 320;
        if (controls) controls.reset();
      });
    }

    animate3d();
  }

  function on3dResize() {
    if (!renderer || !camera || !latent3dContainer) return;
    const w = latent3dContainer.clientWidth;
    const h = latent3dContainer.clientHeight;
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
    renderer.setSize(w, h);
  }

  let isDragging3D = false;
  let dragStartPos = { x: 0, y: 0 };

  function on3dPointerDown(e) {
    isDragging3D = false;
    dragStartPos = { x: e.clientX, y: e.clientY };
  }

  function on3dPointerMove(e) {
    const rect = latent3dContainer.getBoundingClientRect();
    mouseVector.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
    mouseVector.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;

    if (e.buttons > 0) {
      const dx = Math.abs(e.clientX - dragStartPos.x);
      const dy = Math.abs(e.clientY - dragStartPos.y);
      if (dx > 4 || dy > 4) {
        isDragging3D = true;
      }
    }
  }

  // Track Shift key state manually — Safari doesn't always report e.shiftKey on wheel events from trackpad
  let isShiftDown = false;
  window.addEventListener('keydown', (e) => { if (e.key === 'Shift') isShiftDown = true; });
  window.addEventListener('keyup', (e) => { if (e.key === 'Shift') isShiftDown = false; });
  window.addEventListener('blur', () => { isShiftDown = false; });

  let targetZoomDist = 320;

  function doLatentZoom(delta) {
    if (!camera || !controls) return;
    const target = controls.target || new THREE.Vector3(0, 0, 0);
    const offset = camera.position.clone().sub(target);
    const currentActualDist = offset.length();

    if (Math.abs(targetZoomDist - currentActualDist) > 400) {
      targetZoomDist = currentActualDist;
    }

    const factor = Math.exp(delta * 0.0015);
    targetZoomDist = Math.max(25, Math.min(1400, targetZoomDist * factor));
  }

  function on3dWheel(e) {
    if (isShiftDown || e.shiftKey) {
      e.preventDefault();
      e.stopPropagation();
      // Safari macOS trackpad maps Shift+scroll to deltaX instead of deltaY
      const delta = Math.abs(e.deltaY) >= Math.abs(e.deltaX) ? e.deltaY : e.deltaX;
      if (delta) doLatentZoom(delta);
    }
  }

  // Safari-only: native trackpad pinch gesture support (gesturechange event)
  let gestureStartScale = 1;
  const gestureTarget = latentViewport || latent3dContainer;
  if (gestureTarget) {
    gestureTarget.addEventListener('gesturestart', function(e) {
      if (isShiftDown) {
        e.preventDefault();
        gestureStartScale = e.scale || 1;
      }
    }, { passive: false });
    gestureTarget.addEventListener('gesturechange', function(e) {
      if (isShiftDown) {
        e.preventDefault();
        const scaleDiff = (e.scale || 1) - gestureStartScale;
        gestureStartScale = e.scale || 1;
        doLatentZoom(-scaleDiff * 250);
      }
    }, { passive: false });
    gestureTarget.addEventListener('gestureend', function(e) {
      if (isShiftDown) e.preventDefault();
    }, { passive: false });
  }

  function on3dClick(e) {
    // If the user was dragging/rotating/orbiting, DO NOT open video modal!
    if (isDragging3D) {
      isDragging3D = false;
      return;
    }
    if (hoveredCard && hoveredCard.userData && hoveredCard.userData.item) {
      openModal(hoveredCard.userData.item);
    }
  }

  let clock = new THREE.Clock();

  function animate3d() {
    if (currentView !== 'latent' || document.hidden || !scene || !renderer) {
      stopThreeLoop();
      return;
    }
    animFrameId = requestAnimationFrame(animate3d);

    const elapsedTime = clock.getElapsedTime();

    if (controls) controls.update();

    // Smooth Lerp Camera Zoom Interpolation (60 FPS Silky Smooth)
    if (camera && controls) {
      const target = controls.target || new THREE.Vector3(0, 0, 0);
      const offset = camera.position.clone().sub(target);
      const currentDist = offset.length();

      if (Math.abs(targetZoomDist - currentDist) > 0.05) {
        const newDist = currentDist + (targetZoomDist - currentDist) * 0.12;
        offset.setLength(newDist);
        camera.position.copy(target).add(offset);
      }
    }

    cardMeshes.forEach((mesh, i) => {
      mesh.position.y = mesh.userData.originalPos.y + Math.sin(elapsedTime * 1.5 + i) * 0.8;
    });

    if (isDragging3D && latentTooltip) {
      latentTooltip.style.display = 'none';
    }

    if (raycaster && camera && !isDragging3D) {
      raycaster.setFromCamera(mouseVector, camera);
      const intersects = raycaster.intersectObjects(cardMeshes);

      if (intersects.length > 0) {
        const hitMesh = intersects[0].object;
        if (hoveredCard !== hitMesh) {
          if (hoveredCard) {
            hoveredCard.scale.set(1, 1, 1);
          }
          hoveredCard = hitMesh;
          hoveredCard.scale.set(1.2, 1.2, 1.2);
        }

        const item = hitMesh.userData.item;
        latentTooltip.style.display = 'block';

        const rect = latent3dContainer.getBoundingClientRect();
        const screenPos = hitMesh.position.clone().project(camera);
        const sx = (screenPos.x * 0.5 + 0.5) * rect.width;
        const sy = (-(screenPos.y * 0.5) + 0.5) * rect.height;

        latentTooltip.style.left = `${Math.min(Math.max(10, sx + 15), rect.width - 290)}px`;
        latentTooltip.style.top = `${Math.min(Math.max(10, sy + 15), rect.height - 130)}px`;

        const tagsHtml = item.tags.map(t => renderTag(t)).join(' ');
        const viewsStr = item.views ? formatViews(item.views) : '';
        const dateStr = item.upload_date ? formatDate(item.upload_date) : '';
        const creatorHtml = renderCreatorLink(item.autor);

        latentTooltip.innerHTML = `
          <div class="tooltip-title">${item.titulo}</div>
          <div class="tooltip-creator">${creatorHtml} • ${viewsStr} • ${dateStr}</div>
          <div class="tooltip-tags">${tagsHtml}</div>
        `;
      } else {
        if (hoveredCard) {
          hoveredCard.scale.set(1, 1, 1);
          hoveredCard = null;
        }
        latentTooltip.style.display = 'none';
      }
    }

    renderer.render(scene, camera);
  }

  document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
      stopThreeLoop();
    } else if (currentView === 'latent' && scene) {
      stopThreeLoop();
      animate3d();
    }
  });

  function update3dFilterState() {
    if (!cardMeshes.length) return;
    const filteredSet = new Set(getFilteredData().map(d => d.id));

    cardMeshes.forEach(mesh => {
      const isMatch = filteredSet.has(mesh.userData.item.id);
      if (isMatch) {
        mesh.userData.cardMat.opacity = 0.95;
        mesh.userData.borderMat.opacity = 0.8;
      } else {
        mesh.userData.cardMat.opacity = 0.1;
        mesh.userData.borderMat.opacity = 0.08;
      }
    });
  }

  // 6. Update Main UI
  function updateUI() {
    UserStore.updateCounts();
    const data = getFilteredData();
    itemsCounter.textContent = `${data.length} of ${activeDataset.length} tutorials`;

    if (data.length === 0) {
      destroyThreeScene();
      document.body.classList.remove('latent-view-active');
      viewGrid.style.display = 'none';
      viewTable.style.display = 'none';
      if (viewLatent) viewLatent.style.display = 'none';
      emptyState.style.display = 'block';

      // Build YouTube search URL with current context
      const ytLink = document.getElementById('yt-search-link');
      if (ytLink) {
        const swName = SOFTWARE_REGISTRY[activeSoftware]?.name || '';
        const query = [searchTerm, swName, 'tutorial'].filter(Boolean).join(' ');
        ytLink.href = `https://www.youtube.com/results?search_query=${encodeURIComponent(query)}`;
        ytLink.style.display = searchTerm ? 'inline-flex' : 'none';
      }
      return;
    }

    emptyState.style.display = 'none';

    if (currentView === 'grid') {
      destroyThreeScene();
      document.body.classList.remove('latent-view-active');
      viewGrid.style.display = 'block';
      viewTable.style.display = 'none';
      if (viewLatent) viewLatent.style.display = 'none';
      renderGrid(data);
    } else if (currentView === 'table') {
      destroyThreeScene();
      document.body.classList.remove('latent-view-active');
      viewGrid.style.display = 'none';
      viewTable.style.display = 'block';
      if (viewLatent) viewLatent.style.display = 'none';
      renderTable(data);
    } else if (currentView === 'latent') {
      document.body.classList.add('latent-view-active');
      viewGrid.style.display = 'none';
      viewTable.style.display = 'none';
      if (viewLatent) {
        viewLatent.style.display = 'flex';
        setTimeout(() => {
          viewLatent.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }, 60);
      }
      if (!scene) {
        initThreeScene();
      } else {
        update3dFilterState();
      }
    }
  }

  // 7. Video Modal Handler
  let activeModalItem = null;

  function openModal(item) {
    activeModalItem = item;
    modalVideoTitle.textContent = item.titulo;
    modalExternalLink.href = item.enlace;

    const tagsHtml = item.tags.map(t => renderTag(t)).join(' ');
    const creatorHtml = renderCreatorLink(item.autor);

    modalVideoMeta.innerHTML = `
      <span>${creatorHtml}</span> &nbsp;•&nbsp; <span>${tagsHtml}</span>
    `;

    if (item.vid) {
      modalIframe.src = `https://www.youtube.com/embed/${item.vid}?autoplay=1`;
    } else {
      modalIframe.src = item.enlace;
    }

    updateModalActionButtons();

    videoModal.classList.add('active');
    document.body.style.overflow = 'hidden';
  }

  function updateModalActionButtons() {
    if (!activeModalItem || !activeModalItem.vid) return;
    const vid = activeModalItem.vid;

    const btnFav = document.getElementById('modal-btn-fav');
    const btnSave = document.getElementById('modal-btn-save');
    const btnWatched = document.getElementById('modal-btn-watched');

    const isFav = UserStore.isFavorite(vid);
    const isSaved = UserStore.isSaved(vid);
    const isWatched = UserStore.isWatched(vid);

    if (btnFav) {
      btnFav.querySelector('.action-icon').innerHTML = isFav ? SVG_ICONS.heartFilled : SVG_ICONS.heartOutline;
      btnFav.querySelector('.action-label').textContent = isFav ? 'Favorited' : 'Favorite';
      btnFav.classList.toggle('active', isFav);
    }
    if (btnSave) {
      btnSave.querySelector('.action-icon').innerHTML = isSaved ? SVG_ICONS.bookmarkFilled : SVG_ICONS.bookmarkOutline;
      btnSave.querySelector('.action-label').textContent = isSaved ? 'Saved' : 'Watch Later';
      btnSave.classList.toggle('active', isSaved);
    }
    if (btnWatched) {
      btnWatched.querySelector('.action-icon').innerHTML = isWatched ? SVG_ICONS.watchedFilled : SVG_ICONS.watchedOutline;
      btnWatched.querySelector('.action-label').textContent = isWatched ? 'Completed' : 'Mark Watched';
      btnWatched.classList.toggle('active', isWatched);
    }
  }

  // Modal Action Listeners
  const modalBtnFav = document.getElementById('modal-btn-fav');
  const modalBtnSave = document.getElementById('modal-btn-save');
  const modalBtnWatched = document.getElementById('modal-btn-watched');

  if (modalBtnFav) {
    modalBtnFav.addEventListener('click', () => {
      if (activeModalItem && activeModalItem.vid) {
        UserStore.toggleFavorite(activeModalItem.vid);
        updateModalActionButtons();
        updateUI();
      }
    });
  }
  if (modalBtnSave) {
    modalBtnSave.addEventListener('click', () => {
      if (activeModalItem && activeModalItem.vid) {
        UserStore.toggleSaved(activeModalItem.vid);
        updateModalActionButtons();
        updateUI();
      }
    });
  }
  if (modalBtnWatched) {
    modalBtnWatched.addEventListener('click', () => {
      if (activeModalItem && activeModalItem.vid) {
        UserStore.toggleWatched(activeModalItem.vid);
        updateModalActionButtons();
        updateUI();
      }
    });
  }

  function closeModal() {
    videoModal.classList.remove('active');
    modalIframe.src = '';
    document.body.style.overflow = '';
  }

  modalCloseBtn.addEventListener('click', closeModal);
  videoModal.addEventListener('click', (e) => {
    if (e.target === videoModal) closeModal();
  });
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && videoModal.classList.contains('active')) {
      closeModal();
    }
  });

  // User Collection Filter Listeners
  document.querySelectorAll('.user-filter-chip[data-user-filter]').forEach(chip => {
    chip.addEventListener('click', () => {
      document.querySelectorAll('.user-filter-chip[data-user-filter]').forEach(c => c.classList.remove('active'));
      chip.classList.add('active');
      selectedUserFilter = chip.dataset.userFilter;
      updateUI();
      if (currentView === 'latent') update3dFilterState();
    });
  });

  // Filter Listeners
  searchInput.addEventListener('input', (e) => {
    searchTerm = e.target.value.trim();
    updateUI();
    if (currentView === 'latent') update3dFilterState();
  });

  filterCategory.addEventListener('change', (e) => {
    selectedCategory = e.target.value;
    updateUI();
    if (currentView === 'latent') update3dFilterState();
  });

  filterAuthor.addEventListener('change', (e) => {
    selectedAuthor = e.target.value;
    updateUI();
    if (currentView === 'latent') update3dFilterState();
  });

  sortSelect.addEventListener('change', (e) => {
    sortBy = e.target.value;
    updateUI();
  });

  viewBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      viewBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      currentView = btn.dataset.view;
      updateUI();
    });
  });

  // Theme Toggle (Dark vs Light SVG Toggle)
  themeBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const selectedTheme = btn.dataset.theme;
      document.documentElement.setAttribute('data-theme', selectedTheme);
      themeBtns.forEach(b => {
        if (b.dataset.theme === selectedTheme) {
          b.classList.add('active');
        } else {
          b.classList.remove('active');
        }
      });
    });
  });

  // Shortcut (⌘K or Ctrl+K)
  document.addEventListener('keydown', (e) => {
    if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
      e.preventDefault();
      searchInput.focus();
    }
  });

  // Init
  populateFilters();
  updateUI();
  checkHash();
});
