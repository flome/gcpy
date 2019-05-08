import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from . import gcdb, gcana, utils

def plot(addText="internal", **kwargs):   
    fig = plt.figure(**kwargs)        
    
    addTLDOSlabel(fig=fig, addText=addText)
    return fig

if __name__ == "__main__":

    print("A module for simple glow curve plotting.")

    