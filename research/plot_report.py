"""Render exact benchmark figures from saved results; no simulated screenshots."""
from pathlib import Path
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from neuro import dataset,spectrum
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/media'
OUT.mkdir(parents=True,exist_ok=True)
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.spines.top':False,
 'axes.spines.right':False,'axes.labelcolor':'#d0d9ed','text.color':'#f3f6fc',
 'axes.edgecolor':'#435473','xtick.color':'#a6b2c8','ytick.color':'#a6b2c8',
 'axes.titleweight':'bold','grid.color':'#4d648b','figure.facecolor':'#080d18','axes.facecolor':'#080d18','savefig.facecolor':'#080d18'})
report=json.loads((ROOT/'reports/synthetic-benchmark.json').read_text())
fig,axs=plt.subplots(1,2,figsize=(13,4.7),gridspec_kw={'width_ratios':[1.6,1]},layout='constrained')
h=report['history']
axs[0].plot([a['epoch'] for a in h],[a['train_loss'] for a in h],color='#6b9cff',label='Training')
axs[0].plot([a['epoch'] for a in h],[a['validation_loss'] for a in h],color='#ff9858',label='Validation')
axs[0].set(xlabel='Epoch',ylabel='Cross-entropy loss',title='Learning on artificial frequency patterns')
axs[0].legend(frameon=False);axs[0].grid(alpha=.12)
cm=np.array(report['cnn']['confusion_matrix'])
from matplotlib.colors import LinearSegmentedColormap
axs[1].imshow(cm,cmap=LinearSegmentedColormap.from_list('signal',['#10192b','#2662e8']),vmin=0,vmax=48)
axs[1].set(xticks=[0,1],yticks=[0,1],xticklabels=['A','B'],yticklabels=['A','B'],xlabel='Predicted condition',ylabel='Generated condition',title='Held-out virtual subjects · CNN')
for i in range(2):
 for j in range(2):axs[1].text(j,i,str(cm[i,j]),ha='center',va='center',fontsize=24,color='#f3f6fc')
fig.suptitle('NEUROWEAVE  /  MODEL AUDIT  /  SYNTHETIC BENCHMARK',fontsize=15,fontweight='bold')
fig.supxlabel('96 held-out artificial windows. Both CNN and spectral baseline: 100% balanced accuracy. Not evidence of real EEG performance.',fontsize=9)
fig.savefig(OUT/'benchmark.png',dpi=160);plt.close(fig)
x,y,ids=dataset();fig,axs=plt.subplots(2,2,figsize=(13,5.2),layout='constrained')
for label,color in [(0,'#6b9cff'),(1,'#ff9858')]:
 raw=x[480+label];f,p=spectrum(raw)
 axs[label,0].plot(np.arange(256)/128,raw[0],color=color,lw=1.2)
 axs[label,0].set(title=f'Condition {"AB"[label]} · channel 1',xlabel='Time (s)',ylabel='Amplitude (µV)',ylim=(-35,35))
 axs[label,1].plot(f,p,color=color);axs[label,1].set(xlim=(0,40),xlabel='Frequency (Hz)',ylabel='PSD (µV²/Hz)',title='Hann periodogram · 8-channel average')
 for ax in axs[label]:ax.grid(alpha=.12)
fig.suptitle('NEUROWEAVE  /  SIGNAL RECORD  /  TWO GENERATED CONDITIONS',fontsize=15,fontweight='bold')
fig.supxlabel('Artificial 10 Hz and 20 Hz components with noise and virtual-subject variation. These are not measured brain states.',fontsize=9)
fig.savefig(OUT/'signal-comparison.png',dpi=160);plt.close(fig)
print('Rendered benchmark.png and signal-comparison.png from saved/generated data.')
