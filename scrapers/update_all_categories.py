import scrapetube
import pandas as pd
import numpy as np
import re
import os
import datetime
import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.manifold import TSNE

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_DIR = os.path.join(BASE_DIR, "datasets", "csv")
JS_DIR = os.path.join(BASE_DIR, "datasets", "js")
JSON_DIR = os.path.join(BASE_DIR, "datasets", "json")

SOFTWARE_DEFINITIONS = {
    "td": {
        "title": "TouchDesigner",
        "csv": os.path.join(CSV_DIR, "touchdesigner_tutorials.csv"),
        "js": os.path.join(JS_DIR, "tutorials_data.js"),
        "json": os.path.join(JSON_DIR, "touchdesigner_tutorials.json"),
        "queries": [
            "TouchDesigner tutorial",
            "TouchDesigner beginner tutorial intro",
            "TouchDesigner GLSL shader tutorial",
            "TouchDesigner projection mapping tutorial",
            "TouchDesigner audio reactive tutorial",
            "TouchDesigner Python tutorial",
            "TouchDesigner instancing point cloud tutorial",
            "TouchDesigner 3D SOPs geometry tutorial",
            "TouchDesigner Kinect tracking tutorial",
            "Elekktronaut TouchDesigner",
            "Bileam Tschepe TouchDesigner",
            "Paketa12 TouchDesigner"
        ],
        "rules": [
            ("Beginner Guides", ["beginner", "intro", "introduction", "basics", "from zero", "getting started", "start", "first steps"]),
            ("Core Fundamentals & Operators", ["overview", "fundamentals", "learn", "course", "walkthrough", "operators", "top", "chop", "dat", "sop", "comp"]),
            ("Generative Art & Graphics", ["generative", "art", "graphics", "visuals", "pattern", "abstract", "feedback", "noise"]),
            ("GLSL & Shader Programming", ["glsl", "shader", "shaders", "code", "fragment shader", "raymarching"]),
            ("Projection Mapping", ["projection mapping", "mapping", "projector", "kantan mapper", "stoner", "warp", "blend"]),
            ("Audio Reactivity", ["audio reactive", "audio", "music reactive", "beat sync", "sound reactive", "spectrum", "fft"]),
            ("Python Scripting & System", ["python", "scripting", "dat python", "code", "execute", "extensions"]),
            ("3D & Geometry (SOPs)", ["3d", "geometry", "sop", "sops", "mesh", "render", "camera", "lighting"]),
            ("Point Clouds & Instancing", ["instancing", "point cloud", "particles", "points", "instance", "gpu instancing"]),
            ("Sensors, Tracking & Hardware", ["kinect", "leap motion", "tracking", "sensor", "hardware", "midi", "osc", "camera tracking"])
        ]
    },
    "blender": {
        "title": "Blender 3D",
        "csv": os.path.join(CSV_DIR, "blender_tutorials.csv"),
        "js": os.path.join(JS_DIR, "blender_tutorials_data.js"),
        "json": os.path.join(JSON_DIR, "blender_tutorials.json"),
        "queries": [
            "Blender tutorial",
            "Blender beginner tutorial",
            "Blender geometry nodes tutorial",
            "Blender modeling sculpting tutorial",
            "Blender shading texturing tutorial",
            "Blender lighting rendering Cycles EEVEE",
            "Blender rigging animation tutorial",
            "Blender physics simulation cloth particles",
            "Blender Guru donut tutorial",
            "CG Matter Blender geometry nodes",
            "Duck 3D Blender tutorial",
            "Grant Abbitt Blender"
        ],
        "rules": [
            ("Beginner Guides", ["beginner", "intro", "introduction", "basics", "from zero", "getting started", "start", "donut"]),
            ("3D Modeling & Sculpting", ["modeling", "modelling", "sculpting", "sculpt", "hard surface", "mesh", "topology", "subdivision"]),
            ("Geometry Nodes & Procedural", ["geometry nodes", "procedural", "geo nodes", "node group", "fields"]),
            ("Shading, Texturing & UVs", ["shading", "materials", "texturing", "texture", "uv unwrap", "pbr", "procedural material"]),
            ("Lighting & Environment", ["lighting", "environment", "hdri", "world", "sun", "sky", "volumetric", "fog"]),
            ("Cycles & EEVEE Rendering", ["rendering", "cycles", "eevee", "render settings", "compositor", "denoise"]),
            ("Character Rigging", ["rigging", "rig", "armature", "bones", "weight paint", "character rig"]),
            ("3D Animation & Motion", ["animation", "animate", "keyframes", "graph editor", "walk cycle", "motion"]),
            ("Physics, Cloth & Particle Simulation", ["physics", "simulation", "sim", "cloth", "particles", "fluid", "smoke", "fire", "rigid body"]),
            ("VFX & Compositing", ["vfx", "compositing", "green screen", "motion tracking", "camera tracking", "visual effects"])
        ]
    },
    "ableton": {
        "title": "Ableton Live",
        "csv": os.path.join(CSV_DIR, "ableton_tutorials.csv"),
        "js": os.path.join(JS_DIR, "ableton_tutorials_data.js"),
        "json": os.path.join(JSON_DIR, "ableton_tutorials.json"),
        "queries": [
            "Ableton Live tutorial",
            "Ableton Live beginner tutorial",
            "Ableton beat making drums tutorial",
            "Ableton sound design synth Operator Wavetable",
            "Ableton mixing EQ compression tutorial",
            "Ableton mastering audio tutorial",
            "Ableton vocal processing tutorial",
            "Ableton Max for Live M4L tutorial",
            "YouSuckAtProducing Ableton",
            "In The Mix Ableton",
            "EDM Prod Ableton",
            "SadowickProduction Ableton"
        ],
        "rules": [
            ("Beginner Guides", ["beginner", "intro", "introduction", "basics", "from zero", "getting started", "start", "interface"]),
            ("Beat Making & Drums", ["beat making", "drums", "drum rack", "groove", "rhythm", "percussion", "hihats", "808"]),
            ("Synthesizers & Sound Design", ["sound design", "synth", "operator", "wavetable", "drift", "analog", "bass design", "patch"]),
            ("Mixing Techniques", ["mixing", "eq", "compression", "reverb", "delay", "sidechain", "gain staging", "balance"]),
            ("Mastering & Audio Polish", ["mastering", "limiter", "loudness", "lufs", "final polish", "master chain", "saturation"]),
            ("Vocal Processing & Effects", ["vocal", "vocals", "autotune", "tuning", "vocal chain", "harmonies", "pitch correction"]),
            ("Max for Live (M4L)", ["max for live", "m4l", "maxmsp", "devices", "custom devices", "patcher"]),
            ("Arrangement & Songwriting", ["arrangement", "structure", "songwriting", "transitions", "build up", "drop"]),
            ("Live Performance & Hardware", ["live performance", "push", "hardware", "controller", "session view", "gig"]),
            ("MIDI & Automation", ["midi", "automation", "cc", "envelopes", "macro", "rack"])
        ]
    },
    "logicpro": {
        "title": "Logic Pro",
        "csv": os.path.join(CSV_DIR, "logicpro_tutorials.csv"),
        "js": os.path.join(JS_DIR, "logicpro_tutorials_data.js"),
        "json": os.path.join(JSON_DIR, "logicpro_tutorials.json"),
        "queries": [
            "Logic Pro tutorial",
            "Logic Pro beginner tutorial",
            "Logic Pro Alchemy synth tutorial",
            "Logic Pro Flex Pitch vocal editing",
            "Logic Pro mixing EQ compressor tutorial",
            "Logic Pro mastering tutorial",
            "Logic Pro orchestral film scoring tutorial",
            "Music Tech Help Guy Logic Pro",
            "Why Logic Pro Rules tutorial"
        ],
        "rules": [
            ("Beginner Guides", ["beginner", "intro", "introduction", "basics", "from zero", "getting started", "start", "overview"]),
            ("Alchemy & Native Synths", ["alchemy", "synth", "retro synth", "es2", "sculpture", "sound design", "instruments"]),
            ("Flex Pitch & Vocal Editing", ["flex pitch", "flex time", "vocal", "tuning", "pitch correction", "vocal editing"]),
            ("Mixing & EQ Techniques", ["mixing", "eq", "channel eq", "compressor", "bus", "aux", "reverb", "delay", "panning"]),
            ("Mastering & Dynamics", ["mastering", "limiter", "multipress", "loudness", "master track", "dither"]),
            ("Orchestral & Film Scoring", ["orchestral", "film score", "cinematic", "strings", "horns", "articulation", "score"]),
            ("Drummer & Beat Production", ["drummer", "drum kit designer", "beat", "pattern region", "step sequencer"]),
            ("Automation & Smart Controls", ["automation", "smart controls", "track automation", "latch", "read"]),
            ("MIDI Recording & Sequencing", ["midi", "piano roll", "quantize", "midi FX", "arpeggiator"])
        ]
    },
    "reaper": {
        "title": "REAPER",
        "csv": os.path.join(CSV_DIR, "reaper_tutorials.csv"),
        "js": os.path.join(JS_DIR, "reaper_tutorials_data.js"),
        "json": os.path.join(JSON_DIR, "reaper_tutorials.json"),
        "queries": [
            "REAPER tutorial",
            "REAPER beginner tutorial DAW",
            "REAPER custom scripts ReaScript Lua tutorial",
            "REAPER JSFX plugin tutorial",
            "REAPER game audio Wwise FMOD tutorial",
            "REAPER mixing audio routing tutorial",
            "REAPER mastering loudness tutorial",
            "Kenny Gioia REAPER Mania tutorial",
            "REAPER Blog tutorial"
        ],
        "rules": [
            ("Beginner Guides", ["beginner", "intro", "introduction", "basics", "from zero", "getting started", "start", "first steps"]),
            ("Custom Scripts & Actions", ["reascript", "lua", "python", "custom action", "script", "shortcuts", "workflow"]),
            ("JSFX & Plugin DSP", ["jsfx", "plugins", "reaplugs", "reacomp", "reaeq", "custom plugin", "dsp"]),
            ("Game Audio & Middleware", ["game audio", "wwise", "fmod", "sound design", "asset export", "batch converter"]),
            ("Audio Mixing & Routing", ["mixing", "routing", "routing matrix", "send", "receive", "bus", "track channels"]),
            ("Mastering & Loudness", ["mastering", "loudness", "lufs", "limiter", "render", "stems"]),
            ("Vocal Processing & Tuning", ["vocal", "vocals", "reatune", "tuning", "pitch", "vocal chain"]),
            ("MIDI Editing & Virtual Instruments", ["midi", "piano roll", "vst", "vsti", "virtual instrument", "quantize"]),
            ("Control Surfaces & Hardware", ["control surface", "hardware", "midi controller", "osc", "hardware setup"])
        ]
    },
    "maxmsp": {
        "title": "Max/MSP",
        "csv": os.path.join(CSV_DIR, "maxmsp_tutorials.csv"),
        "js": os.path.join(JS_DIR, "maxmsp_tutorials_data.js"),
        "json": os.path.join(JSON_DIR, "maxmsp_tutorials.json"),
        "queries": [
            "Max/MSP tutorial",
            "Max MSP beginner tutorial patching",
            "Max Jitter 3D video tutorial",
            "Max MSP audio DSP synthesis tutorial",
            "Max MSP generative music tutorial",
            "Max for Live M4L patch tutorial",
            "Max MSP Arduino hardware tutorial",
            "Max MSP gen~ tutorial",
            "Cycling74 Max MSP tutorial",
            "Dude837 Max MSP tutorial"
        ],
        "rules": [
            ("Beginner Guides", ["beginner", "intro", "introduction", "basics", "from zero", "getting started", "start", "patching"]),
            ("Jitter & 3D Visuals", ["jitter", "jit", "video", "matrix", "3d", "gl", "opengl", "jit.gl"]),
            ("MSP Audio DSP & Synthesis", ["msp", "audio", "dsp", "synth", "synthesis", "oscillator", "filter", "signal"]),
            ("Generative Music & Algorithms", ["generative", "algorithmic", "probability", "random", "sequencer", "pattern"]),
            ("Max for Live Integration", ["max for live", "m4l", "ableton", "live", "amxd", "plugin"]),
            ("MIDI & Serial Hardware", ["midi", "serial", "arduino", "hardware", "sensor", "controller"]),
            ("Open Sound Control (OSC)", ["osc", "open sound control", "udp", "network", "remote"]),
            ("Gen~ Low-Level Coding", ["gen~", "gen", "code", "expr", "sample level", "c++"])
        ]
    },
    "premiere": {
        "title": "Premiere Pro",
        "csv": os.path.join(CSV_DIR, "premiere_tutorials.csv"),
        "js": os.path.join(JS_DIR, "premiere_tutorials_data.js"),
        "json": os.path.join(JSON_DIR, "premiere_tutorials.json"),
        "queries": [
            "Premiere Pro tutorial",
            "Premiere Pro beginner tutorial",
            "Premiere Pro color grading Lumetri tutorial",
            "Premiere Pro transitions speed ramp tutorial",
            "Premiere Pro titles essential graphics tutorial",
            "Premiere Pro audio editing essential sound",
            "Premiere Pro export settings tutorial",
            "Peter McKinnon Premiere Pro",
            "Premiere Gal tutorial",
            "Cinecom.net Premiere Pro"
        ],
        "rules": [
            ("Beginner Guides", ["beginner", "intro", "introduction", "basics", "from zero", "getting started", "start", "overview"]),
            ("Video Editing & Cutting", ["editing", "cutting", "trimming", "timeline", "sequence", "b-roll", "edit"]),
            ("Color Grading & Lumetri", ["color grading", "lumetri", "color correction", "lut", "scopes", "cinematic look"]),
            ("Transitions & Speed Ramping", ["transitions", "speed ramp", "whip pan", "seamless transition", "slow motion", "time remapping"]),
            ("Titles & Essential Graphics", ["titles", "essential graphics", "text", "lower thirds", "mogrt", "captions"]),
            ("Audio Cleaning & Essential Sound", ["audio", "essential sound", "noise reduction", "dialogue", "voiceover", "sound design"]),
            ("Exporting & Render Settings", ["export", "render", "settings", "h.264", "4k", "youtube export", "bitrate"]),
            ("Multicam Editing", ["multicam", "multi-camera", "sync audio", "camera switching"])
        ]
    },
    "aftereffects": {
        "title": "After Effects",
        "csv": os.path.join(CSV_DIR, "aftereffects_tutorials.csv"),
        "js": os.path.join(JS_DIR, "aftereffects_tutorials_data.js"),
        "json": os.path.join(JSON_DIR, "aftereffects_tutorials.json"),
        "queries": [
            "After Effects tutorial",
            "After Effects beginner tutorial motion graphics",
            "After Effects VFX green screen keying tutorial",
            "After Effects compositing tracking tutorial",
            "After Effects expressions code tutorial",
            "After Effects 3D camera camera tracker tutorial",
            "After Effects text kinetic typography tutorial",
            "Video Copilot After Effects Andrew Kramer",
            "SonduckFilm After Effects",
            "Ben Marriott After Effects"
        ],
        "rules": [
            ("Beginner Guides", ["beginner", "intro", "introduction", "basics", "from zero", "getting started", "start", "overview"]),
            ("Motion Graphics & Shape Layers", ["motion graphics", "shape layers", "mograph", "vector animation", "easing", "graph editor"]),
            ("VFX & Green Screen Keying", ["vfx", "green screen", "keying", "chroma key", "keylight", "rotoscoping", "roto"]),
            ("Compositing & Tracking", ["compositing", "tracking", "mocha", "motion tracking", "null object", "matchmove"]),
            ("Expressions & Code Automation", ["expressions", "expression", "code", "wiggle", "loopout", "javascript"]),
            ("3D Space & Camera Animations", ["3d", "3d space", "camera", "camera tracker", "depth of field", "lights"]),
            ("Text Effects & Kinetic Typography", ["text", "kinetic typography", "text effect", "text animation", "typewriter"]),
            ("Plugin Tools (Element 3D/Trapcode)", ["element 3d", "trapcode", "particular", "stardust", "plugins", "optical flares"])
        ]
    },
    "photoshop": {
        "title": "Photoshop",
        "csv": os.path.join(CSV_DIR, "photoshop_tutorials.csv"),
        "js": os.path.join(JS_DIR, "photoshop_tutorials_data.js"),
        "json": os.path.join(JSON_DIR, "photoshop_tutorials.json"),
        "queries": [
            "Photoshop tutorial",
            "Photoshop beginner tutorial",
            "Photoshop photo retouching skin tutorial",
            "Photoshop image compositing manipulation tutorial",
            "Photoshop Generative AI Firefly tutorial",
            "Photoshop color grading adjustment layers",
            "Photoshop text typography poster tutorial",
            "Photoshop Training Channel Nemanja",
            "PiXimperfect Photoshop Unmesh Dinda",
            "Phlearn Photoshop tutorial"
        ],
        "rules": [
            ("Beginner Guides", ["beginner", "intro", "introduction", "basics", "from zero", "getting started", "start", "overview"]),
            ("Photo Retouching & Beauty", ["retouching", "skin", "portrait", "frequency separation", "dodge and burn", "blemish"]),
            ("Image Compositing & Manipulation", ["compositing", "manipulation", "photo manipulation", "blend", "surreal", "photomontage"]),
            ("Generative AI & Firefly", ["generative ai", "firefly", "generative fill", "ai", "prompt"]),
            ("Color Adjustment & Grading", ["color grading", "adjustment layers", "curves", "levels", "color balance", "camera raw"]),
            ("Text Effects & Typography", ["text", "typography", "text effect", "poster", "font", "layer styles"]),
            ("Mockups & Branding Graphics", ["mockup", "branding", "smart object", "logo mockup", "design"]),
            ("Selections & Masking", ["selection", "masking", "layer mask", "pen tool", "select subject", "refine edge"])
        ]
    },
    "illustrator": {
        "title": "Adobe Illustrator",
        "csv": os.path.join(CSV_DIR, "illustrator_tutorials.csv"),
        "js": os.path.join(JS_DIR, "illustrator_tutorials_data.js"),
        "json": os.path.join(JSON_DIR, "illustrator_tutorials.json"),
        "queries": [
            "Adobe Illustrator tutorial",
            "Illustrator beginner tutorial",
            "Illustrator logo design tutorial",
            "Illustrator pen tool pathfinder tutorial",
            "Illustrator vector illustration tutorial",
            "Illustrator typography text effect tutorial",
            "Illustrator 3D inflation tutorial",
            "Illustrator pattern packaging design tutorial",
            "Spoon Graphics Illustrator",
            "Dansky Illustrator",
            "Satori Graphics Illustrator"
        ],
        "rules": [
            ("Beginner Guides", ["beginner", "intro", "introduction", "basics", "from zero", "getting started", "start", "overview"]),
            ("Pen Tool & Precise Paths", ["pen tool", "bezier", "path", "anchor points", "curvature tool", "handles"]),
            ("Vector Illustration & Drawing", ["vector", "illustration", "drawing", "flat design", "character", "isometric", "shading"]),
            ("Logo Design & Branding", ["logo", "logo design", "branding", "monogram", "icon", "badge", "identity"]),
            ("Typography & Text Effects", ["typography", "text", "font", "lettering", "text effect", "type", "calligraphy"]),
            ("3D & Inflation Effects", ["3d", "inflation", "revolve", "extrude", "bevel", "3d materials"]),
            ("Pattern Design & Textures", ["pattern", "seamless", "repeating", "texture", "swatches"]),
            ("Packaging & Label Design", ["packaging", "label", "dieline", "mockup", "box design"]),
            ("Shape Builder & Pathfinder", ["shape builder", "pathfinder", "unite", "divide", "minus front", "geometry"])
        ]
    },
    "davinci": {
        "title": "DaVinci Resolve",
        "csv": os.path.join(CSV_DIR, "davinci_tutorials.csv"),
        "js": os.path.join(JS_DIR, "davinci_tutorials_data.js"),
        "json": os.path.join(JSON_DIR, "davinci_tutorials.json"),
        "queries": [
            "DaVinci Resolve tutorial",
            "DaVinci Resolve beginner tutorial",
            "DaVinci Resolve color grading tutorial Lumetri",
            "DaVinci Resolve Fusion motion graphics VFX",
            "DaVinci Resolve Fairlight audio tutorial",
            "DaVinci Resolve cut edit page tutorial",
            "DaVinci Resolve speed ramp transition tutorial",
            "Casey Faris DaVinci Resolve",
            "Cullen Kelly DaVinci Resolve",
            "Darren Mostyn DaVinci Resolve"
        ],
        "rules": [
            ("Beginner Guides", ["beginner", "intro", "introduction", "basics", "from zero", "getting started", "start", "overview"]),
            ("Cut & Edit Page Workflows", ["cut page", "edit page", "editing", "trimming", "timeline", "b-roll", "cut"]),
            ("Color Grading & Wheels", ["color grading", "color correction", "color wheels", "scopes", "cinematic look", "node tree", "log"]),
            ("Color Space Transform & LUTs", ["color space transform", "cst", "lut", "aces", "davinci yrgb", "color management"]),
            ("Fusion Motion Graphics", ["fusion", "motion graphics", "titles", "lower thirds", "keyframe", "nodes"]),
            ("Fusion Visual Effects (VFX)", ["vfx", "tracking", "keying", "green screen", "compositing", "clean plate"]),
            ("Fairlight Audio Mixing", ["fairlight", "audio", "sound", "mixing", "eq", "compressor", "dialogue"]),
            ("Noise Reduction & Restoration", ["noise reduction", "temporal noise", "spatial noise", "sharpening", "restoration"]),
            ("Deliver & Export Settings", ["deliver", "export", "render", "settings", "youtube export", "h.265", "prores"])
        ]
    },
    "sibelius": {
        "title": "Avid Sibelius",
        "csv": os.path.join(CSV_DIR, "sibelius_tutorials.csv"),
        "js": os.path.join(JS_DIR, "sibelius_tutorials_data.js"),
        "json": os.path.join(JSON_DIR, "sibelius_tutorials.json"),
        "queries": [
            "Avid Sibelius tutorial",
            "Sibelius beginner tutorial notation",
            "Sibelius score layout orchestral tutorial",
            "Sibelius shortcuts fast note input",
            "Sibelius playback NotePerformer tutorial",
            "Sibelius lead sheet chord symbols tutorial",
            "Music Notation Sibelius tutorial"
        ],
        "rules": [
            ("Beginner Guides", ["beginner", "intro", "introduction", "basics", "from zero", "getting started", "start", "overview"]),
            ("Note Input Methods", ["note input", "keypad", "step time", "flexi-time", "midi keyboard", "entry"]),
            ("Keyboard Shortcuts & Speed", ["shortcuts", "speedy", "keybindings", "fast input", "workflow"]),
            ("Score Formatting & Page Setup", ["layout", "formatting", "page setup", "staves", "system", "score", "margins"]),
            ("Dynamic Parts & Engraving", ["dynamic parts", "parts", "engraving", "house styles", "stem"]),
            ("Playback & NotePerformer", ["playback", "sound", "noteperformer", "vst", "sounds", "expression", "mixer"]),
            ("Arranging & Orchestration", ["arranging", "orchestration", "transposition", "piano score", "instruments"]),
            ("Lead Sheets & Chord Symbols", ["lead sheet", "chords", "chord symbols", "slash notation", "jazz"]),
            ("Lyrics & Text Annotations", ["lyrics", "text", "title", "composer", "expression text", "technique"])
        ]
    },
    "vsc": {
        "title": "Visual Studio Code",
        "csv": os.path.join(CSV_DIR, "vsc_tutorials.csv"),
        "js": os.path.join(JS_DIR, "vsc_tutorials_data.js"),
        "json": os.path.join(JSON_DIR, "vsc_tutorials.json"),
        "queries": [
            "Visual Studio Code tutorial",
            "VS Code beginner tutorial",
            "VS Code extensions Copilot tutorial",
            "VS Code shortcuts productivity tips",
            "VS Code debugging breakpoint tutorial",
            "VS Code Git GitHub integration tutorial",
            "VS Code web development HTML CSS JS tutorial",
            "Fireship VS Code",
            "Traversy Media VS Code"
        ],
        "rules": [
            ("Beginner Guides", ["beginner", "intro", "introduction", "basics", "from zero", "getting started", "start", "installation"]),
            ("Extension Setup & Copilot", ["extensions", "plugins", "copilot", "github copilot", "prettier", "eslint", "ai"]),
            ("Theme & Workspace Customization", ["theme", "customization", "settings.json", "icons", "font", "workspace"]),
            ("Shortcuts & Multi-Cursor", ["shortcuts", "productivity", "tips", "multi cursor", "keybindings", "command palette", "snippets"]),
            ("Code Debugging & Breakpoints", ["debugging", "debugger", "launch.json", "breakpoints", "console", "variables"]),
            ("Integrated Terminal & Tasks", ["terminal", "integrated terminal", "tasks.json", "bash", "zsh", "npm"]),
            ("Git & GitHub Integration", ["git", "github", "source control", "version control", "branch", "commit", "push"]),
            ("Web Development Setup", ["web", "html", "css", "javascript", "typescript", "react", "live server"]),
            ("Python & Backend Setup", ["python", "venv", "virtualenv", "django", "fastapi", "interpreter"])
        ]
    },
    "unity": {
        "title": "Unity Engine",
        "csv": os.path.join(CSV_DIR, "unity_tutorials.csv"),
        "js": os.path.join(JS_DIR, "unity_tutorials_data.js"),
        "json": os.path.join(JSON_DIR, "unity_tutorials.json"),
        "queries": [
            "Unity tutorial game development",
            "Unity beginner tutorial 2D 3D",
            "Unity C# scripting tutorial",
            "Unity Shader Graph tutorial",
            "Unity UI canvas tutorial",
            "Unity physics Rigidbody tutorial",
            "Unity animation Animator state machine tutorial",
            "Brackeys Unity",
            "Code Monkey Unity",
            "Sebastian Lague Unity"
        ],
        "rules": [
            ("Beginner Guides", ["beginner", "intro", "introduction", "basics", "from zero", "getting started", "start", "game loop"]),
            ("C# Programming & Logic", ["c#", "csharp", "scripting", "programming", "code", "monobehaviour", "variables", "functions"]),
            ("2D Physics & Movement", ["2d", "sprite", "tilemap", "2d physics", "rigidbody2d", "platformer"]),
            ("3D Physics & Raycasting", ["3d", "physics", "rigidbody", "collider", "collision", "raycast", "character controller"]),
            ("Shader Graph & Shaders", ["shader graph", "shader", "materials", "custom shader", "nodes"]),
            ("URP & Lighting Setup", ["urp", "hdrp", "lighting", "lightmap", "post processing", "shadows"]),
            ("UI Canvas & HUD Design", ["ui", "canvas", "menu", "hud", "button", "textmeshpro"]),
            ("Animator & State Machines", ["animator", "animation", "blend tree", "state machine", "spritesheet"]),
            ("VFX Graph & Particle Systems", ["vfx graph", "particles", "particle system", "fire", "sparks", "visual effects"])
        ]
    },
    "unreal": {
        "title": "Unreal Engine",
        "csv": os.path.join(CSV_DIR, "unreal_tutorials.csv"),
        "js": os.path.join(JS_DIR, "unreal_tutorials_data.js"),
        "json": os.path.join(JSON_DIR, "unreal_tutorials.json"),
        "queries": [
            "Unreal Engine 5 tutorial",
            "UE5 beginner tutorial",
            "Unreal Engine Blueprints visual scripting tutorial",
            "Unreal Engine Nanite Lumen lighting tutorial",
            "Unreal Engine Niagara particle FX tutorial",
            "Unreal Engine landscape foliage environment tutorial",
            "Unreal Engine MetaHuman character tutorial",
            "Unreal Sensei UE5",
            "William Faucher Unreal"
        ],
        "rules": [
            ("Beginner Guides", ["beginner", "intro", "introduction", "basics", "from zero", "getting started", "start", "ue5"]),
            ("Blueprints Visual Scripting", ["blueprints", "blueprint", "visual scripting", "event graph", "functions", "logic"]),
            ("Lumen & Lighting Systems", ["lumen", "lighting", "ray tracing", "shadows", "post process", "global illumination"]),
            ("Nanite & High-Poly Meshes", ["nanite", "mesh", "high poly", "geometry", "virtualized geometry"]),
            ("Niagara VFX & Particles", ["niagara", "vfx", "particles", "smoke", "fire", "explosion", "fluid"]),
            ("Landscape & Environment Creation", ["landscape", "foliage", "environment", "open world", "biomes", "quixel"]),
            ("MetaHuman & Character Rigging", ["metahuman", "character", "control rig", "animation", "skeletal mesh"]),
            ("Materials & Shader Graphs", ["materials", "material editor", "shader", "pbr", "blend material"]),
            ("Cinematics & Sequencer", ["sequencer", "cinematics", "camera", "movie render queue", "film"])
        ]
    },
    "python": {
        "title": "Python",
        "csv": os.path.join(CSV_DIR, "python_tutorials.csv"),
        "js": os.path.join(JS_DIR, "python_tutorials_data.js"),
        "json": os.path.join(JSON_DIR, "python_tutorials.json"),
        "queries": [
            "Python tutorial",
            "Python beginner tutorial full course",
            "Python object oriented programming OOP tutorial",
            "Python data science Pandas Numpy tutorial",
            "Python web scraping BeautifulSoup Selenium tutorial",
            "Python machine learning PyTorch TensorFlow tutorial",
            "Python automation script tutorial",
            "Python Django FastAPI web tutorial",
            "Corey Schafer Python",
            "Programming with Mosh Python",
            "FreeCodeCamp Python"
        ],
        "rules": [
            ("Beginner Guides", ["beginner", "intro", "introduction", "basics", "from zero", "getting started", "start", "full course"]),
            ("Control Flow & Loops", ["loops", "if statement", "functions", "data types", "lists", "dictionaries"]),
            ("Object-Oriented Programming (OOP)", ["oop", "object oriented", "classes", "inheritance", "polymorphism", "methods", "dunder"]),
            ("Data Science with Pandas & NumPy", ["data science", "pandas", "numpy", "matplotlib", "dataframe", "seaborn"]),
            ("Machine Learning & PyTorch/TensorFlow", ["machine learning", "ai", "pytorch", "tensorflow", "scikit-learn", "deep learning"]),
            ("Web Scraping & Automation", ["automation", "scraping", "web scraping", "beautifulsoup", "selenium", "requests", "bot"]),
            ("FastAPI & Django Web Backend", ["django", "fastapi", "flask", "api", "rest api", "backend", "database"]),
            ("File I/O & Scripting Utilities", ["file io", "json", "os", "sys", "pathlib", "scripting", "csv"])
        ]
    },
    "resolume": {
        "title": "Resolume Arena",
        "csv": os.path.join(CSV_DIR, "resolume_tutorials.csv"),
        "js": os.path.join(JS_DIR, "resolume_tutorials_data.js"),
        "json": os.path.join(JSON_DIR, "resolume_tutorials.json"),
        "queries": [
            "Resolume Arena tutorial",
            "Resolume Arena beginner tutorial",
            "Resolume VJ performance tutorial",
            "Resolume Arena projection mapping tutorial",
            "Resolume Wire tutorial generative",
            "Resolume Arena DMX LED pixel mapping tutorial",
            "Resolume Arena NDI Syphon Spout tutorial",
            "Resolume Arena BPM sync audio reactive tutorial",
            "DocOptic Resolume",
            "Sean Bowes Resolume"
        ],
        "rules": [
            ("Beginner Guides", ["beginner", "intro", "introduction", "basics", "from zero", "getting started", "start", "interface"]),
            ("Decks, Clips & Layer Mixing", ["decks", "clips", "layers", "mixing", "blend mode", "transition", "vj"]),
            ("Projection Mapping & Advanced Output", ["projection mapping", "advanced output", "mapping", "slices", "projector"]),
            ("Edge Blending & Keystone Warping", ["edge blending", "keystone", "warp", "soft edge", "blending"]),
            ("Resolume Wire Generative Patches", ["wire", "resolume wire", "generative", "nodes", "patch", "custom effect"]),
            ("DMX Lighting Control", ["dmx", "artnet", "e1.31", "lighting control", "fixtures"]),
            ("Pixel Mapping & LED Fixtures", ["pixel mapping", "led", "led strips", "fixture map", "pixels"]),
            ("NDI, Spout & Video Routing", ["ndi", "spout", "syphon", "routing", "video input", "capture card"]),
            ("BPM Sync & Audio Reactivity", ["bpm", "bpm sync", "audio reactive", "fft", "tempo", "clock"])
        ]
    },
    "comfyui": {
        "title": "ComfyUI",
        "csv": os.path.join(CSV_DIR, "comfyui_tutorials.csv"),
        "js": os.path.join(JS_DIR, "comfyui_tutorials_data.js"),
        "json": os.path.join(JSON_DIR, "comfyui_tutorials.json"),
        "queries": [
            "ComfyUI tutorial",
            "ComfyUI beginner tutorial node graph",
            "ComfyUI Stable Diffusion XL SDXL tutorial",
            "ComfyUI ControlNet IPAdapter tutorial",
            "ComfyUI AnimateDiff video tutorial",
            "ComfyUI Flux tutorial",
            "ComfyUI custom nodes tutorial",
            "ComfyUI img2img upscaling tutorial",
            "Latent Vision ComfyUI",
            "Purz ComfyUI",
            "Scott Detweiler ComfyUI"
        ],
        "rules": [
            ("Beginner Guides", ["beginner", "intro", "introduction", "basics", "from zero", "getting started", "start", "installation"]),
            ("Node Graph Architecture", ["nodes", "node graph", "workflow", "connections", "ksampler", "latent"]),
            ("SDXL & Stable Diffusion Models", ["sdxl", "stable diffusion", "checkpoint", "lora", "clip", "vae", "model"]),
            ("Flux Model Workflows", ["flux", "flux.1", "flux dev", "flux schnell", "flux workflow"]),
            ("ControlNet Pose & Canny", ["controlnet", "openpose", "canny", "depth", "reference", "pose"]),
            ("IPAdapter & Style Transfer", ["ipadapter", "style transfer", "image reference", "clip vision"]),
            ("AnimateDiff & AI Video", ["animatediff", "video", "animation", "frame", "fps", "video2video"]),
            ("Image Upscaling & Hires Fix", ["upscale", "ultimate sd upscale", "hires fix", "tiled ksampler", "magnific"]),
            ("Custom Nodes & ComfyManager", ["custom nodes", "comfyui-manager", "manager", "install nodes", "extension"])
        ]
    },
    "madmapper": {
        "title": "MadMapper",
        "csv": os.path.join(CSV_DIR, "madmapper_tutorials.csv"),
        "js": os.path.join(JS_DIR, "madmapper_tutorials_data.js"),
        "json": os.path.join(JSON_DIR, "madmapper_tutorials.json"),
        "queries": [
            "MadMapper tutorial",
            "MadMapper beginner tutorial projection mapping",
            "MadMapper LED pixel mapping DMX ArtNet tutorial",
            "MadMapper 3D calibration Spatial Scanner tutorial",
            "MadMapper materials shaders ISF tutorial",
            "MadMapper Syphon Spout NDI tutorial",
            "MadMapper laser control tutorial",
            "GarageCube MadMapper"
        ],
        "rules": [
            ("Beginner Guides", ["beginner", "intro", "introduction", "basics", "from zero", "getting started", "start", "interface"]),
            ("Surface Creation & Masking", ["surface", "quad", "mesh", "masking", "mask", "bezier surface", "feathering"]),
            ("3D Projection Mapping & Calibration", ["projection mapping", "3d", "calibration", "mesh warping", "architectural"]),
            ("Spatial Scanner 3D Reconstruction", ["spatial scanner", "reconstruction", "3d scan", "structured light", "scanner"]),
            ("LED Strip Pixel Mapping", ["led", "pixel mapping", "led strips", "pixels", "madlight"]),
            ("DMX & ArtNet Lighting Output", ["dmx", "artnet", "lighting output", "fixtures", "spi"]),
            ("Procedural Shaders & ISF Materials", ["materials", "isf", "shaders", "generative", "procedural", "visuals"]),
            ("Laser Control & Hardware", ["laser", "dac", "pangolin", "etherdream", "laser mapping"]),
            ("Syphon, Spout & NDI Video Routing", ["syphon", "spout", "ndi", "video routing", "media server", "inputs"])
        ]
    }
}

