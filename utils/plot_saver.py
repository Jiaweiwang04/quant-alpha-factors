import os

def save_plot(fig, filename="backtest_result.png"):
    
    path = os.path.join("images", filename)
    fig.savefig(path)
    print(f"save plot to {path}")