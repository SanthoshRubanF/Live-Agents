import matplotlib.pyplot as plt
import matplotlib.patches as patches

def create_diagram():
    # 1920x1080 resolution
    fig, ax = plt.subplots(figsize=(19.2, 10.8), dpi=100)
    ax.set_xlim(0, 20)
    ax.set_ylim(0, 12)
    ax.axis('off')
    fig.patch.set_facecolor('white')

    # Colors
    GOOGLE_BLUE = '#4285F4'
    GOOGLE_RED = '#EA4335'
    GOOGLE_YELLOW = '#FBBC04'
    GOOGLE_GREEN = '#34A853'
    BOX_BG = '#FFFFFF'
    TEXT_COLOR = '#202124'

    def draw_box(ax, x, y, width, height, title, content="", color=GOOGLE_BLUE):
        # Drop shadow
        shadow = patches.FancyBboxPatch((x+0.1, y-0.1), width, height, 
                                        boxstyle="round,pad=0.2,rounding_size=0.2", 
                                        fc='#000000', alpha=0.1, ec="none")
        ax.add_patch(shadow)
        
        # Main box
        box = patches.FancyBboxPatch((x, y), width, height, 
                                     boxstyle="round,pad=0.2,rounding_size=0.2", 
                                     fc=BOX_BG, ec=color, lw=2.5)
        ax.add_patch(box)
        
        # Title
        ax.text(x + width/2, y + height - 0.2, title, ha='center', va='top', 
                fontsize=16, fontweight='bold', color=color)
        
        # Content list
        if content:
            ax.text(x + 0.3, y + height - 1.0, content, ha='left', va='top', 
                    fontsize=14, color=TEXT_COLOR, linespacing=2.0)

    # 1. Left: Browser
    draw_box(ax, 1, 5, 3.5, 3.5, "Browser (Client)", 
             "• Microphone\n• Camera\n• Audio out", GOOGLE_BLUE)

    # 2. Center: Cloud Run
    draw_box(ax, 8, 4.5, 4.5, 4.5, "Google Cloud Run", 
             "FastAPI + WebSocket\n\n• ADK Runner\n• LiveQueue\n• Session Manager", GOOGLE_GREEN)

    # 3. Right: Google AI
    draw_box(ax, 16, 7, 2.8, 2, "Vertex AI", 
             "Gemini Live\n3.01 Pro", GOOGLE_BLUE)

    draw_box(ax, 16, 3.5, 2.8, 1.8, "Google Search", 
             "(grounding)", GOOGLE_RED)

    def draw_arrow(ax, x1, y1, x2, y2, label, label_x, label_y, color='#5F6368', rad=0.2):
        arrow = patches.FancyArrowPatch((x1, y1), (x2, y2), 
                                        connectionstyle=f"arc3,rad={rad}", 
                                        arrowstyle="simple,head_width=8,head_length=8", 
                                        color=color, lw=2)
        ax.add_patch(arrow)
        bbox_props = dict(boxstyle="round,pad=0.3,rounding_size=0.2", fc="white", ec="none", alpha=0.9)
        ax.text(label_x, label_y, label, ha='center', va='center', fontsize=11, 
                color=color, fontweight='bold', bbox=bbox_props)

    # Arrow definitions
    draw_arrow(ax, 4.7, 7.8, 7.8, 7.8, "PCM audio (16kHz) + JPEG frames via WebSocket", 6.25, 8.3, rad=-0.05)
    draw_arrow(ax, 7.8, 6.2, 4.7, 6.2, "PCM audio (24kHz) + transcripts", 6.25, 5.7, rad=-0.05)

    draw_arrow(ax, 12.7, 8.2, 15.8, 8.2, "Bidi stream (audio + vision)", 14.25, 8.7, rad=-0.05)
    draw_arrow(ax, 15.8, 7.2, 12.7, 7.2, "Audio response + text", 14.25, 6.7, rad=-0.05)

    draw_arrow(ax, 12.7, 5.3, 15.8, 4.7, "Search queries", 14.25, 5.5, rad=-0.05)
    draw_arrow(ax, 15.8, 4.0, 12.7, 4.6, "Grounded facts", 14.25, 3.8, rad=-0.05)

    # Infra row at bottom
    def draw_infra(ax, x, y, width, height, title, color):
        box = patches.FancyBboxPatch((x, y), width, height, boxstyle="round,pad=0.1,rounding_size=0.2", 
                                     fc=color, ec="none")
        ax.add_patch(box)
        ax.text(x + width/2, y + height/2, title, ha='center', va='center', 
                fontsize=14, fontweight='bold', color='white')

    draw_infra(ax, 4.5, 1, 3, 1, "Cloud Build", GOOGLE_BLUE)
    draw_infra(ax, 8.8, 1, 3.5, 1, "Artifact Registry", GOOGLE_YELLOW)
    draw_infra(ax, 13.5, 1, 3, 1, "Cloud Run", GOOGLE_GREEN)

    arrow_style = "simple,head_width=8,head_length=8"
    ax.add_patch(patches.FancyArrowPatch((7.6, 1.5), (8.7, 1.5), color='#5F6368', arrowstyle=arrow_style))
    ax.add_patch(patches.FancyArrowPatch((12.4, 1.5), (13.4, 1.5), color='#5F6368', arrowstyle=arrow_style))

    # Main Title
    ax.text(10, 11, "Gemini Live Agent Architecture", ha='center', va='center', 
            fontsize=26, fontweight='bold', color=TEXT_COLOR)

    # Subtitle
    ax.text(10, 0.2, "CI/CD Pipeline", ha='center', va='center', 
            fontsize=14, fontweight='bold', color='#5F6368')
            
    # Remove margins to strict 1920x1080 without auto-tightening
    plt.subplots_adjust(left=0.01, right=0.99, bottom=0.01, top=0.99)
    
    # Save outputs
    fig.savefig('architecture_diagram.png', dpi=100, facecolor='white')
    fig.savefig('architecture_diagram_thumb.png', dpi=50, facecolor='white')
    print("Saved: architecture_diagram.png")
    print("Saved: architecture_diagram_thumb.png")

if __name__ == "__main__":
    create_diagram()