def extract_author(v):
    for key in ['ownerText', 'longBylineText', 'shortBylineText']:
        runs = v.get(key, {}).get('runs', [])
        if runs and runs[0].get('text'):
            return runs[0].get('text').strip()
    return "Desconocido"

def extract_title(v):
    runs = v.get('title', {}).get('runs', [])
    if runs and runs[0].get('text'):
        return runs[0].get('text').strip()
    return ""

def extract_snippet(v):
    snippets = v.get('detailedMetadataSnippets', [])
    if snippets:
        runs = snippets[0].get('snippetText', {}).get('runs', [])
        return " ".join([r.get('text', '') for r in runs]).strip()
    return ""

def parse_views(v):
    view_text = v.get('viewCountText', {})
    text = view_text.get('simpleText', '') or view_text.get('runs', [{}])[0].get('text', '')
    m = re.search(r'([\d,.]+)', text)
    if m:
        return int(m.group(1).replace(',', '').replace('.', ''))
    return 0

def parse_relative_date(v):
    pub = v.get('publishedTimeText', {}).get('simpleText', '')
    now = datetime.datetime.now()
    if 'year' in pub:
        m = re.search(r'(\d+)', pub)
        years = int(m.group(1)) if m else 1
        return (now - datetime.timedelta(days=365*years)).strftime('%Y-%m-%d')
    elif 'month' in pub:
        m = re.search(r'(\d+)', pub)
        months = int(m.group(1)) if m else 1
        return (now - datetime.timedelta(days=30*months)).strftime('%Y-%m-%d')
    elif 'week' in pub:
        m = re.search(r'(\d+)', pub)
        weeks = int(m.group(1)) if m else 1
        return (now - datetime.timedelta(days=7*weeks)).strftime('%Y-%m-%d')
    elif 'day' in pub:
        m = re.search(r'(\d+)', pub)
        days = int(m.group(1)) if m else 1
        return (now - datetime.timedelta(days=days)).strftime('%Y-%m-%d')
    return '2023-06-15'

