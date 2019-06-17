from gcpy import gcplot
import matplotlib.pyplot as plt
import numpy as np


x = np.linspace(0, 2*np.pi, 200)
y = np.sin(x)

for style in ["screen", "print"]:
    gcplot.setPlotStyle(style)
    fig = gcplot.getStyledFigure()
    plt.plot(x, y)
    plt.xlabel('x')
    plt.ylabel('y')
    plt.savefig("output/test_%s_0.png"%style)
    plt.show()
    fig = None

y = 10000*y

for style in ["screen", "print"]:
    gcplot.setPlotStyle(style)
    fig = gcplot.getStyledFigure()
    plt.plot(x, y)
    plt.xlabel('x')
    plt.ylabel('y')
    plt.savefig("output/test_%s_1.png"%style)  
    plt.show()
    fig = None

y = 10000*y

for style in ["screen", "print"]:
    gcplot.setPlotStyle(style)
    fig = gcplot.getStyledFigure()
    plt.plot(x, y)
    plt.xlabel('x')
    plt.ylabel('y')
    plt.savefig("output/test_%s_2.png"%style)  
    plt.show()
    fig = None
