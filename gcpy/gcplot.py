# -*- coding: utf-8 -*-
'''
Author: Florian Mentzel <florian.mentzel@udo.edu>, Robert Theinert <robert.theinert@udo.edu>
Date: Jun. 2019
'''

import matplotlib.pyplot as plt

styles = [
    'matplotlib',
    'print',
    'screen'
]


rcParams_general = {    
    # figure
    
    'figure.subplot.wspace' : 0.1,
    'figure.subplot.hspace' : 0.1,
    #'figure.autolayout': True,
    "savefig.bbox" : "tight",
    "savefig.pad_inches" : 0.1,
    # axis
    'axes.labelpad' : 8,
    'axes.ymargin' : 0.1,
    # legend
    'legend.columnspacing' : 1.2,
    'legend.handletextpad' : 0.7,
    'legend.handlelength' : 1.8,
    'legend.edgecolor' : '0.8',
    'legend.numpoints' : 1,
    'legend.scatterpoints' : 1,
    'legend.shadow' : False,
    'legend.frameon' : True,
    'legend.framealpha' : 0.8,
    'legend.fancybox' : True,
    # grid
    #'axes.grid': True,
    'grid.color': 'b0b0b0',
    'grid.linestyle': '-',
    'grid.linewidth': 0.8,
    # xticks
    'xtick.direction': 'in',
    'xtick.top': False,
    'xtick.bottom': True,
    'xtick.major.size' : 4,
    'xtick.minor.size' : 2,
    'xtick.major.pad' : 10.0,
    # yticks          
    'ytick.direction': 'in',
    'ytick.left': True,
    'ytick.right': False,
    'ytick.major.size' : 4,
    'ytick.minor.size' : 2,  
    # lines        
    'lines.linewidth' : 1.5,
    'lines.markersize' : 8,
    'lines.markeredgewidth' : 0.0,
    'lines.linewidth': 1.5,
    'lines.dashed_pattern': [2.8, 1.2],
    'lines.dashdot_pattern': [4.8, 1.2, 0.8, 1.2],
    'lines.dotted_pattern': [1.1, 1.1],
    'lines.scale_dashes': True,
    'errorbar.capsize': 0 ,
    #patches        
    'patch.force_edgecolor': False,
    #text
    'mathtext.fontset': 'dejavusans',
    'mathtext.rm': 'serif'
}

labels = {
    "mainLabel": "TL-DOS",
    "screen": {
        "subLabel": "internal preview",
        "xpos" : 0.21,
        "ypos" : 0.938
    },
    "print": {
        "subLabel": "internal",
        "xpos" : 0.2,
        "ypos" : 0.94
    }
}

rcParams_print = {
    # figure
    'savefig.format' : 'pdf',
    'figure.figsize' : (5,4),
    'figure.dpi' : 300,
    'savefig.dpi' : 300,
    'font.size': 12,
    'figure.subplot.left' : 0,
    'figure.subplot.right' : 1,
    'figure.subplot.bottom' : 0,
    'figure.subplot.top' : 1,
}

rcParams_screen = {
    'savefig.format' : 'png',
    'figure.figsize' : (10,8),
    'figure.dpi' : 96,
    'savefig.dpi' : 96,
    'font.size': 20,
    'figure.subplot.left' : 0.125,
    'figure.subplot.right' : 0.99,
    'figure.subplot.bottom' : 0.12,
    'figure.subplot.top' : 0.98
}


def setPlotStyle(style):
    if style not in styles:
        raise AttributeError("The passed style %s is not valid. Please choose from: %s"%(style, styles))
    
    setPlotStyle.currentStyle = style
    if style == "matplotlib":
        plt.rcdefaults()
        return

    plt.rcParams.update(rcParams_general)
    if style == "print":
        plt.rcParams.update(rcParams_print)
    if style == "screen":
        plt.rcParams.update(rcParams_screen)

setPlotStyle("screen")


def getStyledFigure(mainLabel="TL-DOS", subLabel=None, **kwargs):
    fig = plt.figure(**kwargs)
    if mainLabel:
        if subLabel is None:
            subLabel = labels[setPlotStyle.currentStyle]["subLabel"]
        fig = addTLDOSlabel(fig, mainLabel=mainLabel, subLabel=subLabel)

    return fig

def addTLDOSlabel(fig=None, ax=None, xpos=None, ypos=None, mainLabel=labels["mainLabel"], subLabel=None):
        return addLabel(fig=fig, ax=ax, xpos=xpos, ypos=ypos, mainLabel=mainLabel, subLabel=subLabel)

def addLabel(fig=None, ax=None, xpos=None, ypos=None, mainLabel=None, subLabel=None):
    if fig is None and ax is None:
        raise AttributeError("The passed figure or axis are not valid: \nFigure:%s, Axis:%s "%(figure, axis))

    if fig is None and ax is not None:
        fig = ax.get_figure()
    if fig is None:
        raise AttributeError("No figure was passed and I cannot get figure from axis!")

    ax_color = plt.rcParams["axes.facecolor"]
    if xpos is None:
        xmin = plt.rcParams["figure.subplot.left"]
        xmax = plt.rcParams["figure.subplot.right"]
        xdist = xmax - xmin
        xpos = xmin + xdist*labels[setPlotStyle.currentStyle]["xpos"]
    if ypos is None:
        ymin = plt.rcParams["figure.subplot.bottom"]
        ymax = plt.rcParams["figure.subplot.top"]
        ydist = ymax - ymin 
        ypos = ymin + ydist*labels[setPlotStyle.currentStyle]["ypos"]

    try:                
        fig.text(xpos,ypos,
                mainLabel, 
                fontsize=plt.rcParams['font.size']+2, 
                horizontalalignment='right', verticalalignment='center', 
                family='sans-serif', style='oblique', weight='bold', bbox=dict(facecolor=ax_color, linewidth=0)
                )
    except:
        raise('Error at main label: wrong input-argument type! Please check: mainLabel: %s, subLabel: %s, xpos: %s, ypos: %s'%(
                mainLabel, subLabel, xpos, ypos)
            )

    try:
        fig.text(xpos*1.05,ypos,
                subLabel, fontsize=plt.rcParams['font.size'], 
                horizontalalignment='left', verticalalignment='center',
                family='serif',fontstyle='italic',fontweight='medium', bbox=dict(facecolor=ax_color, linewidth=0)
                )
    except:
        raise('Error at sub label: wrong input-argument type! Please check: mainLabel: %s, subLabel: %s, xpos: %s, ypos: %s'%(
                mainLabel, subLabel, xpos, ypos)
            )
    
    return fig