def categorize(title, snippet, rules):
    text = (title + " " + snippet).lower()
    matched_categories = []
    
    for category_name, keywords in rules:
        for kw in keywords:
            if re.search(r'\b' + re.escape(kw) + r'\b', text):
                matched_categories.append(category_name)
                break

    if not matched_categories:
        matched_categories.append("Beginner Guides")
    
    primary = matched_categories[0]
    descriptors = ", ".join(matched_categories)
    return primary, matched_categories, f"{primary} ({descriptors})"

def fetch_query(query, rules):
    items = []
    try:
        results = scrapetube.get_search(query, limit=50)
        for v in results:
            vid = v.get('videoId')
            if not vid:
                continue
            title = extract_title(v)
            if not title:
                continue
            author = extract_author(v)
            snippet = extract_snippet(v)
            views = parse_views(v)
            date_str = parse_relative_date(v)
            url = f"https://www.youtube.com/watch?v={vid}"

            primary, tags, cat_desc = categorize(title, snippet, rules)

            items.append({
                "vid": vid,
                "autor": author,
                "titulo": title,
                "enlace": url,
                "categoria_principal": primary,
                "tags": tags,
                "categoria_descriptores": cat_desc,
                "vistas_reales": views,
                "fecha_publicacion": date_str
            })
    except Exception as e:
        print(f"Error query '{query}': {e}", flush=True)
    return items

