# Assembly Line: Scene-by-Scene Blueprint Generator
# Purpose: Generate visual cues and editing instructions for InShot

def generate_blueprint(script_title, scenes):
    print(f"--- Visual Blueprint: {script_title} ---")
    blueprint = []
    for i, scene in enumerate(scenes):
        entry = f"Scene {i+1} ({scene['duration']}s): {scene['visual']} | Overlay: {scene['text']}"
        blueprint.append(entry)
    return blueprint

if __name__ == "__main__":
    # Example Blueprint for Victor Sokolov: The Ghost Key
    v_scenes = [
        {"duration": 5, "visual": "Noir/Dark office, silhouette of man at desk", "text": "THE GHOST KEY"},
        {"duration": 8, "visual": "Digital rain, green code over luxury penthouse", "text": "THE 00M HEIST"},
        {"duration": 7, "visual": "Close up: Cold eyes, cigarette smoke", "text": "NO TRACE LEFT"}
    ]
    data = generate_blueprint("Victor Sokolov: The Ghost Key", v_scenes)
    for line in data:
        print(line)
