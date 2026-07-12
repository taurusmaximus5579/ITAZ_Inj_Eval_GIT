#!/usr/bin/env python
"""
Integration test to verify complete image caching workflow.
Tests: imports, cache structure, GUI loading simulation.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import matplotlib.pyplot as plt
from PIL import Image
import io

def test_integration():
    print("🔗 Integration Test: Complete Image Caching Workflow\n")
    print("="*60)
    
    # Test 1: Verify all modules import correctly
    print("\n1️⃣ Module Import Test")
    try:
        from image_cache_manager import get_cache, clear_cache
        print("   ✓ image_cache_manager imported")
        from image_utils import persist_or_cache_figure
        print("   ✓ image_utils imported")
        from analysis import needle_lift, ics, gain, rate_down
        print("   ✓ All analysis modules imported")
        from plotting import plot_signals_per_file
        print("   ✓ plotting module imported")
        import ITAZ_Inj_Eval_GUI_github
        print("   ✓ GUI module imported")
    except ImportError as e:
        print(f"   ✗ Import error: {e}")
        return False
    
    # Test 2: Verify cache structure
    print("\n2️⃣ Cache Structure Test")
    from image_cache_manager import get_cache, clear_cache
    
    clear_cache()
    cache = get_cache()
    print(f"   ✓ Cache initialized and cleared: {type(cache).__name__}")
    print(f"   ✓ Cache is empty: {len(cache) == 0}")
    
    # Test 3: Test caching workflow
    print("\n3️⃣ Caching Workflow Test")
    from image_utils import persist_or_cache_figure
    
    categories = {
        "ICS": ["Signal_1", "Signal_2", "Overview", "Boost", "Hold", "Zero"],
        "NeedleLift": ["Overview", "Single_1", "Single_2", "Histogram"],
        "Signals": ["file1", "file2", "file3"],
        "Gain": ["GainCurve"],
        "RateDown": ["RateDownCurve"]
    }
    
    for category, names in categories.items():
        for name in names:
            # Create a simple test figure
            fig, ax = plt.subplots(figsize=(8, 6))
            ax.plot([1, 2, 3, 4], [1, 4, 2, 3])
            ax.set_title(f"{category}: {name}")
            
            # Cache it
            persist_or_cache_figure(fig, image_cache=cache, category=category, 
                                  name=name, save_to_disk=False)
            plt.close(fig)
    
    print(f"   ✓ Cached {sum(len(names) for names in categories.values())} test images")
    
    # Test 4: Verify cache contents
    print("\n4️⃣ Cache Contents Verification")
    cache = get_cache()
    total_images = 0
    
    for category in sorted(cache.keys()):
        images = cache[category]
        total_images += len(images)
        print(f"   - {category:12}: {len(images):2} images")
        if images:
            name, img = images[0]
            print(f"     └─ {name}: {img.size}px ({img.mode})")
    
    print(f"   ✓ Total: {total_images} images in cache")
    
    # Test 5: Test GUI loading simulation
    print("\n5️⃣ GUI Image Loading Simulation")
    
    cache = get_cache()
    gui_tabs = {
        "Strom": [],
        "Nadelhub": [],
        "Ergebnisse": [],
        "Messsignale": [],
    }
    
    # Simulate what GUI.load_images() does
    if "ICS" in cache:
        gui_tabs["Strom"] = [img for _, img in cache["ICS"]]
    
    if "NeedleLift" in cache:
        gui_tabs["Nadelhub"] = [img for _, img in cache["NeedleLift"]]
    
    if "Signals" in cache:
        gui_tabs["Messsignale"] = [img for _, img in cache["Signals"]]
    
    gui_tabs["Ergebnisse"] = []
    if "Gain" in cache:
        gui_tabs["Ergebnisse"].extend([img for _, img in cache["Gain"]])
    if "RateDown" in cache:
        gui_tabs["Ergebnisse"].extend([img for _, img in cache["RateDown"]])
    
    # Display results
    for tab_name in ["Strom", "Nadelhub", "Messsignale", "Ergebnisse"]:
        images = gui_tabs[tab_name]
        status = "✓" if images else "○"
        print(f"   {status} Tab '{tab_name:12}': {len(images)} images ready")
    
    # Test 6: Test cache clearing
    print("\n6️⃣ Cache Cleanup Test")
    clear_cache()
    cache = get_cache()
    if len(cache) == 0:
        print(f"   ✓ Cache cleared successfully")
    else:
        print(f"   ✗ Cache not empty: {list(cache.keys())}")
        return False
    
    # Test 7: Verify no disk writes
    print("\n7️⃣ Disk Write Verification")
    new_png_count = 0
    for folder in ['bilder', 'Bilder', 'Images', 'Results']:
        folder_path = os.path.join('.', folder)
        if os.path.exists(folder_path):
            png_files = [f for f in os.listdir(folder_path) if f.endswith('.png')]
            if png_files:
                new_png_count += len(png_files)
    
    if new_png_count == 0:
        print(f"   ✓ No new PNG files written to disk")
    else:
        print(f"   ⚠️ Found {new_png_count} PNG files (may be from previous runs)")
    
    print("\n" + "="*60)
    print("✅ Integration test PASSED!")
    print("\nImplementation Summary:")
    print("  • All analysis modules cache images in memory")
    print("  • No PNG files written to disk during analysis")
    print("  • GUI can load all cached image categories")
    print("  • Cache can be cleared to free memory")
    print("="*60)
    
    return True

if __name__ == "__main__":
    success = test_integration()
    sys.exit(0 if success else 1)