def compute_3d_latent_space(records):
    documents = []
    for r in records:
        text_content = f"{r.get('titulo', '')} {r.get('categoria_principal', '')} {' '.join(r.get('tags', []))} {r.get('categoria_descriptores', '')}"
        documents.append(text_content.lower())

    vectorizer = TfidfVectorizer(max_features=300, stop_words='english')
    X = vectorizer.fit_transform(documents)

    tsne = TSNE(n_components=3, perplexity=30, random_state=42, init='pca', learning_rate='auto')
    coords_3d = tsne.fit_transform(X.toarray())

    x_min, x_max = coords_3d[:, 0].min(), coords_3d[:, 0].max()
    y_min, y_max = coords_3d[:, 1].min(), coords_3d[:, 1].max()
    z_min, z_max = coords_3d[:, 2].min(), coords_3d[:, 2].max()

    norm_x = ((coords_3d[:, 0] - x_min) / (x_max - x_min) * 240 - 120).round(2)
    norm_y = ((coords_3d[:, 1] - y_min) / (y_max - y_min) * 240 - 120).round(2)
    norm_z = ((coords_3d[:, 2] - z_min) / (z_max - z_min) * 240 - 120).round(2)

    for idx, r in enumerate(records):
        r['latent_x'] = float(norm_x[idx])
        r['latent_y'] = float(norm_y[idx])
        r['latent_z'] = float(norm_z[idx])

    return records

