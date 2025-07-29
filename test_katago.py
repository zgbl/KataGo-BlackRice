#!/usr/bin/env python3
import json
import subprocess

def test_katago_analysis():
    """Test KataGo analysis with simple query"""
    print("Testing KataGo analysis...")
    
    # Simple query - empty board analysis
    query = {
        "id": "test_simple",
        "moves": [],
        "rules": "tromp-taylor",
        "komi": 7.5,
        "boardXSize": 19,
        "boardYSize": 19,
        "analyzeTurns": [0],
        "maxVisits": 50  # Override config file setting
    }
    
    query_json = json.dumps(query)
    print(f"Query: {query_json}")
    
    try:
        # Run analysis
        cmd = [
            "docker", "exec", "-i", "katago-gpu",
            "timeout", "30",
            "katago", "analysis",
            "-config", "/app/configs/analysis_example.cfg",
            "-model", "/app/models/model.bin.gz"
        ]
        
        result = subprocess.run(cmd, input=query_json, text=True, 
                              capture_output=True, timeout=35)
        
        print(f"\nReturn code: {result.returncode}")
        print(f"Stdout length: {len(result.stdout)}")
        print(f"Stderr length: {len(result.stderr)}")
        
        if result.stdout:
            print("\nFirst 500 chars of stdout:")
            print(result.stdout[:500])
            
        if result.stderr:
            print("\nFirst 500 chars of stderr:")
            print(result.stderr[:500])
            
        # Look for JSON response
        if result.returncode == 0:
            for line in result.stdout.split('\n'):
                line = line.strip()
                if line and line.startswith('{') and '"id":"test_simple"' in line:
                    try:
                        response = json.loads(line)
                        print(f"\n✅ Analysis successful!")
                        print(f"ID: {response.get('id')}")
                        root_info = response.get('rootInfo', {})
                        print(f"Visits: {root_info.get('visits', 0)}")
                        print(f"Winrate: {root_info.get('winrate', 0):.3f}")
                        return True
                    except json.JSONDecodeError as e:
                        print(f"JSON decode error: {e}")
                        continue
        
        print("❌ Analysis failed or no valid response found")
        return False
        
    except subprocess.TimeoutExpired:
        print("❌ Command timeout")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_with_moves():
    """Test analysis with actual moves"""
    print("\nTesting with moves...")
    
    query = {
        "id": "test_moves",
        "moves": [["B", "Q4"], ["W", "D4"]],
        "rules": "tromp-taylor",
        "komi": 7.5,
        "boardXSize": 19,
        "boardYSize": 19,
        "analyzeTurns": [2],
        "maxVisits": 30  # Even fewer visits
    }
    
    query_json = json.dumps(query)
    print(f"Query: {query_json}")
    
    try:
        cmd = [
            "docker", "exec", "-i", "katago-gpu",
            "timeout", "20",
            "katago", "analysis",
            "-config", "/app/configs/analysis_example.cfg",
            "-model", "/app/models/model.bin.gz"
        ]
        
        result = subprocess.run(cmd, input=query_json, text=True, 
                              capture_output=True, timeout=25)
        
        print(f"\nReturn code: {result.returncode}")
        
        if result.returncode == 0:
            for line in result.stdout.split('\n'):
                line = line.strip()
                if line and line.startswith('{') and '"id":"test_moves"' in line:
                    try:
                        response = json.loads(line)
                        print(f"✅ Move analysis successful!")
                        root_info = response.get('rootInfo', {})
                        print(f"Winrate: {root_info.get('winrate', 0):.3f}")
                        print(f"Visits: {root_info.get('visits', 0)}")
                        
                        # Show best moves
                        move_infos = response.get('moveInfos', [])
                        if move_infos:
                            print("Best moves:")
                            for i, move_info in enumerate(move_infos[:3]):
                                move = move_info.get('move', 'pass')
                                visits = move_info.get('visits', 0)
                                winrate = move_info.get('winrate', 0)
                                print(f"  {i+1}. {move} (visits: {visits}, winrate: {winrate:.3f})")
                        return True
                    except json.JSONDecodeError:
                        continue
        
        print("❌ Move analysis failed")
        if result.stderr:
            print(f"Error: {result.stderr[:300]}")
        return False
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("🎯 KataGo Analysis Test")
    print("=" * 40)
    
    # Test 1: Simple empty board
    success1 = test_katago_analysis()
    
    # Test 2: With moves (only if first test passed)
    if success1:
        success2 = test_with_moves()
        if success2:
            print("\n🎉 All tests passed! KataGo is working correctly.")
        else:
            print("\n⚠️ Basic test passed, but move analysis failed.")
    else:
        print("\n❌ Basic test failed. Check KataGo configuration.")