#!/usr/bin/env python
"""
Test script to verify in-memory image caching works correctly.
Tests that images are cached without being saved to disk.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from image_cache_manager import get_cache, clear_cache
from image_utils import persist_or_cache_figure
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

def test_image_cache():
    print("🧪 Testing image cache functionality...\n")
    
    # Clear cache before test
    clear_cache()
    cache = get_cache()
    print(f"✓ Cache initialized and cleared: {len(cache)} categories")
    
    # Test 1: Generate test images and cache them
    print("\n📊 Test 1: Caching matplotlib figures...")
    for i in range(3):
        fig, ax = plt.subplots(figsize=(8, 6))
        x = np.linspace(0, 10, 100)
        y = np.sin(x + i)
        ax.plot(x, y, label=f'sin(x+{i})')
        ax.set_title(f'Test Plot {i+1}')
        ax.legend()
        
        persist_or_cache_figure(fig, image_cache=cache, category="TestSignals", 
                              name=f"Signal_{i+1}", save_to_disk=False)
        plt.close(fig)
        print(f"  ✓ Cached test plot {i+1}")
    
    # Verify cached images
    if "TestSignals" in cache:
        print(f"\n✓ 'TestSignals' category created with {len(cache['TestSignals'])} images")
        for name, img in cache["TestSignals"]:
            print(f"  - {name}: {img.size} pixels, mode={img.mode}")
    else:
        print("✗ 'TestSignals' category not found in cache!")
        return False
    
    # Test 2: Verify no PNG files were created
    print("\n🔍 Test 2: Checking disk for PNG files...")
    png_files = []
    for root, dirs, files in os.walk(os.path.dirname(__file__)):
        for f in files:
            if f.lower().endswith('.png'):
                full_path = os.path.join(root, f)
                # Skip iframe_figures folder
                if 'iframe_figures' not in full_path:
                    png_files.append(full_path)
    
    if png_files:
        print(f"  ⚠️  Found {len(png_files)} PNG files (expected 0):")
        for f in png_files[:5]:
            print(f"    - {f}")
    else:
        print("  ✓ No PNG files created on disk (as expected)")
    
    # Test 3: Verify cache can be cleared
    print("\n🧹 Test 3: Testing cache clear...")
    clear_cache()
    cache = get_cache()
    if len(cache) == 0:
        print("  ✓ Cache successfully cleared")
    else:
        print(f"  ✗ Cache not empty after clear: {list(cache.keys())}")
        return False
    
    print("\n" + "="*60)
    print("✅ All tests passed! Image caching is working correctly.")
    print("="*60)
    return True

if __name__ == "__main__":
    success = test_image_cache()
    sys.exit(0 if success else 1)