def process_software(sw_key, cfg):
    print(f"\n=================================================================", flush=True)
    print(f"  Procesando categorías expandidas para {cfg['title']} ({sw_key})", flush=True)
    print(f"=================================================================", flush=True)
    
    all_raw_items = []
    seen_vids = set()

    with ThreadPoolExecutor(max_workers=12) as executor:
        futures = [executor.submit(fetch_query, q, cfg['rules']) for q in cfg['queries']]

        for future in as_completed(futures):
            res = future.result()
            for item in res:
                if item["vid"] not in seen_vids:
                    seen_vids.add(item["vid"])
                    all_raw_items.append(item)

    print(f"Total recolectado de YouTube para {sw_key}: {len(all_raw_items)} únicos reales", flush=True)

    df_temp = pd.DataFrame(all_raw_items)
    df_temp.drop_duplicates(subset=["enlace"], inplace=True)
    df_temp = df_temp.sort_values(by="vistas_reales", ascending=False).reset_index(drop=True)

    if len(df_temp) > 500:
        df_temp = df_temp.iloc[:500]

    records = df_temp.to_dict(orient="records")

    records = compute_3d_latent_space(records)

    with open(cfg['json'], 'w', encoding='utf-8') as f:
        json.dump(records, f, ensure_ascii=False, indent=2)

    csv_records = []
    js_records = []
    for idx, r in enumerate(records):
        csv_records.append({
            "autor": r["autor"],
            "titulo": r["titulo"],
            "enlace": r["enlace"],
            "categoria_descriptores": r["categoria_descriptores"],
            "vistas_reales": r["vistas_reales"],
            "fecha_publicacion": r["fecha_publicacion"],
            "latent_x": r["latent_x"],
            "latent_y": r["latent_y"],
            "latent_z": r["latent_z"]
        })
        
        js_records.append({
            'id': idx + 1,
            'vid': r["vid"],
            'autor': r["autor"],
            'titulo': r["titulo"],
            'enlace': r["enlace"],
            'categoria_principal': r["categoria_principal"],
            'tags': r["tags"],
            'categoria_descriptores': r["categoria_descriptores"],
            'views': r["vistas_reales"],
            'upload_date': r["fecha_publicacion"],
            'latent_x': r["latent_x"],
            'latent_y': r["latent_y"],
            'latent_z': r["latent_z"]
        })

    final_df = pd.DataFrame(csv_records)
    final_df['latent_x'] = final_df['latent_x'].round(2)
    final_df['latent_y'] = final_df['latent_y'].round(2)
    final_df['latent_z'] = final_df['latent_z'].round(2)
    final_df.to_csv(cfg['csv'], index=False, encoding="utf-8-sig")

    var_name = "TUTORIALS_DATA" if sw_key == "td" else f"{sw_key.upper()}_TUTORIALS_DATA"
    window_name = "window.TD_DATA" if sw_key == "td" else f"window.{sw_key.upper()}_DATA"
    with open(cfg['js'], 'w', encoding='utf-8') as f:
        f.write(f"const {var_name} = " + json.dumps(js_records, ensure_ascii=False, indent=2) + f";\n{window_name} = {var_name};\n")

    print(f"¡ÉXITO! {len(final_df)} tutoriales guardados con categorías expandidas para {cfg['title']}:", flush=True)
    print(f"  - {cfg['csv']}", flush=True)
    print(f"  - {cfg['js']}", flush=True)

def main():
    print("=== Iniciando Actualización Completa de Categorías Expandidas (8-10 por Software) ===", flush=True)
    for sw_key, cfg in SOFTWARE_DEFINITIONS.items():
        process_software(sw_key, cfg)
    print("\n=== EXPANSIÓN Y REGENERACIÓN COMPLETA DE CATEGORÍAS FINALIZADA CON ÉXITO TOTAL ===", flush=True)

if __name__ == "__main__":
    main()
