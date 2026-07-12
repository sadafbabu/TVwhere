import urllib.request
import json
import hashlib
import threading
import time
import re
from pathlib import Path
from tvwhere.config import CACHE_DIR, CACHE_TTL, ensure_dirs

def get_url_hash(url: str) -> str:
    """Generate a stable MD5 hash for a URL to use as cache filename."""
    return hashlib.md5(url.encode('utf-8')).hexdigest()

def get_cached_playlist(url: str) -> list:
    """Retrieve playlist from cache if it exists and is not expired."""
    ensure_dirs()
    cache_file = CACHE_DIR / f"{get_url_hash(url)}.json"
    if cache_file.exists():
        file_time = cache_file.stat().st_mtime
        if (time.time() - file_time) < CACHE_TTL:
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
    return None

def save_to_cache(url: str, data: list):
    """Save parsed playlist to local cache."""
    ensure_dirs()
    cache_file = CACHE_DIR / f"{get_url_hash(url)}.json"
    try:
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Error writing to cache: {e}")

def parse_m3u(content: str) -> list:
    """Parse raw M3U content and return a list of channel dicts."""
    # Strip Windows line endings
    content = content.replace('\r', '')
    lines = content.split('\n')
    
    channels = []
    current_meta = {}
    
    # Regex to extract tvg tags
    logo_regex = re.compile(r'tvg-logo="([^"]*)"')
    group_regex = re.compile(r'group-title="([^"]*)"')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        if line.startswith('#EXTINF:'):
            # Parse attributes
            logo_match = logo_regex.search(line)
            group_match = group_regex.search(line)
            
            logo = logo_match.group(1) if logo_match else ""
            group = group_match.group(1) if group_match else "General"
            
            # Find the channel name (after the last comma)
            idx = line.rfind(',')
            if idx != -1:
                name = line[idx+1:].strip()
            else:
                name = "Unknown Channel"
                
            # Clean name from redundant resolution/group info
            # Detect resolution (1080p, 720p, 4k, etc.)
            res_match = re.search(r'\b(4k|1080p|720p|480p|360p)\b', name, re.IGNORECASE)
            resolution = res_match.group(1).lower() if res_match else ""
            
            current_meta = {
                'name': name,
                'logo': logo,
                'group': group,
                'resolution': resolution
            }
        elif line.startswith('http://') or line.startswith('https://'):
            if current_meta:
                current_meta['url'] = line
                channels.append(current_meta)
                current_meta = {}
                
    return channels

def fetch_and_parse(url: str, callback, error_callback):
    """Worker function to fetch, parse, cache, and invoke callbacks."""
    # First check cache
    cached = get_cached_playlist(url)
    if cached is not None:
        callback(cached)
        return

    # Fetch from web
    try:
        req = urllib.request.Request(
            url, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        )
        with urllib.request.urlopen(req, timeout=15) as response:
            content = response.read().decode('utf-8', errors='ignore')
            
        channels = parse_m3u(content)
        if channels:
            save_to_cache(url, channels)
            callback(channels)
        else:
            error_callback("Empty playlist or failed to parse channels.")
    except Exception as e:
        error_callback(f"Failed to load playlist: {str(e)}")

def get_channels_async(url: str, callback, error_callback):
    """Fetch channels in a background thread to prevent UI lockup."""
    thread = threading.Thread(
        target=fetch_and_parse, 
        args=(url, callback, error_callback),
        daemon=True
    )
    thread.start()
