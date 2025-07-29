#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KataGo Windows Test Script
Based on stepbystep.py, adapted for Windows Docker environment
"""

import json
import subprocess
import time
import re
import sys

# Analysis settings
ANALYSIS_SETTINGS = {
    'max_visits': 200,
    'max_time': 3.0,
    'timeout': 5
}

# Windows Docker container name (from docker-compose.yml)
CONTAINER_NAME = "katago-gpu"  # Using GPU version

def check_docker_status():
    """Check if Docker container is running"""
    try:
        # Check if container exists and is running
        result = subprocess.run([
            "docker", "ps", "--filter", f"name={CONTAINER_NAME}", "--format", "{{.Status}}"
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0 and "Up" in result.stdout:
            print(f"✅ Docker container '{CONTAINER_NAME}' is running")
            return True
        else:
            print(f"❌ Docker container '{CONTAINER_NAME}' is not running")
            print("Please start the container with: docker-compose up -d katago-gpu")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Docker command timeout")
        return False
    except Exception as e:
        print(f"❌ Docker status check failed: {e}")
        return False

def test_basic_analysis():
    """Test basic KataGo analysis functionality"""
    print("Testing basic KataGo analysis...")
    
    # Simple test query
    test_query = {
        "id": "test",
        "moves": [],
        "rules": "tromp-taylor",
        "komi": 7.5,
        "boardXSize": 19,
        "boardYSize": 19,
        "analyzeTurns": [0],
        "maxVisits": 10
    }
    
    query_json = json.dumps(test_query)
    
    try:
        # Use docker exec to run analysis
        cmd = [
            "docker", "exec", "-i", CONTAINER_NAME,
            "timeout", "15",
            "katago", "analysis",
            "-config", "/app/configs/analysis_example.cfg",
            "-model", "/app/models/model.bin.gz"
        ]
        
        result = subprocess.run(cmd, input=query_json, text=True, capture_output=True, timeout=20)
        
        print(f"Return code: {result.returncode}")
        
        if result.returncode == 0:
            # Look for JSON response
            for line in result.stdout.split('\n'):
                line = line.strip()
                if line and line.startswith('{'):
                    try:
                        response = json.loads(line)
                        print(f"✅ Basic analysis successful! ID: {response.get('id')}")
                        root_info = response.get('rootInfo', {})
                        visits = root_info.get('visits', 0)
                        winrate = root_info.get('winrate', 0)
                        print(f"Visits: {visits}, Winrate: {winrate:.3f}")
                        
                        if visits > 0:
                            print("✅ Basic analysis test passed")
                            return True
                    except json.JSONDecodeError:
                        continue
        
        print("❌ Basic analysis test failed - no valid response")
        if result.stderr:
            print(f"Error: {result.stderr[:300]}")
        return False
        
    except subprocess.TimeoutExpired:
        print("❌ Test command timeout")
        return False
    except Exception as e:
        print(f"❌ Basic analysis test failed - {e}")
        return False

def send_analysis_query(moves, analyze_turn, debug=False):
    """Send analysis query to KataGo"""
    # Build moves list for KataGo
    katago_moves = []
    for i, (color, pos) in enumerate(moves[:analyze_turn]):
        if pos.lower() != "pass":
            katago_moves.append([color.upper(), pos.upper()])
        else:
            katago_moves.append([color.upper()])
    
    # Create analysis query
    query = {
        "id": f"analysis_{analyze_turn}",
        "moves": katago_moves,
        "rules": "tromp-taylor",
        "komi": 7.5,
        "boardXSize": 19,
        "boardYSize": 19,
        "analyzeTurns": [len(katago_moves)],
        "maxVisits": ANALYSIS_SETTINGS['max_visits']
    }
    
    if debug:
        print(f"Query: {json.dumps(query, indent=2)}")
    
    query_json = json.dumps(query)
    
    try:
        cmd = [
            "docker", "exec", "-i", CONTAINER_NAME,
            "timeout", str(ANALYSIS_SETTINGS['timeout']),
            "katago", "analysis",
            "-config", "/app/configs/analysis_example.cfg",
            "-model", "/app/models/model.bin.gz"
        ]
        
        result = subprocess.run(cmd, input=query_json, text=True, capture_output=True, 
                              timeout=ANALYSIS_SETTINGS['timeout'] + 5)
        
        if debug:
            print(f"Return code: {result.returncode}")
            print(f"Stdout: {result.stdout[:500]}")
            if result.stderr:
                print(f"Stderr: {result.stderr[:300]}")
        
        if result.returncode == 0:
            # Parse JSON response
            for line in result.stdout.split('\n'):
                line = line.strip()
                if line and line.startswith('{'):
                    try:
                        response = json.loads(line)
                        if response.get('id') == query['id']:
                            return response
                    except json.JSONDecodeError:
                        continue
        
        return None
        
    except subprocess.TimeoutExpired:
        if debug:
            print("Analysis timeout")
        return None
    except Exception as e:
        if debug:
            print(f"Analysis error: {e}")
        return None

def test_simple_game():
    """Test analysis with a simple game sequence"""
    print("\n🎯 Testing simple game analysis")
    print("=" * 50)
    
    # Simple game moves
    test_moves = [
        ["B", "Q4"],   # Black Q4
        ["W", "D4"],   # White D4
        ["B", "Q16"],  # Black Q16
        ["W", "D16"],  # White D16
        ["B", "C3"]    # Black C3
    ]
    
    print(f"Analyzing {len(test_moves)} moves...")
    
    # First check basic functionality
    if not test_basic_analysis():
        print("❌ Basic test failed, stopping")
        return False
    
    # Analyze each position
    for i in range(1, len(test_moves) + 1):
        current_move = test_moves[i-1]
        print(f"\n📍 Move {i}: {current_move[0]} {current_move[1]}")
        print(f"   Analyzing... ", end="", flush=True)
        
        start_time = time.time()
        result = send_analysis_query(test_moves, i)
        end_time = time.time()
        
        if result:
            root_info = result.get('rootInfo', {})
            winrate = root_info.get('winrate', 0)
            score_lead = root_info.get('scoreLead', 0)
            visits = root_info.get('visits', 0)
            
            # Get best move
            best_move = "None"
            if 'moveInfos' in result and result['moveInfos']:
                best_move = result['moveInfos'][0]['move']
            
            print(f"✅ ({end_time - start_time:.1f}s)")
            
            # Display results based on whose turn it is
            is_black_turn = (i % 2 == 1)
            if is_black_turn:
                color_indicator = "⚫"
                display_winrate = winrate
                player = "Black"
            else:
                color_indicator = "⚪"
                display_winrate = 1 - winrate
                player = "White"
            
            print(f"   {color_indicator} {player} winrate: {display_winrate:.1%} | Score: {score_lead:+.1f} | Visits: {visits} | Best: {best_move}")
            
        else:
            print(f"❌ Analysis failed")
            return False
    
    print("\n✅ Simple game analysis completed successfully!")
    return True

def configure_settings():
    """Configure analysis settings"""
    print("\n⚙️  Analysis Settings")
    print("=" * 30)
    print(f"Current settings:")
    print(f"  Visits: {ANALYSIS_SETTINGS['max_visits']}")
    print(f"  Time limit: {ANALYSIS_SETTINGS['max_time']}s")
    print(f"  Timeout: {ANALYSIS_SETTINGS['timeout']}s")
    
    print("\nSelect mode:")
    print("1. Fast mode (30 visits, 5s) - Recommended for testing")
    print("2. Standard mode (100 visits, 10s)")
    print("3. Precise mode (300 visits, 20s)")
    print("4. Custom settings")
    print("0. Keep current settings")
    
    choice = input("\nSelect (0-4): ").strip()
    
    if choice == "1":
        ANALYSIS_SETTINGS['max_visits'] = 30
        ANALYSIS_SETTINGS['max_time'] = 5.0
        ANALYSIS_SETTINGS['timeout'] = 10
        print("✅ Set to fast mode")
    elif choice == "2":
        ANALYSIS_SETTINGS['max_visits'] = 100
        ANALYSIS_SETTINGS['max_time'] = 10.0
        ANALYSIS_SETTINGS['timeout'] = 15
        print("✅ Set to standard mode")
    elif choice == "3":
        ANALYSIS_SETTINGS['max_visits'] = 300
        ANALYSIS_SETTINGS['max_time'] = 20.0
        ANALYSIS_SETTINGS['timeout'] = 25
        print("✅ Set to precise mode")
    elif choice == "4":
        try:
            visits = int(input("Visits (10-1000): "))
            time_limit = float(input("Time limit(s) (1-60): "))
            
            if 10 <= visits <= 1000 and 1 <= time_limit <= 60:
                ANALYSIS_SETTINGS['max_visits'] = visits
                ANALYSIS_SETTINGS['max_time'] = time_limit
                ANALYSIS_SETTINGS['timeout'] = int(time_limit + 5)
                print("✅ Custom settings saved")
            else:
                print("❌ Parameters out of range")
        except ValueError:
            print("❌ Please enter valid numbers")
    elif choice == "0":
        print("✅ Keeping current settings")
    else:
        print("❌ Invalid choice")

def diagnose_system():
    """Diagnose KataGo system"""
    print("\n🔍 KataGo System Diagnosis")
    print("=" * 40)
    
    # 1. Check container status
    print("1. Checking Docker container...")
    if not check_docker_status():
        return False
    
    # 2. Check config file
    print("\n2. Checking config file...")
    try:
        result = subprocess.run([
            "docker", "exec", CONTAINER_NAME,
            "cat", "/app/configs/analysis_example.cfg"
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print("✅ Config file accessible")
            # Parse key settings
            config_lines = result.stdout.split('\n')
            for line in config_lines[:10]:  # Show first 10 lines
                if '=' in line and not line.strip().startswith('#'):
                    print(f"   {line.strip()}")
        else:
            print("❌ Cannot read config file")
            return False
    except Exception as e:
        print(f"❌ Config file check failed: {e}")
        return False
    
    # 3. Check model file
    print("\n3. Checking model file...")
    try:
        result = subprocess.run([
            "docker", "exec", CONTAINER_NAME,
            "ls", "-la", "/app/models/"
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print("✅ Model directory contents:")
            for line in result.stdout.split('\n'):
                if 'model' in line.lower() or '.bin' in line.lower():
                    print(f"   {line}")
        else:
            print("❌ Cannot access model directory")
            return False
    except Exception as e:
        print(f"❌ Model file check failed: {e}")
        return False
    
    # 4. Test simple analysis
    print("\n4. Testing simple analysis...")
    return test_basic_analysis()

def main():
    """Main function"""
    print("🎯 KataGo Windows Test Tool")
    print("=" * 40)
    
    while True:
        print("\nSelect option:")
        print("1. Quick test (5 moves)")
        print("2. Basic analysis test")
        print("3. Analysis settings")
        print("4. System diagnosis")
        print("5. Debug mode test")
        print("0. Exit")
        
        choice = input("\nEnter choice (0-5): ").strip()
        
        if choice == "0":
            print("Goodbye!")
            break
            
        elif choice == "1":
            test_simple_game()
            
        elif choice == "2":
            test_basic_analysis()
            
        elif choice == "3":
            configure_settings()
            
        elif choice == "4":
            diagnose_system()
            
        elif choice == "5":
            print("\n🐛 Debug mode - testing with verbose output")
            # Test with debug output
            test_moves = [["B", "Q4"], ["W", "D4"]]
            result = send_analysis_query(test_moves, 1, debug=True)
            if result:
                print(f"✅ Debug test successful: {result.get('id')}")
            else:
                print("❌ Debug test failed")
                
        else:
            print("❌ Invalid choice")

if __name__ == "__main__":
    main()